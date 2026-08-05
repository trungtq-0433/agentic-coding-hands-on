<!-- layout-exempt: multi-component runbook — every docs/ path here is rebuild-spec's own output target, not a consumer assumption -->

# Multi-component runbook (monorepo / polyglot microservices)

Load this file when any multi-component flag is set (`--root` / `--batch` / `--aggregate` /
`--emit-manifest` / `--manifest` / `--digest-collect` / `--primary-lang` / `--force-aggregate`)
OR when a plain single run **auto-switches** (SKILL.md Preflight 2.5: `detectJson.auto_switch == true`
on a one-spec-per-unit multi-executable repo — e.g. a Delphi repo with N `.dpr` + shared `Common/`/`DB/`).
A genuinely single-component repo (no `component_profile`, or `--mono`) ignores the whole thing — run
`/tkm:rebuild-spec` as before.

Synthesis internals (neutral-digest schema, topology adapters, entity-correlation) live in
[`system-synthesis-contract.md`](./system-synthesis-contract.md); this file is the orchestration
runbook + the multi-component flag semantics.

## Runbook (v12.0.0 — monorepo / polyglot microservices; v14.0.0 adds reused gate)

```
0. /tkm:rebuild-spec --root <root> --emit-manifest      # discover sub-repos → .rebuild-components.json
   (→ Product-group gate; → Reused sub-root gate for each status:"reused" component)
   (→ writes the shared-layer SIDECAR .rebuild-components-shared.json from detectJson.shared)
0.4 Shared-layer pre-pass (v22.0.0): for each sidecar shared[] entry, run its extractor ONCE at the
    ROOT plan-dir — see "Shared-layer pre-pass" below. Produces the shared DB/Common digests + the
    per-component filtered DB views the --batch loop attributes.
0.5 for each reused component: synth_digest_from_docs.py  # build neutral digest from existing docs
1. while pending: /tkm:rebuild-spec --batch <manifest>  # one component per call (stateless, resumable)
1b. for pass in feature-specs, screen-specs, flows, glossary, jobs, test-cases, design-intent:   # per-component passes, same loop shape
      while pending(pass): /tkm:rebuild-spec --batch <manifest> --pass <pass>
2. /tkm:rebuild-spec --aggregate <root>                 # emit .system-scout-report.md (FACTS data only) + per-component-confidence.md
3. system-researcher CREATES <name>.draft.md from templates/aggregate + scout report + EACH component's docs (authors prose+tables+Mermaid) → review (SY-R1..R8) → promote to <name>.md
```
> **Step 0 — Auto-switch entry (v22.0.0):** Step 0 has TWO entries that converge here.
> - **Explicit:** the user passed a multi-component flag (`--emit-manifest`/`--root`/`--batch`/…).
> - **Auto:** a plain `/tkm:rebuild-spec` run whose `detectJson.auto_switch == true` (a `component_profile`
>   exists — a `one-spec-per-unit` profile claiming ≥2 component roots — e.g. Delphi with N `.dpr` under
>   `PG/<MODULE>/`). SKILL.md Preflight 2.5 prints the `[INFO] multi-component detected …` line and enters
>   this runbook at Step 0.
> Both paths run Step 0 `--emit-manifest` identically (the detector writes the component manifest AND the
> shared sidecar). **Bypasses:** `--mono` (force one mono component → `auto_switch=false`); an explicit
> `--root <subrepo>` (you scoped one component — never auto-switches). **Idempotency:** if
> `.rebuild-components.json` already exists, load + resume — do NOT re-detect or re-switch.
> **Step 1b (v16.1.0 — per-pass auto-loop):** after every component's CORE is done (Step 1), loop the
> remaining passes per component the same way. Each `--batch --pass <name>` call processes EXACTLY ONE
> eligible component (`--<pass> --root <comp>`) in a FRESH context, then writes
> `pass_status[<name>]=done|failed` and exits. Eligibility = core `status:"done"` AND prereq passes done
> AND this pass `pending`. **DAG:** `flows`/`glossary`/`test-cases` require `feature-specs` (`test-cases` —
> v26.1.0 B6 pass — EXPANDS technical-spec.md/edge-cases.md, same prereq class as flows/glossary);
> `feature-specs`/`screen-specs`/`jobs`/`design-intent` need only core (`jobs` — v26.1.0 A2 pass — is a
> re-projection of `behavior-logic.md`, same prereq class as `screen-specs`; `design-intent` — v26.1.0
> B5 pass, EXPERIMENTAL/report-only — reads architecture.md + business-rules.md + entities.md, no
> feature-specs dependency, same prereq class). **reused/excluded components skip every pass.**
> A pass "done" carries no sha
> (output is a disk-verifiable docs tree). Orthogonal to `--aggregate` (which consumes only the core
> digest); `--lang` still runs LAST, once, over the whole tree — never inside this loop.
> **`design-intent` per-component caveat (Decision 4):** Step 1b runs `--design-intent` PER
> COMPONENT (each component gets its own `docs/system/design-intent.md` draft, gated by its own
> D.4 confirmation — no cross-component synthesis in v1). A 7th AGGREGATE-tier design-intent
> artifact (system-researcher-authored, cross-component "why") is explicitly OUT OF SCOPE for v1
> — see `CHANGELOG.md` v26.1.0 sub-entry 3 "aggregate-tier design-intent = follow-up".
> **Product-group gate (v13.3.0 — RT2-F4b) — run at Step 0, BEFORE `--batch`:** detection classifies each
> build unit's `role` from manifest content (`frontend`/`backend`/`service`) and emits a `component_group:`
> warning when ≥2 **complementary** units (FE + BE) sit under one **named** wrapper that has no root manifest
> (e.g. `ssv-wsm-employee/{backend,frontend}` — one Helm chart, FE consumes the BE's API). A wrapper named
> like a conventional container (`apps/`, `services/`, `packages/`…) is never grouped; neither are same-role
> siblings. A `group` is the signature of **one product split into FE+BE build units**, NOT two peer
> microservices. On each detected group, the orchestrator MUST decide granularity before emitting batches:
> - **Interactive** → `AskUserQuestion`: **(a, Recommended)** treat each group as ONE component — emit with
>   `--collapse-groups` so each group folds into a single `fullstack` entry (`path=<wrapper>`, `role=fullstack`)
>   and the later `--batch`/`--root <wrapper>` rebuild keeps the FE→BE contract in one spec; **(b)** keep the
>   units split (each group member stays its own entry, carrying `group:<wrapper>`).
> - **`--auto` / non-interactive** → default to (a): emit with `--collapse-groups`.
>
> So Step 0 becomes `… --emit-manifest --collapse-groups` on path (a), or plain `… --emit-manifest` on (b).
>
> Whichever path: the manifest entry carries `group` (null for ungrouped units). At `--aggregate`, two
> components sharing a `group` are the SAME product — their FE→BE relationship is an **internal contract
> documented inside that product's spec**, never a cross-service topology edge. The detector only surfaces
> the group; it never merges on its own (discovery-only).
> **Reused sub-root gate (v14.0.0 — Phase 05/06) — run at Step 0, AFTER the Product-group gate:**
> detection emits a `component_reused:` warning for every sub-dir whose `docs/.rebuild-state.json`
> exists (it was previously rebuilt as a standalone component). For each such entry, the orchestrator
> MUST `AskUserQuestion` (main thread only — never inside a fan-out agent) BEFORE emitting batches:
> - **(a, Recommended) Reuse** — register the component into the system layer from its existing docs
>   (no source rebuild). Persist `status: "reused"` in the manifest (unchanged from detection).
> - **(b) Rebuild fully** — flip the manifest entry to `status: "pending"`, clear the reused
>   provenance fields (`docs_path`/`source_sha`/`is_git_root`). The component is then treated like any
>   other `--batch` target and fully rebuilt from source.
> - **(c) Exclude** — accept dangling cross-refs. Persist `status: "excluded"`. Every `--aggregate`
>   run prints `[WARN] component_excluded: <name>` and leaves a `[UNVERIFIED]` edge wherever that
>   component was referenced.
>
> The choice is persisted in the manifest so it is **never re-asked** on a resumed run (idempotent).
> The gate fires only when `status:"reused"` is the raw detector default and no recorded decision
> exists. `--auto` / non-interactive → default to **(a) Reuse**.
>
> **Status semantics for `--batch` and `--aggregate`:**
> - `--batch` processes only `status:"pending"` — `reused` and `excluded` entries are skipped.
> - `--aggregate` `check_completeness` treats `status:"reused"` as **SATISFIED** (the
>   `synth_digest_from_docs.py` step produced a digest for it), NOT as incomplete. `excluded` is
>   **dropped** with a `[WARN] component_excluded: <name>` banner (the user accepted dangling refs).
>
> **Step 3 — system-researcher authoring (v19.0.0):** Python is the scanner only. `--aggregate` writes
> ONLY `.system-scout-report.md` (FACTS as data tables — no Mermaid) + the mechanical
> `per-component-confidence.md`; it does NOT create any `<name>.draft.md`. Now spawn the
> **system-researcher** (one agent, or one per artifact in chained waves of ≤`REBUILD_MAX_PARALLEL`
> — the global-cap env itself, NOT the W8 fix-cycle knob; 6 artifacts → a wave of 5 then a wave of 1;
> never more than 5 concurrent) per
> `references/system-researcher-contract.md` to CREATE and AUTHOR the 6 drafts — `overview`,
> `component-catalog`, `architecture`, `glossary`, `cross-service-flows`, `data-ownership-map` — each from
> `templates/aggregate/<name>-template.md` + the scout report + the components' docs. The researcher
> authors the prose, **builds the tables, AND draws the Mermaid itself** (topology/layer/saga) from the
> scout edges PLUS docs-derived edges (tagged `[UNVERIFIED]` + cited) — this is how a reused component's
> missing edges finally reach the charts, not just the prose. Mermaid labels MUST be safe (a mechanical
> lint re-checks at promote). Replace every `{{FILL: ...}}` marker; none may remain.
> **[CRITICAL] read the components' docs.** The agent MUST open and read each component's own docs
> (`architecture.md`, `api-map.md`, `behavior-logic.md`, `entities.md`, `route-list.md`, `system/`) at the
> docs path the scout report's Services table gives — **without exception for any `reused: true` /
> docs-derived component** — and mine them to SUPPLEMENT the heuristic edge list. It may state a component
> has no cross-service edge ONLY after reading its docs; writing *"chưa quan sát được" / "not observed" /
> "isolated"* about a component whose docs it did not read is a CRITICAL violation (caught by `SY-R8`). A
> docs-derived edge it adds carries `[UNVERIFIED]` + a `source: components/<name>/...` citation.
> **Wording rubric (a clean first draft means fewer review cycles):** full plain-language sentences for **a
> new engineer**; **active voice**; **define every acronym/term on first use**; **no raw symbol/ID dumps**
> standing in for prose; keep every `[UNVERIFIED]`. The pinned `{{SCOUT}}` blocks are embedded verbatim —
> never redraw a diagram or restate a table from memory.
> **Optional — why-read-here annotations (C-faithful, v23.0.0):** after authoring the 6 drafts, the
> researcher MAY write `.nav-why.json` in the `system/` directory — a flat JSON object mapping each
> aggregate filename to a 1-line causal reason why it is read at that point in the sequence (e.g.
> `"architecture.md": "Read after the catalog because the layer diagram references the components listed there."`).
> Annotated files override the static fallback clauses in the `system/README.md` reading-order table;
> omitted files keep the static clause. This is optional and additive — absent `.nav-why.json` is safe.
> See `references/system-researcher-contract.md` → "Optional: why-read-here annotations" for the schema.
>
> **Step 3.5 — aggregate review → fix-cycle → promote (v17.0.0; v18 retarget):** the authored drafts are
> NOT promoted on authoring alone. Insert a W7a-style review gate over the **6 authored artifacts** (only the
> mechanical numbers table `per-component-confidence.md` is not reviewed). This MIRRORS the core
> `pipeline-w7-w9.md` loop — **do not restate the algorithm; follow it there** — with these aggregate deltas:
> 1. **Review:** spawn ONE `reviewer` agent reading the authored `*.draft.md` + the per-component digests +
>    **each component's own docs** (to verify `SY-R8` — the researcher actually read reused docs and did not
>    declare a read-available component "unobserved") +
>    `references/verification-checklist-system-synthesis.md` (rules `SY-R1..SY-R8`). It writes
>    `review-report.md` carrying the standard YAML frontmatter (`failed:`, `warnings:`, `result:` — the
>    frontmatter is required, same shape the W7.5 guard expects).
> 2. **Fix-cycle:** `while failed > 0 and cycle < MAX_FIX_CYCLES` (`= 3`): a bounded per-draft fix fan-out
>    (reuse `REBUILD_W8_MAX_PARALLEL`) fixes the flagged drafts, then ONE re-reviewer per cycle re-checks
>    and rewrites the report. Use `_review_report_lib.mutate_review_report` to decrement `failed:` and flip
>    `result: PASS` — no new Python parser is needed (the existing helper handles the report shape).
> 3. **Promote gate:** promote `<name>.draft.md` → `<name>.md` ONLY when `failed == 0` **AND**
>    `_synthesis_narrative_lib.validate_filled_scaffold(scaffold, filled)` returns no violations.
>    After the rename completes, **MANDATORY**: run the deterministic draft-purge step to remove the
>    now-promoted draft files:
>    ```
>    python3 purge_system_drafts.py \
>        --system-dir docs/<lang>/system \
>        --docs-root docs/<lang>
>    ```
>    (In single-lang / bare-docs layout substitute `docs/system` and `docs` respectively.)
>    This prevents stale `*.draft.md` files from accumulating in `docs/` across runs.
>    The purge is gated on the promoted sibling: a draft with no `<name>.md` sibling is kept.
>    **[v25.2.0] Confidence companions (in-v1):** right after the purge, run
>    `derive_confidence_report.py --limitation-note synthesis` once per promoted `<name>.md`
>    (`per-component-confidence.md` excluded — mechanical, not authored). Best-effort, advisory,
>    exit 0 always — NEVER gates promotion. See `references/confidence-report-contract.md`.
>    ```
>    for f in overview component-catalog architecture glossary cross-service-flows data-ownership-map; do
>      [ -f docs/<lang>/system/$f.md ] && .claude/skills/.venv/bin/python3 \
>        claude/skills/rebuild-spec/scripts/derive_confidence_report.py \
>        --artifact docs/<lang>/system/$f.md --project-root . --limitation-note synthesis
>    done
>    ```
>    (In single-lang / bare-docs layout substitute `docs/system` for `docs/<lang>/system`.)
> 4. **Non-convergence:** if 3 cycles still leave `failed > 0`, mirror W8's escalate path — preserve the
>    drafts, ESCALATE to the user, and do **NOT** promote.
> Re-running `--aggregate` overwrites only the `.draft.md`, never a promoted file.
> Thin-orchestrator / context-per-repo: a single session cannot hold 10–20 full rebuilds — each
> `--batch` call runs in a FRESH context and only the manifest + status is carried between calls.
> Sequential by default; bounded-parallel optional for independent repos (reuse `REBUILD_*_MAX_PARALLEL`).
> A genuinely single-component repo (no `component_profile`, or `--mono`) ignores this entirely — run `/tkm:rebuild-spec` as before.
> **Real source sha (Phase R4):** the orchestrator MUST pass the component's real source sha to
> `build_source_to_fcode.py --last-rebuild-sha` when running inside a `--batch` loop on a git
> repository. Obtain it with `git -C <component_path> rev-parse HEAD` before each `--batch` call
> and forward it via `--last-rebuild-sha`. If the sha cannot be resolved (non-git source or git
> unavailable), the field stays empty and `synthesize_system.py` emits
> `[WARN] no_source_baseline: <name>` — a sentinel to flag that incremental baseline is unavailable
> for that component. Never use the all-zeros sentinel `0000…0000` as a real sha.

