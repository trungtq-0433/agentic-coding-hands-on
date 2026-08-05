#!/usr/bin/env node
/**
 * Integration tests for memory-graph-queue.cjs hook
 * Run: node --test claude/hooks/__tests__/memory-graph-queue.test.cjs
 *
 * Covers:
 * - Config gate behavior (isMemoryGraphEnabled)
 * - Hook event filtering (only Stop events)
 * - End-to-end queue file generation
 * - Fail-open guarantee (never exit non-zero)
 * - Edge cases (missing fields, malformed input, nonexistent transcript)
 */

const { describe, it, afterEach } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const HOOK_PATH = path.join(__dirname, '..', 'memory-graph-queue.cjs');
let tempDirs = [];

function createTempDir() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-queue-hook-test-'));
  tempDirs.push(dir);
  return dir;
}

afterEach(() => {
  for (const dir of tempDirs) {
    try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
  }
  tempDirs = [];
});

function runHook(inputData, env = {}, hookCwd = null) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [HOOK_PATH], {
      cwd: hookCwd || process.cwd(),
      env: { ...process.env, ...env }
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => { stdout += data.toString(); });
    proc.stderr.on('data', (data) => { stderr += data.toString(); });

    proc.stdin.write(JSON.stringify(inputData));
    proc.stdin.end();

    proc.on('close', (code) => resolve({ stdout, stderr, exitCode: code }));
    proc.on('error', reject);

    setTimeout(() => {
      proc.kill('SIGTERM');
      reject(new Error('Hook execution timed out'));
    }, 5000);
  });
}

function createSyntheticTranscript(turns) {
  return turns.map(t => JSON.stringify(t)).join('\n');
}

