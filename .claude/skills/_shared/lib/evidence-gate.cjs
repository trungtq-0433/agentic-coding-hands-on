#!/usr/bin/env node
'use strict';

/**
 * evidence-gate — the inline gate a skill runs at its Deliver/ship boundary.
 *
 *   node evidence-gate.cjs --evidence-dir <absolute-dir> --stage <hard|advisory>
 *
 * A thin shell over hooks/lib/evidence-validator.cjs: parse args, validate, print
 * the verdict, exit. Exit 2 ONLY when a hard stage finds blocking violations;
 * otherwise exit 0. There is no global hook, no settings wiring, no config
 * toggle — the gate only runs when a skill invokes it, so there is nothing to
 * disarm and no session/branch plan to resolve. The caller passes the absolute
 * evidence dir it already knows from its plan context.
 *
 * Fail-OPEN: an internal crash (bad args, validator throwing) exits 0 so the gate
 * never wedges a workflow on its own bug. It fails CLOSED only on a real
 * validation failure at a hard stage — which is the whole point.
 */

const { validateEvidence } = require('../../../hooks/lib/evidence-validator.cjs');

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--evidence-dir') args.evidenceDir = argv[i + 1];
    else if (argv[i] === '--stage') args.stage = argv[i + 1];
  }
  return args;
}

try {
  const { evidenceDir, stage } = parseArgs(process.argv.slice(2));
  const resolvedStage = stage === 'hard' ? 'hard' : 'advisory';

  if (!evidenceDir) {
    // Misinvocation, not a validation failure — fail open, but say so loudly.
    process.stdout.write('evidence-gate: no --evidence-dir given; skipping (fail-open)\n');
    process.exit(0);
  }

  const result = validateEvidence({ evidenceDir, stage: resolvedStage });

  if (result.blocking.length) {
    process.stdout.write(`evidence-gate: BLOCKED (${resolvedStage}) — ${result.blocking.length} issue(s):\n`);
    for (const b of result.blocking) process.stdout.write(`  ✗ ${b}\n`);
  }
  if (result.warnings.length) {
    process.stdout.write(`evidence-gate: ${result.warnings.length} warning(s):\n`);
    for (const w of result.warnings) process.stdout.write(`  ! ${w}\n`);
  }
  if (result.ok && !result.warnings.length) {
    process.stdout.write(`evidence-gate: SEALED (${resolvedStage}) — evidence verified\n`);
  }

  process.exit(result.ok ? 0 : 2);
} catch (err) {
  // Internal crash → fail open. Never block a workflow on the gate's own bug.
  process.stdout.write(`evidence-gate: internal error, failing open — ${err.message}\n`);
  process.exit(0);
}
