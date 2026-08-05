#!/usr/bin/env node
/**
 * TaskCompleted hook — records task closure and surfaces team progress to the lead.
 *
 * Fires: TaskCompleted — when any teammate calls TaskUpdate with status: completed,
 *        or finishes a turn while tasks remain in-progress.
 * Docs:  https://code.claude.com/docs/en/hooks#taskcompleted
 * Flow:  Deliver stage — the moment a Forge unit closes.
 *
 * Exit 0 always (fail-open). additionalContext is informational; Claude Code may
 * ignore it for this event. Appends a markdown log line to TKM_REPORTS_PATH so
 * the lead has a durable audit trail across turns.
 *
 * Input:  { task_id, task_subject, task_description, teammate_name, team_name, … }
 * Output: additionalContext — progress summary (completed/total, unblocked notice).
 */

// Crash wrapper
try {
  const fs = require('fs');
  const path = require('path');
  const os = require('os');
  const { isHookEnabled } = require('./lib/tkm-config-utils.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  if (!isHookEnabled('task-completed-handler')) {
    process.exit(0);
  }

const TASKS_DIR = path.join(os.homedir(), '.claude', 'tasks');

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch { return null; }
}

function countTasks(teamName) {
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
    return { pending, inProgress, completed, total: pending + inProgress + completed };
  } catch { return null; }
}

/** Resolve a candidate plan directory from the task payload, if any. */
function resolvePlanDir(payload) {
  return (
    payload.plan_dir ||
    payload.planDir ||
    (payload.task_metadata && payload.task_metadata.planDir) ||
    (payload.metadata && payload.metadata.planDir) ||
    null
  );
}

/**
 * Advisory evidence check: if the completing task's plan has an evidence/ dir,
 * run the validator at ADVISORY stage and surface any gaps. Never blocks task
 * tooling (the hard block lives at the ship/Deliver gate). Returns markdown lines
 * (empty when there is no evidence dir or nothing to surface).
 */
function evidenceAdvisory(planDir) {
  if (!planDir) return [];
  try {
    const evidenceDir = path.join(planDir, 'evidence');
    if (!fs.existsSync(evidenceDir)) return [];
    const { validateEvidence } = require('./lib/evidence-validator.cjs');
    const r = validateEvidence({ evidenceDir, stage: 'advisory' });
    const gaps = r.blocking.concat(r.warnings);
    if (!gaps.length) return ['', '_Evidence check: artifacts present, no gaps surfaced (advisory)._'];
    const lines = ['', `**Evidence gaps (advisory — ${gaps.length}):**`];
    for (const g of gaps) lines.push(`- ${g}`);
    lines.push('_Advisory only — completion is not blocked. The hard gate runs at ship/Deliver._');
    return lines;
  } catch { return []; /* fail-open */ }
}

function logCompletion(teamName, taskId, taskSubject, teammateName) {
  const reportsPath = process.env.TKM_REPORTS_PATH;
  if (!reportsPath) return;
  const logFile = path.join(reportsPath, `team-${teamName}-completions.md`);
  try {
    fs.mkdirSync(path.dirname(logFile), { recursive: true });
    const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
    const line = `- [${timestamp}] Task #${taskId} "${taskSubject}" completed by ${teammateName}\n`;
    fs.appendFileSync(logFile, line);
  } catch { /* fail-open */ }
}

function main() {
  const timer = createHookTimer('task-completed-handler', { event: 'TaskCompleted' });
  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) {
      timer.end({ status: 'skip', exit: 0, note: 'empty-input' });
      process.exit(0);
    }

    const payload = JSON.parse(stdin);
    const { task_id, task_subject, teammate_name, team_name } = payload;

    // Advisory evidence check — runs for solo tasks too (before the team guard).
    const evidenceLines = evidenceAdvisory(resolvePlanDir(payload));

    if (!team_name) {
      // No team context: still surface evidence gaps if this task is plan-backed.
      if (evidenceLines.length) {
        const ctx = [`## Task Completed`, `Task #${task_id} "${task_subject}" completed.`]
          .concat(evidenceLines)
          .join('\n');
        console.log(JSON.stringify({
          hookSpecificOutput: { hookEventName: 'TaskCompleted', additionalContext: ctx },
        }));
        timer.end({ status: 'ok', exit: 0, note: 'evidence-advisory-no-team' });
        process.exit(0);
      }
      timer.end({ status: 'skip', exit: 0, note: 'missing-team-name' });
      process.exit(0);
    }

    // Append to the team's completion log; durable across turns.
    logCompletion(team_name, task_id, task_subject, teammate_name);

    // Snapshot task counts so the lead sees remaining work at a glance.
    const counts = countTasks(team_name);
    const lines = [];
    lines.push(`## Task Completed`);
    lines.push(`Task #${task_id} "${task_subject}" completed by ${teammate_name}.`);

    if (counts) {
      const remaining = counts.pending + counts.inProgress;
      lines.push(`Progress: ${counts.completed}/${counts.total} done. ${counts.pending} pending, ${counts.inProgress} in progress.`);
      if (remaining === 0) {
        lines.push('');
        lines.push('**All tasks completed.** Consider shutting down teammates and synthesizing results.');
      }
    }

    // Surface evidence gaps (advisory) alongside team progress.
    for (const l of evidenceLines) lines.push(l);

    const output = {
      hookSpecificOutput: {
        hookEventName: 'TaskCompleted',
        additionalContext: lines.join('\n')
      }
    };
    console.log(JSON.stringify(output));
    timer.end({ status: 'ok', exit: 0, target: String(task_id || ''), note: 'completion-logged' });
    process.exit(0);
  } catch (error) {
    if (process.env.TKM_DEBUG) {
      console.error(`[task-completed-handler] Error: ${error.message}`);
    }
    logHookCrash('task-completed-handler', error, { event: 'TaskCompleted' });
    process.exit(0);
  }
  }

  main();
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('task-completed-handler', e, { event: 'TaskCompleted' });
  } catch (_) {}
  process.exit(0); // fail-open
}
