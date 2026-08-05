#!/usr/bin/env node
/**
 * Tests for skill-extension-loader.cjs hook — user-owned skill extension injection
 * Run: node --test claude/hooks/__tests__/skill-extension-loader.test.cjs
 *
 * Scenarios:
 * - No extensions dir → silent {} output
 * - Valid pre/post/override extensions → injected in pre → override → post order
 * - Invalid frontmatter (wrong extends, bad type, missing frontmatter) → skipped
 * - Oversize payload → degrades to file-path summary
 * - Path traversal in skill name → rejected with {}
 * - Frontmatter with no trailing newline after closing --- → empty body, not leaked
 * - Malformed stdin → fail-open {} with exit 0
 *
 * Each test gets a fresh temp project dir (no shared state between cases).
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const HOOK_PATH = path.join(__dirname, '..', 'skill-extension-loader.cjs');

/** Run hook with given stdin payload, resolve {stdout, exitCode, parsed}.
 * CLAUDE_PROJECT_DIR is stripped by default so cwd-based tests stay hermetic
 * (the test runner itself sets it); pass it explicitly via envOverride to test
 * project-dir resolution. */
function runHook(stdinPayload, envOverride) {
  return new Promise((resolve, reject) => {
    const env = { ...process.env, ...(envOverride || {}) };
    if (!envOverride || !('CLAUDE_PROJECT_DIR' in envOverride)) delete env.CLAUDE_PROJECT_DIR;
    const proc = spawn('node', [HOOK_PATH], { env });
    let stdout = '';
    let settled = false;
    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', () => {});
    proc.stdin.write(stdinPayload);
    proc.stdin.end();
    const timeoutId = setTimeout(() => {
      if (!settled) {
        settled = true;
        proc.kill('SIGTERM');
        reject(new Error('Hook execution timed out'));
      }
    }, 5000);
    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutId);
      let parsed = null;
      try {
        if (stdout.trim()) parsed = JSON.parse(stdout.trim());
      } catch (_) {}
      resolve({ stdout, exitCode: code, parsed });
    });
  });
}

/** Build PreToolUse stdin payload for a Skill call */
function skillPayload(skillName, cwd) {
  return JSON.stringify({
    tool_name: 'Skill',
    tool_input: { skill: skillName },
    cwd,
  });
}

/** Write an extension file with frontmatter */
function writeExtension(dir, name, { extendsField, type, body }) {
  const fm = ['---'];
  if (extendsField !== undefined) fm.push(`extends: ${extendsField}`);
  if (type !== undefined) fm.push(`type: ${type}`);
  fm.push('---', '');
  fs.writeFileSync(path.join(dir, name), fm.join('\n') + (body || 'instruction body'));
}

