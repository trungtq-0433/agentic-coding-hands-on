import { test } from 'node:test';
import assert from 'node:assert';
import { readFileSync } from 'node:fs';
import { meta } from '../../propose-improvements-workflow.js';

// The workflow runtime only tolerates a single top-level `export` (the `meta` block),
// so the orchestration helpers are plain (un-exported) declarations in propose-improvements-workflow.js.
// To unit-test them without re-introducing exports that break the loader, load the
// same source and re-export the helpers through an in-memory module — keeping
// propose-improvements-workflow.js the single source of truth.
const src = readFileSync(new URL('../../propose-improvements-workflow.js', import.meta.url), 'utf8');
const shim =
  src +
  '\nexport { parseProposalArgs, activeTracks, BUSINESS_DISCOVERY, TECHNICAL_DISCOVERY, BUSINESS_IMPROVEMENT, TECHNICAL_IMPROVEMENT };';
const {
  parseProposalArgs,
  activeTracks,
  BUSINESS_DISCOVERY,
  TECHNICAL_DISCOVERY,
  BUSINESS_IMPROVEMENT,
  TECHNICAL_IMPROVEMENT,
} = await import('data:text/javascript,' + encodeURIComponent(shim));

test('meta registers as /tkm:propose-improvements-workflow', () => {
  assert.strictEqual(meta.name, 'tkm:propose-improvements-workflow');
  assert.ok(Array.isArray(meta.phases) && meta.phases.length === 10);
});

test('item enumerations mirror the skill counts', () => {
  assert.strictEqual(BUSINESS_DISCOVERY.length, 9);
  assert.strictEqual(TECHNICAL_DISCOVERY.length, 8);
  assert.strictEqual(BUSINESS_IMPROVEMENT.length, 11);
  assert.strictEqual(TECHNICAL_IMPROVEMENT.length, 14);
});

test('bare invocation → both tracks, no flags', () => {
  const f = parseProposalArgs('');
  assert.deepStrictEqual(f.errors, []);
  assert.strictEqual(f.track, 'both');
  assert.strictEqual(f.force, false);
  assert.strictEqual(f.level, 'medium');
  assert.strictEqual(f.high, false);
  assert.strictEqual(f.specFolder, null);
  assert.strictEqual(f.focus, '');
});

test('prompt (focus) preserved, flag order independent', () => {
  const a = parseProposalArgs('--force --technical-only focus on observability');
  const b = parseProposalArgs('focus on observability --force --technical-only');
  assert.strictEqual(a.focus, 'focus on observability');
  assert.strictEqual(b.focus, 'focus on observability');
  assert.strictEqual(a.force, true);
  assert.strictEqual(a.track, 'technical');
  assert.deepStrictEqual(a, b);
});

test('--level high + --spec-folder parse and strip', () => {
  const f = parseProposalArgs('--level high --spec-folder docs/specs prioritize auth');
  assert.strictEqual(f.level, 'high');
  assert.strictEqual(f.high, true);
  assert.strictEqual(f.specFolder, 'docs/specs');
  assert.strictEqual(f.focus, 'prioritize auth');
  assert.deepStrictEqual(f.errors, []);
});

test('--spec-folder without arg → BLOCKED', () => {
  const f = parseProposalArgs('--spec-folder');
  assert.ok(f.errors.some((e) => e.includes('--spec-folder requires a path')));
});

test('mutually exclusive --technical-only + --business-only → BLOCKED', () => {
  const f = parseProposalArgs('--technical-only --business-only');
  assert.ok(f.errors.some((e) => e.includes('mutually exclusive')));
});

test('--debug is a deprecated no-op → recognized, stripped, warns (not prompt text), no error', () => {
  const f = parseProposalArgs('--debug use-context');
  assert.deepStrictEqual(f.errors, []);
  assert.strictEqual(f.focus, 'use-context'); // --debug stripped, not folded into focus
  assert.ok(f.warnings.some((w) => w.includes('--debug is no longer supported')));
});

test('--high is a deprecated alias → maps to --level max + high=true, warns, no error', () => {
  const f = parseProposalArgs('--high prioritize auth');
  assert.deepStrictEqual(f.errors, []);
  assert.strictEqual(f.level, 'max');
  assert.strictEqual(f.high, true);
  assert.strictEqual(f.focus, 'prioritize auth'); // --high stripped, not folded into focus
  assert.ok(f.warnings.some((w) => w.includes('--high is deprecated')));
});

