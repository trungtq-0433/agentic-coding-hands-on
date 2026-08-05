/**
 * Step 1 — SDD (Spec-Driven Development) detection.
 *
 * Pure-logic core is exported for unit testing; CLI shim at the bottom.
 * Scans the repo for Spec-Driven-Development signals and writes sdd-detection.json.
 *
 * Usage (CLI):
 *   node detect-sdd.mjs --repo-root <path> --output-path <path> [--spec-folder <path>]
 *
 * Stdout contract:
 *   done: step-1 → <abs path>   |   skip: step-1 (artifact exists)
 *   [spec-folder: <path>/ (verified, SDD detection skipped)]   (only with --spec-folder)
 *   Status: DONE | Status: DONE_WITH_CONCERNS — <reason> | Status: BLOCKED — <reason>
 *
 * Exit codes: 0 = DONE / DONE_WITH_CONCERNS / skip;  non-zero = BLOCKED.
 *
 * FILE-SIZE NOTE (deviates from the repo's <200-line guideline, intentionally):
 * a 1:1 behavioural port of detect_sdd_lib.py + detect_sdd.py kept in a single module
 * so the pure core and CLI shim trace to one Python source pair. Splitting further would
 * fragment the parity mapping without reducing complexity. Byte-for-byte equivalence with
 * the Python source is locked by __tests__/parity.test.mjs.
 */

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

// ---------------------------------------------------------------------------
// Constants (mirror detect_sdd_lib.py)
// ---------------------------------------------------------------------------

const PRUNE_DIRS = new Set([
  'node_modules', '.venv', 'venv', '.git', '.hg', '.svn',
  'dist', 'build', '.next', '.nuxt', 'out', 'target', 'vendor',
  '__pycache__', '.cache', '.pytest_cache', '.tox', '.gradle',
  '.idea', '.vscode',
]);

const PRIMARY_DIRS = ['specs', '.specify', 'docs/specs'];
const PRIMARY_ROOT_FILES = [
  'spec.md', 'SPEC.md', 'specs.md', 'SPECIFICATION.md',
  'specify.config.yml', 'specify.yaml',
];

const SPEC_FILENAME_PREFIXES = [
  'feature-', 'user-story-', 'us-', 'fr-', 'scr-', 'perm-',
];

// Order matches Python dict — first matching keyword wins per heading line.
const HEADING_KEYWORD_KIND = [
  ['featurelist', 'feature-list'],
  ['userstories', 'user-stories'],
  ['screenlist', 'screen-list'],
  ['screenflow', 'screen-list'],
  ['datamodel', 'data-model'],
  ['systemoverview', 'system-overview'],
  ['permissions', 'permissions'],
  ['backgroundlogic', 'background-logic'],
  ['routelist', 'route-list'],
];
const HEADING_KINDS = new Set(HEADING_KEYWORD_KIND.map(([, kind]) => kind));

const TOOLING_MARKERS = [
  /\btkm:rebuild-spec\b/,
  /\bspeckit\b/,
  /\bspecify\s+(init|check|run|install|plan)\b/,
  /\bnpx\s+specify\b/,
];
const TOOLING_SEARCH_FILES = ['package.json', 'pyproject.toml', 'CLAUDE.md'];

const PLAN_DIR_KEYWORDS = [
  'featurelist', 'userstories', 'screenlist', 'screenflow',
  'datamodel', 'feature-spec', 'routelist', 'backgroundlogic', 'permissions',
];

// ---------------------------------------------------------------------------
// Pruned filesystem iteration (mirrors _walk / _iter_files / _iter_md)
// ---------------------------------------------------------------------------

/**
 * Yields absolute file paths under root (depth-first, iterative).
 * Skips PRUNE_DIRS at any depth. Max depth measured from root (same as Python).
 *
 * @param {string} root - Absolute directory path to walk.
 * @param {number} maxDepth - Maximum depth below root (default 6).
 * @param {(name: string) => boolean} fileFilter - True to include a file.
 * @yields {string} Absolute file paths.
 */
