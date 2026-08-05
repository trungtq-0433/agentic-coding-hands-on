#!/usr/bin/env node
/**
 * Unit tests for claude/hooks/lib/milestone-marker.cjs.
 *
 * The marker writes into tkm-config-utils' per-session JSON file in tmpdir,
 * so tests just round-trip via readSessionState().
 */

const { afterEach, beforeEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { markMilestone, ALLOWED_KINDS, parseArgs } = require('../lib/milestone-marker.cjs');
const { readSessionState, getSessionTempPath } = require('../lib/tkm-config-utils.cjs');

let sessionId;

beforeEach(() => {
  sessionId = `test-${Date.now()}-${Math.random().toString(36).slice(2)}`;
});

afterEach(() => {
  // Clean the session state file created by updateSessionState.
  try { fs.unlinkSync(getSessionTempPath(sessionId)); } catch { /* ignore */ }
});

describe('parseArgs', () => {
  it('parses --k=v args', () => {
    assert.deepStrictEqual(parseArgs(['--kind=takumi', '--session-id=abc']), {
      kind: 'takumi',
      'session-id': 'abc',
    });
  });

  it('ignores positional args', () => {
    assert.deepStrictEqual(parseArgs(['positional', '--kind=ship']), { kind: 'ship' });
  });
});

describe('ALLOWED_KINDS', () => {
  it('covers exactly takumi/ship/plan', () => {
    assert.deepStrictEqual([...ALLOWED_KINDS].sort(), ['plan', 'ship', 'takumi']);
  });
});

describe('markMilestone', () => {
  it('writes kind + timestamp to session state', () => {
    const ok = markMilestone({ kind: 'takumi', sessionId, now: new Date('2026-01-01T00:00:00Z') });
    assert.strictEqual(ok, true);
    const state = readSessionState(sessionId);
    assert.strictEqual(state.milestone_completed, 'takumi');
    assert.strictEqual(state.milestone_at, '2026-01-01T00:00:00.000Z');
  });

  it('preserves other session state keys', () => {
    // Seed pre-existing state
    const tmp = getSessionTempPath(sessionId);
    fs.writeFileSync(tmp, JSON.stringify({ activePlan: '/plans/x', other: 'keep' }));
    markMilestone({ kind: 'ship', sessionId });
    const state = readSessionState(sessionId);
    assert.strictEqual(state.activePlan, '/plans/x');
    assert.strictEqual(state.other, 'keep');
    assert.strictEqual(state.milestone_completed, 'ship');
  });

  it('overwrites milestone on subsequent calls (last-writer-wins)', () => {
    markMilestone({ kind: 'takumi', sessionId });
    markMilestone({ kind: 'ship', sessionId });
    const state = readSessionState(sessionId);
    assert.strictEqual(state.milestone_completed, 'ship');
  });

  it('rejects unknown kinds', () => {
    assert.strictEqual(markMilestone({ kind: 'release', sessionId }), false);
    assert.strictEqual(readSessionState(sessionId), null);
  });

  it('rejects empty sessionId', () => {
    assert.strictEqual(markMilestone({ kind: 'takumi', sessionId: '' }), false);
  });
});
