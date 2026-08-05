#!/usr/bin/env node
/**
 * Contract test — privacy-block.cjs.
 *
 * - Read on sensitive file: modern Claude deny shape + exit 0.
 * - Bash command referencing sensitive file when lib/env.cjs marks the host
 *     as Codex: modern deny shape + exit 0 (hard block; no AskUserQuestion
 *     protocol exists there).
 * - Bash command referencing sensitive file when lib/env.cjs marks the host
 *     as Claude (the kit-shipped default): stderr warn + exit 0 (preserves
 *     the existing approval flow).
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const HOOK_PATH = path.join(__dirname, '..', 'privacy-block.cjs');
const ENV_MARKER_PATH = path.join(__dirname, '..', 'lib', 'env.cjs');

function runHook(payload) {
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

/**
 * Temporarily swap lib/env.cjs to the requested agent marker, run fn(),
 * then restore the original file content. Done before each Codex-branch
 * assertion since the kit ships the Claude default on disk.
 */
async function withAgentMarker(agent, fn) {
  const original = fs.readFileSync(ENV_MARKER_PATH, 'utf-8');
  fs.writeFileSync(
    ENV_MARKER_PATH,
    `module.exports = { agent: '${agent}' };\n`,
  );
  try {
    return await fn();
  } finally {
    fs.writeFileSync(ENV_MARKER_PATH, original);
  }
}

describe('privacy-block.cjs — modern Claude block shape + F9 hybrid', () => {
  it('Read on sensitive .env.production → modern deny shape, exit 0', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Read',
      tool_input: { file_path: '/tmp/test-fixtures/.env.production' },
    };
    const { parsed, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0, 'must exit 0 (decision in JSON)');
    assert.ok(parsed && parsed.hookSpecificOutput, 'must emit hookSpecificOutput');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'PreToolUse');
    assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, 'deny');
    assert.ok(parsed.hookSpecificOutput.permissionDecisionReason);
  });

  it('Bash with Codex env marker → hard block (modern deny shape, exit 0)', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Bash',
      tool_input: { command: 'cat .env' },
    };
    const { parsed, exitCode } = await withAgentMarker('codex', () => runHook(payload));
    assert.strictEqual(exitCode, 0);
    assert.ok(parsed && parsed.hookSpecificOutput, 'Codex bash must emit JSON block');
    assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, 'deny');
  });

  it('Bash with default (Claude) env marker → warn-only (stderr, no JSON deny, exit 0)', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Bash',
      tool_input: { command: 'cat .env' },
    };
    const { stdout, stderr, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0);
    assert.ok(stderr.length > 0, 'Claude warn-only must emit stderr');
    if (stdout.trim()) {
      const parsed = JSON.parse(stdout.trim());
      if (parsed.hookSpecificOutput) {
        assert.notStrictEqual(
          parsed.hookSpecificOutput.permissionDecision,
          'deny',
          'Claude bash must NOT emit deny (warn-only)'
        );
      }
    }
  });
});
