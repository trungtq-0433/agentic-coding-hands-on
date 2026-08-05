#!/usr/bin/env node
/**
 * Contract test — scout-block.cjs must emit modern Claude block shape
 * on blocked patterns: hookSpecificOutput.permissionDecision === "deny"
 * + permissionDecisionReason populated, exit 0. Empty input must fail
 * open (silent {} + exit 0) — consistent with the hook's other error
 * paths (parse-fail, invalid-structure).
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');

const HOOK_PATH = path.join(__dirname, '..', 'scout-block.cjs');

function runHook(payload, opts = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [HOOK_PATH], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env,
    });

    let stdout = '';
    let stderr = '';
    let settled = false;

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    if (opts.emptyInput) {
      proc.stdin.end();
    } else {
      proc.stdin.write(JSON.stringify(payload));
      proc.stdin.end();
    }

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

describe('scout-block.cjs — modern Claude block shape + fail-open', () => {
  it('broad-pattern: Glob **/* → modern deny shape, exit 0', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Glob',
      tool_input: { pattern: '**/*' },
    };
    const { parsed, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0, 'must exit 0 (decision in JSON)');
    assert.ok(parsed && parsed.hookSpecificOutput, 'must emit hookSpecificOutput');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'PreToolUse');
    assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, 'deny');
    assert.ok(
      parsed.hookSpecificOutput.permissionDecisionReason,
      'must have permissionDecisionReason'
    );
  });

  it('empty input: fail-open (silent {} + exit 0)', async () => {
    const { stdout, stderr, exitCode } = await runHook(null, { emptyInput: true });
    assert.strictEqual(exitCode, 0, 'empty input must fail open with exit 0');
    assert.strictEqual(stdout.trim(), '{}', 'empty input must emit silent {}');
    assert.strictEqual(stderr, '', 'empty input must be silent on stderr');
  });

  it('passthrough: Read on regular path → exit 0, no deny in stdout', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Read',
      tool_input: { file_path: 'src/index.ts' },
    };
    const { stdout, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0);
    if (stdout.trim()) {
      const parsed = JSON.parse(stdout.trim());
      if (parsed.hookSpecificOutput) {
        assert.notStrictEqual(parsed.hookSpecificOutput.permissionDecision, 'deny');
      }
    }
  });
});
