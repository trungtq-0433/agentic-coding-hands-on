---
name: tkm:translate-file
description: "Translate files (PDF/DOCX/XLSX/EPUB) into any language using a parallel sub-agent pipeline — convert → chunk → glossary → translate → merge. For documents, spreadsheets, books, and manuals."
argument-hint: "<file-path> [--target <lang>] [--concurrency <n>] [--keep-intermediates]"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
  openclaw:
    requires:
      bins: ["python3", "pandoc", "ebook-convert"]
module: specialized-output
triggers: ["translate this document", "dịch file", "translate PDF/Word/Excel", "translate book", "翻訳", "dịch tài liệu"]
---
# File Translation

A document that spans hundreds of pages cannot be translated in a single pass.
The pipeline divides, translates in parallel, and reassembles — each piece handled with care.

You are a file translation assistant. You translate documents from one language to another by orchestrating a multi-step pipeline.

> **DO NOT** create plans or reports in USER directory.
> **MUST** create plans or reports in **THE CURRENT WORKING PROJECT DIRECTORY**.

## Workflow

### 0. Check and Auto-Install Dependencies

Load `references/setup.md` for full install instructions. Verify both `pandoc` and `ebook-convert` are available. If either is missing, follow the auto-install steps there **without asking the user**. **Do NOT proceed if calibre is still missing after the auto-install attempt** — output must always match the input file type (PDF→PDF, DOCX→DOCX), so there is no fallback. Tell the user which tool failed and ask them to install it manually, then re-run.

### 1. Collect Parameters

Determine the following from the user's message:

- **file_path**: Path to the input file (PDF, DOCX, XLSX, or EPUB) — REQUIRED
- **target_lang**: Target language code (default: `vi`) — e.g. vi, en, zh, ja, ko, fr, de, es
- **concurrency**: Number of parallel sub-agents per batch (default: `8`)
- **temp_root**: Optional directory under which `{filename}_temp/` should be created
- **export_name**: Optional filename stem for user-facing output aliases
- **custom_instructions**: Any additional translation instructions from the user (optional)

If the file path is not provided, ask the user.

### 2. Preprocess — Convert to Markdown Chunks

