#!/usr/bin/env node
/**
 * SessionStart hook — seeds the workshop before any Study begins.
 *
 * Fires once per session: startup, resume, clear, compact.
 * Loads config, detects project shape, writes env vars, and prints context.
 * Runs first in the SessionStart chain; a crash here must never block the session.
 *
 * Exit codes:
 *   0 — always (fail-open)
 *
 * Detection logic lives in lib/project-detector.cjs to allow reuse by OpenCode plugins.
 */

// Outer crash wrapper — last resort; keeps session alive on unexpected errors
try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const {
    loadConfig,
    readSessionState,
    writeEnv,
    updateSessionState,
    resolvePlanPath,
    getReportsPath,
    resolveNamingPattern,
    extractTaskListId,
    isHookEnabled
  } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');
  const { loadState, refreshStatuslineSnapshot } = require('./lib/session-state-manager.cjs');
  const { createEmptyActivitySnapshot } = require('./lib/statusline-session-cache.cjs');

  // Skip without side-effects if disabled in tkm.config.json
  if (!isHookEnabled('session-init')) {
    process.exit(0);
  }

  // Pull in the shared detection functions (type, PM, framework, git, coding level)
  const {
    detectProjectType,
    detectPackageManager,
    detectFramework,
    getGitBranch,
    getGitRoot,
    getCodingLevelStyleName,
    getCodingLevelGuidelines,
    buildContextOutput
  } = require('./lib/project-detector.cjs');

/**
 * Recover skills orphaned in `.shadowed/` by the now-disabled skill-dedup hook (Issue #422).
 * The hook is gone but old installs may still have stranded skills — fix once at startup.
 */
function cleanupOrphanedShadowedSkills() {
  const shadowedDir = path.join(process.cwd(), '.claude', 'skills', '.shadowed');
  if (!fs.existsSync(shadowedDir)) return { restored: [], skipped: [], kept: [] };

  const skillsDir = path.join(process.cwd(), '.claude', 'skills');
  const restored = [];
  const skipped = [];
  const kept = [];

  try {
    const entries = fs.readdirSync(shadowedDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const src = path.join(shadowedDir, entry.name);
      const dest = path.join(skillsDir, entry.name);

      try {
        if (!fs.existsSync(dest)) {
          fs.renameSync(src, dest);
          restored.push(entry.name);
          continue;
        }

        const orphanedSkill = path.join(src, 'SKILL.md');
        const localSkill = path.join(dest, 'SKILL.md');
        if (fs.existsSync(orphanedSkill) && fs.existsSync(localSkill)) {
          const orphanedContent = fs.readFileSync(orphanedSkill, 'utf8');
          const localContent = fs.readFileSync(localSkill, 'utf8');
          if (orphanedContent === localContent) {
            fs.rmSync(src, { recursive: true, force: true });
            skipped.push(entry.name);
          } else {
            kept.push(entry.name);
          }
        } else {
          fs.rmSync(src, { recursive: true, force: true });
          skipped.push(entry.name);
        }
      } catch (error) {
        process.stderr.write(`[session-init] Failed to process "${entry.name}": ${error.message}\n`);
      }
    }

    const manifestFile = path.join(shadowedDir, '.dedup-manifest.json');
    if (fs.existsSync(manifestFile)) fs.unlinkSync(manifestFile);
    if (fs.existsSync(shadowedDir) && fs.readdirSync(shadowedDir).length === 0) {
      fs.rmdirSync(shadowedDir);
    }

    return { restored, skipped, kept };
  } catch (error) {
    process.stderr.write(`[session-init] Shadowed cleanup error: ${error.message}\n`);
    return { restored, skipped, kept };
  }
}

/**
 * Detect whether this session is running inside an Agent Team.
 * Scans ~/.claude/teams/ for configs with live members.
 * Returns first match — Claude Code supports one active team per session.
 * Team lifecycle (create/cleanup) is owned by Claude Code, not this hook.
 * @returns {{ teamName: string, memberCount: number } | null}
 */
