#!/usr/bin/env node
/**
 * Unit tests for claude/hooks/telemetry.cjs — buffer, extractors, handlers.
 * Does not exercise process.exit / stdin; handlers are called directly.
 */

const { afterEach, beforeEach, describe, it } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

// IMPORTANT: require the module fresh each test so BUFFER_DIR reflects the
// stubbed HOME. The module caches BUFFER_DIR at require-time so we have to
// set HOME before the first require and delete the cache to rebind.
let telemetry;
let tmpHome;

function freshRequire() {
  const p = require.resolve('../telemetry.cjs');
  delete require.cache[p];
  // Also drop user-identity + telemetry-client + rate-throttle caches so
  // module-level paths rebind to the new HOME.
  delete require.cache[require.resolve('../lib/user-identity.cjs')];
  delete require.cache[require.resolve('../lib/telemetry-client.cjs')];
  delete require.cache[require.resolve('../lib/rate-throttle.cjs')];
  telemetry = require('../telemetry.cjs');
}

beforeEach(() => {
  tmpHome = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-tel-hook-'));
  process.env.HOME = tmpHome;
  freshRequire();
});

afterEach(() => {
  try { fs.rmSync(tmpHome, { recursive: true, force: true }); } catch { /* ignore */ }
});

/* ─── extractSkCommand ───────────────────────────────────────────────── */

describe('extractSkCommand', () => {
  it('returns the command for /tkm: prefix', () => {
    assert.strictEqual(telemetry.extractSkCommand('/tkm:takumi do stuff'), '/tkm:takumi');
  });

  it('returns null for non-/tkm: prompts (no prompt text leakage)', () => {
    assert.strictEqual(telemetry.extractSkCommand('hello world'), null);
    assert.strictEqual(telemetry.extractSkCommand('/help'), null);
  });

  it('returns null for malformed /tkm: commands', () => {
    assert.strictEqual(telemetry.extractSkCommand('/tkm:'), null);
    assert.strictEqual(telemetry.extractSkCommand('/tkm:BAD NAME'), '/tkm:BAD');
    // actually BAD is alphanumeric — allowed. test injection chars:
    assert.strictEqual(telemetry.extractSkCommand('/tkm:takumi;rm'), null);
  });

  it('returns null for non-string inputs', () => {
    assert.strictEqual(telemetry.extractSkCommand(undefined), null);
    assert.strictEqual(telemetry.extractSkCommand(42), null);
  });
});

/* ─── classifyTool ───────────────────────────────────────────────────── */

describe('classifyTool', () => {
  it('maps Task → agent with subagent_type', () => {
    assert.deepStrictEqual(
      telemetry.classifyTool('Task', { subagent_type: 'planner' }),
      { event_type: 'agent', event_name: 'planner' },
    );
  });

  it('Task without subagent_type → agent:unknown', () => {
    assert.deepStrictEqual(
      telemetry.classifyTool('Task', {}),
      { event_type: 'agent', event_name: 'unknown' },
    );
  });

  it('maps Skill → skill event', () => {
    assert.deepStrictEqual(
      telemetry.classifyTool('Skill', { skill: 'debug' }),
      { event_type: 'skill', event_name: 'debug' },
    );
  });

  it('other tools → tool event', () => {
    assert.deepStrictEqual(
      telemetry.classifyTool('Read', {}),
      { event_type: 'tool', event_name: 'Read' },
    );
  });

  it('returns null for missing tool_name', () => {
    assert.strictEqual(telemetry.classifyTool(undefined, {}), null);
    assert.strictEqual(telemetry.classifyTool('', {}), null);
  });
});

/* ─── appendEvent / readBufferEvents / deleteBuffer ─────────────────── */

