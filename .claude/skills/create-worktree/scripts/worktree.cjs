#!/usr/bin/env node
/**
 * Git Worktree Manager for Takumi Agent Kit
 * Cross-platform Node.js script for creating isolated git worktrees
 *
 * Usage: node worktree.cjs <command> [options]
 * Commands:
 *   create <project> <feature>  Create a new worktree (project optional for standalone)
 *   remove <name-or-path>       Remove a worktree and its branch
 *   info                        Get repo info (type, projects, env files)
 *   list                        List existing worktrees
 *
 * Options:
 *   --prefix <type>        Branch prefix (feat|fix|refactor|docs|test|chore|perf)
 *   --worktree-root <path> Explicit worktree directory (Claude's decision)
 *   --json                 Output in JSON format for LLM consumption
 *   --env <files>          Comma-separated list of .env files to copy (legacy)
 *   --dry-run              Show what would be done without executing
 *   --no-prefix            Skip branch prefix and preserve original case
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ---------------------------------------------------------------------------
// Node version gate — must run before any output helpers are defined because
// outputError is referenced below; if not yet defined we fall back to stderr.
// ---------------------------------------------------------------------------
const MIN_NODE_VERSION = 18;
const nodeVersion = parseInt(process.version.slice(1).split('.')[0], 10);
if (nodeVersion < MIN_NODE_VERSION) {
  // outputError not available yet — write raw JSON so callers can parse it.
  process.stderr.write(
    JSON.stringify({ success: false, error: { code: 'NODE_VERSION_ERROR', message: `Node.js ${MIN_NODE_VERSION}+ required. Current: ${process.version}` } }) + '\n'
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// CLI argument parsing — strip recognized flags from argv before reading cmd
// ---------------------------------------------------------------------------
const argv = process.argv.slice(2);

// --json
const jsonFlagIdx = argv.indexOf('--json');
const useJsonOutput = jsonFlagIdx > -1;
if (jsonFlagIdx > -1) argv.splice(jsonFlagIdx, 1);

// --prefix <value>
const prefixFlagIdx = argv.indexOf('--prefix');
let branchPrefix = 'feat';
let branchPrefixWarning = null;
if (prefixFlagIdx > -1) {
  const rawValue = argv[prefixFlagIdx + 1] || 'feat';
  branchPrefix = sanitizeBranchPrefix(rawValue);
  if (branchPrefix !== rawValue.toLowerCase()) {
    branchPrefixWarning = `Branch prefix sanitized: "${rawValue}" → "${branchPrefix}"`;
  }
  argv.splice(prefixFlagIdx, 2);
}

// --env <files>
const envFlagIdx = argv.indexOf('--env');
let requestedEnvFiles = [];
if (envFlagIdx > -1) {
  requestedEnvFiles = (argv[envFlagIdx + 1] || '')
    .split(',')
    .map(v => v.trim())
    .filter(Boolean);
  argv.splice(envFlagIdx, 2);
}

// --dry-run
const dryRunFlagIdx = argv.indexOf('--dry-run');
const isDryRun = dryRunFlagIdx > -1;
if (dryRunFlagIdx > -1) argv.splice(dryRunFlagIdx, 1);

// --no-prefix
const noPrefixFlagIdx = argv.indexOf('--no-prefix');
const noPrefix = noPrefixFlagIdx > -1;
if (noPrefixFlagIdx > -1) argv.splice(noPrefixFlagIdx, 1);

// --worktree-root <path>
const wtRootFlagIdx = argv.indexOf('--worktree-root');
let explicitWorktreeRoot = null;
if (wtRootFlagIdx > -1) {
  explicitWorktreeRoot = argv[wtRootFlagIdx + 1];
  argv.splice(wtRootFlagIdx, 2);
}

// Positional arguments after flag stripping
const command = argv[0];
const arg1 = argv[1];  // project (monorepo) or feature (standalone) or worktree-name (remove)
const arg2 = argv[2];  // feature (monorepo create)

// ---------------------------------------------------------------------------
// String / name sanitisation helpers
// ---------------------------------------------------------------------------

/**
 * Normalise a branch prefix value to lowercase, alphanumeric-plus-dash only.
 * Falls back to 'feat' if empty after cleaning.
 */