describe('skill-extension-loader hook', () => {
  let tmpDir;
  let extDir;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-ext-test-'));
    extDir = path.join(tmpDir, '.claude', 'skills', 'review-code', 'extensions');
    fs.mkdirSync(extDir, { recursive: true });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it('outputs {} when skill has no extensions dir', async () => {
    const { parsed, exitCode } = await runHook(skillPayload('tkm:fix-bug', tmpDir));
    assert.strictEqual(exitCode, 0);
    assert.deepStrictEqual(parsed, {});
  });

  it('injects valid extensions in pre → override → post order', async () => {
    writeExtension(extDir, 'z-first-by-type.md', {
      extendsField: 'tkm:review-code',
      type: 'pre',
      body: 'PRE BODY',
    });
    writeExtension(extDir, 'a-last-by-type.md', {
      extendsField: 'tkm:review-code',
      type: 'post',
      body: 'POST BODY',
    });
    writeExtension(extDir, 'm-middle.md', {
      extendsField: 'review-code', // prefix-less extends must also match
      type: 'override:What to Inspect',
      body: 'OVERRIDE BODY',
    });

    const { parsed, exitCode } = await runHook(skillPayload('tkm:review-code', tmpDir));
    assert.strictEqual(exitCode, 0);
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, undefined);
    assert.match(ctx, /Active Extensions for tkm:review-code/);
    const preIdx = ctx.indexOf('PRE BODY');
    const overrideIdx = ctx.indexOf('OVERRIDE BODY');
    const postIdx = ctx.indexOf('POST BODY');
    assert.ok(preIdx >= 0 && overrideIdx > preIdx && postIdx > overrideIdx, 'order must be pre → override → post');
  });

  it('skips files with wrong extends, invalid type, or missing frontmatter', async () => {
    writeExtension(extDir, 'valid.md', {
      extendsField: 'tkm:review-code',
      type: 'post',
      body: 'VALID BODY',
    });
    writeExtension(extDir, 'wrong-target.md', {
      extendsField: 'tkm:fix-bug',
      type: 'post',
      body: 'WRONG TARGET',
    });
    writeExtension(extDir, 'bad-type.md', {
      extendsField: 'tkm:review-code',
      type: 'around', // invalid
      body: 'BAD TYPE',
    });
    fs.writeFileSync(path.join(extDir, 'no-frontmatter.md'), 'just plain text');

    const { parsed } = await runHook(skillPayload('tkm:review-code', tmpDir));
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('VALID BODY'));
    assert.ok(!ctx.includes('WRONG TARGET'));
    assert.ok(!ctx.includes('BAD TYPE'));
    assert.match(ctx, /Skipped invalid extension files:.*bad-type\.md/);
  });

  it('degrades to file-path summary when payload exceeds size cap', async () => {
    writeExtension(extDir, 'huge.md', {
      extendsField: 'tkm:review-code',
      type: 'post',
      body: 'X'.repeat(5000),
    });
    const { parsed } = await runHook(skillPayload('tkm:review-code', tmpDir));
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(!ctx.includes('X'.repeat(100)), 'oversize body must not be inlined');
    assert.match(ctx, /huge\.md \(\d+ chars — read this file and apply it\)/);
  });

  it('rejects path traversal in skill name with {}', async () => {
    // Plant a decoy outside .claude/skills/ that a traversal would reach
    const decoyDir = path.join(tmpDir, '.claude', 'hooks', 'extensions');
    fs.mkdirSync(decoyDir, { recursive: true });
    writeExtension(decoyDir, 'decoy.md', {
      extendsField: 'tkm:../hooks',
      type: 'post',
      body: 'DECOY BODY',
    });

    for (const name of ['tkm:../hooks', '../../etc', 'tkm:../../..']) {
      const { parsed, exitCode } = await runHook(skillPayload(name, tmpDir));
      assert.strictEqual(exitCode, 0);
      assert.deepStrictEqual(parsed, {}, `traversal skill name "${name}" must be rejected`);
    }
  });

  it('returns empty body when closing --- has no trailing newline (no frontmatter leak)', async () => {
    fs.writeFileSync(
      path.join(extDir, 'no-trailing-newline.md'),
      '---\nextends: tkm:review-code\ntype: post\n---'
    );
    writeExtension(extDir, 'valid.md', {
      extendsField: 'tkm:review-code',
      type: 'pre',
      body: 'VALID BODY',
    });
    const { parsed } = await runHook(skillPayload('tkm:review-code', tmpDir));
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(!ctx.includes('extends: tkm:review-code\ntype: post'), 'frontmatter must not leak into injected body');
    assert.ok(ctx.includes('VALID BODY'));
  });

  it('fails open on malformed stdin', async () => {
    const { parsed, exitCode } = await runHook('not json at all');
    assert.strictEqual(exitCode, 0);
    assert.deepStrictEqual(parsed, {});
  });

  it('outputs {} for non-Skill tool calls', async () => {
    const { parsed } = await runHook(
      JSON.stringify({ tool_name: 'Read', tool_input: { file_path: '/x' }, cwd: tmpDir })
    );
    assert.deepStrictEqual(parsed, {});
  });
});

