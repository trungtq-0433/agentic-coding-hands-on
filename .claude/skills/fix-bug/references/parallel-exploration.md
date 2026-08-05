# Parallel Exploration

Patterns for running several subagents at once — to scout the codebase, confirm the work, and keep them coordinated through native Tasks.

## Parallel Exploration (Scouting)

Fire off several `Explore` subagents together whenever you need to find:
- Related files scattered across different areas
- Similar implementations or patterns
- Dependencies and where things get used

**Pattern:**
```
Task(subagent_type="Explore", prompt="Find [X] in [area1]", description="Scout area1")
Task(subagent_type="Explore", prompt="Find [Y] in [area2]", description="Scout area2")
Task(subagent_type="Explore", prompt="Find [Z] in [area3]", description="Scout area3")
```

**Example - Multi-area scouting:**
```
// One message, several Task calls:
Task("Explore", "Find auth-related files in src/", "Scout auth")
Task("Explore", "Find API routes handling users", "Scout API")
Task("Explore", "Find test files for auth module", "Scout tests")
```

## Parallel Verification (Bash)

Send several `Bash` subagents to confirm the work from different angles.

**Pattern:**
```
Task(subagent_type="Bash", prompt="Run [command1]", description="Verify X")
Task(subagent_type="Bash", prompt="Run [command2]", description="Verify Y")
```

**Example - Multi-verification:**
```
// One message:
Task("Bash", "Run typecheck: bun run typecheck", "Verify types")
Task("Bash", "Run lint: bun run lint", "Verify lint")
Task("Bash", "Run build: bun run build", "Verify build")
```

## Task-Coordinated Parallel (Moderate+)

On multi-phase fixes, let native Tasks keep the parallel agents in step.
See `references/task-orchestration.md` for full patterns.

**Pattern - Parallel issue trees:**
```
// Create separate task trees per independent issue
T_A1 = TaskCreate(subject="[Issue A] Debug", activeForm="Debugging A")
T_A2 = TaskCreate(subject="[Issue A] Fix",   activeForm="Fixing A",   addBlockedBy=[T_A1])
T_B1 = TaskCreate(subject="[Issue B] Debug", activeForm="Debugging B")
T_B2 = TaskCreate(subject="[Issue B] Fix",   activeForm="Fixing B",   addBlockedBy=[T_B1])
T_final = TaskCreate(subject="Integration verify", addBlockedBy=[T_A2, T_B2])

// One agent per issue tree
Task("implementer", "Fix Issue A. Claim tasks via TaskUpdate.", "Fix A")
Task("implementer", "Fix Issue B. Claim tasks via TaskUpdate.", "Fix B")
```

Each agent claims its work with `TaskUpdate(status="in_progress")` and closes it with `TaskUpdate(status="completed")`. Blocked tasks open up on their own as the dependencies clear.

## When to Use Parallel

| Scenario | Parallel Strategy |
|----------|-------------------|
| Root cause unclear, several suspects | 2-3 Explore agents across different areas |
| Multi-module fix | Explore each module in parallel |
| After implementation | Bash agents for typecheck + lint + build |
| Before commit | Bash agents for test + build + lint |
| 2+ independent issues | One Task tree per issue + implementer agents |

## Combining Explore + Tasks + Bash

**Step 1:** Parallel Explore for the scout
**Step 2:** Sequential build (advance Tasks as phases close)
**Step 3:** Parallel Bash for the verify

```
// Scout phase - parallel
Task("Explore", "Find payment handlers", "Scout payments")
Task("Explore", "Find order processors", "Scout orders")

// Collect results, implement fix, TaskUpdate each phase

// Verify phase - parallel
Task("Bash", "Run tests: bun test", "Run tests")
Task("Bash", "Run typecheck", "Check types")
Task("Bash", "Run build", "Verify build")
```

## Resource Limits

- Hold to 3 parallel agents at most (system resources)
- Each subagent runs against a 200K token context ceiling
- Keep prompts tight so context doesn't balloon
- Call `TaskList()` to find work that's unblocked and waiting
