#!/usr/bin/env node
'use strict';

/**
 * Git info cache — batches git queries for cross-platform statusline performance.
 * Windows CreateProcess overhead makes 5-6 spawns per render expensive; this cache
 * collapses them to zero on cache-hit, with a 30s TTL and event-driven invalidation.
 * No bash-only syntax (no 2>/dev/null); windowsHide set on all exec calls.
 *
 * @module git-info-cache
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// 30s TTL handles external git changes (checkout outside the session).
// PostToolUse hooks call invalidateCache() after Edit/Write/Bash for faster refresh.
const CACHE_TTL = 30000;
const CACHE_MISS = Symbol('cache_miss');
const CACHE_SKIP = Symbol('cache_skip');

function isTimeoutError(error) {
  if (!error) return false;
  if (error.killed) return true;
  if (error.signal === 'SIGTERM') return true;
  return /timed out|etimedout/i.test(String(error.message || ''));
}

function getExecTimeoutMs() {
  const parsed = Number.parseInt(process.env.TKM_GIT_TIMEOUT_MS || '', 10);
  if (Number.isFinite(parsed) && parsed > 0) return parsed;
  return 3000;
}

/**
 * Safe command execution with optional cwd.
 * Timeout guard prevents hangs on slow or network-mounted repos.
 */
function execIn(cmd, cwd) {
  try {
    return {
      output: execSync(cmd, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore'],
        windowsHide: true,
        cwd: cwd || undefined,
        timeout: getExecTimeoutMs()
      }).trim(),
      timedOut: false
    };
  } catch (error) {
    return {
      output: '',
      timedOut: isTimeoutError(error)
    };
  }
}

/**
 * Cache file path for the given working directory (MD5-based name, 8 hex chars).
 */
function getCachePath(cwd) {
  const hash = require('crypto')
    .createHash('md5')
    .update(cwd)
    .digest('hex')
    .slice(0, 8);
  return path.join(os.tmpdir(), `sk-git-cache-${hash}.json`);
}

/**
 * Read cache if within TTL. Returns CACHE_MISS on miss or expiry.
 * No existsSync — avoids TOCTOU; read and catch instead.
 */
function readCache(cachePath, options = {}) {
  const { allowStale = false } = options;
  try {
    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    if (Date.now() - cache.timestamp < CACHE_TTL || allowStale) {
      return cache.data; // null = non-git dir; object = git info
    }
  } catch {
    // Missing, corrupt, or parse error — treat as cache miss
  }
  return CACHE_MISS;
}

/**
 * Atomic cache write — temp file then rename, prevents partial reads on Windows.
 */
function writeCache(cachePath, data) {
  const tmpPath = cachePath + '.tmp';
  try {
    fs.writeFileSync(tmpPath, JSON.stringify({ timestamp: Date.now(), data }));
    fs.renameSync(tmpPath, cachePath);
  } catch {
    try { fs.unlinkSync(tmpPath); } catch {}
  }
}

/**
 * Count non-empty lines in a newline-delimited string.
 */
function countLines(str) {
  if (!str) return 0;
  return str.split('\n').filter(l => l.trim()).length;
}

/**
 * Fetch git info in-process. The cache eliminates redundant spawns; this function
 * is only called on cache miss or TTL expiry.
 * @param {string} cwd - Directory to run git commands in
 * @returns {{ branch, unstaged, staged, ahead, behind } | null | symbol}
 *   null = not a git repo; CACHE_SKIP = timeout, use stale value
 */
function fetchGitInfo(cwd) {
  // Fast repo check — must run in target cwd, not process.cwd()
  const repoCheck = execIn('git rev-parse --git-dir', cwd);
  if (repoCheck.timedOut) return CACHE_SKIP;
  if (!repoCheck.output) {
    return null;
  }

  const branchPrimary = execIn('git branch --show-current', cwd);
  const branchFallback = execIn('git rev-parse --short HEAD', cwd);
  const unstagedResult = execIn('git diff --name-only', cwd);
  const stagedResult = execIn('git diff --cached --name-only', cwd);
  const aheadBehindResult = execIn('git rev-list --left-right --count @{u}...HEAD', cwd);

  if (
    branchPrimary.timedOut ||
    branchFallback.timedOut ||
    unstagedResult.timedOut ||
    stagedResult.timedOut ||
    aheadBehindResult.timedOut
  ) {
    return CACHE_SKIP;
  }

  const branch = branchPrimary.output || branchFallback.output;
  const unstaged = countLines(unstagedResult.output);
  const staged = countLines(stagedResult.output);

  // Ahead/behind — no 2>/dev/null; that flag is invalid on Windows cmd.exe
  let ahead = 0;
  let behind = 0;
  if (aheadBehindResult.output) {
    const parts = aheadBehindResult.output.split(/\s+/);
    behind = parseInt(parts[0], 10) || 0;
    ahead = parseInt(parts[1], 10) || 0;
  }

  return { branch, unstaged, staged, ahead, behind };
}

/**
 * Get git info for cwd — cache-first, fresh fetch on miss.
 */
function getGitInfo(cwd = process.cwd()) {
  const cachePath = getCachePath(cwd);

  // Cache first — includes cached null for non-git dirs
  const cached = readCache(cachePath);
  if (cached !== CACHE_MISS) return cached;

  // Cache miss — fetch fresh in target cwd
  const data = fetchGitInfo(cwd);
  if (data === CACHE_SKIP) {
    // Timeout/transient error: don't poison the cache as non-git.
    // Return last stale value if one exists.
    const stale = readCache(cachePath, { allowStale: true });
    return stale === CACHE_MISS ? null : stale;
  }

  // Cache null too — avoids re-spawning git on every render in non-git dirs
  writeCache(cachePath, data);

  return data;
}

/**
 * Invalidate cache for a directory — called after file changes to force a fresh git query.
 */
function invalidateCache(cwd = process.cwd()) {
  try { fs.unlinkSync(getCachePath(cwd)); } catch {}
}

module.exports = { getGitInfo, invalidateCache };
