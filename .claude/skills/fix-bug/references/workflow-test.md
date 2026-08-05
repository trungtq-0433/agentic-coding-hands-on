# Test Failure Fix Workflow

For mending failing tests and broken test suites. Phases are tracked through native Claude Tasks.

## Task Setup (Before Starting)

```
T1 = TaskCreate(subject="Compile & collect failures", activeForm="Compiling and collecting failures")
T2 = TaskCreate(subject="Debug root causes",          activeForm="Debugging test failures",       addBlockedBy=[T1])
T3 = TaskCreate(subject="Plan fixes",                 activeForm="Planning fixes",                addBlockedBy=[T2])
T4 = TaskCreate(subject="Implement fixes",             activeForm="Implementing fixes",            addBlockedBy=[T3])
T5 = TaskCreate(subject="Re-test",                     activeForm="Re-running tests",              addBlockedBy=[T4])
T6 = TaskCreate(subject="Code review",                 activeForm="Reviewing code",                addBlockedBy=[T5])
```

## Workflow

### Step 1: Compile & Collect Failures
`TaskUpdate(T1, status="in_progress")`
Hand off to the `tester` agent. Clear every syntax error before the suite runs.

- Run the full test suite and gather all failures
- Cluster failures by module/area

`TaskUpdate(T1, status="completed")`

### Step 2: Debug
`TaskUpdate(T2, status="in_progress")`
Bring in the `debugger` agent for root cause analysis.

- Work through each failure cluster
- Find the shared root causes running under several failures

`TaskUpdate(T2, status="completed")`

### Step 3: Plan
`TaskUpdate(T3, status="in_progress")`
Use the `planner` agent to set the fix strategy.

- Order the fixes — shared root causes lead
- Spot the dependencies between fixes

`TaskUpdate(T3, status="completed")`

### Step 4: Implement
`TaskUpdate(T4, status="in_progress")`
Work the fixes one step at a time, following the plan.

`TaskUpdate(T4, status="completed")`

### Step 5: Re-test
`TaskUpdate(T5, status="in_progress")`
Hand off to the `tester` agent. If tests still fail → leave T5 `in_progress` and drop back to Step 2.

`TaskUpdate(T5, status="completed")`

### Step 6: Review
`TaskUpdate(T6, status="in_progress")`
Bring in the `reviewer` agent.

`TaskUpdate(T6, status="completed")`

## Common Commands
```bash
npm test
bun test
pytest
go test ./...
```

## Tips
- Run the single failing test first — tighter iteration loop
- Hold the test's assertions against what the code actually does
- Confirm the fixtures/mocks are set up right
- Leave the tests alone unless the test itself is wrong