Run the conversion script to produce chunks:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/convert.py "<file_path>" --olang "<target_lang>"
```

If the user provided `temp_root`, add `--temp-root "<temp_root>"`. The temp
directory leaf name remains `{filename}_temp/`; only the parent directory
changes.

**Format-preserving pipelines (auto-selected by file type):**

- **DOCX input** → automatically uses `docx_native` mode (python-docx in-place extraction). Preserves exact fonts, sizes, colors, spacing, tables, images, and embedded objects. Also extracts section headers/footers and footnotes/endnotes for translation. Falls back to Calibre/Markdown on failure.
- **PDF input** → automatically uses `pdf_inplace` mode (PyMuPDF text-swap engine). Keeps the original PDF as canvas: redacts only text glyphs (`images=0, graphics=0`), then re-inserts translated text into exact original bounding boxes. Images, formulas, vector graphics, and layout are **never touched**. Falls back to `pdf_docx_bridge` (pdf2docx → python-docx) on failure, then Calibre/Markdown as last resort.
  - `pdf_profile.json` is emitted alongside chunks. It records `scanned_pages`, `columns_per_page`, `has_translatable_images`, and `dominant_script`.
  - User overrides (CLI flags or custom_instructions): `--translate-img` (run vision-OCR on image-only pages), `--page-range N-M` (translate only pages N through M).
- **PPTX input** → automatically uses `pptx_native` mode (python-pptx). Captures per-run formatting (bold/italic/color/size/font) for every paragraph across slides, tables, and speaker notes. Requires the MAP pass (step 6.6) before rebuild to preserve mid-paragraph formatting.
- **XLSX input** → automatically uses `xlsx_native` mode (openpyxl). Extracts text cells only (skips formulas, numbers, empty cells). Preserves all formulas, formatting, and structure.
- **EPUB input** → always uses Calibre/Markdown (no native mode).

In DOCX/PDF-bridge native mode, chunks contain `[P:N]` paragraph markers — see rule 14 in the translation prompt.
In `pdf_inplace` mode, chunks contain `[E:page_line]` element markers — see rule 14-B in the translation prompt.
In XLSX native mode, chunks contain `[CELL:SheetName!A1]` cell address markers — preserve these exactly when translating.
In `pptx_native` mode, chunks contain `[PPTX:S:SH:P]` slide/shape/paragraph markers — preserve these exactly when translating (same rule as 14: translate only text after the marker, do not alter or remove the marker).

To force legacy Calibre/Markdown behavior for any format, add `--mode markdown`.

This creates a `{filename}_temp/` directory containing:

- `input.html`, `input.md` — intermediate files (Calibre/Markdown mode only)
- `chunk0001.md`, `chunk0002.md`, ... — source chunks for translation
- `manifest.json` — chunk manifest for tracking and validation
- `config.txt` — pipeline configuration with metadata (`conversion_method` field)
- `docx_structure.json` — per-paragraph format metadata (native mode only)

### 3. Discover Source Chunks

Use Glob to find all source chunks:

```
Glob: {filename}_temp/chunk*.md
```

Exclude `output_chunk*.md` from the source list. The selective re-translation
plan below decides which chunks actually need work.

### 3.5. Build Glossary (term consistency)

A separate sub-agent translates each chunk with a fresh context. Without shared state, the same proper noun can drift across multiple translations. The glossary makes every sub-agent see the same canonical translation for the terms that appear in its chunk.

If `<temp_dir>/glossary.json` already exists, skip the rebuild — re-running the skill must not overwrite a hand-edited glossary. To force a rebuild, delete the file.

Otherwise:

1. **Sample chunks**: read `chunk0001.md`, the last chunk, and 3 evenly-spaced middle chunks. If `chunk_count < 5`, sample all of them.
2. **Extract terms**: from the samples, identify proper nouns and recurring domain terms that need consistent translation across the document — typically people, places, organizations, technical concepts. Translate each into the target language. Skip generic vocabulary that any translator would render the same way.
3. **Write `glossary.json`** in the temp dir, matching this v2 schema:

   ```json
   {
     "version": 2,
     "terms": [
       {"id": "Manhattan", "source": "Manhattan", "target": "マンハッタン",
        "category": "place", "aliases": [], "gender": "unknown",
        "confidence": "medium", "frequency": 0,
        "evidence_refs": [], "notes": ""}
     ],
     "high_frequency_top_n": 20,
     "applied_meta_hashes": {}
   }
   ```

   Existing v1 `glossary.json` files are auto-upgraded to v2 on first load. v2 forbids the same surface form (source or alias) appearing in two different terms; if a v1 file has polysemous duplicate sources, the upgrade aborts with a disambiguation message.
4. **Count frequencies** by running:

   ```bash
   {baseDir}/../.venv/bin/python3 {baseDir}/scripts/glossary.py count-frequencies "<temp_dir>"
   ```

   This scans every `chunk*.md` (excluding `output_chunk*.md`), updates each term's `frequency` field, and writes back atomically.

The glossary is hand-editable. If the user edits a `target`, `aliases`, or
`category` field after a partial run, the run-state planner in the next step
will re-translate only chunks whose recorded term set or term hashes are
affected.

### 3.7. Plan Selective Re-translation

Run:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/run_state.py plan "<temp_dir>"
```

If the user explicitly asks to apply glossary edits to outputs produced before
`run_state.json` existed, add `--retranslate-untracked`; otherwise keep the
default so old temp dirs remain resumable without mass re-translation.

Capture stdout JSON:

- `translation_chunk_ids` — chunks to translate in this run.
- `record_only_chunk_ids` — existing valid outputs that need `run_state.json`
  records but do not need translation.
- `unchanged_chunk_ids` — existing outputs already consistent with the current
  source chunks and glossary.

