#!/usr/bin/env node
/**
 * privacy-checker.cjs — Pure pattern-matching core for sensitive-file detection.
 * No stdin/stdout, no exit codes — just decisions.
 * Shared by privacy-block.cjs and any other runtime that needs the same guard.
 *
 * @module privacy-checker
 */

const path = require('path');
const fs = require('fs');

// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

const APPROVED_PREFIX = 'APPROVED:';

// Files that look sensitive by name but are safe to read (docs/templates)
const SAFE_PATTERNS = [
  /\.example$/i,   // .env.example, config.example
  /\.sample$/i,    // .env.sample
  /\.template$/i,  // .env.template
];

// Patterns that flag a path as requiring user approval before read
const PRIVACY_PATTERNS = [
  /^\.env$/,              // .env
  /^\.env\./,             // .env.local, .env.production, etc.
  /\.env$/,               // path/to/.env
  /\/\.env\./,            // path/to/.env.local
  /credentials/i,         // credentials.json, etc.
  /secrets?\.ya?ml$/i,    // secrets.yaml, secret.yml
  /\.pem$/,               // Private keys
  /\.key$/,               // Private keys
  /id_rsa/,               // SSH keys
  /id_ed25519/,           // SSH keys
  /secrets?\.(json|toml)$/i,        // secrets.json, secret.toml
  /service[-_]?account.*\.json$/i,  // GCP service-account keys
];

// ═══════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * True when the path is an example/sample/template — never blocked.
 * @param {string} testPath - Path to check
 * @returns {boolean} true if file matches safe patterns
 */
function isSafeFile(testPath) {
  if (!testPath) return false;
  const basename = path.basename(testPath);
  return SAFE_PATTERNS.some(p => p.test(basename));
}

/**
 * True when the path carries the APPROVED: prefix set by the approval flow.
 * @param {string} testPath - Path to check
 * @returns {boolean} true if path starts with APPROVED:
 */
function hasApprovalPrefix(testPath) {
  return testPath && testPath.startsWith(APPROVED_PREFIX);
}

/**
 * Remove the APPROVED: prefix to recover the real file path.
 * @param {string} testPath - Path to process
 * @returns {string} Path without APPROVED: prefix
 */
function stripApprovalPrefix(testPath) {
  if (hasApprovalPrefix(testPath)) {
    return testPath.slice(APPROVED_PREFIX.length);
  }
  return testPath;
}

/**
 * True when a stripped path attempts traversal (..) or is absolute — warn but still allow.
 * @param {string} strippedPath - Path after stripping APPROVED: prefix
 * @returns {boolean} true if path looks suspicious
 */
function isSuspiciousPath(strippedPath) {
  return strippedPath.includes('..') || path.isAbsolute(strippedPath);
}

/**
 * True when the path matches a privacy-sensitive pattern.
 * Decodes URI components to catch obfuscated paths before pattern matching.
 * @param {string} testPath - Path to check
 * @returns {boolean} true if path matches privacy-sensitive patterns
 */
function isPrivacySensitive(testPath) {
  if (!testPath) return false;

  // Strip APPROVED: before pattern matching so the prefix doesn't confuse regexes
  const cleanPath = stripApprovalPrefix(testPath);
  let normalized = cleanPath.replace(/\\/g, '/');

  // Decode URI components (%2e = '.') to foil obfuscated paths
  try {
    normalized = decodeURIComponent(normalized);
  } catch (e) {
    // Malformed encoding — proceed with the raw value
  }

  // Safe-patterns win — example/sample/template files are never blocked
  if (isSafeFile(normalized)) {
    return false;
  }

  const basename = path.basename(normalized);

  for (const pattern of PRIVACY_PATTERNS) {
    if (pattern.test(basename) || pattern.test(normalized)) {
      return true;
    }
  }
  return false;
}

/**
 * Extract every path candidate from a tool input for sensitivity checking.
 * Handles file_path, path, pattern, and bash command strings (including APPROVED:
 * references and variable assignments).
 * @param {Object} toolInput - Tool input object with file_path, path, pattern, or command
 * @returns {Array<{value: string, field: string}>} Array of extracted paths with field names
 */
function extractPaths(toolInput) {
  const paths = [];
  if (!toolInput) return paths;

  if (toolInput.file_path) paths.push({ value: toolInput.file_path, field: 'file_path' });
  if (toolInput.path) paths.push({ value: toolInput.path, field: 'path' });
  if (toolInput.pattern) paths.push({ value: toolInput.pattern, field: 'pattern' });

  // Scan bash command strings for sensitive path references
  if (toolInput.command) {
    // APPROVED:-prefixed paths take priority — extract them first
    const approvedMatch = toolInput.command.match(/APPROVED:[^\s]+/g) || [];
    approvedMatch.forEach(p => paths.push({ value: p, field: 'command' }));

    // Only scan for bare .env references when no APPROVED: path was found
    if (approvedMatch.length === 0) {
      const envMatch = toolInput.command.match(/\.env[^\s]*/g) || [];
      envMatch.forEach(p => paths.push({ value: p, field: 'command' }));

      // Also check bash variable assignments (FILE=.env, ENV_FILE=.env.local)
      const varAssignments = toolInput.command.match(/\w+=[^\s]*\.env[^\s]*/g) || [];
      varAssignments.forEach(a => {
        const value = a.split('=')[1];
        if (value) paths.push({ value, field: 'command' });
      });

      // Pull .env references out of $(...) substitutions
      const cmdSubst = toolInput.command.match(/\$\([^)]*?(\.env[^\s)]*)[^)]*\)/g) || [];
      for (const subst of cmdSubst) {
        const inner = subst.match(/\.env[^\s)]*/);
        if (inner) paths.push({ value: inner[0], field: 'command' });
      }
    }
  }

  return paths.filter(p => p.value);
}

