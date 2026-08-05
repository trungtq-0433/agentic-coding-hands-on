'use strict';

// Tests for the inline gate CLI. It is a thin shell over evidence-validator:
// arg-parse → validate → print → exit. Exit 2 only when a hard stage blocks;
// fail-OPEN (exit 0) on internal crash, never on a real validation failure.

const { test } = require('node:test');
const assert = require('node:assert');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const CLI = path.join(__dirname, '..', 'evidence-gate.cjs');
const FIX = path.join(__dirname, '..', '..', '..', '..', 'hooks', 'lib', '__tests__', 'fixtures', 'evidence');

function run(args) {
  const r = spawnSync('node', [CLI, ...args], { encoding: 'utf8' });
  return { code: r.status, out: `${r.stdout}${r.stderr}` };
}

test('valid SEALED dir at hard stage → exit 0', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'valid-sealed'), '--stage', 'hard']);
  assert.strictEqual(r.code, 0, r.out);
});

test('missing evidence at hard stage → exit 2 with reasons', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'missing-artifact'), '--stage', 'hard']);
  assert.strictEqual(r.code, 2);
  assert.match(r.out, /temper-results|inspection-verdict|missing/i);
});

test('failed command at hard stage → exit 2', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'failed-command'), '--stage', 'hard']);
  assert.strictEqual(r.code, 2);
  assert.match(r.out, /fail/i);
});

test('same failed-command dir at advisory stage → exit 0 with warnings', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'failed-command'), '--stage', 'advisory']);
  assert.strictEqual(r.code, 0, r.out);
  assert.match(r.out, /warn/i);
});

test('leaked secret value is advisory — exit 0 even at hard stage', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'leaked-secret-value'), '--stage', 'hard']);
  assert.strictEqual(r.code, 0, r.out);
  assert.match(r.out, /secret|AKIA/i);
});

test('nonexistent dir at hard stage → exit 2 (cannot ship unproven)', () => {
  const r = run(['--evidence-dir', path.join(os.tmpdir(), 'tkm-no-such-evidence-dir-xyz'), '--stage', 'hard']);
  assert.strictEqual(r.code, 2);
});

test('nonexistent dir at advisory stage → exit 0 (warns only)', () => {
  const r = run(['--evidence-dir', path.join(os.tmpdir(), 'tkm-no-such-evidence-dir-xyz'), '--stage', 'advisory']);
  assert.strictEqual(r.code, 0, r.out);
});

test('missing --evidence-dir → fail-open exit 0 (never a hard block on bad invocation)', () => {
  const r = run(['--stage', 'hard']);
  assert.strictEqual(r.code, 0, r.out);
});

test('unspecified stage defaults to advisory → exit 0 on otherwise-blocking evidence', () => {
  const r = run(['--evidence-dir', path.join(FIX, 'failed-command')]);
  assert.strictEqual(r.code, 0, r.out);
});
