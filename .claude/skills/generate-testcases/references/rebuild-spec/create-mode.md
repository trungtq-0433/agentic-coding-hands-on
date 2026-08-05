# Create Mode

Use this mode when the user wants to generate new testcase suites from one rebuild-spec feature, a ticket-guided issue scope, or all features in one rebuild-spec project.

Load `references/rebuild-spec/common-rules.md` and `references/rebuild-spec/category-and-format-rules.md` first.

Load `references/rebuild-spec/context-objective.md` too.

Load `references/rebuild-spec/ticket-rules.md` too when a ticket file path is provided.

## Context & Objective

- Build one unified, source-grounded understanding of the target behavior before generating cases.
- Choose the cheapest search and read order yourself across the allowed source set. The stages below define required outcomes, not a rigid file-reading ritual.
- When CRUD, visibility, delete, restore, sync, maintenance, or persisted-state behavior is involved, actively search DB-related specs and turn them into concrete DB verification steps.

## Stage 0: Build ticket-summary.md When Ticket Input Exists

1. Read the ticket file first when provided.
2. Extract ticket semantics using `references/rebuild-spec/ticket-rules.md`.
3. Rewrite literal credentials, passwords, tokens, email addresses, private links, raw SQL, raw log links, and attachment IDs into role-based or evidence-only notes unless the user explicitly asks for the raw values.
4. Write `ticket-summary.md` into each matched feature folder.
5. If one ticket maps to multiple features, write `contexts/project/ticket-scope-map.md` before generating suites.

## Stage 1: Resolve Scope And Folder

1. Resolve the rebuild-spec root first.
2. Determine the target set:
   - direct feature spec path => that feature only
   - one explicit `F###` in the request or `--feature F###` => that feature only
   - ticket input with no explicit feature => ticket-derived subset from `ticket-summary.md` and rebuild-spec artifacts
   - no feature filter and no ticket => every feature listed in `feature-list.md`
3. If the request contains multiple explicit feature filters, stop and ask the user to choose one or omit the filter to run the whole project.
4. If both a direct feature spec path and one explicit feature filter are present, keep only the path-selected feature when the codes match. If they do not match, stop and ask the user to resolve the conflict.
5. If both a ticket and one explicit feature filter are present, keep only the overlapping feature. If there is no overlap, stop and ask the user to resolve the conflict.
6. Use `.rebuild-spec-testcases/contexts/project/` as the batch working folder in whole-project mode or multi-feature ticket mode.
7. For each target feature, use `.rebuild-spec-testcases/contexts/[feature-code]-[feature-name]/` as the feature working folder.

## Stage 2: Build source-summary.md For Each Target Feature

1. Start from the strongest available anchors: feature codes, screen codes, routes, ticket issue statements, actor roles, entity names, state flags, or DB clues.
2. Search the allowed source set in the order that best grounds the current behavior. Always inspect the matched feature `technical-spec.md` plus the relevant `feature-list.md` and `screen-list.md` entries.
3. When persistence or data-state may matter, proactively inspect DB-related specs such as `entities.md`, `behavior-logic.md`, or explicit DB clues in the ticket.
4. Write `source-summary.md` using the normalized shape from `references/rebuild-spec/category-and-format-rules.md`.
5. Capture only explicit source content:
   - ticket issue focus, reproduction path, actual vs expected result, and regression notes when ticket input exists
   - overview, actor realm, feature type, priority
   - screen and route inventory
   - validation rules
   - interactions and transitions
   - business rules and edge cases
   - database and data-state notes when relevant
   - access, permission, and session rules
6. Preserve code labels such as `F###`, `SCR###`, `US###`, `PERM###`, route strings, entity names, and explicit state flags only when the source provides them.
7. Overwrite `source-summary.md` if it already exists.

## Stage 3: Build categories.md

1. Read `source-summary.md`.
2. Generate `categories.md` with exactly three sections:
   - `ACCESSING`
   - `GUI`
   - `FUNCTION`
