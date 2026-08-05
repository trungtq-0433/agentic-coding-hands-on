#!/usr/bin/env node
/**
 * Contract test — skill-extension-loader.cjs must emit the modern Claude
 * context-only shape (or empty `{}` when no extensions exist) on
 * PreToolUse / Skill: NO `permissionDecision` key.
 */

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const HOOK_PATH = path.join(__dirname, '..', 'skill-extension-loader.cjs');

function runHook(payload, cwd) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [HOOK_PATH], {
      cwd: cwd || process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env,
    });

    let stdout = '';
    let stderr = '';
    let settled = false;

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    proc.stdin.write(JSON.stringify(payload));
    proc.stdin.end();

    const t = setTimeout(() => {
      if (!settled) {
        settled = true;
        proc.kill('SIGTERM');
        reject(new Error('Hook timed out'));
      }
    }, 1000);

    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(t);
      let parsed = null;
      try { parsed = stdout.trim() ? JSON.parse(stdout.trim()) : null; } catch (_) {}
      resolve({ stdout, stderr, exitCode: code, parsed });
    });
  });
}

describe('skill-extension-loader.cjs — modern Claude context-only shape', () => {
  let tmpDir;
  const skillName = 'review-code';

  before(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-ext-shape-'));
    const extDir = path.join(tmpDir, '.claude', 'skills', skillName, 'extensions');
    fs.mkdirSync(extDir, { recursive: true });
    fs.writeFileSync(
      path.join(extDir, 'sample.md'),
      `---\nextends: tkm:${skillName}\ntype: post\n---\nEXT BODY\n`
    );
  });

  after(() => {
    try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) {}
  });

  it('with extensions: emits hookSpecificOutput with no permissionDecision', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Skill',
      tool_input: { skill: `tkm:${skillName}` },
      cwd: tmpDir,
    };
    const { parsed, exitCode } = await runHook(payload, tmpDir);
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'must emit JSON on stdout');
    assert.ok(parsed.hookSpecificOutput, 'must have hookSpecificOutput');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'PreToolUse');
    assert.strictEqual(
      parsed.hookSpecificOutput.permissionDecision,
      undefined,
      'context-only hook must NOT set permissionDecision'
    );
    assert.ok(
      parsed.hookSpecificOutput.additionalContext.includes('EXT BODY'),
      'additionalContext should include extension body'
    );
  });

  it('no extensions: emits empty object (no permissionDecision leakage)', async () => {
    const noExtCwd = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-ext-none-'));
    try {
      const payload = {
        hook_event_name: 'PreToolUse',
        tool_name: 'Skill',
        tool_input: { skill: `tkm:other-skill` },
        cwd: noExtCwd,
      };
      const { parsed, exitCode } = await runHook(payload, noExtCwd);
      assert.strictEqual(exitCode, 0);
      // Either parsed=={} or parsed.hookSpecificOutput.permissionDecision===undefined
      if (parsed && parsed.hookSpecificOutput) {
        assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, undefined);
      }
    } finally {
      try { fs.rmSync(noExtCwd, { recursive: true, force: true }); } catch (_) {}
    }
  });
});
