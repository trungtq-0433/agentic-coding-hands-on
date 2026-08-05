'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.join(__dirname, '..', 'precompact-guard.cjs');

function run(cwd) {
  const out = execSync(`node "${HOOK}"`, { input: JSON.stringify({ cwd }), encoding: 'utf8' }) || '{}';
  return JSON.parse(out);
}

function gitDir({ dirty }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'precompact-'));
  execSync('git init -q', { cwd: dir });
  fs.writeFileSync(path.join(dir, 'f.txt'), 'one');
  if (!dirty) {
    execSync('git add -A && git -c user.email=t@t -c user.name=t commit -qm init', { cwd: dir });
  }
  return dir;
}

test('injects a checkpoint reminder when the tree is dirty', () => {
  const dir = gitDir({ dirty: true });
  try {
    const r = run(dir);
    assert.strictEqual(r.continue, true, 'never blocks the compact');
    assert.ok(r.additionalContext, 'dirty tree must warn');
    assert.match(r.additionalContext, /uncommitted/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('stays silent on a clean tree', () => {
  const dir = gitDir({ dirty: false });
  try {
    const r = run(dir);
    assert.strictEqual(r.continue, true);
    assert.strictEqual(r.additionalContext, undefined);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('no-op outside a git repo', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'precompact-nogit-'));
  try {
    const r = run(dir);
    assert.strictEqual(r.continue, true);
    assert.strictEqual(r.additionalContext, undefined);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test('fail-open on malformed input', () => {
  const out = execSync(`node "${HOOK}"`, { input: 'not json', encoding: 'utf8' }) || '{}';
  const r = JSON.parse(out);
  assert.strictEqual(r.continue, true);
});
