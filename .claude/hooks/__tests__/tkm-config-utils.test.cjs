#!/usr/bin/env node
/**
 * Tests for tkm-config-utils.cjs - Config and path utilities
 * Run: node --test .claude/hooks/__tests__/tkm-config-utils.test.cjs
 *
 * Covers:
 * - Config loading and merging
 * - Path sanitization
 * - Slug sanitization
 * - Plan resolution
 * - Reports path generation
 * - Naming patterns
 */

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const path = require('path');
const fs = require('fs');
const os = require('os');

const {
  deepMerge,
  normalizePath,
  isAbsolutePath,
  sanitizePath,
  sanitizeSlug,
  escapeShellValue,
  extractSlugFromBranch,
  getReportsPath,
  formatDate,
  validateNamingPattern,
  resolveNamingPattern,
  extractIssueFromBranch,
  getGitBranch,
  getGitRoot,
  DEFAULT_CONFIG,
  loadConfig,
  isGraphifyEnabled,
  isMemoryGraphEnabled,
  LOCAL_CONFIG_PATH,
  LEGACY_LOCAL_CONFIG_PATH
} = require('../lib/tkm-config-utils.cjs');

describe('tkm-config-utils.cjs', () => {

  describe('deepMerge', () => {

    it('merges nested objects', () => {
      const target = { a: { b: 1, c: 2 } };
      const source = { a: { d: 3 } };
      const result = deepMerge(target, source);

      assert.deepStrictEqual(result, { a: { b: 1, c: 2, d: 3 } });
    });

    it('source values override target', () => {
      const target = { a: { b: 1 } };
      const source = { a: { b: 2 } };
      const result = deepMerge(target, source);

      assert.deepStrictEqual(result, { a: { b: 2 } });
    });

    it('arrays are replaced entirely', () => {
      const target = { x: [1, 2, 3] };
      const source = { x: [4, 5] };
      const result = deepMerge(target, source);

      assert.deepStrictEqual(result, { x: [4, 5] });
    });

    it('handles null source', () => {
      const target = { a: 1 };
      const result = deepMerge(target, null);

      assert.deepStrictEqual(result, { a: 1 });
    });

    it('handles null target', () => {
      const source = { a: 1 };
      const result = deepMerge(null, source);

      assert.deepStrictEqual(result, { a: 1 });
    });

    it('handles null values in source', () => {
      const target = { a: 1 };
      const source = { a: null };
      const result = deepMerge(target, source);

      assert.deepStrictEqual(result, { a: null });
    });

    it('deep merges multiple levels', () => {
      const target = { a: { b: { c: 1 } } };
      const source = { a: { b: { d: 2 } } };
      const result = deepMerge(target, source);

      assert.deepStrictEqual(result, { a: { b: { c: 1, d: 2 } } });
    });

  });

  describe('normalizePath', () => {

    it('returns null for empty string', () => {
      assert.strictEqual(normalizePath(''), null);
    });

    it('returns null for whitespace only', () => {
      assert.strictEqual(normalizePath('   '), null);
    });

    it('returns null for null input', () => {
      assert.strictEqual(normalizePath(null), null);
    });

    it('returns null for undefined', () => {
      assert.strictEqual(normalizePath(undefined), null);
    });

    it('trims whitespace', () => {
      assert.strictEqual(normalizePath('  plans  '), 'plans');
    });

    it('removes trailing slashes', () => {
      assert.strictEqual(normalizePath('plans/'), 'plans');
      assert.strictEqual(normalizePath('plans//'), 'plans');
    });

    it('preserves internal slashes', () => {
      assert.strictEqual(normalizePath('path/to/plans'), 'path/to/plans');
    });

    it('handles Windows backslashes', () => {
      const result = normalizePath('path\\to\\plans\\');
      assert.ok(!result.endsWith('\\'), 'Should remove trailing backslash');
    });

    it('returns null for only slashes', () => {
      assert.strictEqual(normalizePath('///'), null);
    });

  });

  describe('isAbsolutePath', () => {

    it('returns true for Unix absolute paths', () => {
      assert.strictEqual(isAbsolutePath('/home/user'), true);
      assert.strictEqual(isAbsolutePath('/'), true);
    });

    it('returns true for Windows absolute paths (on Windows)', () => {
      // path.isAbsolute is OS-specific; Windows paths only detected on Windows
      if (process.platform === 'win32') {
        assert.strictEqual(isAbsolutePath('C:\\Users'), true);
        assert.strictEqual(isAbsolutePath('D:/projects'), true);
      } else {
        // On Unix, Windows paths are not recognized as absolute
        assert.strictEqual(isAbsolutePath('C:\\Users'), false);
      }
    });

    it('returns false for relative paths', () => {
      assert.strictEqual(isAbsolutePath('plans'), false);
      assert.strictEqual(isAbsolutePath('./plans'), false);
      assert.strictEqual(isAbsolutePath('../plans'), false);
    });

    it('returns false for null/undefined', () => {
      assert.strictEqual(isAbsolutePath(null), false);
      assert.strictEqual(isAbsolutePath(undefined), false);
      assert.strictEqual(isAbsolutePath(''), false);
    });

  });

  describe('sanitizePath', () => {

    const projectRoot = '/project';

    it('allows normal relative paths', () => {
      assert.strictEqual(sanitizePath('plans', projectRoot), 'plans');
      assert.strictEqual(sanitizePath('docs', projectRoot), 'docs');
    });

    it('allows absolute paths', () => {
      assert.strictEqual(sanitizePath('/custom/plans', projectRoot), '/custom/plans');
    });

    it('blocks null bytes', () => {
      assert.strictEqual(sanitizePath('plans\x00bad', projectRoot), null);
    });

    it('blocks path traversal', () => {
      assert.strictEqual(sanitizePath('../../../etc', projectRoot), null);
    });

    it('allows paths within project', () => {
      assert.strictEqual(sanitizePath('src/plans', projectRoot), 'src/plans');
    });

    it('returns null for empty input', () => {
      assert.strictEqual(sanitizePath('', projectRoot), null);
      assert.strictEqual(sanitizePath(null, projectRoot), null);
    });

  });

  describe('sanitizeSlug', () => {

    it('returns empty for null/undefined', () => {
      assert.strictEqual(sanitizeSlug(null), '');
      assert.strictEqual(sanitizeSlug(undefined), '');
    });

    it('converts spaces to hyphens', () => {
      assert.strictEqual(sanitizeSlug('my feature'), 'my-feature');
    });

    it('removes invalid filename chars then converts remaining special chars', () => {
      // Invalid filename chars (<>:"/\|?*) are removed first, then other non-alphanum become hyphens
      // So 'feat/add*new' → 'feataddnew' (/ and * removed as invalid filename chars)
      const result = sanitizeSlug('feat/add*new');
      assert.ok(!result.includes('/'), 'Should not contain slash');
      assert.ok(!result.includes('*'), 'Should not contain asterisk');
    });

    it('collapses multiple hyphens', () => {
      assert.strictEqual(sanitizeSlug('my--feature'), 'my-feature');
    });

    it('removes leading/trailing hyphens', () => {
      assert.strictEqual(sanitizeSlug('-slug-'), 'slug');
    });

    it('truncates long slugs', () => {
      const longSlug = 'a'.repeat(150);
      const result = sanitizeSlug(longSlug);
      assert.ok(result.length <= 100, 'Should truncate to 100 chars');
    });

    it('handles valid slugs unchanged', () => {
      assert.strictEqual(sanitizeSlug('my-feature'), 'my-feature');
      assert.strictEqual(sanitizeSlug('feature123'), 'feature123');
    });

  });

  describe('escapeShellValue', () => {

    it('escapes backslashes', () => {
      assert.strictEqual(escapeShellValue('path\\to\\file'), 'path\\\\to\\\\file');
    });

    it('escapes double quotes', () => {
      assert.strictEqual(escapeShellValue('say "hello"'), 'say \\"hello\\"');
    });

    it('escapes dollar signs', () => {
      assert.strictEqual(escapeShellValue('$HOME'), '\\$HOME');
    });

    it('escapes backticks', () => {
      assert.strictEqual(escapeShellValue('`cmd`'), '\\`cmd\\`');
    });

    it('handles non-string input', () => {
      assert.strictEqual(escapeShellValue(123), 123);
      assert.strictEqual(escapeShellValue(null), null);
    });

    it('escapes combined special chars', () => {
      const input = 'echo "$HOME" && `ls`';
      const expected = 'echo \\"\\$HOME\\" && \\`ls\\`';
      assert.strictEqual(escapeShellValue(input), expected);
    });

  });

  describe('extractSlugFromBranch', () => {

    it('extracts from feat/ branches', () => {
      assert.strictEqual(extractSlugFromBranch('feat/add-feature'), 'add-feature');
    });

    it('extracts from fix/ branches', () => {
      assert.strictEqual(extractSlugFromBranch('fix/bug-fix'), 'bug-fix');
    });

    it('extracts from chore/ branches', () => {
      assert.strictEqual(extractSlugFromBranch('chore/update-deps'), 'update-deps');
    });

    it('handles nested prefixes', () => {
      assert.strictEqual(extractSlugFromBranch('feat/user/add-feature'), 'add-feature');
    });

    it('returns null for non-matching branches', () => {
      assert.strictEqual(extractSlugFromBranch('main'), null);
      assert.strictEqual(extractSlugFromBranch('develop'), null);
    });

    it('returns null for null/undefined', () => {
      assert.strictEqual(extractSlugFromBranch(null), null);
      assert.strictEqual(extractSlugFromBranch(undefined), null);
    });

    it('sanitizes extracted slug', () => {
      const result = extractSlugFromBranch('feat/add*new#feature');
      assert.ok(!result.includes('*'), 'Should sanitize special chars');
      assert.ok(!result.includes('#'), 'Should sanitize special chars');
    });

  });

  describe('extractIssueFromBranch', () => {

    it('extracts from issue-123 format', () => {
      assert.strictEqual(extractIssueFromBranch('issue-123-fix'), '123');
    });

    it('extracts from gh-123 format', () => {
      assert.strictEqual(extractIssueFromBranch('gh-123-feature'), '123');
    });

    it('extracts from fix-123 format', () => {
      assert.strictEqual(extractIssueFromBranch('fix-123-bug'), '123');
    });

    it('extracts from feat-123 format', () => {
      assert.strictEqual(extractIssueFromBranch('feat-123-new'), '123');
    });

    it('extracts from /123/ format', () => {
      assert.strictEqual(extractIssueFromBranch('fix/123/description'), '123');
    });

    it('extracts from #123 format', () => {
      assert.strictEqual(extractIssueFromBranch('feat/#123-new'), '123');
    });

    it('returns null for no issue', () => {
      assert.strictEqual(extractIssueFromBranch('main'), null);
      assert.strictEqual(extractIssueFromBranch('feature-new'), null);
    });

    it('returns null for null/undefined', () => {
      assert.strictEqual(extractIssueFromBranch(null), null);
      assert.strictEqual(extractIssueFromBranch(undefined), null);
    });

  });

  describe('getReportsPath', () => {

    const planConfig = { reportsDir: 'reports' };
    const pathsConfig = { plans: 'plans' };

    it('uses plan-specific path for session-resolved plans', () => {
      const result = getReportsPath('plans/my-plan', 'session', planConfig, pathsConfig);
      assert.ok(result.includes('my-plan'), 'Should include plan name');
      assert.ok(result.includes('reports'), 'Should include reports dir');
    });

    it('uses default path for branch-resolved plans', () => {
      const result = getReportsPath('plans/my-plan', 'branch', planConfig, pathsConfig);
      assert.ok(!result.includes('my-plan'), 'Should NOT include plan name for branch');
      assert.ok(result.includes('reports'), 'Should include reports dir');
    });

    it('uses default path for null plan', () => {
      const result = getReportsPath(null, null, planConfig, pathsConfig);
      assert.strictEqual(result, 'plans/reports/');
    });

    it('handles whitespace-only planPath (Issue #327)', () => {
      const result = getReportsPath('   ', 'session', planConfig, pathsConfig);
      assert.strictEqual(result, 'plans/reports/', 'Should use default for whitespace');
    });

    it('returns absolute path when baseDir provided', () => {
      const baseDir = '/project';
      const result = getReportsPath(null, null, planConfig, pathsConfig, baseDir);
      assert.ok(result.startsWith('/project'), 'Should start with baseDir');
    });

  });

  describe('formatDate', () => {

    it('formats YYMMDD correctly', () => {
      const result = formatDate('YYMMDD');
      assert.match(result, /^\d{6}$/, 'Should be 6 digits');
    });

    it('formats YYMMDD-HHmm correctly', () => {
      const result = formatDate('YYMMDD-HHmm');
      assert.match(result, /^\d{6}-\d{4}$/, 'Should be 6 digits dash 4 digits');
    });

    it('formats YYYYMMDD correctly', () => {
      const result = formatDate('YYYYMMDD');
      assert.match(result, /^\d{8}$/, 'Should be 8 digits');
    });

    it('handles complex format', () => {
      const result = formatDate('YYYY-MM-DD_HH:mm:ss');
      assert.match(result, /^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}$/, 'Should match pattern');
    });

  });

  describe('validateNamingPattern', () => {

    it('valid pattern with {slug}', () => {
      const result = validateNamingPattern('250101-1200-{slug}');
      assert.strictEqual(result.valid, true);
    });

    it('invalid: missing {slug}', () => {
      const result = validateNamingPattern('250101-1200');
      assert.strictEqual(result.valid, false);
      assert.ok(result.error.includes('{slug}'));
    });

    it('invalid: empty pattern', () => {
      const result = validateNamingPattern('');
      assert.strictEqual(result.valid, false);
    });

    it('invalid: null pattern', () => {
      const result = validateNamingPattern(null);
      assert.strictEqual(result.valid, false);
    });

    it('invalid: unresolved placeholder', () => {
      const result = validateNamingPattern('{date}-{slug}');
      assert.strictEqual(result.valid, false);
      assert.ok(result.error.includes('{date}'));
    });

  });

  describe('resolveNamingPattern', () => {

    const planConfig = {
      namingFormat: '{date}-{issue}-{slug}',
      dateFormat: 'YYMMDD-HHmm',
      issuePrefix: 'GH-'
    };

    it('includes date in pattern', () => {
      const result = resolveNamingPattern(planConfig, null);
      assert.match(result, /^\d{6}-\d{4}/, 'Should start with date');
    });

    it('includes {slug} placeholder', () => {
      const result = resolveNamingPattern(planConfig, null);
      assert.ok(result.includes('{slug}'), 'Should include {slug}');
    });

    it('includes issue when branch has issue', () => {
      const result = resolveNamingPattern(planConfig, 'fix/123-some-bug');
      assert.ok(result.includes('GH-123'), 'Should include issue');
    });

    it('removes {issue} cleanly when no issue', () => {
      const result = resolveNamingPattern(planConfig, 'main');
      assert.ok(!result.includes('{issue}'), 'Should not have {issue}');
      assert.ok(!result.includes('--'), 'Should not have double hyphens');
    });

    it('uses issuePrefix from config', () => {
      const customConfig = { ...planConfig, issuePrefix: '#' };
      const result = resolveNamingPattern(customConfig, 'fix/456-bug');
      assert.ok(result.includes('#456'), 'Should use custom prefix');
    });

  });

  describe('getGitBranch', () => {

    it('returns null for non-git directory', () => {
      const tempDir = path.join(os.tmpdir(), 'non-git-' + Date.now());
      fs.mkdirSync(tempDir, { recursive: true });
      try {
        const result = getGitBranch(tempDir);
        assert.strictEqual(result, null);
      } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('returns branch name for git directory', () => {
      const result = getGitBranch();
      // Will return null if not in git repo, or branch name if in git repo
      assert.ok(result === null || typeof result === 'string');
    });

  });

  describe('getGitRoot', () => {

    it('returns null for non-git directory', () => {
      const tempDir = path.join(os.tmpdir(), 'non-git-root-' + Date.now());
      fs.mkdirSync(tempDir, { recursive: true });
      try {
        const result = getGitRoot(tempDir);
        assert.strictEqual(result, null);
      } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('returns absolute path for git directory', () => {
      const result = getGitRoot();
      if (result) {
        assert.ok(result.startsWith('/'), 'Should be absolute path');
      }
    });

    it('uses cwd parameter for resolution', () => {
      const currentRoot = getGitRoot();
      if (currentRoot) {
        const subdirPath = path.join(currentRoot, '.claude', 'hooks');
        if (fs.existsSync(subdirPath)) {
          const result = getGitRoot(subdirPath);
          assert.strictEqual(result, currentRoot, 'Should resolve to same root');
        }
      }
    });

  });

  describe('DEFAULT_CONFIG', () => {

    it('has required plan config', () => {
      assert.ok(DEFAULT_CONFIG.plan);
      assert.ok(DEFAULT_CONFIG.plan.namingFormat);
      assert.ok(DEFAULT_CONFIG.plan.dateFormat);
      assert.ok(DEFAULT_CONFIG.plan.reportsDir);
    });

    it('has required paths config', () => {
      assert.ok(DEFAULT_CONFIG.paths);
      assert.ok(DEFAULT_CONFIG.paths.docs);
      assert.ok(DEFAULT_CONFIG.paths.plans);
    });

    it('has locale config', () => {
      assert.ok(DEFAULT_CONFIG.locale !== undefined);
    });

    it('has trust config', () => {
      assert.ok(DEFAULT_CONFIG.trust !== undefined);
      assert.strictEqual(DEFAULT_CONFIG.trust.enabled, false);
    });

    it('enables statusline quota chips by default', () => {
      assert.strictEqual(DEFAULT_CONFIG.statuslineQuota, true);
    });

    it('defaults takumi.sddMode to ask (first-run prompt)', () => {
      assert.ok(DEFAULT_CONFIG.takumi !== undefined);
      assert.strictEqual(DEFAULT_CONFIG.takumi.sddMode, 'ask');
    });

    it('enables the graphify Knowledge Graph by default', () => {
      assert.ok(DEFAULT_CONFIG.graphify !== undefined);
      assert.strictEqual(DEFAULT_CONFIG.graphify.enabled, true);
    });

    it('disables memory-graph (tier-auto KG memory) by default', () => {
      assert.ok(DEFAULT_CONFIG.memoryGraph !== undefined);
      assert.strictEqual(DEFAULT_CONFIG.memoryGraph.enabled, false);
    });

  });

  describe('isGraphifyEnabled', () => {

    it('honors the env hard opt-out (GRAPHIFY_DISABLE=1)', () => {
      const prev = process.env.GRAPHIFY_DISABLE;
      process.env.GRAPHIFY_DISABLE = '1';
      try {
        assert.strictEqual(isGraphifyEnabled(), false);
      } finally {
        if (prev === undefined) delete process.env.GRAPHIFY_DISABLE;
        else process.env.GRAPHIFY_DISABLE = prev;
      }
    });

    it('honors REBUILD_NO_GRAPH=1 as a hard opt-out', () => {
      const prev = process.env.REBUILD_NO_GRAPH;
      process.env.REBUILD_NO_GRAPH = '1';
      try {
        assert.strictEqual(isGraphifyEnabled(), false);
      } finally {
        if (prev === undefined) delete process.env.REBUILD_NO_GRAPH;
        else process.env.REBUILD_NO_GRAPH = prev;
      }
    });

  });

  describe('isMemoryGraphEnabled', () => {

    it('defaults to false when no config file is present', () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-no-config-'));
      const originalCwd = process.cwd();
      fs.mkdirSync(path.join(tempDir, '.claude'), { recursive: true });
      process.chdir(tempDir);
      try {
        const prevEnv = process.env.MEMORY_GRAPH_DISABLE;
        delete process.env.MEMORY_GRAPH_DISABLE;
        try {
          assert.strictEqual(isMemoryGraphEnabled(), false);
        } finally {
          if (prevEnv !== undefined) process.env.MEMORY_GRAPH_DISABLE = prevEnv;
        }
      } finally {
        process.chdir(originalCwd);
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('returns true when .claude/.tkm.json sets memoryGraph.enabled=true', () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-enabled-'));
      const originalCwd = process.cwd();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(
        path.join(claudeDir, '.tkm.json'),
        JSON.stringify({ memoryGraph: { enabled: true } })
      );
      process.chdir(tempDir);
      try {
        const prevEnv = process.env.MEMORY_GRAPH_DISABLE;
        delete process.env.MEMORY_GRAPH_DISABLE;
        try {
          assert.strictEqual(isMemoryGraphEnabled(), true);
        } finally {
          if (prevEnv !== undefined) process.env.MEMORY_GRAPH_DISABLE = prevEnv;
        }
      } finally {
        process.chdir(originalCwd);
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('returns false when .claude/.tkm.json sets memoryGraph.enabled=false', () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-disabled-'));
      const originalCwd = process.cwd();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(
        path.join(claudeDir, '.tkm.json'),
        JSON.stringify({ memoryGraph: { enabled: false } })
      );
      process.chdir(tempDir);
      try {
        const prevEnv = process.env.MEMORY_GRAPH_DISABLE;
        delete process.env.MEMORY_GRAPH_DISABLE;
        try {
          assert.strictEqual(isMemoryGraphEnabled(), false);
        } finally {
          if (prevEnv !== undefined) process.env.MEMORY_GRAPH_DISABLE = prevEnv;
        }
      } finally {
        process.chdir(originalCwd);
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('honors MEMORY_GRAPH_DISABLE=1 as hard opt-out', () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-env-disable-'));
      const originalCwd = process.cwd();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      fs.writeFileSync(
        path.join(claudeDir, '.tkm.json'),
        JSON.stringify({ memoryGraph: { enabled: true } })
      );
      process.chdir(tempDir);
      try {
        const prevEnv = process.env.MEMORY_GRAPH_DISABLE;
        process.env.MEMORY_GRAPH_DISABLE = '1';
        try {
          assert.strictEqual(isMemoryGraphEnabled(), false);
        } finally {
          if (prevEnv === undefined) delete process.env.MEMORY_GRAPH_DISABLE;
          else process.env.MEMORY_GRAPH_DISABLE = prevEnv;
        }
      } finally {
        process.chdir(originalCwd);
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('only reads .claude/.tkm.json and global ~/.claude/.tkm.json (not .takumi.json)', () => {
      const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'memory-graph-takumi-ignore-'));
      const originalCwd = process.cwd();
      const claudeDir = path.join(tempDir, '.claude');
      fs.mkdirSync(claudeDir, { recursive: true });
      // Write to .takumi.json (should be ignored for memory-graph)
      fs.writeFileSync(
        path.join(claudeDir, '.takumi.json'),
        JSON.stringify({ memoryGraph: { enabled: true } })
      );
      process.chdir(tempDir);
      try {
        const prevEnv = process.env.MEMORY_GRAPH_DISABLE;
        delete process.env.MEMORY_GRAPH_DISABLE;
        try {
          // Should still be false because .takumi.json is not read for memory-graph
          assert.strictEqual(isMemoryGraphEnabled(), false);
        } finally {
          if (prevEnv !== undefined) process.env.MEMORY_GRAPH_DISABLE = prevEnv;
        }
      } finally {
        process.chdir(originalCwd);
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

  });

  describe('config file resolution (.tkm.json with .sk.json fallback)', () => {
    let tempDir;
    let originalCwd;

    beforeEach(() => {
      originalCwd = process.cwd();
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'tkm-config-test-'));
      fs.mkdirSync(path.join(tempDir, '.claude'), { recursive: true });
      process.chdir(tempDir);
    });

    afterEach(() => {
      process.chdir(originalCwd);
      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('exposes .tkm.json as primary and .sk.json as legacy path', () => {
      assert.strictEqual(LOCAL_CONFIG_PATH, '.claude/.tkm.json');
      assert.strictEqual(LEGACY_LOCAL_CONFIG_PATH, '.claude/.sk.json');
    });

    it('reads local .tkm.json config', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.tkm.json'),
        JSON.stringify({ plan: { reportsDir: 'from-tkm' } })
      );
      const config = loadConfig();
      assert.strictEqual(config.plan.reportsDir, 'from-tkm');
    });

    it('isGraphifyEnabled reads graphify.enabled from local .takumi.json (tkm CLI file)', () => {
      // `tkm graphify off` writes .claude/.takumi.json — the KG toggle must honor it.
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.takumi.json'),
        JSON.stringify({ graphify: { enabled: false } })
      );
      assert.strictEqual(isGraphifyEnabled(), false);
    });

    it('isGraphifyEnabled: local .tkm.json still works when no .takumi.json', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.tkm.json'),
        JSON.stringify({ graphify: { enabled: false } })
      );
      assert.strictEqual(isGraphifyEnabled(), false);
    });

    it('falls back to deprecated local .sk.json when .tkm.json is absent', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.sk.json'),
        JSON.stringify({ plan: { reportsDir: 'from-legacy-sk' } })
      );
      const config = loadConfig();
      assert.strictEqual(config.plan.reportsDir, 'from-legacy-sk');
    });

    it('prefers .tkm.json over .sk.json when both exist', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.tkm.json'),
        JSON.stringify({ plan: { reportsDir: 'from-tkm' } })
      );
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.sk.json'),
        JSON.stringify({ plan: { reportsDir: 'from-legacy-sk' } })
      );
      const config = loadConfig();
      assert.strictEqual(config.plan.reportsDir, 'from-tkm');
    });

    it('project-scope .tkm.json overrides takumi.sddMode (shared decision)', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.tkm.json'),
        JSON.stringify({ takumi: { sddMode: 'off' } })
      );
      const config = loadConfig();
      assert.strictEqual(config.takumi.sddMode, 'off');
    });

    it('falls back to default sddMode when no config file sets it', () => {
      const config = loadConfig();
      assert.strictEqual(config.takumi.sddMode, 'ask');
    });

    it('coerces an invalid takumi.sddMode value back to ask', () => {
      fs.writeFileSync(
        path.join(tempDir, '.claude', '.tkm.json'),
        JSON.stringify({ takumi: { sddMode: 'yes' } })
      );
      const config = loadConfig();
      assert.strictEqual(config.takumi.sddMode, 'ask');
    });
  });

});
