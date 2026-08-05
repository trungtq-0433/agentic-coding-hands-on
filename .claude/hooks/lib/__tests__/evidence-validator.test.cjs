#!/usr/bin/env node
'use strict';

// Anti-faking matrix for the evidence validator. Written before the validator
// (TDD): every rule that decides block/pass is locked here first. The real
// guarantee is this matrix staying green — not the order it was authored in.

const { test } = require('node:test');
const assert = require('node:assert');
const path = require('node:path');

const {
  validateEvidence,
  buildTemperResults,
} = require('../evidence-validator.cjs');

const FIX = path.join(__dirname, 'fixtures', 'evidence');
const dir = (name) => path.join(FIX, name);

// ── validateEvidence: hard-stage policy ────────────────────────────────────

test('valid SEALED evidence passes at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('valid-sealed'), stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.strictEqual(r.blocking.length, 0);
  assert.strictEqual(r.stage, 'hard');
});

test('missing artifact blocks at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('missing-artifact'), stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /temper-results|inspection-verdict|missing/i.test(b)));
});

test('a failed command blocks at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('failed-command'), stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /fail/i.test(b)));
});

test('faked string exitCode blocks at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('faked-exitcode-string'), stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /exitCode|integer/i.test(b)));
});

test('an unknown/extra key blocks at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('extra-key'), stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /unknown|extra|sneaky/i.test(b)));
});

test('unproven claims + UNKNOWN contract block at hard stage', () => {
  const r = validateEvidence({ evidenceDir: dir('hard-stage-unproven'), stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /unproven/i.test(b)));
  assert.ok(r.blocking.some((b) => /contract|UNKNOWN/i.test(b)));
});

// ── C1: a non-object artifact (JSON null / array) must BLOCK, not crash ─────

test('a null inspection-verdict.json blocks at hard stage (no crash / no fail-open bypass)', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), 'null');
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false, JSON.stringify(r));
  assert.ok(r.blocking.length > 0);
});

test('a null study-context.json blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.writeFileSync(path.join(tmp, 'study-context.json'), 'null');
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
});

test('an array (non-object) artifact blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.writeFileSync(path.join(tmp, 'study-context.json'), '[1,2,3]');
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
});

// ── H1: forged status:pass with a non-zero exitCode must block ──────────────

test('a forged status:pass with non-zero exitCode blocks even when a real pass exists', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  fs.writeFileSync(path.join(tmp, 'temper-results.json'), JSON.stringify({ commands: [
    { command: 'real', exitCode: 0, status: 'pass', summary: 'green', ts: '2026-06-16T00:00:00.000Z' },
    { command: 'forged', exitCode: 1, status: 'pass', summary: 'claims pass but exit 1', ts: '2026-06-16T00:00:00.000Z' },
  ] }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false, JSON.stringify(r));
  assert.ok(r.blocking.some((b) => /status|exitCode|inconsistent/i.test(b)));
});

// ── M1: empty acceptanceCovered / regressionChecked block at hard stage ─────

test('empty acceptanceCovered blocks at hard stage (nothing proven)', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: [], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /acceptanceCovered/i.test(b)));
});

test('empty regressionChecked blocks at hard stage (nothing walked)', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['x'], regressionChecked: [],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /regressionChecked/i.test(b)));
});

// ── subset-check: every study criterion must be covered by the verdict ──────

test('a study criterion not echoed in acceptanceCovered blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.writeFileSync(path.join(tmp, 'study-context.json'), JSON.stringify({
    task: 't', mode: 'auto', acceptanceCriteria: ['gate blocks a faked ship', 'gate passes a real ship'],
    touchpoints: ['a'], blastRadius: ['b'], contracts: ['c'],
  }));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED',
    acceptanceCovered: ['gate blocks a faked ship'], // second criterion not covered
    regressionChecked: ['ok'], contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /cover the criterion|gate passes a real ship/i.test(b)));
});

test('all study criteria echoed in acceptanceCovered pass at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.writeFileSync(path.join(tmp, 'study-context.json'), JSON.stringify({
    task: 't', mode: 'auto', acceptanceCriteria: ['gate blocks a faked ship', 'gate passes a real ship'],
    touchpoints: ['a'], blastRadius: ['b'], contracts: ['c'],
  }));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED',
    acceptanceCovered: ['proved: gate blocks a faked ship', 'proved: gate passes a real ship'],
    regressionChecked: ['ok'], contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});

// ── H2: a raw-runs file must NOT be mistaken for a temper artifact ──────────

