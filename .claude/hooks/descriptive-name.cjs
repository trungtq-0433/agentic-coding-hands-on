#!/usr/bin/env node
/**
 * descriptive-name — PreToolUse / Write hook. Forge stage.
 *
 * Fires before every Write call and injects naming guidance so files created
 * during Forge carry self-documenting names that LLM tools (Grep, Glob, Search)
 * can parse without opening the file. Always allow — this is advisory only.
 */

// Outer crash wrapper — fail-open so a broken hook never blocks a Write
try {
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  if (!isHookEnabled('descriptive-name')) {
    process.exit(0);
  }

  try {
  const timer = createHookTimer('descriptive-name', { event: 'PreToolUse', tool: 'Write' });
  let injectedPrompt = `## File naming guidance:
- Skip this guidance if you are creating markdown or plain text files
- Prefer kebab-case for JS/TS/Python/shell (.js, .ts, .py, .sh) with descriptive names
- Respect language conventions: C#/Java/Kotlin/Swift use PascalCase (.cs, .java, .kt, .swift), Go/Rust use snake_case (.go, .rs)
- Other languages: follow their ecosystem's standard naming convention
- Goal: self-documenting names for LLM tools (Grep, Glob, Search)`

  console.log(JSON.stringify({
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "additionalContext": injectedPrompt
    }
  }));

    timer.end({ status: 'ok', exit: 0 });
    // Advisory only — every path is allowed
    process.exit(0);

  } catch (error) {
    // Fail-open: hook errors must never block file creation
    console.error('WARN: Hook error, allowing operation -', error.message);
    logHookCrash('descriptive-name', error, { event: 'PreToolUse', tool: 'Write' });
    process.exit(0);
  }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('descriptive-name', e, { event: 'PreToolUse', tool: 'Write' });
  } catch (_) {}
  process.exit(0); // fail-open
}
