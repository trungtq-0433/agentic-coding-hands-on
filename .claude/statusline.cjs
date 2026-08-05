#!/usr/bin/env node
'use strict';

// Reads a JSON status object from stdin, writes one ANSI statusline to stdout.
// Layout is driven by statuslineLayout in .tkm.json; absent → legacy defaults.

const proc = require('process');
const os   = require('os');
const fs   = require('fs');
const path = require('path');

const { setColorEnabled }   = require('./hooks/lib/colors.cjs');
const { loadConfig, readSessionState } = require('./hooks/lib/tkm-config-utils.cjs');
const { getGitInfo }        = require('./hooks/lib/git-info-cache.cjs');
const { readActivitySnapshot } = require('./hooks/lib/statusline-session-cache.cjs');
const {
  readUsageCache,
  normalizeUtilization,
  isUsageCacheFresh,
  resolveQuotaDisplayEligibility
} = require('./hooks/lib/usage-limits-cache.cjs');
const { resolveLayout }     = require('./hooks/lib/statusline-section-registry.cjs');
const { render, renderCompact, renderMinimal } = require('./hooks/lib/statusline-render-modes.cjs');
const { formatCountdown }   = require('./hooks/lib/statusline-string-utils.cjs');

// How many tokens ahead of context size to trigger compact auto-threshold.
const AUTOCOMPACT_BUFFER = 40000;
// Usage cache older than this is stale for rendering purposes.
const USAGE_CACHE_RENDER_TTL_MS = 300000;

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

// Collapse $HOME prefix to ~ for display.
function collapseHome(p) {
  const home = os.homedir();
  return p.startsWith(home) ? p.replace(home, '~') : p;
}

// Drain stdin; optional inactivity timeout via TKM_STATUSLINE_STDIN_TIMEOUT_MS.
function drainStdin() {
  return new Promise((resolve, reject) => {
    const buf = [];
    proc.stdin.setEncoding('utf8');

    const rawMs = proc.env.TKM_STATUSLINE_STDIN_TIMEOUT_MS || '';
    const parsed = Number.parseInt(rawMs, 10);
    const waitMs = Number.isFinite(parsed) && parsed > 0 ? parsed : 0;

    let watchdog = null;

    function cancelWatchdog() {
      if (watchdog) { clearTimeout(watchdog); watchdog = null; }
    }

    function resetWatchdog() {
      if (!waitMs) return;
      cancelWatchdog();
      watchdog = setTimeout(
        () => reject(new Error(`stdin timeout after ${waitMs}ms`)),
        waitMs
      );
    }

    resetWatchdog();
    proc.stdin.on('data',  chunk => { buf.push(chunk); resetWatchdog(); });
    proc.stdin.on('end',   ()    => { cancelWatchdog(); resolve(buf.join('')); });
    proc.stdin.on('error', err   => { cancelWatchdog(); reject(err); });
  });
}

// Convert usage-limits cache into displayable window strings, e.g. ["5h 20% (1h30m)", "wk 45% (4d)"].
function quotaWindows(cache) {
  if (!cache || cache.status !== 'available') return [];
  if (!isUsageCacheFresh(cache, USAGE_CACHE_RENDER_TTL_MS)) return [];

  const now = Date.now();

  // Prefer snapshot percentages — they include reset countdowns when available.
  const fromSnapshot = [
    { label: '5h', percent: cache.snapshot?.fiveHourPercent, resetsAt: cache.data?.five_hour?.resets_at },
    { label: 'wk', percent: cache.snapshot?.weekPercent,     resetsAt: cache.data?.seven_day?.resets_at }
  ].map(({ label, percent, resetsAt }) => {
    if (percent == null) return null;
    let suffix = '';
    if (resetsAt) {
      const cd = formatCountdown(new Date(resetsAt).getTime() - now);
      if (cd) suffix = ` (${cd})`;
    }
    return `${label} ${percent}%${suffix}`;
  }).filter(Boolean);

  if (fromSnapshot.length > 0) return fromSnapshot;

  // Raw utilization fallback — no countdown available here.
  return [
    { label: '5h', value: cache.data?.five_hour?.utilization },
    { label: 'wk', value: cache.data?.seven_day?.utilization }
  ].map(({ label, value }) => {
    const pct = normalizeUtilization(value);
    return pct == null ? null : `${label} ${pct}%`;
  }).filter(Boolean);
}

// ──────────────────────────────────────────────────────────────────────────────
// Entry point
// ──────────────────────────────────────────────────────────────────────────────

