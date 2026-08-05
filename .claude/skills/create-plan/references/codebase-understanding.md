# Codebase Understanding Phase

## Core Activities

### Parallel Scout Agents
- Reach for `/tkm:scan-codebase ext` first, `/tkm:scan-codebase` as the fallback, to track down the files the task will touch
- Point each scout at one slice of the task and let it surface the files for that slice
- Hold off on analysis until every scout has checked back in
- This is how you find your way around a large codebase without reading all of it

### Project Docs Discovery

> See plan `260513-1134-takumi-load-docs-context` (Phase 01 + Phase 02).
> The Phase 02 hook surfaces a paths-only docs index to subagents at spawn time.
> This section is for the planner phase itself — how the planner navigates `docs/`.

How to find your way through `docs/` (no fixed filenames — bend to whatever is actually there):

1. **Step A — Survey:** run `ls docs/` to see the lay of the land. No `docs/` directory? Move on quietly — its absence never stalls planning.
2. **Step B — Rebuild-spec shape:** a `docs/generated/feature-list.md` means you're in the v4.0.0 layered layout, and that file is your front door for feature work. <!-- layout-exempt: docs/ root paths below are single-lang; mode-aware pointer in research-phase.md -->
   - Open `docs/generated/feature-list.md` and locate the feature the task concerns.
   - Then go deep into just that feature's `docs/features/{slug}/technical-spec.md`.
   - The cross-cutting context sits up top — `docs/system/overview.md`, `docs/generated/entities.md`, `docs/generated/screen-flow.md`, and friends. Pull only the pieces your task actually crosses.
3. **Step C — Flat-topic shape:** when `docs/*.md` files live at the top level with no `system/`/`generated/` subdirs, browse by subject and open whichever file lines up with the task's domain.
4. **Step D — Workflow rules:** if `claude/rules/development-rules.md` is present, read it for the kit-wide workflow rules — it always lives at `claude/rules/`, never inside `docs/`.
5. **Rule:** reading everything is a waste. Read what the task touches and stop.

### Environment Analysis
- Look over how the dev environment is wired up
- Read the dotenv files and other configuration
- Pin down which dependencies are required
- Get a feel for how the project builds and ships

### Pattern Recognition
- Trace the patterns the codebase already leans on
- Surface the conventions and the architectural calls behind them
- Notice where the implementation stays consistent
- Learn how errors are handled here

### Integration Planning
- Work out where the new feature seams into what already exists
- Chart how components depend on one another
- Follow the data flow and how state is held
- Keep backward compatibility in view

## Best Practices

- Read the docs before you touch the code
- Lean on scouts to pinpoint files — they sharpen the docs review, they never replace it
- Write down the patterns you find so the plan stays consistent with them
- Call out any rough edges or accumulated debt
- Weigh what the change does to the features already running
