/**
 * secret-redact — regex-based redaction of secret-shaped substrings before conversation
 * text is written to disk (memory-graph-queue-lib.cjs's renderMarkdown). Pattern
 * vocabulary ported from claude/skills/rebuild-spec/scripts/_credential_scrub_lib.py's
 * `_SCRUB_PATTERNS` (recall-focused: over-redacting prose is safe here, the output is a
 * queued knowledge-graph source doc, not something a human reads for content fidelity).
 *
 * Structural regex only — deliberately NOT entropy-based. Entropy detection catches more
 * but flags plausible-looking prose too often for something that mangles conversation
 * text; the patterns below cover the concrete shapes (AWS/OpenAI/Anthropic/GitHub/Slack
 * keys, PEM blocks, JWTs, Bearer tokens, scheme://user:pass@host, and KEY=VALUE /
 * KEY: VALUE assignments with a credential-ish key) called out as the actual failure
 * scenario: pasting a .env, AWS_SECRET_ACCESS_KEY=..., a DB connection string, or a JWT
 * into chat while memoryGraph.enabled=true.
 *
 * Not a leak guarantee — a determined or unusually-shaped secret can still slip through.
 * Defense in depth, not a substitute for not pasting real credentials into chat.
 *
 * Stdlib only, no deps.
 * @module secret-redact
 */
'use strict';

const REDACTED = '[REDACTED]';

// Fixed-shape secret patterns — unambiguous enough to redact unconditionally.
const PATTERNS = [
  // AWS access key ID
  [/\bAKIA[0-9A-Z]{16}\b/g, REDACTED],
  // AWS secret access key / session token assignment
  [/((?:aws_secret_access_key|aws_session_token)\s*[=:]\s*)\S+/gi, `$1${REDACTED}`],
  // Anthropic API keys (checked before the generic sk- pattern, same prefix family)
  [/\bsk-ant-[A-Za-z0-9_-]{16,}\b/g, REDACTED],
  // OpenAI-style keys (sk-..., sk-proj-...)
  [/\bsk-[A-Za-z0-9_-]{16,}\b/g, REDACTED],
  // GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_)
  [/\bgh[oprsu]_[A-Za-z0-9]{20,}\b/g, REDACTED],
  // Slack tokens
  [/\bxox[baprs]-[A-Za-z0-9-]{10,}\b/g, REDACTED],
  // PEM-style private key blocks
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, REDACTED],
  // JWTs (three dot-separated base64url segments)
  [/\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g, REDACTED],
  // Authorization: Bearer <token>
  [/(Bearer\s+)\S+/gi, `$1${REDACTED}`],
  // scheme://user:pass@host credentials (DB connection strings, broker URLs)
  [/(\w+:\/\/[^:/@\s]+):[^@/\s]+@/g, `$1:${REDACTED}@`]
];

// Credential-ish KEY segments for KEY=VALUE / KEY: VALUE assignments (.env pastes,
// config snippets). Segment-boundary match (split on [_.-], each segment compared as a
// whole word via startsWith) — mirrors _key_has_credential_segment in
// _credential_scrub_lib.py so e.g. BYPASS_HEALTHCHECK does not false-positive on "pass".
const ENV_KEY_VOCAB = ['pass', 'pwd', 'secret', 'token', 'key', 'credential', 'dsn', 'auth'];
const ASSIGN_RE = /\b([A-Za-z][\w.-]*)([ \t]*[=:][ \t]*)(\S+)/g;

function keyHasCredentialSegment(key) {
  const segments = key.split(/[_.-]/).filter(Boolean).map((s) => s.toLowerCase());
  return segments.some((seg) => ENV_KEY_VOCAB.some((word) => seg.startsWith(word)));
}

function redactEnvStyleAssignments(text) {
  return text.replace(ASSIGN_RE, (match, key, sep, value) => {
    if (value === REDACTED) return match;
    // "Authorization: Bearer <token>" is already handled by the dedicated Bearer
    // pattern above (it redacts the token itself); without this exclusion the generic
    // assignment pass also fires on "Authorization" (it contains the "auth" segment)
    // and redacts the literal word "Bearer" instead, leaving a confusing double redact.
    if (key.toLowerCase() === 'authorization') return match;
    if (!keyHasCredentialSegment(key)) return match;
    return `${key}${sep}${REDACTED}`;
  });
}

/** Redact secret-shaped substrings in `text`. Regex-based; not a leak guarantee. */
function redactSecrets(text) {
  if (!text) return text;
  let out = text;
  for (const [pattern, replacement] of PATTERNS) {
    out = out.replace(pattern, replacement);
  }
  return redactEnvStyleAssignments(out);
}

module.exports = { redactSecrets, REDACTED };