function* _walk(root, maxDepth = 6, fileFilter = () => true) {
  let rootDepthParts;
  try {
    const stat = fs.statSync(root);
    if (!stat.isDirectory()) return;
    rootDepthParts = root.split(path.sep).length;
  } catch {
    return;
  }

  const stack = [root];
  while (stack.length > 0) {
    const cur = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(cur, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const full = path.join(cur, entry.name);
      if (entry.isDirectory()) {
        if (PRUNE_DIRS.has(entry.name)) continue;
        const depth = full.split(path.sep).length - rootDepthParts;
        if (depth >= maxDepth) continue;
        stack.push(full);
      } else if (entry.isFile() && fileFilter(entry.name)) {
        yield full;
      }
    }
  }
}

function* _iterFiles(root, maxDepth = 6) {
  yield* _walk(root, maxDepth, () => true);
}

function* _iterMd(root, maxDepth = 6) {
  yield* _walk(root, maxDepth, (name) => name.toLowerCase().endsWith('.md'));
}

function _hasAnyFile(dir) {
  for (const _ of _iterFiles(dir)) return true; // eslint-disable-line no-unused-vars
  return false;
}

function _hasMdFile(dir) {
  for (const _ of _iterMd(dir)) return true; // eslint-disable-line no-unused-vars
  return false;
}

// ---------------------------------------------------------------------------
// Primary detection
// ---------------------------------------------------------------------------

/**
 * @param {string} repoRoot - Absolute resolved repo root.
 * @returns {{ kind: string, path: string, weight: number }[]}
 */
export function primarySignals(repoRoot) {
  const hits = [];

  for (const rel of PRIMARY_DIRS) {
    const d = path.join(repoRoot, rel);
    let stat;
    try { stat = fs.statSync(d); } catch { continue; }
    if (!stat.isDirectory()) continue;

    const hasContent = rel === '.specify' ? _hasAnyFile(d) : _hasMdFile(d);
    if (hasContent) {
      hits.push({ kind: 'specs-dir', path: `${rel}/`, weight: 3 });
    }
  }

  for (const fname of PRIMARY_ROOT_FILES) {
    const p = path.join(repoRoot, fname);
    try {
      const stat = fs.statSync(p);
      if (stat.isFile()) {
        hits.push({ kind: 'spec-file', path: fname, weight: 2 });
      }
    } catch {
      // file absent — skip
    }
  }

  return hits;
}

// ---------------------------------------------------------------------------
// Secondary detection
// ---------------------------------------------------------------------------

/**
 * @param {string} repoRoot - Absolute resolved repo root.
 * @returns {{ kind: string, path: string, weight: number }[]}
 */
export function secondarySignals(repoRoot) {
  const hits = [];
  hits.push(..._filenamePrefixSignals(repoRoot));
  hits.push(..._headingKeywordSignals(repoRoot));
  hits.push(..._toolingMarkerSignals(repoRoot));
  hits.push(..._planDirSignals(repoRoot));
  return hits;
}

function _filenamePrefixSignals(repoRoot) {
  const out = [];
  for (const searchRoot of ['docs', 'specs']) {
    const base = path.join(repoRoot, searchRoot);
    let stat;
    try { stat = fs.statSync(base); } catch { continue; }
    if (!stat.isDirectory()) continue;

    for (const absPath of _iterMd(base, 6)) {
      const name = path.basename(absPath).toLowerCase();
      if (SPEC_FILENAME_PREFIXES.some((prefix) => name.startsWith(prefix))) {
        const rel = path.relative(repoRoot, absPath).replace(/\\/g, '/');
        out.push({ kind: 'spec-file', path: rel, weight: 1 });
      }
    }
  }
  return out;
}

