'use strict';

/**
 * Neon progress bar builder — block-char bars with 3 time-driven animation styles.
 * Driven by Date.now() so each poll render advances the frame without an event loop.
 * Output is raw chars only; callers apply ANSI color per character.
 *
 * @module statusline-neon-bar
 */

const SOLID = '█'; // full block
const DENSE = '▓'; // dark shade — sweep spot / wave edge
const MID   = '▒'; // medium shade — wave trailing edge
const LIGHT = '░'; // light shade — empty track

/**
 * Build an animated neon progress bar — raw chars, no ANSI color.
 *
 * @param {number} percent         0–100
 * @param {number} width           total character width (default 12)
 * @param {object} opts
 *   @param {'sweep'|'pulse'|'wave'} opts.style  animation style (default 'sweep')
 *   @param {number} opts.frameIntervalMs        ms per animation frame (default 200 ≈ 5fps)
 * @returns {string} exactly `width` chars
 */
function neonBar(percent, width = 12, { style = 'sweep', frameIntervalMs = 200 } = {}) {
  const filled = Math.max(0, Math.min(width, Math.round(percent / 100 * width)));
  const frameIndex = Math.floor(Date.now() / frameIntervalMs);

  if (style === 'sweep') {
    // ▓ sweep spot travels left→right through filled portion — neon tube scan
    const sweepPos = filled > 0 ? frameIndex % filled : -1;
    return Array.from({ length: width }, (_, i) => {
      if (i >= filled) return LIGHT;
      return i === sweepPos ? DENSE : SOLID;
    }).join('');
  }

  if (style === 'pulse') {
    // All filled chars pulse █ ↔ ▓ together — neon flicker
    const filledChar = frameIndex % 2 === 0 ? SOLID : DENSE;
    return Array.from({ length: width }, (_, i) =>
      i < filled ? filledChar : LIGHT
    ).join('');
  }

  if (style === 'wave') {
    if (filled === 0) return LIGHT.repeat(width);
    // ▓▒ gradient swaps at fill boundary — liquid fill ripple
    const frame = frameIndex % 2;
    return Array.from({ length: width }, (_, i) => {
      if (i < filled - 1) return SOLID;
      if (i === filled - 1) return frame === 0 ? DENSE : MID;
      if (i === filled)     return frame === 0 ? MID   : DENSE;
      return LIGHT;
    }).join('');
  }

  // Unknown style: static gradient fallback (████▓▒░░░)
  return Array.from({ length: width }, (_, i) => {
    if (i < filled - 1) return SOLID;
    if (i === filled - 1) return DENSE;
    if (i === filled)     return MID;
    return LIGHT;
  }).join('');
}

module.exports = { neonBar, SOLID, DENSE, MID, LIGHT };
