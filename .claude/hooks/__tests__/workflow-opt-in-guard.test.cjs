'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.join(__dirname, '..', 'workflow-opt-in-guard.cjs');

let counter = 0;
function writeTranscript(entries) {
  const p = path.join(os.tmpdir(), `wf-guard-${process.pid}-${counter++}.jsonl`);
  fs.writeFileSync(p, entries.map((e) => JSON.stringify(e)).join('\n'));
  return p;
}

const userText = (text) => ({ type: 'user', message: { role: 'user', content: text } });
const userBlocks = (blocks) => ({ type: 'user', message: { role: 'user', content: blocks } });
const assistant = () => ({ type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: 'working' }] } });
const toolResult = () => userBlocks([{ type: 'tool_result', tool_use_id: 'x', content: 'ok' }]);

/** Run the guard with a payload; return true when it denies the tool call. */
function denies(payload) {
  const out = execSync(`node "${HOOK}"`, { input: JSON.stringify(payload), encoding: 'utf8' }) || '{}';
  const parsed = JSON.parse(out);
  return Boolean(parsed.hookSpecificOutput && parsed.hookSpecificOutput.permissionDecision === 'deny');
}

const workflowCall = (transcript_path) => ({ tool_name: 'Workflow', tool_input: {}, transcript_path });

test('allows Workflow when the latest prompt contains "workflow"', () => {
  const t = writeTranscript([userText('please run a workflow to audit this repo')]);
  assert.ok(!denies(workflowCall(t)));
});

test('opt-in word is case-insensitive', () => {
  const t = writeTranscript([userText('Kick off a WORKFLOW now')]);
  assert.ok(!denies(workflowCall(t)));
});

test('recognizes text-block array content', () => {
  const t = writeTranscript([userBlocks([{ type: 'text', text: 'do a workflow over the screens' }])]);
  assert.ok(!denies(workflowCall(t)));
});

test('denies Workflow when the latest prompt lacks "workflow"', () => {
  const t = writeTranscript([userText('refactor the parser and add tests')]);
  assert.ok(denies(workflowCall(t)));
});

test('skips trailing tool_result entries and reads the real human prompt', () => {
  const t = writeTranscript([userText('run a workflow over all screens'), assistant(), toolResult()]);
  assert.ok(!denies(workflowCall(t)));
});

test('fail-closed: only tool_result user entries, no typed prompt', () => {
  const t = writeTranscript([assistant(), toolResult()]);
  assert.ok(denies(workflowCall(t)));
});

test('fail-closed: missing transcript_path', () => {
  assert.ok(denies({ tool_name: 'Workflow', tool_input: {} }));
});

test('fail-closed: nonexistent transcript file', () => {
  assert.ok(denies(workflowCall(path.join(os.tmpdir(), 'wf-guard-does-not-exist.jsonl'))));
});

test('passes through non-Workflow tools', () => {
  assert.ok(!denies({ tool_name: 'Bash', tool_input: { command: 'ls' } }));
});

test('fail-closed on malformed input', () => {
  const out = execSync(`node "${HOOK}"`, { input: 'not json', encoding: 'utf8' }) || '{}';
  const parsed = JSON.parse(out);
  assert.ok(parsed.hookSpecificOutput && parsed.hookSpecificOutput.permissionDecision === 'deny');
});
