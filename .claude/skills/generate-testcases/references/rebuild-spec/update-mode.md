# Update Mode

Use this mode when the user wants to refresh existing testcase suites from the current rebuild-spec source for one feature, a ticket-guided issue scope, or all features in one rebuild-spec project.

Load `references/rebuild-spec/common-rules.md` and `references/rebuild-spec/category-and-format-rules.md` first.

Load `references/rebuild-spec/context-objective.md` too.

Load `references/rebuild-spec/ticket-rules.md` too when a ticket file path is provided.

## Context & Objective

- Rebuild the target context from the most informative source clues instead of replaying a rigid read order.
- Search adaptively across the allowed source set until behavior, regression scope, and persisted state are grounded well enough to update the suite safely.
- When CRUD, visibility, delete, restore, sync, maintenance, or persisted-state behavior is involved, actively search DB-related specs and carry the DB checks through the diff and updated rows.

## Stage 0: Build ticket-summary.md When Ticket Input Exists

1. Read the ticket file first when provided.
2. Extract ticket semantics using `references/rebuild-spec/ticket-rules.md`.
3. Rewrite literal credentials, passwords, tokens, email addresses, private links, raw SQL, raw log links, and attachment IDs into role-based or evidence-only notes unless the user explicitly asks for the raw values.
4. Write `ticket-summary.md` into each matched feature folder.
5. If one ticket maps to multiple features, write `contexts/project/ticket-scope-map.md` before updating suites.

## Stage 1: Build source-summary.md For Each Target Feature

1. Resolve the rebuild-spec root first.
2. Determine the target set using the same scope rules as create mode.
3. Rebuild `source-summary.md` for each target feature using the same context-building rules as create mode.
4. Treat each `source-summary.md` as the current source of truth for its feature update.

## Stage 2: Build base-testcases.md For Each Target Feature

1. In single-feature mode, load the existing testcase suite from `--existing` when provided.
2. If `--existing` is absent, fall back to `.rebuild-spec-testcases/testcases/{feature-code}-{feature-name}.md`.
3. In whole-project mode or multi-feature ticket mode, reject `--existing` and use the canonical per-feature suite path for every resolved feature.
4. Save the loaded suite as `base-testcases.md`.
5. If no existing suite can be resolved for a target feature, stop and ask the user to run `create` first or switch to a single-feature update with an explicit suite path.

## Stage 3: Build spec-diff-analysis.md For Each Target Feature

1. Compare `source-summary.md` and `ticket-summary.md` when present against `base-testcases.md`.
2. Split findings into three groups:
   - `NEW`
   - `MODIFIED`
   - `DELETED`
3. Use these meanings only:
   - `NEW`: explicit current-source or ticket-guided behavior with no matching testcase row
   - `MODIFIED`: a related row exists, but its scope, data, steps, or expected result no longer matches the explicit current source
   - `DELETED`: a row no longer has explicit support in the current source
4. Write `spec-diff-analysis.md` with those sections.
5. Do not invent why the behavior changed.

## Stage 4: Apply Update Logic

### NEW Items

1. Categorize each new explicit behavior with the shared ACCESSING/GUI/FUNCTION boundaries.
2. Generate only rows justified by the current source or explicit ticket content.
3. Allocate new IDs by incrementing the highest matching family already present in `base-testcases.md`.
4. For every new validation rule, add both valid coverage and invalid or boundary coverage.
5. When DB state is part of the new behavior, add concrete DB verification steps and use `Data and Database Integrity Testing` when the DB assertion is primary.
6. Do not create GUI micro-cases for every newly mentioned screen or field.

### MODIFIED Items

1. Locate related rows in `base-testcases.md` by `Category`, `Sub_Category`, `Sub_Sub_Category`, `Page_Name`, or objective text.
2. Update `Precondition`, `Test_Data`, `Steps`, and `Expected_Result` to match the current explicit source.
3. Add rows only when the current source introduces a new validation branch, redirect branch, explicit rule, ticket-scoped regression expectation, or DB state assertion that the base suite does not cover.
4. Clear execution-result fields because updated rows need re-testing.

### DELETED Items

1. Remove rows that no longer have explicit support in the current source.
2. If the deleted detail only affects the feature-wide GUI case, update that single case instead of spawning replacement rows.

## Stage 5: Build updated-testcases.md

1. Output one markdown table using the shared schema.
2. Sort rows in this order:
   - `ACCESSING`
   - `GUI`
   - `FUNCTION`
3. Preserve existing IDs unless a new row is required.
4. Ensure new or modified rows keep blank execution-result fields.
5. Run the shared dedupe and collision-cleanup rules before exporting.

## Stage 6: Export Final Suite And CSV Per Feature

1. Write `.rebuild-spec-testcases/testcases/{feature-code}-{feature-name}.md` from `updated-testcases.md`.
2. Export `.rebuild-spec-testcases/testcases/{feature-code}-{feature-name}.csv`.
3. Derive the `Section` column from the category boundary or testcase ID family.

## Stage 7: Finalize Whole-Project Runs

1. If the run scope is whole-project or multi-feature ticket mode, repeat Stages 1-6 for every resolved feature.
2. Write only `.rebuild-spec-testcases/contexts/project/project-run-summary.md` into the batch folder, with the processed feature list and any hard stops.
3. Refresh `.rebuild-spec-testcases/testcases/project-index.md` to reflect the updated per-feature suites.

## Hard Rules

- Keep the updated suite consistent with the shared table format.
- Modify rows only when justified by explicit current-source evidence.
- Keep one feature-wide GUI layout case unless the source clearly justifies more.
- Do not invent new routes, screen states, permission checks, or fallback errors just to preserve previous coverage.

## Hard Stops

- Root path does not match a rebuild-spec layout
- Multiple explicit feature filters in one request
- Missing required source files
- Whole-project or multi-feature ticket update request combined with `--existing`
- Ticket file missing or unreadable
- Ticket-derived scope too ambiguous to map safely
- Ticket conflicts with explicit feature selection
- No features resolved from `feature-list.md`
- Missing existing testcase suite for any target feature
- Ambiguous source change that cannot be mapped without inventing behavior
- Context too large to finish safely in one run