'use strict';

/**
 * graphify-cli — shared `graphify` CLI-location and throttle-marker helpers.
 * Extracted out of graph-reindex-sync.cjs so memory-graph-nudge.cjs (Phase 3,
 * plans/260716-1046-memory-graph-tier-auto) can reuse the same locateGraphify()
 * probe and marker throttle instead of duplicating the logic.
 *
 * Security: never resolves the graphify binary from a repo-tracked file — only
 * GRAPHIFY_BIN (test seam) or `graphify` on PATH.
 *
 * @module graphify-cli
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

/** Resolve the argv prefix used to invoke graphify, or null if unavailable. */
function locateGraphify() {
  if (process.env.GRAPHIFY_BIN) return [process.env.GRAPHIFY_BIN];
  try {
    execFileSync('graphify', ['--version'], { timeout: 5000, stdio: 'ignore' });
    return ['graphify'];
  } catch { /* not on PATH */ }
  // SECURITY: never resolve the binary from a repo-tracked file. Trust only
  // GRAPHIFY_BIN (test seam) and `graphify` on PATH. If neither, do nothing.
  return null;
}

/** Per-project tmp marker (base64url of path) so cross-session nudges throttle without littering the repo. */
function tmpMarker(name, projectDir) {
  const key = Buffer.from(projectDir).toString('base64url').slice(0, 64);
  return path.join(os.tmpdir(), `tkm-${name}-${key}`);
}

/** True if the marker file was touched within the throttle window. */
function recentlyTouched(marker, windowMs) {
  try { return (Date.now() - fs.statSync(marker).mtimeMs) < windowMs; }
  catch { return false; }
}

module.exports = {
  locateGraphify,
  tmpMarker,
  recentlyTouched,
};
