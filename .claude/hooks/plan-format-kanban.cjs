#!/usr/bin/env node
/**
 * plan-format-kanban — PostToolUse hook. Blueprint stage.
 *
 * Fires after Edit/Write on any plan.md and enforces two Blueprint invariants:
 *   1. Phase link text must be human-readable, not raw filenames.
 *   2. Status column in the phases table must be updated via `ck plan check`
 *      rather than hand-edited — direct edits break canonical format.
 *
 * Reads the written file from disk; issues warnings as additionalContext but
 * always allows — never blocks the Blueprint commit.
 */

'use strict';

const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  const timer = createHookTimer('plan-format-kanban', { event: 'PostToolUse' });
  try {
    const data = JSON.parse(input);
    const toolName = data.tool_name || '';
    const filePath = data.tool_input?.file_path || data.tool_input?.path || '';

    // Only plan.md files carry the kanban phase table
    if (!filePath.endsWith('/plan.md')) {
      timer.end({ tool: toolName, status: 'skip', exit: 0, note: 'non-plan-file' });
      process.stdout.write(JSON.stringify({ continue: true }));
      return;
    }

    // Read the committed file — tool_input content may be a patch, not the full file
    const fs = require('fs');
    if (!fs.existsSync(filePath)) {
      timer.end({ tool: toolName, status: 'skip', exit: 0, note: 'file-missing' });
      process.stdout.write(JSON.stringify({ continue: true }));
      return;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    // Matches: [phase-01a-some-name.md](./...) — filename used as link text
    const badPattern = /\|\s*\d+[a-z]?\s*\|\s*\[phase-\d+[a-z]?-[^\]]*\.md\]\(/gi;
    const matches = content.match(badPattern);

    const warnings = [];

    if (matches && matches.length > 0) {
      warnings.push(
        '[!] plan.md: Link text should be human-readable, not filenames.',
        `    Found ${matches.length} instance(s) using filename as link text.`,
        '    Bad:  [phase-01-setup.md](./phase-01-setup.md)',
        '    Good: [Setup Environment](./phase-01-setup.md)',
        '    Update link text to descriptive phase names for better readability.'
      );
    }

    // Detect direct status edits in the phases table
    if (toolName === 'Edit' || toolName === 'Write') {
      const toolOutput = data.tool_input?.new_string || data.tool_input?.content || '';

      // Only flag table rows (lines starting with |) — avoids false positives
      // from frontmatter or prose that happen to contain status keywords.
      // Covers all values the shared normalizeStatus() recognizes.
      const lines = (toolOutput || '').split('\n');
      const editingTableStatus = lines.some(line => {
        // Must be a table row containing a phase ID AND a status keyword
        // Covers all values the shared normalizeStatus() recognizes
        return /^\|\s*\d+[a-z]?\s*\|/i.test(line) &&
               /\|\s*(Pending|In Progress|In-Progress|Completed|Complete|Done|Active|WIP)\s*\|/i.test(line);
      });

      // Warn only when a plan.md phases table row is being hand-edited
      if (editingTableStatus) {
        warnings.push(
          '\n[Plan Status Warning] Direct status edit detected in phases table.',
          'Canonical format: | Phase | Name | Status | (3-column table)',
          'Use CLI for deterministic status updates:',
          '  ck plan check <id>          # Mark completed',
          '  ck plan check <id> --start  # Mark in-progress',
          '  ck plan uncheck <id>        # Revert to pending',
          'Direct edits may break canonical format.'
        );
      }
    }

    if (warnings.length > 0) {
      timer.end({
        tool: toolName,
        status: 'warn',
        exit: 0,
        target: 'plan.md',
        note: `${warnings.length}-warning(s)`
      });
      process.stdout.write(JSON.stringify({ continue: true, additionalContext: warnings.join('\n') }));
      return;
    }

    timer.end({ tool: toolName, status: 'ok', exit: 0, target: 'plan.md' });
    process.stdout.write(JSON.stringify({ continue: true }));
  } catch (_err) {
    // Fail-open: hook errors must never stall Blueprint writes
    logHookCrash('plan-format-kanban', _err, { event: 'PostToolUse' });
    process.stdout.write(JSON.stringify({ continue: true }));
  }
});
