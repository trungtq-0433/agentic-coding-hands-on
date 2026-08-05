# Task Orchestration

Native Claude Task tools for tracking and steering fix workflows.

**Skill:** Activate `tkm:manage-project` for the heavier orchestration — hydration (plan checkboxes → Tasks), sync-back (Tasks → plan checkboxes), cross-session resume, and progress-tracking patterns.

**Tool Availability:** `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList` are **CLI-only** — off in the VSCode extension (`isTTY` check). On error, track progress with `TodoWrite` instead. The fix workflow runs to completion either way — Tasks bring visibility and coordination, not the core behavior.

## When to Use Tasks

| Complexity | Use Tasks? | Reason |
|-----------|-----------|--------|
| Simple/Quick | No | < 3 steps, the bookkeeping costs more than it returns |
| Moderate (Standard) | Yes | 6 steps, several subagents to keep in step |
| Complex (Deep) | Yes | 9 steps, dependency chains, parallel agents |
| Parallel | Yes | Several independent issue trees |

## Task Tools

- `TaskCreate(subject, description, activeForm, metadata)` - Create a task
- `TaskUpdate(taskId, status, addBlockedBy, addBlocks)` - Update status/deps
- `TaskGet(taskId)` - Get the full task detail
- `TaskList()` - List every task with its status

**Lifecycle:** `pending` → `in_progress` → `completed`

## Standard Workflow Tasks (6 phases)

Stand up every task first, then work down the list:

```
T1 = TaskCreate(subject="Scout codebase",       activeForm="Scouting codebase",     metadata={step: 1, phase: "investigate"})
T2 = TaskCreate(subject="Diagnose root cause",   activeForm="Diagnosing root cause", metadata={step: 2, phase: "investigate"})
T3 = TaskCreate(subject="Implement fix",         activeForm="Implementing fix",      metadata={step: 3, phase: "implement"},  addBlockedBy=[T1, T2])
T4 = TaskCreate(subject="Verify + prevent",      activeForm="Verifying fix",         metadata={step: 4, phase: "verify"},     addBlockedBy=[T3])
T5 = TaskCreate(subject="Code review",           activeForm="Reviewing code",        metadata={step: 5, phase: "verify"},     addBlockedBy=[T4])
T6 = TaskCreate(subject="Finalize",              activeForm="Finalizing",            metadata={step: 6, phase: "finalize"},   addBlockedBy=[T5])
```

Advance them as the work moves:
```
TaskUpdate(taskId=T1, status="in_progress")
// ... scout the codebase ...
TaskUpdate(taskId=T1, status="completed")
// T3 opens up on its own once T1 + T2 close
```

## Deep Workflow Tasks (9 phases)

Steps 1+2+3 run side by side (scout + diagnose + research).

```
T1 = TaskCreate(subject="Scout codebase",           metadata={step: 1, phase: "investigate"})
T2 = TaskCreate(subject="Diagnose root cause",       metadata={step: 2, phase: "investigate"})
T3 = TaskCreate(subject="Research solutions",         metadata={step: 3, phase: "investigate"})
T4 = TaskCreate(subject="Brainstorm approaches",      metadata={step: 4, phase: "design"},     addBlockedBy=[T1, T2, T3])
T5 = TaskCreate(subject="Create implementation plan", metadata={step: 5, phase: "design"},     addBlockedBy=[T4])
T6 = TaskCreate(subject="Implement fix",              metadata={step: 6, phase: "implement"},  addBlockedBy=[T5])
T7 = TaskCreate(subject="Verify + prevent",           metadata={step: 7, phase: "verify"},     addBlockedBy=[T6])
T8 = TaskCreate(subject="Code review",                metadata={step: 8, phase: "verify"},     addBlockedBy=[T7])
T9 = TaskCreate(subject="Finalize & docs",            metadata={step: 9, phase: "finalize"},   addBlockedBy=[T8])
```

**Note:** Steps 1, 2, and 3 run together (scout + diagnose + research all at once).

## Parallel Issue Coordination

For 2+ independent issues, give each its own task tree:

```
// Issue A tree
TaskCreate(subject="[Issue A] Scout",      metadata={issue: "A", step: 1})
TaskCreate(subject="[Issue A] Diagnose",   metadata={issue: "A", step: 2})
TaskCreate(subject="[Issue A] Fix",        metadata={issue: "A", step: 3}, addBlockedBy=[A-step1, A-step2])
TaskCreate(subject="[Issue A] Verify",     metadata={issue: "A", step: 4}, addBlockedBy=[A-step3])

// Issue B tree
TaskCreate(subject="[Issue B] Scout",      metadata={issue: "B", step: 1})
TaskCreate(subject="[Issue B] Diagnose",   metadata={issue: "B", step: 2})
TaskCreate(subject="[Issue B] Fix",        metadata={issue: "B", step: 3}, addBlockedBy=[B-step1, B-step2])
TaskCreate(subject="[Issue B] Verify",     metadata={issue: "B", step: 4}, addBlockedBy=[B-step3])

// Final shared task
TaskCreate(subject="Integration verify",   addBlockedBy=[A-step4, B-step4])
```

Spawn one `implementer` subagent per issue tree. Each agent:
1. Claims its tasks with `TaskUpdate(status="in_progress")`
2. Closes them with `TaskUpdate(status="completed")`
3. Blocked tasks open up on their own as the dependencies clear

## Subagent Task Assignment

Hand tasks to subagents through the `owner` field:

```
TaskUpdate(taskId=taskA, owner="agent-scout")
TaskUpdate(taskId=taskB, owner="agent-diagnose")
```

Find available work: `TaskList()` → filter on `status=pending`, `blockedBy=[]`, `owner=null`

## Rules

- Stand up the tasks BEFORE the work starts (plan it upfront)
- One task `in_progress` per agent, no more
- Mark a task done THE MOMENT it's finished — don't batch them
- Lean on `metadata` to filter: `{step, phase, issue, severity}`
- If a task fails → leave it `in_progress`, spin a subtask for the blocker
- Drop Tasks altogether on the Quick workflow (< 3 steps)
