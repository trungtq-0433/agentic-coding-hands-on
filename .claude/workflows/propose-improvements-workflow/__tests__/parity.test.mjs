/**
 * parity.test.mjs — cross-language parity guard for the 3 byte-stable deterministic steps.
 *
 * Three of the lib/*.mjs CLIs (detect-sdd / combine / apply-verdicts) are 1:1 behavioural
 * ports of the propose-improvements skill's Python step scripts
 * (claude/skills/propose-improvements/scripts/*.py). The other __tests__ exercise the JS
 * cores in isolation; THIS suite proves those three JS CLIs still reproduce their Python
 * counterparts BYTE-FOR-BYTE, so future edits to either side can't silently drift apart.
 * (phase-d-prep is deliberately NOT in this suite — its JS port has diverged from the Python
 * on purpose; see the comment above the phase-d note below and phase-d-prep.test.mjs.)
 *
 * For each step it: builds an identical fixture tree under two temp dirs, runs the
 * Python CLI in one and the JS CLI in the other, then asserts the produced artifact
 * bytes + normalised stdout match exactly.
 *
 * The Python CLIs (detect_sdd.py / combine_proposals.py / apply_verdicts.py) and their
 * *_lib.py modules import stdlib only, so any `python3` on PATH works — no venv required.
 * If no python3 (or the propose-improvements scripts) are present the whole suite SKIPS
 * rather than fails, keeping CI green on minimal images.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// __tests__ → propose-improvements-workflow → workflows → claude → repo root
const REPO_ROOT = path.resolve(__dirname, '../../../../');
const JS_LIB = path.resolve(__dirname, '../lib');
const PY_SCRIPTS = path.join(REPO_ROOT, 'claude/skills/propose-improvements/scripts');

/** Resolve a python3 interpreter: prefer the kit venv, else PATH. */
function resolvePython() {
  const venv = path.join(REPO_ROOT, '.claude/skills/.venv/bin/python3');
  if (fs.existsSync(venv)) return venv;
  // Probe PATH (stdlib-only scripts → any python3 is fine).
  for (const cand of ['python3', 'python']) {
    const r = spawnSync(cand, ['--version'], { encoding: 'utf8' });
    if (r.status === 0) return cand;
  }
  return null;
}

const PYTHON = resolvePython();
const TOOLCHAIN_OK = !!PYTHON && fs.existsSync(PY_SCRIPTS);
const SKIP = TOOLCHAIN_OK ? false : 'python3 or propose-improvements scripts unavailable — parity check skipped';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Write a { relpath: content } map under base, creating parent dirs. */
function writeTree(base, files) {
  for (const [rel, content] of Object.entries(files)) {
    const full = path.join(base, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, content, 'utf8');
  }
}

/** Run a CLI in cwd, capturing stdout regardless of exit code. */
function runCli(bin, args, cwd) {
  const r = spawnSync(bin, args, { cwd, encoding: 'utf8' });
  return { stdout: r.stdout ?? '', stderr: r.stderr ?? '', status: r.status };
}

/**
 * Normalise text for cross-run comparison:
 *  - strip the run's own cwd prefix (absolute paths in stdout/manifests differ only
 *    by the temp dir),
 *  - collapse the `_Generated YYYY-MM-DD.` date stamp (combine uses today's date),
 *  - mask the proposal H1 title defensively. Both the Python skill and the JS port now
 *    emit "Improvement Proposal" (the skill was renamed from "Upsale Proposal"), so the
 *    H1 matches byte-for-byte; the mask stays only to absorb any future title drift.
 *    Everything else (structure, transforms, sort, dedup, evidence, path handling) must
 *    still match the Python source byte-for-byte.
 */
function normalise(text, cwd) {
  let out = text.split(cwd).join('<CWD>');
  out = out.replace(/_Generated \d{4}-\d{2}-\d{2}\./g, '_Generated <DATE>.');
  out = out.replace(/(Upsale|Improvement) Proposal/g, '<PROPOSAL>');
  return out;
}

function read(base, rel) {
  return fs.readFileSync(path.join(base, rel), 'utf8');
}

