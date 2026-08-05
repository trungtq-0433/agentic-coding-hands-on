#!/usr/bin/env node
/**
 * context-builder.cjs — Craft and deliver the session injection payload.
 *
 * Pure builder: assembles language, session, rules, paths, and plan blocks
 * for injection into agent working memory. Called by dev-rules-reminder
 * (UserPromptSubmit), subagent-init (SubagentStart), and usage-quota-cache-refresh.
 *
 * @module context-builder
 */

'use strict';

const fs   = require('fs');
const os   = require('os');
const path = require('path');
const { execSync } = require('child_process');

// Cache written by usage-context-awareness.cjs; read here during injection.
const USAGE_CACHE_FILE        = path.join(os.tmpdir(), 'sk-usage-limits-cache.json');
const RECENT_INJECTION_TTL_MS = 5 * 60 * 1000;
const PENDING_INJECTION_TTL_MS = 30 * 1000;
const WARN_THRESHOLD     = 70;
const CRITICAL_THRESHOLD = 90;

const {
  loadConfig,
  resolvePlanPath,
  getReportsPath,
  resolveNamingPattern,
  normalizePath,
  getGitBranch,
  readSessionState,
  updateSessionState,
} = require('./tkm-config-utils.cjs');

// ─── SHELL UTILITY ──────────────────────────────────────────────────────────

/** Run a shell command; return trimmed stdout or null on failure. */
function execSafe(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch {
    return null;
  }
}

// ─── PATH RESOLVERS ─────────────────────────────────────────────────────────

/**
 * Locate a rules file: local rules/ → global rules/ → local workflows/ → global workflows/.
 * The workflows/ fallback preserves compat with installs predating the rules/ rename.
 */
function resolveRulesPath(filename, configDirName = '.claude') {
  const cwd    = process.cwd();
  const home   = os.homedir();

  const localRules  = path.join(cwd,  configDirName,  'rules', filename);
  const globalRules = path.join(home, '.claude', 'rules', filename);
  if (fs.existsSync(localRules))  return `${configDirName}/rules/${filename}`;
  if (fs.existsSync(globalRules)) return `~/.claude/rules/${filename}`;

  // Legacy workflows/ fallback
  const localWf  = path.join(cwd,  configDirName,  'workflows', filename);
  const globalWf = path.join(home, '.claude', 'workflows', filename);
  if (fs.existsSync(localWf))  return `${configDirName}/workflows/${filename}`;
  if (fs.existsSync(globalWf)) return `~/.claude/workflows/${filename}`;

  return null;
}

/** Locate a script file: local .claude/scripts/ → global ~/.claude/scripts/. */
function resolveScriptPath(filename, configDirName = '.claude') {
  const localSrc  = path.join(process.cwd(),  configDirName,  'scripts', filename);
  const globalSrc = path.join(os.homedir(), '.claude', 'scripts', filename);
  if (fs.existsSync(localSrc))  return `${configDirName}/scripts/${filename}`;
  if (fs.existsSync(globalSrc)) return `~/.claude/scripts/${filename}`;
  return null;
}

/** Locate the skills venv Python binary; local install preferred over global. */
function resolveSkillsVenv(configDirName = '.claude') {
  const win     = process.platform === 'win32';
  const binDir  = win ? 'Scripts' : 'bin';
  const pyBin   = win ? 'python.exe' : 'python3';

  const localPy  = path.join(process.cwd(),  configDirName,  'skills', '.venv', binDir, pyBin);
  const globalPy = path.join(os.homedir(), '.claude', 'skills', '.venv', binDir, pyBin);

  if (fs.existsSync(localPy)) {
    return win
      ? `${configDirName}\\skills\\.venv\\Scripts\\python.exe`
      : `${configDirName}/skills/.venv/bin/python3`;
  }
  if (fs.existsSync(globalPy)) {
    return win
      ? '~\\.claude\\skills\\.venv\\Scripts\\python.exe'
      : '~/.claude/skills/.venv/bin/python3';
  }
  return null;
}

