#!/usr/bin/env node

const { afterEach, beforeEach, describe, it } = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');

const client = require('../lib/telemetry-client.cjs');

const {
  MAX_FEEDBACK_CHARS,
  MAX_RATING_COMMENT_CHARS,
  buildCwdHash,
  normalizeScore,
  parseArgs,
  post,
  readEndpoint,
  resolveEndpointSource,
  sendFeedback,
  sendRating,
  truncate,
} = client;

let tmpDir;
let cwdMetaDir;
let cacheFile;
let originalEnv;

beforeEach(() => {
  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-tel-'));
  cwdMetaDir = path.join(tmpDir, 'proj');
  fs.mkdirSync(path.join(cwdMetaDir, '.claude'), { recursive: true });
  cacheFile = path.join(tmpDir, 'sk-user.json');

  originalEnv = { ...process.env };
  delete process.env.TKM_TELEMETRY_ENDPOINT;
  delete process.env.TKM_TELEMETRY_DEV;
  delete process.env.CLAUDE_PLUGIN_ROOT;
  // Prevent sendFeedback from hitting the real ~/.claude/sk-user.json during tests.
  process.env.HOME = tmpDir;
});

afterEach(() => {
  try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) { /* ignore */ }
  process.env = originalEnv;
});

function writeMetadata(cwdDir, data) {
  fs.writeFileSync(path.join(cwdDir, '.claude', 'metadata.json'), JSON.stringify(data));
}

function writeUserCache(login) {
  // Mirrors claude/hooks/lib/user-identity.cjs format.
  const payload = { githubLogin: login, resolvedAt: Date.now(), source: 'manual' };
  const claudeDir = path.join(tmpDir, '.claude');
  fs.mkdirSync(claudeDir, { recursive: true });
  fs.writeFileSync(path.join(claudeDir, 'sk-user.json'), JSON.stringify(payload));
}

/* ─── truncate ───────────────────────────────────────────────────────── */

describe('truncate', () => {
  it('returns unchanged when within limit', () => {
    assert.strictEqual(truncate('hi', 10), 'hi');
  });

  it('slices to max when exceeding', () => {
    assert.strictEqual(truncate('abcdef', 3), 'abc');
  });

  it('returns empty on non-string input', () => {
    assert.strictEqual(truncate(undefined, 5), '');
    assert.strictEqual(truncate(42, 5), '');
  });

  it('MAX_FEEDBACK_CHARS is 2000', () => {
    assert.strictEqual(MAX_FEEDBACK_CHARS, 2000);
  });
});

/* ─── parseArgs ──────────────────────────────────────────────────────── */

describe('parseArgs', () => {
  it('parses --k=v pairs', () => {
    const a = parseArgs(['--text=hello world', '--session-id=abc']);
    assert.strictEqual(a.text, 'hello world');
    assert.strictEqual(a['session-id'], 'abc');
  });

  it('parses bare --flag as true', () => {
    const a = parseArgs(['--dry-run']);
    assert.strictEqual(a['dry-run'], true);
  });

  it('collects positional args in _', () => {
    const a = parseArgs(['send-feedback', '--text=hi']);
    assert.deepStrictEqual(a._, ['send-feedback']);
  });
});

/* ─── buildCwdHash ───────────────────────────────────────────────────── */

describe('buildCwdHash', () => {
  it('returns deterministic sha256 hex (64 chars)', () => {
    const h = buildCwdHash(cwdMetaDir);
    assert.strictEqual(h.length, 64);
    assert.match(h, /^[0-9a-f]+$/);
  });

  it('same input → same hash', () => {
    assert.strictEqual(buildCwdHash(cwdMetaDir), buildCwdHash(cwdMetaDir));
  });

  it('different cwds → different hashes (no git remote)', () => {
    const other = path.join(tmpDir, 'other');
    fs.mkdirSync(other);
    assert.notStrictEqual(buildCwdHash(cwdMetaDir), buildCwdHash(other));
  });

  it('falls back to absolute cwd when git remote missing', () => {
    const h = buildCwdHash(cwdMetaDir);
    const expected = crypto
      .createHash('sha256')
      .update(path.resolve(cwdMetaDir))
      .digest('hex');
    assert.strictEqual(h, expected);
  });
});

