#!/usr/bin/env node
/**
 * scout-checker.cjs — Facade over the scout-block/* sub-modules.
 * Exposes a single checkScoutBlock() entry point shared by scout-block.cjs
 * and any other runtime that needs the same .skignore guard.
 *
 * @module scout-checker
 */

const fs = require('fs');
const path = require('path');

// Sub-module imports — each owns one concern
const { loadPatterns, createMatcher, matchPath } = require('../scout-block/pattern-matcher.cjs');
const { extractFromToolInput } = require('../scout-block/path-extractor.cjs');
const { detectBroadPatternIssue } = require('../scout-block/broad-pattern-detector.cjs');

// ═══════════════════════════════════════════════════════════════════════════
// COMMAND PATTERNS
// ═══════════════════════════════════════════════════════════════════════════

// Package manager build/install/test — allowed even when the command token touches a blocked path.
// Handles filter flags: pnpm --filter web run build, yarn workspace app build
const BUILD_COMMAND_PATTERN = /^(npm|pnpm|yarn|bun)\s+([^\s]+\s+)*(run\s+)?(build|test|lint|dev|start|install|ci|add|remove|update|publish|pack|init|create|exec)/;

// Direct tool invocations — JS/TS, Go, Rust, Java, .NET, containers, IaC, Python, Ruby, PHP, Deno, Elixir
const TOOL_COMMAND_PATTERN = /^(\.\/)?(npx|pnpx|bunx|tsc|esbuild|vite|webpack|rollup|turbo|nx|jest|vitest|mocha|eslint|prettier|go|cargo|make|mvn|mvnw|gradle|gradlew|dotnet|docker|podman|kubectl|helm|terraform|ansible|bazel|cmake|sbt|flutter|swift|ant|ninja|meson|python3?|pip|uv|deno|bundle|rake|gem|php|composer|ruby|mix|elixir)/;

// Execution from .venv/bin/ or venv/bin/ (Unix) and .venv/Scripts/ or venv/Scripts/ (Windows)
const VENV_EXECUTABLE_PATTERN = /(^|[\/\\])\.?venv[\/\\](bin|Scripts)[\/\\]/;

// Python venv creation — cross-platform:
// python/python3 -m venv, py -m venv (Windows launcher, -3, -3.11, …),
// uv venv (Rust-based), virtualenv (legacy)
const VENV_CREATION_PATTERN = /^(python3?|py)\s+(-[\w.]+\s+)*-m\s+venv\s+|^uv\s+venv(\s|$)|^virtualenv\s+/;

// ═══════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Remove leading ENV=VALUE assignments and wrappers (sudo, env, nice, etc.)
 * so pattern matching sees the real executable.
 * e.g., "NODE_ENV=production npm run build" → "npm run build"
 * @param {string} command - The command to strip
 * @returns {string}
 */
function stripCommandPrefix(command) {
  if (!command || typeof command !== 'string') return command;
  let stripped = command.trim();
  // Drop KEY=VALUE prefixes
  stripped = stripped.replace(/^(\w+=\S+\s+)+/, '');
  // Drop one level of sudo/env/nice/nohup/time/timeout wrapper
  stripped = stripped.replace(/^(sudo|env|nice|nohup|time|timeout)\s+/, '');
  // Second pass handles "sudo env VAR=x cmd" patterns
  stripped = stripped.replace(/^(\w+=\S+\s+)+/, '');
  return stripped.trim();
}

/**
 * True when the command matches the build/tooling allowlist.
 * @param {string} command - The command to check
 * @returns {boolean}
 */
function isBuildCommand(command) {
  if (!command || typeof command !== 'string') return false;
  const trimmed = command.trim();
  return BUILD_COMMAND_PATTERN.test(trimmed) || TOOL_COMMAND_PATTERN.test(trimmed);
}

/**
 * Split a compound shell command on &&, ||, and ; so each sub-command can be
 * checked independently. Newlines are intentionally NOT split — they typically
 * delimit heredoc bodies, not compound operators.
 * Quoted-string operators are not handled (rare enough to ignore).
 *
 * @param {string} command - The compound command string
 * @returns {string[]} Array of sub-commands (trimmed, non-empty)
 */