// ─── PLAN CONTEXT ───────────────────────────────────────────────────────────

/**
 * Derive active plan metadata from config + git state.
 * Produces the planLine, reportsPath, namePattern, and validation thresholds
 * consumed by the section builders below.
 */
function buildPlanContext(sessionId, config) {
  const { plan, paths } = config;
  const branch  = getGitBranch();
  const resolved = resolvePlanPath(sessionId, config);
  const reports  = getReportsPath(resolved.path, resolved.resolvedBy, plan, paths);
  const pattern  = resolveNamingPattern(plan, branch);

  let planLine;
  if (resolved.resolvedBy === 'session') {
    planLine = `- Plan: ${resolved.path}`;
  } else if (resolved.resolvedBy === 'branch') {
    planLine = `- Plan: none | Suggested: ${resolved.path}`;
  } else {
    planLine = `- Plan: none`;
  }

  const validation    = plan.validation || {};
  const vMode = validation.mode         || 'prompt';
  const vMin  = validation.minQuestions || 3;
  const vMax  = validation.maxQuestions || 8;

  // Takumi SDD mode (injected so takumi Stage 0 can read it without a config lookup)
  const sddMode = config.takumi?.sddMode || 'ask';

  return {
    reportsPath:     reports,
    gitBranch:       branch,
    planLine,
    namePattern:     pattern,
    validationMode:  vMode,
    validationMin:   vMin,
    validationMax:   vMax,
    sddMode,
  };
}

// ─── DEDUP / SCOPE KEY ──────────────────────────────────────────────────────

/**
 * Derive a stable scope key from cwd so re-injection triggers when the
 * working directory changes between prompts.
 */
function buildInjectionScopeKey({ baseDir } = {}) {
  const resolved = normalizePath(path.resolve(baseDir || process.cwd())) || process.cwd();
  return resolved;
}

// ─── INTERNAL SCOPE-STATE HELPERS ───────────────────────────────────────────

/** Parse a timestamp stored as either a number or ISO string into epoch ms. */
function toEpoch(raw) {
  if (typeof raw === 'number') return raw;
  if (typeof raw === 'string') return Date.parse(raw);
  return NaN;
}

/** Pull the per-scope sub-object from the reminder state blob; null if absent. */
function pickScopeState(reminderState, key) {
  const scopes = reminderState?.scopes;
  if (!scopes || typeof scopes !== 'object') return null;
  const entry = scopes[key];
  return entry && typeof entry === 'object' ? entry : null;
}

/** True when the scope was injected within the recent-injection TTL. */
function withinRecentTTL(scopeState, now = Date.now()) {
  const ts = toEpoch(scopeState?.lastInjectedAt);
  return Number.isFinite(ts) && now - ts < RECENT_INJECTION_TTL_MS;
}

/** True when a pending reservation exists within the pending TTL. */
function withinPendingTTL(scopeState, now = Date.now()) {
  const ts = toEpoch(scopeState?.pendingAt);
  return Number.isFinite(ts) && now - ts < PENDING_INJECTION_TTL_MS;
}

/** Drop stale scope entries; keep only those still within either TTL. */
function evictExpiredScopes(scopes, now = Date.now()) {
  const kept = {};
  for (const [k, v] of Object.entries(scopes || {})) {
    if (!v || typeof v !== 'object') continue;
    if (withinRecentTTL(v, now) || withinPendingTTL(v, now)) kept[k] = v;
  }
  return kept;
}

// ─── TRANSCRIPT FALLBACK ────────────────────────────────────────────────────

/**
 * Scan the tail of a transcript file for the modularization marker.
 * When scopeKey is given, also require a matching CWD line — prevents a
 * foreign-cwd transcript from suppressing injection in the current directory.
 */
