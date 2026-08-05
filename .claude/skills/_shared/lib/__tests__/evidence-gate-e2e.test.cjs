'use strict';

// End-to-end scenario for the inline evidence gate. Builds throwaway evidence
// dirs (no git, no hook payload — the gate takes a directory, not a repo) and
// asserts the CLI's exit codes. This is the acceptance gate for the gate itself:
// faked/missing/failed evidence is blocked at a hard stage; real SEALED passes;
// advisory never blocks.

const { test } = require('node:test');
const assert = require('node:assert');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const CLI = path.join(__dirname, '..', 'evidence-gate.cjs');
const { buildTemperResults } = require('../../../../hooks/lib/evidence-validator.cjs');

const STUDY = { task: 't', mode: 'auto', acceptanceCriteria: ['x'], touchpoints: ['a'], blastRadius: ['b'], contracts: ['c'] };
const SEALED = { score: 9, criticalCount: 0, decision: 'SEALED', acceptanceCovered: ['x'], regressionChecked: ['b'], contractStatus: 'OK', refuted: [], unproven: [], reachableRegressions: [] };

function mkEvidence(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ev-e2e-'));
  for (const [name, obj] of Object.entries(files)) {
    fs.writeFileSync(path.join(dir, name), typeof obj === 'string' ? obj : JSON.stringify(obj));
  }
  return dir;
}

function gate(dir, stage) {
  const r = spawnSync('node', [CLI, '--evidence-dir', dir, '--stage', stage], { encoding: 'utf8' });
  return { code: r.status, out: `${r.stdout}${r.stderr}` };
}

const cleanup = [];
function track(dir) { cleanup.push(dir); return dir; }
process.on('exit', () => { for (const d of cleanup) try { fs.rmSync(d, { recursive: true, force: true }); } catch {} });

test('(a) missing artifact + hard → exit 2', () => {
  const dir = track(mkEvidence({ 'study-context.json': STUDY }));
  assert.strictEqual(gate(dir, 'hard').code, 2);
});

test('(b) failed command + hard → exit 2', () => {
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': { commands: [{ command: 'x', exitCode: 1, status: 'fail', summary: 'red', ts: '2026-06-16T00:00:00.000Z' }] },
    'inspection-verdict.json': SEALED,
  }));
  assert.strictEqual(gate(dir, 'hard').code, 2);
});

test('(c1) faked string exitCode + hard → exit 2', () => {
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': { commands: [{ command: 'x', exitCode: '0', status: 'pass', summary: 'fake', ts: '2026-06-16T00:00:00.000Z' }] },
    'inspection-verdict.json': SEALED,
  }));
  assert.strictEqual(gate(dir, 'hard').code, 2);
});

test('(c2) extra/injected key + hard → exit 2', () => {
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': { commands: [{ command: 'x', exitCode: 0, status: 'pass', summary: 'ok', ts: '2026-06-16T00:00:00.000Z', injected: true }] },
    'inspection-verdict.json': SEALED,
  }));
  assert.strictEqual(gate(dir, 'hard').code, 2);
});

test('(d) leaked secret VALUE is advisory — surfaced as a warning, never the thing that blocks', () => {
  // Otherwise-valid SEALED with a secret in a summary → PASSES at hard, secret only warns.
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': buildTemperResults([{ command: 'deploy', exitCode: 0, stdout: 'used AKIAIOSFODNN7EXAMPLE', ts: '2026-06-16T00:00:00.000Z' }]),
    'inspection-verdict.json': SEALED,
  }));
  const r = gate(dir, 'hard');
  assert.strictEqual(r.code, 0, r.out);
  assert.match(r.out, /secret|AKIA/i);
});

test('(d2) a secret co-occurring with a real violation still exits 2 (blocked by the violation, secret surfaced)', () => {
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': { commands: [{ command: 'deploy', exitCode: 1, status: 'fail', summary: 'failed with key AKIAIOSFODNN7EXAMPLE', ts: '2026-06-16T00:00:00.000Z' }] },
    'inspection-verdict.json': SEALED,
  }));
  const r = gate(dir, 'hard');
  assert.strictEqual(r.code, 2, r.out);
  assert.match(r.out, /fail/i);
  assert.match(r.out, /secret|AKIA/i);
});

test('(e) valid SEALED + all-pass + hard → exit 0', () => {
  const dir = track(mkEvidence({
    'study-context.json': STUDY,
    'temper-results.json': buildTemperResults([{ command: 'node --test', exitCode: 0, stdout: 'all green', ts: '2026-06-16T00:00:00.000Z' }]),
    'inspection-verdict.json': SEALED,
  }));
  assert.strictEqual(gate(dir, 'hard').code, 0);
});

test('(f) same blocking evidence at advisory → exit 0 + warnings', () => {
  const dir = track(mkEvidence({ 'study-context.json': STUDY })); // missing temper + verdict
  const r = gate(dir, 'advisory');
  assert.strictEqual(r.code, 0, r.out);
  assert.match(r.out, /warn/i);
});
