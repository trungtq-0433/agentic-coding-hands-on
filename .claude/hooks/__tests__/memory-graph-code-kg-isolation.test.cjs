#!/usr/bin/env node
/**
 * Collision check (phase-03 Implementation Step 4, plans/260716-1046-memory-graph-tier-auto):
 * after a code-KG `graphify update .`, graph.json must contain NO conversation nodes — the
 * queue dir (memory-graph-out/) is gitignored, and graphify's detect() honors .gitignore
 * (empirically confirmed in the Phase 1 sanity spike). This test locks that guarantee in as
 * a regression check using the REAL graphify binary (skips if unavailable) — `update` is
 * code-only/no-LLM, so it's fast and deterministic, no network/API key needed.
 *
 * Run: bun test claude/hooks/__tests__/memory-graph-code-kg-isolation.test.cjs
 */

const { describe, it, before } = require('node:test');
const assert = require('node:assert');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

function hasGraphify() {
  try {
    execFileSync('graphify', ['--version'], { timeout: 5000, stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function git(cwd, args) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

describe('memory-graph-out/ isolation from the code knowledge graph', { skip: !hasGraphify() && 'graphify not on PATH' }, () => {
  let dir;

  before(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-collision-'));
    git(dir, ['init', '-q']);
    git(dir, ['config', 'user.email', 'test@example.com']);
    git(dir, ['config', 'user.name', 'Test']);
    git(dir, ['config', 'commit.gpgsign', 'false']);

    // Tracked code file — should be ingested.
    fs.writeFileSync(path.join(dir, 'index.js'), 'function trackedFn() { return 1; }\nmodule.exports = { trackedFn };\n');

    // Gitignored memory-graph queue dir — must NOT be ingested.
    fs.writeFileSync(path.join(dir, '.gitignore'), 'memory-graph-out/\n');
    const queueDir = path.join(dir, 'memory-graph-out', 'raw');
    fs.mkdirSync(queueDir, { recursive: true });
    fs.writeFileSync(
      path.join(queueDir, 'conv-secret-session.md'),
      '---\nsession_id: conv-secret-session\n---\n\n**User:** my_conversation_marker_fact\n'
    );

    git(dir, ['add', '-A']);
    git(dir, ['commit', '-q', '-m', 'init']);

    execFileSync('graphify', ['update', '.'], { cwd: dir, timeout: 60_000, stdio: 'ignore' });
  });

  it('code-KG graph.json ingests the tracked file', () => {
    const graph = JSON.parse(fs.readFileSync(path.join(dir, 'graphify-out', 'graph.json'), 'utf8'));
    const serialized = JSON.stringify(graph);
    assert.ok(serialized.includes('index.js'), 'tracked code file should be node-ified');
  });

  it('code-KG graph.json contains no trace of the gitignored conversation queue', () => {
    const graph = JSON.parse(fs.readFileSync(path.join(dir, 'graphify-out', 'graph.json'), 'utf8'));
    const serialized = JSON.stringify(graph);
    assert.ok(!serialized.includes('memory-graph-out'), 'queue dir path must not appear in the code graph');
    assert.ok(!serialized.includes('conv-secret-session'), 'queue session id must not appear');
    assert.ok(!serialized.includes('my_conversation_marker_fact'), 'queued conversation content must not leak in');
  });
});