function splitCompoundCommand(command) {
  if (!command || typeof command !== 'string') return [];
  return command.split(/\s*(?:&&|\|\||;)\s*/).filter(cmd => cmd && cmd.trim().length > 0);
}

/**
 * Unwrap bash -c "...", sh -c '...', or eval "..." to get the inner command.
 * Lets the real command be re-evaluated rather than the wrapper string.
 * @param {string} command - The command to unwrap
 * @returns {string} Inner command, or original if not a shell executor
 */
function unwrapShellExecutor(command) {
  if (!command || typeof command !== 'string') return command;
  const match = command.trim().match(
    /^(?:(?:bash|sh|zsh)\s+-c|eval)\s+["'](.+)["']\s*$/
  );
  return match ? match[1] : command;
}

/**
 * True when the command runs from a .venv bin directory (virtualenv executables).
 * @param {string} command - The command to check
 * @returns {boolean}
 */
function isVenvExecutable(command) {
  if (!command || typeof command !== 'string') return false;
  return VENV_EXECUTABLE_PATTERN.test(command);
}

/**
 * True when the command creates a Python virtual environment.
 * @param {string} command - The command to check
 * @returns {boolean}
 */
function isVenvCreationCommand(command) {
  if (!command || typeof command !== 'string') return false;
  return VENV_CREATION_PATTERN.test(command.trim());
}

/**
 * True when a command is safe to allow regardless of the paths it touches.
 * Strips ENV prefixes and wrappers before testing against all three allowlists.
 * @param {string} command - The command to check
 * @returns {boolean}
 */
function isAllowedCommand(command) {
  const stripped = stripCommandPrefix(command);
  return isBuildCommand(stripped) || isVenvExecutable(stripped) || isVenvCreationCommand(stripped);
}

function findGitRoot(startDir) {
  if (!startDir || typeof startDir !== 'string') return null;

  let dir = path.resolve(startDir);
  const root = path.parse(dir).root;

  while (true) {
    if (fs.existsSync(path.join(dir, '.git')) || dir === root) {
      return fs.existsSync(path.join(dir, '.git')) ? dir : null;
    }

    dir = path.dirname(dir);
  }
}

/**
 * Locate a project-local .skignore at <git-root>/<configDirName>/.skignore.
 * Anchoring at the git root keeps the path stable however deep the caller's cwd is.
 *
 * @param {string} startDir - Directory to start searching from
 * @param {string} [configDirName] - Config directory at git root (.claude, .opencode)
 * @returns {string|null}
 */
function findProjectCkignore(startDir, configDirName) {
  if (!configDirName || typeof configDirName !== 'string') return null;
  const gitRoot = findGitRoot(startDir);
  if (!gitRoot) return null;
  const candidate = path.join(gitRoot, configDirName, '.skignore');
  return fs.existsSync(candidate) ? candidate : null;
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN ENTRY POINT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Determine whether a tool call accesses a .skignore-blocked path or uses an
 * overly broad glob pattern. Returns the first violation found.
 *
 * @param {Object} params
 * @param {string} params.toolName - Name of tool (Bash, Glob, Read, etc.)
 * @param {Object} params.toolInput - Tool input with file_path, path, pattern, command
 * @param {Object} [params.options]
 * @param {string} [params.options.skignorePath] - Path to .skignore file
 * @param {string} [params.options.projectSkignorePath] - Explicit project-local .skignore path
 * @param {string} [params.options.claudeDir] - Path to .claude or .opencode directory
 * @param {string} [params.options.cwd] - Working directory used to discover a project .skignore
 * @param {string} [params.options.projectConfigDirName] - Git-root config dir for project-local overrides
 * @param {boolean} [params.options.checkBroadPatterns] - Check for overly broad glob patterns (default: true)
 * @returns {{
 *   blocked: boolean,
  *   path?: string,
  *   pattern?: string,
  *   reason?: string,
 *   configPath?: string,
  *   isBroadPattern?: boolean,
  *   suggestions?: string[],
  *   isAllowedCommand?: boolean
 * }}
 */
function checkScoutBlock({ toolName, toolInput, options = {} }) {
  const {
    skignorePath,
    projectSkignorePath,
    claudeDir = path.join(process.cwd(), '.claude'),
    cwd = process.cwd(),
    projectConfigDirName,
    checkBroadPatterns = true
  } = options;

  // Unwrap bash -c / eval wrappers before any other analysis
  if (toolInput.command) {
    const unwrapped = unwrapShellExecutor(toolInput.command);
    if (unwrapped !== toolInput.command) {
      toolInput = { ...toolInput, command: unwrapped };
    }
  }

  // Split compound commands (&&, ||, ;) before calling isAllowedCommand.
  // Without splitting, BUILD_COMMAND_PATTERN's unanchored end would match
  // the prefix of "npm run build && cat dist/file.js" and let the whole
  // thing through. Only non-allowed sub-commands are path-checked.
  if (toolInput.command) {
    const subCommands = splitCompoundCommand(toolInput.command);
    const nonAllowed = subCommands.filter(cmd => !isAllowedCommand(cmd.trim()));
    if (nonAllowed.length === 0) {
      return { blocked: false, isAllowedCommand: true };
    }
    // Only extract paths from non-allowed sub-commands
    if (nonAllowed.length < subCommands.length) {
      toolInput = { ...toolInput, command: nonAllowed.join(' ; ') };
    }
  }

  // Check for overly broad glob patterns (Glob tool)
  if (checkBroadPatterns && (toolName === 'Glob' || toolInput.pattern)) {
    const broadResult = detectBroadPatternIssue(toolInput);
    if (broadResult.blocked) {
      return {
        blocked: true,
        isBroadPattern: true,
        pattern: toolInput.pattern,
        reason: broadResult.reason || 'Pattern too broad - may fill context with too many files',
        suggestions: broadResult.suggestions || []
      };
    }
  }

  // Resolve .skignore path
  const resolvedCkignorePath = skignorePath || path.join(claudeDir, '.skignore');
  const discoveredProjectCkignorePath = projectSkignorePath || findProjectCkignore(cwd, projectConfigDirName);
  const resolvedProjectCkignorePath = discoveredProjectCkignorePath
    && path.resolve(discoveredProjectCkignorePath) !== path.resolve(resolvedCkignorePath)
      ? discoveredProjectCkignorePath
      : null;
  const configPath = resolvedProjectCkignorePath || resolvedCkignorePath;

  // Load patterns and create matcher
  const patterns = loadPatterns(resolvedCkignorePath, resolvedProjectCkignorePath);
  const matcher = createMatcher(patterns);

  // Extract paths from tool input
  const extractedPaths = extractFromToolInput(toolInput);

  // If no paths extracted, allow operation
  if (extractedPaths.length === 0) {
    return { blocked: false };
  }

  // Check each path against patterns
  for (const extractedPath of extractedPaths) {
    const result = matchPath(matcher, extractedPath);
    if (result.blocked) {
      return {
        blocked: true,
        path: extractedPath,
        pattern: result.pattern,
        configPath,
        reason: `Path matches blocked pattern: ${result.pattern}`
      };
    }
  }

  // All paths allowed
  return { blocked: false };
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

module.exports = {
  // Main entry point
  checkScoutBlock,

  // Command checkers
  isBuildCommand,
  isVenvExecutable,
  isVenvCreationCommand,
  isAllowedCommand,
  splitCompoundCommand,
  stripCommandPrefix,
  unwrapShellExecutor,
  findGitRoot,
  findProjectCkignore,

  // Re-export scout-block modules for direct access
  loadPatterns,
  createMatcher,
  matchPath,
  extractFromToolInput,
  detectBroadPatternIssue,

  // Patterns (for testing)
  BUILD_COMMAND_PATTERN,
  TOOL_COMMAND_PATTERN,
  VENV_EXECUTABLE_PATTERN,
  VENV_CREATION_PATTERN
};
