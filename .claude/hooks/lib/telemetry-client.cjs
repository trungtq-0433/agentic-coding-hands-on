/**
 * Telemetry and feedback HTTP client — shared lib, no event firing.
 *
 * Called by:
 *   - /tkm:feedback command   → sendFeedback()
 *   - /tkm:rate command (P5)  → sendRating()
 *   - Stop hook telemetry flush (P4) → sendTelemetryBatch()
 *
 * Every exported function is fire-and-forget: resolves to
 * { ok: boolean, status?: number }, never throws. Failures go to stderr;
 * the hook process always continues.
 *
 * Endpoint resolution order:
 *   1. TKM_TELEMETRY_ENDPOINT + TKM_TELEMETRY_DEV=1 — dev override so
 *      engineers can aim /tkm:feedback at a local server without polluting
 *      production data.
 *   2. metadata.json telemetry_endpoint — authoritative for end-user installs;
 *      a stale env var cannot silently hijack traffic.
 *   3. TKM_TELEMETRY_ENDPOINT alone — fallback when no kit is installed yet.
 *   4. __TKM_DEFAULT_ENDPOINT__ baked at release time.
 *
 * cwd_hash = sha256(git remote origin || absolute cwd) — one-way project id.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { resolveGithubUser } = require('./user-identity.cjs');

const DEFAULT_TIMEOUT_MS = 5000;
const MAX_FEEDBACK_CHARS = 2000;
const MAX_RATING_COMMENT_CHARS = 500;
const ALLOWED_RATING_MILESTONES = new Set(['takumi', 'ship', 'plan']);

// Baked at release time. In source both the assignment and the sentinel hold
// the literal placeholder; the release step rewrites ONLY the assignment,
// leaving the sentinel intact so bakedEndpoint() can detect an unbaked build.
const BAKED_ENDPOINT_SENTINEL = '__TKM_DEFAULT_ENDPOINT__';
const BAKED_ENDPOINT = '__TKM_DEFAULT_ENDPOINT__';

function bakedEndpoint() {
  return BAKED_ENDPOINT && BAKED_ENDPOINT !== BAKED_ENDPOINT_SENTINEL
    ? BAKED_ENDPOINT.replace(/\/+$/, '')
    : null;
}

/* ─── Config resolution ────────────────────────────────────────────────── */

