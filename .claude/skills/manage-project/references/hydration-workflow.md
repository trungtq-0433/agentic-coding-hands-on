# Hydration Workflow

A task is **session-scoped** — close the session and it's gone. The plan files are the layer that **persists**. Hydration is how you carry state across that gap from one session to the next.

## Flow Diagram

```
┌──────────────────┐  Hydrate   ┌───────────────────┐
│ Plan Files       │ ─────────► │ Claude Tasks      │
│ (persistent)     │            │ (session-scoped)  │
│ [ ] Phase 1      │            │ ◼ pending         │
│ [ ] Phase 2      │            │ ◼ pending         │
└──────────────────┘            └───────────────────┘
                                        │ Work
                                        ▼
┌──────────────────┐  Sync-back ┌───────────────────┐
│ Plan Files       │ ◄───────── │ Task Updates      │
│ (updated)        │            │ (completed)       │
│ [x] Phase 1      │            │ ✓ completed       │
│ [ ] Phase 2      │            │ ◼ in_progress     │
└──────────────────┘            └───────────────────┘
```

## Tool Availability

The Task tools (`TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskList`) run in the CLI only — the VSCode extension shuts them off. When they're out of reach, carry progress with `TodoWrite` instead. The pattern doesn't depend on them: the plan files stay the source of truth, and sync-back flips the checkboxes either way.

## Session Start: Hydration

1. Read the plan files: `plan.md` plus the `phase-XX-*.md` set
2. Treat every unchecked `[ ]` line as work still owed
3. `TaskCreate` one per unchecked item, stamped with metadata (phase, priority, effort, planDir, phaseFile) — or `TodoWrite` when the Task tools are gone
4. Chain the phases with `addBlockedBy` (skip this on the TodoWrite fallback)
5. Anything already `[x]` is finished — pass over it

**Look before you build:** `TaskList()` first. If tasks are already there (same session), don't make them twice. If the call errors, fall through to TodoWrite.

## During Work

- `TaskUpdate(status: "in_progress")` the moment you pick a task up
- `TaskUpdate(status: "completed")` the moment it's done — not later
- Parallel agents stay in step through the one shared task list
- A blocked task clears itself once whatever it waited on completes

## Session End: Sync-Back

1. Gather the completed tasks (`TaskUpdate(status: "completed")`) and their metadata (`phase`, `phaseFile`, `planDir`).
2. Sweep all `phase-XX-*.md` files in the target plan directory.
3. Match and backfill: flip `[ ]` → `[x]` for every completed item across every phase file, the earlier ones included.
4. Move the `plan.md` frontmatter status field along (pending → in-progress → completed).
5. Recompute the progress percentages in the `plan.md` overview from the real checkbox counts.
6. Call out any completed task that won't match a phase file.
7. A git commit pins the transition down for the next session to find.

## Cross-Session Resume

When the user runs `/tkm:takumi path/to/plan.md` in a fresh session:
1. `TaskList()` → empty (the old session took its tasks with it)
2. Read the plan files → hydrate again from the unchecked `[ ]` items
3. Whatever's already `[x]` is done, so only the remaining work becomes tasks
4. The dependency chain rebuilds itself

## Compound Interest Effect

The specs sharpen with every hydration cycle:
- **Session 1:** Run the first tasks, lay down the patterns
- **Session 2:** See what's finished, extend the patterns already in place
- **Session 3:** Full sight of everything prior, so fewer questions need asking

The git history traces the climb. The checked boxes mark the route that held. Session by session, the specs accrue an **institutional memory**.

## YAML Frontmatter Sync

Plan files MUST have frontmatter with these fields:

```yaml
---
title: Feature name
description: Brief description
status: in-progress  # pending | in-progress | completed
priority: P1
effort: medium
branch: feature-branch
tags: [auth, api]
created: 2026-02-05
---
```

Carry the `status` field forward during sync-back as the plan's state shifts.