describe('buffer helpers', () => {
  it('appends events and reads them back', () => {
    telemetry.appendEvent('sess-1', { event_type: 'tool', event_name: 'Read', ts: 't1' });
    telemetry.appendEvent('sess-1', { event_type: 'agent', event_name: 'planner', ts: 't2' });
    const events = telemetry.readBufferEvents('sess-1');
    assert.strictEqual(events.length, 2);
    assert.strictEqual(events[0].event_name, 'Read');
    assert.strictEqual(events[1].event_name, 'planner');
  });

  it('readBufferEvents returns [] when file missing', () => {
    assert.deepStrictEqual(telemetry.readBufferEvents('nope'), []);
  });

  it('deleteBuffer removes the file', () => {
    telemetry.appendEvent('sess-2', { event_type: 'tool', event_name: 'Grep', ts: 't' });
    assert.strictEqual(fs.existsSync(telemetry.bufferFileFor('sess-2')), true);
    telemetry.deleteBuffer('sess-2');
    assert.strictEqual(fs.existsSync(telemetry.bufferFileFor('sess-2')), false);
  });

  it('appendEvent silently no-ops on missing sessionId', () => {
    assert.doesNotThrow(() => telemetry.appendEvent(null, { x: 1 }));
    assert.doesNotThrow(() => telemetry.appendEvent('', { x: 1 }));
  });

  it('readBufferEvents tolerates garbage lines', () => {
    fs.mkdirSync(telemetry.BUFFER_DIR, { recursive: true });
    fs.writeFileSync(
      telemetry.bufferFileFor('mixed'),
      '{"event_type":"tool","event_name":"ok"}\nnot-json\n{"event_type":"tool","event_name":"ok2"}\n',
    );
    const events = telemetry.readBufferEvents('mixed');
    assert.strictEqual(events.length, 2);
    assert.strictEqual(events[1].event_name, 'ok2');
  });
});

/* ─── capEvents ──────────────────────────────────────────────────────── */

describe('capEvents', () => {
  it('passes through under cap', () => {
    const events = [{ event_type: 'tool', event_name: 'Read', ts: 't' }];
    assert.deepStrictEqual(telemetry.capEvents(events), events);
  });

  it('drops oldest events until under MAX_PAYLOAD_BYTES', () => {
    // Build ~2KB events until we exceed 10KB.
    const big = 'x'.repeat(2000);
    const events = Array.from({ length: 20 }, (_, i) => ({
      event_type: 'tool',
      event_name: `evt-${i}`,
      ts: 't',
      payload: { blob: big },
    }));
    const capped = telemetry.capEvents(events);
    assert.ok(JSON.stringify(capped).length <= telemetry.MAX_PAYLOAD_BYTES);
    // newest events preserved
    assert.strictEqual(capped[capped.length - 1].event_name, 'evt-19');
  });
});

/* ─── handleUserPromptSubmit ─────────────────────────────────────────── */

describe('handleUserPromptSubmit', () => {
  it('appends command event for /tkm: prompt', () => {
    telemetry.handleUserPromptSubmit({ session_id: 's', prompt: '/tkm:takumi do x' });
    const events = telemetry.readBufferEvents('s');
    assert.strictEqual(events.length, 1);
    assert.strictEqual(events[0].event_type, 'command');
    assert.strictEqual(events[0].event_name, '/tkm:takumi');
  });

  it('ignores non-/sk prompts (never captures prompt text)', () => {
    telemetry.handleUserPromptSubmit({ session_id: 's', prompt: 'please help me' });
    assert.strictEqual(telemetry.readBufferEvents('s').length, 0);
  });
});

/* ─── handlePostToolUse ──────────────────────────────────────────────── */

describe('handlePostToolUse', () => {
  it('captures agent event from Task tool', () => {
    telemetry.handlePostToolUse({
      session_id: 's',
      tool_name: 'Task',
      tool_input: { subagent_type: 'planner' },
    });
    const events = telemetry.readBufferEvents('s');
    assert.strictEqual(events[0].event_type, 'agent');
    assert.strictEqual(events[0].event_name, 'planner');
  });

  it('captures tool event from ordinary tools', () => {
    telemetry.handlePostToolUse({ session_id: 's', tool_name: 'Grep' });
    assert.strictEqual(telemetry.readBufferEvents('s')[0].event_type, 'tool');
  });

  it('ignores events without session_id (no orphan writes)', () => {
    telemetry.handlePostToolUse({ tool_name: 'Read' });
    // No buffer dir writes since sessionId is missing.
    const existed = fs.existsSync(path.join(telemetry.BUFFER_DIR, '.jsonl'));
    assert.strictEqual(existed, false);
  });
});