function transcriptHasMarker(transcriptPath, scopeKey = null) {
  try {
    if (!transcriptPath || !fs.existsSync(transcriptPath)) return false;
    const tail = fs.readFileSync(transcriptPath, 'utf-8').split('\n').slice(-150);
    if (!tail.some(l => l.includes('[IMPORTANT] Consider Modularization'))) return false;
    if (!scopeKey) return true;
    return tail.some(l => l === `- CWD: ${scopeKey}` || l === `- Working directory: ${scopeKey}`);
  } catch {
    return false;
  }
}

// ─── PUBLIC DEDUP API ───────────────────────────────────────────────────────

/**
 * True when context was injected within the TTL window.
 * Session-state is checked first; transcript scan is the fallback when no sessionId.
 */
function wasRecentlyInjected(transcriptPath, sessionId = null, scopeKey = 'session') {
  try {
    if (sessionId) {
      const reminderBlob = readSessionState(sessionId)?.devRulesReminder;
      if (withinRecentTTL(pickScopeState(reminderBlob, scopeKey))) return true;
    }
    return transcriptHasMarker(transcriptPath, scopeKey);
  } catch {
    return false;
  }
}

/**
 * Atomically claim an injection slot; losing concurrent hooks skip injection.
 * Writes a pending marker first; caller upgrades to injected via markRecentlyInjected.
 */
function reserveInjectionScope(sessionId, scopeKey = 'session', transcriptPath = null) {
  const alreadyInTranscript = transcriptHasMarker(transcriptPath, scopeKey);

  if (!sessionId) {
    return { shouldInject: !alreadyInTranscript, reserved: false };
  }

  try {
    let shouldInject = false;
    const now = Date.now();

    const updated = updateSessionState(sessionId, (state) => {
      const reminderBlob = (state.devRulesReminder && typeof state.devRulesReminder === 'object')
        ? state.devRulesReminder
        : {};
      const scopes     = evictExpiredScopes(reminderBlob.scopes, now);
      const scopeEntry = pickScopeState({ scopes }, scopeKey) || {};

      // Slot already claimed or pending — bail out without mutation.
      if (withinRecentTTL(scopeEntry, now) || withinPendingTTL(scopeEntry, now)) {
        return state;
      }

      if (alreadyInTranscript) {
        // Transcript proves injection happened — backfill the timestamp and exit.
        scopes[scopeKey] = { ...scopeEntry, lastInjectedAt: new Date(now).toISOString() };
        return { ...state, devRulesReminder: { ...reminderBlob, scopes } };
      }

      // We own the slot; write the pending marker.
      shouldInject = true;
      scopes[scopeKey] = { ...scopeEntry, pendingAt: new Date(now).toISOString() };
      return { ...state, devRulesReminder: { ...reminderBlob, scopes } };
    });

    if (!updated) {
      return { shouldInject: !alreadyInTranscript, reserved: false };
    }

    return { shouldInject, reserved: shouldInject };
  } catch {
    return { shouldInject: !alreadyInTranscript, reserved: false };
  }
}

/**
 * Promote the pending slot to injected: write lastInjectedAt and drop pendingAt.
 * Called by the hook after it has successfully delivered the payload.
 */
function markRecentlyInjected(sessionId, scopeKey = 'session') {
  if (!sessionId) return false;

  try {
    return updateSessionState(sessionId, (state) => {
      const reminderBlob = (state.devRulesReminder && typeof state.devRulesReminder === 'object')
        ? state.devRulesReminder
        : {};
      const scopes     = evictExpiredScopes(reminderBlob.scopes);
      const scopeEntry = pickScopeState({ scopes }, scopeKey) || {};

      const next = { ...scopeEntry, lastInjectedAt: new Date().toISOString() };
      delete next.pendingAt;
      scopes[scopeKey] = next;

      return { ...state, devRulesReminder: { ...reminderBlob, scopes } };
    });
  } catch {
    return false;
  }
}

/**
 * Rollback a pending reservation when the hook errors after claiming the slot.
 * Prevents a stale pending entry from blocking the next prompt's injection.
 */
