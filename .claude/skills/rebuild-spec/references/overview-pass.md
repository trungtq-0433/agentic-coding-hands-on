<!-- layout-exempt: rebuild-spec reference doc — all docs/system and docs/features paths here are this skill's own input targets -->
# Overview Pass (`--overview`) — Client-Facing System Overview

Standalone `--overview` pass of `/tkm:rebuild-spec` (dispatched from SKILL.md when the flag is set). It
synthesises a single, **client-facing System Overview** (overview → detail) from the
already-promoted `docs/` spec set and emits **two deliverables**, both named
`<ProjectName>_System_Overview`:

- `docs/<ProjectName>_System_Overview.md` — the living Markdown source
- `docs/<ProjectName>_System_Overview.docx` — a polished Word deliverable (Arial, navy heading palette,
  bordered tables with shaded header, cover page, per-section page breaks, page-numbered footer)

This is a **presentation/synthesis** pass — it never reads source code or regenerates artifacts;
it re-shapes existing `docs/` content into a stakeholder document. Language: **English, always
client-ified** (system tokens replaced with business terminology).

**`<ProjectName>` resolution (do this first):** read the `**Project**:` field from
`docs/system/overview.md`; if absent, fall back to the repository root directory's base name.
Sanitise to a filesystem-safe token (keep `[A-Za-z0-9._-]`, replace spaces/other with `_`).
Example: `**Project**: BeSelf` → files `docs/BeSelf_System_Overview.md` + `docs/BeSelf_System_Overview.docx`.
The document title (H1) and running header use **`<ProjectName> — System Overview`**.

## Invocation

```
/tkm:rebuild-spec --overview
```

## Preflight (ABORT if unmet)

Prerequisite chain (single source of truth: SKILL.md § Pass ordering). `--overview` requires the
**core pass** to have promoted at minimum:

- `docs/system/overview.md`, `docs/system/architecture.md`, `docs/system/permissions.md`, `docs/system/business-rules.md`
- `docs/generated/feature-list.md`, `screen-list.md`, `screen-flow.md`, `entities.md`, `permissions-matrix.md`, `api-map.md`

ABORT if `docs/generated/feature-list.md` is missing:
`"ABORT — docs/generated/feature-list.md missing. Run /tkm:rebuild-spec (core pass) first, then re-run --overview."`

**Optional enrichment (used if present, skipped if absent):**
`docs/features/*/{technical-spec,business-context,screens,edge-cases}.md` (§5 detail, §11 open issues),
`docs/flows/*.md` (§4 lifecycle), `docs/system/glossary.md` (terminology). The pass degrades
gracefully — sections sourced from an absent pass note "not yet generated".

## Document Structure (canonical 11 sections + screen list)

| # | Section | Sourced from |
|---|---------|--------------|
| 1 | System Overview | `docs/system/overview.md` |
| 2 | Purpose & Business Value | overview + business-rules (As-Is/To-Be merged → purpose; no "old-system" narrative) |
| 3 | Actors & Roles | `docs/system/permissions.md`, `permissions-matrix.md` |
| 4 | Business Flows & Lifecycle | `docs/flows/*` + `screen-flow.md` (step tables + status legends) |
| 5 | Detailed Function List | `feature-list.md` + `docs/features/*` — **tables grouped by role** (Common / Viewer / Creator & Admin / Background) |
| 6 | Screen List | `docs/generated/screen-list.md` (table: Screen · Route · Type) |
| 7 | External Integrations | `architecture.md`, `api-map.md` |
| 8 | Configuration & Optional Features | `permissions-matrix.md` (gates), `entities.md` (discriminators) |
| 9 | Technical Architecture & Infrastructure | `architecture.md`, `overview.md` (product-level only) |
| 10 | Data Model (Summary) | `entities.md` (business grouping, not DB jargon) |
| 11 | Open Questions & Known Issues | `## Unresolved Questions` across `docs/features/*` + review reports |

The document title (H1) is **`<ProjectName> — System Overview`**. A title-metadata block (Client / System / Version / Date / Prepared by) precedes §1, followed by a Table of Contents.

## Waves

### OV.1 — Section synthesis (fan-out)
Spawn `doc-writer` agents (≈4, one per section cluster) to draft each section **grounded in the
`docs/` sources above** — no invented content. Clusters that bound context well:
- A: §5 Function List + §6 Screen List
- B: §2 Purpose + §4 Flows
- C: §7 Integrations + §8 Config + §9 Tech + §10 Data Model
- D: §11 Open Questions (aggregate feature-spec Unresolved Questions)

Each agent returns its section markdown (it does not write the shared file). Orchestrator assembles
§1 + §3 (small, write directly) + the returned sections into `docs/<ProjectName>_System_Overview.md`.

### OV.2 — Client-ify (business terminology + consistency)
Rewrite the assembled document replacing **all** system/technical identifiers with business terms,
applied consistently across every section. The mapping is **derived per project** from THIS
project's own `docs/generated/entities.md` (column / enum / discriminator names), `route-list.md`
(endpoints), and `docs/system/glossary.md` (if present) — **never** from a hardcoded vocabulary.

**Transformation rules (project-agnostic — apply to whatever tokens THIS project has):**