/** Run the same scenario under Python + JS and assert parity. */
function assertParity({ pyArgs, jsArgs, fixtures, artifacts }) {
  const pyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'parity-py-'));
  const jsDir = fs.mkdtempSync(path.join(os.tmpdir(), 'parity-js-'));
  try {
    writeTree(pyDir, fixtures(pyDir));
    writeTree(jsDir, fixtures(jsDir));

    const py = runCli(PYTHON, pyArgs(pyDir), pyDir);
    const js = runCli(process.execPath, jsArgs(jsDir), jsDir);

    assert.equal(js.status, py.status, `exit codes differ (py=${py.status} js=${js.status})\npy stderr: ${py.stderr}\njs stderr: ${js.stderr}`);
    assert.equal(
      normalise(js.stdout, jsDir),
      normalise(py.stdout, pyDir),
      'stdout differs between Python and JS'
    );

    for (const rel of artifacts) {
      const pyArt = fs.existsSync(path.join(pyDir, rel));
      const jsArt = fs.existsSync(path.join(jsDir, rel));
      assert.equal(jsArt, pyArt, `artifact presence differs for ${rel} (py=${pyArt} js=${jsArt})`);
      if (pyArt) {
        assert.equal(
          normalise(read(jsDir, rel), jsDir),
          normalise(read(pyDir, rel), pyDir),
          `artifact bytes differ for ${rel}`
        );
      }
    }
  } finally {
    fs.rmSync(pyDir, { recursive: true, force: true });
    fs.rmSync(jsDir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// Shared fixture content (fixed date → deterministic; identical bytes both sides)
// ---------------------------------------------------------------------------

const USE_CONTEXT_JSON = JSON.stringify({ useContext: 'hybrid', confidence: 'high' }, null, 2) + '\n';

const FINALISED_COMBINED = `# Improvement Proposal — parityfix

_Generated 2026-01-01. Use context: **hybrid**. Based on repository analysis._

## Technical

### Architecture · 1 item · max=high · effort=low
<!-- aspect-id: architecture -->

#### Adopt CI caching
- **Value:** high
- **Need:** Builds re-download dependencies every run.
- **Benefits:** Faster pipelines, lower cost.
- **Proposed solution:** Cache the dependency store between runs.
- **Engineering effort hint:** low

<!-- dedup: applied (n=0) -->
`;

const TECH_TRACK_PROPOSAL = `# Technical Improvement Proposal — parityfix
**Use context:** hybrid

## Architecture
<!-- aspect-id: architecture -->

### Adopt CI caching
- **Value:** high
- **Need:** Builds re-download dependencies every run.
- **Benefits:** Faster pipelines, lower cost.
- **Proposed solution:** Cache the dependency store between runs.
- **Engineering effort hint:** low
`;

const KEEP_VERDICT = `---
item_index: 1
item_slug: adopt-ci-caching
decision: KEEP
---
`;

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test('parity: detect-sdd matches detect_sdd.py', { skip: SKIP }, () => {
  assertParity({
    fixtures: () => ({
      'specs/feature-login.md': '# FeatureList\n\n- login\n',
      'specs/user-story-1.md': '# UserStories\n\n- as a user...\n',
    }),
    pyArgs: (d) => [path.join(PY_SCRIPTS, 'detect_sdd.py'), '--repo-root', d, '--output-path', 'plans/improvement-proposal/sdd-detection.json'],
    jsArgs: (d) => [path.join(JS_LIB, 'detect-sdd.mjs'), '--repo-root', d, '--output-path', 'plans/improvement-proposal/sdd-detection.json'],
    artifacts: ['plans/improvement-proposal/sdd-detection.json'],
  });
});

test('parity: combine matches combine_proposals.py', { skip: SKIP }, () => {
  assertParity({
    fixtures: () => ({
      'plans/improvement-proposal/technical/03-technical-proposal.md': TECH_TRACK_PROPOSAL,
      'plans/improvement-proposal/use-context.json': USE_CONTEXT_JSON,
    }),
    // NOTE: no --date-str → both sides use today's date; normalise() collapses it.
    pyArgs: () => [
      path.join(PY_SCRIPTS, 'combine_proposals.py'),
      '--technical-path', 'plans/improvement-proposal/technical/03-technical-proposal.md',
      '--use-context-json', 'plans/improvement-proposal/use-context.json',
      '--output', 'plans/improvement-proposal/combined-initial.md',
      '--project-name', 'parityfix',
    ],
    jsArgs: () => [
      path.join(JS_LIB, 'combine.mjs'),
      '--technical-path', 'plans/improvement-proposal/technical/03-technical-proposal.md',
      '--use-context-json', 'plans/improvement-proposal/use-context.json',
      '--output', 'plans/improvement-proposal/combined-initial.md',
      '--project-name', 'parityfix',
    ],
    artifacts: ['plans/improvement-proposal/combined-initial.md'],
  });
});

// NOTE: phase-d-prep is intentionally NOT parity-checked. Unlike the other three
// steps, propose-improvements' phase-d-prep.mjs has diverged from the skill's Python
// phase_d_prep.py on purpose: the JS now emits a slim payload carrying only the
// proposal item (no evidence / stack-context / use-context), because the validator
// self-verifies against the repo. The Python engine stays fat for the Python skill.
// See propose-improvements/__tests__/phase-d-prep.test.mjs for the JS-side coverage.

test('parity: apply-verdicts matches apply_verdicts.py', { skip: SKIP }, () => {
  assertParity({
    fixtures: () => ({
      'plans/improvement-proposal/combined-initial.md': FINALISED_COMBINED,
      'plans/improvement-proposal/validation/item-01-adopt-ci-caching.md': KEEP_VERDICT,
    }),
    pyArgs: () => [
      path.join(PY_SCRIPTS, 'apply_verdicts.py'),
      '--combined-path', 'plans/improvement-proposal/combined-initial.md',
      '--validation-dir', 'plans/improvement-proposal/validation/',
      '--output-path', 'plans/improvement-proposal/improvement-proposal.md',
    ],
    jsArgs: () => [
      path.join(JS_LIB, 'apply-verdicts.mjs'),
      '--combined-path', 'plans/improvement-proposal/combined-initial.md',
      '--validation-dir', 'plans/improvement-proposal/validation/',
      '--output-path', 'plans/improvement-proposal/improvement-proposal.md',
    ],
    artifacts: ['plans/improvement-proposal/improvement-proposal.md'],
  });
});
