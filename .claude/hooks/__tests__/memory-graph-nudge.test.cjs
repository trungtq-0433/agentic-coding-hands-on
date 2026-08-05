#!/usr/bin/env node
/**
 * Tests for memory-graph-nudge.cjs — SessionStart nudge hook (default-OFF).
 * Run: bun test claude/hooks/__tests__/memory-graph-nudge.test.cjs
 *
 * The real `graphify` CLI is stubbed via GRAPHIFY_BIN so the "installed vs not"
 * nudge-text branch is asserted without pip/network/LLM.
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const HOOK_PATH = path.join(__dirname, '..', 'memory-graph-nudge.cjs');

function makeTmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-nudge-'));
}

function writeCfg(dir, enabled) {
  const d = path.join(dir, '.claude');
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, '.tkm.json'), JSON.stringify({ memoryGraph: { enabled } }));
}

function queueDirFor(dir) {
  return path.join(dir, 'memory-graph-out', 'raw');
}

function writePendingFile(dir, name = 'session-a.md') {
  const q = queueDirFor(dir);
  fs.mkdirSync(q, { recursive: true });
  fs.writeFileSync(path.join(q, name), '---\nsession_id: x\n---\n\n**User:** hi\n');
}

function writeGraph(dir, atMs) {
  const gdir = path.join(queueDirFor(dir), 'graphify-out');
  fs.mkdirSync(gdir, { recursive: true });
  const gpath = path.join(gdir, 'graph.json');
  fs.writeFileSync(gpath, '{"nodes":[],"links":[]}');
  if (atMs) fs.utimesSync(gpath, new Date(atMs), new Date(atMs));
}

function writeGraphifyStub(dir) {
  const stub = path.join(dir, 'graphify-stub.sh');
  fs.writeFileSync(stub, '#!/bin/sh\nexit 0\n');
  fs.chmodSync(stub, 0o755);
  return stub;
}

function runHook(dir, env = {}) {
  return new Promise((resolve, reject) => {
    const home = path.join(dir, '_home');
    fs.mkdirSync(home, { recursive: true });
    const proc = spawn(process.execPath, [HOOK_PATH], {
      cwd: dir,
      env: { ...process.env, HOME: home, USERPROFILE: home, PATH: '', ...env },
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
    }, 5000);
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

describe('memory-graph-nudge.cjs', () => {
  let dir;

  beforeEach(() => { dir = makeTmp(); });
  afterEach(() => {
    try { fs.rmSync(dir, { recursive: true, force: true }); } catch (_) {}
  });

  it('default config (disabled) → no-op, empty stdout', async () => {
    writePendingFile(dir);
    const { stdout, exitCode } = await runHook(dir);
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
  });

  it('MEMORY_GRAPH_DISABLE=1 → no-op even with config enabled', async () => {
    writeCfg(dir, true);
    writePendingFile(dir);
    const { stdout, exitCode } = await runHook(dir, { MEMORY_GRAPH_DISABLE: '1' });
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
  });

  it('enabled, no pending files → no-op', async () => {
    writeCfg(dir, true);
    const { stdout, exitCode } = await runHook(dir);
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
  });

  it('enabled, pending files, graphify on PATH → routes through /graphify --update skill (not a bare CLI call), no install text', async () => {
    writeCfg(dir, true);
    writePendingFile(dir);
    const stub = writeGraphifyStub(dir);
    const { parsed, exitCode } = await runHook(dir, { GRAPHIFY_BIN: stub });
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'should emit a nudge');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'SessionStart');
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('1 conversation delta'), 'names the pending count');
    // Only the /graphify skill dispatches the in-session subagents (host = LLM); a bare
    // `graphify <dir> --update` CLI call errors with "no LLM API key found" on prose deltas.
    // So the installed path routes through the skill too — it just drops the install explainer.
    assert.ok(ctx.includes('/graphify` skill'), 'installed path routes through the skill, not a bare CLI');
    assert.ok(ctx.includes('--update'), 'names update mode');
    assert.ok(ctx.includes('memory-graph-out/raw'), 'names the queue path');
    assert.ok(!ctx.includes('self-installs'), 'installed path omits the one-time install explainer');
  });

  it('enabled, pending files, graphify NOT on PATH → routes through /graphify skill install', async () => {
    writeCfg(dir, true);
    writePendingFile(dir);
    const { parsed, exitCode } = await runHook(dir); // no GRAPHIFY_BIN, empty PATH
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'should emit a nudge');
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('/graphify` skill'), 'routes through the skill, not a bare CLI call');
    assert.ok(ctx.includes('self-installs'), 'explains the one-time install cost');
  });

  it('graph newer than pending files → no-op (nothing new to fold in)', async () => {
    writeCfg(dir, true);
    writePendingFile(dir);
    writeGraph(dir, Date.now() + 60_000); // graph built "in the future" relative to the queued file
    const { stdout, exitCode } = await runHook(dir);
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '');
  });

  it('throttle: second run within the window stays silent', async () => {
    writeCfg(dir, true);
    writePendingFile(dir);
    const stub = writeGraphifyStub(dir);
    const first = await runHook(dir, { GRAPHIFY_BIN: stub });
    assert.ok(first.parsed, 'first run nudges');
    const second = await runHook(dir, { GRAPHIFY_BIN: stub });
    assert.strictEqual(second.stdout.trim(), '', 'second run within throttle window must stay silent');
  });
});
