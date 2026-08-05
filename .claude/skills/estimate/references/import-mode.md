# Import Mode — Historical Data Ingestion

AI-assisted import of estimate data from any format into the historical calibration store.

## Workflow

### 1. Parse Input Document

Reuse the same parsing pipeline as estimation (SKILL.md Step 2):

- **Estimate JSON** (has `options`/`categories`/`tasks`): Skip parsing — go directly to Step 2.
- **Excel/CSV with WBS structure**: Run `python3 skills/estimate/scripts/parse-document.py <file> --cache`
- **PDF/DOCX/PPTX/images**: Run `python3 skills/estimate/scripts/parse-document.py <file> --cache`
- **Markdown/text**: Read directly with Read tool.
- **URLs**: Run `python3 skills/estimate/scripts/parse-document.py <url>`

Apply the same sparse-content and multimodal fallback rules as estimation Step 2.

### 2. Interpret & Structure Content

Route by input type:

| Input Type | Method |
|-----------|--------|
| Estimate JSON (agentic-estimate output) | `normalize_estimate_json()` from `historical_data_loader.py` — automatic |
| Excel/CSV with task rows | **Run `extract-role-effort.py` first** (see below), then fill gaps — semi-automatic |
| Unstructured (PDF, DOCX, images, Markdown) | AI extracts task list → manually structure into canonical format |

#### Excel/CSV Extraction (MANDATORY for Excel inputs)

**Always run the extraction script before writing any ad-hoc code:**

```bash
# Step 1: Extract and review (table output)
python3 scripts/extract-role-effort.py <excel-file>

# Step 2: If auto-detected sheet is wrong, specify:
python3 scripts/extract-role-effort.py <excel-file> --sheet "All team"

# Step 3: Get structured output for historical entry creation:
python3 scripts/extract-role-effort.py <excel-file> --yaml
python3 scripts/extract-role-effort.py <excel-file> --json
```

The script (`agentic_estimate/utils/role_effort_extractor.py`) auto-detects:
- WBS sheet selection (prioritizes "All team", "WBS", "Effort" sheets)
- Multi-row header layout with role columns (BE, FE, QA, Design, Infra, PM, BrSE)
- Effort sub-columns (Code, FixBug, Review, UT, etc.) and sums them per role
- Task name/ID columns
- Task type classification via KB aliases

**After running**, review the output for common gaps:
- **"unclassified" tasks**: Non-English task names (Japanese/Vietnamese) may not match KB aliases → manually classify
- **Missing role columns**: Check if responsive/localization QA columns were detected → re-run with `--scan-rows 20` or manually add missing columns
- **Missing roles not in WBS**: BrSE, PM, Infra, UAT are often project-level, not per-task → add from the Summary sheet as `management`/`testing`/`infrastructure` categories
- **Per-task vs summary total mismatch**: VN-style WBS files may use 7-hour workday units in detail rows while summary uses man-months. If per-task sums ≠ summary totals, use proportional scaling: `task_md = round(task_raw / sum_raw * summary_total)`

**To update an existing YAML entry with extracted effort:**
```bash
python3 scripts/extract-role-effort.py <excel-file> --update-entry knowledge-base/historical/accepted/<slug>.yaml
```

**Canonical entry format** (target schema: `schemas/historical-entry-schema.json`):

```yaml
type: accepted  # or "actual"
project:
  name: "project-slug"
  date: "YYYY-MM-DD"
  domain: "e-commerce"          # optional
  tech_stack: ["react", "nestjs"] # optional
  team_size: 5                  # optional
  team_experience: "mid"        # optional
estimate:
  total_md: 100
  tasks:
    - task_type: "crud"         # KB category key
      total_md: 20
      effort:
        be: 10
        fe: 8
        qa_manual: 2
actual:                         # only for type: actual
  total_md: 130
```

**Duplicate task_types**: If a project has two distinct task groups under the same KB category (e.g., app infrastructure + cloud infrastructure), prefer subtypes: `infrastructure_app`, `infrastructure_cloud`. If no meaningful distinction, two entries with the same `task_type` are valid but add a comment explaining the split.

**For unstructured content**: AI extracts task names and effort values, then uses `classify_task_type()` to map task names to KB categories. Warn the user about extraction confidence.

### 3. Collect Metadata (Interactive)

Ask user to confirm/provide:

1. **Entry type**: `accepted` or `actual` *(required)*
2. **Domain**: e-commerce, saas, fintech, healthcare, etc. *(required)*
3. **Tech stack**: comma-separated *(auto-detect from document if available, confirm with user)*
4. **Team size** *(optional — skip if not in source data)* and **team experience** *(optional — infer from document hints like "rank 3.5 developer")*
5. **Slug**: auto-generated from project name *(confirm only if ambiguous)*
6. If `actual`: ask for **actual total man-days** spent

### 4. Sanitize & Validate

1. Run `sanitize_entry()` — strips client-identifiable fields (estimator, client_name, source_document, assumptions). Run even when constructing entries from scratch (catches fields added during extraction).
2. Generalize task names to KB categories using `classify_task_type()` — the extraction script applies this automatically; verify output categories are correct.
3. Validate against `schemas/historical-entry-schema.json` — either via `validate_entry()` or direct `jsonschema.validate()`. Note: `validate-estimate.py` is for estimate JSON output only, NOT historical YAML entries.
4. **Show sanitized YAML preview** to user for confirmation before saving

### 5. Save Entry

```bash
# Check for duplicates first
python3 -c "from agentic_estimate.utils import check_duplicate_slug; print(check_duplicate_slug('<slug>', '<type>'))"
```

- Save YAML to `knowledge-base/historical/{accepted|actuals}/<slug>.yaml`
- If duplicate: ask user to rename slug or use `--force`
- Optionally copy raw file to `knowledge-base/historical/raw/`

### 6. Recompile Knowledge Base

```bash
python3 scripts/compile-knowledge-base.py
```

Confirm `references/historical-summary.md` is updated with new entry stats.

## Batch Import

For multiple files, repeat Steps 1-5 for each file, then run Step 6 once at the end.

## CLI Alternative

For pre-structured JSON/Excel, the CLI script is faster than the interactive skill:

```bash
python3 scripts/import-historical.py <file> --type accepted --domain e-commerce --dry-run
python3 scripts/import-historical.py <file> --type actual --actual-md 150 --force
```

## Multi-Plan Files

When a source document contains multiple estimation plans (e.g., Plan A standard vs Plan B AIDD), **always import both as separate entries**. Use slug suffixes to distinguish: `<slug>-plan-a-<date>`, `<slug>-plan-b-aidd-<date>`. Each entry captures its own multipliers (e.g., AIDD reduction rates in Plan B's `multipliers_used`).

## Unit Conversion

Source sheets may use different effort units. Always check headers and appendix for unit definitions:
- **Man-days (MD)**: use directly
- **Man-months (MM)**: multiply by working days/month (default 20, check Appendix)
- **Man-hours**: divide by working hours/day (default 7h for VN, 8h elsewhere, check Appendix)

## Edge Cases

- **Duplicate slug**: Ask user to rename or confirm overwrite
- **Schema validation failure**: Show errors, let AI fix the entry and re-validate
- **Unstructured content with low confidence**: Warn user, show extracted data for manual correction
- **Multi-estimate file**: If input contains multiple sub-projects, import each as a separate entry
