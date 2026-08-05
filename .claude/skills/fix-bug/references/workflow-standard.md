# Standard Workflow

The complete pipeline for moderate-complexity issues. Phases are tracked through native Claude Tasks.

## Task Setup (Before Starting)

Stand up every phase task upfront, wired with its dependencies. See `references/task-orchestration.md`.

```
T1 = TaskCreate(subject="Scout codebase",        activeForm="Scouting codebase")
T2 = TaskCreate(subject="Diagnose root cause",    activeForm="Diagnosing root cause")
T3 = TaskCreate(subject="Implement fix",          activeForm="Implementing fix",    addBlockedBy=[T1, T2])
T4 = TaskCreate(subject="Verify + prevent",       activeForm="Verifying fix",       addBlockedBy=[T3])
T5 = TaskCreate(subject="Code review",            activeForm="Reviewing code",      addBlockedBy=[T4])
T6 = TaskCreate(subject="Finalize",               activeForm="Finalizing",          addBlockedBy=[T5])
```

## Steps

### Step 1: Scout Codebase
`TaskUpdate(T1, status="in_progress")`

**Mandatory skill chain:**
1. Activate `tkm:scan-codebase` skill OR fan out 2-3 parallel `Explore` subagents.
2. Chart: affected files, module boundaries, dependencies, related tests, recent git changes.

**Pattern:** In a SINGLE message, launch 2-3 Explore agents:
```
Task("Explore", "Find [area1] files related to issue", "Scout area1")
Task("Explore", "Find [area2] patterns/usage", "Scout area2")
Task("Explore", "Find [area3] tests/dependencies", "Scout area3")
```

See `references/parallel-exploration.md` for patterns.

`TaskUpdate(T1, status="completed")`
**Output:** `✓ Step 1: Scouted [N] areas - [M] files, [K] tests found`

### Step 2: Diagnose Root Cause
`TaskUpdate(T2, status="in_progress")`

**Mandatory skill chain:**
1. **Capture pre-fix state:** Write down the exact error messages, failing test output, stack traces.
2. Activate `tkm:debug-code` skill. Pull in the `debugger` subagent if the trail goes cold.
3. Activate `tkm:think-sequential` — let structured reasoning shape the hypotheses.
4. Spawn parallel `Explore` subagents to weigh each hypothesis against the evidence in the code.
5. If 2+ hypotheses fall → auto-activate `tkm:solve-problem`.
6. Trace backward to the root cause — not the spot where the symptom shows.

See `references/diagnosis-protocol.md` for full methodology.

`TaskUpdate(T2, status="completed")`
**Output:** `✓ Step 2: Diagnosed - Root cause: [summary], Evidence: [brief], Scope: [N files]`

### Step 3: Implement Fix
`TaskUpdate(T3, status="in_progress")` — auto-unblocked once T1 + T2 close.

Fix the ROOT CAUSE the diagnosis named. Not the symptom.

- Reach for `tkm:solve-problem` when you stall
- Lean on `tkm:think-sequential` for tangled logic
- Smallest change that works. Stay inside the existing patterns.

`TaskUpdate(T3, status="completed")`
**Output:** `✓ Step 3: Implemented - [N] files changed`

### Step 4: Verify + Prevent
`TaskUpdate(T4, status="in_progress")`

**Mandatory skill chain:**
1. **Iron-law verify:** Re-run the EXACT commands from the pre-fix capture. Diff before against after.
2. **Regression test:** Add or extend test(s) over the fixed issue. The test MUST fail without the fix and pass with it.
3. **Defense-in-depth:** Layer in prevention where it fits (see `references/prevention-gate.md`).
4. **Parallel verification:** Launch `Bash` agents:
```
Task("Bash", "Run typecheck", "Verify types")
Task("Bash", "Run lint", "Verify lint")
Task("Bash", "Run build", "Verify build")
Task("Bash", "Run tests", "Verify tests")
```

**If verification fails:** Drop back to Step 2 and re-diagnose. Three attempts is the ceiling.

`TaskUpdate(T4, status="completed")`
**Output:** `✓ Step 4: Verified + Prevented - [before/after], [N] tests added, [M] guards`

### Step 5: Code Review
`TaskUpdate(T5, status="in_progress")`
Hand off to the `reviewer` subagent.

See `references/review-cycle.md` for mode-specific handling.

`TaskUpdate(T5, status="completed")`
**Output:** `✓ Step 5: Review [score]/10 - [status]`

### Step 6: Finalize
`TaskUpdate(T6, status="in_progress")`
- Summarize: root cause, changes, prevention measures, confidence score
- Activate `tkm:manage-project` for task sync-back and plan status updates
- Refresh docs through `doc-writer` if the change earns it
- Ask to commit via the `git-manager` subagent
- Run `/tkm:write-journal`

`TaskUpdate(T6, status="completed")`
**Output:** `✓ Step 6: Complete - [action]`

## Skills/Subagents Activated

| Step | Skills/Subagents |
|------|------------------|
| 1 | `tkm:scan-codebase` OR parallel `Explore` subagents |
| 2 | `tkm:debug-code`, `tkm:think-sequential`, `debugger` subagent, parallel `Explore`, (`tkm:solve-problem` auto) |
| 3 | `tkm:solve-problem` (if stuck), `tkm:think-sequential` (complex logic) |
| 4 | `tester` subagent, parallel `Bash` verification |
| 5 | `reviewer` subagent |
| 6 | `tkm:manage-project`, `git-manager`, `doc-writer` subagents |

**Rules:** No skipped steps. Confirm a phase before moving past it. One phase at a time.
**Frontend:** Reach for `chrome`, `tkm:automate-browser`, or whatever skill/tool fits to verify.
**Visual Assets:** Use the Read tool to inspect and confirm visual assets.
