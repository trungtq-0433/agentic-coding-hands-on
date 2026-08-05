#!/usr/bin/env node
'use strict';

/**
 * Milestone marker — stamps milestone_completed on the per-session state so the
 * Stop telemetry hook can read it when the session ends.
 *
 * Called as a trailing step by /tkm:takumi, /tkm:ship, and /tkm:create-plan:
 *   node milestone-marker.cjs --kind=takumi --session-id="$CLAUDE_SESSION_ID"
 *
 * Always exits 0 — marking is best-effort, not load-bearing.
 *
 * @module milestone-marker
 */

const { updateSessionState } = require('./tkm-config-utils.cjs');

const ALLOWED_KINDS = new Set(['takumi', 'ship', 'plan']);

function parseArgs(argv) {
  const args = {};
  for (const raw of argv) {
    const m = raw.match(/^--([^=]+)=(.*)$/);
    if (m) args[m[1]] = m[2];
  }
  return args;
}

function markMilestone({ kind, sessionId, now = new Date() }) {
  if (!sessionId || !ALLOWED_KINDS.has(kind)) return false;
  return updateSessionState(sessionId, (state) => ({
    ...state,
    milestone_completed: kind,
    milestone_at: now.toISOString(),
  }));
}

if (require.main === module) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const sessionId = args['session-id'] || process.env.CLAUDE_SESSION_ID || process.env.TKM_SESSION_ID || '';
    const kind = args.kind || '';
    const ok = markMilestone({ kind, sessionId });
    process.stdout.write(JSON.stringify({ ok, kind, sessionId: sessionId || null }) + '\n');
  } catch (e) {
    process.stderr.write(`[milestone] ${e?.message || e}\n`);
  }
  process.exit(0);
}

module.exports = { ALLOWED_KINDS, markMilestone, parseArgs };
