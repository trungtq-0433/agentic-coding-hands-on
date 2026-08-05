#!/usr/bin/env node
'use strict';

/**
 * evidence-gate-guard.cjs — PreToolUse[Bash] guard: hard-blocks a ship action
 * (git push, gh pr create, wrangler deploy, npm publish) unless the located
 * plan's evidence/ directory carries a SEALED verdict.
 *
 * Lifecycle-hook counterpart to `skills/_shared/lib/evidence-gate.cjs` (the
 * inline gate a skill calls at its own Deliver boundary — bypassable by
 * skipping the skill). This hook fires on every Bash call regardless of how
 * the session got there.
 *
 * Stage detection (see lib/stage-detector.cjs): hard = the Bash command IS a
 * ship action -> verdict must be SEALED or deny. soft = no ship Bash command
 * yet, but the latest typed prompt names a ship verb -> advisory
 * `additionalContext` only. null = neither signal -> pass through silently.
 *
 * ALL verdict policy (SEALED, criticalCount, findings[]/location, etc.) lives
 * in hooks/lib/evidence-validator.cjs — this file is a thin caller, never a
 * second implementation of that policy.
 *
 * Fail behaviour: fail-OPEN on any internal error (bad input, locator/validator
 * throwing, no evidence dir located) — never wedge a session on the gate's own
 * bug. Fails CLOSED only when the validator reports a real hard-stage
 * violation against a FOUND evidence directory.
 *
 * Bypass: `.tkm.json` -> hooks."evidence-gate-guard": false disables the hook
 * entirely. A typed prompt containing "--skip-tests" or "--skip-review"
 * downgrades a hard stage to advisory (artifacts intentionally absent).
 *
 * Registered for matcher "Bash"; emits permissionDecision/additionalContext,
 * exit 0 always — same convention as workflow-opt-in-guard.cjs.
 */

const fs = require('fs');

const SKIP_FLAG_RE = /--skip-(?:tests|review)\b/i;

function emitDeny(reason) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    },
  }));
}

function emitAdvisory(note) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: note,
    },
  }));
}

function emitAllow() {
  process.stdout.write(JSON.stringify({}));
}

/**
 * Most recent human-typed prompt from the transcript tail, or null. Mirrors
 * workflow-opt-in-guard.cjs's lastHumanPrompt: walks entries backward, skips
 * assistant turns and tool_result-only entries (which also carry role:user).
 */
function lastHumanPrompt(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return null;
  const lines = fs.readFileSync(transcriptPath, 'utf-8').split('\n').slice(-150);
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    let entry;
    try { entry = JSON.parse(line); } catch (_) { continue; }
    if (entry.type !== 'user' || !entry.message || entry.message.role !== 'user') continue;

    const content = entry.message.content;
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) {
      const text = content.filter((b) => b && b.type === 'text').map((b) => b.text).join(' ').trim();
      if (text) return text;
      // otherwise a tool_result-only entry — keep walking back
    }
  }
  return null;
}

/** Build an actionable, path-only deny reason — never echoes artifact contents. */
function buildDenyReason(evidenceDir, result) {
  const top = result.blocking.slice(0, 3).map((b) => `  - ${b}`).join('\n');
  const more = result.blocking.length > 3 ? `\n  - …and ${result.blocking.length - 3} more` : '';
  return (
    `Ship blocked: evidence at "${evidenceDir}" is not SEALED (${result.blocking.length} issue(s)):\n` +
    `${top}${more}\n` +
    `Reproduce: node claude/skills/_shared/lib/evidence-gate.cjs --evidence-dir "${evidenceDir}" --stage hard\n` +
    `Bypass: disable via .tkm.json -> hooks."evidence-gate-guard": false, or include ` +
    `"--skip-tests"/"--skip-review" in your request to downgrade this check to advisory.`
  );
}

