#!/usr/bin/env node
/**
 * precompact-guard — PreCompact hook. Guards work-in-progress before the context
 * window is compacted.
 *
 * When the agent is mid-Forge with uncommitted changes, compaction can bury the
 * thread that explains them. This hook checks the working tree right before a
 * compact and, if it's dirty, injects a reminder to checkpoint first — commit or
 * stash the work and refresh TodoWrite so progress survives the summary.
 *
 * Advisory only (never blocks the compact); opt-out via `.tkm.json`
 * hooks.precompact-guard=false; fail-open on any error.
 */

try {
  const fs = require('fs');
  const { execSync } = require('child_process');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  if (!isHookEnabled('precompact-guard')) {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  /** Count uncommitted entries in the working tree; 0 when clean or not a repo. */
  function uncommittedCount(cwd) {
    try {
      const out = execSync('git status --porcelain', {
        cwd,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore'],
        timeout: 5000,
      });
      return out.split('\n').filter((l) => l.trim()).length;
    } catch {
      return 0; // not a git repo, or git unavailable — nothing to guard
    }
  }

  function main() {
    const timer = createHookTimer('precompact-guard', { event: 'PreCompact' });
    try {
      const data = JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
      const cwd = data.cwd || process.cwd();
      const dirty = uncommittedCount(cwd);

      const result = { continue: true };
      if (dirty > 0) {
        result.additionalContext =
          `\n\n[Checkpoint before compaction] ${dirty} uncommitted change(s) in the working tree. ` +
          `Before the context is compacted, preserve progress: commit or stash the work, and update ` +
          `TodoWrite so the remaining steps survive the summary.`;
      }

      timer.end({ status: 'ok', exit: 0, note: dirty > 0 ? 'wip-reminder' : 'clean' });
      process.stdout.write(JSON.stringify(result));
    } catch (e) {
      logHookCrash('precompact-guard', e, { event: 'PreCompact' });
      process.stdout.write(JSON.stringify({ continue: true }));
    }
  }

  main();
} catch (e) {
  try {
    require('./lib/hook-logger.cjs').logHookCrash('precompact-guard', e, { event: 'PreCompact' });
  } catch (_) {}
  process.stdout.write(JSON.stringify({ continue: true }));
  process.exit(0); // fail-open
}