If `record_only_chunk_ids` is non-empty, record them before launching
sub-agents:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/run_state.py record "<temp_dir>" chunk0001 chunk0002 ...
```

Use `translation_chunk_ids` as the work queue for Step 4. If it is empty, skip
to Step 5.

### 4. Parallel Translation with Sub-Agents

**Check conversion mode first**: read `config.txt` from the temp directory.
- If `conversion_method` is `docx_native` or `pdf_docx_bridge`: chunks contain `[P:N]` paragraph markers — rule 14 MUST be added to each sub-agent's translation prompt.
- If `conversion_method` is `pdf_inplace`: chunks contain `[E:page_line]` element markers — rule 14-B MUST be added. Each line is exactly one PDF text line (one bbox). Sub-agents must preserve `[E:...]` prefixes verbatim and **must never merge adjacent elements** even if they form a natural sentence — splitting is intentional because each element maps to a unique bbox. This is critical: merging destroys the bbox mapping and breaks re-insertion.
- If `conversion_method` is `xlsx_native`: chunks contain `[CELL:SheetName!A1]` markers. Each line is one cell. Sub-agents must preserve the `[CELL:...]` prefix exactly and translate only the text after it. Rule 14 does **not** apply (no `[P:N]` markers). Heading rules (8–11) also do not apply.

**Each chunk gets its own independent sub-agent** (1 chunk = 1 sub-agent = 1 fresh context). This prevents context accumulation and output truncation.

Launch chunks in batches to respect API rate limits:

- Each batch: up to `concurrency` sub-agents in parallel (default: 8)
- Wait for the current batch to complete before launching the next

**Spawn each sub-agent with the following task.** Use whatever sub-agent/background-agent mechanism your runtime provides (e.g. the Agent tool, sessions_spawn, or equivalent).

The output file is `output_` prefixed to the source filename: `chunk0001.md` → `output_chunk0001.md`.

> Translate the file `<temp_dir>/chunk<NNNN>.md` to {TARGET_LANGUAGE} and write the result to `<temp_dir>/output_chunk<NNNN>.md`. Follow the translation rules below. Output only the translated content — no commentary.

Each sub-agent receives:

- The single chunk file it is responsible for
- The temp directory path
- The target language
- The translation prompt (see below)
- A per-chunk term table (see "Term table assembly" below)
- Read-only neighboring chunk excerpts (see "Neighbor context assembly" below)
- Any custom instructions

**Term table assembly** — before spawning a sub-agent, run:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/glossary.py print-terms-for-chunk "<temp_dir>" "chunk<NNNN>.md"
```

Capture stdout. The CLI emits a 3-column markdown table (`原文 | 別名 | 訳文`) of every term that either appears in this chunk (by source OR any alias) OR is in the top-N most-frequent terms document-wide. Inject the table as `{TERM_TABLE}` in rule #13 of the translation prompt. **If stdout is empty (no glossary, or no relevant terms), omit rule #13 from this chunk's prompt entirely** — do not leave a dangling `{TERM_TABLE}` placeholder.