function clearPendingInjection(sessionId, scopeKey = 'session') {
  if (!sessionId) return false;

  try {
    return updateSessionState(sessionId, (state) => {
      const reminderBlob = (state.devRulesReminder && typeof state.devRulesReminder === 'object')
        ? state.devRulesReminder
        : {};
      const scopes     = evictExpiredScopes(reminderBlob.scopes);
      const scopeEntry = pickScopeState({ scopes }, scopeKey);

      if (!scopeEntry || !scopeEntry.pendingAt) return state;

      const trimmed = { ...scopeEntry };
      delete trimmed.pendingAt;

      if (Object.keys(trimmed).length === 0) {
        delete scopes[scopeKey];
      } else {
        scopes[scopeKey] = trimmed;
      }

      return { ...state, devRulesReminder: { ...reminderBlob, scopes } };
    });
  } catch {
    return false;
  }
}

// ─── SECTION BUILDERS ───────────────────────────────────────────────────────

/**
 * Language instruction block.
 * Defaults thinking to 'en' when a non-English response language is set —
 * English reasoning gives the model sharper logical precision.
 */
function buildLanguageSection({ thinkingLanguage, responseLanguage }) {
  const effective = thinkingLanguage || (responseLanguage ? 'en' : null);
  const showThink = effective && effective !== responseLanguage;
  const showReply = !!responseLanguage;

  if (!showThink && !showReply) return [];

  const out = ['## Language'];
  if (showThink) out.push(`- Thinking: Use ${effective} for reasoning (logic, precision).`);
  if (showReply) out.push(`- Response: Respond in ${responseLanguage} (natural, fluent).`);
  out.push('');
  return out;
}

/** Session environment block: cwd, OS, memory, CPU. */
function buildSessionSection(staticEnv = {}) {
  const heapMB   = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);
  const totalMB  = Math.round(os.totalmem() / 1024 / 1024);
  const memPct   = Math.round((heapMB / totalMB) * 100);
  const cpuUser  = Math.round((process.cpuUsage().user   / 1_000_000) * 100);
  const cpuSys   = Math.round((process.cpuUsage().system / 1_000_000) * 100);

  return [
    `## Session`,
    `- DateTime: ${new Date().toLocaleString()}`,
    `- CWD: ${staticEnv.cwd || process.cwd()}`,
    `- Timezone: ${staticEnv.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone}`,
    `- Working directory: ${staticEnv.cwd || process.cwd()}`,
    `- OS: ${staticEnv.osPlatform || process.platform}`,
    `- User: ${staticEnv.user || process.env.USERNAME || process.env.USER}`,
    `- Locale: ${staticEnv.locale || process.env.LANG || ''}`,
    `- Memory usage: ${heapMB}MB/${totalMB}MB (${memPct}%)`,
    `- CPU usage: ${cpuUser}% user / ${cpuSys}% system`,
    `- Spawning multiple subagents can cause performance issues, spawn and delegate tasks intelligently based on the available system resources.`,
    `- Remember that each subagent only has 200K tokens in context window, spawn and delegate tasks intelligently to make sure their context windows don't get bloated.`,
    `- IMPORTANT: Include these environment information when prompting subagents to perform tasks.`,
    '',
  ];
}

// ─── USAGE HELPERS (used by buildUsageSection, currently disabled) ───────────

/** Load the usage cache; return null if absent or older than 5 min. */
function loadUsageCache() {
  try {
    if (!fs.existsSync(USAGE_CACHE_FILE)) return null;
    const raw   = JSON.parse(fs.readFileSync(USAGE_CACHE_FILE, 'utf-8'));
    const fresh = Date.now() - raw.timestamp < 300_000 && raw.data;
    return fresh ? raw.data : null;
  } catch {
    return null;
  }
}

/**
 * Human-readable time remaining until a quota reset.
 * Returns null when the reset is > 5 hours away or already elapsed.
 */
function fmtTimeUntilReset(resetAt) {
  if (!resetAt) return null;
  const secs = Math.floor(new Date(resetAt).getTime() / 1000) - Math.floor(Date.now() / 1000);
  if (secs <= 0 || secs > 18_000) return null;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return `${h}h ${m}m`;
}