/* ─── handleSessionStart (orphan cleanup) ────────────────────────────── */

describe('handleSessionStart', () => {
  it('deletes orphan buffers older than 24h', () => {
    fs.mkdirSync(telemetry.BUFFER_DIR, { recursive: true });
    const old = path.join(telemetry.BUFFER_DIR, 'old.jsonl');
    const fresh = path.join(telemetry.BUFFER_DIR, 'fresh.jsonl');
    fs.writeFileSync(old, '{}\n');
    fs.writeFileSync(fresh, '{}\n');
    // Force `old` mtime to 25h ago.
    const oldTime = (Date.now() - 25 * 60 * 60 * 1000) / 1000;
    fs.utimesSync(old, oldTime, oldTime);

    telemetry.handleSessionStart();

    assert.strictEqual(fs.existsSync(old), false);
    assert.strictEqual(fs.existsSync(fresh), true);
  });

  it('no-ops when buffer dir missing', () => {
    assert.doesNotThrow(() => telemetry.handleSessionStart());
  });
});

/* ─── handleStop (buffer delete, happy path POST) ────────────────────── */

describe('handleStop', () => {
  it('always deletes buffer even when endpoint missing', async () => {
    telemetry.appendEvent('s', { event_type: 'tool', event_name: 'Read', ts: 't' });
    await telemetry.handleStop({ session_id: 's', usage: {} });
    assert.strictEqual(fs.existsSync(telemetry.bufferFileFor('s')), false);
  });

  it('skips POST when session_id missing', async () => {
    await assert.doesNotReject(telemetry.handleStop({ usage: {} }));
  });

  it('reads milestone from session state and includes it in the payload', async () => {
    const http = require('http');

    const claudeDir = path.join(tmpHome, '.claude');
    fs.mkdirSync(claudeDir, { recursive: true });
    fs.writeFileSync(
      path.join(claudeDir, 'sk-user.json'),
      JSON.stringify({ githubLogin: 'octocat', resolvedAt: Date.now(), source: 'manual' }),
    );

    // Seed session state with milestone_completed = 'ship' (simulates /tkm:ship marker).
    const { getSessionTempPath, writeSessionState } = require('../lib/tkm-config-utils.cjs');
    writeSessionState('sess-ms', { milestone_completed: 'ship' });

    const cwdMetaDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-tel-cwd-'));
    fs.mkdirSync(path.join(cwdMetaDir, '.claude'), { recursive: true });
    const originalCwd = process.cwd();
    process.chdir(cwdMetaDir);

    try {
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
          fs.writeFileSync(
            path.join(cwdMetaDir, '.claude', 'metadata.json'),
            JSON.stringify({
              version: '1.2.3',
              telemetry_endpoint: `http://127.0.0.1:${port}/api`,
            }),
          );
          await telemetry.handleStop({ session_id: 'sess-ms', usage: {} });
        });
      });

      assert.strictEqual(received.session.milestone_completed, 'ship');
    } finally {
      process.chdir(originalCwd);
      fs.rmSync(cwdMetaDir, { recursive: true, force: true });
      try { fs.unlinkSync(getSessionTempPath('sess-ms')); } catch { /* ignore */ }
    }
  });

  it('POSTs full payload to /telemetry and deletes buffer on happy path', async () => {
    const http = require('http');

    // Seed user-identity cache inside the stubbed HOME.
    const claudeDir = path.join(tmpHome, '.claude');
    fs.mkdirSync(claudeDir, { recursive: true });
    fs.writeFileSync(
      path.join(claudeDir, 'sk-user.json'),
      JSON.stringify({ githubLogin: 'octocat', resolvedAt: Date.now(), source: 'manual' }),
    );

    // Local metadata.json with endpoint + token in the process cwd.
    const cwdMetaDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sk-tel-cwd-'));
    fs.mkdirSync(path.join(cwdMetaDir, '.claude'), { recursive: true });

    const originalCwd = process.cwd();
    process.chdir(cwdMetaDir);

    try {
      telemetry.appendEvent('sess-happy', { event_type: 'tool', event_name: 'Read', ts: 't1' });
      telemetry.appendEvent('sess-happy', { event_type: 'agent', event_name: 'planner', ts: 't2' });

      const received = await new Promise((resolve) => {
        const server = http.createServer((req, res) => {
          let body = '';
          req.on('data', (c) => { body += c; });
          req.on('end', () => {
            res.writeHead(204); res.end();
            server.close();
            resolve({
              url: req.url,
              clientHeader: req.headers['x-tkm-client'],
              tokenHeader: req.headers['x-sk-token'],
              body: JSON.parse(body),
            });
          });
        });
        server.listen(0, '127.0.0.1', async () => {
          const { port } = server.address();
          fs.writeFileSync(
            path.join(cwdMetaDir, '.claude', 'metadata.json'),
            JSON.stringify({
              version: '1.2.3',
              telemetry_endpoint: `http://127.0.0.1:${port}/api`,
            }),
          );
          await telemetry.handleStop({
            session_id: 'sess-happy',
            usage: { input_tokens: 100, output_tokens: 50 },
            milestone: 'takumi',
          });
        });
      });

      assert.strictEqual(received.url, '/api/telemetry');
      assert.strictEqual(received.clientHeader, 'agent-kit/1.2.3');
      assert.strictEqual(received.tokenHeader, undefined);
      assert.strictEqual(received.body.user, 'octocat');
      assert.strictEqual(received.body.session.id, 'sess-happy');
      assert.strictEqual(received.body.session.sk_version, '1.2.3');
      assert.strictEqual(received.body.session.input_tokens, 100);
      assert.strictEqual(received.body.session.milestone_completed, 'takumi');
      assert.strictEqual(received.body.events.length, 2);
      assert.strictEqual(received.body.events[0].event_name, 'Read');
      // Buffer cleared after flush.
      assert.strictEqual(fs.existsSync(telemetry.bufferFileFor('sess-happy')), false);
    } finally {
      process.chdir(originalCwd);
      fs.rmSync(cwdMetaDir, { recursive: true, force: true });
    }
  });
});