try {
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');
  const { detectStage } = require('./lib/stage-detector.cjs');
  const { locateEvidenceDir } = require('./lib/evidence-dir-locator.cjs');
  const timer = createHookTimer('evidence-gate-guard', { event: 'PreToolUse', tool: 'Bash' });

  let enabled = true;
  try { enabled = isHookEnabled('evidence-gate-guard'); } catch (_) { /* config error -> treat as enabled */ }
  if (!enabled) { timer.end({ status: 'ok', note: 'disabled' }); emitAllow(); process.exit(0); }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(0, 'utf-8'));
  } catch (_) {
    // Unparseable payload — fail OPEN (this hook fails closed only on a real
    // verdict violation, never on its own input trouble).
    timer.end({ status: 'ok', exit: 0, note: 'bad-input-fail-open' });
    emitAllow();
    process.exit(0);
  }

  if (data.tool_name && data.tool_name !== 'Bash') {
    timer.end({ status: 'ok', note: 'not-bash' });
    emitAllow();
    process.exit(0);
  }

  const bashCommand = data.tool_input && data.tool_input.command;
  const prompt = lastHumanPrompt(data.transcript_path);
  const { stage, signal } = detectStage({ bashCommand, prompt });

  if (!stage) {
    timer.end({ status: 'ok', note: 'no-signal' });
    emitAllow();
    process.exit(0);
  }

  // Intentional skip: user's request carries --skip-tests / --skip-review —
  // the artifacts are knowingly absent, so a hard stage downgrades to advisory.
  const skipRequested = SKIP_FLAG_RE.test(prompt || '');
  const effectiveStage = (stage === 'hard' && skipRequested) ? 'soft' : stage;

  if (effectiveStage === 'soft') {
    timer.end({ status: 'ok', note: skipRequested ? 'skip-flag-downgrade' : 'soft-advisory' });
    emitAdvisory(
      `[evidence-gate] Ship intent detected (${signal}). When you actually push/PR/deploy, the ` +
      `evidence gate will check for a SEALED verdict in the plan's evidence/ directory.`
    );
    process.exit(0);
  }

  // effectiveStage === 'hard' from here on.
  let evidenceDir;
  try {
    evidenceDir = locateEvidenceDir({ cwd: data.cwd, sessionId: data.session_id || process.env.TKM_SESSION_ID || null });
  } catch (_) {
    evidenceDir = null; // locator failure -> treat as "not found", fail open below
  }

  if (!evidenceDir) {
    // Decision: no evidence dir located at a hard stage fails OPEN, not closed.
    // Rationale — mirrors evidence-gate.cjs's own "no --evidence-dir -> fail open"
    // stance: an unlocatable evidence dir is ambiguous (no takumi plan/evidence
    // workflow ran at all vs. a genuine skip) rather than a proven violation, and
    // hard-blocking every `git push` in repos not using the plan-evidence flow
    // would be a session-wedging false positive — the top risk this phase flags.
    // The gap is still surfaced via advisory context, not silently swallowed.
    timer.end({ status: 'ok', note: 'no-evidence-dir-fail-open' });
    emitAdvisory(
      `[evidence-gate] Ship action detected (${signal}) but no evidence directory could be located ` +
      `(checked TKM_EVIDENCE_DIR, .claude/workflow-artifacts.json, and the active plan's evidence/ dir). ` +
      `Proceeding — set TKM_EVIDENCE_DIR or run through the plan-evidence workflow if this ship should have been gated.`
    );
    process.exit(0);
  }

  const { validateEvidence } = require('./lib/evidence-validator.cjs');
  const result = validateEvidence({ evidenceDir, stage: 'hard' });

  if (result.ok) {
    timer.end({ status: 'ok', note: 'sealed' });
    emitAllow();
    process.exit(0);
  }

  timer.end({ status: 'block', exit: 2, note: 'not-sealed' });
  emitDeny(buildDenyReason(evidenceDir, result));
  process.exit(0);

} catch (e) {
  // Fail-open: an internal crash in the guard must never wedge a Bash call.
  try {
    require('./lib/hook-logger.cjs').logHookCrash('evidence-gate-guard', e, { event: 'PreToolUse', tool: 'Bash', exit: 0 });
  } catch (_) { /* logger must never crash the hook */ }
  emitAllow();
  process.exit(0);
}
