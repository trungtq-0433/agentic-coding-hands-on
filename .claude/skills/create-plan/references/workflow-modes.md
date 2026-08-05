# Processing Levels & Strategy

create-plan's effort axis is the shared `--level low|medium|high|max`
(`_shared/processing-levels.md`). Strategy flags (`--parallel`, `--two`,
`--tdd`, `--no-tasks`) are **orthogonal** — they compose with any level.

## Auto-Detection (Default: `--auto` / no flag)

With no `--level` given, read the task and pick the level (and any strategy flag it implies):

| Signal | Level / flag | Rationale |
|--------|--------------|-----------|
| Simple task, clear scope, no unknowns | `low` | Skip research overhead |
| Ordinary task, mostly familiar | `medium` *(default)* | Light research, no gates |
| Complex task, unfamiliar domain, new tech | `high` | Research + red team |
| Security / auth / data integrity / high blast radius | `max` | Full research + scout + red team + validate |
| 3+ independent features/layers/modules | + `--parallel` | Enable concurrent agents (composes with the level) |
| Ambiguous approach, multiple valid paths | + `--two` | Compare alternatives (composes with the level) |

When the signal isn't clear-cut, fall back to `AskUserQuestion`.

## Deprecated alias resolution

Resolve old flags to a level BEFORE anything else, then print a one-line deprecation notice:

| Old flag | Resolves to | Notice |
|----------|-------------|--------|
| `--fast` | `--level low` | `--fast is deprecated; use --level low` |
| `--hard` | `--level high` | `--hard is deprecated; use --level high` |
| `--deep` | `--level max` | `--deep is deprecated; use --level max` |

`--parallel` / `--two` were never effort levels — they stay as the orthogonal strategy flags below, unchanged.

## Scope Challenge Integration

Step 0 (the Scope Challenge in `scope-challenge.md`) comes before level detection and can tilt it:
- User picks **EXPANSION** → lean toward `--level high` (or add `--two`)
- User picks **REDUCTION** → lean toward `--level low`
- User picks **HOLD** → ride with whatever auto-detection chose

An explicit `--level` always wins over the suggestion.
The scope challenge itself is skipped at `--level low` or when the task is trivial.

## Per-Level Workflow

### `--level low`
Skip research entirely. Analyze → Plan → Hydrate Tasks.

1. Read the codebase docs (`codebase-summary.md`, `code-standards.md`, `system-architecture.md`)
2. Hand the plan off to the `planner` subagent
3. Hydrate tasks (unless `--no-tasks`)
4. **Context reminder:** `/tkm:takumi --auto {absolute-plan-path}/plan.md`

**Why the `--auto` takumi flag?** Lean planning earns lean execution — the review gates come off.

### `--level medium` *(default)*
One light research pass, no gates. Research(light) → Analyze → Plan → Hydrate Tasks.

1. Send out a single `researcher` agent (capped) only if the task has real unknowns; otherwise lean on the docs
2. Read the codebase docs; scout with `/tkm:scan-codebase` only when the docs fall short
3. Hand research + docs to the `planner` subagent
4. Hydrate tasks (unless `--no-tasks`)
5. **Context reminder:** `/tkm:takumi {absolute-plan-path}/plan.md`

### `--level high`
Research → Scout → Plan → Red Team → Validate(optional) → Hydrate Tasks.

1. Send out at most 2 `researcher` agents at once, each on a different angle, each capped at 5 calls
2. Read the codebase docs; when they're stale or absent, run `/tkm:scan-codebase` to comb the code
3. Collect the research and scout report paths, then feed them to the `planner` subagent
4. Run the post-plan red team review (Red Team Review section below)
5. Run the post-plan validation if `Validation: mode` calls for it (Validation section below)
6. Hydrate tasks (unless `--no-tasks`)
7. **Context reminder:** `/tkm:takumi {absolute-plan-path}/plan.md`

**Why no takumi flag?** Careful planning earns interactive review gates on the way out.

### `--level max`
Research(deep) → per-phase Scout → Plan → Red Team → Validate → Hydrate Tasks.

1. Send out 2-3 `researcher` agents, plus a per-phase scout pass for the riskier phases
2. Read the codebase docs; run `/tkm:scan-codebase` for the areas each phase touches
3. Feed research + per-phase scout reports to the `planner` subagent
4. Run the post-plan red team review (always)
5. Run the post-plan validation (always)
6. Hydrate tasks (unless `--no-tasks`)
7. **Context reminder:** `/tkm:takumi {absolute-plan-path}/plan.md`

## Orthogonal Strategy Flags