/**
 * Read .tkm.json (with deprecated .sk.json fallback) to check whether the guard
 * is disabled via `privacyBlock: false`. Fails open when neither file is readable.
 * @param {string} [configDir] - Directory containing .tkm.json (defaults to .claude in cwd)
 * @returns {boolean} true if privacy block should be skipped
 */
function isPrivacyBlockDisabled(configDir) {
  const baseDir = configDir || path.join(process.cwd(), '.claude');
  // Try .tkm.json first; fall back to deprecated .sk.json (read-only)
  for (const name of ['.tkm.json', '.sk.json']) {
    try {
      const config = JSON.parse(fs.readFileSync(path.join(baseDir, name), 'utf8'));
      return config.privacyBlock === false;
    } catch {
      // Not found or unreadable — try next candidate; guard stays enabled
    }
  }
  return false;
}

/**
 * Build the @@PRIVACY_PROMPT@@ payload the agent passes to AskUserQuestion.
 * @param {string} filePath - Blocked file path
 * @returns {Object} Prompt data object
 */
function buildPromptData(filePath) {
  const basename = path.basename(filePath);
  return {
    type: 'PRIVACY_PROMPT',
    file: filePath,
    basename: basename,
    question: {
      header: 'File Access',
      text: `I need to read "${basename}" which may contain sensitive data (API keys, passwords, tokens). Do you approve?`,
      options: [
        { label: 'Yes, approve access', description: `Allow reading ${basename} this time` },
        { label: 'No, skip this file', description: 'Continue without accessing this file' }
      ]
    }
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN ENTRY POINT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Determine whether a tool call touches a privacy-sensitive file, and what action to take.
 * Returns one of: blocked (exit 2), approved (APPROVED: prefix present), isBash (warn-only),
 * or clean (allow).
 *
 * @param {Object} params
 * @param {string} params.toolName - Name of tool (Read, Write, Bash, etc.)
 * @param {Object} params.toolInput - Tool input with file_path, path, command, etc.
 * @param {Object} [params.options]
 * @param {boolean} [params.options.disabled] - Skip checks if true
 * @param {string} [params.options.configDir] - Directory for .tkm.json config
 * @param {boolean} [params.options.allowBash] - Allow Bash tool without blocking (default: true)
 * @returns {{
 *   blocked: boolean,
 *   filePath?: string,
 *   reason?: string,
 *   approved?: boolean,
 *   isBash?: boolean,
 *   suspicious?: boolean,
 *   promptData?: Object
 * }}
 */
function checkPrivacy({ toolName, toolInput, options = {} }) {
  const { disabled, configDir, allowBash = true } = options;

  // Short-circuit when the guard is explicitly disabled
  if (disabled || isPrivacyBlockDisabled(configDir)) {
    return { blocked: false };
  }

  const isBashTool = toolName === 'Bash';
  const paths = extractPaths(toolInput);

  // Evaluate each extracted path in order; first match wins
  for (const { value: testPath } of paths) {
    if (!isPrivacySensitive(testPath)) continue;

    // APPROVED: prefix — user already approved; allow and flag suspicious paths
    if (hasApprovalPrefix(testPath)) {
      const strippedPath = stripApprovalPrefix(testPath);
      return {
        blocked: false,
        approved: true,
        filePath: strippedPath,
        suspicious: isSuspiciousPath(strippedPath)
      };
    }

    // Bash: warn-only so the "Yes → bash cat" flow remains usable
    if (isBashTool && allowBash) {
      return {
        blocked: false,
        isBash: true,
        filePath: testPath,
        reason: `Bash command accesses sensitive file: ${testPath}`
      };
    }

    // Sensitive path, no approval — block and emit prompt data
    return {
      blocked: true,
      filePath: testPath,
      reason: `Sensitive file access requires user approval`,
      promptData: buildPromptData(testPath)
    };
  }

  // No sensitive paths — allow
  return { blocked: false };
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Primary decision function
  checkPrivacy,

  // Helpers exposed for testing and direct use
  isSafeFile,
  isPrivacySensitive,
  hasApprovalPrefix,
  stripApprovalPrefix,
  isSuspiciousPath,
  extractPaths,
  isPrivacyBlockDisabled,
  buildPromptData,

  // Pattern constants for testing
  APPROVED_PREFIX,
  SAFE_PATTERNS,
  PRIVACY_PATTERNS
};
