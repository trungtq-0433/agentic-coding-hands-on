#!/usr/bin/env node
'use strict';

const { test } = require('node:test');
const assert = require('node:assert');

const { detectStage } = require('../stage-detector.cjs');

// ── hard stage: Bash command matches a real ship action ────────────────────

test('git push is a hard stage', () => {
  const r = detectStage({ bashCommand: 'git push origin main' });
  assert.strictEqual(r.stage, 'hard');
  assert.strictEqual(r.signal, 'git push');
});

test('gh pr create is a hard stage', () => {
  const r = detectStage({ bashCommand: 'gh pr create --title "x" --body "y"' });
  assert.strictEqual(r.stage, 'hard');
});

test('wrangler deploy is a hard stage', () => {
  const r = detectStage({ bashCommand: 'npx wrangler deploy' });
  assert.strictEqual(r.stage, 'hard');
});

test('npm publish is a hard stage', () => {
  const r = detectStage({ bashCommand: 'npm publish --access public' });
  assert.strictEqual(r.stage, 'hard');
});

test('an unrelated Bash command with no prompt signal is null', () => {
  const r = detectStage({ bashCommand: 'ls -la' });
  assert.strictEqual(r.stage, null);
});

test('git push wins over a mismatched prompt (hard beats soft)', () => {
  const r = detectStage({ bashCommand: 'git push', prompt: 'just running some checks' });
  assert.strictEqual(r.stage, 'hard');
});

// ── M2: hard-command matching must not false-match quotes/args, and must
//        recognize --dry-run as non-hard ──────────────────────────────────

test('git push quoted inside another command\'s string arg does not match', () => {
  const r = detectStage({ bashCommand: 'git commit -m "ready to git push"' });
  assert.strictEqual(r.stage, null);
});

test('git push quoted via echo does not match', () => {
  const r = detectStage({ bashCommand: 'echo "git push"' });
  assert.strictEqual(r.stage, null);
});

test('git push --dry-run is not a hard stage', () => {
  const r = detectStage({ bashCommand: 'git push --dry-run' });
  assert.notStrictEqual(r.stage, 'hard');
});

test('a chained "a && git push" is a hard stage', () => {
  const r = detectStage({ bashCommand: 'npm run build && git push' });
  assert.strictEqual(r.stage, 'hard');
  assert.strictEqual(r.signal, 'git push');
});

// ── soft stage: typed prompt names genuine shipping intent, no ship Bash
//    command yet ─────────────────────────────────────────────────────────

test('typed "ship" verb with a neutral Bash command is soft', () => {
  const r = detectStage({ bashCommand: 'ls -la', prompt: "let's ship this feature" });
  assert.strictEqual(r.stage, 'soft');
  assert.match(r.signal, /ship/);
});

test('typed "deploy" verb is soft', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'time to deploy to prod' });
  assert.strictEqual(r.stage, 'soft');
});

test('"open a pr" phrase is soft', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'open a pr for this' });
  assert.strictEqual(r.stage, 'soft');
});

test('"create a pr" phrase is soft', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'let\'s create a pr now' });
  assert.strictEqual(r.stage, 'soft');
});

test('"push the branch" phrase is soft', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'time to push the branch' });
  assert.strictEqual(r.stage, 'soft');
});

test('"ready to merge" phrase is soft', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'this is ready to merge' });
  assert.strictEqual(r.stage, 'soft');
});

test('"pr" inside another word ("prepare") does not match', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'prepare the release notes' });
  assert.strictEqual(r.stage, null);
});

// ── M3: bare push/merge/pr in ordinary prose must not fire the soft advisory ─

test('"merge conflict" prose does not trigger a soft signal', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'there was a merge conflict on main' });
  assert.strictEqual(r.stage, null);
});

test('"push notification" prose does not trigger a soft signal', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'you got a push notification' });
  assert.strictEqual(r.stage, null);
});

test('bare "pr" abbreviation with no shipping companion word does not trigger', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'the pr team handles public relations' });
  assert.strictEqual(r.stage, null);
});

// ── negation handling ───────────────────────────────────────────────────────

test('"don\'t ship" is negated -> no soft signal', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: "don't ship this yet" });
  assert.strictEqual(r.stage, null);
});

test('"not ready to deploy" is negated -> no soft signal', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: 'we are not ready to deploy' });
  assert.strictEqual(r.stage, null);
});

test('negation only suppresses the negated verb, not an earlier unnegated one', () => {
  const r = detectStage({ bashCommand: 'echo hi', prompt: "let's merge this, don't deploy yet" });
  assert.strictEqual(r.stage, 'soft');
  assert.match(r.signal, /merge/);
});

// ── no signal at all ────────────────────────────────────────────────────────

test('no bash command, no prompt -> null stage', () => {
  const r = detectStage({});
  assert.strictEqual(r.stage, null);
  assert.strictEqual(r.signal, null);
});
