# Update Mode

Use this mode when the user wants to refresh an existing testcase suite after a MoMorph/Figma spec change.

Load `references/momorph/common-rules.md` and `references/momorph/category-and-format-rules.md` first.

## Stage 1: Build spec_diff_analysis.md

1. Call `list_frame_spec_diffs(screenId)`.
2. Split the diff into three groups:
   - `NEW`
   - `MODIFIED`
   - `DELETED`
3. Write `spec_diff_analysis.md` with those sections.
4. Use only explicit diff details. Do not invent why an item changed.

## Stage 2: Build base_testcases.md

1. Call `get_frame_test_cases(screenId)`.
2. Save the response as `base_testcases.md`.
3. Treat this file as the formatting source of truth for the current suite.

## Stage 3: Gather Viewpoints For NEW Items Only

1. Inspect only the `NEW` section of `spec_diff_analysis.md`.
2. For each new item, identify the closest `item_type` and context.
3. Resolve `screen_filename` with the same packaged similarity lookup pattern used in create mode:
   - inspect `data/screen_descriptions.json`,
   - choose only an overlapping reference screen,
   - allow a direct fallback to an uncatalogued file under `data/viewpoints_description/` when the current spec strongly matches that packaged reference,
   - resolve the corresponding JSON file under `data/viewpoints_description/`,
   - skip viewpoints entirely if no concrete packaged reference screen can be resolved.
4. Traverse the resolved JSON array, including nested `sub_items`, and read direct `test_view_points` only from the matching branches that help generate the new rows.
5. Use packaged viewpoints as templates only; they may not add behavior not present in the diff.

## Stage 4: Apply Update Logic

### NEW Items

1. Categorize each new item with the shared ACCESSING/GUI/FUNCTION boundaries.
2. Generate only the rows justified by the new source details.
3. Allocate new IDs by incrementing the highest matching family already present in `base_testcases.md`.
4. For every new validation rule, add both valid coverage and invalid or boundary coverage.
5. Do not create GUI micro-cases for every new field.

### MODIFIED Items

1. Locate related rows in `base_testcases.md` by `Sub_Category`, `Sub_Sub_Category`, `Category`, or objective text.
2. Update `Steps`, `Test_Data`, and `Expected_Result` to match the new source.
3. Add rows when a new validation or interaction rule was introduced.
4. For a changed validation rule, keep or add both valid coverage and invalid or boundary coverage.
5. Remove rows when the old rule no longer exists.
6. Clear execution-result fields because the updated testcase needs re-testing.

### DELETED Items

1. Remove rows tied to the deleted item.
2. If the deleted item only affected the screen-wide GUI case, update that single case instead of creating replacement micro-cases.

## Stage 5: Build updated_testcases.md

1. Output one markdown table using the shared schema.
2. Keep the original 17-column format from `base_testcases.md`.
3. Sort rows in this order:
   - ACCESSING
   - GUI
   - FUNCTION
4. Preserve existing IDs unless a new row is required.
5. Ensure new or modified rows keep blank execution-result fields.
6. Run the shared dedupe and collision-cleanup rules before exporting.

## Stage 6: Export Final CSV

1. Read `updated_testcases.md`.
2. Derive the `Section` column from the category boundary or the testcase ID family.
3. Apply the shared CSV rules:
   - blank fields stay blank
   - `<br>` becomes actual newlines
   - multiline or comma cells are quoted
4. Export `.momorph/testcases/{screenId}-{screen-name}.csv`.

## Hard Rules

- Keep the updated suite consistent with the existing table format.
- Only modify rows justified by explicit `NEW`, `MODIFIED`, or `DELETED` evidence.
- Keep one screen-wide GUI layout case.
- Do not add URL access tests for modal-only content.
- Do not invent missing source details just to keep prior test coverage unchanged.

## Hard Stops

- Missing `screenId`
- More than one target screen
- Missing diff data or missing base testcases
- Ambiguous source change that cannot be mapped without inventing behavior
- Context too large to finish safely in one run