## Shared-layer pre-pass + attribution (v22.0.0)

A multi-executable repo (Ishindenshin shape) keeps each `PG/<MODULE>/` component's DB objects in a
SIBLING tree `DB/{TABLE,SP,VIEW}/<MODULE>/` and shared logic in `PG/Common/`. The extractors
`os.walk(--root)` only — a per-component run of `--root PG/POS` never sees `DB/SP/POS` or `Common/`.
The shared layers (named by the `component_profile`'s `shared_layer_dirs`, surfaced in
`detectJson.shared` and the manifest sidecar `.rebuild-components-shared.json`) are scanned ONCE and
attributed to each component by citation-path segment.

**Pre-pass (Step 0.4 — runs ONCE at the ROOT plan-dir `plans/<active>/`, before the `--batch` loop):**
for each sidecar `shared[]` entry —
- `kind: "db"` → `extract_sql_schema --root <path>` → the shared DB digest.
- `kind: "source"` → `extract_data_flow --root <path>` → the shared dataflow digest (Common).

The pre-pass uses the **root** plan-dir (NOT `components/<name>/`). Because `_path_lib.resolve_component_paths`
gives the root and every component DISTINCT plan-dirs, their `_extraction-manifest.json` files never
collide → `is_extractor_completed` can never cross-skip. No `--out-suffix` is needed.

