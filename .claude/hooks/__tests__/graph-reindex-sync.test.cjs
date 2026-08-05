#!/usr/bin/env node
/**
 * Tests for graph-reindex-sync.cjs — SessionStart graph-freshness hook (default-ON).
 * Run: bun test claude/hooks/__tests__/graph-reindex-sync.test.cjs
 *
 * The real `graphify` CLI is stubbed via GRAPHIFY_BIN (a shell script) so the
 * code-only `graphify update .` re-index is asserted without pip/network/LLM. The
 * hook spawns that update DETACHED, so tests poll for the stub's side-effect file.
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const HOOK_PATH = path.join(__dirname, '..', 'graph-reindex-sync.cjs');

// --- fixture helpers --------------------------------------------------------

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'graph-reindex-sync-'));
}

function git(cwd, args) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

/** git-init a repo with one commit; return the initial commit sha. */
function initRepo(dir) {
  git(dir, ['init', '-q']);
  git(dir, ['config', 'user.email', 'test@example.com']);
  git(dir, ['config', 'user.name', 'Test']);
  git(dir, ['config', 'commit.gpgsign', 'false']);
  fs.writeFileSync(path.join(dir, 'README.txt-seed'), 'seed'); // non-doc seed
  git(dir, ['add', '-A']);
  git(dir, ['commit', '-q', '-m', 'init']);
  return git(dir, ['rev-parse', 'HEAD']);
}

function writeGraph(dir, builtAtCommit) {
  const gdir = path.join(dir, 'graphify-out');
  fs.mkdirSync(gdir, { recursive: true });
  const graph = { directed: false, multigraph: false, nodes: [], links: [] };
  if (builtAtCommit) graph.built_at_commit = builtAtCommit;
  fs.writeFileSync(path.join(gdir, 'graph.json'), JSON.stringify(graph));
}

function writeCfg(dir, enabled) {
  const d = path.join(dir, '.claude');
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, '.tkm.json'), JSON.stringify({ graphify: { enabled } }));
}

/**
 * Executable stub `graphify`. On `update`, appends a line to $GRAPHIFY_STUB_UPDATES
 * (proves the code re-index ran + counts invocations) and writes a graph.json.
 */
function writeStub(dir) {
  const stub = path.join(dir, 'graphify-stub.sh');
  const updates = path.join(dir, 'stub-updates.log');
  fs.writeFileSync(stub, [
    '#!/bin/sh',
    'if [ "$1" = "update" ]; then',
    '  echo "update" >> "$GRAPHIFY_STUB_UPDATES"',
    '  mkdir -p graphify-out',
    '  printf \'{"nodes":[],"links":[]}\' > graphify-out/graph.json',
    '  exit 0',
    'fi',
    'exit 0',
    '',
  ].join('\n'));
  fs.chmodSync(stub, 0o755);
  return { stub, updates };
}

async function pollFor(file, ms = 4000) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    if (fs.existsSync(file)) return true;
    await new Promise((r) => setTimeout(r, 50));
  }
  return false;
}

function countLines(file) {
  try { return fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).length; }
  catch { return 0; }
}

function runHook(dir, env = {}) {
  return new Promise((resolve, reject) => {
    const home = path.join(dir, '_home');
    fs.mkdirSync(home, { recursive: true });
    const proc = spawn(process.execPath, [HOOK_PATH], {
      cwd: dir,
      env: { ...process.env, HOME: home, USERPROFILE: home, ...env },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    let settled = false;
    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));
    proc.stdin.write(JSON.stringify({ hook_event_name: 'SessionStart', source: 'startup', cwd: dir }));
    proc.stdin.end();
    const t = setTimeout(() => {
      if (!settled) { settled = true; proc.kill('SIGTERM'); reject(new Error('Hook timed out')); }
    }, 8000);
    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(t);
      let parsed = null;
      try { parsed = stdout.trim() ? JSON.parse(stdout.trim()) : null; } catch (_) {}
      resolve({ stdout, stderr, exitCode: code, parsed });
    });
    proc.on('error', (err) => { if (!settled) { settled = true; clearTimeout(t); reject(err); } });
  });
}

// --- tests ------------------------------------------------------------------

describe('graph-reindex-sync.cjs', () => {
  let dir, stub, updates;

  beforeEach(() => {
    dir = makeTmp();
    ({ stub, updates } = writeStub(dir));
  });
  afterEach(() => {
    try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
  });

  it('GRAPHIFY_DISABLE=1 → no-op: no update, empty stdout', async () => {
    initRepo(dir);
    const { stdout, exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates, GRAPHIFY_DISABLE: '1' });
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
    await new Promise((r) => setTimeout(r, 300));
    assert.ok(!fs.existsSync(updates), 'disabled hook must not run graphify update');
  });

  it('config graphify.enabled=false → no-op: no update', async () => {
    initRepo(dir);
    writeCfg(dir, false);
    const { stdout, exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
    await new Promise((r) => setTimeout(r, 300));
    assert.ok(!fs.existsSync(updates), 'config-disabled hook must not run graphify update');
  });

  it('git repo, no graph, graphify available → code re-index runs + .gitignore updated', async () => {
    initRepo(dir);
    const { exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    assert.strictEqual(exitCode, 0);
    assert.ok(await pollFor(updates), 'graphify update . should have run (detached)');
    const gi = fs.readFileSync(path.join(dir, '.gitignore'), 'utf8');
    assert.ok(gi.includes('graphify-out'), '.gitignore should ignore graphify-out/');
  });

  it('graphify not available, git repo, no graph → build nudge', async () => {
    initRepo(dir);
    // No GRAPHIFY_BIN and `graphify` not on PATH (empty PATH) → locateGraphify() null.
    const { parsed, exitCode } = await runHook(dir, { GRAPHIFY_STUB_UPDATES: updates, PATH: '' });
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'should emit a nudge');
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('rebuild-spec'), 'nudge to run rebuild-spec');
  });

  it('docs changed since built_at_commit → nudge, and code re-index still runs', async () => {
    const sha = initRepo(dir);
    writeGraph(dir, sha);
    fs.mkdirSync(path.join(dir, 'docs'), { recursive: true });
    fs.writeFileSync(path.join(dir, 'docs', 'guide.md'), '# new doc');
    git(dir, ['add', '-A']);
    git(dir, ['commit', '-q', '-m', 'add doc']);
    const { parsed, exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'should emit JSON');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'SessionStart');
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('docs/guide.md'), 'nudge lists the changed doc');
    assert.ok(await pollFor(updates), 'code re-index still runs alongside the docs nudge');
  });

  it('throttle: rapid second run does not re-spawn graphify update', async () => {
    initRepo(dir);
    await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    assert.ok(await pollFor(updates), 'first run indexes');
    await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    await new Promise((r) => setTimeout(r, 400));
    assert.strictEqual(countLines(updates), 1, 'second run within throttle window must not re-index');
  });

  it('not a git repo, no graph → no-op, no crash', async () => {
    const { stdout, exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub, GRAPHIFY_STUB_UPDATES: updates });
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
    await new Promise((r) => setTimeout(r, 300));
    assert.ok(!fs.existsSync(updates), 'no git + no graph → nothing to index');
  });
});
