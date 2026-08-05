# MAP Pass Protocol — Steps 6.5 and 6.6

## 6.5. MAP Pass (docx_native mode only)

**Run this step only when `conversion_method` is `docx_native`** and `docx_structure.json` exists in the temp directory. Skip entirely for `pdf_inplace`, `xlsx_native`, or `calibre_htmlz` modes.

This step distributes translated text into the original formatting runs via a two-phase translate→map pipeline, replacing the old proportional-split approach.

### 6.5.1 Prepare MAP batches

First merge the translated chunks into `output.md`:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/merge_and_build.py --temp-dir "<temp_dir>" --merge-only
```

Then prepare MAP batches — reads `output.md` + `docx_structure.json`, partitions elements into single-format (synthesized directly) and multi-format (need LLM mapping):

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/docx/docx_mapping.py prepare "<temp_dir>"
```

Capture stdout: an integer N = number of `docx_map_chunkNNNN.json` files written.
- If N = 0: all elements are single-format — skip to 6.5.3 (finalize directly).
- If N > 0: spawn N MAP sub-agents in the next step.

### 6.5.2 MAP Sub-Agents (one per chunk)

For each `<temp_dir>/docx_map_chunkNNNN.json`, spawn a sub-agent with this task:

> Read the file `<temp_dir>/docx_map_chunkNNNN.json`. It is a JSON array where each element has:
> - `id`: element identifier
> - `translated_general_text`: the already-translated text (do NOT change this)
> - `components`: original formatting runs with text and attributes (bold, italic, underline, font_size, font_color, font_name)
>
> Your task: generate `mapped_components` for each element — distribute the `translated_general_text` across formatting runs following the rules in `{baseDir}/scripts/docx/references/mapping-prompt.md`.
>
> Write the result to `<temp_dir>/output_docx_map_chunkNNNN.json` as a JSON array:
> ```json
> [{"id": "...", "mapped_components": [{"text": "...", "bold": null, ...}]}]
> ```
> No markdown fences, no commentary — raw JSON only.
>
> CRITICAL: The concatenation of all `text` fields in `mapped_components` MUST equal `translated_general_text` exactly. Verify this before writing.

Launch all N sub-agents in parallel (same concurrency limit as translation). Wait for all to complete before proceeding.

### 6.5.3 Finalize

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/docx/docx_mapping.py finalize "<temp_dir>"
```

This reads `output_docx_map_chunkNNNN.json` outputs + single-format skip data, validates concat equality, applies single-run fallback on mismatch, and writes `docx_mapped.json`.

---

## 6.6. MAP Pass (pptx_native mode only)

**Run this step only when `conversion_method` is `pptx_native`** and `pptx_structure.json` exists. Skip for all other modes.

Same two-phase translate→map pipeline as DOCX (step 6.5), adapted for PPTX slide/shape markers.

### 6.6.1 Prepare MAP batches

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/pptx/pptx_mapping.py prepare "<temp_dir>"
```

Reads `output_chunk*.md` (already translated) + `pptx_structure.json`. Partitions elements into single-format (synthesized directly, no LLM) and multi-format (need LLM mapping). Capture stdout integer N:
- If N = 0: all single-format — skip to 6.6.3.
- If N > 0: spawn N MAP sub-agents.

### 6.6.2 MAP Sub-Agents (one per chunk)

For each `<temp_dir>/pptx_map_chunkNNNN.json`, spawn a sub-agent with this task:

> Read `<temp_dir>/pptx_map_chunkNNNN.json`. It is a JSON array where each element has:
> - `id`: element identifier (e.g. `"PPTX:0:1:2"`)
> - `translated_general_text`: already-translated text (do NOT change this)
> - `components`: original formatting runs with text and attributes (bold, italic, underline, font_size, font_color, font_name)
>
> Generate `mapped_components` for each element — distribute `translated_general_text` across formatting runs following the rules in `{baseDir}/scripts/docx/references/mapping-prompt.md`.
>
> Write the result to `<temp_dir>/output_pptx_map_chunkNNNN.json` as a JSON array:
> ```json
> [{"id": "...", "mapped_components": [{"text": "...", "bold": null, ...}]}]
> ```
> No markdown fences, no commentary — raw JSON only.
>
> CRITICAL: The concatenation of all `text` fields in `mapped_components` MUST equal `translated_general_text` exactly.

Launch all N sub-agents in parallel (same concurrency limit as translation).

### 6.6.3 Finalize

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/pptx/pptx_mapping.py finalize "<temp_dir>"
```

Reads `output_pptx_map_chunkNNNN.json` + skip data, validates concat equality, applies single-run fallback on mismatch, writes `pptx_mapped.json`.