describe('skill-extension-loader — multi-root resolution + shared dir', () => {
  const dirs = [];
  function freshDir(label) {
    const d = fs.mkdtempSync(path.join(os.tmpdir(), `skill-ext-${label}-`));
    dirs.push(d);
    return d;
  }
  /** Create <root>/.claude/skills/<skillDir>/extensions and return it */
  function localExtDir(root, skillDir) {
    const d = path.join(root, '.claude', 'skills', skillDir, 'extensions');
    fs.mkdirSync(d, { recursive: true });
    return d;
  }
  /** Create <sharedRoot>/<skillDir> and return it */
  function sharedExtDir(sharedRoot, skillDir) {
    const d = path.join(sharedRoot, skillDir);
    fs.mkdirSync(d, { recursive: true });
    return d;
  }
  function writeConfig(root, obj, basename = '.tkm.json') {
    const d = path.join(root, '.claude');
    fs.mkdirSync(d, { recursive: true });
    fs.writeFileSync(path.join(d, basename), JSON.stringify(obj));
  }

  afterEach(() => {
    for (const d of dirs.splice(0)) fs.rmSync(d, { recursive: true, force: true });
  });

  it('resolves local extensions via $CLAUDE_PROJECT_DIR when cwd differs', async () => {
    const projectDir = freshDir('proj');
    const workDir = freshDir('work'); // cwd, no .claude
    writeExtension(localExtDir(projectDir, 'review-code'), 'e.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'PROJECTDIR BODY',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', workDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('PROJECTDIR BODY'));
  });

  it('resolves local extensions via $HOME for a global install', async () => {
    const homeDir = freshDir('home');
    const workDir = freshDir('work');
    writeExtension(localExtDir(homeDir, 'review-code'), 'e.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'GLOBAL HOME BODY',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', workDir),
      { HOME: homeDir }
    );
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('GLOBAL HOME BODY'));
  });

  it('prefers $CLAUDE_PROJECT_DIR over cwd when both have extensions', async () => {
    const projectDir = freshDir('proj');
    const workDir = freshDir('work');
    writeExtension(localExtDir(projectDir, 'review-code'), 'e.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'FROM PROJECTDIR',
    });
    writeExtension(localExtDir(workDir, 'review-code'), 'e.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'FROM CWD',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', workDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('FROM PROJECTDIR'));
    assert.ok(!ctx.includes('FROM CWD'));
  });

  it('injects team-shared extensions from configured sharedDir', async () => {
    const projectDir = freshDir('proj');
    const sharedRoot = freshDir('shared');
    writeConfig(projectDir, { skillExtensions: { sharedDir: sharedRoot } });
    writeExtension(sharedExtDir(sharedRoot, 'review-code'), 'team.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'SHARED TEAM BODY',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', projectDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('SHARED TEAM BODY'));
  });

  it('reads sharedDir from .takumi.json written by the tkm CLI', async () => {
    const projectDir = freshDir('proj');
    const sharedRoot = freshDir('shared');
    // CLI writes .takumi.json (not the kit-native .tkm.json) — loader must bridge both
    writeConfig(projectDir, { skillExtensions: { sharedDir: sharedRoot } }, '.takumi.json');
    writeExtension(sharedExtDir(sharedRoot, 'review-code'), 'team.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'SHARED VIA TAKUMI JSON',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', projectDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('SHARED VIA TAKUMI JSON'));
  });

  it('local overrides shared on filename collision', async () => {
    const projectDir = freshDir('proj');
    const sharedRoot = freshDir('shared');
    writeConfig(projectDir, { skillExtensions: { sharedDir: sharedRoot } });
    writeExtension(localExtDir(projectDir, 'review-code'), 'x.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'LOCAL WINS',
    });
    writeExtension(sharedExtDir(sharedRoot, 'review-code'), 'x.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'SHARED LOSES',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', projectDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    const ctx = parsed.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('LOCAL WINS'));
    assert.ok(!ctx.includes('SHARED LOSES'));
  });

  it('ignores a sharedDir that escapes the project root (relative ../)', async () => {
    const projectDir = freshDir('proj');
    const sibling = freshDir('sibling');
    // Plant an extension in a sibling reachable only via ../
    writeExtension(sharedExtDir(sibling, 'review-code'), 'evil.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'ESCAPED BODY',
    });
    const rel = path.relative(projectDir, sibling); // starts with ..
    writeConfig(projectDir, { skillExtensions: { sharedDir: rel } });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', projectDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    // No local extensions + rejected shared → silent {}
    assert.deepStrictEqual(parsed, {});
  });

  it('no sharedDir config → only local loads (no regression)', async () => {
    const projectDir = freshDir('proj');
    writeExtension(localExtDir(projectDir, 'review-code'), 'e.md', {
      extendsField: 'tkm:review-code', type: 'post', body: 'LOCAL ONLY',
    });
    const { parsed } = await runHook(
      skillPayload('tkm:review-code', projectDir),
      { CLAUDE_PROJECT_DIR: projectDir }
    );
    assert.ok(parsed.hookSpecificOutput.additionalContext.includes('LOCAL ONLY'));
  });
});
