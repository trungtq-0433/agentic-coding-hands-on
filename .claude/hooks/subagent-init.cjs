#!/usr/bin/env node
/**
 * SubagentStart hook — hands each spawned agent the minimal context it needs to act.
 *
 * Fires when a Task tool call starts a subagent.
 * Reads env vars from session-init rather than recomputing them.
 * Target payload: ~200 tokens (plan path, reports path, naming pattern, core rules).
 *
 * Exit codes:
 *   0 — always (fail-open)
 */

// Outer crash wrapper — subagent must start even if this hook fails
try {
  const fs = require('fs');
  const path = require('path');
  const {
    loadConfig,
    resolveNamingPattern,
    getGitBranch,
    getGitRoot,
    resolvePlanPath,
    getReportsPath,
    normalizePath,
    extractTaskListId,
    isHookEnabled
  } = require('./lib/tkm-config-utils.cjs');
  const { resolveSkillsVenv } = require('./lib/context-builder.cjs');
  const { createHookTimer, logHookCrash } = require('./lib/hook-logger.cjs');

  // Skip without side-effects if disabled in tkm.config.json
  if (!isHookEnabled('subagent-init')) {
    process.exit(0);
  }

/**
 * Return config-defined contextPrefix for a given agent type, or null.
 */
function getAgentContext(agentType, config) {
  const agentConfig = config.subagent?.agents?.[agentType];
  if (!agentConfig?.contextPrefix) return null;
  return agentConfig.contextPrefix;
}

// Agents that update Blueprint status or write plan-scoped reports
const PLAN_AWARE_AGENTS = new Set([
  'planner', 'project-manager', 'code-simplifier',
  'brainstormer', 'reviewer', 'implementer'
]);

// Agents that reason about architecture benefit from a docs/ index.
// Mechanical agents (tester, git-manager, debugger) don't need it.
const DOCS_AWARE_AGENTS = new Set([
  'planner', 'reviewer', 'doc-writer', 'implementer'
]);

/**
 * Emit the `ck plan` CLI reference for Blueprint-aware agents (~50 tokens).
 * Deterministic updates via CLI beat hand-editing plan.md Status columns.
 */
function buildPlanCliSection(agentType) {
  if (!PLAN_AWARE_AGENTS.has(agentType)) return [];
  return [
    ``,
    `## Plan CLI (deterministic updates)`,
    `\`ck plan check <id>\` = completed | \`ck plan check <id> --start\` = in-progress | \`ck plan uncheck <id>\` = revert`,
    `Fallback: if \`ck\` unavailable, edit plan.md Status column directly.`
  ];
}

// Per-feature spec file names, current first. Current rebuild-spec layout uses
// `technical-spec.md` as the primary per-feature file; `spec.md` is the legacy name.
const FEATURE_SPEC_FILES = ['technical-spec.md', 'spec.md'];

// Machine-generated namespaces that hold high-value navigation landmarks
// (`docs/system/overview.md`, `docs/generated/feature-list.md`, …). Their .md files are
// listed individually rather than collapsed to a count line — agents navigate by these.
const ARCHITECTURAL_SUBDIRS = new Set(['system', 'generated']);

// True if `dir` is a feature directory — i.e. directly contains a per-feature spec file.
function isFeatureDir(dir) {
  return FEATURE_SPEC_FILES.some(f => fs.existsSync(path.join(dir, f)));
}

// Detect a rebuild-spec feature container: a directory whose immediate subdirs are
// feature dirs (each holding a per-feature spec file). Handles both the current layout
// (`docs/features/F###_*/technical-spec.md`) and the legacy nesting
// (`docs/specs/features/F###_*/spec.md`) — the caller probes both depths.
// Returns a one-line summary like "docs/features/ — 40 feature specs (F###_*/)",
// or null if the directory doesn't match the pattern.
function summarizeSpecDir(dirPath, relPrefix) {
  try {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    let specCount = 0;
    for (const e of entries) {
      if (!e.isDirectory()) continue;
      if (isFeatureDir(path.join(dirPath, e.name))) {
        specCount++;
      }
    }
    if (specCount > 0) {
      return `${relPrefix}/ — ${specCount} feature specs (F###_*/). Start with feature-list.md`;
    }
    return null;
  } catch (_err) {
    return null;
  }
}

/**
 * Render the docs index block. Hard caps: ≤15 file bullets, ≤5 subdir summaries.
 */
function formatDocsIndexBlock({ topLevelMd, depth2Md, subdirSummaries }) {
  const FILE_CAP = 15;
  const SUBDIR_CAP = 5;
  const lines = [
    ``,
    `## Project Docs Index (./docs/) — agent decides what to read`,
    ``
  ];
  const allFiles = [...topLevelMd, ...depth2Md];
  if (allFiles.length > 0) {
    lines.push(`Files:`);
    const shown = allFiles.slice(0, FILE_CAP);
    shown.forEach(p => lines.push(`- ${p}`));
    const overflow = allFiles.length - shown.length;
    if (overflow > 0) lines.push(`- (${overflow} more)`);
  }
  if (subdirSummaries.length > 0) {
    if (allFiles.length > 0) lines.push(``);
    lines.push(`Subdirs:`);
    const shownSubs = subdirSummaries.slice(0, SUBDIR_CAP);
    shownSubs.forEach(s => lines.push(`- ${s}`));
    const overflow = subdirSummaries.length - shownSubs.length;
    if (overflow > 0) lines.push(`- (${overflow} more)`);
  }
  lines.push(``, `Read what's relevant to the task. Don't read everything.`);
  return lines;
}

// Build a paths-only `docs/` catalog for docs-aware agents.
// Rules:
//   - Always list depth-1 .md files.
//   - For each depth-1 subdir D, classify by descendants:
//     * If D is itself a feature container (current layout: D/F###_*/technical-spec.md)
//       → emit the feature-spec summary line for D.
//     * Else if a subdir of D is a feature container (legacy: docs/specs/features/F###_*/spec.md)
//       → list D's .md files individually AND emit the feature-spec summary line.
//     * Else if D is an architectural namespace (system/, generated/) → list its .md files
//       individually so landmarks (overview.md, feature-list.md) surface by path.
//     * Else if D contains .md files only → emit one summary line
//       "docs/D/ — N .md files". Keeps non-architectural dirs (journals, archives)
//       from flooding the index.
//     * Else skip.
// Fail-safe: any error → empty array. Token budget: ≤200 worst case.
function buildProjectDocsIndex(cwd, agentType) {
  if (!DOCS_AWARE_AGENTS.has(agentType)) return [];
  try {
    const docsDir = path.join(cwd, 'docs');
    if (!fs.existsSync(docsDir)) return [];
    const stat = fs.statSync(docsDir);
    if (!stat.isDirectory()) return [];

    const topLevelMd = [];
    const depth2Md = [];
    const subdirSummaries = [];

    const lvl1 = fs.readdirSync(docsDir, { withFileTypes: true });
    for (const ent of lvl1) {
      if (ent.isFile() && ent.name.endsWith('.md')) {
        topLevelMd.push(`docs/${ent.name}`);
        continue;
      }
      if (!ent.isDirectory()) continue;

      const lvl1Path = path.join(docsDir, ent.name);
      const relPrefix = `docs/${ent.name}`;

      // Current layout: the depth-1 dir is itself a feature container
      // (`docs/features/F###_*/technical-spec.md`). Probe it directly.
      const selfSummary = summarizeSpecDir(lvl1Path, relPrefix);
      if (selfSummary) {
        subdirSummaries.push(selfSummary);
        continue;
      }

      let lvl2;
      try {
        lvl2 = fs.readdirSync(lvl1Path, { withFileTypes: true });
      } catch (_err) {
        continue;
      }

      const lvl2Files = [];
      const lvl2SpecSummaries = [];
      for (const sub of lvl2) {
        if (sub.isFile() && sub.name.endsWith('.md')) {
          lvl2Files.push(`${relPrefix}/${sub.name}`);
          continue;
        }
        if (sub.isDirectory()) {
          const summary = summarizeSpecDir(path.join(lvl1Path, sub.name), `${relPrefix}/${sub.name}`);
          if (summary) lvl2SpecSummaries.push(summary);
        }
      }

      if (lvl2SpecSummaries.length > 0) {
        // Feature-spec system — list md files individually alongside spec summaries
        depth2Md.push(...lvl2Files);
        subdirSummaries.push(...lvl2SpecSummaries);
      } else if (ARCHITECTURAL_SUBDIRS.has(ent.name) && lvl2Files.length > 0) {
        // Architectural namespace (system/, generated/): surface files individually
        depth2Md.push(...lvl2Files);
      } else if (lvl2Files.length > 0) {
        // Plain collection (journals, archives, etc.) — collapse to count summary
        subdirSummaries.push(`${relPrefix}/ — ${lvl2Files.length} .md files`);
      }
    }

    topLevelMd.sort();
    depth2Md.sort();
    subdirSummaries.sort();

    if (topLevelMd.length === 0 && depth2Md.length === 0 && subdirSummaries.length === 0) {
      return [];
    }
    return formatDocsIndexBlock({ topLevelMd, depth2Md, subdirSummaries });
  } catch (_err) {
    return [];
  }
}

/**
 * Emit trust-verification block when a passphrase is configured.
 */
function buildTrustVerification(config) {
  if (!config.trust?.enabled || !config.trust?.passphrase) return [];
  return [
    ``,
    `## Trust Verification`,
    `Passphrase: "${config.trust.passphrase}"`
  ];
}

/**
 * Entry point — builds and emits the additionalContext JSON block for Claude Code.
 */
async function main() {
  const timer = createHookTimer('subagent-init', { event: 'SubagentStart' });
  let agentType = 'unknown';
  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) {
      timer.end({ status: 'skip', exit: 0, note: 'empty-input' });
      process.exit(0);
    }

    const payload = JSON.parse(stdin);
    agentType = payload.agent_type || 'unknown';
    const agentId = payload.agent_id || 'unknown';

    // Config needed for trust passphrase, naming pattern, and per-agent contextPrefix
    const config = loadConfig({ includeProject: false, includeAssertions: false });

    // Honour payload.cwd for monorepo support — each subagent resolves paths from its own CWD,
    // not process.cwd(). Trim guards against empty-string edge case (Issue #327).
    const effectiveCwd = payload.cwd?.trim() || process.cwd();

    // Recompute naming pattern directly — env vars may not propagate to all subagent runners.
    const gitBranch = getGitBranch(effectiveCwd);
    const gitRoot = getGitRoot(effectiveCwd);
    // Base is CWD, not git root — files are created relative to the subagent's directory (Issue #327).
    const baseDir = effectiveCwd;

    // Path-resolution trace — enable with TKM_DEBUG=1 to diagnose monorepo issues
    if (process.env.TKM_DEBUG) {
      console.error(`[subagent-init] effectiveCwd=${effectiveCwd}, gitRoot=${gitRoot}, baseDir=${baseDir}`);
    }
    const namePattern = resolveNamingPattern(config.plan, gitBranch);

    // Resolve active plan via session_id (Issue #321); absolute paths rooted at CWD (Issue #327).
    const sessionId = payload.session_id || process.env.TKM_SESSION_ID || null;
    const resolved = resolvePlanPath(sessionId, config);
    const reportsPath = getReportsPath(resolved.path, resolved.resolvedBy, config.plan, config.paths, baseDir);
    const activePlan = resolved.resolvedBy === 'session' ? resolved.path : '';
    const suggestedPlan = resolved.resolvedBy === 'branch' ? resolved.path : '';

    // Shared helper: derive task list ID from plan directory name (DRY with session-init)
    const taskListId = extractTaskListId(resolved);
    const plansPath = path.join(baseDir, normalizePath(config.paths?.plans) || 'plans');
    const docsPath = path.join(baseDir, normalizePath(config.paths?.docs) || 'docs');
    const thinkingLanguage = config.locale?.thinkingLanguage || '';
    const responseLanguage = config.locale?.responseLanguage || '';
    // When responseLanguage is set without thinkingLanguage, default thinking to 'en' for precision
    const effectiveThinking = thinkingLanguage || (responseLanguage ? 'en' : '');

    // Assemble the compact context block (~200 tokens)
    const lines = [];

    // Agent identity header
    lines.push(`## Subagent: ${agentType}`);
    lines.push(`ID: ${agentId} | CWD: ${effectiveCwd}`);
    lines.push(``);

    // Blueprint context
    lines.push(`## Context`);
    if (activePlan) {
      lines.push(`- Plan: ${activePlan}`);
      if (taskListId) {
        lines.push(`- Task List: ${taskListId} (shared with session)`);
      }
    } else if (suggestedPlan) {
      lines.push(`- Plan: none | Suggested: ${suggestedPlan}`);
    } else {
      lines.push(`- Plan: none`);
    }
    lines.push(`- Reports: ${reportsPath}`);
    // docs.maxLoc has to travel with the paths: doc-writer splits a page before it
    // crosses this ceiling, and a spawned subagent cannot see the main session's
    // `## Paths` line. Resolved exactly as context-builder does, so both surfaces
    // report the same number.
    const docsMaxLoc = Math.max(1, parseInt(config.docs?.maxLoc, 10) || 800);
    lines.push(`- Paths: ${plansPath}/ | ${docsPath}/ | docs.maxLoc: ${docsMaxLoc}`);
    lines.push(``);

    // Language directives — only emitted when locale config is set
    const hasThinking = effectiveThinking && effectiveThinking !== responseLanguage;
    if (hasThinking || responseLanguage) {
      lines.push(`## Language`);
      if (hasThinking) {
        lines.push(`- Thinking: Use ${effectiveThinking} for reasoning (logic, precision).`);
      }
      if (responseLanguage) {
        lines.push(`- Response: Respond in ${responseLanguage} (natural, fluent).`);
      }
      lines.push(``);
    }

    // Venv path for skill Python scripts — agents must use this, never global pip
    const skillsVenv = resolveSkillsVenv();

    // Iron Laws summary — minimal, always present
    lines.push(`## Rules`);
    lines.push(`- Reports → ${reportsPath}`);
    lines.push(`- YAGNI / KISS / DRY`);
    lines.push(`- Concise, list unresolved Qs at end`);
    // Inject venv path when skills/.venv exists
    if (skillsVenv) {
      lines.push(`- Python scripts in .claude/skills/: Use \`${skillsVenv}\``);
      lines.push(`- Never use global pip install`);
    }

    // Pre-computed naming templates — avoids reliance on env var propagation
    lines.push(``);
    lines.push(`## Naming`);
    lines.push(`- Report: ${path.join(reportsPath, `${agentType}-${namePattern}.md`)}`);
    lines.push(`- Plan dir: ${path.join(plansPath, namePattern)}/`);

    // `ck plan` CLI section for Blueprint-aware agents (Issue #540)
    lines.push(...buildPlanCliSection(agentType));

    // Docs index for architecture-aware agents; skipped for mechanical roles
    lines.push(...buildProjectDocsIndex(effectiveCwd, agentType));

    // Trust passphrase block — present only when trust.enabled in config
    lines.push(...buildTrustVerification(config));

    // Per-agent contextPrefix from config, if defined
    const agentContext = getAgentContext(agentType, config);
    if (agentContext) {
      lines.push(``);
      lines.push(`## Agent Instructions`);
      lines.push(agentContext);
    }

    // SubagentStart contract: output must use hookSpecificOutput.additionalContext
    const output = {
      hookSpecificOutput: {
        hookEventName: "SubagentStart",
        additionalContext: lines.join('\n')
      }
    };

    console.log(JSON.stringify(output));
    timer.end({ status: 'ok', exit: 0, target: agentType, note: 'context-injected' });
    process.exit(0);
  } catch (error) {
    console.error(`SubagentStart hook error: ${error.message}`);
    logHookCrash('subagent-init', error, { event: 'SubagentStart', target: agentType });
    process.exit(0); // Fail-open
  }
  }

  main();
} catch (e) {
  try {
    const { logHookCrash } = require('./lib/hook-logger.cjs');
    logHookCrash('subagent-init', e, { event: 'SubagentStart' });
  } catch (_) {}
  process.exit(0); // fail-open
}
