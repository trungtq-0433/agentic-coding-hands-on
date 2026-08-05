# Task Management Integration

## Session-Scoped Reality

Claude Tasks don't outlive the session — when it ends, they're gone. What sits in `~/.claude/tasks/` is lock files, not the task data itself. The plan files (plan.md, the phase-XX.md checkboxes) are the layer that **persists**.

**Tool Availability:** `TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskList` run **in the CLI only** — the VSCode extension shuts them off behind an `isTTY` check. When they error out, fall back to `TodoWrite` for progress. The plan files stay authoritative; hydration is a convenience layered on top, not a requirement.

The **hydration pattern** is what carries work across sessions:

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

- **Hydrate:** Walk the plan files and TaskCreate one task for each unchecked `[ ]`
- **Work:** TaskUpdate keeps in_progress/completed current as you go
- **Sync-back:** Flip `[ ]` → `[x]` in the phase files and update the status in plan.md's frontmatter

## When to Create Tasks

**Default:** On — tasks hydrate themselves the moment the plan files land
**Skip with:** the `--no-tasks` flag on the planning request
**3-Task Rule:** under 3 phases, skip tasks — the overhead outweighs the payoff

| Scenario | Tasks? | Why |
|----------|--------|-----|
| Multi-phase feature (3+ phases) | Yes | Watch progress, open the door to parallel work |
| Complex dependencies between phases | Yes | Phases unblock themselves |
| Plan will be executed by takumi | Yes | Clean handoff |
| Single-phase quick fix | No | Just go do it |
| Trivial 1-2 step plan | No | The bookkeeping isn't worth it |

## Task Creation Patterns

### Phase-Level TaskCreate

```
TaskCreate(
  subject: "Setup environment and dependencies",
  activeForm: "Setting up environment",
  description: "Install packages, configure env, setup database. See phase-01-setup.md",
  metadata: { phase: 1, priority: "P1", effort: "2h",
              planDir: "plans/260205-auth/", phaseFile: "phase-01-setup.md" }
)
```

### Critical Step TaskCreate

For the steps inside a phase that carry real risk or complexity:

```
TaskCreate(
  subject: "Implement OAuth2 token refresh",
  activeForm: "Implementing token refresh",
  description: "Handle token expiry, refresh flow, error recovery",
  metadata: { phase: 3, step: "3.4", priority: "P1", effort: "1.5h",
              planDir: "plans/260205-auth/", phaseFile: "phase-03-api.md",
              critical: true, riskLevel: "high" },
  addBlockedBy: ["{phase-2-task-id}"]
)
```

## Metadata & Naming Conventions

**Required metadata:** `phase`, `priority` (P1/P2/P3), `effort`, `planDir`, `phaseFile`
**Optional metadata:** `step`, `critical`, `riskLevel`, `dependencies`

**subject** (imperative): an action verb plus what it produces, under 60 chars
- "Setup database migrations", "Implement OAuth2 flow", "Create user profile endpoints"

**activeForm** (present continuous): the same subject in its -ing form
- "Setting up database", "Implementing OAuth2", "Creating user profile endpoints"

**description**: a sentence or two naming concrete deliverables, pointing at the phase file

## Dependency Chains

```
Phase 1 (no blockers)              ← start here
Phase 2 (addBlockedBy: [P1-id])    ← auto-unblocked when P1 completes
Phase 3 (addBlockedBy: [P2-id])
Step 3.4 (addBlockedBy: [P2-id])   ← critical steps share phase dependency
```

Reach for `addBlockedBy` on a forward reference ("X has to land before this can start").
Reach for `addBlocks` when the parent comes first ("X is what's holding these children up").

## Takumi Handoff Protocol

### Same-Session (planning → takumi immediately)

1. Planning hydrates the tasks, so they're already sitting in the session
2. Takumi's Step 3 calls `TaskList`, sees them, and adopts them
3. Takumi skips creating anything and goes straight to building

### Cross-Session (new session, resume plan)

1. User opens a new session with `/tkm:takumi path/to/plan.md`
2. Takumi's Step 3 calls `TaskList` and gets nothing back — the old session took the tasks with it
3. Takumi reads the plan files and rebuilds tasks from the unchecked `[ ]` items
4. Anything already `[x]` is finished, so it's left alone

### Sync-Back (takumi Step 6)

1. `TaskUpdate` closes out every task in the session.
2. The `project-manager` subagent runs a full-plan sync-back:
   - Sweep all `phase-XX-*.md` files.
   - Match completed tasks back by their metadata (`phase`, `phaseFile`).
   - Tick over any checkbox left stale, `[ ]` → `[x]`, across every phase — not just the one in hand.
   - Pull `plan.md`'s status and progress from what the checkboxes now say.
3. If a completed task won't map to any phase file, surface the loose ends before calling the work done.
4. A git commit pins the state transition for the next session to pick up.

## Quality Checks

Once tasks are hydrated, confirm:
- The dependency chain has no cycles
- Every phase has a task standing for it
- The required metadata is all there (phase, priority, effort, planDir, phaseFile)
- The task count lines up with the unchecked `[ ]` items in the plan files
- Output: `✓ Hydrated [N] phase tasks + [M] critical step tasks with dependency chain`