**Attribution (deterministic — NOT LLM prose, RT Finding 5):** `_shared_attribution_lib.matches_module_label`
(full-segment equality — `"POS"` matches `DB/TABLE/POS/x.sql` but NOT `DB/TABLE/POSDEN/x.sql`) drives
`filter_shared_digest_by_label`, which writes a per-component FILTERED view of the shared-DB digest keeping
only objects whose citation carries the component's `<MODULE>` segment (= its executable basename). The
db-objects / crud-matrix authoring step consumes the FILTERED view directly (already attributed — do NOT
re-filter); Common is referenced by pointer from the shared dataflow digest, never re-scanned per component.

**Module-name convention (DECLARED):** `PG/<MODULE>` basename ⇔ `DB/<TYPE>/<MODULE>` segment. A component
with no matching DB segment → empty db-objects + an `[UNVERIFIED]` note (no phantom attribution). A shared
DB package with NO `PG` executable (e.g. `SP/PLS`) attaches to NO component and surfaces only at the
aggregate / system layer.

## Per-component secondary-lang translation (`--lang L --root C`) — P05 / D2 + D6

Secondary languages for a component are **TRANSLATE-PER-COMPONENT**: Path B (TR.0–TR.5 in
`pipeline-translate.md`) scoped to the component's docs subtree. This is the ONLY supported
secondary-lang mechanism for components — no derived-view (rung-1/2/3) projection is used.

