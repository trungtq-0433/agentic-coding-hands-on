'use strict';

/**
 * Statusline section registry — maps section IDs to render functions.
 * Each renderer: (ctx, sectionConfig, theme) => string | null.
 * Agents and todos are excluded; they're multi-line and live in statusline-activity-renderers.cjs.
 *
 * @module statusline-section-registry
 */

const {
  green, yellow, red, coloredBar, resolveColor, colorizeChar, brightMagenta
} = require('./colors.cjs');
const { neonBar } = require('./statusline-neon-bar.cjs');

// Default section order — left-to-right within a line, top-to-bottom across lines
const DEFAULT_SECTIONS = [
  { id: 'brand',     enabled: true,  order: 0 },
  { id: 'model',     enabled: true,  order: 1 },
  { id: 'context',   enabled: true,  order: 2 },
  { id: 'quota',     enabled: true,  order: 3, icon: '⏳' },
  { id: 'directory', enabled: true,  order: 4, icon: '📂' },
  { id: 'git',       enabled: true,  order: 5, icon: '✦' },
  { id: 'cost',      enabled: false, order: 6, icon: '💰' },
  { id: 'changes',   enabled: true,  order: 7 },
  { id: 'agents',    enabled: true,  order: 8, icon: '🔄' },
  { id: 'todos',     enabled: true,  order: 9, icon: '✅' },
];

const DEFAULT_THEME = {
  contextLow:  'brightGreen',
  contextMid:  'brightYellow',
  contextHigh: 'brightRed',
  accent:      'brightCyan',
  muted:       'dim',
  separator:   'dim',
};

function getContextColorName(percent, theme) {
  if (percent >= 80) return theme.contextHigh || 'brightRed';
  if (percent >= 50) return theme.contextMid || 'brightYellow';
  return theme.contextLow || 'brightGreen';
}

function getQuotaColorName(usageWindows, theme) {
  const percents = Array.isArray(usageWindows)
    ? usageWindows
      .map((windowText) => {
        const match = String(windowText).match(/(\d+)%/);
        return match ? Number(match[1]) : null;
      })
      .filter((percent) => Number.isFinite(percent))
    : [];
  if (!theme.quotaLow && !theme.quotaHigh) return theme.muted;
  return percents.some((percent) => percent >= 85)
    ? (theme.quotaHigh || theme.quotaLow || theme.muted)
    : (theme.quotaLow || theme.muted);
}

// Per-character neon bar: uniform colorName on filled chars, dim on empty.
// colorName defaults to threshold-based color when omitted.
function colorNeonBar(percent, width = 12, colorName = null) {
  const raw = neonBar(percent, width, { style: 'sweep' });
  const filled = Math.max(0, Math.min(width, Math.round(percent / 100 * width)));
  const barColor = colorName || (percent >= 80 ? 'brightRed' : percent >= 50 ? 'brightYellow' : 'brightGreen');
  return raw.split('').map((char, i) =>
    i < filled ? colorizeChar(char, barColor) : colorizeChar(char, 'dim')
  ).join('');
}

// --- Section renderers ---
function renderBrandSection(ctx, sectionConfig, theme) {
  const label = sectionConfig.label || 'TAKUMI';
  const icon  = sectionConfig.icon  || '◆';
  return brightMagenta(`${icon} ${label}`);
}

function renderModelSection(ctx, sectionConfig, theme) {
  const colorFn = resolveColor(sectionConfig.color || theme.accent);
  return colorFn(ctx.modelName);
}

// "████▓░░░░░░░ 40%" — null when contextPercent is 0
function renderContextSection(ctx, sectionConfig, theme) {
  if (!(ctx.contextPercent > 0)) return null;
  const colorName = getContextColorName(ctx.contextPercent, theme);
  const percentColor = resolveColor(colorName);
  return `${colorNeonBar(ctx.contextPercent, 12, colorName)} ${percentColor(`${ctx.contextPercent}%`)}`;
}

// "⏳ 5h ████▓░ 20%  wk ██▓░ 45%" — null when no usage windows
function renderQuotaSection(ctx, sectionConfig, theme) {
  if (!ctx.usageWindows || ctx.usageWindows.length === 0) return null;
  const icon = sectionConfig.icon || '⏳';
  const parts = ctx.usageWindows.map(windowText => {
    const match = String(windowText).match(/^(\w+)\s+(\d+)%(.*)/);
    if (!match) return resolveColor('dim')(windowText);
    const [, label, pctStr, rest] = match;
    const pct = parseInt(pctStr, 10);
    const pctColorName = pct >= 85
      ? (theme.quotaHigh || 'brightRed')
      : (theme.quotaLow  || 'brightGreen');
    const miniBar = colorNeonBar(pct, 4, pctColorName);
    const pctColor = resolveColor(pctColorName);
    return `${label} ${miniBar} ${pctColor(`${pct}%${rest}`)}`;
  });
  return `${icon} ${parts.join('  ')}`;
}

// "📂 ~/project" — current working directory
function renderDirectorySection(ctx, sectionConfig, theme) {
  return `${sectionConfig.icon || '📂'} ${resolveColor(sectionConfig.color || 'yellow')(ctx.currentDir)}`;
}