/* ─── readEndpoint ───────────────────────────────────────────────────── */

describe('readEndpoint', () => {
  it('metadata wins over env by default (no dev gate)', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api' });
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://from-env/api';
    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-meta/api');
  });

  it('env TKM_TELEMETRY_ENDPOINT wins over metadata ONLY with TKM_TELEMETRY_DEV=1', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api' });
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://from-env/api';
    process.env.TKM_TELEMETRY_DEV = '1';
    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-env/api');
  });

  it('env used as fallback when metadata has no endpoint (no gate needed)', () => {
    writeMetadata(cwdMetaDir, {}); // metadata exists but no telemetry_endpoint
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://from-env/api';
    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-env/api');
  });

  it('falls back to metadata telemetry_endpoint', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api/' });
    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-meta/api');
  });

  it('returns null when neither is set', () => {
    assert.strictEqual(readEndpoint(cwdMetaDir), null);
  });
});

/* ─── post ───────────────────────────────────────────────────────────── */

describe('post', () => {
  it('returns no_endpoint when url missing', async () => {
    const r = await post(null, { x: 1 }, { version: '1.0.0' });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'no_endpoint');
  });

  it('sends body + X-TKM-Client header to local server', async () => {
    const received = await new Promise((resolve, reject) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve({
            method: req.method,
            clientHeader: req.headers['x-tkm-client'],
            tokenHeader: req.headers['x-sk-token'],
            contentType: req.headers['content-type'],
            body,
          });
        });
      });
      server.on('error', reject);
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        const r = await post(`http://127.0.0.1:${port}/api/feedback`, { hello: 'world' }, {
          version: '1.8.0',
          timeoutMs: 2000,
        });
        assert.strictEqual(r.ok, true);
        assert.strictEqual(r.status, 204);
      });
    });

    assert.strictEqual(received.method, 'POST');
    assert.strictEqual(received.clientHeader, 'agent-kit/1.8.0');
    assert.strictEqual(received.tokenHeader, undefined);
    assert.match(received.contentType || '', /application\/json/);
    assert.deepStrictEqual(JSON.parse(received.body), { hello: 'world' });
  });

  it('sends agent-kit/unknown when version is null', async () => {
    const received = await new Promise((resolve, reject) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve({ clientHeader: req.headers['x-tkm-client'] });
        });
      });
      server.on('error', reject);
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        await post(`http://127.0.0.1:${port}/api/x`, {}, { timeoutMs: 2000 });
      });
    });
    assert.strictEqual(received.clientHeader, 'agent-kit/unknown');
  });

  it('returns {ok:false,status} on server error', async () => {
    const server = http.createServer((_req, res) => {
      res.writeHead(500); res.end('boom');
    });
    await new Promise((r) => server.listen(0, '127.0.0.1', r));
    const { port } = server.address();
    const r = await post(`http://127.0.0.1:${port}/x`, {}, { version: '1.0', timeoutMs: 2000 });
    server.close();
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.status, 500);
  });

  it('times out and returns error:timeout', async () => {
    const server = http.createServer(() => { /* never respond */ });
    await new Promise((r) => server.listen(0, '127.0.0.1', r));
    const { port } = server.address();
    const r = await post(`http://127.0.0.1:${port}/x`, {}, { version: '1.0', timeoutMs: 50 });
    server.close();
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'timeout');
  });
});

/* ─── sendFeedback ───────────────────────────────────────────────────── */