/** Percentage string with severity label when threshold crossed. */
function fmtUsagePct(value, label) {
  const pct = Math.round(value);
  if (pct >= CRITICAL_THRESHOLD) return `${label}: ${pct}% [CRITICAL]`;
  if (pct >= WARN_THRESHOLD)     return `${label}: ${pct}% [WARNING]`;
  return `${label}: ${pct}%`;
}

/**
 * Context-window utilization block.
 * Currently disabled — early return keeps the wire empty until the use-case warrants it.
 */
function buildContextSection(sessionId) {
  // TEMPORARILY DISABLED
  return [];
  if (!sessionId) return [];

  // RE-ENABLED IF NEEDED IN THE FUTURE
  try {
    const ctxFile = path.join(os.tmpdir(), `sk-context-${sessionId}.json`);
    if (!fs.existsSync(ctxFile)) return [];

    const data = JSON.parse(fs.readFileSync(ctxFile, 'utf-8'));
    if (Date.now() - data.timestamp > 300_000) return [];

    const usedK = Math.round(data.tokens / 1000);
    const sizeK = Math.round(data.size   / 1000);
    const out   = [
      `## Current Session's Context`,
      `- Context: ${data.percent}% used (${usedK}K/${sizeK}K tokens)`,
      `- **NOTE:** Optimize the workflow for token efficiency`,
    ];

    if (data.percent >= CRITICAL_THRESHOLD) {
      out.push(`- **CRITICAL:** Context nearly full. Before compaction hits:`);
      out.push(`  1. Update TodoWrite with current progress (completed + remaining)`);
      out.push(`  2. Be extremely concise — no verbose explanations`);
      out.push(`  3. Session state will auto-restore after compaction`);
    } else if (data.percent >= WARN_THRESHOLD) {
      out.push(`- **WARNING:** Context usage moderate - be concise, optimize token efficiency, keep tool outputs short.`);
    }

    out.push('');
    return out;
  } catch {
    return [];
  }
}

/**
 * Quota usage block.
 * Currently disabled — early return until the use-case warrants re-enabling.
 */
function buildUsageSection() {
  // TEMPORARILY DISABLED
  return [];

  // RE-ENABLED IF NEEDED IN THE FUTURE
  const usage = loadUsageCache();
  if (!usage) return [];

  const parts = [];

  if (usage.five_hour) {
    const u = usage.five_hour.utilization;
    if (typeof u === 'number') parts.push(fmtUsagePct(u, '5h'));
    const left = fmtTimeUntilReset(usage.five_hour.resets_at);
    if (left) parts.push(`resets in ${left}`);
  }
  if (usage.seven_day?.utilization != null) {
    parts.push(fmtUsagePct(usage.seven_day.utilization, '7d'));
  }

  if (!parts.length) return [];
  return [`## Usage Limits`, `- ${parts.join(' | ')}`, ''];
}

/**
 * Rules and conventions block.
 * Absolute paths for plansPath/docsPath prevent ambiguity in multi-CLAUDE.md projects.
 */
function buildRulesSection({ devRulesPath, skillsVenv, plansPath, docsPath }) {
  const pRef = plansPath || 'plans';
  const dRef = docsPath  || 'docs';
  const out  = ['## Rules'];

  if (devRulesPath) {
    out.push(`- Read and follow development rules: "${devRulesPath}"`);
  }

  out.push(`- Markdown files are organized in: Plans → "${pRef}" directory, Docs → "${dRef}" directory`);
  out.push(`- **IMPORTANT:** DO NOT create markdown files outside of "${pRef}" or "${dRef}" UNLESS the user explicitly requests it.`);

  if (skillsVenv) {
    out.push(`- Python scripts in .claude/skills/: Use \`${skillsVenv}\``);
  }

  out.push(`- When skills' scripts are failed to execute, always fix them and run again, repeat until success.`);
  out.push(`- Follow **YAGNI (You Aren't Gonna Need It) - KISS (Keep It Simple, Stupid) - DRY (Don't Repeat Yourself)** principles`);
  out.push(`- Sacrifice grammar for the sake of concision when writing reports.`);
  out.push(`- In reports, list any unresolved questions at the end, if any.`);
  out.push(`- IMPORTANT: Ensure token consumption efficiency while maintaining high quality.`);
  out.push('');

  return out;
}

