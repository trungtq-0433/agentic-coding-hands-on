'use strict';

/**
 * Statusline render-mode builders: full, compact, minimal.
 * All three are config-driven via a resolved layout (from resolveLayout()).
 * Absent statuslineLayout in .tkm.json → output matches the pre-refactor renderer exactly.
 *
 * Mode signatures: (ctx, layout) => void  — write lines via console.log.
 *
 * @module statusline-render-modes
 */

const { red, dim, resolveColor } = require('./colors.cjs');
const {
  DEFAULT_SECTIONS,
  getContextColorName,
  getQuotaColorName,
  getSectionRenderer
} = require('./statusline-section-registry.cjs');
const { visibleLength, getTerminalWidth } = require('./statusline-string-utils.cjs');
const { renderAgentsLines, renderTodosLine } = require('./statusline-activity-renderers.cjs');

/**
 * Look up and render a single section by ID — shared by all render modes.
 * @param {Object[]} enabledSections - Sections with enabled !== false
 * @param {string} id - Section ID
 * @param {Object} ctx - Render context
 * @param {Object} theme - Theme config
 * @returns {string} Rendered text, or '' if section is disabled or missing
 */
function renderSection(enabledSections, id, ctx, theme) {
  const sec = enabledSections.find(s => s.id === id);
  if (!sec) return '';
  const fn = getSectionRenderer(id);
  return (fn && fn(ctx, sec, theme)) || '';
}

/**
 * Render layout.configLines (user's lines[][] config) in order.
 * Agents and todos are excluded here — render() handles them as multi-line sections.
 */
function renderConfiguredLines(ctx, layout) {
  const effectiveSections = layout.sections.length > 0 ? layout.sections : DEFAULT_SECTIONS;
  const enabledSections = effectiveSections.filter(s => s.enabled !== false);
  const rs = (id) => renderSection(enabledSections, id, ctx, layout.theme);

  const lines = [];
  for (const configLine of layout.configLines) {
    // agents/todos go through render() as multi-line sections — skip them here
    const ids = configLine.filter(id => id !== 'agents' && id !== 'todos');
    if (ids.length === 0) continue;
    const rendered = ids.map(rs).filter(Boolean).join('  ');
    if (rendered) lines.push(rendered);
  }
  return lines;
}

/**
 * Build session lines with responsive wrapping (legacy path when no lines config).
 * @param {Object} ctx    - Render context
 * @param {Object} layout - Resolved layout from resolveLayout()
 * @returns {string[]}
 */
function renderSessionLines(ctx, layout) {
  // User-configured lines take priority
  if (layout.configLines && layout.configLines.length > 0) {
    return renderConfiguredLines(ctx, layout);
  }

  // Legacy responsive wrapping — backward compat when no lines config present
  const termWidth = getTerminalWidth();
  const threshold = Math.floor(termWidth * (layout.responsiveBreakpoint || 0.85));
  const effectiveSections = layout.sections.length > 0 ? layout.sections : DEFAULT_SECTIONS;
  const enabledSections = effectiveSections.filter(s => s.enabled !== false);

  const rs = (id) => renderSection(enabledSections, id, ctx, layout.theme);

  const dirPart    = rs('directory');
  const branchPart = rs('git');
  const sessionPart = ['brand', 'model', 'context', 'quota']
    .map(rs).filter(Boolean).join('  ');
  const statsPart = ['cost', 'changes']
    .map(rs).filter(Boolean).join('  ');

  const locationPart = branchPart ? `${dirPart}  ${branchPart}` : dirPart;
  const statsLen     = visibleLength(statsPart);

  const allOneLine     = `${sessionPart}  ${locationPart}  ${statsPart}`;
  const sessionLocation = `${sessionPart}  ${locationPart}`;

  const lines = [];
  if (visibleLength(allOneLine) <= threshold && statsLen > 0) {
    lines.push(allOneLine);
  } else if (visibleLength(sessionLocation) <= threshold) {
    lines.push(sessionLocation);
    if (statsLen > 0) lines.push(statsPart);
  } else if (visibleLength(sessionPart) <= threshold) {
    lines.push(sessionPart);
    lines.push(locationPart);
    if (statsLen > 0) lines.push(statsPart);
  } else {
    lines.push(sessionPart);
    if (dirPart)    lines.push(dirPart);
    if (branchPart) lines.push(branchPart);
    if (statsLen > 0) lines.push(statsPart);
  }

  return lines;
}

/**
 * Full render: session lines plus optional agents and todos.
 * @param {Object}  ctx
 * @param {Object}  layout
 * @param {boolean} singleLineMode - Skip agents/todos when true
 */
