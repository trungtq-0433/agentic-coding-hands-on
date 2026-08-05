import { test } from 'node:test';
import assert from 'node:assert';
import { readFileSync } from 'node:fs';

// Same single-source-of-truth shim pattern as proposal-flags.test.js: load
// propose-improvements-workflow.js and re-export the (un-exported) idempotency helpers.
const src = readFileSync(new URL('../../propose-improvements-workflow.js', import.meta.url), 'utf8');
const shim = src + '\nexport { normalizeArtifactSet, normPath, skipResult };';
const { normalizeArtifactSet, normPath, skipResult } = await import(
  'data:text/javascript,' + encodeURIComponent(shim)
);

test('normalizeArtifactSet canonicalizes paths for set.has() gating', () => {
  const set = normalizeArtifactSet([
    'plans/improvement-proposal/scout-report.md',
    './plans/improvement-proposal/use-context.json',          // leading ./
    'plans\\improvement-proposal\\technical\\01-discovery\\01-repository-identity.md', // backslashes
    '  plans/improvement-proposal/combined-initial.md  ',     // surrounding whitespace
    'plans/improvement-proposal/validation/',                 // trailing slash
    '',                                                       // empty → dropped
    null,                                                     // nullish → dropped
  ]);
  assert.ok(set.has('plans/improvement-proposal/scout-report.md'));
  assert.ok(set.has('plans/improvement-proposal/use-context.json'));
  assert.ok(set.has('plans/improvement-proposal/technical/01-discovery/01-repository-identity.md'));
  assert.ok(set.has('plans/improvement-proposal/combined-initial.md'));
  assert.ok(set.has('plans/improvement-proposal/validation')); // trailing slash stripped
  assert.strictEqual(set.size, 5); // empty + null dropped
});

// K-mcp-fetch per-task idempotency gates `inventory.has(normPath(task.output))`. The inventory is
// built by normalizeArtifactSet (same canonicalization), so a task.output the plan agent emits with a
// stray "./", backslashes, or trailing slash MUST still match its on-disk file — otherwise a present
// file is re-fetched (wasteful but safe) or, worse, the dirty form is treated as a distinct path.
test('normPath canonicalizes a task.output for inventory lookup (matches normalizeArtifactSet)', () => {
  const inventory = normalizeArtifactSet(['plans/external-knowledge/mcp/01-product-identity.md']);
  for (const dirty of [
    './plans/external-knowledge/mcp/01-product-identity.md',          // leading ./
    'plans\\external-knowledge\\mcp\\01-product-identity.md',         // backslashes
    '  plans/external-knowledge/mcp/01-product-identity.md  ',        // surrounding whitespace
    'plans/external-knowledge/mcp/01-product-identity.md',            // already clean
  ]) {
    assert.ok(inventory.has(normPath(dirty)), `should match: ${JSON.stringify(dirty)}`);
  }
  // A genuinely different (missing) task output must NOT match → that task gets fetched.
  assert.ok(!inventory.has(normPath('plans/external-knowledge/mcp/02-tech-stack.md')));
});

test('normalizeArtifactSet tolerates non-array input', () => {
  assert.strictEqual(normalizeArtifactSet(undefined).size, 0);
  assert.strictEqual(normalizeArtifactSet(null).size, 0);
  assert.strictEqual(normalizeArtifactSet('not-an-array').size, 0);
});

test('skipResult is shaped like a STATUS_SCHEMA agent return', () => {
  const r = skipResult('plans/improvement-proposal/scout-report.md');
  assert.strictEqual(r.status, 'SKIP');
  assert.deepStrictEqual(r.logLines, [
    'skip: plans/improvement-proposal/scout-report.md (artifact exists)',
  ]);
});
