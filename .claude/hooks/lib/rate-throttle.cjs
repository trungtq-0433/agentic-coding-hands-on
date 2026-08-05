'use strict';

/**
 * Per-user throttle for the Stop-hook rating prompt.
 * State file format: { [githubLogin]: lastShownMs, ... }
 * No sensitive data — logins appear in git remotes already; timestamps are coarse.
 *
 * @module rate-throttle
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const DEFAULT_THROTTLE_FILE = path.join(os.homedir(), '.claude', 'sk-rate-state.json');
const DEFAULT_WINDOW_MS = 24 * 60 * 60 * 1000;

function readThrottleState(stateFile = DEFAULT_THROTTLE_FILE) {
  try {
    const parsed = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function recentlyPrompted(login, stateFile = DEFAULT_THROTTLE_FILE, windowMs = DEFAULT_WINDOW_MS, now = Date.now()) {
  // No login → treat as recently prompted so we never spam anonymous flows.
  if (!login || typeof login !== 'string') return true;
  const state = readThrottleState(stateFile);
  // Unknown login → never prompted → not throttled.
  // Guard: if we stored 0, `now - 0 < 24h` would be a false-positive for ~24h after epoch.
  if (!Object.prototype.hasOwnProperty.call(state, login)) return false;
  const lastShown = Number(state[login]);
  if (!Number.isFinite(lastShown)) return false;
  return (now - lastShown) < windowMs;
}

function persistLastShown(login, stateFile = DEFAULT_THROTTLE_FILE, now = Date.now()) {
  if (!login || typeof login !== 'string') return false;
  try {
    fs.mkdirSync(path.dirname(stateFile), { recursive: true });
    const state = readThrottleState(stateFile);
    state[login] = now;
    const tmp = `${stateFile}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
    fs.renameSync(tmp, stateFile);
    return true;
  } catch {
    return false;
  }
}

function clearThrottleState(stateFile = DEFAULT_THROTTLE_FILE) {
  try { fs.unlinkSync(stateFile); return true; } catch { return false; }
}

module.exports = {
  DEFAULT_THROTTLE_FILE,
  DEFAULT_WINDOW_MS,
  readThrottleState,
  recentlyPrompted,
  persistLastShown,
  clearThrottleState,
};
