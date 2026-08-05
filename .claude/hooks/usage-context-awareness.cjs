#!/usr/bin/env node
/**
 * Thin config-gate wrapper for the usage quota cache refresh.
 *
 * This hook name is the gate key: disabled via `usage-context-awareness` in
 * the config. The actual work — statusline cache warming — lives in
 * usage-quota-cache-refresh.cjs and is invoked directly below.
 */

'use strict';

try {
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { logHookCrash } = require('./lib/hook-logger.cjs');
  const { runUsageQuotaCacheRefreshHook } = require('./usage-quota-cache-refresh.cjs');

  if (!isHookEnabled('usage-context-awareness')) {
    console.log(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  runUsageQuotaCacheRefreshHook({
    hookName: 'usage-context-awareness',
    userAgent: 'takumi-agent-kit-engineer/usage-context-awareness'
  }).catch((error) => {
    logHookCrash('usage-context-awareness', error || 'main-catch');
    console.log(JSON.stringify({ continue: true }));
    process.exit(0);
  });
} catch (error) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('usage-context-awareness', error);
  } catch {}
  console.log(JSON.stringify({ continue: true }));
  process.exit(0);
}
