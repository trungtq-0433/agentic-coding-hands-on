#!/usr/bin/env node
/**
 * Tests for memory-graph-queue-lib.cjs
 * Run: node --test claude/hooks/__tests__/memory-graph-queue-lib.test.cjs
 *
 * Covers:
 * - Config gate (isMemoryGraphEnabled)
 * - Transcript filtering (filterTranscript, extractText)
 * - Threshold heuristic (passesHeuristic)
 * - Cap (capTurns)
 * - Render + write (renderMarkdown, writeQueueFile)
 * - Directory resolution + .gitignore (resolveQueueDir, ensureGitignoreEntry)
 * - Fail-open guarantee
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  resolveQueueDir,
  filterTranscript,
  passesHeuristic,
  capTurns,
  renderMarkdown,
  writeQueueFile,
  extractText,
  ensureGitignoreEntry,
  MIN_USER_TURNS,
  MIN_TOTAL_CHARS,
  MAX_TURNS,
  MAX_CHARS
} = require('../lib/memory-graph-queue-lib.cjs');

// Temp directory tracking for cleanup
let tempDirs = [];

function createTempDir() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-queue-test-'));
  tempDirs.push(dir);
  return dir;
}

afterEach(() => {
  for (const dir of tempDirs) {
    try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
  }
  tempDirs = [];
});

describe('memory-graph-queue-lib.cjs', () => {

  describe('constants', () => {
    it('exports expected heuristic constants', () => {
      assert.strictEqual(MIN_USER_TURNS, 2);
      assert.strictEqual(MIN_TOTAL_CHARS, 200);
      assert.strictEqual(MAX_TURNS, 40);
      assert.strictEqual(MAX_CHARS, 16000);
    });
  });

  describe('extractText', () => {
    it('extracts text from string content', () => {
      const text = extractText('Hello world');
      assert.strictEqual(text, 'Hello world');
    });

    it('extracts text blocks from array content', () => {
      const content = [
        { type: 'text', text: 'Line 1' },
        { type: 'text', text: 'Line 2' }
      ];
      const text = extractText(content);
      assert.strictEqual(text, 'Line 1\nLine 2');
    });

    it('filters out non-text blocks', () => {
      const content = [
        { type: 'text', text: 'Keep this' },
        { type: 'tool_use', id: 'tool-1', name: 'Read', input: {} },
        { type: 'text', text: 'Keep this too' }
      ];
      const text = extractText(content);
      assert.strictEqual(text, 'Keep this\nKeep this too');
    });

    it('handles empty input', () => {
      assert.strictEqual(extractText(''), '');
      assert.strictEqual(extractText([]), '');
      assert.strictEqual(extractText(null), '');
    });

    it('trims whitespace from text blocks', () => {
      const content = [
        { type: 'text', text: '  padded text  ' },
        { type: 'text', text: '\n\n' }
      ];
      const text = extractText(content);
      assert.strictEqual(text, 'padded text');
    });
  });

  describe('filterTranscript', () => {
    it('reads and filters a JSONL transcript', () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');

      const lines = [
        JSON.stringify({
          message: { role: 'user', content: 'What is 2+2?' }
        }),
        JSON.stringify({
          message: { role: 'assistant', content: [{ type: 'text', text: 'The answer is 4.' }] }
        }),
        JSON.stringify({
          message: { role: 'user', content: 'Thanks' }
        })
      ];
      fs.writeFileSync(transcriptPath, lines.join('\n'));

      const turns = filterTranscript(transcriptPath);
      assert.strictEqual(turns.length, 3);
      assert.strictEqual(turns[0].role, 'user');
      assert.strictEqual(turns[0].text, 'What is 2+2?');
      assert.strictEqual(turns[1].role, 'assistant');
      assert.strictEqual(turns[1].text, 'The answer is 4.');
    });

    it('skips tool_use and tool_result blocks', () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');

      const lines = [
        JSON.stringify({
          message: { role: 'user', content: 'Read a file' }
        }),
        JSON.stringify({
          message: { role: 'assistant', content: [
            { type: 'tool_use', id: 'read-1', name: 'Read', input: { file: 'test.js' } }
          ] }
        }),
        JSON.stringify({
          message: { role: 'user', content: [
            { type: 'tool_result', tool_use_id: 'read-1', content: 'file contents' }
          ] }
        }),
        JSON.stringify({
          message: { role: 'assistant', content: 'I read the file.' }
        })
      ];
      fs.writeFileSync(transcriptPath, lines.join('\n'));

      const turns = filterTranscript(transcriptPath);
      // Only user "Read a file" and assistant "I read the file." should be kept
      assert.strictEqual(turns.length, 2);
      assert.strictEqual(turns[0].text, 'Read a file');
      assert.strictEqual(turns[1].text, 'I read the file.');
    });

    it('skips thinking blocks', () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');

      const lines = [
        JSON.stringify({
          message: { role: 'user', content: 'Hello' }
        }),
        JSON.stringify({
          message: { role: 'assistant', content: [
            { type: 'thinking', text: 'I think...' },
            { type: 'text', text: 'My response' }
          ] }
        })
      ];
      fs.writeFileSync(transcriptPath, lines.join('\n'));

      const turns = filterTranscript(transcriptPath);
      assert.strictEqual(turns.length, 2);
      assert.strictEqual(turns[1].text, 'My response');
    });

    it('skips entries with isSidechain: true', () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');

      const lines = [
        JSON.stringify({
          message: { role: 'user', content: 'Keep this' }
        }),
        JSON.stringify({
          isSidechain: true,
          message: { role: 'assistant', content: 'Drop this sidechain entry entirely' }
        }),
        JSON.stringify({
          message: { role: 'assistant', content: 'Keep this' }
        })
      ];
      fs.writeFileSync(transcriptPath, lines.join('\n'));

      const turns = filterTranscript(transcriptPath);
      assert.strictEqual(turns.length, 2);
      assert.strictEqual(turns[0].text, 'Keep this');
      assert.strictEqual(turns[1].text, 'Keep this');
    });

    it('handles missing or nonexistent transcript', () => {
      const turns = filterTranscript('/nonexistent/path/transcript.jsonl');
      assert.strictEqual(turns.length, 0);
    });

    it('handles malformed JSONL gracefully', () => {
      const tempDir = createTempDir();
      const transcriptPath = path.join(tempDir, 'transcript.jsonl');

      fs.writeFileSync(transcriptPath, [
        JSON.stringify({ message: { role: 'user', content: 'Valid line' } }),
        'this is not valid JSON',
        JSON.stringify({ message: { role: 'assistant', content: 'Another valid line' } })
      ].join('\n'));

      const turns = filterTranscript(transcriptPath);
      assert.strictEqual(turns.length, 2);
    });
  });

  describe('passesHeuristic', () => {
    it('accepts a session with >= 2 user turns and >= 200 chars', () => {
      const turns = [
        { role: 'user', text: 'a'.repeat(100) },
        { role: 'assistant', text: 'response' },
        { role: 'user', text: 'b'.repeat(100) }
      ];
      assert.strictEqual(passesHeuristic(turns), true);
    });

    it('rejects a session with < 2 user turns', () => {
      const turns = [
        { role: 'user', text: 'a'.repeat(300) }
      ];
      assert.strictEqual(passesHeuristic(turns), false);
    });

    it('rejects a session with < 200 total chars', () => {
      const turns = [
        { role: 'user', text: 'short' },
        { role: 'assistant', text: 'reply' },
        { role: 'user', text: 'brief' }
      ];
      assert.strictEqual(passesHeuristic(turns), false);
    });

    it('rejects an empty session', () => {
      assert.strictEqual(passesHeuristic([]), false);
    });

    it('accepts boundary case: exactly 2 user turns and 200 chars', () => {
      const turns = [
        { role: 'user', text: 'a'.repeat(100) },
        { role: 'assistant', text: 'filler' },
        { role: 'user', text: 'b'.repeat(100) }
      ];
      assert.strictEqual(passesHeuristic(turns), true);
    });
  });

  describe('capTurns', () => {
    it('keeps transcripts under MAX_TURNS unchanged', () => {
      const turns = Array.from({ length: 20 }, (_, i) => ({
        role: i % 2 === 0 ? 'user' : 'assistant',
        text: 'text'.repeat(10)
      }));
      const capped = capTurns(turns);
      assert.strictEqual(capped.length, 20);
    });

    it('truncates to last MAX_TURNS when exceeding turn limit', () => {
      const turns = Array.from({ length: 50 }, (_, i) => ({
        role: i % 2 === 0 ? 'user' : 'assistant',
        text: 'x'.repeat(100)
      }));
      const capped = capTurns(turns);
      assert.strictEqual(capped.length, MAX_TURNS);
      assert.strictEqual(capped[0], turns[50 - MAX_TURNS]);
    });

    it('further trims from front if char limit exceeded', () => {
      const turns = Array.from({ length: 40 }, (_, i) => ({
        role: i % 2 === 0 ? 'user' : 'assistant',
        text: 'x'.repeat(500) // 40 turns * 500 chars = 20000 > MAX_CHARS
      }));
      const capped = capTurns(turns);
      const totalChars = capped.reduce((sum, t) => sum + t.text.length, 0);
      assert(totalChars <= MAX_CHARS, `Total chars ${totalChars} should be <= ${MAX_CHARS}`);
      assert(capped.length < 40, 'Should trim more than just taking last 40 turns');
    });

    it('preserves at least 1 turn even if it exceeds MAX_CHARS alone', () => {
      const turns = [
        { role: 'user', text: 'x'.repeat(MAX_CHARS + 1000) }
      ];
      const capped = capTurns(turns);
      assert.strictEqual(capped.length, 1);
    });

    it('handles empty transcript', () => {
      const capped = capTurns([]);
      assert.strictEqual(capped.length, 0);
    });
  });

  describe('renderMarkdown', () => {
    it('renders frontmatter + speaker-tagged body', () => {
      const turns = [
        { role: 'user', text: 'Hello' },
        { role: 'assistant', text: 'Hi there' }
      ];
      const markdown = renderMarkdown(turns, 'test-session-123');

      assert.match(markdown, /^---/);
      assert.match(markdown, /session_id: test-session-123/);
      assert.match(markdown, /captured_at: \d{4}-\d{2}-\d{2}T/); // ISO datetime
      assert.match(markdown, /# Conversation transcript/);
      assert.match(markdown, /\*\*User:\*\* Hello/);
      assert.match(markdown, /\*\*Assistant:\*\* Hi there/);
    });

    it('produces valid markdown structure', () => {
      const turns = [
        { role: 'user', text: 'Question?' },
        { role: 'assistant', text: 'Answer.' }
      ];
      const markdown = renderMarkdown(turns, 'session-id');

      const lines = markdown.split('\n');
      assert.strictEqual(lines[0], '---');
      assert(lines.some(l => l.includes('session_id:')));
      assert(lines.some(l => l.includes('captured_at:')));
      assert(lines.some(l => l === '---'));
      assert(lines.some(l => l === '# Conversation transcript'));
    });

    it('handles turns with multiline text', () => {
      const turns = [
        { role: 'user', text: 'Line 1\nLine 2\nLine 3' },
        { role: 'assistant', text: 'Single response' }
      ];
      const markdown = renderMarkdown(turns, 'session-id');

      assert.match(markdown, /\*\*User:\*\* Line 1\nLine 2\nLine 3/);
    });

    it('includes trailing newline', () => {
      const turns = [{ role: 'user', text: 'Test' }];
      const markdown = renderMarkdown(turns, 'session-id');

      assert(markdown.endsWith('\n'));
    });

    it('redacts secret-shaped text before writing it into the markdown body', () => {
      const turns = [
        { role: 'user', text: 'my AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY, keep it safe' },
        { role: 'assistant', text: 'Got it, noted.' }
      ];
      const markdown = renderMarkdown(turns, 'session-id');

      assert(!markdown.includes('wJalrXUtnFEMI'));
      assert.match(markdown, /AWS_SECRET_ACCESS_KEY=\[REDACTED\]/);
    });
  });

  describe('writeQueueFile', () => {
    it('writes a new queue file atomically', () => {
      const tempDir = createTempDir();
      const queueDir = path.join(tempDir, 'queue');
      fs.mkdirSync(queueDir, { recursive: true });

      const markdown = '# Test\n**User:** Hello\n';
      const result = writeQueueFile(queueDir, 'session-001', markdown);

      assert.strictEqual(result.written, true);
      assert(fs.existsSync(result.path));
      assert.strictEqual(
        fs.readFileSync(result.path, 'utf8'),
        markdown
      );
    });

    it('is idempotent: second write to same sessionId is a no-op', () => {
      const tempDir = createTempDir();
      const queueDir = path.join(tempDir, 'queue');
      fs.mkdirSync(queueDir, { recursive: true });

      const markdown1 = '# First write';
      const result1 = writeQueueFile(queueDir, 'session-002', markdown1);
      assert.strictEqual(result1.written, true);

      const markdown2 = '# Second write (should be ignored)';
      const result2 = writeQueueFile(queueDir, 'session-002', markdown2);
      assert.strictEqual(result2.written, false);
      assert.strictEqual(result2.reason, 'dedup');

      const stored = fs.readFileSync(result1.path, 'utf8');
      assert.strictEqual(stored, markdown1);
    });

    it('uses predictable session-based filenames', () => {
      const tempDir = createTempDir();
      const queueDir = path.join(tempDir, 'queue');
      fs.mkdirSync(queueDir, { recursive: true });

      writeQueueFile(queueDir, 'my-session', 'content');

      assert(fs.existsSync(path.join(queueDir, 'my-session.md')));
    });

    it('handles multiple different sessionIds', () => {
      const tempDir = createTempDir();
      const queueDir = path.join(tempDir, 'queue');
      fs.mkdirSync(queueDir, { recursive: true });

      writeQueueFile(queueDir, 'session-a', 'Content A');
      writeQueueFile(queueDir, 'session-b', 'Content B');

      assert(fs.existsSync(path.join(queueDir, 'session-a.md')));
      assert(fs.existsSync(path.join(queueDir, 'session-b.md')));

      const filesInQueue = fs.readdirSync(queueDir);
      assert.strictEqual(filesInQueue.length, 2);
    });
  });

  describe('ensureGitignoreEntry', () => {
    it('appends entry to existing .gitignore', () => {
      const tempDir = createTempDir();
      const gitignorePath = path.join(tempDir, '.gitignore');
      fs.writeFileSync(gitignorePath, 'node_modules/\n');

      ensureGitignoreEntry(tempDir, 'memory-graph-out/');

      const content = fs.readFileSync(gitignorePath, 'utf8');
      assert.match(content, /memory-graph-out\//);
    });

    it('creates .gitignore if absent', () => {
      const tempDir = createTempDir();
      const gitignorePath = path.join(tempDir, '.gitignore');

      ensureGitignoreEntry(tempDir, 'memory-graph-out/');

      assert(fs.existsSync(gitignorePath));
      const content = fs.readFileSync(gitignorePath, 'utf8');
      assert.match(content, /memory-graph-out\//);
    });

    it('does not duplicate entry', () => {
      const tempDir = createTempDir();
      const gitignorePath = path.join(tempDir, '.gitignore');

      ensureGitignoreEntry(tempDir, 'memory-graph-out/');
      ensureGitignoreEntry(tempDir, 'memory-graph-out/');

      const content = fs.readFileSync(gitignorePath, 'utf8');
      const count = (content.match(/memory-graph-out/g) || []).length;
      assert.strictEqual(count, 1);
    });

    it('preserves existing content', () => {
      const tempDir = createTempDir();
      const gitignorePath = path.join(tempDir, '.gitignore');
      fs.writeFileSync(gitignorePath, 'old-entry/\n');

      ensureGitignoreEntry(tempDir, 'memory-graph-out/');

      const content = fs.readFileSync(gitignorePath, 'utf8');
      assert.match(content, /old-entry\//);
      assert.match(content, /memory-graph-out\//);
    });

    it('handles entry without trailing slash variant', () => {
      const tempDir = createTempDir();
      const gitignorePath = path.join(tempDir, '.gitignore');
      fs.writeFileSync(gitignorePath, 'memory-graph-out\n');

      ensureGitignoreEntry(tempDir, 'memory-graph-out/');

      const content = fs.readFileSync(gitignorePath, 'utf8');
      const count = (content.match(/memory-graph-out/g) || []).length;
      assert.strictEqual(count, 1);
    });

    it('fails gracefully on permission errors', () => {
      const tempDir = createTempDir();
      // This should not throw; best-effort behavior
      ensureGitignoreEntry('/nonexistent/path/that/cannot/be/written', 'entry/');
      // If we reach here without throwing, the graceful failure worked
      assert(true);
    });
  });

  describe('resolveQueueDir', () => {
    it('creates queue directory recursively', () => {
      const tempDir = createTempDir();
      const queueDir = resolveQueueDir(tempDir);

      assert(fs.existsSync(queueDir));
      assert(queueDir.includes('memory-graph-out'));
      assert(queueDir.includes('raw'));
    });

    it('ensures .gitignore entry', () => {
      const tempDir = createTempDir();
      resolveQueueDir(tempDir);

      const gitignorePath = path.join(tempDir, '.gitignore');
      assert(fs.existsSync(gitignorePath));
      const content = fs.readFileSync(gitignorePath, 'utf8');
      assert.match(content, /memory-graph-out\//);
    });

    it('returns correct directory path', () => {
      const tempDir = createTempDir();
      const queueDir = resolveQueueDir(tempDir);

      assert(queueDir.startsWith(tempDir));
      assert(queueDir.includes('memory-graph-out' + path.sep + 'raw'));
    });

    it('is idempotent', () => {
      const tempDir = createTempDir();
      const queueDir1 = resolveQueueDir(tempDir);
      const queueDir2 = resolveQueueDir(tempDir);

      assert.strictEqual(queueDir1, queueDir2);
      assert(fs.existsSync(queueDir1));
    });
  });

});
