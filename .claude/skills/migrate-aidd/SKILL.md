---
name: tkm:migrate-aidd
description: "Migrate projects already running AIDD via GitHub Spec-Kit/SDD into the Takumi canonical spec set. Reads OLD specs first as primary evidence, consults source code only to fill gaps. Sibling of tkm:rebuild-spec but spec-driven. Activate when the user has a Speckit/SDD spec folder (specs/, .specify/) and wants Takumi-canonical specs in docs/features/ + docs/system/."  # layout-exempt: skill description; mode-aware pointer in Preflight step 4
argument-hint: "<spec-folder>"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: planning-architecture
triggers: ["migrate spec-kit", "SDD migration", "AIDD", "import specs", "spec-driven", "migrate to takumi"]
---

# tkm:migrate-aidd

<!-- layout-exempt: output layout overview; mode-aware pointer in Preflight step 4 -->
Migrate a Spec-Kit/SDD project's existing specs into the 9 Takumi canonical
artifacts + per-feature F### specs. Output lands in `docs/system/`,
`docs/generated/`, `docs/flows/`, and `docs/features/{slug}/` (v4 layout).

SIBLING of `tkm:rebuild-spec`, but **spec-driven**: old specs are primary
evidence; source code is consulted ONLY to fill gaps. This is a THIN skill — it
owns `SKILL.md`, three references, and three scripts; everything else
(templates, validators, reviewers, promote logic, the wave graph) is REUSED from
rebuild-spec **by path**.

**Principles:** YAGNI, KISS, DRY | Specs-first, code-as-fallback | Reuse rebuild-spec in place | Template-first | Zero third-party deps (stdlib python only).

## Usage

<!-- layout-exempt: usage example — output dirs are definitional targets; mode-aware pointer in Preflight step 4 -->
```
/tkm:migrate-aidd <spec-folder>     # full migration of a Speckit/SDD spec folder → docs/system/ + docs/generated/ + docs/flows/ + docs/features/
```

`<spec-folder>` is relative to the repo root (e.g. `specs/`, `docs/specs/`).
Incremental re-migration is **DEFERRED to v2** — v1 is full migration only.

## Preflight

1. Project root = CWD (must be under git).
2. **Detect + locate specs** — reuse `detect_sdd.py` AS-IS:
   ```
   .claude/skills/.venv/bin/python3 claude/skills/propose-improvements/scripts/detect_sdd.py \
     --spec-folder <spec-folder> --repo-root . \
     --output-path plans/<active>/artifacts/sdd-detection.json
   ```
   Require `isSDD:true` AND non-empty `specsRoot` in the verdict JSON. `Status: BLOCKED` → ABORT with the script's reason (do not write anything).
3. Resolve active plan from `## Plan Context`; fallback `plans/<timestamp>-migrate-aidd/`.
<!-- layout-exempt: output dir setup + collision guard — paths are operational targets for this skill; mode signal in step 4 pointer above -->
4. Ensure output dirs. **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). In single-lang mode (the common case) the paths below are correct as-is. Output dirs: `docs/system/`, `docs/generated/`, `docs/flows/`,
   `docs/features/`, `plans/<active>/artifacts/`.
5. **Output-collision guard** — if `docs/features/` already exists OR
   `docs/system/overview.md` already exists, STOP and prompt the user via
   `AskUserQuestion`: **abort** / **overwrite** / **separate dir**
   (`docs-migrated/`). Note: `promote_drafts.py` archives only review
   reports — existing files under `docs/system/`, `docs/generated/`, `docs/flows/`,
   and `docs/features/` are REPLACED on overwrite, so confirm before clobbering.
   Never overwrite silently.

## Pipeline

migrate-aidd = rebuild-spec with **Wave 0 + Wave 1 evidence source swapped**.
Waves 1.5–9.5 (gates, reviewers, fix cycles, promote) are reused VERBATIM — see
`claude/skills/rebuild-spec/references/pipeline.md` for the wave graph and
`TaskCreate`/`blockedBy` patterns. Do NOT re-describe reused waves.

Load on demand (not inlined): `references/source-target-mapping.md`,
`references/spec-parse-strategy.md`, `references/citation-mode.md`.

### Wave 0' — read old specs (replaces scan-codebase + build_session_context)
Run, in order, with `.claude/skills/.venv/bin/python3`:
```
# 1. detection (preflight step 2 above) → sdd-detection.json {specsRoot}
# 2. parse speckit specs → spec-summary.md + _speckit-index.json
claude/skills/migrate-aidd/scripts/parse_speckit_specs.py \
  --spec-folder <spec-folder> --plan-dir plans/<active> \
  --detection-json plans/<active>/artifacts/sdd-detection.json
# 3. emit _session-context.md (SAME schema as rebuild-spec → W2–W9 run unchanged)
claude/skills/migrate-aidd/scripts/build_migrate_session_context.py \
  --plan-dir plans/<active> \
  --spec-summary plans/<active>/artifacts/spec-summary.md \
  --stack-note "<stack note>"
```
BL inventory: if `spec-summary.md` surfaces a BehaviorLogic-like section, extract
it to `_scout-bl-inventory.md` via
`claude/skills/rebuild-spec/scripts/extract_scout_section.py`; else write
`_scout-bl-inventory.md` containing `<!-- NO BL SOURCE IN SPECS — code-scan in W2 fallback -->`.

