#!/usr/bin/env node
/**
 * graph-reindex-sync — SessionStart hook. Keeps the knowledge graph's CODE layer fresh.
 *
 * The Knowledge Graph is ON by default (config graphify.enabled). When enabled AND the
 * graphify CLI is available, this hook runs `graphify update .` — a code-only, AST,
 * NO-LLM re-extraction — to refresh (or create) the code graph each session. The run is
 * spawned DETACHED (never blocks session start) and THROTTLED via a lock marker (no
 * overlapping / rapid re-runs). Doc/semantic re-extraction (LLM) is NOT done here —
 * rebuild-spec owns that; this hook only NUDGES when docs changed since the graph built.
 *
 * Zero-impact when disabled: config graphify.enabled=false, env GRAPHIFY_DISABLE=1 /
 * REBUILD_NO_GRAPH=1, or the hook toggled off. Always exits 0 (fail-open).
 *
 * Security: never resolves the graphify binary from a repo-tracked file — only
 * GRAPHIFY_BIN (test seam) or `graphify` on PATH. Never writes to .git/hooks.
 *
 * Test seam: GRAPHIFY_BIN overrides the graphify executable (point it at a stub) so
 * unit tests assert behavior without a real graphify/pip/network.
 */

try {
  const fs = require('fs');
  const path = require('path');
  const { spawn } = require('child_process');
  const { isHookEnabled, isGraphifyEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');
  const { locateGraphify, tmpMarker, recentlyTouched } = require('./lib/graphify-cli.cjs');
  const docs = require('./lib/graph-docs-staleness.cjs');

  if (!isHookEnabled('graph-reindex-sync')) process.exit(0);

  const timer = createHookTimer('graph-reindex-sync', { event: 'SessionStart' });
  const REINDEX_THROTTLE_MS = 10 * 60 * 1000; // don't re-spawn within 10 min / while one is in flight

  function readStdin() {
    try {
      const raw = fs.readFileSync(0, 'utf8').trim();
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  function isGitRepo(dir) {
    try { return fs.existsSync(path.join(dir, '.git')); } catch { return false; }
  }

  function ensureGitignore(projectDir) {
    try {
      const gi = path.join(projectDir, '.gitignore');
      const existing = fs.existsSync(gi) ? fs.readFileSync(gi, 'utf8') : '';
      if (!existing.includes('graphify-out')) {
        const sep = (existing === '' || existing.endsWith('\n')) ? '' : '\n';
        fs.appendFileSync(gi, sep + 'graphify-out/\n');
      }
    } catch { /* best-effort */ }
  }

  /** Spawn `graphify update .` detached (code-only, no-LLM). Returns true if launched. */
  function spawnCodeReindex(argv, projectDir) {
    try {
      const child = spawn(argv[0], [...argv.slice(1), 'update', '.'], {
        cwd: projectDir, detached: true, stdio: 'ignore', windowsHide: true,
      });
      child.unref();
      return true;
    } catch {
      return false;
    }
  }

  function main() {
    const data = readStdin();
    const projectDir = data.cwd || process.cwd();

    // Disabled (config graphify.enabled=false, or env GRAPHIFY_DISABLE/REBUILD_NO_GRAPH) → no-op.
    if (!isGraphifyEnabled()) {
      timer.end({ status: 'ok', exit: 0, note: 'disabled' });
      process.exit(0);
    }

    const graphDir = path.join(projectDir, 'graphify-out');
    const graphPath = path.join(graphDir, 'graph.json');
    const graphExists = fs.existsSync(graphPath);

    const parts = [];
    const argv = locateGraphify();

    // --- Docs freshness: detect + nudge (advisory, throttled). Only meaningful with a graph.
    // Read built_at_commit BEFORE spawning the code re-index below, so a concurrent
    // `graphify update` can't change the graph mid-read. ---
    if (graphExists) {
      const { paths, uncommittedCount, head } = docs.detectStaleDocs(projectDir, graphPath);
      if (paths.length > 0 && !docs.alreadyNudged(graphDir, head, uncommittedCount)) {
        docs.recordNudge(graphDir, head, uncommittedCount);
        parts.push(docs.buildNudge(paths));
      }
    }

    // --- Code freshness: refresh/create the CODE graph (no-LLM), detached + throttled ---
    let reindexed = false;
    if (argv && (graphExists || isGitRepo(projectDir))) {
      const lock = path.join(graphDir, '.reindex.lock');
      if (!recentlyTouched(lock, REINDEX_THROTTLE_MS)) {
        try { fs.mkdirSync(graphDir, { recursive: true }); } catch { /* ignore */ }
        try { fs.writeFileSync(lock, String(Date.now())); } catch { /* ignore */ }
        ensureGitignore(projectDir);
        reindexed = spawnCodeReindex(argv, projectDir);
      }
    } else if (!argv && !graphExists && isGitRepo(projectDir)) {
      // graphify not installed and no graph yet → nudge once to build it (rebuild-spec installs + builds).
      const marker = tmpMarker('graphify-build-nudge', projectDir);
      if (!recentlyTouched(marker, 24 * 60 * 60 * 1000)) { // at most once/day
        try { fs.writeFileSync(marker, String(Date.now())); } catch { /* ignore */ }
        parts.push('Knowledge graph: run `/tkm:rebuild-spec` once to build the code knowledge graph (installs graphify, indexes the repo). After that it refreshes automatically each session.');
      }
    }

    if (parts.length) {
      console.log(JSON.stringify({
        hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: parts.join('\n\n') },
      }));
    }

    timer.end({ status: 'ok', exit: 0, note: `graph:${graphExists ? 1 : 0} reindex:${reindexed ? 1 : 0}` });
    process.exit(0);
  }

  try {
    main();
  } catch (error) {
    logHookCrash('graph-reindex-sync', error, { event: 'SessionStart' });
    process.exit(0); // fail-open
  }
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('graph-reindex-sync', e, { event: 'SessionStart' });
  } catch (_) {}
  process.exit(0); // fail-open
}