describe('sendFeedback', () => {
  it('returns no_endpoint when metadata/env missing', async () => {
    const r = await sendFeedback({ text: 'hi', cwd: cwdMetaDir });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'no_endpoint');
  });

  it('returns empty_text when text is blank', async () => {
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api',
    });
    writeUserCache('octocat');
    const r = await sendFeedback({ text: '   ', cwd: cwdMetaDir });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'empty_text');
  });

  it('returns no_github_login when identity unresolved', async () => {
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api',
    });
    // Ensure no cache + no gh on PATH
    process.env.PATH = tmpDir;
    const r = await sendFeedback({
      text: 'hello',
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, 'nonexistent-cache.json'),
    });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'no_github_login');
  });

  it('sends full payload to /feedback endpoint with X-TKM-Client header', async () => {
    writeUserCache('octocat');

    const received = await new Promise((resolve) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve({
            url: req.url,
            body,
            clientHeader: req.headers['x-tkm-client'],
            tokenHeader: req.headers['x-sk-token'],
          });
        });
      });
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        writeMetadata(cwdMetaDir, {
          version: '9.9.9',
          telemetry_endpoint: `http://127.0.0.1:${port}/api`,
        });
        const r = await sendFeedback({
          text: 'this is great',
          sessionId: 'sess-1',
          cwd: cwdMetaDir,
          cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
        });
        assert.strictEqual(r.ok, true);
      });
    });

    assert.strictEqual(received.url, '/api/feedback');
    assert.strictEqual(received.clientHeader, 'agent-kit/9.9.9');
    assert.strictEqual(received.tokenHeader, undefined);
    const body = JSON.parse(received.body);
    assert.strictEqual(body.github_login, 'octocat');
    assert.strictEqual(body.session_id, 'sess-1');
    assert.strictEqual(body.sk_version, '9.9.9');
    assert.strictEqual(body.text, 'this is great');
    assert.match(body.cwd_hash, /^[0-9a-f]{64}$/);
    assert.match(body.ts, /^\d{4}-\d{2}-\d{2}T/);
  });

  it('truncates text to MAX_FEEDBACK_CHARS before sending', async () => {
    writeUserCache('octocat');

    const received = await new Promise((resolve) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve(JSON.parse(body));
        });
      });
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        writeMetadata(cwdMetaDir, {
          telemetry_endpoint: `http://127.0.0.1:${port}/api`,
        });
        const longText = 'x'.repeat(MAX_FEEDBACK_CHARS + 500);
        const r = await sendFeedback({
          text: longText,
          cwd: cwdMetaDir,
          cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
        });
        assert.strictEqual(r.ok, true);
      });
    });

    assert.strictEqual(received.text.length, MAX_FEEDBACK_CHARS);
  });
});

/* ─── normalizeScore ─────────────────────────────────────────────────── */

describe('normalizeScore', () => {
  it('accepts integers 0..3', () => {
    for (const n of [0, 1, 2, 3]) assert.strictEqual(normalizeScore(n), n);
  });

  it('accepts numeric strings', () => {
    assert.strictEqual(normalizeScore('2'), 2);
    assert.strictEqual(normalizeScore('  3 '), 3);
  });

  it('rejects out-of-range / non-integer / junk', () => {
    for (const bad of [-1, 4, 1.5, NaN, 'two', '', null, undefined, {}]) {
      assert.strictEqual(normalizeScore(bad), null);
    }
  });
});

/* ─── sendRating ─────────────────────────────────────────────────────── */