<!-- layout-exempt: contracts carry-over — paths are operational targets for this skill's promote step -->
**Contracts carry-over (P04):** for each feature where `_speckit-index.json` records
`has_contracts: true`, the W0' researcher MUST:
1. Copy the contracts dir verbatim to `plans/<active>/artifacts/features/{slug}/contracts/`
   (atomic, path-guarded; stdlib `shutil.copytree` or equivalent — do NOT parse contract content).
   `promote_drafts.py` will auto-promote the entire `artifacts/features/{slug}/` tree
   (including `contracts/`) to `docs/features/{slug}/contracts/` — no promote change needed.
2. In that feature's `technical-spec.md` draft (§ "External Integrations", or at the top if
   the section is absent), add a link line:
   `- [OpenAPI contract](contracts/<filename>) [FROM_SPEC: contracts/<filename>]`
   (replace `<filename>` with the actual file name, e.g. `openapi.yaml`).
3. Add an Unresolved Question to the same `technical-spec.md`:
   `- [ ] Verify contract matches real routes — speckit contracts are aspirational
     (a declared route may have no handler). Cross-check against code route-list.`

### Wave 1' — spec→artifact researchers
Reuse rebuild-spec `researcher` agent; only the PROMPT changes (primary evidence =
spec files; code only for the enumerated gap; cite spec-URI or `[FROM_CODE]`).
Evidence routing:

| Artifact | Wave | Primary spec source | Code fallback |
|---|---|---|---|
| system-overview | W1' | `*/plan.md` + constitution | always supplement (README/structure) |
| architecture (Design Rationale) | W1' | `*/research.md` | code: confirm the decision was actually built |
| route-list | W1' | `*/contracts/` | always-on grep when sparse/absent |
| data-model | W1' | `*/data-model.md` (merged) | field types if missing |
| user-stories | W4 | `*/spec.md` user stories | none (pure spec) |
| feature-list | W5 | `*/spec.md` FRs + plan/tasks | none |

Per-artifact contract (paths, templates, grep patterns, merge rule) =
`references/spec-parse-strategy.md` + `references/source-target-mapping.md`.

<!-- layout-exempt: architecture rationale — docs/system/ path is the output target of this skill, not a consumer assumption -->
**research.md → architecture rationale (P05):** when the W1' system-overview/architecture
researcher runs, it MUST also process all `*/research.md` files surfaced in `_speckit-index.json`
(`has_research: true`). For each research.md:
1. Extract design decisions (why X chosen, alternatives rejected, best practices) and write them
   into `docs/system/architecture.md` under a **"## Design Decisions / Rationale"** section.
   Each decision entry cites the source as `spec://NNN-feature/research.md#Section-Heading`
   (use the H2 anchors from `research_sections` in the index — e.g.
   `spec://002-add-auth/research.md#Authentication-Strategy`).
2. **Drift detection:** cross-check each research decision against the code-scan facts
   (route-list, permissions, data-model). Where code **contradicts** a research decision
   (e.g. research states PKCE flow required but no PKCE handler found in route-list), tag that
   entry `[SPEC_VS_CODE_DRIFT]` and add it to the **related feature's** Unresolved Questions:
   `- [ ] [SPEC_VS_CODE_DRIFT] <decision> — research.md prescribes <X> but code scan found no evidence.`
3. If `research.md` is absent for a feature, skip gracefully — do NOT fabricate decisions.
   If code-scan facts are incomplete at W1', emit plain rationale entry + a softer
   `- [ ] Verify <decision> is implemented in code (code-scan incomplete at migration time).`

### Wave 2 / 2b / 3 — code-scan fallback (screen-list, screen-flow, behavior-logic, permissions)
Speckit has NO source for these → reuse rebuild-spec W2/W3 + `/tkm:scan-codebase`,
**scoped** by route-list + data-model entities (fall back to full scan if scoping
unresolvable). Specs-only repo → best-effort `[INFERRED]` inference from spec
hints (each cites a spec section); no hint → "No data" marker. See
`references/spec-parse-strategy.md` § code-scan fallback. Preserve the
`blockedBy` chain W2(SL+SF) → W2b(BL) → W3(Perm).

### Waves 1.5 – 9.5 — reused from rebuild-spec (unchanged)
- W1.5 DataModel gate, W4.5 UserStories gate, W5.5 existence validator, W5.6
  FeatureList gate — schema/artifact-only, source-agnostic. AS-IS.
- W5 → `_canonical-fcodes.json` + per-feature `.pending` markers. AS-IS.
- W6 FeatureSpec fan-out (batches of 5 if >20 F###) — source-agnostic. AS-IS.
  Per-feature output is the **4-file v4 set**:
  `artifacts/features/{slug}/technical-spec.md`, `business-context.md`,
  `screens.md`, `edge-cases.md`.
  F### ↔ NNN reconciliation per `source-target-mapping.md` (orphan-source =
  critical, orphan-feature = warn).
