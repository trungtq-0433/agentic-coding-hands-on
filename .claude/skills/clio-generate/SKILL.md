---
name: clio-generate
description: "Generate SVN Proposal PPTX from Clio Knowledge Graph. Auto-detects whether to run Step A (gen md) first or go straight to Step B (gen slide). Explicit flags: `--gen md` or `--gen slide`. No flag needed — just say 'gen slide for project X' and the skill handles the rest."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - mcp__clio__clio_get_assets_download_url
  - mcp__clio__clio_get_assets_upload_url
  - mcp__clio__clio_finalize_assets_upload
  - mcp__clio__clio_get_artifacts_upload_url
  - mcp__clio__clio_query
argument-hint: "[--gen md|slide] [--project-id ID] [--extra-slides PATH.json]"
metadata:
  author: takumi-agent-kit
  version: "3.2.0"
---

# Slide Proposal — SVN Proposal Generator (2-step pipeline)

This skill runs in two sequential steps, with **smart auto-routing** when no step is specified:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Auto** | No flag / "gen slide" / "tạo slide" | Check if local markdown exists → if not, run Step A then Step B automatically; if yes, go straight to Step B |
| **Step A** | `--gen md` | Check Clio for existing profile → download all assets + merge OR query KG + generate fresh → output local markdown for review |
| **Step B** | `--gen slide` | Check for unresolved conflicts → render SVN PPTX → upload approved markdown, images, and PPTX to Clio |
| **Optional** | `--extra-slides` | AI-generated extra slides from JSON to be included when running Step B |

After Step A, the user may review and edit the markdown before Step B runs. In auto mode the two steps execute back-to-back without interruption.

The profile markdown is **domain-organized**, not slide-organized — adding/removing slides only requires changing the template config, not the agent workflow.

**Requires:** Clio MCP server configured (see Setup below).

---

## Entry Point — Smart Routing

**This section runs first, before any step, whenever the skill is invoked.**

### Step 0: Resolve intent and project_id

1. **Determine project_id** — check in order:
   - Explicit `--project-id` argument from user
   - `.clio.yml` in CWD (`project_id: xxx`)
   - `.estimate.yml` in CWD (`project_id: xxx`)
   - If still missing: ask the user once, then proceed

2. **Determine which step to run** based on the user's input:
   - User passed `--gen md` explicitly → go to **Step A only**
   - User passed `--gen slide` explicitly → go to **Step B only**
   - Otherwise (no flag, or natural language like "gen slide for project X", "tạo slide", "generate proposal") → **Auto mode**: continue to Step 0.3 below

3. **Auto mode — check for existing local markdown:**
   ```bash
   ls outputs/project_content_{project_id}.md 2>/dev/null
   ```
   - **File exists** → skip Step A, go directly to **Step B**. Inform the user: `"Found existing markdown outputs/project_content_{project_id}.md — skipping gen md, rendering slide directly."`
   - **File does NOT exist** → run **Step A** first (silently, no need to ask the user), then **Step B** automatically when Step A completes. Inform the user: `"No local markdown found — running gen md first, then gen slide automatically."`

> **Do NOT ask the user which step to run.** The check above is deterministic. Only ask if `project_id` cannot be resolved.

---

## Data Provider

The skill uses **Clio Knowledge Graph** as the data provider.

- Query tool: `clio_query` MCP tool
- Config: `.clio.yml` (primary) / `.estimate.yml` (fallback)

### Setup

Add to `.mcp.json` or `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "clio": {
      "type": "http",
      "url": "https://clio.sun-asterisk.vn/mcp",
      "headers": { "x-api-key": "${CLIO_API_KEY}" }
    }
  }
}
```

Then create `.clio.yml` in project root with `project_id: your-project-id`.

---

## Step A — `--gen md`

The agent checks Clio for an existing profile markdown (downloading all associated assets), then either merges new KG data into it or generates a fresh one from scratch. The result is saved locally for user review — all uploads happen in Step B after the slide renders.

