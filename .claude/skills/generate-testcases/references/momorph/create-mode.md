# Create Mode

Use this mode when the user wants to generate new testcase artifacts from a MoMorph screen or MoMorph URL.

Load `references/momorph/common-rules.md` and `references/momorph/category-and-format-rules.md` first.

## Stage 1: Resolve Screen And Folder

1. Call `get_frame(screenId)`.
2. Extract the exact screen name.
3. Use `.momorph/contexts/testcases/[screen-name]/` as the working folder.

## Stage 2: Build specs.md

1. Call `list_design_items(screenId)`.
2. Parse these fields when present:
   - `id`
   - `name`
   - `type`
   - `description`
   - `validation`
   - `errorMessage`
   - `placeholder`
   - `defaultValue`
3. Write `specs.md` using the normalized six-section shape from `references/momorph/category-and-format-rules.md`.
4. Distribute content from `description` into the right sections:
   - validation rules
   - interaction behavior
   - error conditions
   - business logic
   - security notes
5. Infer only high-level purpose or navigation labels that are directly supported by the screen context. Do not invent behavior.
6. Overwrite `specs.md` if it already exists.

## Stage 3: Build viewpoints.md

1. Read the packaged screen catalogue from `data/screen_descriptions.json`.
2. Extract keywords from `specs.md`:
   - field names
   - control types
   - validation verbs
   - interaction verbs
   - domain terms such as email, OTP, billing, password
3. Select only screens whose descriptions clearly overlap with the current screen.
4. If the screen catalogue yields no safe candidate but the current spec strongly matches an uncatalogued packaged reference, resolve that file directly from `data/viewpoints_description/` with the lookup rules from `common-rules.md`.
5. For each resolved packaged file, inspect the JSON array as the local replacement for detailed screen info.
6. Traverse all top-level entries and nested `sub_items`, and keep only candidate branches whose `item_type` and behavior clearly overlap with the current screen's explicit source content.
7. Pull direct `test_view_points` from matching branches only. If a branch exposes nested `sub_items`, traverse those branches recursively and extract only the viewpoint-like rules that match the current screen's explicit source content.
8. Keep only viewpoints consistent with the current screen's explicit source content.
9. If no similar screen exists and no packaged viewpoint file resolves safely, write an empty `viewpoints.md` and continue.

## Stage 4: Build categories.md

1. Read `specs.md` and `viewpoints.md`.
2. Generate `categories.md` with exactly three sections:
   - `ACCESSING`
   - `GUI`
   - `FUNCTION`
3. Follow the boundary rules in `references/momorph/category-and-format-rules.md`.
4. Do not let viewpoints add new behavior.
5. Do not emit duplicate category tuples.

## Stage 5: Build accessing-testcases.md

1. Read only the `ACCESSING` rows from `categories.md`.
2. Use `Screen Overview` and `Security Considerations` as the source of truth.
3. If `.momorph/contexts/testcases/group-specs.md` exists, use it only to reason about navigation paths.
4. Cover access permission, authentication, and navigation only.
5. If the current screen is modal-only, skip direct URL access tests.
6. Write `accessing-testcases.md` using the shared markdown table schema.

## Stage 6: Build gui-testcases.md

1. Read only the `GUI` rows from `categories.md`.
2. Produce a compact GUI suite:
   - exactly one screen-wide layout case
   - placeholder cases only for explicit placeholders
   - default-value/state cases only for explicit defaults
   - screen-level state cases only when explicit
   - consolidated visual-rule cases only when explicit
3. Assert repeated-item sub-elements and finite control groups in consolidated form only.
4. Do not create GUI micro-cases.
5. Write `gui-testcases.md` using the shared markdown table schema.

## Stage 7: Build function-testcases.md

1. Read only the `FUNCTION` rows from `categories.md`.
2. Use `Validation Rules`, `User Interactions`, `Functional / Business Rules`, and explicit behavior in `Security Considerations` as the source of truth.
3. Generate at least one testcase for every FUNCTION row.
4. For every explicit validation rule, generate both valid coverage and invalid or boundary coverage.
5. Expand only explicit branches, transitions, list behaviors, and cross-component effects.
6. Choose `Testcase_Type` from the allowed FUNCTION enum only.
7. If `categories.md` is missing FUNCTION rows for explicit behavior, repair `categories.md` first using the shared category rules, then rerun FUNCTION testcase generation. Do not mint ad hoc category tuples during testcase generation.
8. Stop only when FUNCTION behavior is expected but the source sections that define it are missing or clearly underspecified. Static or read-only screens may legitimately leave one or both sections empty.
9. Write `function-testcases.md` using the shared markdown table schema.

## Stage 8: Consolidate To Final CSV

1. Read `accessing-testcases.md`, `gui-testcases.md`, and `function-testcases.md`.
2. Normalize, deduplicate, and simplify using `references/momorph/category-and-format-rules.md`.
3. Preserve every source-backed intent while keeping the smallest clear testcase set.
4. Reassign final IDs sequentially by section.
5. Export `.momorph/testcases/{screenId}-{screen-name}.csv` using the shared CSV contract.

## Hard Stops

- Missing `screenId`
- More than one target screen
- Missing MoMorph tooling needed for the current stage
- Source sections too incomplete to produce non-fabricated testcases
- Context too large to finish safely in one run