test('a raw-runs sidecar file does not false-block (excluded from temper glob)', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  // tester drops raw runs as a bare array under a raw-* name; must be ignored.
  fs.writeFileSync(path.join(tmp, 'raw-temper-runs.json'), JSON.stringify([{ command: 'x', exitCode: 0, stdout: 'ok' }]));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});

// ── secret-scan: ADVISORY only, never blocking ─────────────────────────────

test('a leaked secret value warns but never blocks (even at hard stage)', () => {
  const r = validateEvidence({ evidenceDir: dir('leaked-secret-value'), stage: 'hard' });
  // The secret rule must not be the thing that blocks — this evidence is
  // otherwise valid SEALED, so it must PASS, with the secret only as a warning.
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.ok(r.warnings.some((w) => /secret|AKIA/i.test(w)));
  assert.ok(!r.blocking.some((b) => /secret|AKIA/i.test(b)));
});

// ── score never auto-approves ──────────────────────────────────────────────

test('a high score with a non-SEALED decision still blocks at hard stage', () => {
  // Build the evidence inline so the only failing axis is the decision.
  const tmp = require('node:fs').mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  const fs = require('node:fs');
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 10, criticalCount: 0, decision: 'BLOCKED',
    acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /decision|SEALED|BLOCKED/i.test(b)));
});

// ── non-hard stage = advisory: violations downgrade to warnings ────────────

test('failed command at advisory stage warns, never blocks', () => {
  const r = validateEvidence({ evidenceDir: dir('failed-command'), stage: 'advisory' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.strictEqual(r.blocking.length, 0);
  assert.ok(r.warnings.length > 0);
});

test('missing artifact at advisory stage warns, never blocks', () => {
  const r = validateEvidence({ evidenceDir: dir('missing-artifact'), stage: 'advisory' });
  assert.strictEqual(r.ok, true);
  assert.strictEqual(r.blocking.length, 0);
  assert.ok(r.warnings.length > 0);
});

// ── buildTemperResults: code constructs the artifact, exitCode always int ───

test('buildTemperResults coerces exitCode to a real integer', () => {
  const out = buildTemperResults([
    { command: 'npm test', exitCode: '0', stdout: 'ok\nmore', ts: '2026-06-16T00:00:00.000Z' },
  ]);
  assert.strictEqual(typeof out.commands[0].exitCode, 'number');
  assert.strictEqual(Number.isInteger(out.commands[0].exitCode), true);
  assert.strictEqual(out.commands[0].exitCode, 0);
});

test('buildTemperResults derives status from exitCode when absent', () => {
  const out = buildTemperResults([
    { command: 'a', exitCode: 0, stdout: 'good' },
    { command: 'b', exitCode: 2, stdout: 'bad' },
  ]);
  assert.strictEqual(out.commands[0].status, 'pass');
  assert.strictEqual(out.commands[1].status, 'fail');
});

test('buildTemperResults always supplies a non-empty summary', () => {
  const out = buildTemperResults([{ command: 'a', exitCode: 0, stdout: 'first line\nsecond' }]);
  assert.ok(out.commands[0].summary && out.commands[0].summary.length > 0);
});

test('buildTemperResults output validates as a real temper artifact', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  const out = buildTemperResults([{ command: 'node --test', exitCode: 0, stdout: 'all green' }]);
  fs.writeFileSync(path.join(tmp, 'temper-results.json'), JSON.stringify(out));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});

// ── findings[]: machine-gated file:line location ───────────────────────────

test('an Accept finding without a valid location blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [{ severity: 'Critical', category: 'Security', location: '', summary: 'SQL injection', disposition: 'Accept' }],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false, JSON.stringify(r));
  assert.ok(r.blocking.some((b) => /findings\[0\].*location/i.test(b)));
});

test('legacy verdict without findings[] passes at hard stage with an advisory warning only', () => {
  const r = validateEvidence({ evidenceDir: dir('valid-sealed'), stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.strictEqual(r.blocking.length, 0);
  assert.ok(r.warnings.some((w) => /no findings\[\]|legacy verdict/i.test(w)));
});

test('well-formed findings[] with valid locations (incl. a range and a monorepo path) pass at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [
      { severity: 'Critical', category: 'Security', location: 'src/app.ts:42', summary: 'SQL injection', disposition: 'Accept' },
      { severity: 'Medium', category: 'Assumption', location: 'takumi-kit/claude/hooks/lib/evidence-validator.cjs:120-125', summary: 'null deref', disposition: 'Accept' },
      { severity: 'Low', category: 'Observability', location: 'src/log.ts:10', summary: 'missing log context', disposition: 'Reject' },
      { severity: 'Low', category: 'Failure', summary: 'no rate limiting', disposition: 'Defer' },
    ],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.ok(!r.warnings.some((w) => /legacy verdict/i.test(w)));
});