3. Follow the boundary rules in `references/rebuild-spec/category-and-format-rules.md`.
4. Do not let optional sibling docs add behavior beyond the matched feature spec.
5. Do not emit duplicate category tuples.

## Stage 4: Build accessing-testcases.md

1. Read only the `ACCESSING` rows from `categories.md`.
2. Use `Ticket Focus`, `Feature Overview`, `Screen And Route Inventory`, and `Security And Access Considerations` as the source of truth.
3. Cover authentication, authorization, session handling, redirect gates, and navigation entry paths only.
4. If the feature does not expose a public entry path, skip direct-access rows.
5. Write `accessing-testcases.md` using the shared markdown table schema.

## Stage 5: Build gui-testcases.md

1. Read only the `GUI` rows from `categories.md`.
2. Produce a compact GUI suite:
   - exactly one feature-wide layout case, unless the source explicitly requires extra screen-level GUI rows
   - placeholder cases only for explicit placeholders
   - default-value or default-state cases only for explicit defaults
   - empty-state and data-present-state cases only when explicit
   - conditional-visibility and disabled-state cases only when explicit
   - ticket-specific visual-state rows only when the ticket explicitly describes the broken or expected UI state
3. Do not create GUI micro-cases for every screen or field.
4. Write `gui-testcases.md` using the shared markdown table schema.

## Stage 6: Build function-testcases.md

1. Read only the `FUNCTION` rows from `categories.md`.
2. Use `Ticket Focus`, `Validation Rules`, `User Interactions`, `Functional / Business Rules`, `Database And Data-State Notes`, and behavior-scoped access rules as the source of truth.
3. Generate at least one testcase for every `FUNCTION` row.
4. For every explicit validation rule, generate both valid coverage and invalid or boundary coverage.
5. If ticket input exists, generate at least one reproduction testcase and one explicit fix-validation or regression testcase when the ticket provides enough evidence.
6. When persistence or data-state is part of the behavior, add concrete DB verification steps and expected DB outcomes. Prefer `Data and Database Integrity Testing` when the DB assertion is primary.
7. Expand only explicit branches, redirects, cross-screen flows, list behaviors, state transitions, error outcomes, and DB state transitions.
8. If `categories.md` is missing explicit behavior, repair `categories.md` first using the shared category rules, then rerun FUNCTION testcase generation.
9. Stop only when the source is clearly too underspecified to avoid invented behavior.
10. Write `function-testcases.md` using the shared markdown table schema.

## Stage 7: Consolidate To Final Suite And CSV Per Feature

1. Read `accessing-testcases.md`, `gui-testcases.md`, and `function-testcases.md`.
2. Normalize, deduplicate, and simplify using `references/rebuild-spec/category-and-format-rules.md`.
3. Preserve every explicit source-backed intent while keeping the smallest clear testcase set.
4. Reassign final IDs sequentially by section.
5. Write `.rebuild-spec-testcases/testcases/{feature-code}-{feature-name}.md` as the canonical suite.
6. Export `.rebuild-spec-testcases/testcases/{feature-code}-{feature-name}.csv` using the shared CSV contract.

## Stage 8: Finalize Whole-Project Runs

1. If the run scope is whole-project or multi-feature ticket mode, repeat Stages 2-7 for every resolved feature.
2. Preserve already-generated per-feature suites if a later feature hits a hard stop.
3. Write only `.rebuild-spec-testcases/contexts/project/project-run-summary.md` into the batch folder, with the processed feature list, successful features, and any hard stops.
4. Write `.rebuild-spec-testcases/testcases/project-index.md` listing every successfully generated per-feature markdown and CSV suite.

## Hard Stops

- Root path does not match a rebuild-spec layout
- Multiple explicit feature filters in one request
- Missing `feature-list.md`, `screen-list.md`, or resolved feature `technical-spec.md` files
- Ticket file missing or unreadable
- Ticket-derived scope too ambiguous to map safely
- Ticket conflicts with explicit feature selection
- No features resolved from `feature-list.md`
- Source sections too incomplete to produce non-fabricated testcases
- Context too large to finish safely in one run