/**
 * memory-graph-queue-lib — turns a session transcript into a queued .md fact-capture
 * file for later (Stage 3 nudge) graphify extraction. Deterministic file I/O only — no
 * LLM call, so it's safe to run from inside a Stop hook.
 *
 * Output location settled by the Phase 1 sanity spike
 * (plans/260716-1046-memory-graph-tier-auto/phase-01-sanity-spike.md): graphify's own
 * detect() honors .gitignore, so an in-repo `memory-graph-out/` (gitignored) is safe from
 * the shipped code-KG hook's `graphify update .` — no global dir needed.
 *
 * Written output is plaintext on disk — `.gitignore` keeps it out of `git commit` but
 * not out of local backups/cloud sync/other tools scanning the repo dir. renderMarkdown
 * runs turn text through secret-redact.cjs before it's written, but that's regex-based
 * defense in depth, not a guarantee — see memoryGraph.enabled's config comment.
 *
 * @module memory-graph-queue-lib
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { sanitizeSlug } = require('./tkm-config-utils.cjs');
const { redactSecrets } = require('./secret-redact.cjs');

const QUEUE_SUBDIR = path.join('memory-graph-out', 'raw');
const GITIGNORE_ENTRY = 'memory-graph-out/';

// Queuing heuristic constants — tuned against Phase 1's 58-turn LOCOMO spike transcript
// (~9.5KB / ~1.6K words for 58 turns, so a 40-turn cap sits well under MAX_CHARS).
const MIN_USER_TURNS = 2;
const MIN_TOTAL_CHARS = 200;
const MAX_TURNS = 40;
const MAX_CHARS = 16000;

/** Resolve (and create) the gitignored queue directory for a project root. */
function resolveQueueDir(cwd) {
  const dir = path.join(cwd, QUEUE_SUBDIR);
  fs.mkdirSync(dir, { recursive: true });
  ensureGitignoreEntry(cwd, GITIGNORE_ENTRY);
  return dir;
}

/** Append `entry` to <projectDir>/.gitignore if not already present. Best-effort. */
function ensureGitignoreEntry(projectDir, entry) {
  try {
    const gi = path.join(projectDir, '.gitignore');
    const existing = fs.existsSync(gi) ? fs.readFileSync(gi, 'utf8') : '';
    if (existing.includes(entry.replace(/\/$/, ''))) return;
    const sep = (existing === '' || existing.endsWith('\n')) ? '' : '\n';
    fs.appendFileSync(gi, sep + entry + '\n');
  } catch { /* best-effort */ }
}

/** Pull all non-sidechain user/assistant text blocks from a JSONL transcript, in order. */
function filterTranscript(transcriptPath) {
  const turns = [];
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return turns;

  let raw;
  try {
    raw = fs.readFileSync(transcriptPath, 'utf8');
  } catch {
    return turns;
  }

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    let entry;
    try { entry = JSON.parse(trimmed); } catch { continue; }

    if (entry.isSidechain) continue; // subagent transcript, not the user's own conversation

    const role = entry.message?.role;
    if (role !== 'user' && role !== 'assistant') continue;

    const text = extractText(entry.message?.content);
    if (text) turns.push({ role, text });
  }

  return turns;
}

/** Flatten transcript message content into plain text, keeping only `text` blocks. */
function extractText(content) {
  if (typeof content === 'string') return content.trim();
  if (!Array.isArray(content)) return '';
  return content
    .filter(block => block && block.type === 'text' && typeof block.text === 'string')
    .map(block => block.text.trim())
    .filter(Boolean)
    .join('\n');
}

/** Skip trivial sessions: too few user turns, or too little kept text overall. */
function passesHeuristic(turns) {
  const userTurnCount = turns.filter(t => t.role === 'user').length;
  const totalChars = turns.reduce((sum, t) => sum + t.text.length, 0);
  return userTurnCount >= MIN_USER_TURNS && totalChars >= MIN_TOTAL_CHARS;
}

/** Bound per-session volume: last MAX_TURNS turns, then a hard MAX_CHARS ceiling. */
function capTurns(turns) {
  let capped = turns.length > MAX_TURNS ? turns.slice(-MAX_TURNS) : turns;

  let totalChars = capped.reduce((sum, t) => sum + t.text.length, 0);
  while (totalChars > MAX_CHARS && capped.length > 1) {
    totalChars -= capped[0].text.length;
    capped = capped.slice(1);
  }

  return capped;
}

/**
 * Render frontmatter + speaker-tagged body, matching the Phase 1 spike's transcript shape.
 * Each turn's text is passed through `redactSecrets` first — this file lands as plaintext
 * on disk (see writeQueueFile), so anything secret-shaped pasted into the conversation
 * (AWS keys, tokens, JWTs, .env-style assignments, etc.) gets scrubbed before it's ever
 * written. Regex-based, not a leak guarantee — see secret-redact.cjs.
 */
function renderMarkdown(turns, sessionId) {
  const capturedAt = new Date().toISOString();
  const lines = [
    '---',
    `session_id: ${sessionId}`,
    `captured_at: ${capturedAt}`,
    '---',
    '',
    '# Conversation transcript',
    ''
  ];
  for (const turn of turns) {
    const speaker = turn.role === 'user' ? 'User' : 'Assistant';
    lines.push(`**${speaker}:** ${redactSecrets(turn.text)}`);
  }
  return lines.join('\n') + '\n';
}

/**
 * Write atomically; no-op (dedup) if the session's queue file already exists.
 * `session_id` is sanitized to a safe filename slug — it's framework-assigned, not
 * transcript-controlled, but this hook's output is PII-adjacent so defense-in-depth
 * against a malformed/hostile id (e.g. path traversal) is cheap to add. `markdown`
 * content-side redaction (secret-shaped substrings) already happened upstream in
 * renderMarkdown — this function only guards the filename.
 * Dedup uses an exclusive link (not existsSync-then-rename) so two concurrent writers
 * for the same session_id can't race past the check and have the second overwrite the
 * first — link(2) is atomic at the filesystem level.
 */
function writeQueueFile(queueDir, sessionId, markdown) {
  const safeId = sanitizeSlug(sessionId) || 'unknown-session';
  const filePath = path.join(queueDir, `${safeId}.md`);
  const tmp = `${filePath}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;

  fs.writeFileSync(tmp, markdown);
  try {
    fs.linkSync(tmp, filePath); // atomic exclusive create — throws EEXIST if already written
    return { written: true, path: filePath };
  } catch (err) {
    if (err && err.code === 'EEXIST') return { written: false, path: filePath, reason: 'dedup' };
    throw err;
  } finally {
    try { fs.unlinkSync(tmp); } catch { /* best-effort cleanup */ }
  }
}

module.exports = {
  resolveQueueDir,
  filterTranscript,
  passesHeuristic,
  capTurns,
  renderMarkdown,
  writeQueueFile,
  // exported for unit tests
  extractText,
  ensureGitignoreEntry,
  MIN_USER_TURNS,
  MIN_TOTAL_CHARS,
  MAX_TURNS,
  MAX_CHARS
};