/* ─── rating prompt sampling ────────────────────────────────────────── */

describe('shouldSampleRating', () => {
  it('honors TKM_RATING_FORCE=1', () => {
    assert.strictEqual(telemetry.shouldSampleRating({ forceEnv: '1', rng: () => 1 }), true);
    assert.strictEqual(telemetry.shouldSampleRating({ forceEnv: 'true', rng: () => 1 }), true);
  });

  it('returns true when rng below RATING_SAMPLE_RATE', () => {
    assert.strictEqual(
      telemetry.shouldSampleRating({ forceEnv: undefined, rng: () => telemetry.RATING_SAMPLE_RATE - 0.001 }),
      true,
    );
  });

  it('returns false when rng meets or exceeds threshold', () => {
    assert.strictEqual(
      telemetry.shouldSampleRating({ forceEnv: undefined, rng: () => telemetry.RATING_SAMPLE_RATE }),
      false,
    );
    assert.strictEqual(
      telemetry.shouldSampleRating({ forceEnv: undefined, rng: () => 0.99 }),
      false,
    );
  });
});

describe('readMilestone', () => {
  it('returns null when session state missing', () => {
    assert.strictEqual(telemetry.readMilestone('no-such-session'), null);
  });

  it('returns the milestone when set', () => {
    const { writeSessionState, getSessionTempPath } = require('../lib/tkm-config-utils.cjs');
    writeSessionState('ms-sess', { milestone_completed: 'takumi' });
    try {
      assert.strictEqual(telemetry.readMilestone('ms-sess'), 'takumi');
    } finally {
      try { fs.unlinkSync(getSessionTempPath('ms-sess')); } catch { /* ignore */ }
    }
  });

  it('returns null for unknown milestone values', () => {
    const { writeSessionState, getSessionTempPath } = require('../lib/tkm-config-utils.cjs');
    writeSessionState('bad-ms', { milestone_completed: 'release' });
    try {
      assert.strictEqual(telemetry.readMilestone('bad-ms'), null);
    } finally {
      try { fs.unlinkSync(getSessionTempPath('bad-ms')); } catch { /* ignore */ }
    }
  });
});

