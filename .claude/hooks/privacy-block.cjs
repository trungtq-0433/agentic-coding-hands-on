#!/usr/bin/env node
/**
 * privacy-block.cjs — PreToolUse guard: blocks reads of sensitive files until the
 * user explicitly approves. Fires in the Forge stage before any file tool executes.
 *
 * Approval protocol (APPROVED: prefix):
 * 1. Agent tries: Read ".env" → blocked, emits @@PRIVACY_PROMPT_START@@ JSON
 * 2. Agent surfaces AskUserQuestion to user
 * 3. User approves
 * 4. Agent retries: Read "APPROVED:.env" → allowed
 *
 * Pure matching logic lives in lib/privacy-checker.cjs (shared with other runtimes).
 */

(async () => {
  try {
  const path = require('path');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

    // Pull in the shared privacy-checker facade
    const {
      checkPrivacy,
      isSafeFile,
      isPrivacyBlockDisabled,
      isPrivacySensitive,
      hasApprovalPrefix,
      stripApprovalPrefix,
      extractPaths,
      isSuspiciousPath
    } = require('./lib/privacy-checker.cjs');
    const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');

    // Bail early when the guard is disabled in .tkm.json
    if (!isHookEnabled('privacy-block')) {
      process.exit(0);
    }

/**
 * Build the block message shown to the agent when access is denied.
 * Embeds @@PRIVACY_PROMPT_START@@ / @@PRIVACY_PROMPT_END@@ markers so the
 * agent can extract the JSON and call AskUserQuestion.
 * @param {string} filePath - Blocked file path
 * @returns {string} Formatted block message with JSON marker
 */
function formatBlockMessage(filePath) {
  const basename = path.basename(filePath);

  // Structured payload the agent parses to drive AskUserQuestion
  const promptData = {
    type: 'PRIVACY_PROMPT',
    file: filePath,
    basename: basename,
    question: {
      header: 'File Access',
      text: `I need to read "${basename}" which may contain sensitive data (API keys, passwords, tokens). Do you approve?`,
      options: [
        { label: 'Yes, approve access', description: `Allow reading ${basename} this time` },
        { label: 'No, skip this file', description: 'Continue without accessing this file' }
      ]
    }
  };

  return `
\x1b[36mNOTE:\x1b[0m This is not an error - this block protects sensitive data.

\x1b[33mPRIVACY BLOCK\x1b[0m: Sensitive file access requires user approval

  \x1b[33mFile:\x1b[0m ${filePath}

  This file may contain secrets (API keys, passwords, tokens).

\x1b[90m@@PRIVACY_PROMPT_START@@\x1b[0m
${JSON.stringify(promptData, null, 2)}
\x1b[90m@@PRIVACY_PROMPT_END@@\x1b[0m

  \x1b[34mClaude:\x1b[0m Use AskUserQuestion tool with the JSON above, then:
  \x1b[32mIf "Yes":\x1b[0m Use bash to read: cat "${filePath}"
  \x1b[31mIf "No":\x1b[0m  Continue without this file.
`;
}

/**
 * Emit a brief approval notice when APPROVED: prefix is present.
 * @param {string} filePath - Approved file path
 * @returns {string} Formatted approval notice
 */
function formatApprovalNotice(filePath) {
  return `\x1b[32m✓\x1b[0m Privacy: User-approved access to ${path.basename(filePath)}`;
}

// Detect when the hook is running under Codex (no AskUserQuestion protocol
// exists there, so Bash on sensitive paths must hard-block instead of warning).
// The marker file is written explicitly by each installer, so this is a
// declarative lookup rather than env-var guessing.
function isCodexAgent() {
  try {
    return require('./lib/env.cjs').agent === 'codex';
  } catch (_) {
    return false;
  }
}

// Entry point — reads stdin JSON, dispatches to privacy-checker, exits 0
async function main() {
  const timer = createHookTimer('privacy-block', { event: 'PreToolUse' });
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  let hookData;
  try {
    hookData = JSON.parse(input);
  } catch (e) {
    timer.end({ status: 'warn', exit: 0, note: 'json-parse-failed', error: e.message });
    process.exit(0); // Invalid JSON, allow
  }

  const { tool_input: toolInput, tool_name: toolName } = hookData;

  // Delegate to the shared privacy-checker for decision
  const result = checkPrivacy({
    toolName,
    toolInput,
    options: { allowBash: true }
  });

  // Route on checker decision
  if (result.approved) {
    // APPROVED: prefix present — let the read through, log a notice
    if (result.suspicious) {
      console.error('\x1b[33mWARN:\x1b[0m Approved path is outside project:', result.filePath);
    }
    console.error(formatApprovalNotice(result.filePath));
    timer.end({
      tool: toolName,
      status: 'ok',
      exit: 0,
      target: path.basename(result.filePath || ''),
      note: result.suspicious ? 'approved-suspicious-path' : 'approved'
    });
    process.exit(0);
  }

  if (result.isBash) {
    // F9 hybrid: under Codex there is no AskUserQuestion protocol, so the
    // warn-only path is bypassable. Hard-block instead. Under Claude Code,
    // keep warn-only to preserve the documented "Yes → bash cat" flow.
    if (isCodexAgent()) {
      // timer.end keeps exit:2 — telemetry semantic, decoupled from process exit
      timer.end({
        tool: toolName,
        status: 'block',
        exit: 2,
        target: path.basename(result.filePath || ''),
        note: 'bash-sensitive-file-codex'
      });
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: result.reason
        }
      }));
      process.exit(0);
    }
    console.error(`\x1b[33mWARN:\x1b[0m ${result.reason}`);
    timer.end({
      tool: toolName,
      status: 'warn',
      exit: 0,
      target: path.basename(result.filePath || ''),
      note: 'bash-sensitive-file'
    });
    process.exit(0);
  }

  if (result.blocked) {
    // No approval — emit modern deny shape with prompt markers in reason
    // timer.end keeps exit:2 — telemetry semantic, decoupled from process exit
    timer.end({
      tool: toolName,
      status: 'block',
      exit: 2,
      target: path.basename(result.filePath || ''),
      note: 'approval-required'
    });
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: formatBlockMessage(result.filePath)
      }
    }));
    process.exit(0);
  }

  timer.end({ tool: toolName, status: 'ok', exit: 0 });
  process.exit(0); // Allow
}

    // Guard against double-execution when this module is required for testing
    if (require.main === module) {
      main().catch((error) => {
        logHookCrash('privacy-block', error, { event: 'PreToolUse' });
        process.exit(0);
      });
    }

    // Re-export checker helpers so unit tests can import this entry point directly
    if (typeof module !== 'undefined') {
      module.exports = {
        isSafeFile,
        isPrivacyBlockDisabled,
        isPrivacySensitive,
        hasApprovalPrefix,
        stripApprovalPrefix,
        extractPaths,
      };
    }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('privacy-block', e, { event: 'PreToolUse' });
    } catch (_) {}
    process.exit(0); // fail-open
  }
})();
