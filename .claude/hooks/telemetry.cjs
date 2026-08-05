#!/usr/bin/env node
/**
 * Telemetry hook — multi-event capture with Stop-time flush.
 *
 * Wired in hooks.json for four events:
 *   SessionStart      → delete orphan buffers older than 24 h (no flush — see below)
 *   UserPromptSubmit  → append to buffer for /tkm: commands only
 *   PostToolUse       → append tool / agent / skill events to buffer
 *   Stop              → read buffer, POST to /api/telemetry, delete file
 *
 * Per-session buffer: ~/.claude/sk-events/{sessionId}.jsonl (append-only).
 * The buffer file name is derived from session_id after sanitising to a
 * UUID-ish alphabet; path traversal cannot escape BUFFER_DIR.
 *
 * Privacy invariant: prompt text, file paths, branch names, and env vars are
 * never written. Only safe fields enter the buffer: command name (the token
 * after /tkm:), tool name, and subagent_type.
 *
 * Orphan buffers (>24 h, no matching Stop) are deleted, not flushed — the
 * file alone lacks session metadata (start time, token counts, milestone) so
 * a late flush would produce a misleading sessions row.
 *
 * Fail-open: always exits 0. Errors land in .logs/hook-log.jsonl.
 * Non-Stop events target <50 ms (append-only, no network).
 * Stop runs async fire-and-forget per hooks.json; POST is best-effort.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const { isHookEnabled, readSessionState } = require('./lib/tkm-config-utils.cjs');
const { logHookCrash, createHookTimer } = require('./lib/hook-logger.cjs');
const { post, readEndpoint, readSkVersion, buildCwdHash } = require('./lib/telemetry-client.cjs');
const { resolveGithubUser } = require('./lib/user-identity.cjs');
const { recentlyPrompted, persistLastShown, DEFAULT_THROTTLE_FILE } = require('./lib/rate-throttle.cjs');

const BUFFER_DIR = path.join(os.homedir(), '.claude', 'sk-events');
const MAX_PAYLOAD_BYTES = 10 * 1024;
const ORPHAN_AGE_MS = 24 * 60 * 60 * 1000;
const TKM_COMMAND_PREFIX = '/tkm:';
const RATING_SAMPLE_RATE = 0.07;
const RATING_PROMPT_TEXT =
  '⭐ Rate this session with `/tkm:rate <0|1|2|3> [optional comment]` ' +
  '(0=Chưa hiệu quả, 1=Bình thường, 2=Có ích, 3=Rất hữu ích). ' +
  'Only surface this to the user if the session clearly reached a milestone.';

/* ─── Buffer helpers ──────────────────────────────────────────────────── */

// session_id arrives from Claude stdin — normally well-formed, but we sanitise
// to a UUID-ish alphabet so no unexpected shape can path-traverse out of BUFFER_DIR.
function safeSessionSegment(sessionId) {
  if (typeof sessionId !== 'string' || !sessionId) return null;
  const cleaned = sessionId.replace(/[^a-zA-Z0-9._-]/g, '');
  return cleaned.length > 0 ? cleaned.slice(0, 128) : null;
}

function bufferFileFor(sessionId) {
  const segment = safeSessionSegment(sessionId) || 'unknown';
  return path.join(BUFFER_DIR, `${segment}.jsonl`);
}

function appendEvent(sessionId, event) {
  if (!sessionId) return;
  try {
    fs.mkdirSync(BUFFER_DIR, { recursive: true });
    fs.appendFileSync(bufferFileFor(sessionId), `${JSON.stringify(event)}\n`);
  } catch (_) {
    // Swallow — telemetry append errors must never surface to the session.
  }
}

