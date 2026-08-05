#!/usr/bin/env node
/**
 * Unit tests for claude/hooks/lib/rate-throttle.cjs.
 */

const { afterEach, beforeEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  readThrottleState,
  recentlyPrompted,
  persistLastShown,
  clearThrottleState,
  DEFAULT_WINDOW_MS,
} = require('../lib/rate-throttle.cjs');

let tmpDir;
let stateFile;

beforeEach(() => {
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-throttle-'));
  stateFile = path.join(tmpDir, 'sk-rate-state.json');
});

afterEach(() => {
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch { /* ignore */ }
});

describe('readThrottleState', () => {
  it('returns {} when file missing', () => {
    assert.deepStrictEqual(readThrottleState(stateFile), {});
  });

  it('returns {} on malformed JSON (no throw)', () => {
    fs.writeFileSync(stateFile, 'not-json');
    assert.deepStrictEqual(readThrottleState(stateFile), {});
  });

  it('returns {} when JSON is an array (guards against shape drift)', () => {
    fs.writeFileSync(stateFile, '[1,2,3]');
    assert.deepStrictEqual(readThrottleState(stateFile), {});
  });

  it('reads persisted state', () => {
    fs.writeFileSync(stateFile, JSON.stringify({ alice: 1234 }));
    assert.deepStrictEqual(readThrottleState(stateFile), { alice: 1234 });
  });
});

describe('recentlyPrompted', () => {
  it('returns true for empty/null login (never spams anon flows)', () => {
    assert.strictEqual(recentlyPrompted('', stateFile), true);
    assert.strictEqual(recentlyPrompted(null, stateFile), true);
  });

  it('returns false when login has no record', () => {
    assert.strictEqual(recentlyPrompted('alice', stateFile), false);
  });

  it('returns true within the 24h window', () => {
    const now = 10_000_000;
    fs.writeFileSync(stateFile, JSON.stringify({ alice: now - 1000 }));
    assert.strictEqual(recentlyPrompted('alice', stateFile, DEFAULT_WINDOW_MS, now), true);
  });

  it('returns false once past the window', () => {
    const now = 10_000_000;
    fs.writeFileSync(stateFile, JSON.stringify({ alice: now - (DEFAULT_WINDOW_MS + 1) }));
    assert.strictEqual(recentlyPrompted('alice', stateFile, DEFAULT_WINDOW_MS, now), false);
  });
});

describe('persistLastShown', () => {
  it('writes a new record atomically', () => {
    const ok = persistLastShown('alice', stateFile, 42);
    assert.strictEqual(ok, true);
    assert.deepStrictEqual(readThrottleState(stateFile), { alice: 42 });
  });

  it('merges with existing records', () => {
    fs.writeFileSync(stateFile, JSON.stringify({ bob: 1 }));
    persistLastShown('alice', stateFile, 42);
    assert.deepStrictEqual(readThrottleState(stateFile), { bob: 1, alice: 42 });
  });

  it('is a no-op for empty/null login', () => {
    assert.strictEqual(persistLastShown('', stateFile, 42), false);
    assert.strictEqual(persistLastShown(null, stateFile, 42), false);
    assert.strictEqual(fs.existsSync(stateFile), false);
  });
});

describe('clearThrottleState', () => {
  it('deletes the file if present', () => {
    fs.writeFileSync(stateFile, '{}');
    assert.strictEqual(clearThrottleState(stateFile), true);
    assert.strictEqual(fs.existsSync(stateFile), false);
  });

  it('returns false when file missing (no throw)', () => {
    assert.strictEqual(clearThrottleState(stateFile), false);
  });
});
