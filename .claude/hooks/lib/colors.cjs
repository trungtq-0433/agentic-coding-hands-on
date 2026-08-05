#!/usr/bin/env node
'use strict';

/**
 * ANSI color utility — cross-platform color support for statusline rendering.
 * Honors NO_COLOR, FORCE_COLOR, and COLORTERM environment variables.
 *
 * @module colors
 */

// ANSI escape codes — standard palette + bright variants
const RESET = '\x1b[0m';
const DIM = '\x1b[2m';
const CLEAR_INTENSITY = '\x1b[22m';
const CLEAR_FOREGROUND = '\x1b[39m';
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const MAGENTA = '\x1b[35m';
const CYAN = '\x1b[36m';
const BRIGHT_RED = '\x1b[91m';
const BRIGHT_GREEN = '\x1b[92m';
const BRIGHT_YELLOW = '\x1b[93m';
const BRIGHT_BLUE = '\x1b[94m';
const BRIGHT_MAGENTA = '\x1b[95m';
const BRIGHT_CYAN = '\x1b[96m';
const BRIGHT_WHITE = '\x1b[97m';
const STABLE_PREFIX = `${CLEAR_INTENSITY}${CLEAR_FOREGROUND}`;
const STABLE_SUFFIX = `${RESET}${CLEAR_INTENSITY}${CLEAR_FOREGROUND}`;
const COLOR_CODES = {
  green: GREEN,
  yellow: YELLOW,
  red: RED,
  blue: BLUE,
  cyan: CYAN,
  magenta: MAGENTA,
  dim: DIM,
  brightRed: BRIGHT_RED,
  brightGreen: BRIGHT_GREEN,
  brightYellow: BRIGHT_YELLOW,
  brightBlue: BRIGHT_BLUE,
  brightMagenta: BRIGHT_MAGENTA,
  brightCyan: BRIGHT_CYAN,
  brightWhite: BRIGHT_WHITE,
};

// Detect color support once at module load (cached).
// Statusline runs through a pipe but the output displays in a TTY — default to true.
const shouldUseColor = (() => {
  if (process.env.NO_COLOR) return false;
  if (process.env.FORCE_COLOR) return true;
  // Default true for statusline context (Claude Code handles TTY display)
  return true;
})();

// Mutable override written by statusline.cjs from config.
// null = fall back to env detection; true/false = explicit override.
let _colorOverride = null;

/**
 * Set an explicit color enable/disable override.
 * Pass null to revert to environment-variable detection.
 * @param {boolean} enabled
 */
function setColorEnabled(enabled) {
  _colorOverride = enabled;
}

/**
 * Whether colors should be rendered — respects env vars and config override.
 * NO_COLOR always wins over any config override.
 * @returns {boolean}
 */
function isColorEnabled() {
  // NO_COLOR is the hard override — always takes precedence
  if (process.env.NO_COLOR) return false;
  if (_colorOverride !== null) return _colorOverride;
  return shouldUseColor;
}

// 256-color / truecolor detection via COLORTERM
const has256Color = (() => {
  const ct = process.env.COLORTERM;
  return ct === 'truecolor' || ct === '24bit' || ct === '256color';
})();

/**
 * Wrap text with an ANSI color code.
 * @param {string} text - Text to colorize
 * @param {string} code - ANSI escape code
 * @returns {string} Colorized text, or plain text when colors are disabled
 */
function colorize(text, code) {
  if (!isColorEnabled() || !code) return String(text);
  return `${STABLE_PREFIX}${code}${text}${STABLE_SUFFIX}`;
}

function green(text) { return colorize(text, GREEN); }
function yellow(text) { return colorize(text, YELLOW); }
function red(text) { return colorize(text, RED); }
function blue(text) { return colorize(text, BLUE); }
function cyan(text) { return colorize(text, CYAN); }
function magenta(text) { return colorize(text, MAGENTA); }
function dim(text) { return colorize(text, DIM); }
function brightRed(text) { return colorize(text, BRIGHT_RED); }
function brightGreen(text) { return colorize(text, BRIGHT_GREEN); }
function brightYellow(text) { return colorize(text, BRIGHT_YELLOW); }
function brightBlue(text) { return colorize(text, BRIGHT_BLUE); }
function brightMagenta(text) { return colorize(text, BRIGHT_MAGENTA); }
function brightCyan(text) { return colorize(text, BRIGHT_CYAN); }
function brightWhite(text) { return colorize(text, BRIGHT_WHITE); }

/**
 * Threshold-based ANSI color code for context usage percentage.
 * @param {number} percent - Context usage percentage (0-100)
 * @returns {string} ANSI color code
 */
function resolveColorCode(colorName) {
  if (colorName === 'white' || colorName === 'none' || colorName === 'default') return '';
  return COLOR_CODES[colorName] || '';
}

function getContextColor(percent, palette = {}) {
  const high = resolveColorCode(palette.high || 'red') || RED;
  const mid = resolveColorCode(palette.mid || 'yellow') || YELLOW;
  const low = resolveColorCode(palette.low || 'green') || GREEN;
  if (percent >= 85) return high;
  if (percent >= 70) return mid;
  return low;
}

/**
 * Build a colored context progress bar using ▰▱ block chars.
 * @param {number} percent - Usage percentage (0-100)
 * @param {number} width - Bar width in characters (default 12)
 * @returns {string} Unicode progress bar with threshold-based colors
 */
function coloredBar(percent, width = 12, palette = {}) {
  const clamped = Math.max(0, Math.min(100, percent));
  const filled = Math.round((clamped / 100) * width);
  const empty = width - filled;

  if (!isColorEnabled()) {
    return '▰'.repeat(filled) + '▱'.repeat(empty);
  }

  const color = getContextColor(percent, palette);
  return `${STABLE_PREFIX}${color}${'▰'.repeat(filled)}${STABLE_PREFIX}${DIM}${'▱'.repeat(empty)}${STABLE_SUFFIX}`;
}

/**
 * Resolve a theme color name to a color function.
 * Unknown names fall back to the identity function (no color applied).
 * @param {string} colorName - Color name (e.g. "green", "yellow", "dim")
 * @returns {Function} Color function (string) => string
 */
function resolveColor(colorName) {
  const code = resolveColorCode(colorName);
  return code ? (s) => colorize(s, code) : (s) => String(s);
}

/**
 * Colorize a single character — minimal wrapping, bare RESET only.
 * Lighter than colorize(); designed for per-character neon bar rendering.
 * @param {string} char       single character to color
 * @param {string} colorName  color name from COLOR_CODES (e.g. 'brightCyan')
 * @returns {string}
 */
function colorizeChar(char, colorName) {
  if (!isColorEnabled()) return char;
  const code = resolveColorCode(colorName);
  if (!code) return char;
  return `${code}${char}${RESET}`;
}

module.exports = {
  RESET,
  green,
  yellow,
  red,
  cyan,
  magenta,
  dim,
  brightMagenta,
  brightCyan,
  getContextColor,
  coloredBar,
  colorizeChar,
  shouldUseColor,
  has256Color,
  setColorEnabled,
  isColorEnabled,
  resolveColorCode,
  resolveColor,
};