test('activeTracks resolves by flag + isSDD', () => {
  assert.deepStrictEqual(activeTracks({ track: 'technical' }, true), ['technical']);
  assert.deepStrictEqual(activeTracks({ track: 'technical' }, false), ['technical']);
  assert.deepStrictEqual(activeTracks({ track: 'business' }, true), ['business']);
  assert.deepStrictEqual(activeTracks({ track: 'business' }, false), []); // → caller BLOCKs
  assert.deepStrictEqual(activeTracks({ track: 'both' }, true), ['technical', 'business']);
  assert.deepStrictEqual(activeTracks({ track: 'both' }, false), ['technical']);
});

// ───────────────────────────────────────────────────────────────────────────
// MCP/KB knowledge-source flags (--mcp / --kb)
// ───────────────────────────────────────────────────────────────────────────

// Exact missing-value BLOCKED strings — the canonical contract flags.md must mirror.
const MCP_MISSING_ARG = 'BLOCKED — --mcp requires a server argument';
const KB_MISSING_ARG = 'BLOCKED — --kb requires a path argument';

test('T1: --mcp / --kb parse values and strip them from focus', () => {
  const f = parseProposalArgs('--mcp acme-server --kb docs/kb prioritize auth');
  assert.strictEqual(f.mcpServer, 'acme-server');
  assert.strictEqual(f.kbPath, 'docs/kb');
  assert.strictEqual(f.focus, 'prioritize auth');
  assert.deepStrictEqual(f.errors, []);
});

test('T2: --mcp without arg → exact BLOCKED string', () => {
  const f = parseProposalArgs('--mcp');
  assert.ok(f.errors.includes(MCP_MISSING_ARG), `errors=${JSON.stringify(f.errors)}`);
  // A trailing flag is NOT consumed as the value.
  const g = parseProposalArgs('--mcp --force');
  assert.ok(g.errors.includes(MCP_MISSING_ARG));
  assert.strictEqual(g.mcpServer, null);
  assert.strictEqual(g.force, true);
});

test('T3: --kb without arg → exact BLOCKED string', () => {
  const f = parseProposalArgs('--kb');
  assert.ok(f.errors.includes(KB_MISSING_ARG), `errors=${JSON.stringify(f.errors)}`);
  const g = parseProposalArgs('--kb --technical-only');
  assert.ok(g.errors.includes(KB_MISSING_ARG));
  assert.strictEqual(g.kbPath, null);
  assert.strictEqual(g.track, 'technical');
});

test('T4: --mcp/--kb compose + flag order independent', () => {
  const a = parseProposalArgs('--mcp srv --force --kb https://kb.example.com/x --technical-only --level high focus here');
  const b = parseProposalArgs('focus here --level high --technical-only --kb https://kb.example.com/x --force --mcp srv');
  assert.strictEqual(a.mcpServer, 'srv');
  assert.strictEqual(a.kbPath, 'https://kb.example.com/x');
  assert.strictEqual(a.force, true);
  assert.strictEqual(a.level, 'high');
  assert.strictEqual(a.high, true);
  assert.strictEqual(a.track, 'technical');
  assert.strictEqual(a.focus, 'focus here');
  assert.deepStrictEqual(a.errors, []);
  assert.deepStrictEqual(a, b);
});

test('T5: no-flag parse is byte-identical to the baseline object', () => {
  const baseline = {
    focus: '',
    force: false,
    track: 'both',
    level: 'medium',
    high: false,
    specFolder: null,
    mcpServer: null,
    mcpArgs: {},
    kbPath: null,
    errors: [],
    warnings: [],
  };
  assert.deepStrictEqual(parseProposalArgs(''), baseline);
  assert.deepStrictEqual(parseProposalArgs('just a focus area'), { ...baseline, focus: 'just a focus area' });
});

// ───────────────────────────────────────────────────────────────────────────
// --level (processing depth; the source-code security audit runs at high|max)
// ───────────────────────────────────────────────────────────────────────────

const LEVEL_BAD_ARG = 'BLOCKED — --level requires one of low|medium|high|max';

test('--level high|max derive high=true; low|medium derive high=false', () => {
  assert.strictEqual(parseProposalArgs('--level high').high, true);
  assert.strictEqual(parseProposalArgs('--level max').high, true);
  assert.strictEqual(parseProposalArgs('--level low').high, false);
  assert.strictEqual(parseProposalArgs('--level medium').high, false);
  assert.strictEqual(parseProposalArgs('--level max').level, 'max');
});

