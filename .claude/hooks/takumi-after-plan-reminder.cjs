#!/usr/bin/env node
/**
 * SubagentStop hook (Plan agent) — bridges Blueprint to Forge.
 *
 * Fires when the Plan subagent finishes.
 * Reminds the session to invoke /tkm:takumi --auto before touching any code.
 * Emits the absolute plan path so sessions after /clear (or in a worktree) can locate it.
 *
 * Exit codes:
 *   0 — always (non-blocking)
 */

// Outer crash wrapper — reminder must never halt the session
try {
  const fs = require('fs');
  const path = require('path');
  const { isHookEnabled, readSessionState } = require('./lib/tkm-config-utils.cjs');

  // Skip without side-effects if disabled in tkm.config.json
  if (!isHookEnabled('takumi-after-plan-reminder')) {
    process.exit(0);
  }

  async function main() {
  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) process.exit(0);

    // Resolve the active plan path from session state; ensure it's absolute
    const sessionId = process.env.TKM_SESSION_ID;
    let planPath = null;

    if (sessionId) {
      const state = readSessionState(sessionId);
      if (state?.activePlan) {
        planPath = state.activePlan;
        // Relative paths come from older state — resolve against sessionOrigin
        if (!path.isAbsolute(planPath) && state.sessionOrigin) {
          planPath = path.resolve(state.sessionOrigin, planPath);
        }
      }
    }

    // Always emit the reminder; include full absolute path when available
    console.log('MUST invoke /tkm:takumi --auto skill before implementing the plan');
    if (planPath) {
      const planMdPath = path.join(planPath, 'plan.md');
      console.log(`Best Practice: Run /clear then /tkm:takumi ${planMdPath}`);
    } else {
      // Plan path not in state — emit generic reminder with placeholder
      console.log('Best Practice: Run /clear then /tkm:takumi {full-absolute-path-to-plan.md}');
    }

    process.exit(0);
  } catch (error) {
    // Reminder is best-effort; swallow errors and exit clean
    process.exit(0);
  }
  }

  main();
} catch (e) {
  // Minimal crash log (zero deps — Node builtins only)
  try {
    const fs = require('fs');
    const p = require('path');
    const logDir = p.join(__dirname, '.logs');
    if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
    fs.appendFileSync(p.join(logDir, 'hook-log.jsonl'),
      JSON.stringify({ ts: new Date().toISOString(), hook: p.basename(__filename, '.cjs'), status: 'crash', error: e.message }) + '\n');
  } catch (_) {}
  process.exit(0); // fail-open
}