describe('memory-graph-queue.cjs', () => {

  describe('config gate', () => {
    it('exits 0 when MEMORY_GRAPH_DISABLE=1 env var set', async () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'test'.repeat(100) } },
        { message: { role: 'assistant', content: 'response'.repeat(100) } },
        { message: { role: 'user', content: 'test2'.repeat(100) } }
      ]));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'test-disabled-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, { MEMORY_GRAPH_DISABLE: '1' });

      assert.strictEqual(result.exitCode, 0);
      assert.strictEqual(fs.existsSync(path.join(tempDir, 'memory-graph-out')), false);
    });

    it('exits 0 when no config enables memory-graph (default: off)', async () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'test'.repeat(100) } },
        { message: { role: 'assistant', content: 'response'.repeat(100) } },
        { message: { role: 'user', content: 'test2'.repeat(100) } }
      ]));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'test-default-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);
      assert.strictEqual(fs.existsSync(path.join(tempDir, 'memory-graph-out')), false);
    });

    it('queues when config enables memory-graph', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'test'.repeat(100) } },
        { message: { role: 'assistant', content: 'response'.repeat(100) } },
        { message: { role: 'user', content: 'test2'.repeat(100) } }
      ]));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'test-enabled-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);
      const queueFile = path.join(tempDir, 'memory-graph-out', 'raw', 'test-enabled-session.md');
      assert(fs.existsSync(queueFile), 'Queue file should be created');
    });
  });

  describe('hook event filtering', () => {
    it('ignores non-Stop events', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'test'.repeat(100) } },
        { message: { role: 'assistant', content: 'resp'.repeat(50) } },
        { message: { role: 'user', content: 'test2'.repeat(100) } }
      ]));

      const result = await runHook({
        hook_event_name: 'PostToolUse',
        session_id: 'test-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);
      assert.strictEqual(fs.existsSync(path.join(tempDir, 'memory-graph-out')), false);
    });
  });

  describe('end-to-end queue generation', () => {
    it('generates queue file with correct frontmatter and speaker tags', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'What is AI? '.repeat(20) } },
        { message: { role: 'assistant', content: [{ type: 'text', text: 'AI is artificial intelligence. '.repeat(10) }] } },
        { message: { role: 'user', content: 'Tell me more. '.repeat(20) } },
        { message: { role: 'assistant', content: 'AI systems can learn and adapt. '.repeat(10) } }
      ]));

      const sessionId = 'end-to-end-test-session';
      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: sessionId,
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);

      const queueFile = path.join(tempDir, 'memory-graph-out', 'raw', `${sessionId}.md`);
      assert(fs.existsSync(queueFile), 'Queue file should exist');

      const content = fs.readFileSync(queueFile, 'utf8');
      assert.match(content, /^---/m);
      assert.match(content, new RegExp(`session_id: ${sessionId}`));
      assert.match(content, /captured_at: \d{4}-\d{2}-\d{2}T/);
      assert.match(content, /# Conversation transcript/);
      assert.match(content, /\*\*User:\*\* What is AI\?/);
      assert.match(content, /\*\*Assistant:\*\* AI is artificial intelligence\./);
    });

    it('skips tool_use and tool_result blocks', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'Read file.txt'.repeat(50) } },
        {
          message: {
            role: 'assistant',
            content: [{ type: 'tool_use', id: 'read-1', name: 'Read', input: { file: 'file.txt' } }]
          }
        },
        {
          message: {
            role: 'user',
            content: [{ type: 'tool_result', tool_use_id: 'read-1', content: 'secret_data' }]
          }
        },
        { message: { role: 'assistant', content: 'I read the file.'.repeat(20) } },
        { message: { role: 'user', content: 'Perfect.'.repeat(30) } }
      ]));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'tool-skip-test',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);

      const queueFile = path.join(tempDir, 'memory-graph-out', 'raw', 'tool-skip-test.md');
      const content = fs.readFileSync(queueFile, 'utf8');
      assert(!content.includes('secret_data'), 'Should not contain tool result content');
    });

    it('respects cap: truncates to last 40 turns when over limit', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      const turns = [];
      for (let i = 0; i < 60; i++) {
        const role = i % 2 === 0 ? 'user' : 'assistant';
        turns.push({ message: { role, content: 'x'.repeat(100) } });
      }
      fs.writeFileSync(transcriptPath, turns.map(t => JSON.stringify(t)).join('\n'));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'cap-test-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);

      const queueFile = path.join(tempDir, 'memory-graph-out', 'raw', 'cap-test-session.md');
      const content = fs.readFileSync(queueFile, 'utf8');
      // Count **User:** and **Assistant:** lines - each is a turn
      const userLines = (content.match(/\*\*User:\*\*/g) || []).length;
      const assistantLines = (content.match(/\*\*Assistant:\*\*/g) || []).length;
      const totalTurns = userLines + assistantLines;
      assert(totalTurns <= 40, `Should have <= 40 turns, got ${totalTurns}`);
    });
  });

  describe('trivial session handling', () => {
    it('skips session with only 1 user turn', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, JSON.stringify({ message: { role: 'user', content: 'Single?' } }));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'trivial-session',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);
      assert.strictEqual(fs.existsSync(path.join(tempDir, 'memory-graph-out', 'raw', 'trivial-session.md')), false);
    });
  });

  describe('deduplication', () => {
    it('does not overwrite existing queue file for same sessionId', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'First'.repeat(50) } },
        { message: { role: 'assistant', content: 'Response'.repeat(30) } },
        { message: { role: 'user', content: 'Second'.repeat(50) } }
      ]));

      const sessionId = 'dedup-test';
      const result1 = await runHook({
        hook_event_name: 'Stop',
        session_id: sessionId,
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);
      assert.strictEqual(result1.exitCode, 0);

      const queueFile = path.join(tempDir, 'memory-graph-out', 'raw', `${sessionId}.md`);
      const originalContent = fs.readFileSync(queueFile, 'utf8');

      // Mutate the transcript
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'Modified'.repeat(100) } },
        { message: { role: 'assistant', content: 'Different'.repeat(100) } },
        { message: { role: 'user', content: 'Another'.repeat(100) } }
      ]));

      const result2 = await runHook({
        hook_event_name: 'Stop',
        session_id: sessionId,
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);
      assert.strictEqual(result2.exitCode, 0);

      const finalContent = fs.readFileSync(queueFile, 'utf8');
      assert.strictEqual(finalContent, originalContent, 'File should not be overwritten');
    });
  });

  describe('fail-open guarantee', () => {
    it('exits 0 even when transcript file does not exist', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'missing-transcript',
        transcript_path: '/nonexistent/path/transcript.jsonl',
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0, 'Should exit 0 even with missing transcript');
    });

    it('exits 0 on empty input', async () => {
      const result = await runHook({});
      assert.strictEqual(result.exitCode, 0, 'Should exit 0 on empty input');
    });
  });

  describe('gitignore hygiene', () => {
    it('creates and populates .gitignore in project root', async () => {
      const tempDir = createTempDir();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(path.join(claudeDir, '.tkm.json'), JSON.stringify({
        memoryGraph: { enabled: true }
      }, null, 2));

      const transcriptPath = path.join(tempDir, 'transcript.jsonl');
      fs.writeFileSync(transcriptPath, createSyntheticTranscript([
        { message: { role: 'user', content: 'test'.repeat(100) } },
        { message: { role: 'assistant', content: 'resp'.repeat(50) } },
        { message: { role: 'user', content: 'test2'.repeat(100) } }
      ]));

      const result = await runHook({
        hook_event_name: 'Stop',
        session_id: 'gitignore-test',
        transcript_path: transcriptPath,
        cwd: tempDir
      }, {}, tempDir);

      assert.strictEqual(result.exitCode, 0);

      const gitignorePath = path.join(tempDir, '.gitignore');
      assert(fs.existsSync(gitignorePath), '.gitignore should be created');

      const content = fs.readFileSync(gitignorePath, 'utf8');
      assert.match(content, /memory-graph-out\//);
    });
  });

});