test('--level invalid value or missing arg → exact BLOCKED string', () => {
  const bad = parseProposalArgs('--level hgih');
  assert.ok(bad.errors.includes(LEVEL_BAD_ARG), `errors=${JSON.stringify(bad.errors)}`);
  const missing = parseProposalArgs('--level');
  assert.ok(missing.errors.includes(LEVEL_BAD_ARG));
  // A trailing flag is NOT consumed as the value.
  const trailing = parseProposalArgs('--level --force');
  assert.ok(trailing.errors.includes(LEVEL_BAD_ARG));
  assert.strictEqual(trailing.level, 'medium');
  assert.strictEqual(trailing.force, true);
});

// ───────────────────────────────────────────────────────────────────────────
// --mcp-arg — per-call MCP tool parameters (repeatable key=value)
// ───────────────────────────────────────────────────────────────────────────

const MCP_ARG_MISSING = 'BLOCKED — --mcp-arg requires a key=value argument';
const MCP_ARG_NO_SERVER = 'BLOCKED — --mcp-arg requires --mcp';

test('T13: --mcp-arg parses key=value, strips tokens, requires --mcp', () => {
  const f = parseProposalArgs('--mcp clio --mcp-arg project_id=42 prioritize auth');
  assert.strictEqual(f.mcpServer, 'clio');
  assert.deepStrictEqual(f.mcpArgs, { project_id: '42' });
  assert.strictEqual(f.focus, 'prioritize auth');
  assert.deepStrictEqual(f.errors, []);
});

test('T14: repeatable --mcp-arg accumulates; value may contain "="', () => {
  const f = parseProposalArgs('--mcp acme --mcp-arg region=us --mcp-arg token=a=b');
  assert.deepStrictEqual(f.mcpArgs, { region: 'us', token: 'a=b' });
  assert.deepStrictEqual(f.errors, []);
});

test('T15: repeated key → last write wins', () => {
  const f = parseProposalArgs('--mcp acme --mcp-arg project_id=1 --mcp-arg project_id=2');
  assert.deepStrictEqual(f.mcpArgs, { project_id: '2' });
});

test('T16: --mcp-arg without --mcp → BLOCKED (order-independent)', () => {
  const f = parseProposalArgs('--mcp-arg project_id=42');
  assert.ok(f.errors.includes(MCP_ARG_NO_SERVER), `errors=${JSON.stringify(f.errors)}`);
  // Order-independent: arg before server still parses the server, no error.
  const g = parseProposalArgs('--mcp-arg project_id=42 --mcp clio');
  assert.strictEqual(g.mcpServer, 'clio');
  assert.deepStrictEqual(g.mcpArgs, { project_id: '42' });
  assert.deepStrictEqual(g.errors, []);
});

test('T17: malformed --mcp-arg (no value / no "=") → BLOCKED, token not consumed as value', () => {
  assert.ok(parseProposalArgs('--mcp clio --mcp-arg').errors.includes(MCP_ARG_MISSING));
  assert.ok(parseProposalArgs('--mcp clio --mcp-arg project_id').errors.includes(MCP_ARG_MISSING));
  const f = parseProposalArgs('--mcp clio --mcp-arg --force');
  assert.ok(f.errors.includes(MCP_ARG_MISSING));
  assert.strictEqual(f.force, true); // --force not swallowed as the value
});

test('T18: flags.md documents the exact --mcp-arg BLOCKED strings (parity)', () => {
  const flagsMd = readFileSync(
    new URL('../../../skills/propose-improvements/references/flags.md', import.meta.url),
    'utf8'
  );
  assert.ok(flagsMd.includes(MCP_ARG_MISSING), 'flags.md missing --mcp-arg key=value BLOCKED string');
  assert.ok(flagsMd.includes(MCP_ARG_NO_SERVER), 'flags.md missing --mcp-arg requires --mcp BLOCKED string');
});

test('T12: flags.md documents the exact JS BLOCKED error strings (parity)', () => {
  const flagsMd = readFileSync(
    new URL('../../../skills/propose-improvements/references/flags.md', import.meta.url),
    'utf8'
  );
  assert.ok(flagsMd.includes(MCP_MISSING_ARG), 'flags.md missing --mcp BLOCKED string');
  assert.ok(flagsMd.includes(KB_MISSING_ARG), 'flags.md missing --kb BLOCKED string');
  assert.ok(flagsMd.includes(LEVEL_BAD_ARG), 'flags.md missing --level BLOCKED string');
  // The JS literals must equal what the contract documents.
  assert.strictEqual(parseProposalArgs('--mcp').errors[0], MCP_MISSING_ARG);
  assert.strictEqual(parseProposalArgs('--kb').errors[0], KB_MISSING_ARG);
  assert.strictEqual(parseProposalArgs('--level x').errors[0], LEVEL_BAD_ARG);
});