// "✦ main (2, +1, 3↑)" — null outside git repos
function renderGitSection(ctx, sectionConfig, theme) {
  if (!ctx.gitBranch) return null;
  const gitColorFn = resolveColor(sectionConfig.color || 'magenta');
  let part = `${sectionConfig.icon || '✦'} ${gitColorFn(ctx.gitBranch)}`;
  const indicators = [];
  if (ctx.gitUnstaged > 0) indicators.push(`${ctx.gitUnstaged}`);
  if (ctx.gitStaged > 0)   indicators.push(`+${ctx.gitStaged}`);
  if (ctx.gitAhead > 0)    indicators.push(`${ctx.gitAhead}↑`);
  if (ctx.gitBehind > 0)   indicators.push(`${ctx.gitBehind}↓`);
  if (indicators.length > 0) part += ` ${yellow(`(${indicators.join(', ')})`)}`;
  return part;
}

// "💰 $0.42" — null when no cost data
function renderCostSection(ctx, sectionConfig, theme) {
  if (!ctx.costText) return null;
  return `${sectionConfig.icon || '💰'} ${resolveColor(sectionConfig.color || 'dim')(ctx.costText)}`;
}

// "+10 −5" — null when no lines changed; sectionConfig.color applies a uniform color override
function renderChangesSection(ctx, sectionConfig, theme) {
  if (ctx.linesAdded <= 0 && ctx.linesRemoved <= 0) return null;
  if (sectionConfig.color) {
    const changeFn = resolveColor(sectionConfig.color);
    return changeFn(`+${ctx.linesAdded} −${ctx.linesRemoved}`);
  }
  return `${green(`+${ctx.linesAdded}`)} ${red(`−${ctx.linesRemoved}`)}`;
}

const SECTION_RENDERERS = {
  brand:     renderBrandSection,
  model:     renderModelSection,
  context:   renderContextSection,
  quota:     renderQuotaSection,
  directory: renderDirectorySection,
  git:       renderGitSection,
  cost:      renderCostSection,
  changes:   renderChangesSection,
};

function getSectionRenderer(id) {
  return SECTION_RENDERERS[id] || null;
}

/**
 * Resolve effective layout from statuslineLayout config, falling back to defaults.
 * Accepts the new lines[][] format and the legacy sections[] format.
 * Absent or null statuslineLayout → defaults only, matching pre-refactor output exactly.
 * @param {Object|undefined} statuslineLayout - From .tkm.json config
 * @returns {{ sections, theme, responsiveBreakpoint, maxAgentRows, todoTruncation }}
 */
function resolveLayout(statuslineLayout) {
  if (!statuslineLayout || typeof statuslineLayout !== 'object') {
    return {
      sections: DEFAULT_SECTIONS.slice(),
      theme: { ...DEFAULT_THEME },
      responsiveBreakpoint: 0.85,
      maxAgentRows: 4,
      todoTruncation: 50,
    };
  }

  const defaultById = {};
  for (const s of DEFAULT_SECTIONS) defaultById[s.id] = s;
  const sectionConfig = (statuslineLayout.sectionConfig && typeof statuslineLayout.sectionConfig === 'object')
    ? statuslineLayout.sectionConfig : {};

  let sections;

  if (Array.isArray(statuslineLayout.lines)) {
    // lines[][] format: flatten to ordered sections array with per-section config merged in
    let order = 0;
    sections = [];
    for (const line of statuslineLayout.lines) {
      if (!Array.isArray(line)) continue;
      for (const id of line) {
        const base = defaultById[id] || { id, enabled: true, order: 99 };
        const cfg = sectionConfig[id] || {};
        sections.push({ ...base, ...cfg, id, enabled: true, order: order++ });
      }
    }
  } else if (Array.isArray(statuslineLayout.sections)) {
    // Legacy sections[] format — backward compat
    sections = statuslineLayout.sections
      .map((cs) => {
        const cfg = sectionConfig[cs.id] || {};
        return { ...(defaultById[cs.id] || { id: cs.id, enabled: true, order: 99 }), ...cfg, ...cs };
      })
      .filter(s => s.id)
      .sort((a, b) => (a.order || 0) - (b.order || 0));
  } else {
    sections = DEFAULT_SECTIONS.slice();
  }

  // Guard: string theme (e.g. "dark") would spread as {0:"d",1:"a",...} — reject non-objects
  const themeInput = statuslineLayout.theme;
  const themeOverride = (themeInput && typeof themeInput === 'object' && !Array.isArray(themeInput)) ? themeInput : {};
  // Forward original lines config so render modes know which sections belong on which line
  const configLines = Array.isArray(statuslineLayout.lines) ? statuslineLayout.lines : null;

  return {
    sections,
    configLines,
    theme: { ...DEFAULT_THEME, ...themeOverride },
    themeOverrides: { ...themeOverride },
    responsiveBreakpoint: typeof statuslineLayout.responsiveBreakpoint === 'number'
      ? Math.max(0.5, Math.min(1.0, statuslineLayout.responsiveBreakpoint)) : 0.85,
    maxAgentRows: typeof statuslineLayout.maxAgentRows === 'number'
      ? statuslineLayout.maxAgentRows : 4,
    todoTruncation: typeof statuslineLayout.todoTruncation === 'number'
      ? statuslineLayout.todoTruncation : 50,
  };
}

module.exports = {
  DEFAULT_SECTIONS,
  DEFAULT_THEME,
  getContextColorName,
  getSectionRenderer,
  getQuotaColorName,
  resolveLayout,
};
