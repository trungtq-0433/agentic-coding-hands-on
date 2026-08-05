#!/usr/bin/env node
'use strict';

/**
 * workflow-opt-in-guard.cjs — PreToolUse guard: blocks the Workflow tool unless
 * the user's latest prompt explicitly opts in with the word "workflow".
 *
 * Deterministic floor under the (soft) markdown rule in
 * .claude/rules/orchestration-protocol.md → "Workflow Tool (Opt-In Only)".
 * The Workflow tool fans out many subagents and is expensive, so a stray call
 * is costly — worth a hard stop, not just an instruction.
 *
 * PreToolUse payloads carry no prompt, so the most recent human-typed message is
 * read from the transcript tail (transcript_path). Tool-result entries (also
 * recorded under role:user) are skipped — only genuine typed prompts count.
 *
 * Fail-CLOSED: when opt-in can't be verified the call is denied — the safe
 * default for an opt-in tool (deliberately against the house fail-open style).
 * The deny reason is fed back to the model, which can relay it to the user.
 *
 * Registered for matcher "Workflow"; emits permissionDecision on stdout, exit 0.
 * Disable via .tkm.json → hooks."workflow-opt-in-guard": false.
 */

const fs = require('fs');

const REASON = 'The Workflow tool is opt-in and stays blocked until the user\'s most recent chat message literally contains the word "workflow". A confirmation prompt or menu choice (e.g. AskUserQuestion) does NOT count and will not unblock it — only a new typed user message that includes the word "workflow" will. So either continue with an alternative such as the Task tool, or ask the user to resend their request with the word "workflow" in it (e.g. "run this as a workflow"), then call Workflow again.';

function emitDeny(reason) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason
    }
  }));
}

/**
 * Most recent human-typed prompt from the transcript tail, or null.
 * Walks entries backward; skips assistant turns and tool_result entries
 * (which also carry role:user) so only real typed prompts are considered.
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
      const text = content.filter(b => b && b.type === 'text').map(b => b.text).join(' ').trim();
      if (text) return text; // genuine typed prompt
      // otherwise a tool_result-only entry — keep walking back
    }
  }
  return null;
}

try {
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer } = require('./lib/hook-logger.cjs');
  const timer = createHookTimer('workflow-opt-in-guard', { event: 'PreToolUse', tool: 'Workflow' });

  // Disabled via config → allow.
  let enabled = true;
  try { enabled = isHookEnabled('workflow-opt-in-guard'); } catch (_) { /* config error → treat as enabled */ }
  if (!enabled) { timer.end({ status: 'ok', note: 'disabled' }); process.exit(0); }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(0, 'utf-8'));
  } catch (_) {
    // Matcher guarantees this fired for a Workflow call; unparseable payload → fail-closed.
    timer.end({ status: 'block', exit: 2, note: 'bad-input' });
    emitDeny(REASON);
    process.exit(0);
  }

  // Guard only the Workflow tool; a different named tool passes through.
  if (data.tool_name && data.tool_name !== 'Workflow') {
    timer.end({ status: 'ok', note: 'not-workflow' });
    process.exit(0);
  }

  const prompt = lastHumanPrompt(data.transcript_path);
  const optedIn = prompt !== null && prompt.toLowerCase().includes('workflow');

  if (optedIn) {
    timer.end({ status: 'ok', note: 'opted-in' });
    process.exit(0);
  }

  // Fail-closed: not opted in (or prompt unverifiable) → deny an opt-in tool.
  timer.end({ status: 'block', exit: 2, note: prompt === null ? 'no-prompt' : 'not-opted-in' });
  emitDeny(REASON);
  process.exit(0);

} catch (e) {
  // Fail-closed: an opt-in tool defaults to blocked when the guard itself fails.
  try {
    require('./lib/hook-logger.cjs').logHookCrash('workflow-opt-in-guard', e, { event: 'PreToolUse', tool: 'Workflow', exit: 2 });
  } catch (_) { /* logger must never crash the hook */ }
  emitDeny('The Workflow tool is opt-in and the guard could not verify opt-in. Use an alternative approach such as the Task tool, or ask the user to re-request explicitly with the word "workflow".');
  process.exit(0);
}