**Workflow:**

```
# 1. Generate the primary component docs (Path A):
/tkm:rebuild-spec --root payments

# 2. Translate to a secondary language (Path B, component-scoped):
/tkm:rebuild-spec --lang vi --root payments
#    source:  docs/<primary>/components/payments/   (reads — NEVER mutated)
#    target:  docs/vi/components/payments/           (writes — skeleton-identical prose translation)
#    gate:    validate_translation_skeleton.py (same as core tier)

# 3. Aggregate now finds the vi mirror in docs/vi/components/payments/ and promotes rung-1 (no WARN).
/tkm:rebuild-spec --aggregate .
```

**Auto-sync trigger (D6):** after any per-component primary promote changes artifacts under
`docs/<primary>/components/<name>/`, the auto-sync gate (`translation_sync_gate.py`) schedules
re-translation of only the CHANGED component artifacts into each registered secondary lang.
This rides the EXISTING eager, changed-artifacts-only auto-sync path — no new code path.
Opt-out: `REBUILD_AUTO_SYNC_TRANSLATIONS=0` (defers the sync, same behaviour as for core/system
artifacts).

**Path invariant (reuse seam):**

```
source_root  = _path_lib.resolve_component_paths(..., primary_lang).docs_root
             = docs/<primary>/components/<name>/     (or docs/components/<name>/ for en-primary)
target_root  = resolve_docs_root(L, primary_lang, multilang) + /components/<name>/
             = docs/<L>/components/<name>/
```