/** Modularization guidance block. */
function buildModularizationSection() {
  return [
    `## **[IMPORTANT] Consider Modularization:**`,
    `- Check existing modules before creating new`,
    `- Analyze logical separation boundaries (functions, classes, concerns)`,
    `- Prefer kebab-case for JS/TS/Python/shell; respect language conventions (C#/Java use PascalCase, Go/Rust use snake_case)`,
    `- Write descriptive code comments`,
    `- After modularization, continue with main task`,
    `- When not to modularize: Markdown files, plain text files, bash scripts, configuration files, environment variables files, etc.`,
    '',
  ];
}

/**
 * Paths reference block: tells agents where to write reports, plans, and docs.
 * Absolute paths prevent wrong-subdirectory creation in nested CLAUDE.md projects.
 */
function buildPathsSection({ reportsPath, plansPath, docsPath, docsMaxLoc = 800 }) {
  return [
    `## Paths`,
    `Reports: ${reportsPath} | Plans: ${plansPath}/ | Docs: ${docsPath}/ | docs.maxLoc: ${docsMaxLoc}`,
    '',
  ];
}

/**
 * Plan context block: active plan, reports path, branch, and validation config.
 * Injected at every session start so the agent always knows which plan is live.
 */
function buildPlanContextSection({ planLine, reportsPath, gitBranch, validationMode, validationMin, validationMax, sddMode }) {
  const out = [
    `## Plan Context`,
    planLine,
    `- Reports: ${reportsPath}`,
  ];
  if (gitBranch) out.push(`- Branch: ${gitBranch}`);
  out.push(`- Validation: mode=${validationMode}, questions=${validationMin}-${validationMax}`);
  if (sddMode) {
    out.push(`- SDD mode: ${sddMode} (takumi.sddMode${sddMode === 'ask' ? ' — unset, takumi will prompt on first run' : ''})`);
  }
  out.push('');
  return out;
}

/**
 * Naming convention block: stamp the agent with the current report/plan
 * naming pattern so outputs land in consistent, time-stamped locations.
 */
function buildNamingSection({ reportsPath, plansPath, namePattern }) {
  return [
    `## Naming`,
    `- Report: \`${reportsPath}{type}-${namePattern}.md\``,
    `- Plan dir: \`${plansPath}/${namePattern}/\``,
    `- Replace \`{type}\` with: agent name, report type, or context`,
    `- Replace \`{slug}\` in pattern with: descriptive-kebab-slug`,
  ];
}

// ─── ASSEMBLY ────────────────────────────────────────────────────────────────

/**
 * Combine all section arrays into the final ordered injection payload.
 * Hook-disabled sections are omitted when the config says so.
 */
function buildReminder(params) {
  const {
    sessionId, thinkingLanguage, responseLanguage,
    devRulesPath, skillsVenv, reportsPath, plansPath, docsPath, docsMaxLoc,
    planLine, gitBranch, namePattern, validationMode, validationMin, validationMax,
    sddMode,
    staticEnv, hooks,
  } = params;

  const hk              = hooks || {};
  const ctxEnabled      = hk['context-tracking']          !== false;
  const usageEnabled    = hk['usage-context-awareness']   !== false;

  return [
    ...buildLanguageSection({ thinkingLanguage, responseLanguage }),
    ...buildSessionSection(staticEnv),
    ...(ctxEnabled   ? buildContextSection(sessionId) : []),
    ...(usageEnabled ? buildUsageSection()             : []),
    ...buildRulesSection({ devRulesPath, skillsVenv, plansPath, docsPath }),
    ...buildModularizationSection(),
    ...buildPathsSection({ reportsPath, plansPath, docsPath, docsMaxLoc }),
    ...buildPlanContextSection({ planLine, reportsPath, gitBranch, validationMode, validationMin, validationMax, sddMode }),
    ...buildNamingSection({ reportsPath, plansPath, namePattern }),
  ];
}

