# Create Mode

Use this mode when the user wants to generate new component specs from one MoMorph screen or one screenshot or wireframe image.

Load `common-rules.md` and `output-contract.md` first.

## Stage 0: Set Language And Source Token

1. Set `targetLanguage` from the user's explicit preference when present.
2. If the user did not specify a language, infer it from the user's prompt language; default to English if the prompt is ambiguous.
3. Resolve `source-token`.
   - `momorph`: use `screenId`.
   - `image`: derive a stable slug from the image file stem.

## Stage 1: Build `reference_specs.md` And `design_items.md`

### 1A. Resolve Screen Context

1. In `momorph` mode:
   - call `get_frame(screenId)` and record the frame name, frame ID, and the current item list with each item's `designItemId` when that data is present,
   - call `get_frame_image(screenId)` when available,
   - normalize the current item list from `get_frame(screenId)` into the working inventory,
   - treat that normalized current-item list as the canonical inventory before building staged artifacts.
2. In `image` mode:
   - inspect the full image first,
   - infer a short screen name or purpose from visible heading text or the dominant screen role,
   - if the screen name is still unclear, keep the temporary source token as the folder name.

### 1B. Build `reference_specs.md`

1. In `momorph` mode:
   - build `reference_specs.md` at item level, not only at frame level,
   - for each current item with a resolved `designItemId` from `get_frame(screenId)`, call `get_related_design_items(screenId, designItemId, limit)` with `limit=3` by default unless the user requests another cap,
   - store only the clearly relevant returned references under that current item's section in `reference_specs.md`,
   - if the tool returns source item names, screen names, or short descriptions, keep them with the matching item section,
   - if an item has no `designItemId` in `get_frame(screenId)` or the tool returns no useful references, leave that item's section empty and continue,
   - do not fall back to a broad frame-level reference guess once item-level lookup is available.
2. In `image` mode:
   - write an empty `reference_specs.md` and continue.
   - This empty file preserves the same staged artifact contract as `momorph` mode.
3. Never widen to extra screens or extra images in v1 just to make `reference_specs.md` non-empty.

### 1C. Build the Raw Design Item Inventory

1. In `momorph` mode, use the aligned canonical current-item list as the inventory backbone and preserve each item's resolved `designItemId` in that inventory when available.
2. In `image` mode, detect visible logical components and synthesize rows with these fields:
   - `No`
   - `parentNo`
   - `itemId`
   - `itemName`
   - `textInItem`
   - `iconNameInItem`
   - `hasChildren`
   - `childIds`
   - `startX`
   - `startY`
   - `endX`
   - `endY`
3. In `image` mode, `No` is the hierarchical `itemNo`: top-level items use `1`, `2`, `3`; children use `1.1`, `1.2`; grandchildren use `1.1.1`. Never exceed depth 3.
4. Use `parentNo` only when containment is visually explicit. Otherwise keep the item at the current level and leave `parentNo` blank.
5. For `itemName` in image mode, prefer:
   - visible label text,
   - otherwise a concise role such as `Primary button`, `Email input`, `Card list`, or `Sidebar navigation`.
6. Record `startX`, `startY`, `endX`, and `endY` in original-image pixel space so the later bbox JSON and annotation preview can reuse the exact same bounds.
   - Keep the coordinates ordered at creation time: `startX <= endX` and `startY <= endY`.
7. If there are more than 15 distinct items, split into batches of 15 and write `design_items_part_{batchIndex}.md` plus later `items_analysis_part_{batchIndex}.md`.
8. Write `design_items.md` with:
   - `# Design Context - [screen-name]`
   - screen info block
   - one item overview table covering the fields above plus `designItemId` in `momorph` mode when available.

## Stage 2: Build `items_analysis.md`

### 2A. General Analysis Rules

1. Use the full-screen context plus the local item context as the only truth.
2. In `momorph` mode, use item images when available.
3. In `image` mode, crop mentally or with tooling assistance from the full image; do not invent child structure that is not visually supported.
4. Match any useful tone or terminology only from the current item's section in `reference_specs.md`, but do not borrow from unrelated items or add behavior not present in the current source.
5. In `image` mode, preserve the Stage 1 `No` and bbox coordinates unless Stage 1 contains a clear numbering error.

### 2B. Required Fields Per Item

For each item, derive and write these fields:

- `nameJP`
- `nameTrans`
- `itemType`
- `itemSubtype`
- `buttonType`
- `dataType`
- `format`
- `required`
- `minLength`
- `maxLength`
- `defaultValue`
- `userAction`
- `transitionNote`
- `databaseTable`
- `databaseColumn`
- `databaseNote`
- `validationNote`
- `description`
- `qa`

### 2C. Field Derivation Rules

1. `itemType` must be one of:
   - `button`
   - `checkbox`
   - `radio_button`
   - `dropdown`
   - `file_or_image`
   - `video`
   - `date_picker`
   - `pagination`
   - `popup_dialog`
   - `label`
   - `text_form`
   - `textarea`
   - `table`
   - `others`
