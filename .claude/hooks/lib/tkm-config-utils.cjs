/**
 * tkm-config-utils.cjs — Takumi Agent Kit: core config and path utilities.
 *
 * Handles cascading config load (DEFAULT → global → local), filesystem-safe
 * path handling, session-state I/O with file-lock, and naming-pattern resolution.
 * Consumed by every hook that needs config or safe paths.
 */

'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');
const { execFileSync } = require('child_process');

// ---------------------------------------------------------------------------
// Config file paths
// ---------------------------------------------------------------------------

const LOCAL_CONFIG_PATH  = '.claude/.tkm.json';
const GLOBAL_CONFIG_PATH = path.join(os.homedir(), '.claude', '.tkm.json');

// Legacy .sk.json paths — read-only fallback; existing user configs keep working
const LEGACY_LOCAL_CONFIG_PATH  = '.claude/.sk.json';
const LEGACY_GLOBAL_CONFIG_PATH = path.join(os.homedir(), '.claude', '.sk.json');

// Backward-compat alias — callers that imported CONFIG_PATH still work
const CONFIG_PATH = LOCAL_CONFIG_PATH;

// ---------------------------------------------------------------------------
// Session-state lock tuning
// ---------------------------------------------------------------------------

const _LOCK_TIMEOUT_MS = 500;   // max wait to acquire lock
const _LOCK_RETRY_MS   = 10;    // poll interval while contending
const _LOCK_STALE_MS   = 5000;  // lock older than this is considered dead

// ---------------------------------------------------------------------------
// Default configuration
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG = {
  plan: {
    namingFormat: '{date}-{issue}-{slug}',
    dateFormat: 'YYMMDD-HHmm',
    issuePrefix: null,
    reportsDir: 'reports',
    resolution: {
      // 'mostRecent' removed — only explicit session state activates a plan;
      // branch matching now returns 'suggested', not 'active'
      order: ['session', 'branch'],
      branchPattern: '(?:feat|fix|chore|refactor|docs)/(?:[^/]+/)?(.+)'
    },
    validation: {
      mode: 'prompt',  // 'auto' | 'prompt' | 'off'
      minQuestions: 3,
      maxQuestions: 8,
      focusAreas: ['assumptions', 'risks', 'tradeoffs', 'architecture']
    }
  },
  paths: {
    docs: 'docs',
    plans: 'plans'
  },
  docs: {
    maxLoc: 800  // lines-of-code ceiling per doc file; exceeded = modularization hint
  },
  locale: {
    thinkingLanguage: null,  // reasoning language (e.g. "en" for precision)
    responseLanguage: null   // user-facing response language (e.g. "vi")
  },
  trust: {
    passphrase: null,
    enabled: false
  },
  takumi: {
    // SDD (Spec-Driven Development) mode for the takumi pipeline / tkm-plan spec gate.
    // 'ask' = unset → prompt the user on first takumi run, then persist their choice here.
    // 'on'  = Stage 1.5 (spec authoring) runs. 'off' = spec stage skipped project-wide.
    // Persisted to project-scope .claude/.tkm.json so a team shares one decision.
    sddMode: 'ask'
  },
  project: {
    type: 'auto',
    packageManager: 'auto',
    framework: 'auto'
  },
  skills: {
    research: {
      useGemini: false  // opt-in — requires a working Gemini CLI in PATH
    }
  },
  skillExtensions: {
    // Path to a git-tracked dir of team-shared skill extensions, laid out
    // per-skill: <sharedDir>/<skill-dir>/*.md. Empty = shared extensions off
    // (only local .claude/skills/<dir>/extensions/ loads). Relative paths
    // resolve against the project root and must stay inside it; a sibling repo
    // in a multi-repo layout must use an absolute path.
    sharedDir: ''
  },
  graphify: {
    // Knowledge Graph (graphify) is ON by default. This is a code-level default —
    // it is NOT written into .tkm.json; a project only carries a `graphify` key
    // once someone disables it. Turn off via the CLI / .tkm.json (graphify.enabled
    // = false) or env GRAPHIFY_DISABLE=1 / REBUILD_NO_GRAPH=1.
    enabled: true
  },
  memoryGraph: {
    // Memory-graph (tier-auto self-hosted KG memory, plans/260716-1046-memory-graph-tier-auto)
    // is OFF by default — opt-in until the Phase 4 benchmark confirms extraction quality.
    // Turn on via .tkm.json (memoryGraph.enabled = true) or env MEMORY_GRAPH_DISABLE=1 for
    // a hard kill switch regardless of config.
    //
    // Enabling this persists conversation turns to plaintext .md files under
    // memory-graph-out/raw/ (gitignored, but not excluded from local backups/cloud sync/
    // other tools that scan the repo dir). Text is passed through a regex-based secret
    // redactor (claude/hooks/lib/secret-redact.cjs) before it's written, but that's
    // defense in depth, not a guarantee — avoid pasting real credentials into chat.
    enabled: false
  },
  assertions: [],
  statusline: 'full',
  statuslineColors: true,
  statuslineQuota: true,
  hooks: {
    'session-init': true,
    'subagent-init': true,
    'dev-rules-reminder': true,
    'usage-context-awareness': true,
    'context-tracking': true,
    'scout-block': true,
    'privacy-block': true,
    'workflow-opt-in-guard': true,
    'post-edit-simplify-reminder': true,
    'task-completed-handler': true,
    'teammate-idle-handler': true,
    'session-state': true,
    'telemetry': true
  }
};

