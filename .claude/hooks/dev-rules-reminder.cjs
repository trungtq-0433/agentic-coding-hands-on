#!/usr/bin/env node
/**
 * dev-rules-reminder — UserPromptSubmit hook. Study → Blueprint → Forge stages.
 *
 * On every user prompt, injects session context, active plan, and development
 * rules so the agent enters each Forge session with the full picture. Static
 * env facts (Node, Python, OS) arrive via SessionStart env vars rather than
 * being re-read here. Payload built by lib/context-builder.cjs, which is also
 * shared with the OpenCode plugin path.
 *
 * Injection is scoped per session + CWD to avoid redundant context on every
 * turn. A reservation prevents duplicate injection from concurrent triggers.
 *
 * Exit codes: 0 always — non-blocking.
 */

// Outer crash wrapper — fail-open so a broken hook never silences a prompt
try {
  const fs = require('fs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  // lib/context-builder.cjs owns all payload assembly; imported for reuse
  const {
    buildReminderContext,
    buildInjectionScopeKey,
    reserveInjectionScope,
    markRecentlyInjected,
    clearPendingInjection
  } = require('./lib/context-builder.cjs');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');

  if (!isHookEnabled('dev-rules-reminder')) {
    process.exit(0);
  }

// ═══════════════════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  const timer = createHookTimer('dev-rules-reminder', { event: 'UserPromptSubmit' });
  let sessionId = null;
  let scopeKey = 'session';
  let reservedScope = false;

  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) {
      timer.end({ status: 'skip', exit: 0, note: 'empty-input' });
      process.exit(0);
    }

    const payload = JSON.parse(stdin);
    sessionId = payload.session_id || process.env.TKM_SESSION_ID || null;

    // Issue #327: Use CWD as base for subdirectory workflow support
    // The baseDir is passed to buildReminderContext for absolute path resolution
    const baseDir = process.cwd();
    scopeKey = buildInjectionScopeKey({ baseDir });

    const reservation = reserveInjectionScope(sessionId, scopeKey, payload.transcript_path || null);
    reservedScope = reservation.reserved;
    if (!reservation.shouldInject) {
      timer.end({ status: 'skip', exit: 0, note: 'recently-injected' });
      process.exit(0);
    }

    // Use shared context builder with baseDir for absolute paths
    const { content } = buildReminderContext({ sessionId, baseDir });

    console.log(content);
    markRecentlyInjected(sessionId, scopeKey);
    timer.end({ status: 'ok', exit: 0, note: 'context-injected' });
    process.exit(0);
  } catch (error) {
    if (reservedScope) {
      clearPendingInjection(sessionId, scopeKey);
    }
    console.error(`Dev rules hook error: ${error.message}`);
    logHookCrash('dev-rules-reminder', error, { event: 'UserPromptSubmit' });
    process.exit(0);
  }
  }

  main();
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('dev-rules-reminder', e, { event: 'UserPromptSubmit' });
  } catch (_) {}
  process.exit(0); // fail-open
}
