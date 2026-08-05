#!/usr/bin/env node
/**
 * iron-laws-guard — PreToolUse / Edit+Write hook. Forge → Temper gate.
 *
 * Fires before every Edit or Write on a production source file and injects
 * the Iron Law #1 TDD reminder: a failing test must exist before production
 * code changes. Skips test files, config/fixture/migration files, .sun/
 * artifacts, and skills/ — none of those are production logic under TDD.
 *
 * Always fail-open: a parse error must not block the Forge stage.
 */

let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const tool = data.tool_name || '';
    const toolInput = data.tool_input || {};

    // Only production-code writes trigger the TDD reminder
    if (!['Edit', 'Write'].includes(tool)) {
      process.stdout.write('{}');
      return;
    }

    const filePath = toolInput.file_path || '';

    // Non-source files carry no TDD obligation
    const sourceExtensions = /\.(ts|tsx|js|jsx|py|go|rs|java)$/;
    if (!sourceExtensions.test(filePath)) {
      process.stdout.write('{}');
      return;
    }

    // Skip test files, config files, and .sun/ artifacts
    const isTestFile = /\.(test|spec|e2e)\.(ts|tsx|js|jsx|py)$/.test(filePath);
    const isConfig = /(config|setup|fixture|mock|stub|seed|migration)/.test(filePath);
    const isSunFile = /\.sun\//.test(filePath);
    const isSkillFile = /skills\//.test(filePath);

    if (isTestFile || isConfig || isSunFile || isSkillFile) {
      process.stdout.write('{}');
      return;
    }

    // Production code touched — enforce Iron Law #1
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        additionalContext: "🔴 Iron Law #1 Reminder: Production code modified. Ensure a failing test exists BEFORE this code change. If writing test after code — delete the code, write test first, watch it fail, then write code."
      }
    }));
  } catch (e) {
    // Fail open
    process.stdout.write('{}');
  }
});