// ---------------------------------------------------------------------------
// Characters invalid in filenames across platforms
// Windows: < > : " / \ | ? *   macOS/Linux: / + NUL   control chars
// ---------------------------------------------------------------------------
const INVALID_FILENAME_CHARS = /[<>:"/\\|?*\x00-\x1f\x7f]/g;

// ---------------------------------------------------------------------------
// Deep merge
// ---------------------------------------------------------------------------

/**
 * Recursively merge src into dst; src wins on primitives.
 * Arrays: replace entirely — no append, no dedup.
 * Empty object `{}` in src = inherit from dst (no override).
 */
function deepMerge(dst, src) {
  if (!src || typeof src !== 'object') return dst;
  if (!dst || typeof dst !== 'object') return src;

  const out = { ...dst };

  for (const k of Object.keys(src)) {
    const sv = src[k];
    const dv = dst[k];

    if (Array.isArray(sv)) {
      out[k] = [...sv];
    } else if (sv !== null && typeof sv === 'object') {
      if (Object.keys(sv).length === 0) continue; // empty = inherit dst
      out[k] = deepMerge(dv || {}, sv);
    } else {
      out[k] = sv;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Config file I/O
// ---------------------------------------------------------------------------

/**
 * Parse a JSON config file. Returns null when absent, unreadable, or malformed.
 */
function loadConfigFromPath(cfgPath) {
  try {
    if (!fs.existsSync(cfgPath)) return null;
    return JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  } catch (_) {
    return null;
  }
}

/** Silent fallback for deprecated .sk.json — no stderr noise at hook time. */
function _loadLegacy(legacyPath) {
  return loadConfigFromPath(legacyPath);
}

// ---------------------------------------------------------------------------
// Session-state helpers
// ---------------------------------------------------------------------------

/**
 * Temp-file path for a session's state blob (`sk-session-{id}.json`).
 */
function getSessionTempPath(sessionId) {
  return path.join(os.tmpdir(), `sk-session-${sessionId}.json`);
}

/**
 * Read session state. Returns null when file is absent or unreadable.
 */
function readSessionState(sessionId) {
  if (!sessionId) return null;
  const p = getSessionTempPath(sessionId);
  try {
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (_) {
    return null;
  }
}

/**
 * Write session state atomically (write temp → rename) to avoid torn reads.
 */
function writeSessionState(sessionId, state) {
  if (!sessionId) return false;
  const dest = getSessionTempPath(sessionId);
  const tmp  = `${dest}.${Math.random().toString(36).slice(2)}`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
    fs.renameSync(tmp, dest);
    return true;
  } catch (_) {
    try { fs.unlinkSync(tmp); } catch (__) { /* ignore */ }
    return false;
  }
}

// ---------------------------------------------------------------------------
// File-lock for session-state updates
// ---------------------------------------------------------------------------

function _lockPath(sessionId) {
  return `${getSessionTempPath(sessionId)}.lock`;
}

function _busyWait(ms) {
  if (ms <= 0) return;
  if (
    typeof SharedArrayBuffer === 'function' &&
    typeof Atomics === 'object' &&
    typeof Atomics.wait === 'function'
  ) {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
    return;
  }
  // Fallback: busy-wait when Atomics.wait unavailable (Worker without SAB)
  const end = Date.now() + ms;
  while (Date.now() < end) { /* spin */ }
}

function _removeStaleLock(lp, now = Date.now()) {
  try {
    const st = fs.statSync(lp);
    if (now - st.mtimeMs < _LOCK_STALE_MS) return false;
    fs.unlinkSync(lp);
    return true;
  } catch (_) {
    return false;
  }
}

function _acquireLock(sessionId) {
  const lp       = _lockPath(sessionId);
  const deadline = Date.now() + _LOCK_TIMEOUT_MS;

  while (Date.now() <= deadline) {
    try {
      const fd = fs.openSync(lp, 'wx');
      fs.writeFileSync(fd, String(process.pid));
      return { fd, lockPath: lp };
    } catch (err) {
      if (err?.code !== 'EEXIST') return null;
      _removeStaleLock(lp);
      _busyWait(_LOCK_RETRY_MS);
    }
  }
  return null;
}

function _releaseLock(lock) {
  if (!lock) return;
  try { fs.closeSync(lock.fd); }     catch (_) { /* ignore */ }
  try { fs.unlinkSync(lock.lockPath); } catch (_) { /* ignore */ }
}

/**
 * Read-modify-write session state under an exclusive file lock.
 * `updater` is either a partial patch or a function `(state) => nextState`.
 */
function updateSessionState(sessionId, updater) {
  if (!sessionId) return false;

  const lock = _acquireLock(sessionId);
  if (!lock) return false;

  try {
    const current = readSessionState(sessionId) || {};
    const next = typeof updater === 'function'
      ? updater({ ...current })
      : { ...current, ...(updater || {}) };

    if (!next || typeof next !== 'object') return false;
    return writeSessionState(sessionId, next);
  } finally {
    _releaseLock(lock);
  }
}

// ---------------------------------------------------------------------------
// Path utilities
// ---------------------------------------------------------------------------

/**
 * Trim whitespace, strip trailing slashes. Returns null for empty/non-string input.
 */
function normalizePath(val) {
  if (!val || typeof val !== 'string') return null;
  const trimmed = val.trim();
  if (!trimmed) return null;
  const stripped = trimmed.replace(/[/\\]+$/, '');
  return stripped || null;
}

/**
 * Thin wrapper around path.isAbsolute; guards against falsy input.
 */
function isAbsolutePath(val) {
  if (!val) return false;
  return path.isAbsolute(val);
}

/**
 * Sanitize a slug for filesystem use: strip invalid chars, normalize non-alphanumeric
 * to hyphens, collapse runs, trim edges, cap at 100 chars.
 */
function sanitizeSlug(slug) {
  if (!slug || typeof slug !== 'string') return '';
  return slug
    .replace(INVALID_FILENAME_CHARS, '')
    .replace(/[^a-z0-9-]/gi, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 100);
}

/**
 * Sanitize a path value for config use.
 * Allows absolute paths (consolidated plans use case).
 * Blocks null bytes and path-traversal attempts on relative paths.
 */
function sanitizePath(val, projectRoot) {
  const norm = normalizePath(val);
  if (!norm) return null;
  if (/[\x00]/.test(norm)) return null;
  if (isAbsolutePath(norm)) return norm;

  const resolved = path.resolve(projectRoot, norm);
  if (!resolved.startsWith(projectRoot + path.sep) && resolved !== projectRoot) {
    return null; // relative path escaping project root
  }
  return norm;
}

/**
 * Validate and clamp path-shaped fields in a loaded config object.
 */
function sanitizeConfig(cfg, projectRoot) {
  const out = { ...cfg };

  if (out.plan) {
    out.plan = { ...out.plan };
    if (!sanitizePath(out.plan.reportsDir, projectRoot)) {
      out.plan.reportsDir = DEFAULT_CONFIG.plan.reportsDir;
    }
    out.plan.resolution = {
      ...DEFAULT_CONFIG.plan.resolution,
      ...out.plan.resolution
    };
    out.plan.validation = {
      ...DEFAULT_CONFIG.plan.validation,
      ...out.plan.validation
    };
  }

  if (out.paths) {
    out.paths = { ...out.paths };
    if (!sanitizePath(out.paths.docs, projectRoot))  out.paths.docs  = DEFAULT_CONFIG.paths.docs;
    if (!sanitizePath(out.paths.plans, projectRoot)) out.paths.plans = DEFAULT_CONFIG.paths.plans;
  }

  if (out.locale) out.locale = { ...out.locale };

  // Guard shared-extensions dir: reject relative paths escaping the project root.
  // Absolute paths pass through (sibling-repo layouts); invalid → disable (empty).
  if (out.skillExtensions) {
    out.skillExtensions = { ...out.skillExtensions };
    if (out.skillExtensions.sharedDir && !sanitizePath(out.skillExtensions.sharedDir, projectRoot)) {
      out.skillExtensions.sharedDir = '';
    }
  }

  // Guard takumi.sddMode against typos — an unknown value must not silently skip the
  // spec stage AND the first-run prompt (it would match none of the gate branches).
  if (out.takumi) {
    out.takumi = { ...out.takumi };
    const validSddModes = ['ask', 'on', 'off'];
    if (!validSddModes.includes(out.takumi.sddMode)) {
      out.takumi.sddMode = DEFAULT_CONFIG.takumi.sddMode; // 'ask'
    }
  }

  return out;
}

// ---------------------------------------------------------------------------
// Config loading
// ---------------------------------------------------------------------------

/**
 * Build default config, optionally omitting optional sections.
 */
function _buildDefaultConfig(inclProject, inclAssertions, inclLocale) {
  const base = {
    plan:             { ...DEFAULT_CONFIG.plan },
    paths:            { ...DEFAULT_CONFIG.paths },
    docs:             { ...DEFAULT_CONFIG.docs },
    codingLevel:      -1,
    skills:           { ...DEFAULT_CONFIG.skills },
    graphify:         { ...DEFAULT_CONFIG.graphify },
    memoryGraph:      { ...DEFAULT_CONFIG.memoryGraph },
    hooks:            { ...DEFAULT_CONFIG.hooks },
    statusline:       'full',
    statuslineColors: true,
    statuslineQuota:  true,
    trust:            { ...DEFAULT_CONFIG.trust },
    takumi:           { ...DEFAULT_CONFIG.takumi }
  };
  if (inclLocale)     base.locale     = { ...DEFAULT_CONFIG.locale };
  if (inclProject)    base.project    = { ...DEFAULT_CONFIG.project };
  if (inclAssertions) base.assertions = [];
  return base;
}

/**
 * Load config with cascading resolution: DEFAULT → global → local.
 *
 * Priority (each layer wins over the previous):
 *   1. DEFAULT_CONFIG
 *   2. ~/.claude/.tkm.json  (falls back to .sk.json)
 *   3. ./.claude/.tkm.json  (falls back to .sk.json)
 */
function loadConfig(opts = {}) {
  const {
    includeProject    = true,
    includeAssertions = true,
    includeLocale     = true
  } = opts;

  const root = process.cwd();

  const globalCfg = loadConfigFromPath(GLOBAL_CONFIG_PATH) || _loadLegacy(LEGACY_GLOBAL_CONFIG_PATH);
  const localCfg  = loadConfigFromPath(LOCAL_CONFIG_PATH)  || _loadLegacy(LEGACY_LOCAL_CONFIG_PATH);

  if (!globalCfg && !localCfg) {
    return _buildDefaultConfig(includeProject, includeAssertions, includeLocale);
  }

  try {
    let merged = deepMerge({}, DEFAULT_CONFIG);
    if (globalCfg) merged = deepMerge(merged, globalCfg);
    if (localCfg)  merged = deepMerge(merged, localCfg);

    const out = {
      plan:  merged.plan  || DEFAULT_CONFIG.plan,
      paths: merged.paths || DEFAULT_CONFIG.paths,
      docs:  merged.docs  || DEFAULT_CONFIG.docs,
      trust: merged.trust || DEFAULT_CONFIG.trust,
      takumi: merged.takumi || DEFAULT_CONFIG.takumi
    };

    if (includeLocale)     out.locale     = merged.locale     || DEFAULT_CONFIG.locale;
    if (includeProject)    out.project    = merged.project    || DEFAULT_CONFIG.project;
    if (includeAssertions) out.assertions = merged.assertions || [];

    out.codingLevel      = merged.codingLevel ?? -1;
    out.skills           = merged.skills           || DEFAULT_CONFIG.skills;
    out.skillExtensions  = merged.skillExtensions  || DEFAULT_CONFIG.skillExtensions;
    out.graphify         = merged.graphify         || DEFAULT_CONFIG.graphify;
    out.memoryGraph      = merged.memoryGraph      || DEFAULT_CONFIG.memoryGraph;
    out.hooks            = merged.hooks            || DEFAULT_CONFIG.hooks;
    out.statusline       = merged.statusline       || 'full';
    out.statuslineColors = merged.statuslineColors ?? true;
    out.statuslineQuota  = merged.statuslineQuota  ?? true;
    out.statuslineLayout = merged.statuslineLayout || undefined;

    return sanitizeConfig(out, root);
  } catch (_) {
    return _buildDefaultConfig(includeProject, includeAssertions, includeLocale);
  }
}

// ---------------------------------------------------------------------------
// Shell / env helpers
// ---------------------------------------------------------------------------

/**
 * Escape shell special characters in a value destined for an env file.
 * Handles: backslash, double-quote, dollar, backtick.
 */
function escapeShellValue(str) {
  if (typeof str !== 'string') return str;
  return str
    .replace(/\\/g,  '\\\\')
    .replace(/"/g,   '\\"')
    .replace(/\$/g,  '\\$')
    .replace(/`/g,   '\\`');
}

/**
 * Append `export KEY="value"` to CLAUDE_ENV_FILE (escaped).
 */
function writeEnv(envFile, key, value) {
  if (envFile && value !== null && value !== undefined) {
    fs.appendFileSync(envFile, `export ${key}="${escapeShellValue(String(value))}"\n`);
  }
}

// ---------------------------------------------------------------------------
// Git helpers
// ---------------------------------------------------------------------------

const _GIT_TIMEOUT_MS = 5000;

/**
 * Execute a whitelisted git read command; prevents shell injection.
 * Returns stdout string or null on failure / unknown command.
 */
function _gitExec(cmd, opts = {}) {
  const registry = {
    'git branch --show-current':          ['git', ['branch', '--show-current']],
    'git rev-parse --abbrev-ref HEAD':    ['git', ['rev-parse', '--abbrev-ref', 'HEAD']],
    'git rev-parse --show-toplevel':      ['git', ['rev-parse', '--show-toplevel']]
  };

  const spec = registry[cmd];
  if (!spec) return null;

  const [bin, args] = spec;
  const { cwd = undefined, timeout = _GIT_TIMEOUT_MS } = opts;

  try {
    return execFileSync(bin, args, {
      encoding: 'utf8',
      timeout,
      cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true
    }).trim();
  } catch (_) {
    return null;
  }
}

/** Return current git branch name, or null if not in a repo / on HEAD. */
function getGitBranch(cwd = null) {
  return _gitExec('git branch --show-current', { cwd: cwd || undefined });
}

/** Return the git repository root as an absolute path, or null. */
function getGitRoot(cwd = null) {
  return _gitExec('git rev-parse --show-toplevel', { cwd: cwd || undefined });
}

// ---------------------------------------------------------------------------
// Branch parsing
// ---------------------------------------------------------------------------

/**
 * Extract feature slug from a branch name using the configured pattern.
 * Default: `(?:feat|fix|chore|refactor|docs)/(?:[^/]+/)?(.+)`
 */
function extractSlugFromBranch(branch, pattern) {
  if (!branch) return null;
  const rx = pattern
    ? new RegExp(pattern)
    : /(?:feat|fix|chore|refactor|docs)\/(?:[^\/]+\/)?(.+)/;
  const m = branch.match(rx);
  return m ? sanitizeSlug(m[1]) : null;
}

/**
 * Extract numeric issue ID from a branch name.
 * Tries several common patterns in priority order.
 */
function extractIssueFromBranch(branch) {
  if (!branch) return null;
  const patterns = [
    /(?:issue|gh|fix|feat|bug)[/-]?(\d+)/i,
    /[/-](\d+)[/-]/,
    /#(\d+)/
  ];
  for (const rx of patterns) {
    const m = branch.match(rx);
    if (m) return m[1];
  }
  return null;
}

// ---------------------------------------------------------------------------
// Plan directory helpers
// ---------------------------------------------------------------------------

/**
 * Return the most recent timestamped plan directory, or null.
 * Directories are expected to start with a 6-digit date prefix (YYMMDD…).
 */
function findMostRecentPlan(plansDir) {
  try {
    if (!fs.existsSync(plansDir)) return null;
    const dirs = fs.readdirSync(plansDir, { withFileTypes: true })
      .filter(e => e.isDirectory() && /^\d{6}/.test(e.name))
      .map(e => e.name)
      .sort()
      .reverse();
    return dirs.length > 0 ? path.join(plansDir, dirs[0]) : null;
  } catch (_) {
    return null;
  }
}

/**
 * Resolve the active plan path via cascading lookup.
 *
 * - `'session'` → explicitly set via set-active-plan.cjs → ACTIVE (directive)
 * - `'branch'`  → matched from git branch name → SUGGESTED (hint only)
 *
 * `'mostRecent'` was removed — caused stale-plan pollution across sessions.
 *
 * @returns {{ path: string|null, resolvedBy: 'session'|'branch'|null }}
 */
function resolvePlanPath(sessionId, config) {
  const plansDir      = config?.paths?.plans || 'plans';
  const resolution    = config?.plan?.resolution || {};
  const order         = resolution.order || ['session', 'branch'];
  const branchPattern = resolution.branchPattern;

  for (const method of order) {
    if (method === 'session') {
      const state = readSessionState(sessionId);
      if (state?.activePlan) {
        let p = state.activePlan;
        // Absolute paths (new set-active-plan.cjs) used as-is;
        // legacy relative paths resolved against sessionOrigin when available.
        if (!path.isAbsolute(p) && state.sessionOrigin) {
          p = path.join(state.sessionOrigin, p);
        }
        return { path: p, resolvedBy: 'session' };
      }
      continue;
    }

    if (method === 'branch') {
      try {
        const branch = _gitExec('git branch --show-current');
        const slug   = extractSlugFromBranch(branch, branchPattern);
        if (slug && fs.existsSync(plansDir)) {
          const matches = fs.readdirSync(plansDir, { withFileTypes: true })
            .filter(e => e.isDirectory() && e.name.includes(slug));
          if (matches.length > 0) {
            return {
              path:       path.join(plansDir, matches[matches.length - 1].name),
              resolvedBy: 'branch'
            };
          }
        }
      } catch (_) {
        // plans dir unreadable — skip
      }
      continue;
    }
    // 'mostRecent' is intentionally unsupported — stale-plan hazard
  }

  return { path: null, resolvedBy: null };
}

/**
 * Derive the reports path for a resolved plan.
 *
 * Only session-active plans get plan-scoped report paths.
 * Branch-suggested plans and no-plan cases fall back to `plans/reports/`.
 */
function getReportsPath(planPath, resolvedBy, planConfig, pathsConfig, baseDir = null) {
  const reportsDir = normalizePath(planConfig?.reportsDir) || 'reports';
  const plansDir   = normalizePath(pathsConfig?.plans)     || 'plans';

  // Session-resolved plan → write into its own reports subfolder.
  // Validate normalized path to prevent whitespace-only paths creating invalid dirs.
  const activePlanPath = (planPath && resolvedBy === 'session')
    ? normalizePath(planPath)
    : null;

  const reportPath = activePlanPath
    ? `${activePlanPath}/${reportsDir}`
    : `${plansDir}/${reportsDir}`;

  if (baseDir) {
    // If reportPath is already absolute (absolute planPath case), don't re-join with baseDir
    return path.isAbsolute(reportPath) ? reportPath : path.join(baseDir, reportPath);
  }
  return reportPath + '/';
}

// ---------------------------------------------------------------------------
// Date / naming-pattern utilities
// ---------------------------------------------------------------------------

/**
 * Format a date string from a pattern of tokens: YYYY YY MM DD HH mm ss.
 */
function formatDate(fmt) {
  const n   = new Date();
  const pad = (v, len = 2) => String(v).padStart(len, '0');

  const map = {
    YYYY: n.getFullYear(),
    YY:   String(n.getFullYear()).slice(-2),
    MM:   pad(n.getMonth() + 1),
    DD:   pad(n.getDate()),
    HH:   pad(n.getHours()),
    mm:   pad(n.getMinutes()),
    ss:   pad(n.getSeconds())
  };

  let out = fmt;
  for (const [tok, val] of Object.entries(map)) {
    out = out.replace(tok, val);
  }
  return out;
}

/** Format an issue ID, prepending the configured prefix (or `#` as default). */
function formatIssueId(issueId, planConfig) {
  if (!issueId) return null;
  return planConfig.issuePrefix
    ? `${planConfig.issuePrefix}${issueId}`
    : `#${issueId}`;
}

/**
 * Validate that a resolved naming pattern is usable as a directory name.
 * Pattern must contain `{slug}` and must not have other unresolved placeholders.
 */
function validateNamingPattern(pattern) {
  if (!pattern || typeof pattern !== 'string') {
    return { valid: false, error: 'Pattern is empty or not a string' };
  }

  const withoutSlug = pattern
    .replace(/\{slug\}/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');

  if (!withoutSlug) {
    return { valid: false, error: 'Pattern resolves to empty after removing {slug}' };
  }

  const stray = withoutSlug.match(/\{[^}]+\}/);
  if (stray) {
    return { valid: false, error: `Unresolved placeholder: ${stray[0]}` };
  }

  if (!pattern.includes('{slug}')) {
    return { valid: false, error: 'Pattern must contain {slug} placeholder' };
  }

  return { valid: true };
}

/**
 * Resolve naming pattern tokens ({date}, {issue}) while keeping {slug} as
 * a live placeholder for agents to substitute at plan-creation time.
 *
 * Example: "{date}-{issue}-{slug}", dateFormat="YYMMDD-HHmm", issue="GH-88"
 *   → "251212-1830-GH-88-{slug}"  (issue present)
 *   → "251212-1830-{slug}"         (no issue)
 */
function resolveNamingPattern(planConfig, gitBranch) {
  const { namingFormat, dateFormat, issuePrefix } = planConfig;

  const dateStr  = formatDate(dateFormat);
  const issueNum = extractIssueFromBranch(gitBranch);
  const fullIssue = (issueNum && issuePrefix) ? `${issuePrefix}${issueNum}` : null;

  let pat = namingFormat.replace('{date}', dateStr);

  if (fullIssue) {
    pat = pat.replace('{issue}', fullIssue);
  } else {
    pat = pat.replace(/-?\{issue\}-?/, '-').replace(/--+/g, '-');
  }

  // Tidy up: trim edge hyphens, normalise runs around {slug}
  pat = pat
    .replace(/^-+/, '')
    .replace(/-+$/, '')
    .replace(/-+(\{slug\})/g, '-$1')
    .replace(/(\{slug\})-+/g, '$1-')
    .replace(/--+/g, '-');

  const check = validateNamingPattern(pat);
  if (!check.valid && process.env.TKM_DEBUG) {
    console.error(`[tkm-config] Warning: ${check.error}`);
  }

  return pat;
}

// ---------------------------------------------------------------------------
// Misc utilities
// ---------------------------------------------------------------------------

/**
 * Extract the task-list ID (plan directory name) from a resolution result.
 * Only defined for session-resolved plans; branch-suggested plans return null.
 */
function extractTaskListId(resolved) {
  if (!resolved || resolved.resolvedBy !== 'session' || !resolved.path) return null;
  return path.basename(resolved.path);
}

/**
 * Check whether a hook is enabled in the current config.
 * Defaults to true when the hook key is absent.
 */
function isHookEnabled(hookName) {
  const cfg = loadConfig({ includeProject: false, includeAssertions: false, includeLocale: false });
  return (cfg.hooks || {})[hookName] !== false;
}

/**
 * Whether the graphify Knowledge Graph is enabled. ON by default.
 * Env hard-off (GRAPHIFY_DISABLE / REBUILD_NO_GRAPH) wins; otherwise the first config
 * file that defines `graphify.enabled` — local .takumi.json (what the tkm CLI /
 * `tkm graphify` writes) → local .tkm.json → global .takumi.json → global .tkm.json;
 * else default true. Reading .takumi.json here (rather than only the kit-native
 * .tkm.json) is scoped to this KG toggle so the `tkm graphify` command takes effect
 * without a broader config-file migration.
 */
function _graphifyEnabledFromFile(p) {
  try {
    const c = JSON.parse(fs.readFileSync(p, 'utf8'));
    const g = c && c.graphify;
    if (g && typeof g === 'object' && 'enabled' in g) return g.enabled !== false;
  } catch (_) { /* absent / unreadable / malformed → undefined */ }
  return undefined;
}

function isGraphifyEnabled() {
  if (process.env.GRAPHIFY_DISABLE === '1' || process.env.REBUILD_NO_GRAPH === '1') return false;
  const home = os.homedir();
  const candidates = [
    path.join(process.cwd(), '.claude', '.takumi.json'),
    path.join(process.cwd(), '.claude', '.tkm.json'),
    path.join(home, '.claude', '.takumi.json'),
    path.join(home, '.claude', '.tkm.json'),
  ];
  for (const p of candidates) {
    const v = _graphifyEnabledFromFile(p);
    if (v !== undefined) return v;
  }
  return true;
}

function _memoryGraphEnabledFromFile(p) {
  try {
    const c = JSON.parse(fs.readFileSync(p, 'utf8'));
    const g = c && c.memoryGraph;
    if (g && typeof g === 'object' && 'enabled' in g) return g.enabled !== false;
  } catch (_) { /* absent / unreadable / malformed → undefined */ }
  return undefined;
}

/**
 * Whether the memory-graph (tier-auto self-hosted KG memory) Stop-hook queue writer is
 * enabled. OFF by default — mirrors isGraphifyEnabled()'s file-resolution shape, but the
 * fallback is false, not true: this is opt-in until the Phase 4 benchmark lands
 * (plans/260716-1046-memory-graph-tier-auto).
 */
function isMemoryGraphEnabled() {
  if (process.env.MEMORY_GRAPH_DISABLE === '1') return false;
  const home = os.homedir();
  const candidates = [
    path.join(process.cwd(), '.claude', '.tkm.json'),
    path.join(home, '.claude', '.tkm.json'),
  ];
  for (const p of candidates) {
    const v = _memoryGraphEnabledFromFile(p);
    if (v !== undefined) return v;
  }
  return false;
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  CONFIG_PATH,
  LOCAL_CONFIG_PATH,
  GLOBAL_CONFIG_PATH,
  LEGACY_LOCAL_CONFIG_PATH,
  LEGACY_GLOBAL_CONFIG_PATH,
  DEFAULT_CONFIG,
  INVALID_FILENAME_CHARS,
  deepMerge,
  loadConfigFromPath,
  loadConfig,
  normalizePath,
  isAbsolutePath,
  sanitizePath,
  sanitizeSlug,
  sanitizeConfig,
  escapeShellValue,
  writeEnv,
  getSessionTempPath,
  readSessionState,
  writeSessionState,
  updateSessionState,
  resolvePlanPath,
  extractSlugFromBranch,
  findMostRecentPlan,
  getReportsPath,
  formatIssueId,
  extractIssueFromBranch,
  formatDate,
  validateNamingPattern,
  resolveNamingPattern,
  getGitBranch,
  getGitRoot,
  extractTaskListId,
  isHookEnabled,
  isGraphifyEnabled,
  isMemoryGraphEnabled
};