function sanitizeBranchPrefix(value) {
  const lower = String(value || '').trim().toLowerCase();
  if (!lower) return 'feat';
  const cleaned = lower
    .replace(/[^a-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 20);
  return cleaned || 'feat';
}

/**
 * Verify a caller-supplied .env filename is safe to copy:
 * - must be a string
 * - no null bytes
 * - not absolute
 * - no directory traversal
 * - no path separators
 * - matches .env* pattern
 */
function isSafeEnvFileName(fileName) {
  if (!fileName || typeof fileName !== 'string') return false;
  if (fileName.includes('\0')) return false;
  if (path.isAbsolute(fileName)) return false;
  const normalised = path.normalize(fileName.trim());
  if (normalised.startsWith('..') || normalised.includes(`..${path.sep}`)) return false;
  if (normalised.includes(path.sep)) return false;
  return /^\.env[\w.-]*$/.test(normalised);
}

/**
 * Convert a feature/branch label into a git-safe name.
 * When preserveCase=true (--no-prefix mode) forward slashes and original
 * casing are kept; '..' path components are explicitly rejected.
 */
function sanitizeFeatureName(name, preserveCase = false) {
  const trimmed = String(name || '').trim();
  if (!trimmed) return '';

  // Strip diacritics for cleaner ASCII output.
  let normalised = trimmed.normalize('NFKD').replace(/[̀-ͯ]/g, '');

  if (!preserveCase) normalised = normalised.toLowerCase();

  // Reject traversal segments when slashes are meaningful.
  if (preserveCase && normalised.split('/').some(seg => seg === '..')) {
    return '';
  }

  // Replace characters that are illegal in git branch names.
  const allowedPattern = preserveCase ? /[^a-zA-Z0-9/.-]/g : /[^a-z0-9-]/g;
  normalised = normalised
    .replace(allowedPattern, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');

  if (preserveCase) {
    // Normalise slash sequences and remove dashes flanking slashes.
    normalised = normalised
      .replace(/\/+/g, '/')
      .replace(/^\/|\/$/g, '')
      .replace(/-?\/-?/g, '/');
  }

  // Longer limit for multi-segment names (user/type/feature patterns).
  const limit = preserveCase ? 80 : 50;
  normalised = normalised.slice(0, limit);

  if (normalised) return normalised;

  // Deterministic fallback when only non-ASCII letters were supplied.
  if (/[\p{L}\p{N}]/u.test(trimmed)) {
    const digest = crypto.createHash('sha1').update(trimmed).digest('hex').slice(0, 8);
    return `feature-${digest}`;
  }

  return '';
}

/**
 * Replace forward slashes with dashes so a multi-segment branch name can be
 * used safely as a single filesystem directory component.
 */
function flattenForDirectoryName(branchSegment) {
  return branchSegment.replace(/\//g, '-');
}

// ---------------------------------------------------------------------------
// Output layer — writes either JSON (--json) or human-readable text
// ---------------------------------------------------------------------------

function emit(data) {
  if (useJsonOutput) {
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  if (data.success) {
    console.log(`\n✅ ${data.message}`);
    if (data.worktreePath) {
      console.log(`\n📋 Next Steps:`);
      console.log(`   1. cd ${data.worktreePath}`);
      console.log(`   2. claude`);
      console.log(`   3. Start working on your feature`);
      console.log(`\n🧹 Cleanup when done:`);
      console.log(`   git worktree remove ${data.worktreePath}`);
      console.log(`   git branch -d ${data.branch}`);
    }
    if (data.envTemplatesCopied && data.envTemplatesCopied.length > 0) {
      console.log(`\n📄 Environment templates copied:`);
      data.envTemplatesCopied.forEach(t => console.log(`   ✓ ${t.from} → ${t.to}`));
    } else if (data.envFilesCopied && data.envFilesCopied.length > 0) {
      console.log(`\n📄 Environment files copied:`);
      data.envFilesCopied.forEach(f => console.log(`   ✓ ${f}`));
    }
    if (data.warnings && data.warnings.length > 0) {
      console.log(`\n⚠️  Warnings:`);
      data.warnings.forEach(w => console.log(`   ${w}`));
    }
    return;
  }

  if (data.info) {
    console.log(`\n📦 Repository Info:`);
    console.log(`   Type: ${data.repoType}`);
    console.log(`   Base branch: ${data.baseBranch}`);
    if (data.worktreeRoot) {
      console.log(`\n📂 Worktree location:`);
      console.log(`   Path: ${data.worktreeRoot}`);
      console.log(`   Source: ${data.worktreeRootSource}`);
    }
    if (data.projects && data.projects.length > 0) {
      console.log(`\n📁 Available projects:`);
      data.projects.forEach(p => console.log(`   - ${p.name} (${p.path})`));
    }
    if (data.envFiles && data.envFiles.length > 0) {
      console.log(`\n🔐 Environment files found:`);
      data.envFiles.forEach(f => console.log(`   - ${f}`));
    }
    if (data.dirtyState) {
      console.log(`\n⚠️  Working directory has uncommitted changes`);
    }
  }
}

/**
 * Write a structured error and exit 1.  Never returns.
 * Writes to stdout (JSON) so callers can parse, and stderr for human readers.
 */
function die(code, message, extras = {}) {
  const payload = { success: false, error: { code, message, ...extras } };
  if (useJsonOutput) {
    console.log(JSON.stringify(payload, null, 2));
  } else {
    console.error(`\n❌ Error [${code}]: ${message}`);
    if (extras.suggestion) console.error(`   💡 ${extras.suggestion}`);
    if (extras.availableProjects) {
      console.error(`\n   Available projects:`);
      extras.availableProjects.forEach(p => console.error(`     - ${p}`));
    }
  }
  process.exit(1);
}

// Keep original name as alias — tests call the module indirectly through the
// CLI, but the alias keeps internal error-path calls consistent.
const outputError = die;

// ---------------------------------------------------------------------------
// Git wrapper
// ---------------------------------------------------------------------------

/**
 * Run a git sub-command. Returns { success, output } or { success:false, error, stderr, code }.
 */
function runGit(subcmd, opts = {}) {
  try {
    const raw = execSync(`git ${subcmd}`, {
      encoding: 'utf-8',
      stdio: opts.silent ? 'pipe' : ['pipe', 'pipe', 'pipe'],
      cwd: opts.cwd || process.cwd(),
    });
    return { success: true, output: raw.trim() };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      stderr: err.stderr?.toString().trim() || '',
      code: err.status,
    };
  }
}

// Backwards-compat alias used in several helpers below.
const git = runGit;

// ---------------------------------------------------------------------------
// Repository introspection helpers
// ---------------------------------------------------------------------------

/** Assert we are inside a git repo; return the repo root. */
function requireGitRoot() {
  const result = runGit('rev-parse --show-toplevel', { silent: true });
  if (!result.success) {
    die('NOT_GIT_REPO', 'Not in a git repository', {
      suggestion: 'Run this command from within a git repository',
    });
  }
  return result.output;
}

/** Abort if git is too old to support worktrees (< 2.5). */
function requireWorktreeSupport() {
  const probe = runGit('worktree list', { silent: true });
  if (!probe.success && probe.stderr.includes('not a git command')) {
    die('GIT_VERSION_ERROR', 'Git version too old (worktree requires git 2.5+)', {
      suggestion: 'Upgrade git to version 2.5 or newer',
    });
  }
}

/**
 * Detect the "main" branch of a repo by probing a priority list.
 * Checks local refs first, then origin/remote refs.
 */
function detectBaseBranch(cwd) {
  const candidates = ['dev', 'develop', 'main', 'master'];
  for (const candidate of candidates) {
    const local = runGit(`show-ref --verify --quiet refs/heads/${candidate}`, { silent: true, cwd });
    if (local.success) return candidate;
    const remote = runGit(`show-ref --verify --quiet refs/remotes/origin/${candidate}`, { silent: true, cwd });
    if (remote.success) return candidate;
  }
  return 'main';
}

// Walk limit prevents infinite loops when git graph is unusual.
const SUPERPROJECT_WALK_LIMIT = 10;

/**
 * Walk up the superproject chain from gitRoot and return the topmost ancestor.
 * Useful when the CWD is inside a submodule — worktrees should live at the root.
 */
function resolveTopmostSuperproject(gitRoot) {
  let current = gitRoot;
  let topmost = gitRoot;

  for (let depth = 0; depth < SUPERPROJECT_WALK_LIMIT; depth++) {
    const up = runGit('rev-parse --show-superproject-working-tree', { silent: true, cwd: current });
    if (!up.success || !up.output) break;
    topmost = up.output;
    current = up.output;
  }

  return topmost;
}

/**
 * Validate that rootPath can serve as a worktree container directory.
 * Returns { valid: true, path } or { valid: false, error }.
 * Allows paths that don't exist yet if their grandparent exists (mkdir -p one level).
 */
function validateWorktreeRoot(rootPath) {
  if (typeof rootPath !== 'string' || rootPath.trim().length === 0) {
    return { valid: false, error: 'Worktree root path is empty' };
  }
  if (/[\0\r\n]/.test(rootPath)) {
    return { valid: false, error: 'Worktree root contains invalid control characters' };
  }

  const resolved = path.resolve(rootPath);

  if (fs.existsSync(resolved)) {
    if (!fs.statSync(resolved).isDirectory()) {
      return { valid: false, error: `Path exists but is not a directory: ${resolved}` };
    }
    return { valid: true, path: resolved };
  }

  // Parent must exist so we can mkdir the requested dir.
  const parent = path.dirname(resolved);
  if (fs.existsSync(parent)) {
    if (!fs.statSync(parent).isDirectory()) {
      return { valid: false, error: `Parent path is not a directory: ${parent}` };
    }
    return { valid: true, path: resolved };
  }

  // One additional level — grandparent covers cases like /tmp/new/worktrees.
  const grandparent = path.dirname(parent);
  if (fs.existsSync(grandparent)) {
    return { valid: true, path: resolved };
  }

  return { valid: false, error: `Cannot create worktree directory: parent path does not exist: ${parent}` };
}

/**
 * Decide where worktrees will be stored, applying the following priority:
 *   1. --worktree-root flag (explicit Claude decision)
 *   2. WORKTREE_ROOT env var
 *   3. Topmost superproject's worktrees/ (submodule scenario)
 *   4. Monorepo: worktrees/ inside repo root
 *   5. Standalone: sibling worktrees/ next to the repo
 *
 * Returns { dir, source }.
 */
function resolveWorktreeRoot(gitRoot, isMonorepo, flagOverride = null) {
  if (flagOverride) {
    const check = validateWorktreeRoot(flagOverride);
    if (!check.valid) {
      die('INVALID_WORKTREE_ROOT', check.error, {
        suggestion: 'Provide a valid directory path that exists or can be created',
      });
    }
    return { dir: check.path, source: '--worktree-root flag' };
  }

  const envValue = process.env.WORKTREE_ROOT;
  if (envValue) {
    const check = validateWorktreeRoot(envValue);
    if (!check.valid) {
      die('INVALID_WORKTREE_ROOT', check.error, {
        suggestion: 'Fix WORKTREE_ROOT env var or unset it',
      });
    }
    return { dir: check.path, source: 'WORKTREE_ROOT env' };
  }

  const topmost = resolveTopmostSuperproject(gitRoot);
  if (topmost !== gitRoot) {
    return {
      dir: path.join(topmost, 'worktrees'),
      source: `superproject (${path.basename(topmost)})`,
    };
  }

  if (isMonorepo) {
    return { dir: path.join(gitRoot, 'worktrees'), source: 'monorepo internal' };
  }

  return { dir: path.join(path.dirname(gitRoot), 'worktrees'), source: 'sibling directory' };
}

// ---------------------------------------------------------------------------
// Working-tree status helpers
// ---------------------------------------------------------------------------

/** True when the working tree has any uncommitted changes. */
function hasUncommittedChanges() {
  const diff = runGit('diff --quiet', { silent: true });
  const staged = runGit('diff --cached --quiet', { silent: true });
  return !diff.success || !staged.success;
}

/** Counts of modified / staged / untracked files, or null on error. */
function uncommittedChangeSummary() {
  const status = runGit('status --porcelain', { silent: true });
  if (!status.success) return null;

  const lines = status.output.split('\n').filter(Boolean);
  return {
    modified:  lines.filter(l => l.startsWith(' M') || l.startsWith('M ')).length,
    staged:    lines.filter(l => l.startsWith('A ') || l.startsWith('M ') || l.startsWith('D ')).length,
    untracked: lines.filter(l => l.startsWith('??')).length,
    total:     lines.length,
  };
}

// ---------------------------------------------------------------------------
// .gitmodules / env-file helpers
// ---------------------------------------------------------------------------

/** Parse .gitmodules and return an array of { path, name } submodule entries. */
function readSubmodules(gitRoot) {
  const modulesFile = path.join(gitRoot, '.gitmodules');
  if (!fs.existsSync(modulesFile)) return [];

  const text = fs.readFileSync(modulesFile, 'utf-8');
  const entries = [];
  const re = /path\s*=\s*(.+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const subPath = m[1].trim();
    entries.push({ path: subPath, name: path.basename(subPath) });
  }
  return entries;
}

/** Return names of real .env* files (not symlinks) in dir. */
function listEnvFiles(dir) {
  try {
    return fs.readdirSync(dir).filter(f => {
      if (!f.startsWith('.env')) return false;
      const stat = fs.statSync(path.join(dir, f));
      return stat.isFile() && !stat.isSymbolicLink();
    });
  } catch {
    return [];
  }
}

/** Return names of .env*.example template files in dir. */
function listEnvTemplates(dir) {
  try {
    return fs.readdirSync(dir).filter(f => {
      if (!f.startsWith('.env') || !f.endsWith('.example')) return false;
      const stat = fs.statSync(path.join(dir, f));
      return stat.isFile() && !stat.isSymbolicLink();
    });
  } catch {
    return [];
  }
}

/**
 * Copy .env*.example templates from srcDir to destDir, stripping the .example suffix.
 * Returns { copied: [{from, to}], warnings: [string] }.
 */
function copyEnvTemplates(srcDir, destDir) {
  const templates = listEnvTemplates(srcDir);
  const copied = [];
  const warnings = [];

  for (const tpl of templates) {
    const dest = tpl.replace(/\.example$/, '');
    try {
      fs.copyFileSync(path.join(srcDir, tpl), path.join(destDir, dest));
      copied.push({ from: tpl, to: dest });
    } catch (err) {
      warnings.push(`Failed to copy ${tpl}: ${err.message}`);
    }
  }

  return { copied, warnings };
}

// ---------------------------------------------------------------------------
// Branch / worktree state queries
// ---------------------------------------------------------------------------

/** Filter projects whose name or path contains query (case-insensitive). */
function matchProjects(projects, query) {
  const q = query.toLowerCase();
  return projects.filter(p =>
    p.name.toLowerCase().includes(q) || p.path.toLowerCase().includes(q)
  );
}

/** True when branchName is currently checked out in any worktree. */
function isBranchCheckedOut(branchName, cwd) {
  const listing = runGit('worktree list --porcelain', { silent: true, cwd });
  if (!listing.success) return false;
  return listing.output.includes(`branch refs/heads/${branchName}`);
}

/** Returns 'local' | 'remote' | false depending on where the branch lives. */
function locateBranch(branchName, cwd) {
  if (runGit(`show-ref --verify --quiet refs/heads/${branchName}`, { silent: true, cwd }).success) {
    return 'local';
  }
  if (runGit(`show-ref --verify --quiet refs/remotes/origin/${branchName}`, { silent: true, cwd }).success) {
    return 'remote';
  }
  return false;
}

// ---------------------------------------------------------------------------
// Command implementations
// ---------------------------------------------------------------------------

function cmdInfo() {
  const gitRoot = requireGitRoot();
  requireWorktreeSupport();

  const submodules = readSubmodules(gitRoot);
  const isMonorepo = submodules.length > 0;
  const baseBranch = detectBaseBranch(gitRoot);
  const dirty = hasUncommittedChanges();
  const dirtyDetail = dirty ? uncommittedChangeSummary() : null;
  const envFiles = listEnvFiles(gitRoot);
  const wtRoot = resolveWorktreeRoot(gitRoot, isMonorepo);

  // Gather per-project env files for monorepos.
  const projectEnvFiles = {};
  if (isMonorepo) {
    for (const sub of submodules) {
      const subDir = path.join(gitRoot, sub.path);
      if (fs.existsSync(subDir)) {
        const files = listEnvFiles(subDir);
        if (files.length > 0) projectEnvFiles[sub.name] = files;
      }
    }
  }

  emit({
    info: true,
    repoType: isMonorepo ? 'monorepo' : 'standalone',
    gitRoot,
    baseBranch,
    worktreeRoot: wtRoot.dir,
    worktreeRootSource: wtRoot.source,
    projects: isMonorepo ? submodules : [],
    envFiles,
    projectEnvFiles: isMonorepo ? projectEnvFiles : {},
    dirtyState: dirty,
    dirtyDetails: dirtyDetail,
  });
}

function cmdList() {
  requireGitRoot();

  const listing = runGit('worktree list', { silent: true });
  if (!listing.success) {
    die('WORKTREE_LIST_ERROR', 'Failed to list worktrees', {
      suggestion: 'Ensure you are in a git repository',
    });
  }

  const worktrees = listing.output
    .split('\n')
    .filter(Boolean)
    .map(line => {
      const parts = line.split(/\s+/);
      return {
        path:   parts[0],
        commit: parts[1],
        branch: parts[2]?.replace(/[\[\]]/g, '') || 'detached',
      };
    });

  if (useJsonOutput) {
    console.log(JSON.stringify({ success: true, worktrees }, null, 2));
  } else {
    console.log('\n📂 Existing worktrees:');
    for (const wt of worktrees) {
      console.log(`   ${wt.path}`);
      console.log(`      Branch: ${wt.branch} (${wt.commit.slice(0, 7)})`);
    }
  }
}

function cmdCreate() {
  const gitRoot = requireGitRoot();
  requireWorktreeSupport();

  const submodules = readSubmodules(gitRoot);
  const isMonorepo = submodules.length > 0;
  const warnings = [];

  if (branchPrefixWarning) warnings.push(branchPrefixWarning);

  // Validate explicitly requested env files.
  const safeEnvFiles = [];
  for (const entry of requestedEnvFiles) {
    if (!isSafeEnvFileName(entry)) {
      warnings.push(`Skipped unsafe env file entry: ${entry}`);
      continue;
    }
    if (!safeEnvFiles.includes(entry)) safeEnvFiles.push(entry);
  }

  // Resolve project/feature from positional args based on repo type.
  let projectQuery, featureName;
  if (isMonorepo) {
    projectQuery = arg1;
    featureName  = arg2;
    if (!projectQuery || !featureName) {
      die('MISSING_ARGS', 'Both project and feature are required for monorepo', {
        suggestion: 'Usage: node worktree.cjs create <project> <feature> --prefix <type>',
        availableProjects: submodules.map(p => p.name),
      });
    }
  } else {
    featureName = arg1;
    if (!featureName) {
      die('MISSING_FEATURE', 'Feature name is required', {
        suggestion: 'Usage: node worktree.cjs create <feature> --prefix <type>',
      });
    }
  }

  // Warn about dirty state but do not block.
  if (hasUncommittedChanges()) {
    const detail = uncommittedChangeSummary();
    warnings.push(`Uncommitted changes: ${detail.modified} modified, ${detail.staged} staged, ${detail.untracked} untracked`);
  }

  // Resolve project directory for monorepos.
  let workDir = gitRoot;
  let projectPath = '';
  let projectName = '';

  if (isMonorepo) {
    const matches = matchProjects(submodules, projectQuery);

    if (matches.length === 0) {
      die('PROJECT_NOT_FOUND', `Project "${projectQuery}" not found`, {
        suggestion: 'Check available projects with: node worktree.cjs info',
        availableProjects: submodules.map(p => p.name),
      });
    }
    if (matches.length > 1) {
      die('MULTIPLE_PROJECTS_MATCH', `Multiple projects match "${projectQuery}"`, {
        suggestion: 'Use AskUserQuestion to let user select one',
        matchingProjects: matches.map(p => ({ name: p.name, path: p.path })),
      });
    }

    projectPath = matches[0].path;
    projectName = matches[0].name;
    workDir = path.join(gitRoot, projectPath);

    if (!fs.existsSync(workDir)) {
      die('PROJECT_DIR_NOT_FOUND', `Project directory not found: ${workDir}`, {
        suggestion: 'Initialize submodules: git submodule update --init',
      });
    }
  }

  // Sanitise feature name → git-safe branch label.
  const sanitized = sanitizeFeatureName(featureName, noPrefix);
  if (!sanitized) {
    die('INVALID_FEATURE_NAME', 'Feature name became empty after sanitization', {
      suggestion: 'Use letters/numbers in feature name (example: "login-validation")',
    });
  }

  // Emit a warning when the name had to be changed.
  const expected = noPrefix
    ? featureName.replace(/\s+/g, '-')
    : featureName.toLowerCase().replace(/\s+/g, '-');
  if (sanitized !== expected) {
    warnings.push(`Feature name sanitized: "${featureName}" → "${sanitized}"`);
  }

  const branchName = noPrefix ? sanitized : `${branchPrefix}/${sanitized}`;
  const baseBranch = detectBaseBranch(workDir);

  if (isBranchCheckedOut(branchName, workDir)) {
    die('BRANCH_CHECKED_OUT', `Branch "${branchName}" is already checked out in another worktree`, {
      suggestion: 'Use a different feature name or remove the existing worktree',
    });
  }

  // Determine the container directory for the new worktree.
  const wtRoot = resolveWorktreeRoot(gitRoot, isMonorepo, explicitWorktreeRoot);
  const worktreesDir = wtRoot.dir;

  // Build a filesystem-safe worktree name: flatten slashes, prefix with repo/project name.
  const repoLabel = path.basename(gitRoot);
  const flatLabel = flattenForDirectoryName(sanitized);
  const worktreeName = isMonorepo ? `${projectName}-${flatLabel}` : `${repoLabel}-${flatLabel}`;
  const worktreePath = path.join(worktreesDir, worktreeName);

  if (fs.existsSync(worktreePath)) {
    die('WORKTREE_EXISTS', `Worktree already exists: ${worktreePath}`, {
      suggestion: `To use: cd ${worktreePath} && claude\nTo remove: git worktree remove ${worktreePath}`,
    });
  }

  const branchLocation = locateBranch(branchName, workDir);

  // Dry-run: report what would happen without touching the filesystem.
  if (isDryRun) {
    emit({
      success: true,
      dryRun: true,
      message: 'Dry run - no changes made',
      wouldCreate: {
        worktreePath,
        worktreeRootSource: wtRoot.source,
        branch: branchName,
        baseBranch,
        branchExists: !!branchLocation,
        project: isMonorepo ? projectName : null,
        envFilesToCopy: safeEnvFiles.length > 0 ? safeEnvFiles : undefined,
      },
      warnings: warnings.length > 0 ? warnings : undefined,
    });
    return;
  }

  // Ensure the container directory exists.
  try {
    fs.mkdirSync(worktreesDir, { recursive: true });
  } catch {
    die('MKDIR_FAILED', `Failed to create worktrees directory: ${worktreesDir}`, {
      suggestion: 'Check write permissions',
    });
  }

  // Fetch remote branch before adding the worktree.
  if (branchLocation === 'remote') {
    const fetched = runGit(`fetch origin ${branchName}`, { silent: true, cwd: workDir });
    if (!fetched.success) {
      die('FETCH_FAILED', `Failed to fetch branch from remote: ${branchName}`, {
        suggestion: 'Check network connection and remote repository access',
      });
    }
  }

  // Add the worktree — either check out existing branch or create a new one.
  const addResult = branchLocation
    ? runGit(`worktree add "${worktreePath}" ${branchName}`, { cwd: workDir })
    : runGit(`worktree add -b ${branchName} "${worktreePath}" ${baseBranch}`, { cwd: workDir });

  if (!addResult.success) {
    die('WORKTREE_CREATE_FAILED', 'Failed to create worktree', {
      suggestion: addResult.stderr || addResult.error,
      gitError: addResult.stderr,
    });
  }

  // Copy .env*.example templates into the new worktree.
  const sourceDir = isMonorepo ? workDir : gitRoot;
  const tplResult = copyEnvTemplates(sourceDir, worktreePath);
  tplResult.warnings.forEach(w => warnings.push(w));

  // Also honour legacy --env flag entries.
  const copiedFiles = tplResult.copied.map(c => c.to);
  for (const envFile of safeEnvFiles) {
    const src = path.join(sourceDir, envFile);
    const dst = path.join(worktreePath, envFile);
    if (fs.existsSync(src)) {
      try {
        fs.copyFileSync(src, dst);
        if (!copiedFiles.includes(envFile)) copiedFiles.push(envFile);
      } catch (err) {
        warnings.push(`Failed to copy ${envFile}: ${err.message}`);
      }
    } else {
      warnings.push(`Env file not found: ${envFile}`);
    }
  }

  emit({
    success: true,
    message: 'Worktree created successfully!',
    worktreePath,
    worktreeRootSource: wtRoot.source,
    branch: branchName,
    baseBranch,
    project: isMonorepo ? projectName : null,
    envFilesCopied: copiedFiles,
    envTemplatesCopied: tplResult.copied,
    warnings: warnings.length > 0 ? warnings : undefined,
  });
}

function cmdRemove() {
  if (!arg1) {
    die('MISSING_WORKTREE', 'Worktree name or path is required', {
      suggestion: 'Usage: node worktree.cjs remove <name-or-path>\nUse "node worktree.cjs list" to see available worktrees',
    });
  }

  requireGitRoot();
  requireWorktreeSupport();

  const porcelain = runGit('worktree list --porcelain', { silent: true });
  if (!porcelain.success) {
    die('WORKTREE_LIST_ERROR', 'Failed to list worktrees');
  }

  // Parse porcelain output into structured entries.
  const all = [];
  let entry = {};
  for (const line of porcelain.output.split('\n')) {
    if (line.startsWith('worktree ')) {
      if (entry.path) all.push(entry);
      entry = { path: line.replace('worktree ', '') };
    } else if (line.startsWith('branch ')) {
      entry.branch = line.replace('branch refs/heads/', '');
    }
  }
  if (entry.path) all.push(entry);

  // Exclude the main worktree (the bare repo .git directory).
  const candidates = all.filter(w => !w.path.includes('.git/'));
  const needle = arg1.toLowerCase();

  // Three-tier match: exact → prefix → contains (prefix only for short needles).
  const exactHits = candidates.filter(w => {
    const n = path.basename(w.path).toLowerCase();
    return n === needle || w.path.toLowerCase() === needle || (w.branch || '').toLowerCase() === needle;
  });
  const prefixHits = candidates.filter(w => {
    const n = path.basename(w.path).toLowerCase();
    return n.startsWith(needle) || w.path.toLowerCase().startsWith(needle) || (w.branch || '').toLowerCase().startsWith(needle);
  });
  const containsHits = candidates.filter(w => {
    const n = path.basename(w.path).toLowerCase();
    return n.includes(needle) || w.path.toLowerCase().includes(needle) || (w.branch || '').toLowerCase().includes(needle);
  });

  let hits = exactHits;
  if (hits.length === 0) hits = prefixHits;
  if (hits.length === 0 && needle.length >= 4) hits = containsHits;

  if (hits.length === 0) {
    die('WORKTREE_NOT_FOUND', `No worktree matching "${arg1}" found`, {
      suggestion: 'Use "node worktree.cjs list" to see available worktrees',
      availableWorktrees: candidates.map(w => path.basename(w.path)),
    });
  }
  if (hits.length > 1) {
    die('MULTIPLE_WORKTREES_MATCH', `Multiple worktrees match "${arg1}"`, {
      suggestion: 'Be more specific or use full path',
      matchingWorktrees: hits.map(w => ({ name: path.basename(w.path), path: w.path, branch: w.branch })),
    });
  }

  const target = hits[0];
  const targetPath = target.path;
  const targetBranch = target.branch;

  if (isDryRun) {
    emit({
      success: true,
      dryRun: true,
      message: 'Dry run - no changes made',
      wouldRemove: {
        worktreePath: targetPath,
        branch: targetBranch,
        deleteBranch: !!targetBranch,
      },
    });
    return;
  }

  const rmResult = runGit(`worktree remove "${targetPath}" --force`, { silent: true });
  if (!rmResult.success) {
    die('WORKTREE_REMOVE_FAILED', `Failed to remove worktree: ${targetPath}`, {
      suggestion: rmResult.stderr || 'Check if the worktree has uncommitted changes',
      gitError: rmResult.stderr,
    });
  }

  // Attempt to delete the branch; keep it if git declines (unmerged work).
  let branchDeleted = false;
  let branchKeptNote = null;
  if (targetBranch) {
    const del = runGit(`branch -d "${targetBranch}"`, { silent: true });
    if (del.success) {
      branchDeleted = true;
    } else {
      branchKeptNote = `Branch kept: ${targetBranch} (${del.stderr || 'not fully merged'})`;
    }
  }

  emit({
    success: true,
    message: 'Worktree removed successfully!',
    removedPath: targetPath,
    branchDeleted: branchDeleted ? targetBranch : null,
    branchKept: !branchDeleted && targetBranch ? targetBranch : null,
    warnings: branchKeptNote ? [branchKeptNote] : undefined,
  });
}

function showHelp() {
  const help = `Git Worktree Manager for Takumi Agent Kit

Usage: node worktree.cjs <command> [options]

Commands:
  create <project> <feature>  Create a new worktree (project optional for standalone)
  remove <name-or-path>       Remove a worktree and its branch
  info                        Get repo info (type, projects, env files)
  list                        List existing worktrees

Options:
  --prefix <type>        Branch prefix (feat|fix|refactor|docs|test|chore|perf)
  --worktree-root <path> Explicit worktree directory
  --json                 Output in JSON format for LLM consumption
  --env <files>          Comma-separated list of .env files to copy (legacy)
  --dry-run              Show what would be done without executing
  --no-prefix            Skip branch prefix and preserve original case
  --help, -h             Show this help message`;
  console.log(help);
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
function main() {
  if (command === '--help' || command === '-h' || command === 'help') {
    showHelp();
    return;
  }

  switch (command) {
    case 'create': cmdCreate(); break;
    case 'remove': cmdRemove(); break;
    case 'info':   cmdInfo();   break;
    case 'list':   cmdList();   break;
    default:
      die('UNKNOWN_COMMAND', `Unknown command: ${command || '(none)'}`, {
        suggestion: 'Available commands: create, remove, info, list. Use --help for usage.',
      });
  }
}

main();