describe('maybeEmitRatingPrompt', () => {
  let originalWrite;
  let captured;

  beforeEach(() => {
    captured = [];
    originalWrite = process.stdout.write.bind(process.stdout);
    process.stdout.write = (chunk) => {
      captured.push(String(chunk));
      return true;
    };
  });

  afterEach(() => {
    process.stdout.write = originalWrite;
  });

  function seedMilestone(sid, kind) {
    const { writeSessionState } = require('../lib/tkm-config-utils.cjs');
    writeSessionState(sid, { milestone_completed: kind });
  }

  function cleanupSession(sid) {
    const { getSessionTempPath } = require('../lib/tkm-config-utils.cjs');
    try { fs.unlinkSync(getSessionTempPath(sid)); } catch { /* ignore */ }
  }

  it('skips without githubLogin', () => {
    const stateFile = path.join(tmpHome, '.claude', 'sk-rate-state.json');
    const result = telemetry.maybeEmitRatingPrompt({ sessionId: 's', githubLogin: null, stateFile });
    assert.strictEqual(result.emitted, false);
    assert.strictEqual(result.reason, 'missing_identity');
  });

  it('skips when no milestone set', () => {
    const stateFile = path.join(tmpHome, '.claude', 'sk-rate-state.json');
    const result = telemetry.maybeEmitRatingPrompt({
      sessionId: 'no-ms', githubLogin: 'octocat', stateFile, rng: () => 0,
    });
    assert.strictEqual(result.emitted, false);
    assert.strictEqual(result.reason, 'no_milestone');
  });

  it('emits additionalContext + persists throttle when sampled and fresh', () => {
    seedMilestone('ms-fresh', 'takumi');
    const stateFile = path.join(tmpHome, '.claude', 'sk-rate-state.json');
    try {
      const result = telemetry.maybeEmitRatingPrompt({
        sessionId: 'ms-fresh',
        githubLogin: 'octocat',
        stateFile,
        rng: () => 0,
        now: 10_000,
      });
      assert.strictEqual(result.emitted, true);
      assert.strictEqual(result.milestone, 'takumi');
      assert.strictEqual(captured.length, 1);
      const parsed = JSON.parse(captured[0]);
      assert.ok(parsed.additionalContext.includes('/tkm:rate'));
      assert.ok(parsed.additionalContext.includes('takumi'));
      // Throttle persisted.
      const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      assert.strictEqual(state.octocat, 10_000);
    } finally {
      cleanupSession('ms-fresh');
    }
  });

  it('stays silent when user prompted inside the 24h window', () => {
    seedMilestone('ms-throttled', 'ship');
    const stateFile = path.join(tmpHome, '.claude', 'sk-rate-state.json');
    fs.mkdirSync(path.dirname(stateFile), { recursive: true });
    fs.writeFileSync(stateFile, JSON.stringify({ octocat: 100 }));
    try {
      const result = telemetry.maybeEmitRatingPrompt({
        sessionId: 'ms-throttled',
        githubLogin: 'octocat',
        stateFile,
        rng: () => 0, // would sample if not throttled
        now: 1_000, // only 900ms later
      });
      assert.strictEqual(result.emitted, false);
      assert.strictEqual(result.reason, 'throttled');
      assert.strictEqual(captured.length, 0);
    } finally {
      cleanupSession('ms-throttled');
    }
  });

  it('respects sampling odds when not throttled', () => {
    seedMilestone('ms-unlucky', 'plan');
    const stateFile = path.join(tmpHome, '.claude', 'sk-rate-state.json');
    try {
      const result = telemetry.maybeEmitRatingPrompt({
        sessionId: 'ms-unlucky',
        githubLogin: 'octocat',
        stateFile,
        rng: () => 0.99, // miss
        now: 10_000,
      });
      assert.strictEqual(result.emitted, false);
      assert.strictEqual(result.reason, 'not_sampled');
      assert.strictEqual(captured.length, 0);
      assert.strictEqual(fs.existsSync(stateFile), false);
    } finally {
      cleanupSession('ms-unlucky');
    }
  });
});
