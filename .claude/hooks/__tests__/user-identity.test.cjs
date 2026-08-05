#!/usr/bin/env node

const { afterEach, beforeEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  CACHE_TTL_MS,
  isValidGithubLogin,
  readCache,
  writeCache,
  resolveGithubUser,
} = require('../lib/user-identity.cjs');

let tmpDir;
let cacheFile;
let originalPath;

beforeEach(() => {
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-user-identity-'));
  cacheFile = path.join(tmpDir, 'sk-user.json');
  originalPath = process.env.PATH;
});

afterEach(() => {
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) { /* ignore */ }
  process.env.PATH = originalPath;
});

describe('isValidGithubLogin', () => {
  it('accepts a normal login', () => {
    assert.strictEqual(isValidGithubLogin('octocat'), true);
  });

  it('accepts alphanumeric + hyphen', () => {
    assert.strictEqual(isValidGithubLogin('octo-cat-42'), true);
  });

  it('rejects leading hyphen', () => {
    assert.strictEqual(isValidGithubLogin('-octocat'), false);
  });

  it('rejects trailing hyphen', () => {
    assert.strictEqual(isValidGithubLogin('octocat-'), false);
  });

  it('accepts single character', () => {
    assert.strictEqual(isValidGithubLogin('a'), true);
    assert.strictEqual(isValidGithubLogin('-'), false);
  });

  it('rejects login > 39 chars', () => {
    assert.strictEqual(isValidGithubLogin('a'.repeat(40)), false);
  });

  it('rejects empty string', () => {
    assert.strictEqual(isValidGithubLogin(''), false);
  });

  it('rejects non-string input', () => {
    assert.strictEqual(isValidGithubLogin(undefined), false);
    assert.strictEqual(isValidGithubLogin(null), false);
    assert.strictEqual(isValidGithubLogin(42), false);
  });

  it('rejects login with invalid chars', () => {
    assert.strictEqual(isValidGithubLogin('octo cat'), false);
    assert.strictEqual(isValidGithubLogin('octo_cat'), false);
  });
});

describe('readCache / writeCache', () => {
  it('returns null when cache file missing', () => {
    assert.strictEqual(readCache(cacheFile), null);
  });

  it('writes and reads a fresh cache entry', () => {
    assert.strictEqual(writeCache(cacheFile, 'octocat', 'gh'), true);
    const cached = readCache(cacheFile);
    assert.ok(cached);
    assert.strictEqual(cached.githubLogin, 'octocat');
    assert.strictEqual(cached.source, 'gh');
    assert.strictEqual(typeof cached.resolvedAt, 'number');
  });

  it('rejects writing invalid login', () => {
    assert.strictEqual(writeCache(cacheFile, '-bad', 'gh'), false);
    assert.strictEqual(fs.existsSync(cacheFile), false);
  });

  it('rejects writing invalid source', () => {
    assert.strictEqual(writeCache(cacheFile, 'octocat', 'bogus'), false);
  });

  it('returns null for stale cache (> 30d)', () => {
    const stalePayload = {
      githubLogin: 'octocat',
      resolvedAt: Date.now() - CACHE_TTL_MS - 1000,
      source: 'gh',
    };
    fs.writeFileSync(cacheFile, JSON.stringify(stalePayload));
    assert.strictEqual(readCache(cacheFile), null);
  });

  it('returns null for corrupted JSON', () => {
    fs.writeFileSync(cacheFile, '{not valid json');
    assert.strictEqual(readCache(cacheFile), null);
  });

  it('returns null when login in cache is invalid', () => {
    fs.writeFileSync(cacheFile, JSON.stringify({
      githubLogin: '-nope',
      resolvedAt: Date.now(),
      source: 'gh',
    }));
    assert.strictEqual(readCache(cacheFile), null);
  });
});

describe('resolveGithubUser', () => {
  it('returns cached login on hit without invoking tkm', () => {
    writeCache(cacheFile, 'octocat', 'manual');
    // Empty PATH → if it falls through to exec, tkm would not resolve.
    process.env.PATH = '';
    const login = resolveGithubUser({ cacheFile });
    assert.strictEqual(login, 'octocat');
  });

  it('returns null when tkm CLI missing and no cache', () => {
    process.env.PATH = tmpDir; // directory guaranteed to not contain tkm
    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });

  it('writes cache with source=gh when tkm resolves', () => {
    // Stub `tkm` by placing a fake executable on PATH. Output mirrors
    // `tkm auth status --json` — a single line JSON object with loggedIn
    // + githubLogin (plus the other status fields, which this code ignores).
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\necho \'{"loggedIn":true,"githubLogin":"stub-user","email":"e@x","expiresAt":1}\'\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 2000 });
    assert.strictEqual(login, 'stub-user');

    const cached = readCache(cacheFile);
    assert.ok(cached);
    assert.strictEqual(cached.source, 'gh');
    assert.strictEqual(cached.githubLogin, 'stub-user');
  });

  it('returns null when tkm times out', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    // /usr/bin/sleep absolute path — PATH override below strips /usr/bin from
    // the child env, so bare `sleep` would silently fail and the script would
    // race past the delay.
    fs.writeFileSync(fakeTkm, '#!/bin/sh\n/usr/bin/sleep 5\necho \'{"loggedIn":true,"githubLogin":"too-late"}\'\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 250 });
    assert.strictEqual(login, null);
  });

  it('returns null when tkm outputs invalid login', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\necho \'{"loggedIn":true,"githubLogin":"-bad"}\'\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });

  it('returns null when tkm reports loggedIn=false', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\necho \'{"loggedIn":false,"githubLogin":null}\'\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });

  it('returns null when tkm session lacks a GitHub identity (githubLogin=null)', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\necho \'{"loggedIn":true,"githubLogin":null,"email":"u@example.com"}\'\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });

  it('returns null when tkm exits non-zero', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\nexit 1\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });

  it('returns null when tkm outputs non-JSON', () => {
    const fakeBin = path.join(tmpDir, 'bin');
    fs.mkdirSync(fakeBin, { recursive: true });
    const fakeTkm = path.join(fakeBin, 'tkm');
    fs.writeFileSync(fakeTkm, '#!/bin/sh\necho garbage-not-json\n');
    fs.chmodSync(fakeTkm, 0o755);
    process.env.PATH = fakeBin;

    const login = resolveGithubUser({ cacheFile, timeoutMs: 500 });
    assert.strictEqual(login, null);
  });
});
