'use strict';

/**
 * verdict-findings-location — machine-gates the `findings[]` array inside
 * `inspection-verdict.json`. Extracted out of evidence-validator.cjs to keep
 * that file under the project's 200-line ceiling; this module is the
 * enforcement half of the findings[]/location contract documented in
 * skills/_shared/references/evidence-artifacts.md.
 *
 * Schema intent (versioned by presence, not a counter):
 *   - findings[] ABSENT  → legacy verdict (pre-dates this field). Advisory
 *     only — a single warning, never a block, even at a hard stage. This is
 *     the transition path so in-flight verdicts don't suddenly break.
 *   - findings[] PRESENT → every finding with `disposition: "Accept"` (the
 *     adversarial-review vocabulary for "must fix") MUST carry a real
 *     `location` matching `path:NNN` or `path:NN-MM` (ascending range).
 *     `Reject`/`Defer` findings are not required to carry a location.
 */

const FINDING_KEYS = new Set(['severity', 'category', 'location', 'summary', 'disposition']);
const KNOWN_DISPOSITIONS = new Set(['Accept', 'Reject', 'Defer']);
const LOCATION_RE = /^[^\s:]+:(\d+)(?:-(\d+))?$/;

/** `path:NNN` or `path:NN-MM` with NN <= MM. No bare line numbers, no whitespace. */
function isValidLocation(loc) {
  if (typeof loc !== 'string') return false;
  const m = loc.match(LOCATION_RE);
  if (!m) return false;
  if (m[2] !== undefined && Number(m[2]) < Number(m[1])) return false;
  return true;
}

/**
 * Validate `findings[]`. `V` records a blocking-eligible violation (downgraded
 * to a warning at an advisory stage, same as every other verdict check). Legacy
 * verdicts (findings undefined) are reported through `W` instead — a message
 * that is ALWAYS advisory, never blocking, regardless of stage.
 */
function checkVerdictFindings(findings, V, W) {
  if (findings === undefined) {
    W('inspection-verdict has no findings[] — legacy verdict, location enforcement is advisory only until findings[] is adopted (see evidence-artifacts.md)');
    return;
  }
  if (!Array.isArray(findings)) { V('inspection-verdict findings must be an array'); return; }
  findings.forEach((f, i) => {
    if (!f || typeof f !== 'object' || Array.isArray(f)) { V(`inspection-verdict findings[${i}] is not an object`); return; }
    for (const k of Object.keys(f)) if (!FINDING_KEYS.has(k)) V(`inspection-verdict findings[${i}] has an unknown/extra key: ${k}`);
    if (!KNOWN_DISPOSITIONS.has(f.disposition)) { V(`inspection-verdict findings[${i}] has an invalid disposition: ${JSON.stringify(f.disposition)} (want Accept, Reject, or Defer)`); return; }
    if (f.disposition === 'Accept' && !isValidLocation(f.location)) {
      V(`inspection-verdict findings[${i}] is Accept but has no valid location (want path:NNN or path:NN-MM), got ${JSON.stringify(f.location)}`);
    }
  });
}

module.exports = { checkVerdictFindings, isValidLocation };
