'use strict';

/**
 * stage-detector — classifies a Bash tool call into a ship "stage" so
 * evidence-gate-guard.cjs knows whether to hard-block or merely advise.
 *
 *   hard  — the Bash command about to run IS a ship action (git push,
 *           gh pr create, wrangler deploy, npm publish). The gate must run
 *           for real; a bad verdict blocks the call.
 *   soft  — no ship Bash command yet, but the user's latest typed prompt
 *           names genuine shipping intent (ship/deploy/publish, or a
 *           push/merge/pr phrase with a git/PR companion word) without a
 *           negation ("don't ship this", "not ready to deploy") — advisory
 *           only, nothing irreversible is about to happen.
 *   null  — neither signal present; the guard passes through silently.
 *
 * Pure function, no I/O — the caller (evidence-gate-guard.cjs) supplies the
 * Bash command string and the latest human-typed prompt text; transcript
 * reading stays in the hook, same split as workflow-opt-in-guard.cjs.
 */

// Actual ship actions — matching one of these against the Bash command itself
// is the "hard" signal: the irreversible action is one exec() away. Each
// pattern is anchored to the START of a command segment (see
// detectHardBashCommand) so it only fires against something that will
// actually run as its own command, not text merely mentioning the phrase.
const HARD_BASH_PATTERNS = [
  [/^git\s+push\b/i, 'git push'],
  [/^gh\s+pr\s+create\b/i, 'gh pr create'],
  [/^(?:npx\s+)?wrangler\s+deploy\b/i, 'wrangler deploy'],
  [/^npm\s+publish\b/i, 'npm publish'],
];

// Shell command separators — a hard-command pattern must match at the start
// of one of these segments, never mid-argument or mid-string.
const COMMAND_SEPARATOR_RE = /&&|\|\||;|\n|\|/;

// A dry-run flag on the matched command downgrades it to non-hard — nothing
// irreversible actually happens.
const DRY_RUN_RE = /--dry-run\b/i;

/** Strip single- and double-quoted substrings so quoted text never trips a hard-command match. */
function stripQuotedSegments(cmd) {
  return String(cmd || '').replace(/"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g, ' ');
}

/**
 * First HARD_BASH_PATTERNS label whose command actually runs (not quoted,
 * not buried in another command's args, not a --dry-run invocation), or null.
 */
function detectHardBashCommand(bashCommand) {
  const cleaned = stripQuotedSegments(bashCommand);
  const segments = cleaned.split(COMMAND_SEPARATOR_RE).map((s) => s.trim()).filter(Boolean);
  for (const segment of segments) {
    for (const [re, label] of HARD_BASH_PATTERNS) {
      if (re.test(segment) && !DRY_RUN_RE.test(segment)) return label;
    }
  }
  return null;
}

// Bare-token ship verbs: safe as standalone signals in typed prose — rare as
// filler words in unrelated sentences.
const BARE_SHIP_VERBS = ['ship', 'deploy', 'publish'];

// Context-gated phrases: bare "push" / "merge" / "pr" are common in unrelated
// prose ("push notification", "merge conflict", "pr" as an unrelated
// abbreviation) — only count as shipping intent when paired with a companion
// word that signals an actual git/PR action.
const CONTEXT_INTENT_PATTERNS = [
  /\bpush(?:ed|ing)?\s+(?:the\s+|my\s+)?(?:branch|changes|code|commit|it|this|up)\b/i,
  /\bready to push\b/i,
  /\bmerge\s+(?:this|it|that|now|the\s+\w+|pr\b)/i,
  /\bready to merge\b/i,
  /\b(?:open|create|raise|make|submit)\s+(?:a\s+|the\s+)?pr\b/i,
];

const NEGATION_WORDS = new Set([
  "don't", 'dont', 'not', 'never', "won't", 'wont', "shouldn't", 'shouldnt',
  "can't", 'cant', 'cannot', 'avoid', 'skip', 'skipping', 'no',
]);

/** Lowercase, strip punctuation (keep apostrophes), split on whitespace. */
function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9'\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

/** True when any token in `preceding` is a negation word. */
function isNegated(preceding) {
  return preceding.some((t) => NEGATION_WORDS.has(t));
}

/**
 * First genuine ship-intent verb in `prompt` that is NOT negated within
 * `window` tokens of it, or null. Checks bare verbs first (ship/deploy/
 * publish), then context-gated phrases (push/merge/pr with a companion word).
 */
function hasUnnegatedShipVerb(prompt, window = 4) {
  const tokens = tokenize(prompt);

  for (let i = 0; i < tokens.length; i += 1) {
    if (!BARE_SHIP_VERBS.includes(tokens[i])) continue;
    if (!isNegated(tokens.slice(Math.max(0, i - window), i))) return tokens[i];
  }

  const text = String(prompt || '');
  for (const re of CONTEXT_INTENT_PATTERNS) {
    const m = re.exec(text);
    if (!m) continue;
    const preceding = tokenize(text.slice(0, m.index)).slice(-window);
    if (!isNegated(preceding)) return m[0].toLowerCase().split(/\s+/)[0];
  }

  return null;
}

/**
 * @param {object} input
 * @param {string} [input.bashCommand] - the Bash tool_input.command about to run
 * @param {string} [input.prompt] - latest human-typed prompt text, or null
 * @returns {{stage: 'hard'|'soft'|null, signal: string|null}}
 */
function detectStage({ bashCommand, prompt } = {}) {
  if (bashCommand) {
    const hard = detectHardBashCommand(bashCommand);
    if (hard) return { stage: 'hard', signal: hard };
  }

  const verb = hasUnnegatedShipVerb(prompt);
  if (verb) return { stage: 'soft', signal: `typed prompt verb "${verb}"` };

  return { stage: null, signal: null };
}

module.exports = {
  detectStage,
  hasUnnegatedShipVerb,
  tokenize,
  detectHardBashCommand,
  stripQuotedSegments,
  HARD_BASH_PATTERNS,
  BARE_SHIP_VERBS,
  CONTEXT_INTENT_PATTERNS,
};