describe('sendRating', () => {
  it('returns no_endpoint when metadata/env missing', async () => {
    const r = await sendRating({ score: 2, cwd: cwdMetaDir });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'no_endpoint');
  });

  it('returns invalid_score for out-of-range input', async () => {
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api',
    });
    writeUserCache('octocat');
    const r = await sendRating({
      score: 5,
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
    });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'invalid_score');
  });

  it('returns no_github_login when identity unresolved', async () => {
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api',
    });
    process.env.PATH = tmpDir;
    const r = await sendRating({
      score: 2,
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, 'nonexistent-cache.json'),
    });
    assert.strictEqual(r.ok, false);
    assert.strictEqual(r.error, 'no_github_login');
  });

  it('sends full payload to /rating with truncated comment + allowed milestone', async () => {
    writeUserCache('octocat');

    const received = await new Promise((resolve) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve({
            url: req.url,
            body: JSON.parse(body),
            clientHeader: req.headers['x-tkm-client'],
          });
        });
      });
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        writeMetadata(cwdMetaDir, {
          version: '9.9.9',
          telemetry_endpoint: `http://127.0.0.1:${port}/api`,
        });
        const r = await sendRating({
          score: 2,
          comment: 'x'.repeat(MAX_RATING_COMMENT_CHARS + 100),
          milestone: 'takumi',
          sessionId: 'sess-1',
          cwd: cwdMetaDir,
          cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
        });
        assert.strictEqual(r.ok, true);
      });
    });

    assert.strictEqual(received.url, '/api/rating');
    assert.strictEqual(received.clientHeader, 'agent-kit/9.9.9');
    assert.strictEqual(received.body.score, 2);
    assert.strictEqual(received.body.milestone, 'takumi');
    assert.strictEqual(received.body.github_login, 'octocat');
    assert.strictEqual(received.body.session_id, 'sess-1');
    assert.strictEqual(received.body.comment.length, MAX_RATING_COMMENT_CHARS);
  });

  it('sends null milestone when value is not in allowlist', async () => {
    writeUserCache('octocat');

    const received = await new Promise((resolve) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve(JSON.parse(body));
        });
      });
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        writeMetadata(cwdMetaDir, {
          telemetry_endpoint: `http://127.0.0.1:${port}/api`,
        });
        await sendRating({
          score: 1,
          milestone: 'release',
          cwd: cwdMetaDir,
          cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
        });
      });
    });

    assert.strictEqual(received.milestone, null);
  });

  it('sends null comment when only whitespace', async () => {
    writeUserCache('octocat');

    const received = await new Promise((resolve) => {
      const server = http.createServer((req, res) => {
        let body = '';
        req.on('data', (c) => { body += c; });
        req.on('end', () => {
          res.writeHead(204); res.end();
          server.close();
          resolve(JSON.parse(body));
        });
      });
      server.listen(0, '127.0.0.1', async () => {
        const { port } = server.address();
        writeMetadata(cwdMetaDir, {
          telemetry_endpoint: `http://127.0.0.1:${port}/api`,
        });
        await sendRating({
          score: 3,
          comment: '   ',
          cwd: cwdMetaDir,
          cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
        });
      });
    });

    assert.strictEqual(received.comment, null);
  });
});

/* ─── findMetadataJson via CLAUDE_PLUGIN_ROOT ────────────────────────── */

describe('CLAUDE_PLUGIN_ROOT metadata lookup', () => {
  // Plugin mode: Claude Code invokes hooks from a plugin install where cwd has
  // no local .claude/. Without checking CLAUDE_PLUGIN_ROOT, readEndpoint falls
  // through to ~/.claude/metadata.json (usually absent) → no_endpoint.
  it('reads endpoint from $CLAUDE_PLUGIN_ROOT/.claude/metadata.json when cwd has no .claude', () => {
    const cwdNoClaude = path.join(tmpDir, 'user-proj');
    fs.mkdirSync(cwdNoClaude, { recursive: true });

    const pluginRoot = path.join(tmpDir, 'plugin-root');
    fs.mkdirSync(path.join(pluginRoot, '.claude'), { recursive: true });
    fs.writeFileSync(
      path.join(pluginRoot, '.claude', 'metadata.json'),
      JSON.stringify({ telemetry_endpoint: 'https://from-plugin/api' }),
    );
    process.env.CLAUDE_PLUGIN_ROOT = pluginRoot;

    assert.strictEqual(readEndpoint(cwdNoClaude), 'https://from-plugin/api');
  });

  it('prefers project-local cwd metadata over $CLAUDE_PLUGIN_ROOT', () => {
    // A stale CLAUDE_PLUGIN_ROOT in the shell environment (e.g. leftover from a
    // previous plugin install) must not override a freshly `sk init`-ed project
    // whose .claude/metadata.json holds the canonical config for this session.
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-cwd/api' });

    const pluginRoot = path.join(tmpDir, 'plugin-root');
    fs.mkdirSync(path.join(pluginRoot, '.claude'), { recursive: true });
    fs.writeFileSync(
      path.join(pluginRoot, '.claude', 'metadata.json'),
      JSON.stringify({ telemetry_endpoint: 'https://from-plugin/api' }),
    );
    process.env.CLAUDE_PLUGIN_ROOT = pluginRoot;

    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-cwd/api');
  });

  it('falls through to cwd walk when $CLAUDE_PLUGIN_ROOT has no metadata.json', () => {
    // Empty plugin dir — should not short-circuit; cwd lookup should still work.
    const pluginRoot = path.join(tmpDir, 'plugin-root-empty');
    fs.mkdirSync(pluginRoot, { recursive: true });
    process.env.CLAUDE_PLUGIN_ROOT = pluginRoot;

    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-cwd/api' });
    assert.strictEqual(readEndpoint(cwdMetaDir), 'https://from-cwd/api');
  });

});