| System token class | Client-ify action |
|---|---|
| status / state enum values (e.g. a `before_edit`-style workflow state) | Title-Case business label ("Draft", "Pending Approval", "Published") |
| model columns / boolean flags (snake_case: `*_enable`, `*_at`, `allow_*`, `has_*`) | descriptive business term ("Restricted Access", "Publication Start Date") |
| scopes / methods / worker & service class names / hooks | plain-English description of the behaviour |
| `F### / SCR### / BL### / PERM### / MODEL-### / DISC-###`, enum integers `(0)` | **removed** — refer by feature/screen name |
| library/gem/package names, `file:line` citations, table prefixes, soft-delete jargon (`deleted_at`) | removed; §9 product-level only; §10 "deletion preserves history for audit" |

**§9** → product/platform level only: name the user-visible stack (language · framework · database ·
cloud · client), no internal libraries. **Entity domain names** (the business nouns in `entities.md`)
are KEPT and described plainly — they are the product's vocabulary, not system tokens.

> _Illustrative example (from a dashboard-platform project — DO NOT copy literally; derive your own
> from this project's `entities.md`):_ `app_type` → "Application Type"; `dashboard_type` → "Content
> Category"; `control_access_enable` → "Restricted Access".

The deterministic gate (OV.3a, `verify_overview.py`) enforces the snake_case / ID-code / file:line
classes **generically**, so any leaked system token fails the build regardless of project domain.

### OV.3 — Verify (consistency + no leftover tokens)
Two checks, both must pass before OV.4:

**(a) Deterministic token-leak gate (HARD, run first):**
```
python3 <skill-dir>/extensions/scripts/verify_overview.py docs/<ProjectName>_System_Overview.md
# <skill-dir> = project-local .claude/skills/rebuild-spec OR global ~/.claude/skills/rebuild-spec
```
Exit 0 = token-clean; exit 2 = leaks printed (line + token). The script greps **generic, project-
agnostic** classes — any lowercase `snake_case` identifier (subsumes all column/flag/enum/scope/
method names on any stack), `F###`/`SCR###`/`BL###`/`PERM###`, `MODEL-###`/`DISC-###`, and
`file:line` citations across mobile + backend + web extensions (incl. `.kt`/`.swift`). No hardcoded
per-project vocabulary. Fix every leak and re-run until exit 0 — do NOT proceed on a non-zero exit.

**(b) Reviewer cross-check (catches what regex can't):** Spawn one `reviewer` to verify the
assembled `docs/<ProjectName>_System_Overview.md` against the `docs/` sources: every factual
claim matches source; status labels / role names / counts are identical across sections (no
conflicts); ambiguous business-word tokens the grep skips on purpose (`editing` / `published`
used as raw enums, enum integers like `(0)`) are caught here. Fix any finding before OV.4.

Gate: proceed only when (a) exits 0 AND (b) is consistent.

### OV.4 — Build deliverables
1. Markdown is final at `docs/<ProjectName>_System_Overview.md`.
2. Build the styled Word deliverable with the bundled self-contained builder:
   ```
   python3 <skill-dir>/extensions/scripts/build_overview_docx.py \
     docs/<ProjectName>_System_Overview.md docs/<ProjectName>_System_Overview.docx \
     --header "<ProjectName> — System Overview"
   # <skill-dir> = the resolved rebuild-spec dir:
   #   project-local  .claude/skills/rebuild-spec   OR   global  ~/.claude/skills/rebuild-spec
   # any python3 works (script is stdlib + pandoc only — no project venv required)
   ```
   The script (pandoc + stdlib only; no reference template) applies: Arial default font;
   Title/Heading colours (navy `#1A365D` / `#2C5282` / `#1F4D78`); bordered tables with a navy
   shaded header row + light zebra banding; cover page (title + metadata) with each section on a
   **new page** (Heading2 `pageBreakBefore`); a blank line before/after every table; a centred
   **"Page N"** footer and a right-aligned running header.
3. Two hard gates are **built into the script**: (a) **round-trip** — reopens the .docx via pandoc,
   exits 2 if invalid OOXML (a broken file can't pass silently); (b) **style-presence** — asserts the
   styling actually landed (Arial, navy palette, bordered Table style, per-section page breaks,
   header + footer parts), exits 2 if a pandoc-version XML-shape change made the style patches
   silently no-op (a valid-but-unstyled doc can't pass either). No separate manual step needed.

## Outputs
- `docs/<ProjectName>_System_Overview.md` (Markdown source — living document)
- `docs/<ProjectName>_System_Overview.docx` (Word deliverable)

## Idempotency & Edge Cases
- Re-running regenerates both files from current `docs/`. Safe to run after any spec refresh.
- `pandoc` not on PATH → OV.4 builder aborts with a clear message; the Markdown still exists.
- Optional sources absent → affected sections note "not yet generated"; pass still completes.
- This pass writes only to `docs/<ProjectName>_System_Overview.md` + `docs/<ProjectName>_System_Overview.docx`; it never
  modifies the core/feature/flow/glossary artifacts.

## Completion handoff
```
─── overview pass complete ───
Promoted: docs/<ProjectName>_System_Overview.md + docs/<ProjectName>_System_Overview.docx
Review (optional): open the .docx; confirm pagination, table styling, and business wording.
Re-run: /tkm:rebuild-spec --overview  (after any docs/ refresh)
```
