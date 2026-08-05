# Skill Activation Matrix

Which skill or tool to reach for, and at what point in a fixing workflow.

## Always Activate (ALL Workflows)

| Skill/Tool | Step | Reason |
|------------|------|--------|
| `tkm:scan-codebase` OR parallel `Explore` | Step 1 | Learn the codebase context before diagnosing |
| `tkm:debug-code` | Step 2 | Methodical root cause investigation |
| `tkm:think-sequential` | Step 2 | Hypotheses by reasoning — NO guessing |

## Task Orchestration (Moderate+ Only)

| Tool | Activate When |
|------|---------------|
| `TaskCreate` | Right after the complexity call — lay out every phase task upfront |
| `TaskUpdate` | As each phase opens and closes |
| `TaskList` | Find unblocked work, keep parallel agents in sync |
| `TaskGet` | Pull the full task detail before starting on it |

Skip Tasks on the Quick workflow (< 3 steps). See `references/task-orchestration.md`.

## Auto-Triggered Activation

| Skill | Auto-Trigger Condition |
|-------|------------------------|
| `tkm:solve-problem` | 2+ hypotheses REFUTED in Step 2 diagnosis |
| `tkm:think-sequential` | Always in Step 2 (mandatory for hypothesis formation) |

## Conditional Activation

| Skill | Activate When |
|-------|---------------|
| `tkm:brainstorm` | Several fix approaches in play, an architecture call (Deep only) |
| `tkm:optimize-context` | Fixing AI/LLM/agent code, context-window trouble |
| `tkm:manage-project` | Moderate+ workflows — task hydration, sync-back, progress tracking |

## Subagent Usage

| Subagent | Activate When |
|----------|---------------|
| `debugger` | Root cause murky, needs deep digging (Step 2) |
| `Explore` (parallel) | Sweep several areas at once (Step 1), weigh hypotheses (Step 2) |
| `Bash` (parallel) | Confirm the work: typecheck, lint, build, test (Step 5) |
| `researcher` | External docs or current best practices wanted (Deep only) |
| `planner` | Big fix needs breaking into phases (Deep only) |
| `tester` | After the build, prove the fix holds (Step 5) |
| `tkm:review-code` | After the fix, vet quality and security (Step 5) |
| `git-manager` | Once approved, land the commit (Step 6) |
| `doc-writer` | API/behavior shifts need doc updates (Step 6) |
| `project-manager` | Big fix moves roadmap/plan status (Step 6) |
| `implementer` | Independent issues run in parallel (one agent each) |

## Parallel Patterns

See `references/parallel-exploration.md` for detailed patterns.

| When | Parallel Strategy |
|------|-------------------|
| Scouting (Step 1) | 2-3 `Explore` agents across different areas |
| Testing hypotheses (Step 2) | 2-3 `Explore` agents, one per hypothesis |
| Multi-module fix | `Explore` each module in parallel |
| After implementation (Step 5) | `Bash` agents: typecheck + lint + build + test |
| 2+ independent issues | Task trees + `implementer` agents per issue |

## Workflow → Skills Map

| Workflow | Skills Activated |
|----------|------------------|
| Quick | `tkm:scan-codebase` (minimal), `tkm:debug-code`, `tkm:think-sequential`, `tkm:review-code`, parallel `Bash` verification |
| Standard | Above + Tasks, `tkm:solve-problem` (auto), `tkm:manage-project`, `tester`, parallel `Explore` |
| Deep | All above + `tkm:brainstorm`, `tkm:optimize-context`, `researcher`, `planner` |
| Parallel | Per-issue Task trees + `tkm:manage-project` + `implementer` agents + coordination via `TaskList` |

## Step → Skills Chain (Mandatory Order)

| Step | Mandatory Chain |
|------|----------------|
| Step 0: Mode | `AskUserQuestion` (unless auto/quick detected) |
| Step 1: Scout | `tkm:scan-codebase` OR 2-3 parallel `Explore` → map files, deps, tests |
| Step 2: Diagnose | Capture pre-fix state → `tkm:debug-code` → `tkm:think-sequential` → parallel `Explore` hypotheses → (`tkm:solve-problem` if 2+ fail) |
| Step 3: Assess | Classify complexity → create Tasks (moderate+) |
| Step 4: Fix | Implement per workflow → follow root cause |
| Step 5: Verify+Prevent | Iron-law verify → regression test → defense-in-depth → parallel `Bash` verify |
| Step 6: Finalize | Report → `doc-writer` → `TaskUpdate` → `git-manager` → `/tkm:write-journal` |

## Detection Triggers

| Keyword/Pattern | Skill to Consider |
|-----------------|-------------------|
| "AI", "LLM", "agent", "context" | `tkm:optimize-context` |
| "stuck", "tried everything" | `tkm:solve-problem` |
| "complex", "multi-step" | `tkm:think-sequential` |
| "which approach", "options" | `tkm:brainstorm` |
| "latest docs", "best practice" | `researcher` subagent |
| Screenshot attached | Read tool (built-in) |