/**
 * Primary entry point for all hooks and plugins.
 * Loads takumi config when omitted, resolves every path, and returns the
 * assembled payload plus a section map for callers that need individual blocks.
 */
function buildReminderContext({ sessionId, config, staticEnv, configDirName = '.claude', baseDir } = {}) {
  const cfg = config || loadConfig({ includeProject: false, includeAssertions: false });

  const rulesPath  = resolveRulesPath('development-rules.md', configDirName);
  const skillsPy   = resolveSkillsVenv(configDirName);
  const planCtx    = buildPlanContext(sessionId, cfg);

  const anchor     = baseDir || null;
  const plansRel   = normalizePath(cfg.paths?.plans) || 'plans';
  const docsRel    = normalizePath(cfg.paths?.docs)  || 'docs';

  const joinIfBase = (base, rel) => base ? path.join(base, rel) : rel;

  const p = {
    sessionId,
    thinkingLanguage:  cfg.locale?.thinkingLanguage,
    responseLanguage:  cfg.locale?.responseLanguage,
    devRulesPath:      rulesPath,
    skillsVenv:        skillsPy,
    reportsPath:       joinIfBase(anchor, planCtx.reportsPath),
    plansPath:         joinIfBase(anchor, plansRel),
    docsPath:          joinIfBase(anchor, docsRel),
    docsMaxLoc:        Math.max(1, parseInt(cfg.docs?.maxLoc, 10) || 800),
    planLine:          planCtx.planLine,
    gitBranch:         planCtx.gitBranch,
    namePattern:       planCtx.namePattern,
    validationMode:    planCtx.validationMode,
    validationMin:     planCtx.validationMin,
    validationMax:     planCtx.validationMax,
    sddMode:           planCtx.sddMode,
    staticEnv,
    hooks:             cfg.hooks,
  };

  const lines = buildReminder(p);

  const hk           = cfg.hooks || {};
  const ctxEnabled   = hk['context-tracking']        !== false;
  const usageEnabled = hk['usage-context-awareness'] !== false;

  return {
    content: lines.join('\n'),
    lines,
    sections: {
      language:       buildLanguageSection({ thinkingLanguage: p.thinkingLanguage, responseLanguage: p.responseLanguage }),
      session:        buildSessionSection(staticEnv),
      context:        ctxEnabled   ? buildContextSection(sessionId) : [],
      usage:          usageEnabled ? buildUsageSection()             : [],
      rules:          buildRulesSection({ devRulesPath: rulesPath, skillsVenv: skillsPy, plansPath: p.plansPath, docsPath: p.docsPath }),
      modularization: buildModularizationSection(),
      paths:          buildPathsSection({ reportsPath: p.reportsPath, plansPath: p.plansPath, docsPath: p.docsPath, docsMaxLoc: p.docsMaxLoc }),
      planContext:    buildPlanContextSection(planCtx),
      naming:         buildNamingSection({ reportsPath: p.reportsPath, plansPath: p.plansPath, namePattern: p.namePattern }),
    },
  };
}

// ─── EXPORTS ─────────────────────────────────────────────────────────────────

module.exports = {
  // Entry points
  buildReminderContext,
  buildReminder,

  // Section builders
  buildLanguageSection,
  buildSessionSection,
  buildContextSection,
  buildUsageSection,
  buildRulesSection,
  buildModularizationSection,
  buildPathsSection,
  buildPlanContextSection,
  buildNamingSection,

  // Helpers
  execSafe,
  resolveRulesPath,
  resolveScriptPath,
  resolveSkillsVenv,
  buildPlanContext,
  buildInjectionScopeKey,
  wasRecentlyInjected,
  reserveInjectionScope,
  markRecentlyInjected,
  clearPendingInjection,

  // Backward-compat alias
  resolveWorkflowPath: resolveRulesPath,
};