**Neighbor context assembly** — before spawning a sub-agent, run:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/chunk_context.py "<temp_dir>" "chunk<NNNN>.md"
```

Capture stdout. The CLI emits prompt-ready read-only excerpts: the last ~300
characters of the previous chunk and the first ~300 characters of the next
chunk when those files exist. Inject this block as `{NEIGHBOR_CONTEXT}`. If
stdout is empty, omit the neighbor-context block entirely. The sub-agent must
not translate neighboring excerpts or copy them into the output; they are only
for pronoun, gender, and entity-resolution context.

**Each sub-agent's task**:

1. Read the source chunk file (e.g. `chunk0001.md`)
2. Translate the content following the translation rules below
3. Write the translated content to `output_chunk0001.md`
4. Write observations to `output_chunk0001.meta.json` matching the schema below. **Non-blocking** — leave fields empty if unsure; do not invent entities. Always emit the file (even if all arrays are empty), because its presence + content hash is how the main agent tracks whether feedback was already merged.

**Sub-agent meta schema** (`output_chunk<NNNN>.meta.json`):

```json
{
  "schema_version": 1,
  "new_entities": [
    {"source": "Taig", "target_proposal": "テイグ", "category": "person",
     "evidence": "<≤200-char quote from the chunk>"}
  ],
  "alias_hypotheses": [
    {"variant": "Taig", "may_be_alias_of_source": "Tai",
     "evidence": "<≤200-char quote>"}
  ],
  "attribute_hypotheses": [
    {"entity_source": "Tai", "attribute": "gender", "value": "male",
     "confidence": "high", "evidence": "<≤200-char quote>"}
  ],
  "used_term_sources": ["Tai", "Manhattan"],
  "conflicts": [
    {"entity_source": "Tai", "field": "target", "injected": "タイ",
     "observed_better": "太一", "evidence": "<≤200-char quote>"}
  ]
}
```

**Do NOT include a `chunk_id` field** — chunk identity is derived from the filename. Putting it in the payload creates a hallucination hole and validation will reject the file.

The meta file is read by the main agent later and merged into `glossary.json` (see `merge_meta.py`). Sub-agents should fill the schema honestly: cite real quotes from the chunk, never invent entities to "look productive". An empty meta is a perfectly valid output.

**IMPORTANT**: Each sub-agent translates exactly ONE chunk and writes the result directly to the output file. No START/END markers needed.

#### Translation Prompt for Sub-Agents

Full translation prompt (rules 1–14-B, marker preservation for DOCX/PDF/PPTX modes, HTML attribute escaping table, neighbor context block): `references/translation-prompt-template.md`

Load and inject verbatim into each sub-agent's task. Replace `{TARGET_LANGUAGE}`, `{TERM_TABLE}`, `{CUSTOM_INSTRUCTIONS}`, and `{NEIGHBOR_CONTEXT}` before sending.

### 4.5. Merge Sub-Agent Meta Into Glossary (after each batch)

Full protocol (run_state record → prepare-merge → decision kinds → apply-merge → transactional guarantees): `references/meta-merge-protocol.md`

Run after every batch. Record chunk state first, then merge. Never skip `apply-merge` even when `auto_apply` and `decisions_needed` are both empty — omitting it leaves no-op metas re-scanning forever.

### 5. Verify Completeness and Retry

After all batches complete, use Glob to check that every source chunk has a corresponding output file.

If any are missing, retry them — each missing chunk as its own sub-agent. Maximum 2 attempts per chunk (initial + 1 retry).

Also read `manifest.json` and verify:

- Every chunk id has a corresponding output file
- No output file is empty (0 bytes)

Then run the meta-merge observability snapshot:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/merge_meta.py status "<temp_dir>"
```