function _headingKeywordSignals(repoRoot) {
  const out = [];
  for (const searchRoot of ['docs', 'specs']) {
    const base = path.join(repoRoot, searchRoot);
    let stat;
    try { stat = fs.statSync(base); } catch { continue; }
    if (!stat.isDirectory()) continue;

    for (const absPath of _iterMd(base, 6)) {
      let text;
      try {
        text = fs.readFileSync(absPath, 'utf8');
      } catch {
        continue;
      }
      const lines = text.split('\n');
      let matched = false;
      for (const line of lines) {
        if (!line.startsWith('#')) continue;
        // Strip leading # chars + spaces; lowercase; remove spaces.
        const stripped = line.replace(/^#+/, '').trim().toLowerCase().replace(/ /g, '');
        for (const [kw, kind] of HEADING_KEYWORD_KIND) {
          if (stripped.includes(kw)) {
            const rel = path.relative(repoRoot, absPath).replace(/\\/g, '/');
            out.push({ kind, path: rel, weight: 1 });
            matched = true;
            break; // one keyword per heading line
          }
        }
        if (matched) break; // one heading-keyword hit per file
      }
    }
  }
  return out;
}

function _toolingMarkerSignals(repoRoot) {
  const out = [];
  const candidates = TOOLING_SEARCH_FILES.map((fn) => path.join(repoRoot, fn));

  const workflowsDir = path.join(repoRoot, '.github', 'workflows');
  try {
    const wfStat = fs.statSync(workflowsDir);
    if (wfStat.isDirectory()) {
      let entries;
      try { entries = fs.readdirSync(workflowsDir, { withFileTypes: true }); } catch { entries = []; }
      for (const entry of entries) {
        if (!entry.isFile()) continue;
        const ext = path.extname(entry.name).toLowerCase();
        if (['.yml', '.yaml', '.json', '.md'].includes(ext)) {
          candidates.push(path.join(workflowsDir, entry.name));
        }
      }
    }
  } catch {
    // .github/workflows does not exist — fine
  }

  for (const p of candidates) {
    let stat;
    try { stat = fs.statSync(p); } catch { continue; }
    if (!stat.isFile()) continue;

    let text;
    try { text = fs.readFileSync(p, 'utf8'); } catch { continue; }

    for (const marker of TOOLING_MARKERS) {
      const m = text.match(marker);
      if (m) {
        // Compute 1-based line number of match.
        const matchIdx = text.search(marker);
        const lineNo = text.slice(0, matchIdx).split('\n').length;
        const rel = path.relative(repoRoot, p).replace(/\\/g, '/');
        out.push({ kind: 'spec-file', path: `${rel}:${lineNo}`, weight: 1 });
        break; // one marker hit per file
      }
    }
  }
  return out;
}

function _planDirSignals(repoRoot) {
  const plansDir = path.join(repoRoot, 'plans');
  let stat;
  try { stat = fs.statSync(plansDir); } catch { return []; }
  if (!stat.isDirectory()) return [];

  const out = [];
  let children;
  try { children = fs.readdirSync(plansDir, { withFileTypes: true }); } catch { return []; }

  for (const child of children) {
    if (!child.isDirectory() || PRUNE_DIRS.has(child.name)) continue;
    const childDir = path.join(plansDir, child.name);

    const planMd = path.join(childDir, 'plan.md');
    try {
      const ps = fs.statSync(planMd);
      if (!ps.isFile()) continue;
    } catch {
      continue;
    }

    // Need at least one phase-*.md sibling.
    let hasPhase = false;
    try {
      const siblings = fs.readdirSync(childDir, { withFileTypes: true });
      hasPhase = siblings.some(
        (e) => e.isFile() && e.name.startsWith('phase-') && e.name.endsWith('.md'),
      );
    } catch {
      continue;
    }
    if (!hasPhase) continue;

    let text;
    try { text = fs.readFileSync(planMd, 'utf8'); } catch { continue; }
    const normalized = text.toLowerCase().replace(/ /g, '');

    const distinct = new Set(PLAN_DIR_KEYWORDS.filter((kw) => normalized.includes(kw)));
    if (distinct.size >= 2) {
      const rel = path.relative(repoRoot, planMd).replace(/\\/g, '/');
      out.push({ kind: 'spec-file', path: rel, weight: 1 });
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Classification + specsRoot
// ---------------------------------------------------------------------------

/**
 * Count how many distinct secondary categories fired.
 *
 * Categories (mirrors Python secondary_categories()):
 *   1. filename-prefix: kind=spec-file, path starts with docs/ or specs/
 *   2. heading:         kind in HEADING_KINDS
 *   3. tooling:         kind=spec-file, path contains ":"
 *   4. plan-dir:        kind=spec-file, path starts with plans/
 *
 * @param {{ kind: string, path: string }[]} secondary
 * @returns {number}
 */
export function secondaryCategories(secondary) {
  let firedFilename = false;
  let firedHeading = false;
  let firedTooling = false;
  let firedPlanDir = false;

  for (const sig of secondary) {
    if (sig.kind === 'spec-file' && sig.path.startsWith('plans/')) {
      firedPlanDir = true;
    } else if (sig.kind === 'spec-file' && sig.path.includes(':')) {
      firedTooling = true;
    } else if (
      sig.kind === 'spec-file' &&
      (sig.path.startsWith('docs/') || sig.path.startsWith('specs/'))
    ) {
      firedFilename = true;
    } else if (HEADING_KINDS.has(sig.kind)) {
      firedHeading = true;
    }
  }

  return [firedFilename, firedHeading, firedTooling, firedPlanDir].filter(Boolean).length;
}

/**
 * Apply the documented rule: >=1 PRIMARY OR >=2 distinct SECONDARY categories.
 *
 * @param {{ kind: string, path: string }[]} primary
 * @param {{ kind: string, path: string }[]} secondary
 * @returns {boolean}
 */
export function classify(primary, secondary) {
  if (primary.length > 0) return true;
  return secondaryCategories(secondary) >= 2;
}

/**
 * Pick the first present + content-bearing specs directory.
 *
 * @param {string} repoRoot - Absolute resolved repo root.
 * @returns {string} Relative path with trailing slash, or empty string.
 */
export function resolveSpecsRoot(repoRoot) {
  const specsDir = path.join(repoRoot, 'specs');
  try {
    if (fs.statSync(specsDir).isDirectory() && _hasMdFile(specsDir)) return 'specs/';
  } catch { /* absent */ }

  const docsSpecsDir = path.join(repoRoot, 'docs', 'specs');
  try {
    if (fs.statSync(docsSpecsDir).isDirectory() && _hasMdFile(docsSpecsDir)) return 'docs/specs/';
  } catch { /* absent */ }

  const specifyDir = path.join(repoRoot, '.specify');
  try {
    if (fs.statSync(specifyDir).isDirectory() && _hasAnyFile(specifyDir)) return '.specify/';
  } catch { /* absent */ }

  return '';
}

// ---------------------------------------------------------------------------
// Spec-folder override verification + normalization
// ---------------------------------------------------------------------------

/**
 * Verify a user-supplied spec folder relative to repoRoot.
 *
 * @param {string} repoRoot - Absolute resolved repo root.
 * @param {string} specFolder - User-supplied relative path.
 * @returns {{ ok: boolean, reason: string }}
 */
export function verifySpecFolder(repoRoot, specFolder) {
  if (!specFolder || specFolder.includes('\x00')) {
    return { ok: false, reason: 'spec folder path is empty or contains null bytes' };
  }

  if (path.isAbsolute(specFolder)) {
    return {
      ok: false,
      reason: `spec folder must be relative to the repo root (got: ${specFolder})`,
    };
  }

  // Check for ".." components — mirrors Python's `".." in candidate.parts`.
  const parts = specFolder.replace(/\\/g, '/').split('/').filter(Boolean);
  if (parts.includes('..')) {
    return {
      ok: false,
      reason: `spec folder must not contain '..' (got: ${specFolder})`,
    };
  }

  const repoResolved = fs.realpathSync(repoRoot);
  // Use path.resolve to mimic Python's (repo_resolved / candidate).resolve(strict=False)
  const folderResolved = path.resolve(repoResolved, specFolder);

  // Ensure folder stays inside repo root.
  const rel = path.relative(repoResolved, folderResolved);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    return {
      ok: false,
      reason: `spec folder escapes repository root: ${specFolder}`,
    };
  }

  // Must exist as a directory.
  let folderStat;
  try { folderStat = fs.statSync(folderResolved); } catch {
    return {
      ok: false,
      reason: `spec folder does not exist or is not a directory: ${specFolder}`,
    };
  }
  if (!folderStat.isDirectory()) {
    return {
      ok: false,
      reason: `spec folder does not exist or is not a directory: ${specFolder}`,
    };
  }

  // Require >=1 .md whose resolved path stays inside repo_resolved.
  // Re-resolve each match so symlinks pointing out of repo cannot satisfy the bar.
  for (const absPath of _iterMd(folderResolved)) {
    let realPath;
    try { realPath = fs.realpathSync(absPath); } catch { continue; }
    const mdRel = path.relative(repoResolved, realPath);
    if (!mdRel.startsWith('..') && !path.isAbsolute(mdRel)) {
      return { ok: true, reason: '' };
    }
  }

  return {
    ok: false,
    reason: `spec folder contains no in-repo .md files: ${specFolder}`,
  };
}

/**
 * Normalize a user-supplied spec folder to the `<path>/` form used in JSON output.
 *
 * @param {string} specFolder
 * @returns {string}
 */
export function normalizeSpecFolder(specFolder) {
  return specFolder.replace(/\\/g, '/').replace(/\/+$/, '') + '/';
}

// ---------------------------------------------------------------------------
// Pure detection core (exported for unit testing without fs side-effects of CLI)
// ---------------------------------------------------------------------------

/**
 * Run the full SDD detection pipeline.
 *
 * @param {{ repoRoot: string, specFolder?: string | null }} opts
 * @returns {{
 *   isSDD: boolean,
 *   signals: { kind: string, path: string, weight: number }[],
 *   specsRoot: string,
 *   specFolderVerified?: boolean,
 *   blockedReason?: string,
 * }}
 */
export function detectSdd({ repoRoot, specFolder = null }) {
  const resolvedRoot = fs.realpathSync(repoRoot);

  if (specFolder != null) {
    const { ok, reason } = verifySpecFolder(resolvedRoot, specFolder);
    if (!ok) {
      return {
        isSDD: false,
        signals: [],
        specsRoot: '',
        specFolderVerified: false,
        blockedReason: `--spec-folder verification failed: ${reason}`,
      };
    }
    const specsRoot = normalizeSpecFolder(specFolder);
    return {
      isSDD: true,
      signals: [{ kind: 'specs-dir', path: specsRoot, weight: 3 }],
      specsRoot,
      specFolderVerified: true,
    };
  }

  const primary = primarySignals(resolvedRoot);
  const secondary = secondarySignals(resolvedRoot);
  const isSDD = classify(primary, secondary);
  const specsRoot = isSDD ? resolveSpecsRoot(resolvedRoot) : '';

  return {
    isSDD,
    signals: [...primary, ...secondary],
    specsRoot,
  };
}

// ---------------------------------------------------------------------------
// JSON serialization — byte-identical to Python's json.dump(payload, fh, indent=2) + "\n"
// ---------------------------------------------------------------------------

/**
 * Serialize a detection payload to JSON matching Python's output exactly:
 *   json.dump(payload, fh, indent=2) followed by a newline.
 *
 * Python's json.dump with indent=2 uses ", " and ": " separators by default
 * and writes keys in insertion order. JS JSON.stringify(obj, null, 2) produces
 * the same format. The trailing newline is written explicitly after json.dump.
 *
 * @param {{ isSDD: boolean, signals: object[], specsRoot: string }} payload
 * @returns {string}
 */
function serializePayload(payload) {
  return JSON.stringify(payload, null, 2) + '\n';
}

// ---------------------------------------------------------------------------
// Atomic write (mirrors _atomic_write_json)
// ---------------------------------------------------------------------------

/**
 * Write JSON payload to target atomically via tempfile + rename.
 *
 * @param {string} target - Absolute path of the destination file.
 * @param {{ isSDD: boolean, signals: object[], specsRoot: string }} payload
 */
function atomicWriteJson(target, payload) {
  fs.mkdirSync(path.dirname(target), { recursive: true });

  const suffix = crypto.randomBytes(6).toString('hex');
  const tmpPath = `${target}.${suffix}.tmp`;

  try {
    fs.writeFileSync(tmpPath, serializePayload(payload), 'utf8');
    fs.renameSync(tmpPath, target);
  } catch (err) {
    try { fs.unlinkSync(tmpPath); } catch { /* ignore cleanup error */ }
    throw err;
  }
}

// ---------------------------------------------------------------------------
// CLI shim
// ---------------------------------------------------------------------------

function printStatus(status, reason = '') {
  if (reason) {
    // Mirrors Python: f"Status: {status} — {reason}"  (em dash U+2014)
    console.log(`Status: ${status} — ${reason}`);
  } else {
    console.log(`Status: ${status}`);
  }
}

function parseArgs(argv) {
  const args = {
    repoRoot: process.cwd(),
    outputPath: 'plans/improvement-proposal/sdd-detection.json',
    specFolder: null,
  };

  const positional = argv.slice(2);
  for (let i = 0; i < positional.length; i++) {
    const flag = positional[i];
    if (flag === '--repo-root') {
      args.repoRoot = positional[++i];
    } else if (flag === '--output-path') {
      args.outputPath = positional[++i];
    } else if (flag === '--spec-folder') {
      // Capture the next token even if it is an empty string — mirrors Python's
      // argparse which stores "" (not None) for `--spec-folder ""`.
      args.specFolder = positional[++i] ?? '';
    } else {
      console.error(`Unknown argument: ${flag}`);
      process.exit(1);
    }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv);
  const repoRoot = path.resolve(args.repoRoot);
  const outputPath = path.resolve(args.outputPath);

  // Idempotency — skip when output already non-empty.
  try {
    const stat = fs.statSync(outputPath);
    if (stat.size > 0) {
      console.log('skip: step-1 (artifact exists)');
      printStatus('DONE');
      process.exit(0);
    }
  } catch {
    // file absent — proceed
  }

  // User-supplied spec folder override.
  // null means not provided; "" means provided as empty string (must BLOCK).
  if (args.specFolder !== null) {
    const { ok, reason } = verifySpecFolder(repoRoot, args.specFolder);
    if (!ok) {
      printStatus('BLOCKED', `--spec-folder verification failed: ${reason}`);
      process.exit(2);
    }
    const specsRoot = normalizeSpecFolder(args.specFolder);
    const payload = {
      isSDD: true,
      signals: [{ kind: 'specs-dir', path: specsRoot, weight: 3 }],
      specsRoot,
    };
    try {
      atomicWriteJson(outputPath, payload);
    } catch (err) {
      printStatus('BLOCKED', `write failed: ${err.message}`);
      process.exit(2);
    }
    console.log(`done: step-1 → ${outputPath}`);
    console.log(`spec-folder: ${specsRoot} (verified, SDD detection skipped)`);
    printStatus('DONE');
    process.exit(0);
  }

  // Auto-detection.
  let primary, secondary, isSDD, specsRoot;
  try {
    primary = primarySignals(repoRoot);
    secondary = secondarySignals(repoRoot);
    isSDD = classify(primary, secondary);
    specsRoot = isSDD ? resolveSpecsRoot(repoRoot) : '';
  } catch (exc) {
    // Fallback per sdd-detection.md "Fallback" section.
    const fallback = { isSDD: false, signals: [], specsRoot: '' };
    try {
      atomicWriteJson(outputPath, fallback);
    } catch (writeErr) {
      printStatus('BLOCKED', `fs error during fallback write: ${writeErr.message}`);
      process.exit(2);
    }
    console.log(`done: step-1 → ${outputPath}`);
    printStatus('DONE_WITH_CONCERNS', `fs error: ${exc.message}`);
    process.exit(0);
  }

  const payload = {
    isSDD,
    signals: [...primary, ...secondary],
    specsRoot,
  };

  try {
    atomicWriteJson(outputPath, payload);
  } catch (err) {
    printStatus('BLOCKED', `write failed: ${err.message}`);
    process.exit(2);
  }

  console.log(`done: step-1 → ${outputPath}`);
  printStatus('DONE');
  process.exit(0);
}

// Only run as CLI when invoked directly.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