function render(ctx, layout, singleLineMode) {
  const lines = [...renderSessionLines(ctx, layout)];

  if (!singleLineMode) {
    const effectiveSectionsForEnabled = layout.sections.length > 0 ? layout.sections : DEFAULT_SECTIONS;
    const isEnabled = id => effectiveSectionsForEnabled.some(s => s.id === id && s.enabled !== false);
    const getSectionConfig = id => effectiveSectionsForEnabled.find(s => s.id === id && s.enabled !== false) || {};

    if (isEnabled('agents')) {
      lines.push(...renderAgentsLines(ctx.transcript, layout.maxAgentRows, getSectionConfig('agents')));
    }
    if (isEnabled('todos')) {
      const todosLine = renderTodosLine(ctx.transcript, layout.todoTruncation, getSectionConfig('todos'));
      if (todosLine) lines.push(todosLine);
    }
  }

  for (const line of lines) console.log(line);
}

/**
 * Compact render: first 2 configured lines, or session info then location.
 * @param {Object} ctx
 * @param {Object} layout
 */
function renderCompact(ctx, layout) {
  if (layout.configLines && layout.configLines.length > 0) {
    // Compact: first 2 configured lines only
    const lines = renderConfiguredLines(ctx, layout);
    for (const line of lines.slice(0, 2)) console.log(line);
    return;
  }
  // Legacy fallback — no lines config
  const effectiveSections = layout.sections.length > 0 ? layout.sections : DEFAULT_SECTIONS;
  const enabledSections = effectiveSections.filter(s => s.enabled !== false);
  const rs = (id) => renderSection(enabledSections, id, ctx, layout.theme);

  console.log(['brand', 'model', 'context', 'quota'].map(rs).filter(Boolean).join('  '));
  console.log(['directory', 'git'].map(rs).filter(Boolean).join('  '));
}

/**
 * Minimal render: single line, battery icon instead of progress bar for context.
 * @param {Object} ctx
 * @param {Object} layout
 */
function renderMinimal(ctx, layout) {
  if (layout.configLines && layout.configLines.length > 0) {
    // Minimal: first configured line only
    const lines = renderConfiguredLines(ctx, layout);
    if (lines.length > 0) console.log(lines[0]);
    return;
  }
  // Legacy fallback — no lines config
  const effectiveSections = layout.sections.length > 0 ? layout.sections : DEFAULT_SECTIONS;
  const enabledSections = effectiveSections.filter(s => s.enabled !== false);
  const isEnabled = id => enabledSections.some(s => s.id === id);
  const rs = (id) => renderSection(enabledSections, id, ctx, layout.theme);
  const getSectionConfig = (id) => enabledSections.find(s => s.id === id) || {};
  const themeOverrides = layout.themeOverrides || {};

  const parts = [];

  if (isEnabled('brand'))   parts.push(rs('brand'));
  if (isEnabled('model'))   parts.push(rs('model'));

  // Minimal: swap progress bar for battery icon
  if (ctx.contextPercent > 0 && isEnabled('context')) {
    const batteryConfig = getSectionConfig('context');
    const batteryGlyph = batteryConfig.icon || '🔋';
    const hasCustomContextTheme = ['contextLow', 'contextMid', 'contextHigh']
      .some((key) => Object.prototype.hasOwnProperty.call(themeOverrides, key));
    const batteryIcon = hasCustomContextTheme
      ? resolveColor(getContextColorName(ctx.contextPercent, layout.theme))(batteryGlyph)
      : (ctx.contextPercent > 70 ? red(batteryGlyph) : batteryGlyph);
    parts.push(`${batteryIcon} ${ctx.contextPercent}%`);
  }

  if (ctx.usageWindows?.length > 0 && isEnabled('quota')) {
    const quotaConfig = getSectionConfig('quota');
    const hasCustomQuotaTheme = Object.prototype.hasOwnProperty.call(themeOverrides, 'quotaLow')
      || Object.prototype.hasOwnProperty.call(themeOverrides, 'quotaHigh');
    const quotaText = ctx.usageWindows.join('  ');
    const quotaColor = quotaConfig.color || (hasCustomQuotaTheme ? getQuotaColorName(ctx.usageWindows, layout.theme) : null);
    parts.push(`${quotaConfig.icon || '⏰'} ${quotaColor ? resolveColor(quotaColor)(quotaText) : dim(quotaText)}`);
  }

  if (ctx.gitBranch && isEnabled('git')) {
    parts.push(rs('git'));
  }

  if (isEnabled('directory')) parts.push(rs('directory'));

  console.log(parts.filter(Boolean).join('  '));
}

module.exports = { renderSessionLines, render, renderCompact, renderMinimal };
