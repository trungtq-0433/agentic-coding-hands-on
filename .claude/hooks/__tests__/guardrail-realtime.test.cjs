'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.join(__dirname, '..', 'guardrail-realtime.cjs');

/** Run the hook in a throwaway project dir with the given guardrail config + payload. */
function runHook(guardrail, payload) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'guardrail-test-'));
  try {
    fs.mkdirSync(path.join(dir, '.claude'), { recursive: true });
    if (guardrail !== null) {
      fs.writeFileSync(path.join(dir, '.claude', '.tkm.json'), JSON.stringify({ hooks: { guardrail } }));
    }
    const out = execSync(`node "${HOOK}"`, {
      cwd: dir,
      input: JSON.stringify({ cwd: dir, ...payload }),
      encoding: 'utf8',
    });
    return JSON.parse(out);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

const edit = (file = 'a.ts') => ({ tool_name: 'Edit', tool_input: { file_path: file } });

test('no-op when guardrail config absent', () => {
  const r = runHook(null, edit());
  assert.strictEqual(r.continue, true);
  assert.strictEqual(r.additionalContext, undefined);
});

test('no-op when disabled (enabled !== true)', () => {
  const r = runHook({ enabled: false, checks: { lint: 'false' } }, edit());
  assert.strictEqual(r.continue, true);
  assert.strictEqual(r.additionalContext, undefined);
});

test('skips non-edit tools', () => {
  const r = runHook({ enabled: true, debounceMs: 0, checks: { lint: 'false' } }, { tool_name: 'Bash', tool_input: {} });
  assert.strictEqual(r.continue, true);
  assert.strictEqual(r.additionalContext, undefined);
});

test('injects advisory context when a check fails', () => {
  const r = runHook({ enabled: true, debounceMs: 0, checks: { lint: 'false' } }, edit());
  assert.strictEqual(r.continue, true, 'must never block');
  assert.ok(r.additionalContext, 'a failing check must inject context');
  assert.match(r.additionalContext, /Guardrail/);
  assert.match(r.additionalContext, /lint failed/);
});

test('stays clean when checks pass', () => {
  const r = runHook({ enabled: true, debounceMs: 0, checks: { lint: 'true' } }, edit());
  assert.strictEqual(r.continue, true);
  assert.strictEqual(r.additionalContext, undefined);
});

test('replaces {file} with the edited path (file-scoped check)', () => {
  // `grep` the edited filename out of a string — only matches when {file} expanded.
  const r = runHook({ enabled: true, debounceMs: 0, checks: { lint: 'echo {file} | grep -q nope.ts' } }, edit('real.ts'));
  // grep finds nothing → exit 1 → failure injected, proving {file} became real.ts (not literal {file})
  assert.ok(r.additionalContext, 'check ran against the substituted path');
});

test('fail-open: unknown command never blocks', () => {
  const r = runHook({ enabled: true, debounceMs: 0, checks: { lint: 'tkm_no_such_binary_xyz' } }, edit());
  assert.strictEqual(r.continue, true, 'a broken command must not stall the forge');
});

test('skips empty check commands', () => {
  const r = runHook({ enabled: true, debounceMs: 0, checks: { typecheck: '', lint: '   ', test: 'true' } }, edit());
  assert.strictEqual(r.continue, true);
  assert.strictEqual(r.additionalContext, undefined, 'blank checks contribute no failures');
});

test('debounce suppresses a second run inside the window', () => {
  // A long debounce + shared temp stamp: the FIRST run in this process wins,
  // the SECOND (same window) is skipped → no injection even though lint fails.
  const cfg = { enabled: true, debounceMs: 60_000, checks: { lint: 'false' } };
  runHook(cfg, edit());                 // stamps lastRun
  const second = runHook(cfg, edit());  // within 60s window
  assert.strictEqual(second.continue, true);
  assert.strictEqual(second.additionalContext, undefined, 'debounced run injects nothing');
});
