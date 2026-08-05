/**
 * GitHub identity resolver — local cache backed by the tkm CLI.
 *
 * resolveGithubUser() returns the user's GitHub login via:
 *   1. A fresh (< 30 d) cache at ~/.claude/sk-user.json, or
 *   2. `tkm auth status --json` with a 2 s timeout.
 *
 * The CLI derives identity from the Supabase session token written by
 * `tkm auth login` (GitHub OAuth). Returns null on any failure: missing
 * binary, no session, bad JSON, timeout. Callers — telemetry, feedback,
 * rating — silently skip sending when null.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const DEFAULT_CACHE_PATH = path.join(os.homedir(), '.claude', 'sk-user.json');
const CACHE_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const CLI_TIMEOUT_MS = 2000;
// GitHub login: 1–39 chars, alphanumeric + hyphens, must start and end with
// alphanumeric (no leading/trailing dash). Matches github.com/login rules.
const GITHUB_LOGIN_REGEX = /^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$/;

function isValidGithubLogin(login) {
  return typeof login === 'string' && GITHUB_LOGIN_REGEX.test(login);
}

function readCache(cacheFile) {
  try {
    if (!fs.existsSync(cacheFile)) return null;
    const raw = fs.readFileSync(cacheFile, 'utf8');
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    if (!isValidGithubLogin(parsed.githubLogin)) return null;
    if (typeof parsed.resolvedAt !== 'number') return null;
    if (parsed.source !== 'gh' && parsed.source !== 'manual') return null;
    if (Date.now() - parsed.resolvedAt > CACHE_TTL_MS) return null;
    return parsed;
  } catch (_) {
    return null;
  }
}

function writeCache(cacheFile, login, source) {
  if (!isValidGithubLogin(login)) return false;
  // Source values 'gh' | 'manual' are fixed for back-compat with existing
  // on-disk entries. 'gh' covers both the old gh-CLI path and the current
  // tkm → Supabase path — same upstream GitHub identity, different mechanism.
  if (source !== 'gh' && source !== 'manual') return false;

  const payload = {
    githubLogin: login,
    resolvedAt: Date.now(),
    source,
  };

  try {
    fs.mkdirSync(path.dirname(cacheFile), { recursive: true });
  } catch (_) {
    return false;
  }

  const tmpFile = `${cacheFile}.${process.pid}.${Math.random().toString(36).slice(2)}`;
  try {
    fs.writeFileSync(tmpFile, JSON.stringify(payload, null, 2));
    fs.renameSync(tmpFile, cacheFile);
    return true;
  } catch (_) {
    try { fs.unlinkSync(tmpFile); } catch (_err) { /* ignore */ }
    return false;
  }
}

function resolveViaTkmCli(timeoutMs = CLI_TIMEOUT_MS) {
  let out;
  try {
    out = execFileSync('tkm', ['auth', 'status', '--json'], {
      encoding: 'utf8',
      timeout: timeoutMs,
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: true,
    });
  } catch (_) {
    // ENOENT (tkm not on PATH), non-zero exit, timeout — null means skip telemetry.
    return null;
  }
  try {
    const parsed = JSON.parse((out || '').trim());
    if (!parsed?.loggedIn) return null;
    const login = typeof parsed.githubLogin === 'string' ? parsed.githubLogin : null;
    return isValidGithubLogin(login) ? login : null;
  } catch (_) {
    return null;
  }
}

/**
 * Return the current user's GitHub login, or null if unresolvable.
 * Cache hit (< 30 d) avoids the CLI call entirely.
 *
 * @param {Object} [options]
 * @param {string} [options.cacheFile] - Override cache path (default: ~/.claude/sk-user.json)
 * @param {number} [options.timeoutMs] - CLI timeout in ms (default: 2000)
 * @returns {string|null} GitHub login, or null on any failure
 */
function resolveGithubUser(options = {}) {
  const cacheFile = options.cacheFile || DEFAULT_CACHE_PATH;
  const timeoutMs = options.timeoutMs || CLI_TIMEOUT_MS;

  const cached = readCache(cacheFile);
  if (cached) return cached.githubLogin;

  const login = resolveViaTkmCli(timeoutMs);
  if (login) {
    writeCache(cacheFile, login, 'gh');
    return login;
  }

  return null;
}

module.exports = {
  DEFAULT_CACHE_PATH,
  CACHE_TTL_MS,
  CLI_TIMEOUT_MS,
  GITHUB_LOGIN_REGEX,
  isValidGithubLogin,
  readCache,
  writeCache,
  resolveViaTkmCli,
  resolveGithubUser,
};
