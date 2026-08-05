# Deep Workflow

The full pipeline — research, brainstorming, and planning — for the hard ones. Phases ride on native Claude Tasks wired into dependency chains.

## Task Setup (Before Starting)

Lay out every phase task upfront. Steps 1+2+3 run side by side (scout + diagnose + research).

```
T1 = TaskCreate(subject="Scout codebase",              activeForm="Scouting codebase",          metadata={phase: "investigate"})
T2 = TaskCreate(subject="Diagnose root cause",          activeForm="Diagnosing root cause",      metadata={phase: "investigate"})
T3 = TaskCreate(subject="Research solutions",            activeForm="Researching solutions",      metadata={phase: "investigate"})
T4 = TaskCreate(subject="Brainstorm approaches",         activeForm="Brainstorming",              metadata={phase: "design"},       addBlockedBy=[T1, T2, T3])
T5 = TaskCreate(subject="Create implementation plan",    activeForm="Planning implementation",    metadata={phase: "design"},       addBlockedBy=[T4])
T6 = TaskCreate(subject="Implement fix",                 activeForm="Implementing fix",           metadata={phase: "implement"},    addBlockedBy=[T5])
T7 = TaskCreate(subject="Verify + prevent",              activeForm="Verifying fix",              metadata={phase: "verify"},       addBlockedBy=[T6])
T8 = TaskCreate(subject="Code review",                   activeForm="Reviewing code",             metadata={phase: "verify"},       addBlockedBy=[T7])
T9 = TaskCreate(subject="Finalize & docs",               activeForm="Finalizing",                 metadata={phase: "finalize"},     addBlockedBy=[T8])
```

## Steps

### Step 1: Scout Codebase (parallel with Steps 2+3)
`TaskUpdate(T1, status="in_progress")`

**Mandatory:** Activate `tkm:scan-codebase` skill or fan out 2-3 `Explore` subagents in parallel:
```
Task("Explore", "Find error origin and affected components", "Trace error")
Task("Explore", "Find module boundaries and dependencies", "Map deps")
Task("Explore", "Find related tests and similar patterns", "Find patterns")
```

Chart: every affected file, the module boundaries, the call chains, and the gaps in test coverage.

See `references/parallel-exploration.md` for patterns.

`TaskUpdate(T1, status="completed")`
**Output:** `✓ Step 1: Scouted - [N] files, system impact: [scope]`

### Step 2: Diagnose Root Cause (parallel with Steps 1+3)
`TaskUpdate(T2, status="in_progress")`

**Mandatory skill chain:**
1. **Capture pre-fix state:** Save EVERY error message, failing test, stack trace, log.
2. Activate `tkm:debug-code` skill (systematic-debugging + root-cause-tracing).
3. Activate `tkm:think-sequential` — let reasoning shape the hypotheses.
4. Spawn parallel `Explore` subagents to weigh each hypothesis.
5. If 2+ hypotheses fall → auto-activate `tkm:solve-problem`.
6. Trace back through the call chain to where the ROOT CAUSE starts.

See `references/diagnosis-protocol.md` for full methodology.

`TaskUpdate(T2, status="completed")`
**Output:** `✓ Step 2: Diagnosed - Root cause: [summary], Evidence: [chain]`

### Step 3: Research (parallel with Steps 1+2)
`TaskUpdate(T3, status="in_progress")`
Send the `researcher` subagent after outside knowledge.

- Look up current docs and best practices
- Hunt for similar issues and their solutions
- Pull security advisories where they matter

`TaskUpdate(T3, status="completed")`
**Output:** `✓ Step 3: Research complete - [key findings]`

### Step 4: Brainstorm
`TaskUpdate(T4, status="in_progress")` — auto-unblocks once T1 + T2 + T3 close.
Activate `tkm:brainstorm` skill.

- Weigh the candidate approaches against the scout + diagnosis + research findings
- Lay the trade-offs out
- Get the user's read on the preferred direction

`TaskUpdate(T4, status="completed")`
**Output:** `✓ Step 4: Approach selected - [chosen approach]`

### Step 5: Plan
`TaskUpdate(T5, status="in_progress")`
Send the `planner` subagent to draw up the implementation plan.

- Cut the work into phases
- Mark the dependencies
- Set the success criteria
- Fold the prevention measures into the plan

`TaskUpdate(T5, status="completed")`
**Output:** `✓ Step 5: Plan created - [N] phases`

### Step 6: Implement
`TaskUpdate(T6, status="in_progress")`
Build along the plan. Bring in `tkm:optimize-context`, `tkm:think-sequential`, `tkm:solve-problem`.

- Fix the ROOT CAUSE the diagnosis named — not the symptom
- Follow the plan's phases
- Smallest change per phase

`TaskUpdate(T6, status="completed")`
**Output:** `✓ Step 6: Implemented - [N] files, [M] phases`

### Step 7: Verify + Prevent
`TaskUpdate(T7, status="in_progress")`

**Mandatory skill chain:**
1. **Iron-law verify:** Re-run the EXACT commands from the pre-fix state. Diff before against after.
2. **Regression test:** Add thorough tests. They MUST fail without the fix and pass with it.
3. **Defense-in-depth:** Stack in every prevention layer that fits (see `references/prevention-gate.md`).
4. **Parallel verification:** Launch `Bash` agents: typecheck + lint + build + test.
5. **Edge cases:** Push on boundaries, security implications, performance impact.

**If verification fails:** Drop back to Step 2 and re-diagnose. Three attempts max → put the architecture on trial.

See `references/prevention-gate.md` for prevention requirements.

`TaskUpdate(T7, status="completed")`
**Output:** `✓ Step 7: Verified + Prevented - [before/after], [N] tests, [M] guards`

### Step 8: Code Review
`TaskUpdate(T8, status="in_progress")`
Hand off to the `reviewer` subagent.

See `references/review-cycle.md` for mode-specific handling.

`TaskUpdate(T8, status="completed")`
**Output:** `✓ Step 8: Review [score]/10 - [status]`

### Step 9: Finalize
`TaskUpdate(T9, status="in_progress")`
- Summarize: root cause, evidence chain, changes, prevention measures, confidence score
- Activate `tkm:manage-project` for task sync-back, plan status updates, and progress tracking
- Send the `doc-writer` subagent to handle documentation
- Send the `git-manager` subagent to land the commit
- Run `/tkm:write-journal`

`TaskUpdate(T9, status="completed")`
**Output:** `✓ Step 9: Complete - [actions taken]`

## Skills/Subagents Activated

| Step | Skills/Subagents |
|------|------------------|
| 1 | `tkm:scan-codebase` OR parallel `Explore` subagents |
| 2 | `tkm:debug-code`, `tkm:think-sequential`, parallel `Explore`, (`tkm:solve-problem` auto) |
| 3 | `researcher` (runs parallel with steps 1+2) |
| 4 | `tkm:brainstorm` |
| 5 | `planner` |
| 6 | `tkm:solve-problem`, `tkm:think-sequential`, `tkm:optimize-context` |
| 7 | `tester`, parallel `Bash` verification |
| 8 | `reviewer` |
| 9 | `tkm:manage-project`, `doc-writer`, `git-manager` |

**Rules:** No skipped steps. Confirm a phase before moving past it. One phase at a time.
**Frontend:** Reach for `chrome`, `tkm:automate-browser`, or whatever skill/tool fits to verify.
**Visual Assets:** Use the Read tool to inspect and confirm visual assets.