Both use the same `_lang_lib.resolve_docs_root` resolver the core tier uses — no hand-rolled paths.

**Skeleton-identity invariant:** unchanged. `validate_translation_skeleton.py` enforces byte-identical
headings, code tokens, field labels, table headers, fenced code, and frontmatter for component artifacts
exactly as it does for core artifacts.

**Full spec:** `references/pipeline-translate.md` § "Component-scoped translation".

## v23 one-time component-tree migration (P07)

**Applies to:** v20/v22 repos whose `primary_lang` is NOT `en`.

In v20/v22, the component source lived at `docs/components/` (root) and an optional
derived view existed at `docs/<primary>/components/`. In v23 the canonical source is
`docs/<primary>/components/` (P04 relocation). To converge existing repos onto the new
layout, a one-time migration runs automatically the first time `--aggregate` is called on
a non-en repo that still has the old root layout.

**Trigger:** `_component_migrate_lib.migrate_components_to_lang` is called inside
`synthesize_system._resolve_system_root` (after the flat → per-lang flip, before the
purge pass). It fires once per repo — guarded by the sentinel
`docs/<primary>/.components-migrated-v23`. Subsequent `--aggregate` runs skip it in O(1).

**What it does:**

| Scenario | Action |
|----------|--------|
| `docs/components/` absent (new or already clean v23 repo) | no-op; sentinel written for fast future skip |
| Only `docs/components/` present, no lang dir yet | atomic `os.rename` root → lang; sentinel written |
| Both trees present, byte-identical (common: derived view was a copy) | `shutil.rmtree` root duplicate; sentinel written |
| Both trees present, files differ (manual edits; rare) | keep both; emit `[WARN]`; sentinel NOT written — re-run after resolving manually |
| `primary_lang == "en"` | no-op; en source lives at `docs/components/` by design |

