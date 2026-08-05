'use strict';

/**
 * verdict-risk-gate — machine-gates the optional `riskGate` object inside
 * `inspection-verdict.json`. Extracted out of evidence-validator.cjs to keep
 * that file under the project's 200-line ceiling; mirrors the presence-
 * versioned pattern in verdict-findings-location.cjs.
 *
 * Schema intent (versioned by presence, not a counter):
 *   - riskGate ABSENT → legacy or low-risk verdict. No block, ever — this is
 *     the transition path so verdicts written before this field existed (and
 *     any genuinely low-risk change) never break.
 *   - riskGate PRESENT with signoffRequired: true and humanSignedOff !== true
 *     → BLOCKS at a hard stage. A change touching a sensitive area (auth,
 *     secrets, deploy, DB migrations — see the trigger list in
 *     evidence-artifacts.md) cannot auto-finalize without a human's explicit
 *     sign-off.
 *   - riskGate PRESENT with humanSignedOff: true → passes, regardless of
 *     signoffRequired — the human already looked at it.
 */

const RISK_GATE_KEYS = new Set(['touchesSensitiveArea', 'signoffRequired', 'humanSignedOff']);

/**
 * Validate `riskGate`. `V` records a blocking-eligible violation (downgraded
 * to a warning at an advisory stage, same as every other verdict check).
 */
function checkVerdictRiskGate(riskGate, V) {
  if (riskGate === undefined) return; // absent = low-risk/legacy — never blocks
  if (riskGate === null || typeof riskGate !== 'object' || Array.isArray(riskGate)) {
    V('inspection-verdict riskGate must be an object');
    return;
  }
  for (const k of Object.keys(riskGate)) {
    if (!RISK_GATE_KEYS.has(k)) V(`inspection-verdict riskGate has an unknown/extra key: ${k}`);
  }
  if (riskGate.signoffRequired === true && riskGate.humanSignedOff !== true) {
    V('inspection-verdict riskGate.signoffRequired is true but humanSignedOff is not true — a sensitive-area change (auth/secrets/deploy/migrations) cannot auto-finalize without a human sign-off');
  }
}

module.exports = { checkVerdictRiskGate };
