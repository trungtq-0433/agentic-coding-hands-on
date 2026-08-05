#!/usr/bin/env node
/**
 * memory-graph-nudge — SessionStart hook. Detects queued conversation deltas
 * (written by memory-graph-queue.cjs, the Stop hook) and nudges Claude to fold
 * them into the tier-auto knowledge graph live, this session — mirroring
 * graph-reindex-sync.cjs's doc-staleness nudge pattern
 * (plans/260716-1046-memory-graph-tier-auto, Phase 3).
 *
 * The hook itself never calls the LLM — it only emits `additionalContext`.
 * Claude, live in the new session, runs the `/graphify` skill with `--update`,
 * whose Step 3 Part B dispatches the same in-session `general-purpose` subagent
 * extraction the Stop-hook queue writer defers to — the host session is the LLM,
 * so no external API key is needed. NOTE: this no-key path lives in the skill, not
 * the bare CLI. A plain `graphify <queue-dir> --update` shell call fails on these
 * prose (.md) deltas with "no LLM API key found (… doc file(s) need semantic
 * extraction)" — only the skill dispatches subagents, so the nudge must route
 * through `/graphify`, never a bare CLI invocation.
 *
 * graphify-not-installed case: probes locateGraphify() and routes the nudge through
 * the `/graphify` skill's own self-install step instead of a bare CLI call that
 * would just fail on a machine that never ran it before.
 *
 * Opt-in: OFF by default (config memoryGraph.enabled=false), same gate as
 * memory-graph-queue.cjs. Always exits 0 (fail-open, never blocks session start).
 */

try {
  const fs = require('fs');
  const path = require('path');
  const { isHookEnabled, isMemoryGraphEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');
  const { locateGraphify, tmpMarker, recentlyTouched } = require('./lib/graphify-cli.cjs');
  const { resolveQueueDir } = require('./lib/memory-graph-queue-lib.cjs');

  if (!isHookEnabled('memory-graph-nudge') || !isMemoryGraphEnabled()) process.exit(0);

  const timer = createHookTimer('memory-graph-nudge', { event: 'SessionStart' });
  const NUDGE_THROTTLE_MS = 10 * 60 * 1000; // don't re-nudge within 10 min of the last nudge

  function readStdin() {
    try {
      const raw = fs.readFileSync(0, 'utf8').trim();
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  /** Count raw .md files with no graph yet, or newer than the tier-auto graph.json. */
  function countPending(queueDir, graphPath) {
    let files;
    try {
      files = fs.readdirSync(queueDir).filter((f) => f.endsWith('.md'));
    } catch {
      return 0;
    }
    if (!files.length) return 0;

    let graphMtime = 0;
    try { graphMtime = fs.statSync(graphPath).mtimeMs; } catch { /* no graph yet → every file counts */ }

    return files.filter((f) => {
      try { return fs.statSync(path.join(queueDir, f)).mtimeMs > graphMtime; }
      catch { return false; }
    }).length;
  }

  /** Nudge text branches on graphify availability — see phase-03 "Nudge string". */
  function buildNudge(count, queueDirRel, argv) {
    if (argv) {
      return (
        `Memory-graph: ${count} conversation delta(s) pending. Fold them into your personal ` +
        `knowledge graph now: run the \`/graphify\` skill with \`--update\` on \`${queueDirRel}\` ` +
        `— NOT a bare \`graphify ${queueDirRel} --update\` CLI call. Only the skill dispatches the ` +
        `in-session \`general-purpose\` subagents (the host session is the LLM, so no external API ` +
        `key is needed); the bare CLI would fail on these prose deltas with "no LLM API key found".`
      );
    }
    return (
      `Memory-graph: ${count} conversation delta(s) pending, but \`graphify\` isn't installed ` +
      `yet. Run the \`/graphify\` skill on \`${queueDirRel}\` (not a bare CLI call) — its own ` +
      `Step 1 self-installs the package (\`uv tool install graphifyy\` / \`pip install\`), then ` +
      `continue straight into \`--update\` on the same path. One-time cost; every session after ` +
      `this one just needs the shorter \`/graphify --update\` skill nudge above.`
    );
  }

  function main() {
    const data = readStdin();
    const cwd = data.cwd || process.cwd();

    const queueDir = resolveQueueDir(cwd); // <cwd>/memory-graph-out/raw (gitignored, Phase 2 lib)
    const graphPath = path.join(queueDir, 'graphify-out', 'graph.json');
    const pending = countPending(queueDir, graphPath);

    if (pending === 0) {
      timer.end({ status: 'ok', exit: 0, note: 'no-pending' });
      process.exit(0);
    }

    const marker = tmpMarker('memory-graph-nudge', cwd);
    if (recentlyTouched(marker, NUDGE_THROTTLE_MS)) {
      timer.end({ status: 'ok', exit: 0, note: 'throttled' });
      process.exit(0);
    }
    try { fs.writeFileSync(marker, String(Date.now())); } catch { /* best-effort */ }

    const argv = locateGraphify();
    const queueDirRel = path.relative(cwd, queueDir) || queueDir;
    const additionalContext = buildNudge(pending, queueDirRel, argv);

    console.log(JSON.stringify({
      hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext },
    }));

    timer.end({ status: 'ok', exit: 0, note: `pending:${pending} installed:${argv ? 1 : 0}` });
    process.exit(0);
  }

  try {
    main();
  } catch (error) {
    logHookCrash('memory-graph-nudge', error, { event: 'SessionStart' });
    process.exit(0);
  }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('memory-graph-nudge', e, { event: 'SessionStart' });
  } catch (_) {}
  process.exit(0); // fail-open
}