// Search order for metadata.json:
//   1. cwd walk — project-local .claude/ wins; a project's kit config always
//      beats a shared plugin or stale global config.
//   2. $CLAUDE_PLUGIN_ROOT — set by Claude Code for plugin-mode invocations
//      where the user's cwd has no .claude/ of its own.
//   3. ~/.claude/metadata.json — user-global last resort.
// Falls through only when a tier produces no file on disk.
function findMetadataJson(cwd = process.cwd()) {
  let dir = cwd;
  for (let i = 0; i < 6; i++) {
    const candidate = path.join(dir, '.claude', 'metadata.json');
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;
  if (pluginRoot) {
    const pluginMeta = path.join(pluginRoot, '.claude', 'metadata.json');
    if (fs.existsSync(pluginMeta)) return pluginMeta;
  }

  const globalMeta = path.join(os.homedir(), '.claude', 'metadata.json');
  return fs.existsSync(globalMeta) ? globalMeta : null;
}

// Returns parsed metadata, or { __readError: string } on read/parse failure.
// Callers distinguish parse error from "no file" rather than collapsing both to null.
function readMetadata(cwd) {
  const metaPath = findMetadataJson(cwd);
  if (!metaPath) return null;
  try {
    return JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  } catch (e) {
    return { __readError: `${metaPath}: ${e?.message || String(e)}` };
  }
}

function metadataReadError(cwd) {
  const m = readMetadata(cwd);
  return m && m.__readError ? m.__readError : null;
}

function isDevGateEnabled() {
  return process.env.TKM_TELEMETRY_DEV === '1';
}

function readEndpoint(cwd) {
  const envEndpoint = process.env.TKM_TELEMETRY_ENDPOINT;
  const meta = readMetadata(cwd);
  const fromMeta = meta?.telemetry_endpoint;
  // Precedence: env+dev-gate > metadata > env-fallback > baked > null
  if (envEndpoint && isDevGateEnabled()) return envEndpoint.replace(/\/+$/, '');
  if (fromMeta) return fromMeta.replace(/\/+$/, '');
  if (envEndpoint) return envEndpoint.replace(/\/+$/, '');
  return bakedEndpoint();
}

// Mirrors readEndpoint precedence. Used on POST failure to show which source
// produced the URL — useful when a leaked TKM_TELEMETRY_ENDPOINT from a shell
// rc / VSCode env / launchctl plist is misdirecting traffic.
function resolveEndpointSource(cwd) {
  const envEndpoint = process.env.TKM_TELEMETRY_ENDPOINT;
  const meta = readMetadata(cwd);
  const fromMeta = meta?.telemetry_endpoint;
  if (envEndpoint && isDevGateEnabled()) return 'env-override';
  if (fromMeta) return 'metadata';
  if (envEndpoint) return 'env-fallback';
  if (bakedEndpoint()) return 'baked-default';
  return 'none';
}

function readSkVersion(cwd) {
  const meta = readMetadata(cwd);
  return meta?.version || null;
}

/* ─── Cwd hash ─────────────────────────────────────────────────────────── */

function getGitRemote(cwd) {
  try {
    const out = execFileSync('git', ['-C', cwd, 'remote', 'get-url', 'origin'], {
      encoding: 'utf8',
      timeout: 1000,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
    });
    return (out || '').trim() || null;
  } catch (_) {
    return null;
  }
}

function buildCwdHash(cwd = process.cwd()) {
  const input = getGitRemote(cwd) || path.resolve(cwd);
  return crypto.createHash('sha256').update(input).digest('hex');
}

/* ─── HTTP post ────────────────────────────────────────────────────────── */

/**
 * POST with timeout. Returns { ok, status, error }. Never throws.
 * Silent on success; writes to stderr on any failure.
 */
async function post(urlStr, payload, { version, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  if (!urlStr) return { ok: false, error: 'no_endpoint' };

  let body;
  try {
    body = JSON.stringify(payload);
  } catch (e) {
    return { ok: false, error: `serialize_failed: ${e.message}` };
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(urlStr, {
      method: 'POST',
      body,
      headers: {
        'content-type': 'application/json',
        'X-TKM-Client': `agent-kit/${version || 'unknown'}`,
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    return { ok: resp.ok, status: resp.status };
  } catch (e) {
    clearTimeout(timer);
    const error = e?.name === 'AbortError' ? 'timeout' : (e?.message || String(e));
    process.stderr.write(`[telemetry] POST ${urlStr} failed: ${error}\n`);
    return { ok: false, error };
  }
}

/* ─── Payload builders ─────────────────────────────────────────────────── */

function truncate(s, max) {
  if (typeof s !== 'string') return '';
  return s.length <= max ? s : s.slice(0, max);
}

function assembleBase({ sessionId, skVersion, cwd, cacheFile }) {
  return {
    github_login: resolveGithubUser(cacheFile ? { cacheFile } : undefined) || null,
    session_id: sessionId || null,
    sk_version: skVersion || readSkVersion(cwd) || null,
    cwd_hash: buildCwdHash(cwd),
    ts: new Date().toISOString(),
  };
}

function writeNoEndpointDiag(cwd) {
  const metaPath = findMetadataJson(cwd) || '(none)';
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || '(unset)';
  const envEndpoint = process.env.TKM_TELEMETRY_ENDPOINT ? '(set)' : '(unset)';
  const readErr = metadataReadError(cwd);
  const m = readMetadata(cwd);
  const hasEndpoint = m && !m.__readError && !!m.telemetry_endpoint;
  process.stderr.write(
    `[telemetry] no_endpoint diagnostics:\n` +
      `  cwd=${cwd}\n` +
      `  CLAUDE_PLUGIN_ROOT=${pluginRoot}\n` +
      `  TKM_TELEMETRY_ENDPOINT=${envEndpoint}\n` +
      `  resolved metadata_path=${metaPath}\n` +
      `  metadata has telemetry_endpoint=${hasEndpoint ? 'yes' : 'no'}\n` +
      (readErr ? `  read_error=${readErr}\n` : ''),
  );
}

async function sendFeedback({ text, sessionId, skVersion, cwd = process.cwd(), cacheFile } = {}) {
  const endpoint = readEndpoint(cwd);
  if (!endpoint) {
    writeNoEndpointDiag(cwd);
    return { ok: false, error: 'no_endpoint' };
  }

  const trimmed = truncate((text || '').trim(), MAX_FEEDBACK_CHARS);
  if (!trimmed) return { ok: false, error: 'empty_text' };

  const base = assembleBase({ sessionId, skVersion, cwd, cacheFile });
  if (!base.github_login) return { ok: false, error: 'no_github_login' };

  const version = skVersion || readSkVersion(cwd);
  const payload = { ...base, text: trimmed };
  const result = await post(`${endpoint}/feedback`, payload, { version });
  if (!result.ok) {
    process.stderr.write(
      `[telemetry] endpoint=${endpoint} (source=${resolveEndpointSource(cwd)})\n`,
    );
  }
  return result;
}

function normalizeScore(raw) {
  // Accept numeric string or integer; reject anything non-integer or outside 0..3.
  if (raw === null || raw === undefined) return null;
  if (typeof raw === 'string' && raw.trim() === '') return null;
  const n = typeof raw === 'number' ? raw : Number(String(raw).trim());
  if (!Number.isFinite(n) || !Number.isInteger(n)) return null;
  if (n < 0 || n > 3) return null;
  return n;
}

async function sendRating({ score, comment, sessionId, milestone, skVersion, cwd = process.cwd(), cacheFile } = {}) {
  const endpoint = readEndpoint(cwd);
  if (!endpoint) {
    writeNoEndpointDiag(cwd);
    return { ok: false, error: 'no_endpoint' };
  }

  const normalizedScore = normalizeScore(score);
  if (normalizedScore === null) return { ok: false, error: 'invalid_score' };

  const base = assembleBase({ sessionId, skVersion, cwd, cacheFile });
  if (!base.github_login) return { ok: false, error: 'no_github_login' };

  const version = skVersion || readSkVersion(cwd);
  const trimmedComment = truncate((comment || '').trim(), MAX_RATING_COMMENT_CHARS);
  const milestoneValue = ALLOWED_RATING_MILESTONES.has(milestone) ? milestone : null;

  const payload = {
    ...base,
    score: normalizedScore,
    comment: trimmedComment || null,
    milestone: milestoneValue,
  };
  const result = await post(`${endpoint}/rating`, payload, { version });
  if (!result.ok) {
    process.stderr.write(
      `[telemetry] endpoint=${endpoint} (source=${resolveEndpointSource(cwd)})\n`,
    );
  }
  return result;
}

/* ─── CLI entry ────────────────────────────────────────────────────────── */

function parseArgs(argv) {
  const args = { _: [] };
  for (const raw of argv) {
    const m = raw.match(/^--([^=]+)=(.*)$/);
    if (m) {
      args[m[1]] = m[2];
    } else if (raw.startsWith('--')) {
      args[raw.slice(2)] = true;
    } else {
      args._.push(raw);
    }
  }
  return args;
}

async function runCli(argv) {
  const subcommand = argv[0];
  const args = parseArgs(argv.slice(1));

  if (subcommand === 'send-feedback') {
    const result = await sendFeedback({
      text: args.text || '',
      sessionId: args['session-id'] || null,
      skVersion: args['sk-version'] || null,
    });
    // Compact JSON status line — parseable by the calling command or agent.
    process.stdout.write(`${JSON.stringify(result)}\n`);
    process.exit(result.ok ? 0 : 1);
  }

  if (subcommand === 'send-rating') {
    const result = await sendRating({
      score: args.score,
      comment: args.comment || '',
      sessionId: args['session-id'] || null,
      skVersion: args['sk-version'] || null,
      milestone: args.milestone || null,
    });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    process.exit(result.ok ? 0 : 1);
  }

  if (subcommand === 'diagnose') {
    const cwd = process.cwd();
    const metaPath = findMetadataJson(cwd);
    const m = readMetadata(cwd);
    const readErr = m && m.__readError ? m.__readError : null;
    const out = {
      cwd,
      CLAUDE_PLUGIN_ROOT: process.env.CLAUDE_PLUGIN_ROOT || null,
      TKM_TELEMETRY_ENDPOINT_env_set: !!process.env.TKM_TELEMETRY_ENDPOINT,
      TKM_TELEMETRY_DEV: process.env.TKM_TELEMETRY_DEV || null,
      resolved_metadata_path: metaPath,
      read_error: readErr,
      metadata_keys: m && !m.__readError ? Object.keys(m) : null,
      telemetry_endpoint_in_metadata: m && !m.__readError ? m.telemetry_endpoint || null : null,
      resolved_endpoint: readEndpoint(cwd),
      resolved_endpoint_source: resolveEndpointSource(cwd),
      baked_endpoint_set: !!bakedEndpoint(),
    };
    process.stdout.write(`${JSON.stringify(out, null, 2)}\n`);
    process.exit(0);
  }

  process.stderr.write(`Unknown subcommand: ${subcommand}\n`);
  process.exit(2);
}

if (require.main === module) {
  runCli(process.argv.slice(2)).catch((e) => {
    process.stderr.write(`[telemetry] cli crash: ${e?.message || e}\n`);
    process.exit(1);
  });
}

module.exports = {
  DEFAULT_TIMEOUT_MS,
  MAX_FEEDBACK_CHARS,
  MAX_RATING_COMMENT_CHARS,
  ALLOWED_RATING_MILESTONES,
  BAKED_ENDPOINT_SENTINEL,
  buildCwdHash,
  findMetadataJson,
  readEndpoint,
  resolveEndpointSource,
  readSkVersion,
  readMetadata,
  metadataReadError,
  bakedEndpoint,
  assembleBase,
  truncate,
  post,
  sendFeedback,
  sendRating,
  normalizeScore,
  parseArgs,
};
