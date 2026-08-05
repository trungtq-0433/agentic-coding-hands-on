#!/usr/bin/env node
/**
 * Session-state hook — preserves Forge progress so the next Study finds solid ground.
 *
 * Fires on three events:
 * - PostToolUse (Task/TaskCreate/TaskUpdate/TodoWrite) → refresh statusline activity cache
 * - Stop / SubagentStop → persist markdown state snapshot + refresh cache
 * - (legacy path) no event_name → load previous state text at SessionStart
 *
 * Exit codes:
 *   0 — always (fail-open, never blocks session)
 */

try {
  const fs = require('fs');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');

  if (!isHookEnabled('session-state')) process.exit(0);

  const {
    loadState,
    persistState,
    refreshStatuslineSnapshot
  } = require('./lib/session-state-manager.cjs');

  const TRACKED_POST_TOOL_EVENTS = new Set(['Task', 'TaskCreate', 'TaskUpdate', 'TodoWrite']);

  async function main() {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    const data = stdin ? JSON.parse(stdin) : {};
    const eventType = data.hook_event_name || null;

    if (eventType === 'PostToolUse') {
      const toolName = data.tool_name || '';
      if (TRACKED_POST_TOOL_EVENTS.has(toolName)) {
        await refreshStatuslineSnapshot(data);
      }
      console.log(JSON.stringify({ continue: true }));
      process.exit(0);
    }

    if (eventType === 'Stop' || eventType === 'SubagentStop') {
      await refreshStatuslineSnapshot(data);
      persistState(data, { eventType });
      process.exit(0);
    }

    // Legacy: hook wired to SessionStart — reproduce old load-state behavior.
    if (!eventType) {
      const isCompact = data.source === 'compact';
      if (data.source && data.source !== 'startup' && !isCompact) process.exit(0);

      const state = loadState(process.cwd());
      if (state) {
        if (isCompact) {
          console.log('\n--- Session State (Post-Compaction Recovery) ---');
          console.log(state);
          console.log('--- End Session State ---\n');
          console.log('Context was compacted. Above is your last saved progress. Resume from where you left off.');
          console.log('IMPORTANT: Re-read active plan files and todo list. Do NOT re-do completed work.');
        } else {
          console.log('\n--- Previous Session State ---');
          console.log(state);
          console.log('--- End Session State ---\n');
          console.log('Review above state from your last session. Continue where you left off or start fresh.');
        }
      }
      process.exit(0);
    }

    process.exit(0);
  }

  main().catch(() => {
    process.exit(0);
  });
} catch (e) {
  try {
    const fs = require('fs');
    const p = require('path');
    const logDir = p.join(__dirname, '.logs');
    if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
    fs.appendFileSync(
      p.join(logDir, 'hook-log.jsonl'),
      JSON.stringify({
        ts: new Date().toISOString(),
        hook: 'session-state',
        status: 'crash',
        error: e.message
      }) + '\n'
    );
  } catch (_) {}
  process.exit(0);
}
