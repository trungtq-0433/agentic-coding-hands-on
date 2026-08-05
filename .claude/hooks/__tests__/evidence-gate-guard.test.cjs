#!/usr/bin/env node
'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.join(__dirname, '..', 'evidence-gate-guard.cjs');
const FIXTURES = path.join(__dirname, '..', 'lib', '__tests__', 'fixtures', 'evidence');

let counter = 0;
function writeTranscript(entries) {
  const p = path.join(os.tmpdir(), `evg-guard-${process.pid}-${counter++}.jsonl`);
  fs.writeFileSync(p, entries.map((e) => JSON.stringify(e)).join('\n'));
  return p;
}

const userText = (text) => ({ type: 'user', message: { role: 'user', content: text } });

/** Fresh scratch cwd with no plans/ or .claude/ dirs — locator resolves to null here. */
function makeScratchCwd() {
  return fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), `evg-guard-cwd-${process.pid}-${counter++}-`));
}

/** Run the guard with a payload + optional env/cwd overrides; parse its JSON output. */
function run(payload, { env = {}, cwd } = {}) {
  const out = execSync(`node "${HOOK}"`, {
    input: JSON.stringify(payload),
    encoding: 'utf8',
    env: { ...process.env, ...env },
    cwd,
  }) || '{}';
  return JSON.parse(out);
}

function denies(result) {
  return Boolean(result.hookSpecificOutput && result.hookSpecificOutput.permissionDecision === 'deny');
}

function bashCall(command, transcript_path, cwd) {
  return { tool_name: 'Bash', tool_input: { command }, transcript_path, cwd };
}

// ── hard stage: SEALED evidence -> allow ────────────────────────────────────

test('git push with a SEALED evidence dir is allowed', () => {
  const t = writeTranscript([userText('ship this to prod')]);
  const result = run(bashCall('git push origin main', t), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'valid-sealed') },
  });
  assert.ok(!denies(result));
});

// ── hard stage: non-SEALED evidence -> deny with an actionable reason ──────

test('git push with a missing-artifact evidence dir is denied', () => {
  const t = writeTranscript([userText('ship this to prod')]);
  const result = run(bashCall('git push origin main', t), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'missing-artifact') },
  });
  assert.ok(denies(result));
  const reason = result.hookSpecificOutput.permissionDecisionReason;
  assert.match(reason, /not SEALED/);
  assert.match(reason, /Bypass/);
});

test('gh pr create with a failed-command evidence dir is denied', () => {
  const t = writeTranscript([userText('open the pr now')]);
  const result = run(bashCall('gh pr create --title x --body y', t), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'failed-command') },
  });
  assert.ok(denies(result));
});

// ── hard stage: no evidence dir located -> fail open, advisory only ───────

test('git push with no locatable evidence dir fails open (advisory, not deny)', () => {
  const cwd = makeScratchCwd();
  const t = writeTranscript([userText('git push please')]);
  const result = run(bashCall('git push origin main', t, cwd), {
    env: { TKM_EVIDENCE_DIR: '' },
    cwd,
  });
  assert.ok(!denies(result));
  assert.ok(result.hookSpecificOutput && /no evidence directory/.test(result.hookSpecificOutput.additionalContext || ''));
});

// ── soft stage: typed ship verb, no ship Bash command -> advisory only ────

test('a neutral Bash command with a typed "ship" prompt is advisory, not a deny', () => {
  const t = writeTranscript([userText("let's ship this feature")]);
  const result = run(bashCall('ls -la', t), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'missing-artifact') },
  });
  assert.ok(!denies(result));
});

// ── no signal at all -> pass through silently ──────────────────────────────

test('an unrelated Bash command with no ship signal passes through with no output fields', () => {
  const t = writeTranscript([userText('refactor the parser')]);
  const result = run(bashCall('ls -la', t));
  assert.ok(!denies(result));
  assert.ok(!result.hookSpecificOutput);
});

// ── --skip-tests / --skip-review downgrade a hard stage to advisory ───────

test('git push with "--skip-tests" in the prompt downgrades to advisory even over a failing verdict', () => {
  const t = writeTranscript([userText('ship it now, --skip-tests since the suite is flaky')]);
  const result = run(bashCall('git push origin main', t), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'missing-artifact') },
  });
  assert.ok(!denies(result));
});

// ── internal error handling: fail open ─────────────────────────────────────

test('malformed stdin fails open (allows, no deny)', () => {
  const out = execSync(`node "${HOOK}"`, { input: 'not json', encoding: 'utf8' }) || '{}';
  const result = JSON.parse(out);
  assert.ok(!denies(result));
});

test('non-Bash tool_name passes through untouched', () => {
  const t = writeTranscript([userText('git push now')]);
  const result = run({ tool_name: 'Write', tool_input: {}, transcript_path: t });
  assert.ok(!denies(result));
});

// ── .tkm.json toggle: hooks."evidence-gate-guard": false -> never blocks ──

test('toggled off in .claude/.tkm.json allows even a failing hard-stage push', () => {
  const cwd = makeScratchCwd();
  fs.mkdirSync(path.join(cwd, '.claude'), { recursive: true });
  fs.writeFileSync(
    path.join(cwd, '.claude', '.tkm.json'),
    JSON.stringify({ hooks: { 'evidence-gate-guard': false } })
  );
  const t = writeTranscript([userText('ship this to prod')]);
  const result = run(bashCall('git push origin main', t, cwd), {
    env: { TKM_EVIDENCE_DIR: path.join(FIXTURES, 'missing-artifact') },
    cwd,
  });
  assert.ok(!denies(result));
});