### Workflow

1. **Read project_id** from `.clio.yml` (fallback `.estimate.yml`; ask user if missing)

2. **Check Clio for existing SLIDE_CONTENT file** — call the `clio_get_assets_download_url` MCP tool:
   ```json
   { "project_id": "{project_id}" }
   ```
   The response contains an `items` array. If empty → Case 1.1. If non-empty → Case 1.2.

3. **If file exists on Clio (Case 1.2):**
   - Download **ALL items** returned by the list response — iterate over every item regardless of file type:
     - For `.md` files: save to the canonical fixed name `outputs/project_content_{id}.md`
     - For all other files (`.png`, etc.): save using their remote filename `outputs/{file_name}`

   > **⚠️ CRITICAL — HOW TO DOWNLOAD:** Always use the **Bash tool** to call `clio-api.py download`. **NEVER use WebFetch** for presigned S3 URLs — WebFetch goes through a proxy that blocks the storage domain, and presigned URLs are too long for WebFetch anyway. The only correct method is via the Python script below.

     ```bash
     VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
     SKILL_DIR="claude/skills/clio-generate"

     # For the markdown file (run via Bash tool):
     $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py download \
       --url "{md_download_url}" \
       --output outputs/project_content_{id}.md
     # For every other file in the list (PNG, etc.) — do NOT skip any:
     $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py download \
       --url "{item_download_url}" \
       --output outputs/{item_file_name}
     ```
   - Query KG for the latest data for each section — read each reference file first, then execute the **exact Japanese query strings** defined in that file. Do NOT write your own queries, do NOT translate to English. The KG is built from Japanese documents and only returns results for Japanese queries.
   - Compare KG data against downloaded markdown section by section:
     - **New info not in markdown** → append/update the relevant section
     - **Conflict (KG value differs from existing value)** → mark inline:
       ```
       <!-- CONFLICT: KG says "X", current value is "Y" — needs review -->
       ```
   - **PNG regeneration:** If KG data for `screen_flow` or `schedule` sections changed (new diagram content detected), regenerate the affected PNG(s) via Mermaid CLI and overwrite the local file. They will be uploaded in Step B.
   - The merged result is already at `outputs/project_content_{id}.md` (the file downloaded above, edited in place)

4. **If no file on Clio (Case 1.1):**
   - Query Clio KG for each domain section — **read each reference file first**, then execute the **exact Japanese query strings** defined step-by-step in that file. Do NOT write your own queries. Do NOT translate to English. The KG is built from Japanese documents; English queries return empty results.
   - Generate PNG images (Mermaid CLI for screen flow + schedule)
   - Assemble JSON matching `ProjectProfile.to_dict()` shape
   - Invoke `gen-md.py` with `--project-id {id}` — outputs `outputs/project_content_{id}.md` (fixed name, no timestamp)

5. **Report to user:**
   - If conflicts were found: `"Found N conflict(s) marked in the markdown. Please review and edit outputs/project_content_{id}.md to resolve all <!-- CONFLICT: ... --> markers, then run --gen slide."`
   - If no conflicts: `"Markdown generated/updated locally. Run --gen slide when ready."`

### Profile JSON shape

The JSON the agent assembles must match the dataclass tree in `scripts/lib/profile_schema.py`. Top-level keys: `project_background`, `features`, `nfr_overview`, `screen_flow`, `business_process`, `benefits`, `approach_comparison`, `assumptions`, `infrastructure`, `software_stack`, `nfr_sections`, `nfr_detailed`, `schedule`. Omit any section the KG has no data for.

### Reference Files (what to query per section)

| Section(s) | Reference |
|------------|-----------|
| project_background, features, nfr_overview | `references/generate-content-overview.md` |
| screen_flow, business_process | `references/generate-content-flow.md` |
| benefits | `references/generate-content-benefits.md` |
| approach_comparison, assumptions | `references/generate-content-approach.md` |
| infrastructure, software_stack, nfr_sections, nfr_detailed, schedule | `references/generate-content-technical.md` |