- W6.5 validators: `validate_feature_spec.py` AS-IS; `validate_source_citations.py`
  invoked with the **full** spec-driven invocation — `--specs-root` is REQUIRED or
  every specsRoot-relative citation fails as `citation.file_missing` (critical, blocks promote):
  ```
  claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/validate_source_citations.py \
    --plan-dir plans/<active> --project-root . \
    --mode spec-driven --specs-root <specsRoot> \
    --summary-out plans/<active>/artifacts/validation/validation-summary.json
  ```
  (spec-URI / specsRoot grammar: `references/citation-mode.md`.)
<!-- layout-exempt: W9 promote targets — output dirs are this skill's own promote targets -->
- W7a (9 core) ∥ W6; W7b feature batches; W7-merge; W7.5 structural_fixer; W8 fix
  cycles (≤3); W9 `promote_drafts.py` → `docs/system/`, `docs/generated/`,
  `docs/flows/`, `docs/features/{slug}/`; W9.5 `build_source_to_fcode.py`
  seeded with speckit folder names. ALL AS-IS.

## Subagent contracts

| Wave | Subagent | Evidence source | Output |
|---|---|---|---|
| W0' | (scripts) | `<spec-folder>` speckit artifacts | spec-summary.md, _speckit-index.json, _session-context.md |
| W1'/W4/W5 | `researcher` | spec files (primary) + code grep (gap only) + rebuild-spec template + code-formats.md | `<artifact>.md` |
| W2/W2b/W3 | `researcher` | code scan (scoped) / spec-hint inference (specs-only) | screen/flow/BL/permissions .md |
| W6 | `researcher` | scoped FeatureList/UserStories + 4 v4 feature templates | `features/{slug}/technical-spec.md`, `business-context.md`, `screens.md`, `edge-cases.md` |
| W7a/W7b | `reviewer` | canonical artifacts + 5 split verification-checklist files | review-report.md |
| W8 | `implementer` | review issues grouped by file | fixed artifacts |
| W9 | `doc-writer` | promoted drafts | `docs/system/`, `docs/generated/`, `docs/flows/`, `docs/features/{slug}/` + wave9 flag |  <!-- layout-exempt: subagent table — W9 output dirs are this skill's targets -->

All subagents read `_session-context.md` FIRST. Rows not shown above are
identical to rebuild-spec — see its SKILL.md / pipeline.md.

## References

Reused from rebuild-spec **by path** (no copy, no symlink):
- `claude/skills/rebuild-spec/templates/*` — all 9 core + scout + 4 v4 feature templates (`technical-spec-template.md`, `business-context-template.md`, `screens-template.md`, `edge-cases-template.md`)
- `claude/skills/rebuild-spec/references/{code-formats,verification-checklist-universal,verification-checklist-core-artifacts,verification-checklist-feature-spec,verification-checklist-screen-spec,verification-checklist-quality-gates,canonical-fcode-schema,feature-spec-researcher-contract,user-stories-ipe-protocol,composite-screen-detection,bl-source-patterns,pipeline}.md`
- `claude/skills/rebuild-spec/scripts/{extract_scout_section,validate_feature_existence,validate_feature_spec,validate_source_citations,promote_drafts,build_source_to_fcode,structural_fixer}.py`; shared libs: `_layout_lib.py`, `_slug_lib.py`, `_summary_lib.py`
- `claude/skills/propose-improvements/scripts/detect_sdd.py` — detection
- `claude/skills/_shared/docs-canonical-mapping.md` — output ownership / stub rule

Owned by this skill:
- `references/source-target-mapping.md` — mapping table, data-model merge, NNN↔F### reconciliation
- `references/spec-parse-strategy.md` — per-artifact read/fill/fallback contract
- `references/citation-mode.md` — spec-URI grammar for `--mode spec-driven`
- `scripts/{parse_speckit_specs,speckit_parse_lib,build_migrate_session_context}.py`

## Output

<!-- layout-exempt: output section — all paths are this skill's own promote targets -->
- `docs/system/{overview,permissions,glossary,business-rules,architecture}.md` — curated system narratives
  - `architecture.md` includes a **"## Design Decisions / Rationale"** section populated from `*/research.md` (P05)
- `docs/generated/{route-list,api-map,entities,screen-list,screen-flow,behavior-logic,user-stories,feature-list}.md` — raw inventories
- `docs/flows/{slug}.md` — cross-feature flow docs
- `docs/features/{slug}/{technical-spec,business-context,screens,edge-cases}.md` — 4-file per-feature set
- `docs/features/{slug}/contracts/` — verbatim copy of speckit `contracts/` dir when present (P04)
(same canonical home as rebuild-spec v4; promote + stub rules reused.)

## v2 (deferred — do NOT build)

Incremental re-migration (diff changed source specs), speckit version-detection,
`contracts/` auto-diff (copy-as-is shipped in v1), non-speckit SDD formats.
