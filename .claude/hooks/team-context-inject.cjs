#!/usr/bin/env node
/**
 * SubagentStart hook — orients a freshly-spawned Agent Team member.
 *
 * Fires: SubagentStart — every time a subagent is started.
 * Flow:  Study stage — gives the teammate situational awareness before it acts.
 *
 * Only activates when the agent_id carries the "name@team-name" pattern that
 * marks a team member. Non-team subagents pass through without output.
 * Injects peer roster, live task counts, and TKM stack paths so the teammate
 * can claim work and communicate without reading config files itself.
 *
 * Exit 0 always (fail-open). No network I/O.
 */

// Crash wrapper
try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');

  if (!isHookEnabled('team-context-inject')) {
    process.exit(0);
  }

const TEAMS_DIR = path.join(os.homedir(), '.claude', 'teams');
const TASKS_DIR = path.join(os.homedir(), '.claude', 'tasks');

/**
 * Extract team name from agent_id (format: "name@team-name").
 * Returns null for non-team agents or if the name contains path separators.
 */
function extractTeamName(agentId) {
  if (!agentId || typeof agentId !== 'string') return null;
  const atIdx = agentId.indexOf('@');
  if (atIdx < 1) return null;
  const name = agentId.substring(atIdx + 1);
  // Guard against path traversal — team name feeds a filesystem path.
  if (name.includes('/') || name.includes('\\') || name.includes('..')) return null;
  return name;
}

/** Read and parse JSON file; returns null on any error. */
function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    return null;
  }
}

/** Build a readable peer list from team config, excluding the current agent. */
function buildPeerList(config, currentAgentId) {
  if (!config?.members?.length) return '';
  const peers = config.members
    .filter(m => m.agentId !== currentAgentId)
    .map(m => `${m.name} (${m.agentType})`)
    .join(', ');
  return peers || 'none';
}

/**
 * Collect TKM stack paths from environment variables.
 * session-init.cjs sets these; SubagentStart propagates them to each teammate.
 */
function buildSkContext() {
  const ctx = [];
  const env = process.env;

  if (env.TKM_REPORTS_PATH) ctx.push(`Reports: ${env.TKM_REPORTS_PATH}`);
  if (env.TKM_PLANS_PATH) ctx.push(`Plans: ${env.TKM_PLANS_PATH}`);
  if (env.TKM_PROJECT_ROOT) ctx.push(`Project: ${env.TKM_PROJECT_ROOT}`);
  if (env.TKM_NAME_PATTERN) ctx.push(`Naming: ${env.TKM_NAME_PATTERN}`);
  if (env.TKM_GIT_BRANCH) ctx.push(`Branch: ${env.TKM_GIT_BRANCH}`);
  if (env.TKM_ACTIVE_PLAN) ctx.push(`Active plan: ${env.TKM_ACTIVE_PLAN}`);
  ctx.push('Commits: conventional (feat:, fix:, docs:, refactor:, test:, chore:)');

  return ctx;
}

/** Count tasks by status for the given team. */
function summarizeTasks(teamName) {
  const taskDir = path.join(TASKS_DIR, teamName);
  try {
    if (!fs.existsSync(taskDir)) return null;
    const files = fs.readdirSync(taskDir).filter(f => f.endsWith('.json'));
    let pending = 0, inProgress = 0, completed = 0;
    for (const file of files) {
      const task = readJson(path.join(taskDir, file));
      if (!task?.status) continue;
      if (task.status === 'pending') pending++;
      else if (task.status === 'in_progress') inProgress++;
      else if (task.status === 'completed') completed++;
    }
    return { pending, inProgress, completed, total: files.length };
  } catch {
    return null;
  }
}

/** Hook entry point. */
function main() {
  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) process.exit(0);

    const payload = JSON.parse(stdin);
    const agentId = payload.agent_id || '';

    // Non-team subagents exit immediately — nothing to inject.
    const teamName = extractTeamName(agentId);
    if (!teamName) process.exit(0);

    const configPath = path.join(TEAMS_DIR, teamName, 'config.json');
    const config = readJson(configPath);
    if (!config) process.exit(0);

    const peerList = buildPeerList(config, agentId);
    const tasks = summarizeTasks(teamName);

    const lines = [];
    lines.push(`## Team Context`);
    lines.push(`Team: ${config.name || teamName}`);
    lines.push(`Your peers: ${peerList}`);

    if (tasks) {
      lines.push(`Task summary: ${tasks.pending} pending, ${tasks.inProgress} in progress, ${tasks.completed} completed`);
    }

    // Append TKM stack paths so the teammate doesn't need to scan session-init output.
    const skCtx = buildSkContext();
    if (skCtx.length > 0) {
      lines.push('');
      lines.push('## TKM Context');
      lines.push(...skCtx);
    }

    lines.push('');
    lines.push('Remember: Check TaskList, claim tasks, respect file ownership, use SendMessage to communicate.');

    const output = {
      hookSpecificOutput: {
        hookEventName: "SubagentStart",
        additionalContext: lines.join('\n')
      }
    };

    console.log(JSON.stringify(output));
    process.exit(0);
  } catch (error) {
    // Fail-open — a missing context block must never abort a teammate spawn.
    if (process.env.TKM_DEBUG) {
      console.error(`[team-context-inject] Error: ${error.message}`);
    }
    process.exit(0);
  }
  }

  main();
} catch (e) {
  // Last-resort crash log using only Node builtins — no deps available here.
  try {
    const fs = require('fs');
    const p = require('path');
    const logDir = p.join(__dirname, '.logs');
    if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
    fs.appendFileSync(p.join(logDir, 'hook-log.jsonl'),
      JSON.stringify({ ts: new Date().toISOString(), hook: p.basename(__filename, '.cjs'), status: 'crash', error: e.message }) + '\n');
  } catch (_) {}
  process.exit(0);
}
