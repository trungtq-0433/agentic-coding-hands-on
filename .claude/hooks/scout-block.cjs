#!/usr/bin/env node
/**
 * scout-block.cjs — PreToolUse guard: blocks access to high-noise directories
 * (node_modules, dist, generated output) so the agent's context stays focused.
 * Fires in the Study and Forge stages before file or Bash tools execute.
 *
 * Pattern source: shipped .claude/.skignore baseline + optional per-project
 * override at <git-root>/.claude/.skignore. Both follow gitignore spec via the
 * 'ignore' package; negation (!) unlocks specific paths.
 *
 * Build-command allowlist: npm/pnpm/yarn/bun build, go build, cargo build,
 * make, mvn, gradle, docker build, kubectl, terraform — all pass through even
 * when they reference blocked paths.
 *
 * Exit codes: 0 = allowed, 2 = blocked.
 *
 * Pure matching logic lives in lib/scout-checker.cjs (shared with other runtimes).
 */

// Outer try catches require() failures so the hook never stalls the agent
try {
  const fs = require('fs');
  const path = require('path');

  // Pull in the shared scout-checker facade
  const {
    checkScoutBlock,
    isBuildCommand,
    isVenvExecutable,
    isAllowedCommand
  } = require('./lib/scout-checker.cjs');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');

  // Bail early when the guard is disabled in .tkm.json
  if (!isHookEnabled('scout-block')) {
    process.exit(0);
  }

  // Error formatters stay local — they render Claude-specific terminal output
  const { formatBlockedError } = require('./scout-block/error-formatter.cjs');
  const { formatBroadPatternError } = require('./scout-block/broad-pattern-detector.cjs');

  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  try {
    const timer = createHookTimer('scout-block', { event: 'PreToolUse' });
    // Consume stdin in one shot (hooks are short-lived processes)
    const hookInput = fs.readFileSync(0, 'utf-8');

    // Empty input — fail open, consistent with other error paths below.
    if (!hookInput || hookInput.trim().length === 0) {
      timer.end({ status: 'warn', exit: 0, note: 'empty-input' });
      process.stdout.write('{}');
      process.exit(0);
    }

    let data;
    try {
      data = JSON.parse(hookInput);
    } catch (parseError) {
      // Fail open — unparseable input is not a reason to stall the agent
      console.error('WARN: JSON parse failed, allowing operation');
      timer.end({ status: 'warn', exit: 0, note: 'json-parse-failed', error: parseError.message });
      process.exit(0);
    }

    // Validate structure
    if (!data.tool_input || typeof data.tool_input !== 'object') {
      // Fail open — missing tool_input means nothing to block
      console.error('WARN: Invalid JSON structure, allowing operation');
      timer.end({ status: 'warn', exit: 0, note: 'invalid-structure' });
      process.exit(0);
    }

    const toolInput = data.tool_input;
    const toolName = data.tool_name || 'unknown';
    const claudeDir = path.dirname(__dirname); // hooks/ → .claude/
    const payloadCwd = typeof data.cwd === 'string' && data.cwd.trim()
      ? data.cwd
      : process.cwd();

    // Delegate path/command analysis to the shared scout-checker
    const result = checkScoutBlock({
      toolName,
      toolInput,
      options: {
        claudeDir,
        cwd: payloadCwd,
        projectConfigDirName: '.claude',
        skignorePath: path.join(claudeDir, '.skignore'),
        checkBroadPatterns: true
      }
    });

    // Build/tool commands pass through unconditionally
    if (result.isAllowedCommand) {
      timer.end({ tool: toolName, status: 'ok', exit: 0, note: 'allowed-command' });
      process.exit(0);
    }

    // Overly broad glob — redirect agent to a more precise pattern
    if (result.blocked && result.isBroadPattern) {
      const errorMsg = formatBroadPatternError({
        blocked: true,
        reason: result.reason,
        suggestions: result.suggestions
      }, claudeDir);
      // timer.end keeps exit:2 — telemetry semantic, decoupled from process exit
      timer.end({
        tool: toolName,
        status: 'block',
        exit: 2,
        target: result.pattern || toolInput.path || toolInput.file_path || '',
        note: result.reason || 'broad-pattern'
      });
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: errorMsg
        }
      }));
      process.exit(0);
    }

    // .skignore match — block with path + pattern in the error message
    if (result.blocked) {
      const errorMsg = formatBlockedError({
        path: result.path,
        pattern: result.pattern,
        tool: toolName,
        claudeDir: claudeDir,
        configPath: result.configPath
      });
      // timer.end keeps exit:2 — telemetry semantic, decoupled from process exit
      timer.end({
        tool: toolName,
        status: 'block',
        exit: 2,
        target: result.path || '',
        note: result.pattern || 'blocked-path'
      });
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: errorMsg
        }
      }));
      process.exit(0);
    }

    // No blocked paths — allow
    timer.end({ tool: toolName, status: 'ok', exit: 0 });
    process.exit(0);

  } catch (error) {
    // Fail open — unexpected errors must not block agent progress
    console.error('WARN: Hook error, allowing operation -', error.message);
    logHookCrash('scout-block', error, { event: 'PreToolUse' });
    process.exit(0);
  }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('scout-block', e, { event: 'PreToolUse' });
  } catch (_) {}
  process.exit(0); // fail-open
}
