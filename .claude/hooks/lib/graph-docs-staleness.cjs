'use strict';

/**
 * graph-docs-staleness — detect doc files changed since the knowledge graph was
 * built, plus a per-HEAD throttle so the SessionStart nudge does not nag.
 *
 * CODE edges are refreshed cheaply and automatically — `graphify update .` (AST, free,
 * no LLM) runs each session (SessionStart hook) and on commit (native git hooks). Doc
 * files (.md/.mdx/…) carry SEMANTIC edges that need an LLM re-extraction — only
 * `rebuild-spec` does that; `graphify update .` does NOT touch docs. This module powers
 * the kit's advisory "your docs are stale" nudge — it never spends tokens itself.
 *
 * @module graph-docs-staleness
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

// Doc files that carry semantic (LLM-extracted) graph edges.
const DOC_EXT_RE = /\.(md|mdx|rst|txt|pdf)$/i;

// git pathspecs: doc extensions anywhere + docs/, excluding noise dirs.
const DOC_PATHSPECS = [
  '*.md', '*.mdx', '*.rst', '*.txt', '*.pdf', 'docs/',
  ':(exclude)graphify-out/**',
  ':(exclude)node_modules/**',
  ':(exclude).git/**',
  ':(exclude)plans/**',
];

const THROTTLE_FILE = '.docs_nudge_at';
const NUDGE_PATH_CAP = 5;

function git(projectDir, args, timeout = 5000) {
  return execFileSync('git', args, {
    cwd: projectDir,
    encoding: 'utf8',
    timeout,
    stdio: ['ignore', 'pipe', 'ignore'],
  });
}

function isGitRepo(projectDir) {
  try {
    git(projectDir, ['rev-parse', '--is-inside-work-tree']);
    return true;
  } catch {
    return false;
  }
}

function headSha(projectDir) {
  try {
    return git(projectDir, ['rev-parse', 'HEAD']).trim();
  } catch {
    return null;
  }
}

/**
 * Read `built_at_commit` from graph.json without loading the whole file (it can be
 * many MB). graphify writes the field at the END of the JSON, so read only the tail
 * (last 64 KB). Returns the sha string, or null if absent (→ caller's mtime fallback).
 */
function readBuiltAtCommit(graphPath) {
  let fd;
  try {
    const size = fs.statSync(graphPath).size;
    const len = Math.min(size, 65536);
    const buf = Buffer.alloc(len);
    fd = fs.openSync(graphPath, 'r');
    fs.readSync(fd, buf, 0, len, size - len); // tail
    const m = buf.toString('utf8').match(/"built_at_commit"\s*:\s*"([0-9a-fA-F]{7,40})"/);
    return m ? m[1] : null;
  } catch {
    return null;
  } finally {
    if (fd !== undefined) { try { fs.closeSync(fd); } catch { /* ignore */ } }
  }
}

function commitInHistory(projectDir, sha) {
  if (!sha) return false;
  try {
    git(projectDir, ['cat-file', '-e', `${sha}^{commit}`]);
    return true;
  } catch {
    return false;
  }
}

/** Doc files committed since `sinceSha` (HEAD if range invalid). */
function committedDocChanges(projectDir, sinceSha) {
  try {
    const out = git(projectDir, [
      'diff', '--name-only', `${sinceSha}..HEAD`, '--', ...DOC_PATHSPECS,
    ]);
    return out.split('\n').map((l) => l.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

/** Uncommitted (staged + working tree) doc files. */
function uncommittedDocChanges(projectDir) {
  try {
    const out = git(projectDir, [
      'status', '--porcelain', '--', ...DOC_PATHSPECS,
    ]);
    return out
      .split('\n')
      .map((l) => l.slice(3).trim())
      .filter((p) => p && DOC_EXT_RE.test(p));
  } catch {
    return [];
  }
}

/**
 * Fallback when there is no usable build commit: tracked doc files whose mtime
 * is newer than the graph file itself.
 */
function docsNewerThanGraph(projectDir, graphPath) {
  try {
    const graphMtime = fs.statSync(graphPath).mtimeMs;
    const tracked = git(projectDir, ['ls-files', '--', ...DOC_PATHSPECS])
      .split('\n').map((l) => l.trim()).filter(Boolean);
    return tracked.filter((rel) => {
      try {
        return fs.statSync(path.join(projectDir, rel)).mtimeMs > graphMtime;
      } catch {
        return false;
      }
    });
  } catch {
    return [];
  }
}

/**
 * Detect doc files that changed since the graph was built.
 * @returns {{ paths: string[], uncommittedCount: number, head: string|null }}
 */
function detectStaleDocs(projectDir, graphPath) {
  if (!isGitRepo(projectDir)) {
    return { paths: [], uncommittedCount: 0, head: null };
  }

  const uncommitted = uncommittedDocChanges(projectDir);
  const builtAt = readBuiltAtCommit(graphPath);

  let committed = [];
  if (commitInHistory(projectDir, builtAt)) {
    committed = committedDocChanges(projectDir, builtAt);
  } else {
    // No usable build commit (missing field or shallow clone) → mtime heuristic.
    committed = docsNewerThanGraph(projectDir, graphPath);
  }

  const paths = Array.from(new Set([...committed, ...uncommitted]));
  return { paths, uncommittedCount: uncommitted.length, head: headSha(projectDir) };
}

/** Stable signature of "what we last nudged about". */
function signature(head, uncommittedCount) {
  return `${head || 'no-head'}:${uncommittedCount}`;
}

function throttleFilePath(graphDir) {
  return path.join(graphDir, THROTTLE_FILE);
}

/** True when we already nudged for this exact HEAD + uncommitted-doc state. */
function alreadyNudged(graphDir, head, uncommittedCount) {
  try {
    const last = fs.readFileSync(throttleFilePath(graphDir), 'utf8').trim();
    return last === signature(head, uncommittedCount);
  } catch {
    return false;
  }
}

function recordNudge(graphDir, head, uncommittedCount) {
  try {
    fs.writeFileSync(throttleFilePath(graphDir), signature(head, uncommittedCount));
    return true;
  } catch {
    return false;
  }
}

/** Build the advisory nudge string injected into SessionStart context. */
function buildNudge(paths) {
  const n = paths.length;
  const shown = paths.slice(0, NUDGE_PATH_CAP);
  const more = n > NUDGE_PATH_CAP ? `\n  …and ${n - NUDGE_PATH_CAP} more` : '';
  const list = shown.map((p) => `  - ${p}`).join('\n');
  return (
    `Knowledge graph: ${n} doc file(s) changed since the graph's semantic layer was built ` +
    `(code edges are refreshed automatically each session). To refresh the doc/semantic ` +
    `edges, re-run \`/tkm:rebuild-spec\` — it re-extracts docs (\`graphify update .\` covers ` +
    `code only):\n${list}${more}`
  );
}

module.exports = {
  DOC_EXT_RE,
  DOC_PATHSPECS,
  detectStaleDocs,
  buildNudge,
  alreadyNudged,
  recordNudge,
  signature,
  readBuiltAtCommit,
};