async function run() {
  try {
    const raw = await drainStdin();
    if (!raw.trim()) { console.error('No input provided'); process.exit(1); }

    const payload = JSON.parse(raw);

    // Working directory — prefer workspace field, collapse home for display.
    let workDir = payload.workspace?.current_dir || payload.cwd || 'unknown';
    workDir = collapseHome(workDir);

    const modelLabel = payload.model?.display_name || 'Claude';

    // Git state for the working directory.
    const git = getGitInfo(payload.workspace?.current_dir || payload.cwd || process.cwd());
    const gitBranch   = git?.branch   || '';
    const gitUnstaged = git?.unstaged || 0;
    const gitStaged   = git?.staged   || 0;
    const gitAhead    = git?.ahead    || 0;
    const gitBehind   = git?.behind   || 0;

    // Active plan slug + activity snapshot from session state.
    let activePlan = '';
    let transcript = { agents: [], todos: [], sessionStart: null };
    try {
      const sid = payload.session_id;
      if (sid) {
        const sess = readSessionState(sid);
        const raw_plan = sess?.activePlan?.trim();
        if (raw_plan) {
          const m = raw_plan.match(/plans\/\d+-\d+-(.+?)(?:\/|$)/);
          activePlan = m ? m[1] : raw_plan.split('/').pop();
        }
        transcript = readActivitySnapshot(sid, readSessionState) || transcript;
      }
    } catch {}

    // Context window utilization.
    const usageFields = payload.context_window?.current_usage || {};
    const windowSize  = payload.context_window?.context_window_size || 0;
    let ctxPct    = 0;
    let usedTokens = 0;
    if (windowSize > 0) {
      usedTokens = (usageFields.input_tokens ?? 0)
        + (usageFields.cache_creation_input_tokens ?? 0)
        + (usageFields.cache_read_input_tokens ?? 0);
      const pre = payload.context_window?.used_percentage;
      if (typeof pre === 'number' && pre >= 0) {
        ctxPct = Math.round(pre);
      } else if (windowSize > AUTOCOMPACT_BUFFER) {
        ctxPct = Math.min(100, Math.round(((usedTokens + AUTOCOMPACT_BUFFER) / windowSize) * 100));
      }
    }

    // Persist context snapshot for downstream hooks.
    const sid2 = payload.session_id;
    if (sid2 && windowSize > 0) {
      try {
        const ctxFile = path.join(os.tmpdir(), `sk-context-${sid2}.json`);
        fs.writeFileSync(ctxFile, JSON.stringify({
          percent:   ctxPct,
          remaining: payload.context_window?.remaining_percentage ?? (100 - ctxPct),
          tokens:    usedTokens,
          size:      windowSize,
          usage:     usageFields,
          timestamp: Date.now()
        }));
      } catch {}
    }

    // Load config; derive render mode and quota windows.
    const cfg = loadConfig({ includeProject: false, includeAssertions: false, includeLocale: false });
    const renderMode  = cfg.statusline || 'full';
    const usageSlots  = cfg.statuslineQuota === false
      ? []
      : (resolveQuotaDisplayEligibility({ useCache: true }).eligible
          ? quotaWindows(readUsageCache())
          : []);

    // Cost and diff stats.
    const billingMode = proc.env.CLAUDE_BILLING_MODE || 'api';
    const rawCost     = payload.cost?.total_cost_usd;
    const costText    = billingMode === 'api' && rawCost && /^\d+(\.\d+)?$/.test(String(rawCost))
      ? `$${parseFloat(rawCost).toFixed(4)}`
      : null;
    const linesAdded   = payload.cost?.total_lines_added   || 0;
    const linesRemoved = payload.cost?.total_lines_removed || 0;

    // Assemble render context.
    const ctx = {
      modelName:    modelLabel,
      currentDir:   workDir,
      gitBranch,    gitUnstaged, gitStaged, gitAhead, gitBehind,
      activePlan,   contextPercent: ctxPct, usageWindows: usageSlots,
      costText,     linesAdded, linesRemoved,
      transcript
    };

    // Honour explicit color disable from config (NO_COLOR env always wins inside isColorEnabled()).
    if (cfg.statuslineColors === false) setColorEnabled(false);

    // Layout: from config when present, else defaults.
    const layout = resolveLayout(cfg.statuslineLayout);

    switch (renderMode) {
      case 'none':    console.log(''); break;
      case 'minimal': renderMinimal(ctx, layout); break;
      case 'compact': renderCompact(ctx, layout); break;
      case 'full':
      default:        render(ctx, layout, false); break;
    }

  } catch {
    console.log('📁 ' + (process.cwd() || 'unknown'));
  }
}

run().catch(() => { console.log('📁 error'); process.exit(1); });