describe('readMetadata error surfacing', () => {
  it('returns __readError object on malformed JSON instead of null', () => {
    fs.writeFileSync(path.join(cwdMetaDir, '.claude', 'metadata.json'), '{ not valid json');
    const result = client.readMetadata(cwdMetaDir);
    assert.ok(result && typeof result.__readError === 'string', 'expected __readError string');
    assert.match(result.__readError, /metadata\.json/);
  });

  it('readEndpoint returns null (not crash) when metadata is malformed', () => {
    fs.writeFileSync(path.join(cwdMetaDir, '.claude', 'metadata.json'), '{ not valid json');
    assert.strictEqual(readEndpoint(cwdMetaDir), null);
  });

  it('metadataReadError returns the error message for malformed metadata', () => {
    fs.writeFileSync(path.join(cwdMetaDir, '.claude', 'metadata.json'), '{ not valid json');
    const err = client.metadataReadError(cwdMetaDir);
    assert.ok(err && err.includes('metadata.json'));
  });

  it('metadataReadError returns null when metadata is well-formed', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://x/api' });
    assert.strictEqual(client.metadataReadError(cwdMetaDir), null);
  });
});

describe('findMetadataJson priority order', () => {
  it('returns null when no source has metadata.json', () => {
    const emptyCwd = path.join(tmpDir, 'empty-cwd');
    fs.mkdirSync(emptyCwd, { recursive: true });
    assert.strictEqual(client.findMetadataJson(emptyCwd), null);
  });
});

describe('resolveEndpointSource', () => {
  it('returns "env-override" when env is set AND dev gate is on', () => {
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://from-env/api';
    process.env.TKM_TELEMETRY_DEV = '1';
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api' });
    assert.strictEqual(resolveEndpointSource(cwdMetaDir), 'env-override');
  });

  it('returns "metadata" when env leaks but dev gate is NOT on', () => {
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://leaked-env/api';
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api' });
    assert.strictEqual(resolveEndpointSource(cwdMetaDir), 'metadata');
  });

  it('returns "metadata" when only metadata.json has endpoint', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://from-meta/api' });
    assert.strictEqual(resolveEndpointSource(cwdMetaDir), 'metadata');
  });

  it('returns "env-fallback" when metadata has no endpoint but env is set', () => {
    writeMetadata(cwdMetaDir, {});
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://from-env/api';
    assert.strictEqual(resolveEndpointSource(cwdMetaDir), 'env-fallback');
  });

  it('returns "none" when neither env nor metadata has endpoint', () => {
    assert.strictEqual(resolveEndpointSource(cwdMetaDir), 'none');
  });
});

describe('endpoint source logging on failure', () => {
  function captureStderr(fn) {
    const orig = process.stderr.write.bind(process.stderr);
    const chunks = [];
    process.stderr.write = (c) => { chunks.push(String(c)); return true; };
    return Promise.resolve(fn()).finally(() => { process.stderr.write = orig; })
      .then(() => chunks.join(''));
  }

  it('sendRating writes endpoint + source=metadata to stderr on failure', async () => {
    // Unreachable port forces post() to fail.
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api',
    });
    writeUserCache('octocat');

    const stderr = await captureStderr(() => sendRating({
      score: 3,
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
    }));

    assert.ok(
      stderr.includes('endpoint=http://127.0.0.1:1/api'),
      `expected endpoint line, got: ${stderr}`,
    );
    assert.ok(
      stderr.includes('source=metadata'),
      `expected source=metadata, got: ${stderr}`,
    );
  });

  it('sendFeedback writes source=env-override when dev gate is on and env wins', async () => {
    process.env.TKM_TELEMETRY_ENDPOINT = 'http://127.0.0.1:1/api';
    process.env.TKM_TELEMETRY_DEV = '1';
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'https://prod.example.com/api',
    });
    writeUserCache('octocat');

    const stderr = await captureStderr(() => sendFeedback({
      text: 'hi',
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
    }));

    assert.ok(stderr.includes('source=env-override'), `expected source=env-override, got: ${stderr}`);
    assert.ok(
      !stderr.includes('prod.example.com'),
      `dev gate on — metadata URL should be shadowed, got: ${stderr}`,
    );
  });

  it('sendFeedback uses metadata (and reports source=metadata) when env leaks WITHOUT dev gate', async () => {
    // This is the "end-user machine with leaked TKM_TELEMETRY_ENDPOINT" scenario.
    process.env.TKM_TELEMETRY_ENDPOINT = 'http://leaked-local:8888/api';
    writeMetadata(cwdMetaDir, {
      telemetry_endpoint: 'http://127.0.0.1:1/api', // unreachable → forces failure
    });
    writeUserCache('octocat');

    const stderr = await captureStderr(() => sendFeedback({
      text: 'hi',
      cwd: cwdMetaDir,
      cacheFile: path.join(tmpDir, '.claude', 'sk-user.json'),
    }));

    assert.ok(
      stderr.includes('source=metadata'),
      `env must be ignored without dev gate, got: ${stderr}`,
    );
    assert.ok(
      !stderr.includes('leaked-local'),
      `leaked env URL should never appear, got: ${stderr}`,
    );
  });
});

