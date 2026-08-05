'use strict';

const fs = require('fs');
const path = require('path');
const { loadConfig, resolvePlanPath } = require('./tkm-config-utils.cjs');

/**
 * evidence-dir-locator — resolve the evidence/ directory evidence-gate-guard.cjs
 * should validate against. First rung to hit wins:
 *
 *   1. explicit `explicitDir` (a caller-supplied override, e.g. a future CLI flag)
 *   2. env TKM_EVIDENCE_DIR
 *   3. `.claude/workflow-artifacts.json` pointer — `{ "evidenceDir": "..." }`
 *   4. the ACTIVE plan's `evidence/` dir — resolved via tkm-config-utils'
 *      resolvePlanPath()/session-state, never by directory recency.
 *
 * Rung 4 deliberately only trusts a *session*-resolved plan (the directive set
 * by set-active-plan.cjs), not a branch-name "suggested" match — same
 * convention tkm-config-utils already uses for getReportsPath()/
 * extractTaskListId() (branch matches are a hint, not an activation). A
 * recency walk over plans/ was here previously and got removed: an old,
 * abandoned plan's non-SEALED evidence/ could hard-block every future
 * `git push`, which is exactly the stale-plan hazard tkm-config-utils'
 * `resolvePlanPath` doc comment says 'mostRecent' resolution was removed for.
 *
 * Returns an absolute path, or null when nothing resolves — including the
 * case where an active plan exists but has no evidence/ subdir yet (the
 * caller then fails open, per ship-workflow.md Step 10: "no active plan ->
 * skip, note, continue"). Never throws — every rung fails soft to the next
 * one so a malformed pointer file or a config-load error degrades to "keep
 * looking", not a crash.
 */

/** Read `.claude/workflow-artifacts.json`'s evidenceDir pointer, or null. */
function readPointerFile(pointerPath) {
  try {
    const raw = JSON.parse(fs.readFileSync(pointerPath, 'utf8'));
    const dir = raw && typeof raw.evidenceDir === 'string' ? raw.evidenceDir : null;
    return dir && dir.trim() ? dir.trim() : null;
  } catch (_) {
    return null; // absent, malformed, or unreadable — not this rung's problem
  }
}

/**
 * The active (session-resolved) plan's `evidence/` dir if it exists on disk,
 * or null. Resolution itself is delegated entirely to tkm-config-utils —
 * this function does no directory walking or sorting of its own.
 */
function findActivePlanEvidenceDir(cwd, sessionId) {
  try {
    const config = loadConfig({ includeProject: false, includeAssertions: false, includeLocale: false });
    const resolved = resolvePlanPath(sessionId, config);
    // Only a 'session' resolution counts as ACTIVE for gating purposes — a
    // 'branch' match is a suggestion, not a directive (see resolvePlanPath doc).
    if (!resolved || resolved.resolvedBy !== 'session' || !resolved.path) return null;

    // TODO(deferred, follow-up finding L5): config.paths.plans is read via
    // loadConfig() against the real process.cwd(), not this function's `cwd`
    // param — a caller passing a non-default cwd (e.g. a multi-root install)
    // only ever sees the default "plans" layout for anything that isn't
    // already an absolute session-resolved path. Not fixed in this pass.
    const planPath = path.isAbsolute(resolved.path) ? resolved.path : path.resolve(cwd, resolved.path);
    const candidate = path.join(planPath, 'evidence');
    return fs.existsSync(candidate) ? candidate : null;
  } catch (_) {
    return null;
  }
}

/**
 * @param {object} [opts]
 * @param {string} [opts.explicitDir] - highest-precedence override
 * @param {string} [opts.cwd] - base dir for relative paths (default process.cwd())
 * @param {string} [opts.sessionId] - session id used to resolve the active plan (rung 4)
 * @returns {string|null} absolute evidence dir path, or null when unresolved
 */
function locateEvidenceDir(opts = {}) {
  const cwd = opts.cwd || process.cwd();

  for (const candidate of [opts.explicitDir, process.env.TKM_EVIDENCE_DIR]) {
    if (candidate && String(candidate).trim()) return path.resolve(cwd, String(candidate).trim());
  }

  const pointed = readPointerFile(path.join(cwd, '.claude', 'workflow-artifacts.json'));
  if (pointed) return path.resolve(cwd, pointed);

  const active = findActivePlanEvidenceDir(cwd, opts.sessionId || process.env.TKM_SESSION_ID || null);
  if (active) return active;

  return null;
}

module.exports = { locateEvidenceDir, findActivePlanEvidenceDir, readPointerFile };