test('an invalid disposition value blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [{ severity: 'Low', category: 'Style', location: 'a.ts:1', summary: 'nit', disposition: 'Maybe' }],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /invalid disposition/i.test(b)));
});

test('a descending line range (NN-MM with MM < NN) is not a valid location and blocks an Accept finding', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [{ severity: 'Critical', category: 'Security', location: 'a.ts:50-10', summary: 'bad range', disposition: 'Accept' }],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /findings\[0\].*location/i.test(b)));
});

test('an unknown key inside a finding blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [{ severity: 'Low', category: 'Style', location: 'a.ts:1', summary: 'nit', disposition: 'Reject', sneaky: true }],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /unknown|extra/i.test(b)));
});

test('findings[] location violations downgrade to warnings at advisory stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), JSON.stringify({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
    findings: [{ severity: 'Critical', category: 'Security', location: 'missing', summary: 'SQL injection', disposition: 'Accept' }],
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'advisory' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.ok(r.warnings.some((w) => /findings\[0\].*location/i.test(w)));
});

// ── return shape ───────────────────────────────────────────────────────────

test('validateEvidence returns the documented shape', () => {
  const r = validateEvidence({ evidenceDir: dir('valid-sealed'), stage: 'hard' });
  assert.ok(typeof r.ok === 'boolean');
  assert.ok(Array.isArray(r.blocking));
  assert.ok(Array.isArray(r.warnings));
  assert.ok(typeof r.stage === 'string');
});

// ── riskGate: high-risk auto-stop ──────────────────────────────────────────

function sealedVerdictWith(extra) {
  return JSON.stringify(Object.assign({
    score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['does X'], regressionChecked: ['ok'],
    contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [],
  }, extra));
}

test('riskGate.signoffRequired without humanSignedOff blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), sealedVerdictWith({
    riskGate: { touchesSensitiveArea: true, signoffRequired: true, humanSignedOff: false },
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false, JSON.stringify(r));
  assert.ok(r.blocking.some((b) => /riskGate|signoffRequired|human sign-off/i.test(b)));
});

test('riskGate.signoffRequired with humanSignedOff: true passes at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), sealedVerdictWith({
    riskGate: { touchesSensitiveArea: true, signoffRequired: true, humanSignedOff: true },
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});

test('a verdict with no riskGate at all passes at hard stage (legacy/low-risk)', () => {
  const r = validateEvidence({ evidenceDir: dir('valid-sealed'), stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.strictEqual(r.blocking.length, 0);
});

test('riskGate with signoffRequired: false and no humanSignedOff passes at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), sealedVerdictWith({
    riskGate: { touchesSensitiveArea: false, signoffRequired: false, humanSignedOff: false },
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});

test('riskGate.signoffRequired without humanSignedOff downgrades to a warning at advisory stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), sealedVerdictWith({
    riskGate: { touchesSensitiveArea: true, signoffRequired: true, humanSignedOff: false },
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'advisory' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
  assert.ok(r.warnings.some((w) => /riskGate|signoffRequired/i.test(w)));
});

test('an unknown key inside riskGate blocks at hard stage', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'temper-results.json'), path.join(tmp, 'temper-results.json'));
  fs.writeFileSync(path.join(tmp, 'inspection-verdict.json'), sealedVerdictWith({
    riskGate: { touchesSensitiveArea: true, signoffRequired: false, humanSignedOff: false, sneaky: true },
  }));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, false);
  assert.ok(r.blocking.some((b) => /riskGate.*unknown|extra/i.test(b)));
});

// ── aggregation of parallel per-instance temper files ──────────────────────

test('validator aggregates temper-results-<label>.json files', () => {
  const fs = require('node:fs');
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'ev-'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'study-context.json'), path.join(tmp, 'study-context.json'));
  fs.copyFileSync(path.join(dir('valid-sealed'), 'inspection-verdict.json'), path.join(tmp, 'inspection-verdict.json'));
  fs.writeFileSync(path.join(tmp, 'temper-results-unit.json'), JSON.stringify(buildTemperResults([{ command: 'unit', exitCode: 0, stdout: 'ok' }])));
  fs.writeFileSync(path.join(tmp, 'temper-results-e2e.json'), JSON.stringify(buildTemperResults([{ command: 'e2e', exitCode: 0, stdout: 'ok' }])));
  const r = validateEvidence({ evidenceDir: tmp, stage: 'hard' });
  assert.strictEqual(r.ok, true, JSON.stringify(r.blocking));
});