**Root `docs/README.md` pruning:** after a successful migration the root README is
inspected by `resolve_root_readme_removal`. A purely-generated pointer (rebuild-spec
GEN markers, no user tail) is deleted. A hand-written README is never touched.

**Data-loss safety:** byte-identical check is file-by-file and bidirectional (files
in either tree not present in the other count as differing). The differ branch keeps
both trees and warns — it never deletes unmerged content.

**Manual resolution of a differ warning:** inspect the two trees, merge changes into
`docs/<primary>/components/`, then delete `docs/components/` manually and re-run
`--aggregate`. The sentinel is written on the next successful run.

## Multi-component & aggregate flags

These flag rows are scoped to multi-component / system-of-systems runs. (Single-repo flags stay in
`SKILL.md` → Flag overrides.)

| Flag | Effect |
|------|--------|
| `--emit-manifest` | `detect_stack_profile.py --root <root> --emit-manifest` writes the multi-component **run-plan** `.rebuild-components.json` (root-level; override with `--manifest <path>`) from `components[]` — `[{path, profile, role, group, size_est, timeout_hint, max_loc, status, sha}]` with a preflight `<name>` collision check (RT2-F14). **Also writes the shared-layer SIDECAR** `.rebuild-components-shared.json` (`<manifest-stem>-shared.json`) from `detectJson.shared` — `[{path, kind, label}]` (`kind: "db"\|"source"`). The component manifest stays a JSON ARRAY (RT Finding 1 — the sidecar keeps all array-format consumers untouched). `role` (frontend/backend/service) is classified from manifest content; `group` (v13.3.0) links co-deployed FE+BE build units of one product (null when ungrouped) — see the Product-group gate. Discovery only — generates nothing. |
| `--mono` / `--profile <id>` | **[v22.0.0]** Detection controls for the multi-component auto-switch (SKILL.md Preflight 2.5). `--mono` forces `auto_switch=false` (treat a multi-executable repo as one mono component). `--profile <id>` pins the authoritative profile, keying `component_profile` on it — use when a DB-heavy Delphi repo would otherwise make `oracle-plsql` the hit-count `recommended` (Finding 2). Both are passed to `detect_stack_profile.py`. |
| `--batch <manifest>` | Stateless driver step (RT2-F3): process EXACTLY ONE `pending` component (run its `--root`), write `status=done(+sha)`\|`failed(+reason)`, then exit. Driver loop: `while pending: rebuild-spec --batch <manifest>`. Trivially resumable, failure-isolated, fresh context per component. Timeout is a GATE (RT2-F13): a component that dies without writing status → `failed reason=session_terminated`. Manifest writes are atomic + locked (RT2-F5). |
| `--batch <manifest> --pass <name>` | Per-pass driver step: process EXACTLY ONE eligible component for `<name>` ∈ `feature-specs\|screen-specs\|flows\|glossary\|jobs\|test-cases\|design-intent` — run `--<pass> --root <comp>`, then `mark_pass_done`\|`mark_pass_failed` on the nested `pass_status`, then exit. Eligibility = core `status:"done"` AND prereq passes done AND this pass `pending`. **DAG:** `flows`/`glossary`/`test-cases` require `feature-specs` (`test-cases`, v26.1.0 B6, added); the others (incl. `jobs`, v26.1.0; `design-intent`, v26.1.0 B5, EXPERIMENTAL) need only core. reused/excluded skipped. Pass-done carries **no sha** (docs-tree output, disk-verifiable). `design-intent`'s own D.4/D.5 report-only/confirm-promote gate (F11b) is per-component here — each component's draft stops at its own plan dir until confirmed. Driver loop: Step 1b of the runbook. Without `--pass`, `--batch` is the core step above (byte-identical). Primitives: `scripts/_manifest_pass_status_lib.py`. |
| `--aggregate <root>` (alias `--synthesize`) | Build the system-of-systems layer from the per-component neutral digests. **Output is language-mapped (v13):** `docs/system/*` for en single-lang (unchanged) / `docs/<primary>/system/*` for a per-lang project — `primary_lang` discovered by majority across component `.rebuild-state.json` (conflict → majority + `[WARN] lang_conflict`; `--primary-lang` overrides), a flat legacy tree auto-migrated first. **Artifacts (v19):** Python emits ONLY the facts file `.system-scout-report.md` (DATA tables — Services with `reused` + abs docs path, edge/fan-in-out/entity/correlation/event tables, confidence; **no Mermaid**) + mechanical `per-component-confidence.md`. **Python creates no documents.** The system-researcher then CREATES the 6 drafts (`overview`, `component-catalog`, `architecture` — folds the former `interaction-graph`, `glossary`, `cross-service-flows`, `data-ownership-map`) from `templates/aggregate/<name>-template.md` + the scout report + the components' docs — authoring the prose, tables, AND Mermaid (drawing charts from scout edges + docs-derived `[UNVERIFIED]` edges, safe labels) — then review (`SY-R1..R8`) → promote. The aggregate `system/README.md` is a numbered reading-order table + role reading-paths + components pointer + principles. **Per-lang `components/` placement (v23 — single-source translate model, supersedes v20):** component docs are written ONCE to the language-resolved source root: `docs/components/<name>/` for en single-lang; `docs/<primary>/components/<name>/` for non-en or per-lang repos. `resolve_component_paths` passes `primary_lang` to `resolve_docs_root` — the SAME resolver used by core/system artifacts. There is NO derived-view projection and NO rung-1/2/3 selection. Secondary-lang component docs at `docs/<L>/components/<name>/` are produced by the translation pipeline (`--lang <L> --root <name>`) and auto-synced on change via `translation_sync_gate.py`. A non-en repo upgrading from v20/v22 has its `docs/components/` source migrated to `docs/<primary>/components/` by `migrate_components_to_lang` (runs automatically on the first `--aggregate` call; sentinel `docs/<primary>/.components-migrated-v23`). See `docs/decisions/ADR-0003`. **BLOCK by default (RT2-F11):** a missing/incomplete component digest → `[BLOCKED] component_incomplete`. Cross-service edges unresolvable by static analysis → `[UNVERIFIED]` (no phantom edges); Mermaid ids/labels are injection-escaped. Header carries a manifest-snapshot hash (incl. format version); a component sha changed since last synthesis → `[WARN] stale_digest` (RT2-F10); a template referencing an unknown `{{SCOUT}}` block → `[ERROR] unknown_scout_block`. |
| `--primary-lang <code>` | Override the discovered `primary_lang` for the `--aggregate` output path (default: majority across component `.rebuild-state.json`, else `en`). Path-guarded — an unsafe code aborts. |
| `--force-aggregate` | Degraded `--aggregate`: synthesize over the `done` components, print a banner listing the skipped/`failed` ones. Opt-in only — NOT the default. |
| `--digest-collect <dir>` / `--max-digest-age <n>` | Polyrepo support: gather per-repo `_service-digest.json` into one dir before synthesis; reject digests older than `--max-digest-age`. |
| `--manifest <path>` | Explicit run-plan path (shared by `--emit-manifest`/`--batch`/`--aggregate`); default `.rebuild-components.json` at the root. |
| `--root <subrepo>` | Scope the whole run to ONE sub-repo of a monorepo. Path-resolution is centralized in `_path_lib.resolve_component_paths(project_root, active_plan_dir, root_arg, primary_lang)` — **always pass `primary_lang`** (from `state.primary_lang` or `--primary-lang`). en-primary: `docs_root` → `docs/components/<name>/`, `state_file` → `docs/components/<name>/.rebuild-state.json` (byte-identical to v22). non-en primary (e.g. `vi`): `docs_root` → `docs/vi/components/<name>/`, `state_file` → `docs/vi/components/<name>/.rebuild-state.json` (v23 BREAKING). `plan_dir` → `plans/<active>/components/<name>/` (unchanged, lang-agnostic). `<name>` is the sub-repo path with `/`→`-` (NOT basename — RT2-F14). The orchestrator passes the resolved `docs_root` to `promote_drafts.py --docs-root` and `build_source_to_fcode.py --docs-root/--specs-root` (both already accept explicit paths). **Without `--root`, en-primary is byte-identical to the legacy single-repo layout** (`docs/` at CWD) — no regression. `--root` is path-guarded (must be under the project root; `..`/symlink escape → error). Foundation consumed by `--batch`/`--aggregate` (multi-component, v12.0.0). |