function readBufferEvents(sessionId) {
  try {
    const raw = fs.readFileSync(bufferFileFor(sessionId), 'utf8');
    return raw
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        try { return JSON.parse(line); } catch { return null; }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

function deleteBuffer(sessionId) {
  try { fs.unlinkSync(bufferFileFor(sessionId)); } catch { /* ignore */ }
}

/* ─── Payload cap ─────────────────────────────────────────────────────── */

function capEvents(events) {
  // Drop oldest events first until the serialised payload fits MAX_PAYLOAD_BYTES.
  let working = events.slice();
  while (working.length > 0 && JSON.stringify(working).length > MAX_PAYLOAD_BYTES) {
    working = working.slice(1);
  }
  return working;
}

/* ─── Event extractors (safe field allowlist) ─────────────────────────── */

function extractSkCommand(prompt) {
  if (typeof prompt !== 'string' || !prompt.startsWith(TKM_COMMAND_PREFIX)) return null;
  const head = prompt.split(/\s+/)[0] || '';
  // Accept only slug-safe characters — no paths, no injected text.
  return /^\/tkm:[a-z][a-z0-9-]*$/i.test(head) ? head : null;
}

const MAX_EVENT_NAME_LEN = 120;

function capName(name) {
  return typeof name === 'string' ? name.slice(0, MAX_EVENT_NAME_LEN) : '';
}

function classifyTool(toolName, toolInput) {
  if (toolName === 'Task') {
    const subagent = typeof toolInput?.subagent_type === 'string' ? toolInput.subagent_type : null;
    return { event_type: 'agent', event_name: capName(subagent) || 'unknown' };
  }
  if (toolName === 'Skill') {
    const skillName = typeof toolInput?.skill === 'string' ? toolInput.skill : null;
    return { event_type: 'skill', event_name: capName(skillName) || 'unknown' };
  }
  if (typeof toolName === 'string' && toolName) {
    return { event_type: 'tool', event_name: capName(toolName) };
  }
  return null;
}

/* ─── Per-event handlers ──────────────────────────────────────────────── */

function handleUserPromptSubmit(data) {
  const command = extractSkCommand(data?.prompt);
  if (!command) return;
  appendEvent(data.session_id, {
    event_type: 'command',
    event_name: command,
    ts: new Date().toISOString(),
  });
}

function handlePostToolUse(data) {
  const classified = classifyTool(data?.tool_name, data?.tool_input);
  if (!classified) return;
  appendEvent(data.session_id, {
    ...classified,
    ts: new Date().toISOString(),
  });
}

function readMilestone(sessionId) {
  try {
    const state = readSessionState(sessionId);
    const kind = state?.milestone_completed;
    if (kind === 'takumi' || kind === 'ship' || kind === 'plan') return kind;
    return null;
  } catch {
    return null;
  }
}

function shouldSampleRating({ rng = Math.random, forceEnv = process.env.TKM_RATING_FORCE } = {}) {
  if (forceEnv === '1' || forceEnv === 'true') return true;
  return rng() < RATING_SAMPLE_RATE;
}

// Writes an additionalContext line so Claude Code can surface the `/tkm:rate` prompt.
// Per-login throttle (24 h) via rate-throttle.cjs prevents repeat nudges.
function maybeEmitRatingPrompt({
  sessionId,
  githubLogin,
  rng,
  stateFile = DEFAULT_THROTTLE_FILE,
  now = Date.now(),
} = {}) {
  if (!sessionId || !githubLogin) return { emitted: false, reason: 'missing_identity' };
  const milestone = readMilestone(sessionId);
  if (!milestone) return { emitted: false, reason: 'no_milestone' };
  if (recentlyPrompted(githubLogin, stateFile, undefined, now)) {
    return { emitted: false, reason: 'throttled' };
  }
  if (!shouldSampleRating({ rng })) return { emitted: false, reason: 'not_sampled' };

  const prompt = { additionalContext: `${RATING_PROMPT_TEXT} (milestone: ${milestone})` };
  try {
    process.stdout.write(`${JSON.stringify(prompt)}\n`);
  } catch {
    return { emitted: false, reason: 'stdout_write_failed' };
  }
  persistLastShown(githubLogin, stateFile, now);
  return { emitted: true, milestone };
}

async function handleStop(data) {
  const sessionId = data?.session_id;
  if (!sessionId) return;

  const cwd = process.cwd();
  const endpoint = readEndpoint(cwd);
  // Tighter timeout here — the process may be reaped before the default 2 s elapses.
  // Cache-hit (the common case) returns instantly regardless.
  const githubLogin = resolveGithubUser({ timeoutMs: 1000 });

  // Delete buffer unconditionally — don't leave orphans if POST fails.
  const events = capEvents(readBufferEvents(sessionId));
  deleteBuffer(sessionId);

  // Session state (written by /tkm:takumi etc.) is authoritative for milestone;
  // stdin data.milestone is a fallback Claude Code does not currently populate.
  const milestone = readMilestone(sessionId) || (typeof data?.milestone === 'string' ? data.milestone : null);

  // Rating prompt fires regardless of whether the POST succeeds — users without
  // a configured endpoint should still see it.
  try {
    maybeEmitRatingPrompt({ sessionId, githubLogin });
  } catch { /* never break Stop on prompt failure */ }

  if (!endpoint || !githubLogin) return;

  const usage = data?.usage || {};
  // Claude Code omits session_started_at from the Stop payload, so we derive it:
  // earliest buffered event timestamp → fallback to ended_at.
  // Must not send null — the sessions table has NOT NULL on started_at and
  // PostgREST ignores the column DEFAULT when the value is explicitly null.
  const endedAtIso = new Date().toISOString();
  const earliestEventTs = events.reduce((acc, ev) => {
    const t = typeof ev?.ts === 'string' ? ev.ts : null;
    if (!t) return acc;
    return !acc || t < acc ? t : acc;
  }, null);
  const startedAtIso = data?.session_started_at || earliestEventTs || endedAtIso;
  const payload = {
    user: githubLogin,
    session: {
      id: sessionId,
      sk_version: readSkVersion(cwd),
      project_hash: buildCwdHash(cwd),
      started_at: startedAtIso,
      ended_at: endedAtIso,
      duration_s: typeof data?.duration_s === 'number'
        ? data.duration_s
        : Math.max(0, Math.round((Date.parse(endedAtIso) - Date.parse(startedAtIso)) / 1000)),
      input_tokens: Number(usage.input_tokens) || 0,
      output_tokens: Number(usage.output_tokens) || 0,
      cache_read_tokens: Number(usage.cache_read_tokens) || 0,
      cache_write_tokens: Number(usage.cache_write_tokens) || 0,
      milestone_completed: milestone,
      error_count: Number(data?.error_count) || 0,
    },
    events,
  };

  const version = readSkVersion(cwd);
  await post(`${endpoint}/telemetry`, payload, { version, timeoutMs: 2000 });
}

// Orphan buffers older than 24 h are deleted, not flushed. Without the Stop
// payload (token counts, duration, milestone) a late flush produces a truncated
// sessions row that distorts analytics. Discarding events from crashed sessions
// is the deliberate trade-off.
function handleSessionStart() {
  try {
    if (!fs.existsSync(BUFFER_DIR)) return;
    const now = Date.now();
    for (const file of fs.readdirSync(BUFFER_DIR)) {
      if (!file.endsWith('.jsonl')) continue;
      const full = path.join(BUFFER_DIR, file);
      try {
        const stat = fs.statSync(full);
        if (now - stat.mtimeMs > ORPHAN_AGE_MS) {
          fs.unlinkSync(full);
        }
      } catch { /* skip unreadable */ }
    }
  } catch { /* ignore cleanup failures */ }
}

/* ─── Entry point ─────────────────────────────────────────────────────── */

async function main() {
  if (!isHookEnabled('telemetry')) return;

  let data = {};
  try {
    const raw = fs.readFileSync(0, 'utf-8').trim();
    if (raw) data = JSON.parse(raw);
  } catch {
    return;
  }

  const eventType = data.hook_event_name || 'SessionStart';
  const timer = createHookTimer('telemetry', { event: eventType });

  try {
    switch (eventType) {
      case 'SessionStart':
        handleSessionStart();
        break;
      case 'UserPromptSubmit':
        handleUserPromptSubmit(data);
        break;
      case 'PostToolUse':
        handlePostToolUse(data);
        break;
      case 'Stop':
        await handleStop(data);
        break;
    }
    timer.end({ status: 'ok' });
  } catch (err) {
    try { timer.end({ status: 'error' }); } catch { /* ignore */ }
    logHookCrash('telemetry', err, { event: eventType });
  }
}

if (require.main === module) {
  main()
    .catch((err) => {
      try { logHookCrash('telemetry', err, {}); } catch { /* ignore */ }
    })
    .finally(() => process.exit(0));
}

module.exports = {
  BUFFER_DIR,
  MAX_PAYLOAD_BYTES,
  ORPHAN_AGE_MS,
  RATING_SAMPLE_RATE,
  RATING_PROMPT_TEXT,
  bufferFileFor,
  appendEvent,
  readBufferEvents,
  deleteBuffer,
  capEvents,
  extractSkCommand,
  classifyTool,
  handleUserPromptSubmit,
  handlePostToolUse,
  handleStop,
  handleSessionStart,
  readMilestone,
  shouldSampleRating,
  maybeEmitRatingPrompt,
};