function detectAgentTeam() {
  try {
    const teamsDir = path.join(os.homedir(), '.claude', 'teams');
    if (!fs.existsSync(teamsDir)) return null;

    const teams = fs.readdirSync(teamsDir, { withFileTypes: true });
    for (const entry of teams) {
      if (!entry.isDirectory()) continue;
      const configPath = path.join(teamsDir, entry.name, 'config.json');
      if (!fs.existsSync(configPath)) continue;
      try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        if (config.members && config.members.length > 0) {
          return { teamName: entry.name, memberCount: config.members.length };
        }
      } catch { /* skip malformed configs */ }
    }
    return null;
  } catch {
    return null;
  }
}

function shouldWarmStatuslineCache(source, snapshot) {
  if (!['startup', 'resume', 'compact'].includes(source)) return false;
  return !snapshot || snapshot.warmed !== true;
}

/**
 * Entry point — reads stdin JSON, wires env vars, prints session context.
 */
async function main() {
  const timer = createHookTimer('session-init', { event: 'SessionStart' });
  try {
    const shadowedCleanup = cleanupOrphanedShadowedSkills();
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    const data = stdin ? JSON.parse(stdin) : {};
    const envFile = process.env.CLAUDE_ENV_FILE;
    const source = data.source || 'unknown';
    const sessionId = data.session_id || null;
    const existingSession = sessionId ? readSessionState(sessionId) : null;

    const config = loadConfig();
    const sessionStateEnabled = config.hooks?.['session-state'] !== false;

    const detections = {
      type: detectProjectType(config.project?.type),
      pm: detectPackageManager(config.project?.packageManager),
      framework: detectFramework(config.project?.framework)
    };

    // Resolve plan from session state or branch name; returns { path, resolvedBy }
    const resolved = resolvePlanPath(null, config);

    if (sessionId) {
      updateSessionState(sessionId, prev => ({
        ...prev,
        sessionOrigin: process.cwd(),
        activePlan: resolved.resolvedBy === 'session' ? resolved.path : null,
        suggestedPlan: resolved.resolvedBy === 'branch' ? resolved.path : null,
        timestamp: Date.now(),
        source,
        statusline: prev.statusline || createEmptyActivitySnapshot()
      }));
    }

    if (sessionStateEnabled && sessionId && shouldWarmStatuslineCache(source, existingSession?.statusline)) {
      await refreshStatuslineSnapshot(data);
    }

    // Reports land in the active plan only; suggested plans don't own a reports dir yet
    const reportsPath = getReportsPath(resolved.path, resolved.resolvedBy, config.plan, config.paths);

    // Derive task list ID from plan directory name (shared helper, keeps it DRY)
    const taskListId = extractTaskListId(resolved);

    // Gather cheap static facts here; slow enrichment (Python, remote URL) is deferred.
    const staticEnv = {
      nodeVersion: process.version,
      osPlatform: process.platform,
      gitBranch: getGitBranch(),
      gitRoot: getGitRoot(),
      user: process.env.USERNAME || process.env.USER || process.env.LOGNAME || os.userInfo().username,
      locale: process.env.LANG || '',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      claudeSettingsDir: path.resolve(__dirname, '..')
    };

    // Absolute base is CWD, not git root — subdirectory workflows create files here (Issue #327).
    // Git root is kept in staticEnv for reference only.
    const baseDir = process.cwd();

    // Resolve date and issue number now; keep {slug} as a placeholder for subagents to fill
    const namePattern = resolveNamingPattern(config.plan, staticEnv.gitBranch);

    if (envFile) {
      // Session identity and plan naming config
      writeEnv(envFile, 'TKM_SESSION_ID', sessionId || '');
      writeEnv(envFile, 'TKM_PLAN_NAMING_FORMAT', config.plan.namingFormat);
      writeEnv(envFile, 'TKM_PLAN_DATE_FORMAT', config.plan.dateFormat);
      writeEnv(envFile, 'TKM_PLAN_ISSUE_PREFIX', config.plan.issuePrefix || '');
      writeEnv(envFile, 'TKM_PLAN_REPORTS_DIR', config.plan.reportsDir);

      // Pre-resolved pattern subagents use for report/plan naming.
      // Example: "251212-1830-GH-88-{slug}" or "251212-1830-{slug}".
      // Agents substitute {slug} themselves: `{agent-type}-$TKM_NAME_PATTERN.md`.
      writeEnv(envFile, 'TKM_NAME_PATTERN', namePattern);

      // Plan state — active (session-pinned) vs suggested (branch-derived)
      writeEnv(envFile, 'TKM_ACTIVE_PLAN', resolved.resolvedBy === 'session' ? resolved.path : '');
      writeEnv(envFile, 'TKM_SUGGESTED_PLAN', resolved.resolvedBy === 'branch' ? resolved.path : '');

      // Takumi SDD mode: 'ask' (first-run prompt) | 'on' (spec stage) | 'off' (skip spec stage)
      writeEnv(envFile, 'TKM_SDD_MODE', config.takumi?.sddMode || 'ask');

      // Task list ID ties all sessions working the same plan to one shared task list.
      if (taskListId) {
        writeEnv(envFile, 'CLAUDE_CODE_TASK_LIST_ID', taskListId);
      }

      // Absolute paths rooted at CWD — correct for subdirectory workflows (Issue #327)
      writeEnv(envFile, 'TKM_GIT_ROOT', staticEnv.gitRoot || '');
      writeEnv(envFile, 'TKM_REPORTS_PATH', path.join(baseDir, reportsPath));
      writeEnv(envFile, 'TKM_DOCS_PATH', path.join(baseDir, config.paths.docs));
      writeEnv(envFile, 'TKM_PLANS_PATH', path.join(baseDir, config.paths.plans));
      writeEnv(envFile, 'TKM_PROJECT_ROOT', process.cwd());

      // Detected project shape (type, package manager, framework)
      writeEnv(envFile, 'TKM_PROJECT_TYPE', detections.type || '');
      writeEnv(envFile, 'TKM_PACKAGE_MANAGER', detections.pm || '');
      writeEnv(envFile, 'TKM_FRAMEWORK', detections.framework || '');

      // Runtime environment facts — cached here so downstream hooks skip recomputation
      writeEnv(envFile, 'TKM_NODE_VERSION', staticEnv.nodeVersion);
      writeEnv(envFile, 'TKM_OS_PLATFORM', staticEnv.osPlatform);
      writeEnv(envFile, 'TKM_GIT_BRANCH', staticEnv.gitBranch || '');
      writeEnv(envFile, 'TKM_USER', staticEnv.user);
      writeEnv(envFile, 'TKM_LOCALE', staticEnv.locale);
      writeEnv(envFile, 'TKM_TIMEZONE', staticEnv.timezone);
      writeEnv(envFile, 'TKM_CLAUDE_SETTINGS_DIR', staticEnv.claudeSettingsDir);

      // Optional locale overrides for thinking and response language
      if (config.locale?.thinkingLanguage) {
        writeEnv(envFile, 'TKM_THINKING_LANGUAGE', config.locale.thinkingLanguage);
      }
      if (config.locale?.responseLanguage) {
        writeEnv(envFile, 'TKM_RESPONSE_LANGUAGE', config.locale.responseLanguage);
      }

      // Blueprint validation config (mode, question counts, focus areas)
      const validation = config.plan?.validation || {};
      writeEnv(envFile, 'TKM_VALIDATION_MODE', validation.mode || 'prompt');
      writeEnv(envFile, 'TKM_VALIDATION_MIN_QUESTIONS', validation.minQuestions || 3);
      writeEnv(envFile, 'TKM_VALIDATION_MAX_QUESTIONS', validation.maxQuestions || 8);
      writeEnv(envFile, 'TKM_VALIDATION_FOCUS_AREAS', (validation.focusAreas || ['assumptions', 'risks', 'tradeoffs', 'architecture']).join(','));

      // Coding level — governs output-style selection for response verbosity
      const codingLevel = config.codingLevel ?? 5;
      writeEnv(envFile, 'TKM_CODING_LEVEL', codingLevel);
      writeEnv(envFile, 'TKM_CODING_LEVEL_STYLE', getCodingLevelStyleName(codingLevel));

    }

    // Detect team membership once; result drives both env vars and console output below
    const teamInfo = detectAgentTeam();
    if (envFile && teamInfo) {
      writeEnv(envFile, 'TKM_AGENT_TEAM', teamInfo.teamName);
      writeEnv(envFile, 'TKM_AGENT_TEAM_MEMBERS', teamInfo.memberCount);
    }

    console.log(`Session ${source}. ${buildContextOutput(config, detections, resolved, staticEnv.gitRoot)}`);

    const hasCleanup =
      shadowedCleanup.restored.length > 0 ||
      shadowedCleanup.skipped.length > 0 ||
      shadowedCleanup.kept.length > 0;
    if (hasCleanup) {
      console.log(`\n[!] SKILL-DEDUP CLEANUP (Issue #422):`);
      console.log(`Recovered orphaned .shadowed/ directory from disabled skill-dedup hook.`);
      if (shadowedCleanup.restored.length > 0) {
        console.log(`Restored ${shadowedCleanup.restored.length} skill(s): ${shadowedCleanup.restored.join(', ')}`);
      }
      if (shadowedCleanup.skipped.length > 0) {
        console.log(`Removed ${shadowedCleanup.skipped.length} duplicate(s): ${shadowedCleanup.skipped.join(', ')}`);
      }
      if (shadowedCleanup.kept.length > 0) {
        console.log(`[!] Kept ${shadowedCleanup.kept.length} skill(s) for manual review (content differs): ${shadowedCleanup.kept.join(', ')}`);
        console.log(`    Review .claude/skills/.shadowed/ and merge changes manually.`);
      }
    }

    if (sessionStateEnabled && (source === 'startup' || source === 'compact')) {
      const previousState = loadState(process.cwd());
      if (previousState) {
        if (source === 'compact') {
          console.log('\n--- Session State (Post-Compaction Recovery) ---');
          console.log(previousState);
          console.log('--- End Session State ---\n');
          console.log('Context was compacted. Above is your last saved progress. Resume from where you left off.');
          console.log('IMPORTANT: Re-read active plan files and todo list. Do NOT re-do completed work.');
        } else {
          console.log('\n--- Previous Session State ---');
          console.log(previousState);
          console.log('--- End Session State ---\n');
          console.log('Review above state from your last session. Continue where you left off or start fresh.');
        }
      }
    }

    // Surface team context to the agent when running inside an Agent Team
    if (teamInfo) {
      console.log(`[i] Agent Team detected: "${teamInfo.teamName}" (${teamInfo.memberCount} members)`);
      console.log(`    Team config: ~/.claude/teams/${teamInfo.teamName}/config.json`);
      console.log(`    See .claude/rules/team-coordination-rules.md for teamwork conventions.`);
    }

    // Show git root when session is in a subdirectory — subdirectory mode is supported (Issue #327)
    if (staticEnv.gitRoot && staticEnv.gitRoot !== process.cwd()) {
      console.log(`📁 Subdirectory mode: Plans/docs will be created in current directory`);
      console.log(`   Git root: ${staticEnv.gitRoot}`);
    }

    // Issue #277: auto-compact can silently drop "pending approval" state mid-workflow.
    // Warn the agent to re-confirm with the user before acting — do not assume approval was given.
    // Upstream: Claude Code CLI should preserve interactive state across compaction.
    if (source === 'compact') {
      console.log(`\n⚠️ CONTEXT COMPACTED - APPROVAL STATE CHECK:`);
      console.log(`If you were waiting for user approval via AskUserQuestion (e.g., Step 4 review gate),`);
      console.log(`you MUST re-confirm with the user before proceeding. Do NOT assume approval was given.`);
      console.log(`Use AskUserQuestion to verify: "Context was compacted. Please confirm approval to continue."`);
    }

    // Inject output-style guidelines when a coding level is configured (level -1 = disabled)
    const codingLevel = config.codingLevel ?? -1;
    const guidelines = getCodingLevelGuidelines(codingLevel);
    if (guidelines) {
      console.log(`\n${guidelines}`);
    }

    if (config.assertions?.length > 0) {
      console.log(`\nUser Assertions:`);
      config.assertions.forEach((assertion, i) => {
        console.log(`  ${i + 1}. ${assertion}`);
      });
    }

    timer.end({ status: 'ok', exit: 0, note: source || 'session-start' });
    process.exit(0);
  } catch (error) {
    console.error(`SessionStart hook error: ${error.message}`);
    logHookCrash('session-init', error, { event: 'SessionStart' });
    process.exit(0);
  }
  }

  main();
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('session-init', e, { event: 'SessionStart' });
  } catch (_) {}
  process.exit(0); // fail-open
}
