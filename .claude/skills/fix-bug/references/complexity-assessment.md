# Complexity Assessment

Size up the issue before you route it. This call comes AFTER Step 1 (Scout) and Step 2 (Diagnose).

## Classification Criteria

### Simple (→ workflow-quick.md) — No Tasks

**Indicators:**
- One file in play
- Plain error message (type error, syntax, lint)
- Keywords: `type`, `typescript`, `tsc`, `lint`, `eslint`, `syntax`
- The fix location is obvious
- Diagnosis has confirmed the root cause (not assumed it)

**Task usage:** Skip them. Under 3 steps, the bookkeeping costs more than it returns.

**Examples:**
- "Fix type error in auth.ts"
- "ESLint errors after upgrade"
- "Syntax error in config file"

### Moderate (→ workflow-standard.md) — Use Tasks (6 phases)

**Indicators:**
- 2-5 files in play
- Root cause known, but the fix reaches across several files
- Diagnosis needs investigation to confirm
- Keywords: `bug`, `broken`, `not working`, `fails sometimes`
- Test failures with the root cause already traced

**Task usage:** Stand up 6 phase tasks with dependencies. See `references/task-orchestration.md`.

**Examples:**
- "Login sometimes fails"
- "API returns wrong data"
- "Component not rendering correctly"

### Complex (→ workflow-deep.md) — Use Tasks with Dependency Chains (9 phases)

**Indicators:**
- Reaches across the system (5+ files)
- An architecture call is on the table
- The solution needs research
- Keywords: `architecture`, `refactor`, `system-wide`, `design issue`
- Performance or security holes
- Several components interacting
- Root cause spread across layers/modules

**Task usage:** Stand up 9 phase tasks. Steps 1+2+3 run in parallel (scout+diagnose+research). Full dependency chains. See `references/task-orchestration.md`.

**Examples:**
- "Memory leak in production"
- "Database deadlocks under load"
- "Security vulnerability in auth flow"

### Parallel (→ multiple implementer agents) — Use Task Trees

**Triggers:**
- `--parallel` flag passed explicitly (take the parallel route no matter what auto-classification says)

**Indicators:**
- 2+ independent issues named
- Issues sitting in different areas (frontend + backend, auth + payments)
- Nothing tying the issues to each other
- Keywords: a list of issues, "and", "also", several error types

**Task usage:** Stand up a separate task tree per independent issue (each with scout+diagnose+fix+verify). Spawn one `implementer` agent per tree. See `references/task-orchestration.md`.

**Examples:**
- "Fix type errors AND update UI styling"
- "Auth bug + payment integration issue"
- "3 different test failures in unrelated modules"
