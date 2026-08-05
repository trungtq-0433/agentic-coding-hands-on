#!/usr/bin/env node
'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { locateEvidenceDir } = require('../evidence-dir-locator.cjs');
const { writeSessionState, getSessionTempPath } = require('../tkm-config-utils.cjs');

let counter = 0;
/** Fresh scratch cwd with no plans/ or .claude/ dirs of its own. */
function makeCwd() {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), `evd-locator-${process.pid}-${counter++}-`));
  return dir;
}

/** Unique per-test session id — isolates each test's session-state temp file. */
function makeSessionId() {
  return `evd-locator-test-${process.pid}-${counter++}-${Math.random().toString(36).slice(2)}`;
}

/** Best-effort cleanup of a test session's temp state file. */
function cleanupSession(sessionId) {
  try { fs.unlinkSync(getSessionTempPath(sessionId)); } catch (_) { /* ignore */ }
}

test('rung 1: explicitDir wins over everything else', () => {
  const cwd = makeCwd();
  const explicit = path.join(cwd, 'explicit-dir');
  fs.mkdirSync(explicit, { recursive: true });
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  process.env.TKM_EVIDENCE_DIR = path.join(cwd, 'env-dir');
  try {
    const found = locateEvidenceDir({ cwd, explicitDir: explicit });
    assert.strictEqual(found, explicit);
  } finally {
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('rung 2: TKM_EVIDENCE_DIR env wins when no explicitDir given', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  process.env.TKM_EVIDENCE_DIR = path.join(cwd, 'from-env');
  try {
    const found = locateEvidenceDir({ cwd });
    assert.strictEqual(found, path.resolve(cwd, path.join(cwd, 'from-env')));
  } finally {
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('rung 3: .claude/workflow-artifacts.json pointer wins when no flag/env set', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  delete process.env.TKM_EVIDENCE_DIR;
  try {
    fs.mkdirSync(path.join(cwd, '.claude'), { recursive: true });
    const pointedDir = path.join(cwd, 'plans', 'some-plan', 'evidence');
    fs.mkdirSync(pointedDir, { recursive: true });
    fs.writeFileSync(
      path.join(cwd, '.claude', 'workflow-artifacts.json'),
      JSON.stringify({ evidenceDir: pointedDir })
    );
    const found = locateEvidenceDir({ cwd });
    assert.strictEqual(found, pointedDir);
  } finally {
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('rung 3: malformed pointer file is skipped, falls through to rung 4 (active-plan session state)', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  delete process.env.TKM_EVIDENCE_DIR;
  const sessionId = makeSessionId();
  try {
    fs.mkdirSync(path.join(cwd, '.claude'), { recursive: true });
    fs.writeFileSync(path.join(cwd, '.claude', 'workflow-artifacts.json'), 'not valid json{{{');

    const planDir = path.join(cwd, 'plans', '260101-0000-demo');
    const planEvidence = path.join(planDir, 'evidence');
    fs.mkdirSync(planEvidence, { recursive: true });
    writeSessionState(sessionId, { activePlan: planDir });

    const found = locateEvidenceDir({ cwd, sessionId });
    assert.strictEqual(found, planEvidence);
  } finally {
    cleanupSession(sessionId);
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('rung 4: the ACTIVE (session-resolved) plan\'s evidence/ dir wins, never an older plan by recency', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  delete process.env.TKM_EVIDENCE_DIR;
  const sessionId = makeSessionId();
  try {
    // An older, abandoned plan still carries an evidence/ dir on disk — it must
    // NEVER be picked just because it's the only (or "newest") one present.
    const abandoned = path.join(cwd, 'plans', '260101-0900-abandoned-plan', 'evidence');
    fs.mkdirSync(abandoned, { recursive: true });

    // The actually-active plan (older date, but it's the one session-state points
    // at) also has evidence/ — this is the one that must be returned.
    const activePlanDir = path.join(cwd, 'plans', '260050-0000-active-plan');
    const activeEvidence = path.join(activePlanDir, 'evidence');
    fs.mkdirSync(activeEvidence, { recursive: true });
    writeSessionState(sessionId, { activePlan: activePlanDir });

    const found = locateEvidenceDir({ cwd, sessionId });
    assert.strictEqual(found, activeEvidence);
  } finally {
    cleanupSession(sessionId);
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('rung 4: an active plan lacking evidence/ resolves to null even when an older plan dir has one', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  delete process.env.TKM_EVIDENCE_DIR;
  const sessionId = makeSessionId();
  try {
    const olderWithEvidence = path.join(cwd, 'plans', '260101-0900-older-plan', 'evidence');
    fs.mkdirSync(olderWithEvidence, { recursive: true });

    // Active plan exists on disk but has no evidence/ subdir yet.
    const activePlanDir = path.join(cwd, 'plans', '260113-0100-active-plan-no-evidence');
    fs.mkdirSync(activePlanDir, { recursive: true });
    writeSessionState(sessionId, { activePlan: activePlanDir });

    const found = locateEvidenceDir({ cwd, sessionId });
    assert.strictEqual(found, null);
  } finally {
    cleanupSession(sessionId);
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});

test('returns null when nothing resolves at all', () => {
  const cwd = makeCwd();
  const prevEnv = process.env.TKM_EVIDENCE_DIR;
  delete process.env.TKM_EVIDENCE_DIR;
  try {
    assert.strictEqual(locateEvidenceDir({ cwd }), null);
  } finally {
    if (prevEnv === undefined) delete process.env.TKM_EVIDENCE_DIR; else process.env.TKM_EVIDENCE_DIR = prevEnv;
  }
});
