---
name: tkm:manage-project
description: "Keep the whole commission in view as it moves — read plan state, drive Tasks, write reports, and call for doc updates. Reach for it on oversight passes, status checks, task hydration, and picking work back up across sessions."
argument-hint: "[status | hydrate | sync | report]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: project-context-management
triggers: ["project status", "what's done", "update plan", "track progress", "task management"]
---

# Tracking the Commission

You cannot steer what you cannot see. Holding the state of a commission in view is less about paperwork than about keeping the plan and the actual work pointing the same direction — over many sessions, across several agents, as time stretches the gap between what was intended and what got built. State that goes unrecorded quietly slips out of your hands, and once it slips, it wanders.

**Hold to:** Spend tokens sparingly | Keep reports tight | Let the data do the talking

## When to Use

- Taking stock of where each plan stands
- Moving a plan's status forward once a feature lands
- Pulling Claude Tasks out of plan files, or pushing them back
- Producing a status report or running summary
- Calling for doc updates after a milestone clears
- Confirming a task actually meets its acceptance criteria
- Resuming multi-phase work in a fresh session

## Tool Availability

`TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList` live in the CLI only — the VSCode extension switches them off behind an `isTTY` check.

| Environment | Task Tools | Fallback |
|-------------|-----------|----------|
| CLI terminal | Available | — |
| VSCode extension | **Disabled** | `TodoWrite` |

**Fallback behavior:** When the Task tools throw, reach for `TodoWrite` to carry progress instead. Nothing downstream breaks — plan-file sync-back (the checkboxes, the YAML frontmatter) behaves exactly the same with or without them, and the PM workflow stays whole.

## Core Capabilities

### 1. Task Operations
Load: `references/task-operations.md`

Drive session-scoped work through `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList` (CLI only — see Tool Availability above).
- Stamp each task with metadata: phase, priority, effort, planDir, phaseFile
- Walk status forward: `pending` → `in_progress` → `completed`
- Wire dependencies with `addBlockedBy` / `addBlocks`
- Hand parallel agents non-overlapping ownership

### 2. Session Bridging (Hydration Pattern)
Load: `references/hydration-workflow.md`

Tasks die with the session; plan files outlive it. Hydration is the bridge between the two:
- **Hydrate:** Walk the plan's `[ ]` items → one `TaskCreate` per unchecked line
- **Work:** `TaskUpdate` keeps the live picture honest as you go
- **Sync-back:** Match every completed task across every phase file, flip `[ ]` → `[x]`, and move the YAML frontmatter status
- **Resume:** Whatever stays `[ ]` is what the next session hydrates from

### 3. Progress Tracking
Load: `references/progress-tracking.md`

- Sweep `./plans/*/plan.md` to find the live plans
- Pull status, priority, effort out of the YAML frontmatter
- Tally `[x]` against `[ ]` per phase file to get completion %
- Hold completed work up against what was planned
- Don't mark anything done until its acceptance criteria are actually met

### 4. Documentation Coordination
Load: `references/documentation-triggers.md`

Call for `./docs` updates whenever:
- A phase status moves, or a major feature lands
- An API contract shifts, or an architecture call is made
- A security patch ships, or something breaks backward compatibility

Hand the writing itself to the `doc-writer` subagent.

### 5. Status Reporting
Load: `references/reporting-patterns.md`

Write the report the moment calls for — session summary, plan completion, or a view across many plans.
- Name it: `{reports-path}/pm-{date}-{time}-{slug}.md`
- Trade grammar for brevity; lean on tables, not paragraphs
- Park any unresolved questions at the end

## Workflow

```
[Scan Plans] → [Hydrate Tasks] → [Track Progress] → [Update Status] → [Generate Report] → [Trigger Doc Updates]
```

1. `TaskList()` — look at what's already on the board first
2. Nothing there? Hydrate from the plan files' unchecked items
3. As you work: `TaskUpdate` each task as it moves
4. When it's done: run a full-plan sync-back across every phase file (backfilling the earlier ones), then move the YAML frontmatter
5. Write a status report into the reports directory
6. Hand off doc updates when the changes earn them

## Mandatory Sync-Back Guard

Updating plan status is never a matter of ticking off the phase you happen to be standing in.

1. Sweep all `phase-XX-*.md` files under the target plan directory.
2. Match every `TaskUpdate(status: "completed")` item back to its phase metadata (`phase` / `phaseFile`).
3. Catch up the stale checkboxes in earlier phases before you call a later phase done.
4. Recompute `plan.md` status/progress from the real checkbox counts.
5. If a completed task won't map to any phase file, surface the loose ends and stop short of declaring full completion.

## Plan YAML Frontmatter

Every `plan.md` carries this header — no exceptions:

```yaml
---
title: Feature name
status: in-progress  # pending | in-progress | completed
priority: P1
effort: medium
branch: feature-branch
tags: [auth, api]
created: 2026-02-05
---
```

Move `status` whenever the plan's state moves.

## Quality Standards

- Ground every claim in data — name the plan, cite the report
- Steer toward delivered value and conclusions someone can act on
- Put the things that need attention now at the top
- Keep a clear thread from each requirement to the code that satisfies it

## Related Skills

- `tkm:create-plan` — Draws up the implementation plan (the planning phase)
- `tkm:takumi` — Carries the plan out (the execution phase; hands off to project-manager at the finish)
- `plans-kanban` — A visual board for looking over plans
