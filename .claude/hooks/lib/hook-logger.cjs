/**
 * Structured hook logger — writes JSON Lines to .claude/hooks/.logs/hook-log.jsonl.
 * Auto-creates the .logs/ directory; rotates at 1000 lines (keeps last 500).
 * Zero external dependencies — Node builtins only.
 *
 * @module hook-logger
 */

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, '..', '.logs');
const LOG_FILE = path.join(LOG_DIR, 'hook-log.jsonl');
const LOCK_FILE = path.join(LOG_DIR, 'hook-log.lock');
const MAX_LINES = 1000;
const TRUNCATE_TO = 500;
const LOCK_TIMEOUT_MS = 250;
const LOCK_RETRY_MS = 10;

function sleep(ms) {
  try {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
  } catch (_) {
    const end = Date.now() + ms;
    while (Date.now() < end) {}
  }
}

function withLogLock(fn) {
  ensureLogDir();
  const startedAt = Date.now();

  while (Date.now() - startedAt < LOCK_TIMEOUT_MS) {
    let fd;
    try {
      fd = fs.openSync(LOCK_FILE, 'wx');
      try {
        return fn();
      } finally {
        try { fs.closeSync(fd); } catch (_) {}
        try { fs.unlinkSync(LOCK_FILE); } catch (_) {}
      }
    } catch (error) {
      if (!error || error.code !== 'EEXIST') {
        throw error;
      }
      sleep(LOCK_RETRY_MS);
    }
  }

  return null;
}

/**
 * Create log directory if absent — silent on failure.
 */
function ensureLogDir() {
  try {
    if (!fs.existsSync(LOG_DIR)) {
      fs.mkdirSync(LOG_DIR, { recursive: true });
    }
  } catch (_) {
    // Fail silently — logger must never crash a hook
  }
}

/**
 * Rotate log if it exceeds MAX_LINES — keeps the last TRUNCATE_TO lines.
 */
function rotateIfNeeded() {
  try {
    if (!fs.existsSync(LOG_FILE)) return;
    const lines = fs.readFileSync(LOG_FILE, 'utf-8').split('\n').filter(Boolean);
    if (lines.length >= MAX_LINES) {
      const truncated = lines.slice(-TRUNCATE_TO).join('\n') + '\n';
      fs.writeFileSync(LOG_FILE, truncated, 'utf-8');
    }
  } catch (_) {
    // Fail silently — rotation failure is non-fatal
  }
}

/**
 * Append a structured hook event entry to the log.
 * @param {string} hookName - Hook filename (e.g., 'scout-block')
 * @param {object} data - Log data { event?, tool?, target?, note?, dur?, status, exit?, error? }
 */
function logHook(hookName, data) {
  try {
    const entry = {
      ts: new Date().toISOString(),
      hook: hookName,
      event: data.event || '',
      tool: data.tool || '',
      target: data.target || '',
      note: data.note || '',
      dur: data.dur || 0,
      status: data.status || 'ok',
      exit: data.exit !== undefined ? data.exit : 0,
      error: data.error || ''
    };

    const serialized = JSON.stringify(entry) + '\n';
    const wroteWithLock = withLogLock(() => {
      fs.appendFileSync(LOG_FILE, serialized, 'utf-8');
      rotateIfNeeded();
      return true;
    });

    if (wroteWithLock === null) {
      fs.appendFileSync(LOG_FILE, serialized, 'utf-8');
    }
  } catch (_) {
    // Never crash — hook integrity over log completeness
  }
}

/**
 * Create a duration timer for a hook invocation.
 * @param {string} hookName - Hook filename
 * @param {object} [baseData] - Fields merged into every end() call
 * @returns {{ end: (data) => void }} Timer with end() that logs the elapsed duration
 */
function createHookTimer(hookName, baseData = {}) {
  const start = Date.now();
  let ended = false;
  return {
    end(data = {}) {
      if (ended) return;
      ended = true;
      const dur = Date.now() - start;
      logHook(hookName, { ...baseData, ...data, dur });
    }
  };
}

/**
 * Log a crash entry — normalizes error to a string, status to 'crash'.
 * @param {string} hookName
 * @param {unknown} error
 * @param {object} [data]
 */
function logHookCrash(hookName, error, data = {}) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
        ? error
        : String(error || 'unknown error');
  logHook(hookName, {
    ...data,
    status: 'crash',
    exit: data.exit !== undefined ? data.exit : 0,
    error: message
  });
}

module.exports = {
  logHook,
  createHookTimer,
  logHookCrash
};
