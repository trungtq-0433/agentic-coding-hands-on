<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Artifact Sharding — Chunked Research + Single-File Merge

Loaded on-demand when a pre-gen estimate exceeds threshold. Single source of truth for descriptor table, merge recipe, fragment contract, and slicing rules.

## Pre-gen Estimate (the ONLY oversize safety)

Before creating any artifact's research task, the orchestrator runs `estimate_artifact_loc.py`. Over threshold → dispatch the chunked path; else single task. This is the ONLY oversize mechanism — no post-merge size check exists (YAGNI).

```
.claude/skills/.venv/bin/python3 \
  claude/skills/rebuild-spec/scripts/estimate_artifact_loc.py \
  --artifact <name> \
  --route-list <path> \
  --scout-report <path> \
  --plan-dir <path> \
  --max-loc <int>   # orchestrator passes injected docs.maxLoc; default 800
```

The estimator NEVER reads tkm-config or calls `tkm-config-utils.cjs`. `--max-loc` arrives from the orchestrator's injected `docs.maxLoc` hook context.

## Descriptor Table

| Artifact | Unit | Count source (pre-gen) | avg_lpu | Threshold | Slice key | Det. validator |
|---|---|---|---|---|---|---|
| api-contracts | endpoint | route-list.md data rows | 16 | est_loc>800 (~50 endpoints) | resource namespace | `validate_api_contracts.py` |
| data-model/entities | MODEL###/entity files | scout File Inventory `model` count → data-model.md MODEL### on rerun | 30 | **≥40 models (fixed)** | module/domain | W1.5 gate |
| user-stories | US### | own US### → feature-list F###×3 → screen-list SCR###×1.5 (first-gen) | 33 | est_loc>800 (~24 US) | actor | W4.5 gate |
| **feature-list** | **F###** | **own F### → user-stories US###÷2** | **42** | **est_loc>800 (~19 F###)** | **expand by F### batch (grouping done ONCE in shell)** | W5.6 gate |
| screen-list | SCR### | scout File Inventory `screen` count → screen-list.md SCR### on rerun | 19 | est_loc>800 (~42 screens) | module/route group | `validate_screen_list.py` |
| behavior-logic | BL### | scout `## Background Logic Source Inventory` entries (1:1 w/ BL) | 25 | est_loc>800 (~32 BL) | category/domain | `validate_behavior_logic.py` |
| route-list | route row | route-list.md data rows → scout `route` files×12 (first-gen) | **2** | est_loc>800 (~400 routes) | resource / top-level path prefix | `validate_route_list.py` |
| api-map | endpoint | route-list.md data rows (W1 complete) | **3** | est_loc>800 (~267 endpoints) | resource namespace | `validate_api_map.py` |
| screen-flow | SCR### | scout File Inventory `screen` count (= screen-list) | **10** | est_loc>800 (~80 screens) | module/route group | `validate_screen_flow.py` |
| crud-matrix | table×feature row | `_digest_extract_data_flow.json` distinct tables (Wave 0.6) | 4 | est_loc>800 (~200 rows) | **F### range (RT-DOC-b — NOT domain; Cross-Module built post-merge)** | `validate_crud_matrix.py` |
| db-objects | db object | `_digest_extract_sql_schema.json` db_objects (Wave 0.6) | 6 | est_loc>800 (~133 objects) | object kind/schema | `validate_db_catalog.py` |
| job-list | JOB### | behavior-logic.md BL### entries filtered to job types (v26.1.0) | — | single (not wired to `estimate_artifact_loc.py` in v1 — research shows job counts stay well under threshold; see `references/pipeline-jobs.md` § Wave J.1) | — (file-global, no slice key) | `validate_job_list.py` |
| test-cases | TC### | BR/SM/DEC/DISC codes per feature's technical-spec.md + edge-cases.md rows (v26.1.0) | — | single per feature (one small file per F### — not wired to `estimate_artifact_loc.py`; each feature's own file is individually small by construction, see `references/pipeline-test-cases.md` § Wave TC.1) | — (per-feature reset, no slice key) | `validate_test_cases.py` |
| design-intent | — (no ID scheme; narrative section) | single-file synthesis — no scout inventory count (v26.1.0 B5, EXPERIMENTAL/report-only) | — | single (no post-merge check, like permissions-matrix/business-rules) | — (no slice key) | `validate_design_intent_density.py` (mode-agnostic citation-density gate, F11c — NOT a shard/ID gate) |
| permissions-matrix / permissions / business-rules / system/* / future | — (no unit) | source-file count (crude) or default single | — | single (no post-merge check) | — | — |

Calibration (verified from sun-news generated files): feature-list 1287L/31 F###→lpu 42; route-list 395L/259 rows→lpu 2; api-map 536L/259 endpoints→lpu 3; screen-flow 627L/67 SCR###→lpu 10.

**First-gen signal & its limit:** the artifact's own output file rarely exists at its first dispatch, so the count comes from the scout report's typed `## File Inventory` (`path<TAB>type`) or an already-generated upstream artifact. These are **file-count** signals — a single monolithic route file (hundreds of routes) or a Mode-A model file (Django `models.py` with many classes) is ONE inventory entry and may under-count at first-gen. The incremental rerun path (own output file present) self-corrects; first-gen monolithic-file projects are the residual blind spot. There is no post-merge size backstop, so this is a known edge, not a caught one.

## Reusable Merge Recipe

Identical shape to FS.1.5 (`sort → join → replace placeholder → rm -rf`). Generalized by per-kind/per-slice anchors and `_slice-plan.json` grouping.

**Ordinal rule (REQUIRED):** fragment filenames MUST be zero-padded to 2 digits (`01-…`, `02-…`; 3 digits if >99 slices). The shell researcher writes the same zero-padded ordinals into `_slice-plan.json`. The merge sorts **numerically by ordinal**, never by raw `ls|sort` — lexicographic `ls` orders `10-` before `2-`, which would land fragment bodies under the wrong anchors with >9 slices.

**Completeness rule (REQUIRED):** each `_slice-plan.json` entry carries `expected_count` (rows/blocks the slice should yield). At merge, compare the fragment's actual entry count to `expected_count`; a short/truncated fragment (e.g. a researcher that timed out mid-write) is re-dispatched, NOT merged. This is the only guard against a silently truncated fragment — there is no post-merge size check.

```
FRAG_DIR=plans/<active>/artifacts/_fragments/<artifact>

# 1. Shell researcher writes skeleton + anchors + _slice-plan.json
#    (each slice entry: {ordinal:"01", slice:"<key>", anchor:"<id>", expected_count:N})
# 2. Fan-out researchers write fragments: _fragments/<artifact>/NN-<slice>.md (NN zero-padded)
# 3. Merge step (orchestrator):
frags = sorted(glob("$FRAG_DIR/*.md"), key=ordinal_int)   # numeric, NOT ls|sort
for each slice in _slice-plan.json:
  frag = frags[slice.ordinal]
  if entry_count(frag) < slice.expected_count:            # truncated → do not merge
    re-dispatch slice; continue
for each anchor in the skeleton:
  joined = concat(bodies of fragments grouped under that anchor, "\n\n")
  draft = draft.replace("{POPULATED_BY_FRAGMENTS}" for that anchor, joined)
write draft
bash: rm -rf "$FRAG_DIR"
# 4. After merge + completeness check: run renumber gate then contiguity gate.
#    Exception — feature-list: integrity gate (F### vs _slice-plan.json) runs FIRST,
#    then renumber_artifact_ids.py, then validate_id_contiguity.py.
bash: .claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/renumber_artifact_ids.py \
       --artifact <name> --plan-dir <plan_dir>
bash: .claude/skills/.venv/bin/python3 claude/skills/rebuild-spec/scripts/validate_id_contiguity.py \
       --artifact <name> --plan-dir <plan_dir> \
       --summary-out <plan_dir>/artifacts/validation/validation-summary.json
# NOTE: --project-root and --map-out are optional for both scripts (auto-defaulted).
# Pipeline wave blocks omit them — the defaults match expected paths.
```

## Fragment Contract

Fragments contain **body content only** — no `##` section headers, no preamble, no shared sections. The shell researcher owns all structural elements (headers, preamble, shared sections like `## Conventions`). Fragments contribute entries/blocks under their assigned anchor.

- api-contracts: `### entry` blocks only (no `## kind` headers, no `## Conventions`). Reference shared types by name, never re-list fields (avoids `shared_type_redefined`).
- data-model: entity `### MODEL###` blocks only within assigned MODEL### range.
- user-stories: `## US###` blocks only within assigned US### range.
- feature-list: `### F###` detail blocks only for assigned disjoint F### batch (F### already assigned by shell grouping — researcher does NOT invent F### codes).
- screen-list: `## SCR###` blocks only per route group. SCR+child REGs always co-located.
- behavior-logic: `## BL###` blocks only per category. 1-BL-per-inventory-entry preserved.
- route-list: table-body rows only (no header row, no preamble).
- api-map: endpoint→handler table rows only per resource namespace.
- screen-flow: `### SCR###` transition blocks only per module.

## Batching

Fan-out researchers run in batches capped at `REBUILD_SHARD_MAX_PARALLEL` (default 5), **dispatched sequentially — batch i+1 starts only after ALL of batch i completes** (chain every task of batch i+1 on all task ids of batch i via `addBlockedBy`, never on just the last one — blocking on the last task alone lets the two batches overlap). Shard researchers count toward the global 5-agent cap (SKILL.md § GLOBAL PARALLEL CAP): when other wave tasks are in flight, shrink the batch so total concurrent subagents stay ≤ 5. Mirrors `REBUILD_FS_BATCH_SIZE` / `REBUILD_W8_MAX_PARALLEL` conventions.

## US### Range Pre-allocation Algorithm

1. Actors = distinct roles from the `| Role | Allow | Conditions |` Permission Rules tables in permissions-matrix.md (NOT the `## PERM###:` headings), stable-sorted by name.
2. Per actor, estimate US count = `round(actor_screen_or_perm_count × factor)`; floor 1.
3. Pad each actor's range by +20% headroom → ranges still disjoint. Tail gaps are TEMPORARY — the post-merge renumber gate (`renumber_artifact_ids.py`) compacts US### to contiguous 001..N before W4.5; W4.5 still uniqueness-only, contiguity enforced by `validate_id_contiguity.py`.
4. Assign contiguous blocks: actor[i].start = actor[i-1].end + 1.
5. Researcher contract: "Use ONLY US### in [start,end]; if exceeded, STOP and report."
6. Determinism: ranges computed by `estimate_artifact_loc.py --emit-ranges` (testable).

## Feature-list — Grouping-once + Expand-many (UNIQUE shape)

Feature-list differs from every other artifact: F### is a DERIVED GLOBAL clustering of many source units (US###/SCR###/routes/models/BL###), not a 1:1 map. The W5.6 gate checks GLOBAL properties (coverage, non-overlap, coherence). Independent per-domain clustering would hide cross-chunk scope-overlap.

- **Shell step = GROUPING ONCE (global, single agent):** Produce the compact `## Feature Hierarchy` table + the `F### → {member US###, SCR###, routes, models, BL###}` assignment map. F### born here, disjoint by construction. No separate range pre-allocation.
- **Fan-out = EXPAND DETAILS per F### batch:** The verbose `## Feature Details` `### F###` blocks are written by fan-out chunks, each owning a disjoint batch of already-assigned F###.
- **Merge → F### integrity gate, THEN renumber gate, THEN existing W5 post-step:** Before the canonical-fcode derivation, assert every `### F###` in the merged file appears in `_slice-plan.json`. After that gate passes: run `renumber_artifact_ids.py` (compacts F### codes to contiguous 001..N and rewrites `_slice-plan.json` keys via `rewrite_slice_plan_keys`), then run `validate_id_contiguity.py`. Only then proceed to the W5 post-step: parse `### F###` → slug derivation (using the NEW renumbered codes) → GLOBAL slug-collision check → sorted `_canonical-fcodes.json` → `.pending` folders (UNCHANGED — post-step already runs "after feature-list.md finalized"). The renumber gate therefore slots BETWEEN the F### integrity gate and the canonical-fcode post-step.

## ID Contiguity Gate

**Contract:** After every sharded artifact merge (and after any full-run renumber pass), the artifact's global ID scheme MUST be contiguous 001..N with no gaps, no duplicates, and no overflow (> 999). Per-screen REG### are contiguous within their parent SCR### but reset across screens; per-feature TC### are contiguous within their parent F### but reset across features (v26.1.0 B6 — same per-parent-reset exception class as REG###/SCR###). DISC-### gaps, REG### gaps, and TC### gaps are warnings (non-halting); all other global-scheme gaps are critical (halt).

**Owner → scheme table:**

| Artifact | ID scheme |
|---|---|
| data-model | MODEL### |
| screen-list | SCR### |
| behavior-logic | BL### |
| permissions-matrix | PERM### |
| user-stories | US### |
| feature-list | F### |
| process-flows | FLOW### |
| job-list | JOB### (file-global — single artifact, no per-dir reset; own uniqueness check lives in `validate_job_list.py`, NOT wired into `renumber_artifact_ids.py`/`validate_id_contiguity.py`'s generic `ARTIFACT_OWNS` registry in v1 — see Descriptor Table row above) |
| test-cases | TC### (per-feature reset — like `REG###` resets per `SCR###`; own uniqueness check lives in `validate_test_cases.py`, NOT wired into `renumber_artifact_ids.py`/`validate_id_contiguity.py`'s generic `ARTIFACT_OWNS` registry in v1 — see Descriptor Table row above) |

**Sibling matrix (abbreviated):** screen-list ↔ screen-flow (both own SCR###); user-stories ↔ feature-list ↔ permissions-matrix (US### cross-referenced). When renumber compacts one artifact it applies the same rename map to its registered siblings — ensure sibling files are present before running the gate.

**Incremental skip rule:** On incremental runs, `renumber_artifact_ids.py` runs only for artifacts that were re-generated in that wave (full-only predicate). `validate_id_contiguity.py` runs with `--report-only` on incremental (non-halting warning if a gap appears from a partial re-run; full-only enforces halt on gap).

**Translation interplay:** On full runs, renumber runs BEFORE the translation pass. Secondary-language mirrors regenerate from the renumbered primaries and are therefore consistent by construction. Pre-existing mirrors from a prior run may become stale (IDs shifted); they are handled by the existing translate-sync gate (re-translate, NOT map-apply — applying the rename map to translated mirrors is explicitly out of scope and deferred to the pending translation-sync-gate plan).

**KNOWN LIMITATION (F15):** On a full re-run over an existing `docs/` tree, shifting F### codes can leave orphaned `docs/features/F0NN_OldSlug/` folders. The `promote_drafts.py` step writes new-code folders but never garbage-collects old ones. Folder GC is OUT OF SCOPE — this is a pre-existing concern that renumbering amplifies. Maintainers should manually delete stale folders after any full re-run that shifts F### codes. No implementation work planned (F15 tracking only).

## Idempotent Retry / Resume

On timeout of a shardable artifact:
1. Re-run `estimate_artifact_loc.py` → if `shard:true`, retry as chunked.
2. If partial `_fragments/<artifact>/` dir exists: compare `_slice-plan.json` entries vs the present fragments. Re-dispatch a slice when its fragment is **missing OR shorter than `expected_count`** (truncated mid-write). Overwrite `NN-<slice>.md`.
3. Re-run merge (idempotent: rebuilds whole file from current fragments, no dup sections).
4. "Retry once then failed" cap per fragment; escalate after cap.

Merge always REBUILDS the whole file from the numerically-sorted current fragments — never appends. A re-merged file has no duplicate sections by construction.
