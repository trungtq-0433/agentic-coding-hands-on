#!/usr/bin/env node
/**
 * post-edit-simplify-reminder — PostToolUse / Edit+Write+MultiEdit hook. Forge → Inspect gate.
 *
 * Counts file edits across the session and injects a code-simplifier reminder
 * after the threshold is reached, nudging the agent toward the Inspect stage
 * before the review window closes. Counter resets when the simplifier runs.
 *
 * Threshold: 5+ distinct file edits → reminder (no more than once per 10 min).
 * Session state persisted to OS temp dir; auto-expires after 2 hours.
 */

// Crash wrapper
try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { invalidateCache } = require('./lib/git-info-cache.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  // Early exit if hook disabled in config
  if (!isHookEnabled('post-edit-simplify-reminder')) {
    process.exit(0);
  }

// Session state — persisted across hook invocations within the same session
const SESSION_TRACK_FILE = path.join(os.tmpdir(), 'tkm-simplify-session.json');
const EDIT_THRESHOLD = 5; // fire reminder after this many distinct file edits

/**
 * Load session tracking data, or initialize fresh if missing or stale (>2 h).
 */
function loadSessionData() {
  try {
    if (fs.existsSync(SESSION_TRACK_FILE)) {
      const data = JSON.parse(fs.readFileSync(SESSION_TRACK_FILE, 'utf8'));
      // Reset if session is older than 2 hours
      if (Date.now() - data.startTime > 2 * 60 * 60 * 1000) {
        return initSessionData();
      }
      return data;
    }
  } catch (e) {
    // Ignore errors, reinitialize
  }
  return initSessionData();
}

/**
 * Return a clean session record with zero counters.
 */
function initSessionData() {
  return {
    startTime: Date.now(),
    editCount: 0,
    modifiedFiles: [],
    lastReminder: 0,
    simplifierRun: false
  };
}

/**
 * Persist session tracking data. Write errors are non-fatal.
 */
function saveSessionData(data) {
  try {
    fs.writeFileSync(SESSION_TRACK_FILE, JSON.stringify(data, null, 2));
  } catch (e) {
    // Ignore write errors
  }
}

/**
 * Main hook logic — count the edit, maybe inject reminder.
 */
function main() {
  const timer = createHookTimer('post-edit-simplify-reminder', { event: 'PostToolUse' });
  try {
    let input = '';
    const stdin = fs.readFileSync(0, 'utf8');
    if (stdin) {
      input = stdin;
    }

    const hookData = JSON.parse(input || '{}');
    const toolName = hookData.tool_name || '';
    const toolInput = hookData.tool_input || {};

    // Only edit operations count toward the simplifier threshold
    const editTools = ['Edit', 'Write', 'MultiEdit'];
    if (!editTools.includes(toolName)) {
      timer.end({ tool: toolName, status: 'skip', exit: 0, note: 'non-edit-tool' });
      console.log(JSON.stringify({ continue: true }));
      return;
    }

    // Invalidate git cache so the statusline reflects the current working tree.
    // Use hookData.cwd (not process.cwd()) to handle subagent CWD mismatch.
    invalidateCache(hookData.cwd || process.cwd());

    const session = loadSessionData();

    session.editCount++;
    const filePath = toolInput.file_path || toolInput.path || '';
    if (filePath && !session.modifiedFiles.includes(filePath)) {
      session.modifiedFiles.push(filePath);
    }

    // Remind once the threshold is crossed, but at most once per 10 minutes
    const shouldRemind =
      session.editCount >= EDIT_THRESHOLD &&
      !session.simplifierRun &&
      (Date.now() - session.lastReminder > 10 * 60 * 1000); // Don't remind more than every 10 min

    let additionalContext = '';
    if (shouldRemind) {
      session.lastReminder = Date.now();
      additionalContext = `\n\n[Code Simplification Reminder] You have modified ${session.modifiedFiles.length} files in this session. Consider using the \`code-simplifier\` agent to refine recent changes before proceeding to code review. This is a MANDATORY step in the workflow.`;
    }

    saveSessionData(session);

    const result = {
      continue: true
    };

    if (additionalContext) {
      result.additionalContext = additionalContext;
    }

    timer.end({
      tool: toolName,
      status: 'ok',
      exit: 0,
      note: additionalContext ? 'reminder-injected' : 'tracked-edit'
    });
    console.log(JSON.stringify(result));

  } catch (e) {
    // Fail-open: tracking errors must not interrupt Forge
    logHookCrash('post-edit-simplify-reminder', e, { event: 'PostToolUse' });
    console.log(JSON.stringify({ continue: true }));
  }
  }

  main();
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('post-edit-simplify-reminder', e, { event: 'PostToolUse' });
  } catch (_) {}
  process.exit(0); // fail-open
}