### Invocation (Case 1.1 — fresh generation)

```bash
VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
SKILL_DIR="claude/skills/clio-generate"

# Agent writes JSON to a temp file, then:
$VENV_PYTHON $SKILL_DIR/scripts/gen-md.py \
  --project-id {project_id} \
  --input /tmp/profile_{project_id}.json \
  --output-dir outputs/
```

---

## Step B — `--gen slide`

Reads the profile markdown and renders the SVN PPTX. No Clio KG access needed.

### Workflow

1. **Locate input** — use `outputs/project_content_{id}.md` (fixed filename, one file per project)
2. **Check for unresolved conflicts** — scan the file for any `<!-- CONFLICT:` markers:
   - If found: **stop immediately** and tell the user:
     `"The markdown still has N unresolved conflict(s). Please edit outputs/project_content_{id}.md, resolve all <!-- CONFLICT: ... --> markers, then re-run --gen slide."`
   - If none: proceed
3. **Invoke `gen-slide.py`** — parses profile, runs role-based rendering against the SVN template
4. Output → `outputs/proposal_{id}_{ts}.pptx`
5. **Visual QA (best-effort, skips silently if `officecli` isn't installed):**
   - From `gen-slide.py`'s stdout, collect every `- Inserted extra slide "..." [...] at index N` line (printed for both auto-routed unrecognized sections and manually-authored `--extra-slides` entries). Slide number = `N + 1` (the print is 0-indexed). This is `--auto-slides` below — pass `""` if no such lines were printed.
   - Run `collect-qa-slides.py` to widen the net beyond auto-routed slides: it also asks `officecli view <pptx> issues` for real text-overflow/off-slide/overlapping-shape hotspots and folds in the noisiest ones (capped at `--max-extra`, default 5, so a deck's already-known-and-handled overflow — see `_queue_overflow_extra` in `renderer.py` — doesn't balloon the QA batch). This is what catches bugs in the 17 bespoke template slides that auto-routing alone never looks at.
     ```bash
     VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
     SKILL_DIR="claude/skills/clio-generate"

     $VENV_PYTHON $SKILL_DIR/scripts/collect-qa-slides.py \
       --input outputs/proposal_{id}_{ts}.pptx \
       --auto-slides "{comma-separated 1-indexed slide numbers from step above, or empty string}"
     ```
     Prints `{"available": false, "slides": "..."}` if `officecli` can't be reached (falls back to just the auto-routed slides, same as before) or `{"available": true, "slides": "...", "issue_flagged_dropped": [...], ...}`. If `issue_flagged_dropped` is non-empty, mention in passing that N additional lower-priority slides were skipped by the cap — don't block on it.
     - If `slides` is empty, skip QA entirely — nothing to check.
   - Otherwise screenshot exactly that slide list:
     ```bash
     $VENV_PYTHON $SKILL_DIR/scripts/qa-slides.py \
       --input outputs/proposal_{id}_{ts}.pptx \
       --slides "{the "slides" value from collect-qa-slides.py}" \
       --output-dir outputs/qa_{id}/
     ```
   - Both scripts auto-download `officecli` on first use if not already on PATH (cached under `~/.cache/clio-generate/bin`, verified against the release's SHA256SUMS — no PATH/system changes, safe to delete). If `qa-slides.py` prints `{"available": false}` — unsupported platform or no network reachable to GitHub — skip QA and fall back to the existing manual-review message below.
   - If it prints `{"available": true, "screenshots": [...]}` — for each entry with `"ok": true`, use the **Read tool** on its `path` (PNG) and check for text overflow, overlapping shapes, empty/orphaned placeholder boxes, or an obviously broken layout. Entries with `"ok": false` mean that slide couldn't be rendered (log the error, don't block on it). Some slides pulled in by the issues scan may turn out fine on inspection (e.g. an off-slide decorative shape from the base template, or text truncation already handled by the appendix mechanism) — that's expected noise, not a failure; only act on what's actually visible and wrong.
     - **Issues found** → tell the user which slide number(s) and what looks wrong, then ask whether to proceed with upload as-is or fix `outputs/project_content_{id}.md` first (loop back to editing + re-running `--gen slide` if they choose to fix).
     - **No issues** → proceed straight to upload, no need for the manual-review prompt.
6. **Upload approved markdown + all PNG images to Clio** (the version that produced the PPTX). Repeat for each file (markdown + all PNGs in `outputs/`):

   > **⚠️ CRITICAL — HOW TO UPLOAD:** Step (b) below MUST be executed via the **Bash tool** calling `clio-api.py put`. **NEVER use WebFetch or any other tool** to PUT to presigned S3 URLs — only the Python script works reliably across all environments.

   a. Get file size in bytes:
      ```bash
      VENV_PYTHON=$([ -f ".claude/skills/.venv/bin/python3" ] && echo ".claude/skills/.venv/bin/python3" || echo "python3")
      SKILL_DIR="claude/skills/clio-generate"

      wc -c < outputs/{file_name}
      ```
      Then call `clio_get_assets_upload_url` MCP tool — **one call per file**:
      ```json
      {
        "project_id": "{project_id}",
        "asset_type": "slide-content",
        "file_name": "{file_name}",
        "content_type": "{mime_type}",
        "file_size": {size_in_bytes}
      }
      ```
      Response: `upload_url`, `storage_path`.

   b. PUT the file to S3 via **Bash tool** (not WebFetch):
      ```bash
      $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py put \
        --url "{upload_url}" \
        --file outputs/{file_name}
      ```

   c. Finalize via `clio_finalize_assets_upload` MCP tool — **one call per file**:
      ```json
      {
        "project_id": "{project_id}",
        "asset_type": "slide-content",
        "file_name": "{file_name}",
        "storage_path": "{storage_path}",
        "content_type": "{mime_type}",
        "file_size": {size_in_bytes}
      }
      ```

   - **Version cleanup (PENDING — no delete API yet):** Ideally keep only the last 3 `SLIDE_CONTENT` markdown versions. Implement once a delete endpoint is available.

7. **Upload generated PPTX to Clio** via MCP tool:

   a. Get PPTX file size in bytes:
      ```bash
      wc -c < outputs/proposal_{id}_{ts}.pptx
      ```

   b. Call `clio_get_artifacts_upload_url` MCP tool:
      - `project_id`: "{project_id}"
      - `artifact_type`: "proposal_slide"
      - `file_name`: "proposal_{id}_{ts}.pptx"
      - `content_type`: "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      - `file_size`: {size_in_bytes}

   c. PUT the PPTX to the returned `upload_url` via **Bash tool** (not WebFetch):
      ```bash
      $VENV_PYTHON $SKILL_DIR/scripts/clio-api.py put \
        --url "{upload_url}" \
        --file outputs/proposal_{id}_{ts}.pptx
      ```
      > **No finalize step** — the server auto-registers artifacts after the S3 PUT.

### Invocation

```bash
$VENV_PYTHON $SKILL_DIR/scripts/gen-slide.py \
  --input outputs/project_content_{project_id}.md \
  --output-dir outputs/
```

`--template` defaults to `SVN Proposal Menu.pptx` (auto-resolved from `templates/`).

> **Environment note:** `VENV_PYTHON` auto-detects the interpreter — uses the venv on local/Takumi installs, falls back to system `python3` on sandboxes where the venv is absent. Both `clio-api.py` and `gen-slide.py` call `ensure_deps()` at startup to self-bootstrap `python-pptx`/`lxml`/`Pillow`/`requests` into a writable temp dir when the packages are not yet installed. No manual `pip install` needed.

---

## Hand-written / free-form markdown — automatic section routing

`gen-md.py` (Step A) is an optional convenience, not a requirement — the user may hand-write `outputs/project_content_{id}.md` directly, in any structure or language, without ever running Step A. `gen-slide.py` (Step B) is decoupled from Step A's schema on purpose: any `##` heading that doesn't match the ~13 known section names is **never silently dropped**.

For each unrecognized `## heading`, `profile_parser.py` classifies its content and auto-routes it to one of the generic layouts in `extra_slide_layouts.py` — no `## extra:` prefix or hand-authored JSON needed:

| Content shape under the heading | Layout chosen |
|---|---|
| Exactly 2 `###` subsections | `comparison_2` |
| 3–5 `###` subsections | `numbered_points` |
| A markdown table | `bullets` (one bullet per row) |
| A bulleted/numbered list | `bullets` |
| 1 or 6+ `###` subsections | `bullets` (one bullet per subsection — outside `comparison_2`/`numbered_points`' hard caps, so never truncates) |
| Short plain paragraph (≤280 chars, no blank-line break) | `hero` |
| Anything else | `bullets` |

The slide is inserted right after the last *recognized* section seen before it in the source file (or at the end of the deck if none). `gen-slide.py`'s stdout prints a `WARNING` per auto-routed section (heading, chosen layout, anchor) — **always review the rendered PPTX before uploading to Clio**, since the heuristic can't guarantee the generic layout looks as polished as the 17 bespoke slide designs.

This runs automatically, every time — no flag required. It composes with `--extra-slides` below: manually-authored entries are appended after the auto-routed ones, not replaced by them.

---

## Step B (optional) — `--extra-slides` AI-generated extra slides

After Step A, the user may edit the content markdown and add **free-form extra sections** that don't fit the 17 fixed slide templates. Each is rendered as a polished slide using a **generate-slide-style layout** (ported from `tkm:generate-slide`), drawn onto a blank canvas cloned from the template's blank end card and inserted right after the section it follows.

Use this when an AI agent should pick the layout deliberately (e.g. to match a specific visual intent). For markdown that's simply hand-written without following the schema at all, the automatic routing above already handles it with zero extra authoring — reach for `## extra:` + hand-crafted JSON only when the automatic heuristic's layout choice isn't good enough.

### Convention in content MD

```markdown
## Features
...

## extra: Migration Strategy
Free-form content the user wants to add. Bullets, paragraphs, anything.
- Phase 1: data export
- Phase 2: dual-write
- Phase 3: cutover

## Non-Functional Requirements (Overview)
...
```

- Heading prefix `## extra:` (case-insensitive) marks an extra section.
- The **anchor section** is the nearest preceding `## <known section>` heading — the new slide is inserted right after the slide(s) that section fills (e.g. `## extra:` placed after `## Features` → inserted after slide 5).

### Agent workflow when user requests extra slides

1. Read the content markdown; locate every `## extra: <title>` block and its preceding known section.
2. For each block, **pick a layout** that fits the content shape (same heuristic as `tkm:generate-slide` → `references/layouts.md`) and produce structured content for that layout via AI. Vary layouts across slides.
3. Write a JSON file `/tmp/extra_slides_{project_id}.json` — a list of slide entries:
   ```json
   [
     {
       "layout": "numbered_points",
       "title": "Migration Strategy",
       "anchor_section": "features",
       "points": [
         {"header": "Data export", "body": "Export legacy data to staging."},
         {"header": "Dual-write", "body": "Write to both systems."},
         {"header": "Cutover", "body": "Switch traffic over."}
       ]
     }
   ]
   ```
   - `anchor_section` ∈ keys of `SECTION_TO_SLIDES` in `scripts/lib/templates/svn.py`. Or pin with `"anchor_slide": <int>`.
4. Invoke gen-slide with the extra slides:
   ```bash
   $VENV_PYTHON $SKILL_DIR/scripts/gen-slide.py \
     --input outputs/project_content_{id}.md \
     --extra-slides /tmp/extra_slides_{id}.json \
     --output-dir outputs/
   ```

### Supported layouts (`layout` field + per-layout content keys)

Implemented in `scripts/lib/extra_slide_layouts.py`. Every entry takes an optional `title`.

| `layout` | Content key | Shape it fits |
|----------|-------------|---------------|
| `bullets` *(default)* | `bullets: [str]` | simple list, fallback |
| `numbered_points` | `points: [{header, body}]` (3–5) | sequential/enumerated points |
| `card_grid` | `items: [{title, body, icon?}]` (≤4) | 4 parallel concepts |
| `comparison_2` | `columns: [{title, items:[str]}, {title, items:[str]}]` | two things compared |
| `process_flow` | `steps: [str]` (3–5) | sequential steps |
| `hero` | `message: str` | one big takeaway |

### Notes
- Layouts use the Sun* palette (Sun Red `FF2200`, gold, greys) + Noto Sans JP, auto-scaled from the generate-slide 13.333″ canvas to the SVN 10″ canvas.
- Extra slides are created from a **content slide's layout**, so they inherit the deck's background + master footer / page number / logo. The layout content is drawn directly on top (no white overlay), so the template shows through.
- Overflow handling from main rendering (e.g. table splits in slides 23-25) is accounted for — anchor positions adjust automatically.
- Multiple extras with the same anchor are inserted in the order they appear in the JSON.
- To add a new layout: add a renderer fn in `extra_slide_layouts.py` and register it in `_LAYOUTS`.

---

## Common Rules

- Read `project_id` from `.clio.yml` first, fallback to `.estimate.yml`; ask user if missing
- All KG queries run **SEQUENTIALLY** (not parallel)
- Use `clio_query` MCP tool for all KG queries
- **KG queries MUST use the exact Japanese text defined in each reference file** — do NOT write your own queries, do NOT translate to English. The KG is built from Japanese documents; English queries always return empty results.
- If a query returns empty/unclear, run one broader follow-up; if still unknown, omit that field
- All outputs saved to `outputs/` in CWD (or `SLIDE_GENERATOR__OUTPUTS_PATH` env var)
- **No fabrication** — only include data from KG
- **PNG images only** — generate PNG files via Mermaid CLI; reference them as file paths in the profile (no base64)

---

## Output Files

| File | Step | Description |
|------|------|-------------|
| `outputs/project_content_{id}.md` | A, B | Domain-organized profile; uploaded to Clio as `SLIDE_CONTENT` in Step B via `clio_get_assets_upload_url` |
| `outputs/screen_flow_{id}_{ts}.png` | A, B | Screen transition diagram (Mermaid); uploaded to Clio in Step B; regenerated if flow data changed |
| `outputs/schedule_{id}_{ts}.png` | A, B | Gantt chart (Mermaid); uploaded to Clio in Step B; regenerated if schedule data changed |
| `outputs/proposal_{id}_{ts}.pptx` | B | Final PPTX; uploaded to Clio as `SLIDE_PROPOSAL` via `clio_get_artifacts_upload_url` |

---

## Slide Coverage

The SVN Proposal template (`SVN Proposal Menu.pptx`, 72 slides) is a **slide pool, not a fixed skeleton** — it fills 17 content slides, but the *output* deck is content-driven: only sections present in the profile produce slides. Cover (slide 1) and agenda (slide 2) are always kept; a chapter divider (e.g. "System Overview", "Estimated Assumptions") is kept only when its chapter has ≥1 filled slide. Empty sections produce no slide at all (and no orphan divider) — the old behavior of leaving a blank slide for a missing section is gone. Slide order follows the profile markdown's `## heading` order (falls back to the canonical section order below if that's unavailable). The mapping from profile section → slide(s) lives in `scripts/lib/templates/svn.py` (`SlideRoleConfig` for filling, `SECTION_TO_SLIDES` + `CHAPTER_DIVIDERS` for picking). To add a new slide, declare a new `SlideRoleConfig` plus its `SECTION_TO_SLIDES` entry (and `CHAPTER_DIVIDERS` entry if it belongs to an existing chapter) in `svn.py` — no changes to gen-md or gen-slide are needed.

| Slide | Section consumed | Layout |
|-------|------------------|--------|
| 4 | project_background | Current issues + objectives |
| 5 | features | Description + table |
| 6 | nfr_overview | Description + table |
| 8 | screen_flow | Image overlay |
| 10, 11 | business_process | Categories + before/after |
| 12, 13 | benefits[0:2], benefits[2:4] | 2 title+body each |
| 21 | approach_comparison | Table |
| 23, 24, 25 | assumptions[0:5], [5:8], [8:9] | 2-col tables (fill col 1) |
| 33 | infrastructure | Table |
| 34 | software_stack | Table |
| 35 | nfr_sections | 4 title+body pairs |
| 36 | nfr_detailed | Table |
| 43 | schedule | Text + Gantt image |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Download/upload fails with 403 or proxy error | **Never use WebFetch for presigned S3 URLs** — always use Bash tool to call `clio-api.py download` or `clio-api.py put`. WebFetch goes through a proxy that blocks `linodeobjects.com` and can't handle long presigned URLs |
| `clio_query` not found | MCP server not configured — check Setup |
| `clio_get_assets_download_url` not found | MCP server not configured — check Setup |
| `clio_get_assets_upload_url` not found | MCP server not configured — check Setup |
| `statusCode: 401` from MCP tool | `x-api-key` header missing or invalid — check MCP server config |
| `statusCode: 403` on finalize | Role lower than Editor, or API key is out of project scope |
| `statusCode: 400` on finalize | Wrong `storage_path` or `asset_type` mismatch — use exactly what `clio_get_assets_upload_url` returned |
| `clio-api.py put` HTTP error | Presigned URL expired — re-call `clio_get_assets_upload_url` to get a fresh URL |
| `download_url` expired | Presigned URLs are time-limited — re-call `clio_get_assets_download_url` to get a fresh URL |
| No `.clio.yml` | Create in project root with `project_id` |
| Mermaid PNG fails | Install Node.js and `@mermaid-js/mermaid-cli` |
| `Template not found` | Verify `SVN Proposal Menu.pptx` in `claude/skills/clio-generate/templates/` |
| gen-slide skips slides | Missing profile sections produce empty/cleared shapes — check JSON in Step A |
| `requests` not installed | Run `pip install -r claude/skills/clio-generate/scripts/requirements.txt` |
| `No module named 'pptx'` / `No module named pip` / `No module named ensurepip` (Claude Desktop sandbox) | gen-slide.py **self-bootstraps** deps via `scripts/ensure_deps.py` into a writable temp dir — and when the sandbox python ships without pip **and** ensurepip, it auto-downloads `get-pip.py` into that dir first. Just run `python3 gen-slide.py …`. **Do NOT** bootstrap pip manually across separate bash calls (sandbox `/tmp` is wiped between calls) — the script does it all in one process. Override install dir with `CLIO_PKG_DIR` if needed. |

---

## References

| Topic | File |
|-------|------|
| Profile schema (dataclass tree) | `scripts/lib/profile_schema.py` |
| Slide → profile section mapping | `scripts/lib/templates/svn.py` |
| S3 PUT + download helper (2 subcommands: put, download) | `scripts/clio-api.py` |
| QA slide selection (auto-routed + OfficeCLI issue hotspots, capped) | `scripts/collect-qa-slides.py` |
| Overview sections (background, features, NFR overview) | `references/generate-content-overview.md` |
| Flow sections (screen flow, business process) | `references/generate-content-flow.md` |
| Benefits | `references/generate-content-benefits.md` |
| Approach + assumptions | `references/generate-content-approach.md` |
| Technical (infra, software, NFR detail, schedule) | `references/generate-content-technical.md` |
| Step B execution detail | `references/generate-pptx.md` |
| MCP config snippet | `data/mcp-config-snippet.json` |