These compose with ANY level — they change *how* the work is shaped, not how hard the skill digs.

### `--parallel`
Plan with file ownership + a dependency graph for concurrent execution. Raises the gates like `--level high` (red team + validate run).

1. Run the level's research/scout as usual
2. The planner cuts phases that carry:
   - **Exclusive file ownership** per phase, with no overlap
   - A **dependency matrix** spelling out what runs side by side versus in sequence
   - A **conflict-prevention** strategy
3. plan.md carries the dependency graph, the execution strategy, and the file-ownership matrix
4. Hydrate tasks: `addBlockedBy` on the sequential dependencies, no blockers on the parallel groups
5. **Context reminder:** `/tkm:takumi --parallel {absolute-plan-path}/plan.md`

**Parallel phase requirements:** every phase stands alone (no runtime dependency on another); any file is edited in exactly ONE phase; carve groups along an architectural layer, feature domain, or tech stack (e.g. Phases 1-3 parallel DB/API/UI, Phase 4 integration after).

### `--two`
Draft two competing approaches and compare. Gates run AFTER the user selects.

1. Run the level's research/scout as usual
2. The planner lays out 2 ways to build it, each with trade-offs spelled out + a recommended pick and why
3. User chooses one
4. Red team review + validation run on the CHOSEN approach
5. Hydrate tasks for the chosen approach (unless `--no-tasks`)
6. **Context reminder:** `/tkm:takumi {absolute-plan-path}/plan.md`

## Task Hydration Per Level / Strategy

| Level / flag | Task Granularity | Dependency Pattern |
|--------------|------------------|--------------------|
| `low` | Phase-level only | Sequential chain |
| `medium` | Phase-level only | Sequential chain |
| `high` | Phase + critical steps | Sequential + step deps |
| `max` | Phase + critical steps + per-phase | Sequential + step deps |
| `+ --parallel` | Phase + steps + ownership | Parallel groups + sequential deps |
| `+ --two` | After user selects approach | Sequential chain |

All levels: see `task-management.md` for the TaskCreate patterns and metadata.

## Post-Plan Red Team Review

A hostile pass — reviewers brought in to break the plan before validation gets to it.

**Runs at:** `--level high` and `--level max`, or with `--parallel` / `--two`. **Skipped at:** `--level low` and `--level medium`.

**Invocation:** Run `/tkm:create-plan red-team {plan-directory-path}`.
```
/tkm:create-plan red-team {plan-directory-path}
```

**Sequence:** Red team goes BEFORE validation, and here's why:
1. The red team can reshape the plan — new risks, cut sections, fresh constraints
2. Validation should sign off on the FINAL plan, not a draft that's about to change
3. Validate first, red-team second, and you've just invalidated the answers you collected

## Post-Plan Validation

Read `## Plan Context` → `Validation: mode=X, questions=MIN-MAX`:

| Mode | Behavior |
|------|----------|
| `prompt` | Ask: "Validate this plan with interview?" → Yes (Recommended) / No |
| `auto` | Run `/tkm:create-plan validate {plan-directory-path}` |
| `off` | Skip validation |

**Invocation (prompt mode, once the user says yes):** Run:
```
/tkm:create-plan validate {plan-directory-path}
```

**Runs at:** `--level max` (always); optional at `--level high`. **Skipped at:** `--level low` and `--level medium`.

## Context Reminder (MANDATORY)

Once the plan exists, you MUST print this with the **real absolute path** filled in:

| Level / flag | Takumi Command |
|--------------|-----------------------------|
| `low` | `/tkm:takumi --auto {path}/plan.md` |
| `medium` | `/tkm:takumi {path}/plan.md` |
| `high` | `/tkm:takumi {path}/plan.md` |
| `max` | `/tkm:takumi {path}/plan.md` |
| `+ --parallel` | `/tkm:takumi --parallel {path}/plan.md` |

> **Best Practice:** Run `/clear` before you start building so planning context doesn't bleed into the work.
> Then fire the takumi command above.

**Why the absolute path?** A `/clear` wipes what the previous session knew.
This reminder is **NON-NEGOTIABLE** — it goes out every time, right after you present the plan.

## Pre-Creation Check

Read `## Plan Context` from the injected context:
- **"Plan: {path}"** → Ask "Continue with existing plan? [Y/n]"
- **"Suggested: {path}"** → Just a branch hint — ask whether to activate it or start fresh
- **"Plan: none"** → Start a new one off the `Plan dir:` in `## Naming`

After creating it: `node .claude/scripts/set-active-plan.cjs {plan-dir}`
Carry the plan directory path into every subagent you spawn along the way.
