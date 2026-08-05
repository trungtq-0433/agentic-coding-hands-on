#!/usr/bin/env node
/**
 * Contract test — descriptive-name.cjs must emit the modern Claude
 * context-only shape on PreToolUse / Write: hookSpecificOutput with
 * `additionalContext` present and NO `permissionDecision` key.
 *
 * Documented Claude contract: omit `permissionDecision` when the hook
 * only injects context. Pairs with the Codex wrapper across both
 * capability tables (v0.130.0 and v0.124.0-alpha.3).
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');

const HOOK_PATH = path.join(__dirname, '..', 'descriptive-name.cjs');

function runHook(payload) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [HOOK_PATH], {
      cwd: process.cwd(),
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

describe('descriptive-name.cjs — modern Claude context-only shape', () => {
  const payload = {
    hook_event_name: 'PreToolUse',
    tool_name: 'Write',
    tool_input: { file_path: '/tmp/test-fixtures/foo.ts', content: 'x' },
  };

  it('emits hookSpecificOutput with hookEventName=PreToolUse', async () => {
    const { parsed, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed, 'must emit JSON on stdout');
    assert.ok(parsed.hookSpecificOutput, 'must have hookSpecificOutput');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'PreToolUse');
  });

  it('omits permissionDecision (modern context-only contract)', async () => {
    const { parsed } = await runHook(payload);
    assert.strictEqual(
      parsed.hookSpecificOutput.permissionDecision,
      undefined,
      'context-only hook must NOT set permissionDecision'
    );
  });

  it('includes non-empty additionalContext', async () => {
    const { parsed } = await runHook(payload);
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx && ctx.length > 0, 'additionalContext required');
  });
});