describe('baked defaults (release-time injection)', () => {
  const SOURCE_PATH = require.resolve('../lib/telemetry-client.cjs');

  function loadBakedModule({ endpoint }) {
    const src = fs.readFileSync(SOURCE_PATH, 'utf8');
    let patched = src;
    if (endpoint !== undefined) {
      patched = patched.replace(
        /^const BAKED_ENDPOINT = '__TKM_DEFAULT_ENDPOINT__';$/m,
        `const BAKED_ENDPOINT = ${JSON.stringify(endpoint)};`,
      );
    }
    // Stash next to the real file so relative require('./user-identity.cjs') resolves.
    const stashed = path.join(
      path.dirname(SOURCE_PATH),
      `.__test_baked_${process.pid}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}.cjs`,
    );
    fs.writeFileSync(stashed, patched);
    // Force fresh evaluation so stale module constants don't leak across tests.
    delete require.cache[stashed];
    try {
      return { mod: require(stashed), cleanup: () => fs.unlinkSync(stashed) };
    } catch (e) {
      try { fs.unlinkSync(stashed); } catch (_) { /* ignore */ }
      throw e;
    }
  }

  it('bakedEndpoint returns null in source (placeholder unsubstituted)', () => {
    assert.equal(client.bakedEndpoint(), null);
  });

  it('readEndpoint falls back to baked default when no metadata/env', () => {
    const { mod, cleanup } = loadBakedModule({
      endpoint: 'https://baked.example.com',
    });
    try {
      assert.equal(mod.bakedEndpoint(), 'https://baked.example.com');
      assert.equal(mod.readEndpoint(cwdMetaDir), 'https://baked.example.com');
      assert.equal(mod.resolveEndpointSource(cwdMetaDir), 'baked-default');
    } finally {
      cleanup();
    }
  });

  it('metadata still wins over baked default', () => {
    writeMetadata(cwdMetaDir, { telemetry_endpoint: 'https://meta.example' });
    const { mod, cleanup } = loadBakedModule({ endpoint: 'https://baked.example.com' });
    try {
      assert.equal(mod.readEndpoint(cwdMetaDir), 'https://meta.example');
      assert.equal(mod.resolveEndpointSource(cwdMetaDir), 'metadata');
    } finally {
      cleanup();
    }
  });

  it('env fallback wins over baked when metadata absent (no dev gate)', () => {
    process.env.TKM_TELEMETRY_ENDPOINT = 'https://env.example';
    const { mod, cleanup } = loadBakedModule({ endpoint: 'https://baked.example.com' });
    try {
      assert.equal(mod.readEndpoint(cwdMetaDir), 'https://env.example');
      assert.equal(mod.resolveEndpointSource(cwdMetaDir), 'env-fallback');
    } finally {
      cleanup();
    }
  });

  it('trailing slashes are stripped on baked endpoint', () => {
    const { mod, cleanup } = loadBakedModule({ endpoint: 'https://baked.example.com///' });
    try {
      assert.equal(mod.readEndpoint(cwdMetaDir), 'https://baked.example.com');
    } finally {
      cleanup();
    }
  });
});
