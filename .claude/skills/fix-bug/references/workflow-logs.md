# Log Analysis Fix Workflow

For chasing down issues out of application logs. Phases are tracked through native Claude Tasks.

## Prerequisites
- A log file at `./logs.txt` or somewhere like it

## Setup (if logs missing)

Wire permanent log piping into the project config:
- **Bash/Unix**: `command 2>&1 | tee logs.txt`
- **PowerShell**: `command *>&1 | Tee-Object logs.txt`

## Task Setup (Before Starting)

```
T1 = TaskCreate(subject="Read & analyze logs",  activeForm="Analyzing logs")
T2 = TaskCreate(subject="Scout codebase",        activeForm="Scouting codebase",    addBlockedBy=[T1])
T3 = TaskCreate(subject="Plan fix",              activeForm="Planning fix",          addBlockedBy=[T1, T2])
T4 = TaskCreate(subject="Implement fix",         activeForm="Implementing fix",      addBlockedBy=[T3])
T5 = TaskCreate(subject="Test fix",              activeForm="Testing fix",           addBlockedBy=[T4])
T6 = TaskCreate(subject="Code review",           activeForm="Reviewing code",        addBlockedBy=[T5])
```

## Workflow

### Step 1: Read & Analyze Logs
`TaskUpdate(T1, status="in_progress")`

- Read the logs with `Grep` (start at `head_limit: 30`, widen if you need more)
- Bring in the `debugger` agent for root cause analysis
- Start at the last N lines — the freshest errors
- Watch for stack traces, error codes, timestamps, patterns that repeat

`TaskUpdate(T1, status="completed")`

### Step 2: Scout Codebase
`TaskUpdate(T2, status="in_progress")`
Use the `tkm:scan-codebase` agent or parallel `Explore` subagents to locate where the issue lives.

See `references/parallel-exploration.md` for patterns.

`TaskUpdate(T2, status="completed")`

### Step 3: Plan Fix
`TaskUpdate(T3, status="in_progress")` — auto-unblocks once T1 + T2 close.
Use the `planner` agent.

`TaskUpdate(T3, status="completed")`

### Step 4: Implement
`TaskUpdate(T4, status="in_progress")`
Build the fix.

`TaskUpdate(T4, status="completed")`

### Step 5: Test
`TaskUpdate(T5, status="in_progress")`
Use the `tester` agent. If anything's still off → leave T5 `in_progress` and drop back to Step 2.

`TaskUpdate(T5, status="completed")`

### Step 6: Review
`TaskUpdate(T6, status="in_progress")`
Use the `reviewer` agent.

`TaskUpdate(T6, status="completed")`

## Tips
- Start at the last N lines — the freshest errors
- Watch for stack traces, error codes, timestamps
- Check for patterns and errors that repeat
