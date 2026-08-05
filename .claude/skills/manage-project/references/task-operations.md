# Task Operations Reference

Claude Code ships four native tools for handling tasks that live only as long as the session.

**Tool Availability:** `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList` belong to the CLI alone — the VSCode extension gates them out behind an `isTTY` check. When they throw, drop down to `TodoWrite` to keep progress. Plan-file sync-back doesn't notice the difference.

## TaskCreate

Lay down a structured task with its metadata and dependencies.

```
TaskCreate(
  subject: "Implement JWT auth middleware",
  description: "Add JWT validation to API routes. Verify tokens, extract claims, attach to context.",
  activeForm: "Implementing JWT auth middleware",
  metadata: { feature: "auth", phase: 2, priority: "P1", effort: "2h",
              planDir: "plans/260205-auth/", phaseFile: "phase-02-api.md" }
)
```

**Parameters:**
- `subject` (required): An imperative title under 60 chars ("Implement X", "Add Y", "Fix Z")
- `description` (required): The full requirements plus what counts as done
- `activeForm` (optional): The present-continuous line the spinner shows ("Implementing X")
- `metadata` (optional): Whatever key-value pairs you want to track against

**Required metadata fields:** `phase`, `priority` (P1/P2/P3), `effort`, `planDir`, `phaseFile`
**Optional metadata:** `step`, `critical`, `riskLevel`, `dependencies`, `feature`, `owner`

## TaskUpdate

Move a task between states and tie its dependency chains.

```
TaskUpdate(
  taskId: "task-123",
  status: "in_progress",
  addBlockedBy: ["task-122"]
)
```

**Status lifecycle:** `pending` → `in_progress` → `completed`

**Dependency fields:**
- `addBlockedBy`: "I can't begin until these finish"
- `addBlocks`: "These can't begin until I finish"
- `owner`: Pin it to one agent

Finish a blocking task and everything waiting on it clears on its own.

## TaskGet & TaskList

- `TaskGet(taskId)` → The whole task, dependencies and all
- `TaskList()` → Every task with its status, owner, blockedBy

**A task is "available" when:** its status is `pending`, no owner holds it, and its blockedBy list is empty.

## Dependency Patterns

```
Phase 1 (no blockers)              ← start here
Phase 2 (addBlockedBy: [P1-id])    ← auto-unblocked when P1 completes
Phase 3 (addBlockedBy: [P2-id])
Step 3.4 (addBlockedBy: [P2-id])   ← critical steps share phase dependency
```

## When to Use Tasks

| Scenario | Tasks? | Why |
|----------|--------|-----|
| Multi-phase feature (3+) | Yes | Track progress, enable parallel |
| Complex dependencies | Yes | Automatic unblocking |
| Parallel agent work | Yes | Shared progress tracking |
| Single-phase quick fix | No | Overhead exceeds benefit |
| <3 related steps | No | Just do them directly |

**3-Task Rule:** under three tasks, don't bother creating any — the bookkeeping costs more than it returns.

## Parallel Agent Coordination

1. Cut the tasks so each agent owns its own slice
2. Keep every agent inside its assigned directories, nowhere else
3. Agent A finishes a task → `TaskUpdate(status: "completed")`
4. Anything that was waiting on that work clears itself
5. Agent B (or A again) picks up whatever just opened

**Key:** Set the `owner` field so two agents never grab the same task.
