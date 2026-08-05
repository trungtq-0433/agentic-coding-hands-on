#!/usr/bin/env node
/**
 * memory-graph-queue — Stop hook. Queues conversation deltas as .md fact-capture files
 * for later, LLM-driven extraction — tier-auto self-hosted KG memory
 * (plans/260716-1046-memory-graph-tier-auto).
 *
 * Deterministic file I/O only — NEVER calls the Agent tool (a hook can't; this only
 * queues). Live extraction happens next session via the Phase 3 nudge hook.
 *
 * Opt-in: OFF by default (config memoryGraph.enabled=false). Turn on via .tkm.json
 * (memoryGraph.enabled=true) or env MEMORY_GRAPH_DISABLE=1 for a hard kill switch.
 *
 * Exit codes: 0 always (fail-open, never blocks session end).
 */

try {
  const fs = require('fs');
  const { isHookEnabled, isMemoryGraphEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  if (!isHookEnabled('memory-graph-queue') || !isMemoryGraphEnabled()) process.exit(0);

  const {
    resolveQueueDir,
    filterTranscript,
    passesHeuristic,
    capTurns,
    renderMarkdown,
    writeQueueFile
  } = require('./lib/memory-graph-queue-lib.cjs');

  const timer = createHookTimer('memory-graph-queue', { event: 'Stop' });

  function readStdin() {
    try {
      const raw = fs.readFileSync(0, 'utf8').trim();
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  function main() {
    const data = readStdin();
    if (data.hook_event_name !== 'Stop') {
      timer.end({ status: 'ok', exit: 0, note: 'not-stop' });
      process.exit(0);
    }

    const sessionId = data.session_id;
    const cwd = data.cwd || process.cwd();
    if (!sessionId || !data.transcript_path) {
      timer.end({ status: 'ok', exit: 0, note: 'no-session-or-transcript' });
      process.exit(0);
    }

    const turns = filterTranscript(data.transcript_path);
    if (!passesHeuristic(turns)) {
      timer.end({ status: 'ok', exit: 0, note: `trivial:${turns.length}` });
      process.exit(0);
    }

    const capped = capTurns(turns);
    const markdown = renderMarkdown(capped, sessionId);
    const queueDir = resolveQueueDir(cwd);
    const result = writeQueueFile(queueDir, sessionId, markdown);

    timer.end({ status: 'ok', exit: 0, note: result.written ? `queued:${capped.length}` : result.reason });
    process.exit(0);
  }

  try {
    main();
  } catch (error) {
    logHookCrash('memory-graph-queue', error, { event: 'Stop' });
    process.exit(0);
  }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('memory-graph-queue', e, { event: 'Stop' });
  } catch (_) {}
  process.exit(0); // fail-open
}