Also run the selective re-translation state snapshot:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/run_state.py status "<temp_dir>"
```

Surface a one-line summary in the verification report:

> Translated chunks: 50 • Meta files: 48 found / 47 consumed • Malformed: 1 (chunk0099 — see stderr) • Chunks missing meta: chunk0017, chunk0042

Severity rules (none of these fail the run — meta is non-blocking):

- `unmerged_meta_files > 0` after Step 4.5 ran → bug, flag prominently. Resume should have caught this.
- `malformed_meta_files > 0` → sub-agent emitted invalid meta; print chunk_ids and a "fix the file by hand and re-run if you want this chunk's feedback merged" note.
- `meta_files_found < translated_chunks` → sub-agent-compliance issue (some chunks didn't emit meta at all). Print missing chunk_ids.

Report any chunks that failed translation after retry.

### 6. Translate Document Title

Read `config.txt` from the temp directory to get the `original_title` field.

Translate the title to the target language. For Vietnamese, wrap in dấu ngoặc kép: `"translated_title"`. For Japanese, wrap in 『』: `『translated_title』`.

### 6.5. MAP Pass (docx_native mode only)

Full DOCX MAP pass protocol (prepare batches → spawn sub-agents → finalize → `docx_mapped.json`): `references/map-pass-protocol.md` §6.5

Run only when `conversion_method` is `docx_native` and `docx_structure.json` exists. Skip for `pdf_inplace`, `xlsx_native`, `calibre_htmlz`.

### 6.6. MAP Pass (pptx_native mode only)

Full PPTX MAP pass protocol (prepare batches → spawn sub-agents → finalize → `pptx_mapped.json`): `references/map-pass-protocol.md` §6.6

Run only when `conversion_method` is `pptx_native` and `pptx_structure.json` exists. Skip for all other modes.

### 7. Post-process — Merge and Build

Run the build script with the translated title:

```bash
{baseDir}/../.venv/bin/python3 {baseDir}/scripts/merge_and_build.py --temp-dir "<temp_dir>" --title "<translated_title>" --cleanup
```

If the user provided `export_name`, add `--export-name "<export_name>"`.

The `--cleanup` flag removes intermediate files (chunks, input.html, etc.) after a fully successful build. If the user asked to keep intermediates (`--keep-intermediates`), omit `--cleanup`.

The script reads `output_lang` from `config.txt` automatically. Optional overrides: `--lang`, `--author`.

**Output paths by conversion mode:**

- **`pdf_inplace`**: `merge_and_build.py` parses `[E:id]` markers from `output_chunk*.md`, calls the PyMuPDF in-place engine (`pdf_inplace_build.rebuild`) to produce `output.pdf` directly — no Calibre. Emits `pdf_validation.json` with per-page overflow/image-integrity report (step 7.5). Runs remediation automatically on overflow pages (step 7.6).
- **`pptx_native`**: `merge_and_build.py` calls `build_pptx.py` (reads `pptx_mapped.json`) to reconstruct per-run formatting — bold/italic/color/size preserved on the correct translated words. Runs `pptx_cross_check.py` and emits `pptx_crosscheck.json`. Only produces `output.pptx`.
- **`xlsx_native`**: `merge_and_build.py` calls `build_xlsx.py` to write translated text back into cells — full formula/formatting preservation. Only produces `output.xlsx`.
- **`docx_native` / `pdf_docx_bridge`**: `merge_and_build.py` calls `build_docx.py` to reconstruct `output.docx` directly from `docx_structure.json` + translated paragraphs — full font/size/color/table fidelity. PDF is still generated from HTML via Calibre.
- **`calibre_htmlz` (legacy)**: DOCX and PDF are both generated via Calibre from `output_doc.html`.

### 7.5. Validation Report (pdf_inplace mode)

After rebuild, `pdf_validation.json` is written to the temp dir. Format:

```json
{
  "0": {"overflow_ids": ["0_3", "0_7"], "empty_ids": [], "fit_count": 12},
  "1": {"overflow_ids": [], "empty_ids": [], "fit_count": 8}
}
```

- `overflow_ids`: elements where translated text exceeded the bbox (text longer than source)
- `empty_ids`: elements with empty insertion result
- Image-region diff: compares original vs output at 100 DPI — flags pages where images changed

Surface a one-line summary to the user:
> Validation: 12 pages • overflow: p3, p7 • image-integrity: OK

### 7.6. Remediation Loop (pdf_inplace mode, auto-triggered on overflow)

Automatically triggered when `overflow_ids` is non-empty. Fixed strategy menu (no free-form scripting):

1. **Autofit/shrink** — reduce font-size step-wise until `insert_htmlbox` fits (default, always tried first)
2. **Bbox auto-grow** — expand bbox into adjacent whitespace when autofit is insufficient
3. **Column-split override** — re-flow using `pdf_profile.json` column hint

Capped at ≤2 remediation passes. If still failing after 2 passes, page is kept as-is and reported.

This produces in the temp directory:

- **XLSX mode only:** `output.xlsx` — translated spreadsheet with all formulas and formatting intact
- **Document modes:** `output.md`, `output_web.html`, `output_doc.html`, `output.docx`, `output.pdf`
- `xlsx_structure.json` — cell address metadata (xlsx_native mode only, kept for re-runs)
- `docx_structure.json` — paragraph format metadata (docx_native/pdf_docx_bridge only)

### 8. Report Results

Tell the user:

- Where the output files are located
- How many chunks were translated
- The translated document title
- List generated output files with sizes
- Any format generation failures

## References

- `references/setup.md` — Prerequisites and auto-install steps for pandoc and calibre
