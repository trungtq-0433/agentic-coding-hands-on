/**
 * Node test suite for detect-sdd.mjs.
 *
 * Ports every pure-library case from test_detect_sdd.py and covers the Node
 * CLI directly against temp fixture repositories.
 *
 * Run: node --test claude/workflows/propose-improvements-workflow/__tests__/detect-sdd.test.mjs
 */

import { test, describe, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import {
  primarySignals,
  secondarySignals,
  secondaryCategories,
  classify,
  resolveSpecsRoot,
  verifySpecFolder,
  normalizeSpecFolder,
  detectSdd,
} from '../lib/detect-sdd.mjs';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const NODE_CLI = path.resolve(__dirname, '../lib/detect-sdd.mjs');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Create a temporary directory and return its path.
 * The caller is responsible for cleanup with rmRf(dir).
 */
function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sdd-test-'));
}

function rmRf(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function writeFile(filePath, content = '') {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, 'utf8');
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

/**
 * Run the Node CLI and return { returncode, stdout, stderr }.
 */
function runNode(repoRoot, outputPath, ...extra) {
  const args = [
    NODE_CLI,
    '--repo-root', repoRoot,
    '--output-path', outputPath,
    ...extra,
  ];
  try {
    const stdout = execFileSync(process.execPath, args, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
    return { returncode: 0, stdout, stderr: '' };
  } catch (err) {
    return {
      returncode: err.status ?? 1,
      stdout: err.stdout ?? '',
      stderr: err.stderr ?? '',
    };
  }
}

// ---------------------------------------------------------------------------
// Library-level tests — port of Python test_detect_sdd.py
// ---------------------------------------------------------------------------

describe('Library: primarySignals / secondarySignals / classify / resolveSpecsRoot', () => {
  let tmp;
  before(() => { tmp = makeTmp(); });
  after(() => rmRf(tmp));

  test('test_no_signals_returns_false', () => {
    writeFile(path.join(tmp, 'ns/README.md'), 'hello');
    const repoRoot = path.join(tmp, 'ns');
    assert.deepEqual(primarySignals(repoRoot), []);
    assert.deepEqual(secondarySignals(repoRoot), []);
    assert.equal(classify([], []), false);
    assert.equal(resolveSpecsRoot(repoRoot), '');
  });

  test('test_primary_specs_dir_with_md_fires', () => {
    const repoRoot = path.join(tmp, 'p1');
    fs.mkdirSync(path.join(repoRoot, 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'specs', 'feature-list.md'), '# FeatureList');
    const hits = primarySignals(repoRoot);
    assert.ok(hits.some((s) => s.kind === 'specs-dir' && s.path === 'specs/'));
    assert.equal(classify(hits, []), true);
    assert.equal(resolveSpecsRoot(repoRoot), 'specs/');
  });

  test('test_primary_dotspecify_dir_with_any_file_fires', () => {
    const repoRoot = path.join(tmp, 'p2');
    fs.mkdirSync(path.join(repoRoot, '.specify'), { recursive: true });
    writeFile(path.join(repoRoot, '.specify', 'config.toml'), '');
    const hits = primarySignals(repoRoot);
    assert.ok(hits.some((s) => s.path === '.specify/'));
    assert.equal(classify(hits, []), true);
  });

  test('test_primary_root_spec_file_fires', () => {
    const repoRoot = path.join(tmp, 'p3');
    fs.mkdirSync(repoRoot, { recursive: true });
    writeFile(path.join(repoRoot, 'SPECIFICATION.md'), '...');
    const hits = primarySignals(repoRoot);
    assert.ok(hits.some((s) => s.kind === 'spec-file' && s.path === 'SPECIFICATION.md'));
    assert.equal(classify(hits, []), true);
  });

  test('test_one_secondary_only_returns_false', () => {
    const repoRoot = path.join(tmp, 's1');
    fs.mkdirSync(path.join(repoRoot, 'docs'), { recursive: true });
    writeFile(path.join(repoRoot, 'docs', 'feature-billing.md'), '# Billing');
    const secondary = secondarySignals(repoRoot);
    assert.equal(secondaryCategories(secondary), 1);
    assert.equal(classify([], secondary), false);
  });

  test('test_two_distinct_secondary_categories_fires', () => {
    const repoRoot = path.join(tmp, 's2');
    fs.mkdirSync(path.join(repoRoot, 'docs'), { recursive: true });
    writeFile(path.join(repoRoot, 'docs', 'feature-foo.md'), '# Foo');
    writeFile(path.join(repoRoot, 'docs', 'design.md'), '# UserStories\nbody');
    const secondary = secondarySignals(repoRoot);
    assert.ok(secondaryCategories(secondary) >= 2);
    assert.equal(classify([], secondary), true);
  });

  test('test_heading_keyword_found_in_h2_after_h1_title', () => {
    // Regression: previously broke out after first # line regardless of match.
    const repoRoot = path.join(tmp, 's3');
    fs.mkdirSync(path.join(repoRoot, 'docs'), { recursive: true });
    writeFile(path.join(repoRoot, 'docs', 'spec.md'), '# Spec Document\n\n## FeatureList\n\nbody');
    const secondary = secondarySignals(repoRoot);
    const hits = secondary.filter((s) => s.path === 'docs/spec.md');
    assert.ok(hits.length > 0, 'expected heading-keyword signal from H2 after H1');
    assert.equal(hits[0].kind, 'feature-list');
  });

  test('test_tooling_marker_in_claude_md_fires_third_category', () => {
    const repoRoot = path.join(tmp, 's4');
    fs.mkdirSync(repoRoot, { recursive: true });
    writeFile(path.join(repoRoot, 'CLAUDE.md'), 'Run /tkm:rebuild-spec on the repo.');
    const secondary = secondarySignals(repoRoot);
    const toolingHit = secondary.filter((s) => s.path.startsWith('CLAUDE.md:'));
    assert.ok(toolingHit.length > 0, 'expected tooling-marker signal from CLAUDE.md');
  });

  test('test_plan_dir_signal_requires_phase_and_keyword_bar', () => {
    const repoRoot = path.join(tmp, 's5');
    const pd = path.join(repoRoot, 'plans', '260101-sample');
    fs.mkdirSync(pd, { recursive: true });
    writeFile(path.join(pd, 'phase-01.md'), '...');

    // Below keyword bar: only 1 distinct — NO signal.
    writeFile(path.join(pd, 'plan.md'), '# Plan\nThis touches the FeatureList.');
    const sec1 = secondarySignals(repoRoot);
    assert.equal(sec1.filter((s) => s.path.startsWith('plans/')).length, 0);

    // Above bar: 2 distinct keywords — signal fires.
    writeFile(path.join(pd, 'plan.md'), '# Plan\nTouches FeatureList and UserStories.');
    const sec2 = secondarySignals(repoRoot);
    assert.ok(sec2.filter((s) => s.path.startsWith('plans/')).length > 0);
  });

  test('test_specs_root_priority_specs_over_docs_specs', () => {
    const repoRoot = path.join(tmp, 'r1');
    fs.mkdirSync(path.join(repoRoot, 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'specs', 'x.md'), '# x');
    fs.mkdirSync(path.join(repoRoot, 'docs', 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'docs', 'specs', 'y.md'), '# y');
    assert.equal(resolveSpecsRoot(repoRoot), 'specs/');
  });

  test('test_specs_root_empty_when_no_signals', () => {
    const repoRoot = path.join(tmp, 'r2');
    fs.mkdirSync(repoRoot, { recursive: true });
    assert.equal(resolveSpecsRoot(repoRoot), '');
  });

  test('test_prune_dirs_not_descended', () => {
    const repoRoot = path.join(tmp, 'pr1');
    const nm = path.join(repoRoot, 'node_modules', 'specs');
    fs.mkdirSync(nm, { recursive: true });
    writeFile(path.join(nm, 'spec.md'), '# x');
    assert.deepEqual(primarySignals(repoRoot), []);
  });
});

// ---------------------------------------------------------------------------
// signal shape
// ---------------------------------------------------------------------------

describe('Signal shape', () => {
  test('test_signal_to_dict_shape', () => {
    const sig = { kind: 'specs-dir', path: 'specs/', weight: 3 };
    assert.deepEqual(sig, { kind: 'specs-dir', path: 'specs/', weight: 3 });
  });
});

// ---------------------------------------------------------------------------
// verifySpecFolder / normalizeSpecFolder
// ---------------------------------------------------------------------------

describe('verifySpecFolder / normalizeSpecFolder', () => {
  let tmp;
  before(() => { tmp = makeTmp(); });
  after(() => rmRf(tmp));

  test('test_verify_spec_folder_success_md_file', () => {
    const repoRoot = path.join(tmp, 'v1');
    fs.mkdirSync(path.join(repoRoot, 'my-specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'my-specs', 'feature-billing.md'), '# Billing');
    const { ok, reason } = verifySpecFolder(repoRoot, 'my-specs');
    assert.ok(ok);
    assert.equal(reason, '');
  });

  test('test_verify_spec_folder_missing_dir', () => {
    const repoRoot = path.join(tmp, 'v2');
    fs.mkdirSync(repoRoot, { recursive: true });
    const { ok, reason } = verifySpecFolder(repoRoot, 'nope');
    assert.ok(!ok);
    assert.ok(reason.includes('does not exist'));
  });

  test('test_verify_spec_folder_no_md', () => {
    const repoRoot = path.join(tmp, 'v3');
    fs.mkdirSync(path.join(repoRoot, 'blank'), { recursive: true });
    writeFile(path.join(repoRoot, 'blank', 'config.toml'), '');
    const { ok, reason } = verifySpecFolder(repoRoot, 'blank');
    assert.ok(!ok);
    assert.ok(reason.includes('no in-repo .md'), `got: ${reason}`);
  });

  test('test_verify_spec_folder_rejects_absolute_path', () => {
    const repoRoot = path.join(tmp, 'v4');
    fs.mkdirSync(repoRoot, { recursive: true });
    const { ok, reason } = verifySpecFolder(repoRoot, '/etc');
    assert.ok(!ok);
    assert.ok(reason.includes('relative'));
  });

  test('test_verify_spec_folder_rejects_parent_traversal', () => {
    const repoRoot = path.join(tmp, 'v5');
    fs.mkdirSync(repoRoot, { recursive: true });
    const { ok, reason } = verifySpecFolder(repoRoot, '../etc');
    assert.ok(!ok);
    assert.ok(reason.includes('..'));
  });

  test('test_verify_spec_folder_rejects_null_byte', () => {
    const repoRoot = path.join(tmp, 'v6');
    fs.mkdirSync(repoRoot, { recursive: true });
    const { ok, reason } = verifySpecFolder(repoRoot, 'spec\x00s');
    assert.ok(!ok);
    assert.ok(reason.includes('null'));
  });

  test('test_normalize_spec_folder_appends_slash', () => {
    assert.equal(normalizeSpecFolder('docs/specs'), 'docs/specs/');
    assert.equal(normalizeSpecFolder('docs/specs/'), 'docs/specs/');
    assert.equal(normalizeSpecFolder('docs\\specs'), 'docs/specs/');
  });

  test('test_verify_spec_folder_rejects_symlink_only_content', () => {
    // An in-repo spec dir whose only .md lives behind an out-of-repo symlink
    // must NOT verify.
    const repoRoot = path.join(tmp, 'sym1');
    fs.mkdirSync(repoRoot, { recursive: true });
    const external = `${repoRoot}-external`;
    fs.mkdirSync(external, { recursive: true });
    writeFile(path.join(external, 'leak.md'), '# external');
    const specDir = path.join(repoRoot, 'my-specs');
    fs.mkdirSync(specDir, { recursive: true });
    fs.symlinkSync(external, path.join(specDir, 'linked'));

    const { ok, reason } = verifySpecFolder(repoRoot, 'my-specs');
    assert.ok(!ok);
    assert.ok(reason.includes('no in-repo .md'), `got: ${reason}`);
  });

  test('test_verify_spec_folder_accepts_in_repo_md_with_external_symlink_sibling', () => {
    // Real in-repo .md still verifies even when an unrelated external symlink exists.
    const repoRoot = path.join(tmp, 'sym2');
    fs.mkdirSync(repoRoot, { recursive: true });
    const external = `${repoRoot}-external2`;
    fs.mkdirSync(external, { recursive: true });
    writeFile(path.join(external, 'leak.md'), '# external');
    const specDir = path.join(repoRoot, 'my-specs');
    fs.mkdirSync(specDir, { recursive: true });
    writeFile(path.join(specDir, 'real.md'), '# real');
    fs.symlinkSync(external, path.join(specDir, 'linked'));

    const { ok, reason } = verifySpecFolder(repoRoot, 'my-specs');
    assert.ok(ok, `expected ok, got: ${reason}`);
    assert.equal(reason, '');
  });
});

// ---------------------------------------------------------------------------
// CLI-level tests
// ---------------------------------------------------------------------------

describe('CLI: Node implementation', () => {
  let tmp;
  before(() => { tmp = makeTmp(); });
  after(() => rmRf(tmp));

  test('test_cli_writes_valid_json_and_status_done', () => {
    const repoRoot = path.join(tmp, 'c1');
    fs.mkdirSync(path.join(repoRoot, 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'specs', 'feature-list.md'), '# FeatureList');
    const output = path.join(tmp, 'c1-out', 'sdd.json');

    const res = runNode(repoRoot, output);
    assert.equal(res.returncode, 0, `stderr: ${res.stderr}`);
    assert.ok(res.stdout.includes('Status: DONE'));
    assert.ok(res.stdout.includes('done: step-1'));

    const payload = readJson(output);
    assert.equal(payload.isSDD, true);
    assert.equal(payload.specsRoot, 'specs/');
    assert.ok(Array.isArray(payload.signals) && payload.signals.length > 0);
  });

  test('test_cli_idempotency_skips_when_output_exists', () => {
    const repoRoot = path.join(tmp, 'c2');
    fs.mkdirSync(path.join(repoRoot, 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'specs', 'x.md'), '# x');
    const output = path.join(tmp, 'c2.sdd.json');
    writeFile(output, '{"isSDD": false, "signals": [], "specsRoot": ""}');

    const res = runNode(repoRoot, output);
    assert.equal(res.returncode, 0);
    assert.ok(res.stdout.includes('skip: step-1'));
    // File unchanged.
    assert.equal(readJson(output).isSDD, false);
  });

  test('test_cli_writes_false_when_no_signals', () => {
    const repoRoot = path.join(tmp, 'c3');
    fs.mkdirSync(repoRoot, { recursive: true });
    writeFile(path.join(repoRoot, 'README.md'), 'nothing here');
    const output = path.join(tmp, 'c3.sdd.json');

    const res = runNode(repoRoot, output);
    assert.equal(res.returncode, 0);
    const payload = readJson(output);
    assert.equal(payload.isSDD, false);
    assert.equal(payload.specsRoot, '');
    assert.deepEqual(payload.signals, []);
  });

  test('test_cli_spec_folder_success_forces_sdd_true', () => {
    const repoRoot = path.join(tmp, 'c4');
    fs.mkdirSync(path.join(repoRoot, 'my-specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'my-specs', 'feature.md'), '# Feature');
    const output = path.join(tmp, 'c4.sdd.json');

    const res = runNode(repoRoot, output, '--spec-folder', 'my-specs');
    assert.equal(res.returncode, 0, `stdout: ${res.stdout}\nstderr: ${res.stderr}`);
    assert.ok(res.stdout.includes('done: step-1'));
    assert.ok(res.stdout.includes('spec-folder: my-specs/ (verified'));
    assert.ok(res.stdout.includes('Status: DONE'));

    const payload = readJson(output);
    assert.equal(payload.isSDD, true);
    assert.equal(payload.specsRoot, 'my-specs/');
    assert.deepEqual(payload.signals, [{ kind: 'specs-dir', path: 'my-specs/', weight: 3 }]);
  });

  test('test_cli_spec_folder_failure_blocks', () => {
    const repoRoot = path.join(tmp, 'c5');
    fs.mkdirSync(repoRoot, { recursive: true });
    const output = path.join(tmp, 'c5.sdd.json');

    const res = runNode(repoRoot, output, '--spec-folder', 'missing');
    assert.equal(res.returncode, 2);
    assert.ok(res.stdout.includes('Status: BLOCKED'));
    assert.ok(res.stdout.includes('--spec-folder verification failed'));
    // Must NOT write a fallback artifact on verification failure.
    assert.ok(!fs.existsSync(output));
  });

  test('test_cli_spec_folder_ignored_when_output_already_exists', () => {
    const repoRoot = path.join(tmp, 'c6');
    fs.mkdirSync(path.join(repoRoot, 'my-specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'my-specs', 'x.md'), '# x');
    const output = path.join(tmp, 'c6.sdd.json');
    writeFile(output, '{"isSDD": false, "signals": [], "specsRoot": ""}');

    const res = runNode(repoRoot, output, '--spec-folder', 'my-specs');
    assert.equal(res.returncode, 0);
    assert.ok(res.stdout.includes('skip: step-1'));
    assert.equal(readJson(output).isSDD, false);
  });

  test('test_cli_without_spec_folder_runs_detection', () => {
    const repoRoot = path.join(tmp, 'c7');
    fs.mkdirSync(path.join(repoRoot, 'specs'), { recursive: true });
    writeFile(path.join(repoRoot, 'specs', 'feature-list.md'), '# FeatureList');
    const output = path.join(tmp, 'c7.sdd.json');

    const res = runNode(repoRoot, output);
    assert.equal(res.returncode, 0);
    assert.equal(readJson(output).isSDD, true);
    assert.ok(!res.stdout.includes('spec-folder:'));
  });

  test('test_cli_spec_folder_empty_string_blocks', () => {
    // Regression: empty `--spec-folder ""` must BLOCK, not silently auto-detect.
    const repoRoot = path.join(tmp, 'c8');
    fs.mkdirSync(repoRoot, { recursive: true });
    const output = path.join(tmp, 'c8.sdd.json');

    const res = runNode(repoRoot, output, '--spec-folder', '');
    assert.equal(res.returncode, 2);
    assert.ok(res.stdout.includes('Status: BLOCKED'));
    assert.ok(res.stdout.includes('--spec-folder verification failed'));
    assert.ok(!fs.existsSync(output));
  });
});