2. `buttonType` is only for buttons and must be one of `icon_text`, `icon_only`, `text_only`, `toggle`, or `text_link`.
3. `dataType` is only for visible input controls. Use the closest explicit type such as `string`, `boolean`, `date`, or `integer`. Leave it blank for non-input elements.
4. `format` must describe the visible input pattern, not a vague type label.
   - Example: `<local-part>@<domain>`, `YYYY/MM/DD`, `xxx-xxxx`.
   - If the expected structure is not visible, use `none` and add a QA bullet asking for the required format.
5. `required` should come from visible required or optional markers. If the source is ambiguous, use `false` and raise QA only when the ambiguity blocks accurate validation.
6. `minLength` and `maxLength` may use common field heuristics only when the field purpose is explicit from visible text:
    - Email: `minLength=5`, `maxLength=254`
    - Password: `minLength=8`, `maxLength=128`
    - Phone: `minLength=10`, `maxLength=15`
    - Name: `minLength=1`, `maxLength=100`
    - Textarea: `maxLength=1000`
    - Otherwise leave them blank.
7. `defaultValue` must capture only actual prefilled values or selected states, never placeholders.
8. `userAction` must be exactly one of `on_click`, `while_hovering`, `key_gamepad`, `after_delay`, or blank.
9. `transitionNote` should briefly describe the visible navigation or result in `targetLanguage`.
10. `validationNote` should contain only validation rules and error messages.
    - Use bullets in this shape:
      - `Condition: ...`
      - `Error: "..."`
    - If there are no visible validation rules, leave it blank.
11. `description` must follow this standard structure in `targetLanguage`:
    - `Purpose and Context`
    - `Display Elements`
    - `Function & Logic`
      - Separate those sections with real newline characters `\n`, not semicolons.
   - The final value must contain exactly three lines, one line per section, with no extra blank lines or trailing lines.
      - Keep the three sections in that order, and use the corresponding section labels in `targetLanguage`.
      - Write the final value as multiline text in this shape:
         ```text
         Purpose and Context: ...
         Display Elements: ...
         Function & Logic: ...
         ```
         The English example above shows the structure only; localize the labels when `targetLanguage` is not English.
      - Emit actual line breaks in the value, not the literal characters `\n`.
    Exclude decorative styles and pixel-level layout data.
12. `databaseTable`, `databaseColumn`, and `databaseNote` must stay blank unless the mapping is explicit in the source or the user supplied it directly.
13. `qa` must be a bullet list that focuses on missing frontend behavior, validation, upload rules, list behavior, or state logic. Do not ask about database schema or visual design tokens.

### 2D. Write The Analysis File

1. Write `items_analysis.md` or batched `items_analysis_part_{batchIndex}.md` with:
   - `# Items Analysis - [screen-name]`
   - screen context block
   - one `### Item N: ...` block per item using the field order above.
2. Preserve empty values as blank lines or `-` only in markdown when needed for readability. The final CSV must use blank cells.

## Stage 3: Merge And Export Final Outputs

1. Merge `items_analysis_part_*.md` files if batching was used. Otherwise read `items_analysis.md`.
2. Apply the exact header, cell processing, escaping, and blank-value rules from `output-contract.md`.
3. In `image` mode, keep the CSV `No` column equal to the Stage 1 hierarchical `itemNo`; do not renumber during export.
4. In `image` mode, write `.momorph/specs/{source-token}-{screen-name}-item-bboxes.json` as a JSON array in visual order. Each entry must use this shape:

   ```json
   {
     "itemNo": "1.1",
     "position": {
       "startX": 0,
       "startY": 0,
       "endX": 1200,
       "endY": 56
     }
   }
   ```

5. In `image` mode, run `scripts/annotate-image-bboxes.py` with a Python interpreter that has Pillow available, using the original source image plus the bbox JSON, and write `.momorph/specs/{source-token}-{screen-name}-item-bboxes-annotated.png`.
6. Use `source-token` plus the resolved screen name for the final file paths.
   - `momorph`: `.momorph/specs/{screenId}-{screen-name}.csv`
   - `image` CSV: `.momorph/specs/{source-token}-{screen-name}.csv`
   - `image` bbox JSON: `.momorph/specs/{source-token}-{screen-name}-item-bboxes.json`
   - `image` annotated preview: `.momorph/specs/{source-token}-{screen-name}-item-bboxes-annotated.png`
7. Write raw CSV only. Do not wrap the CSV in markdown fences.

## Hard Stops

- Missing source input
- More than one source in one run
- Mixed-family request
- Update or diff request
- Image hierarchy clearly requires depth greater than 3
- Screen or image too ambiguous to split safely into stable components
- Source too weak to justify non-empty specs without fabrication