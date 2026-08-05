---
name: tkm:rebuild-spec
description: "Reverse-engineer an existing codebase into structured documentation — 11 core doc artifacts (architecture, data models, API specs, flows, etc.) plus per-feature specs (4 files/feature), process-flows, and glossary synthesis via separate standalone passes. Uses parallel agents: scanner, researcher, reviewer, doc-writer."
argument-hint: "[--feature-specs] [--features F001,..] [--flows] [--glossary] [--jobs] [--test-cases] [--design-intent] [--confirm-promote] [--overview] [--api-doc] [--html]"
metadata:
  author: takumi-agent-kit
  version: "26.4.0"
module: documentation-knowledge
triggers: ["document existing codebase", "reverse engineer", "spec from code", "what does this code do"]
---

# tkm:rebuild-spec

Reverse-engineer existing codebase → structured spec artifacts by composing existing skills.
Zero third-party CLI dependencies. Output lands in layered `docs/` paths (system/, generated/, flows/, features/).

**`--html`:** after the markdown artifacts are written, also render a self-contained editorial HTML companion
of the run's primary overview (the architecture / spec summary) next to its markdown — same stem, `.html` —
using [`../_shared/references/editorial-report-html.md`](../_shared/references/editorial-report-html.md). The
markdown docs stay primary; the HTML is a readable single-file view, not a replacement.

**Version history & breaking-change migration notes:** see [`CHANGELOG.md`](./CHANGELOG.md).

**Principles:** YAGNI, KISS, DRY | Compose, don't reinvent | Template-first.

## Usage

<!-- layout-exempt: usage block — all docs/ paths are rebuild-spec's own output targets -->
```
/tkm:rebuild-spec                         # Incremental if .rebuild-state.json present; full otherwise. Reconcile preflight; auto-resume. Produces CORE artifacts only (v5.0.0+). Knowledge Graph is ON by default: builds/uses a graphify graph to accelerate discovery (graph_to_scout replaces the LLM scout); lazily installs graphifyy. Disable via CLI / .tkm.json (graphify.enabled=false) or env GRAPHIFY_DISABLE=1 / REBUILD_NO_GRAPH=1 → vanilla, no graph, no install.
/tkm:rebuild-spec --full                  # Force full rebuild ignoring state. Alone → core artifacts; combined with a pass flag → that pass ignores its cursor and regenerates all outputs.
/tkm:rebuild-spec --since abc123          # Override diff base SHA (custom incremental starting point)
/tkm:rebuild-spec --dry-run               # Print planner decision JSON to stdout; no file writes
/tkm:rebuild-spec --feature-specs         # Standalone pass: generate/refresh all per-feature specs (4 files/feature). Requires feature-list.md.
/tkm:rebuild-spec --features F001,F002    # Scoped subset of --feature-specs pass (warn + proceed). Was: default-pipeline W6 narrowing.
/tkm:rebuild-spec --flows                 # Standalone pass: synthesize process-flows. Requires docs/features/* from --feature-specs pass.
/tkm:rebuild-spec --glossary              # Standalone pass: synthesize glossary. Requires docs/features/* from --feature-specs pass.
/tkm:rebuild-spec --jobs                  # Standalone pass: synthesize batch/background-job inventory. Requires docs/generated/behavior-logic.md.
/tkm:rebuild-spec --test-cases            # Standalone pass: derive UT/IT/UAT test-case lists per feature. Requires docs/features/*.
/tkm:rebuild-spec --design-intent         # EXPERIMENTAL standalone pass: infer "why built this way" architectural rationale. Requires core artifacts. Report-only — writes to the plan dir; use --confirm-promote to publish to docs/system/.
/tkm:rebuild-spec --design-intent --confirm-promote  # Explicit non-interactive promotion of a previously-reviewed design-intent draft to docs/system/design-intent.md (F11b — no other path auto-promotes it).
/tkm:rebuild-spec --screen-specs          # Standalone pass: generate screen specs. Requires docs/generated/screen-list.md.
/tkm:rebuild-spec --api-contracts         # Standalone pass: synthesize API contracts (REST/GraphQL/gRPC). Off by default. Requires core artifacts.
/tkm:rebuild-spec --overview              # Standalone pass: client-facing System Overview (.md + styled .docx) from promoted docs/. Requires feature-list.md.
/tkm:rebuild-spec --api-doc               # Standalone pass: client-facing Sun* API Design .xlsx (BM-2-901-52). Requires route-list.md (swagger optional).
/tkm:rebuild-spec --artifact route-list   # Regenerate single core artifact (reuses upstream if present)
/tkm:rebuild-spec --resume                # Reconcile-only: sync TaskList against disk, close stale in_progress tasks whose outputs already exist. No new work dispatched.
/tkm:rebuild-spec --probe-routes          # Explicit Wave 0.4 bootability gate: AskUserQuestion → Tier-1 CLI probe → write _route-probe.json sidecar used by W1 route-list. Auto-triggered when lockfile present; this flag forces the gate even if no lockfile found.
/tkm:rebuild-spec --legacy                # RE preset for legacy non-web (Delphi/Oracle): bootable=false + RE output contract + profile extractors. Additive over the resolved profile.
/tkm:rebuild-spec --lang vi               # First run: vi becomes PRIMARY, generated inline at docs/vi/. Later run: translates from primary.
/tkm:rebuild-spec --lang jp               # jp de-aliases to ja. Adding the first secondary flips an en-primary repo docs/ → docs/en/, then translates → docs/ja/ (skeleton-identity + ±LOC gates).
```

**Multi-component runbook (monorepo / polyglot microservices):** when running across multiple sub-repos
(`--root` / `--batch` / `--aggregate` / `--emit-manifest`) — OR when a plain single run **auto-switches**
(Preflight 2.5: `detectJson.auto_switch == true` on a one-spec-per-unit multi-executable repo) — the full
driver loop (Steps 0–3 incl. the per-pass auto-loop), the Product-group / Reused sub-root gates, the
Shared-layer pre-pass, the narrative-fill contract, and the multi-component flag table all live in
[`references/multi-component-runbook.md`](./references/multi-component-runbook.md) — loaded on-demand (see
"On-demand pipeline loading"). **A genuinely single-component repo** (no `component_profile` → `auto_switch=false`,
or `--mono`) **ignores this entirely** — run `/tkm:rebuild-spec` as before.

**Recommended pass sequence:**
```
1. /tkm:rebuild-spec                  # core artifacts (always first)
2. /tkm:rebuild-spec --feature-specs  # per-feature 4-file specs
3. /tkm:rebuild-spec --flows          # process-flow synthesis
4. /tkm:rebuild-spec --glossary       # glossary synthesis
5. /tkm:rebuild-spec --jobs           # batch/background-job inventory (optional; core-tier, parallel-safe)
6. /tkm:rebuild-spec --test-cases     # UT/IT/UAT test-case lists per feature (optional; requires --feature-specs)
7. /tkm:rebuild-spec --design-intent  # EXPERIMENTAL "why built this way" rationale (optional; core-tier, parallel-safe; report-only — see --confirm-promote)
8. /tkm:rebuild-spec --api-contracts  # API contracts (optional; core-tier, parallel-safe)
9. /tkm:rebuild-spec --screen-specs   # screen specs (optional)
10. /tkm:rebuild-spec --overview       # client-facing System Overview deliverable (optional; .md + .docx)
11. /tkm:rebuild-spec --api-doc        # client-facing Sun* API Design workbook (optional; .xlsx)
```
> Each pass also prints an optional `/ask-expert` review line in its handoff (see "End-of-pass handoff"). The sequence above is next-pass guidance only — it intentionally omits the review step, which lives in the canonical handoff block.

**End-of-pass handoff (authoritative):** Every pass ends by printing its own "Pass-completion handoff prompt" — defined in that pass's reference file, NOT this sequence. Each handoff includes an optional `/ask-expert` review line (e.g. `/ask-expert "Is the core architecture & data-model documentation accurate and complete?"`) before the next-pass guidance. When printing the handoff, reproduce the canonical block from the pass file verbatim — do not regenerate it from the sequence above (the sequence omits the review step). Handoff sources: core → `references/pipeline-w7-w9.md`; feature-specs → `references/pipeline-feature-specs.md`; flows & glossary → `references/pipeline-flows-glossary.md`; jobs → `references/pipeline-jobs.md`; test-cases → `references/pipeline-test-cases.md`; design-intent → `references/pipeline-design-intent.md` (EXPERIMENTAL — report-only handoff differs from every other pass, see § EXPERIMENTAL status there); api-contracts → `references/pipeline-api-contracts.md`; screen-specs → `references/pipeline-screen-specs.md`; overview → `references/overview-pass.md`; api-doc → `references/api-pass.md`.

### Pass ordering & prerequisites

Single source of truth for the pass dependency chain. Each pass preflight ABORTs (see
its reference file) if its prerequisite is missing.

<!-- layout-exempt: pass dependency table — docs/ paths are rebuild-spec's own output targets and prerequisites -->
| Pass | Prerequisite (must exist) | Produced by |
|------|---------------------------|-------------|
| core | source code | — |
| `--feature-specs` | `docs/generated/feature-list.md` | core |
| `--flows` | `docs/features/*/technical-spec.md` + `docs/generated/entities.md` | feature-specs + core |
| `--glossary` | `docs/features/*/business-context.md` + `docs/generated/entities.md` | feature-specs + core |
| `--jobs` | `docs/generated/behavior-logic.md` | core (parallel-safe w/ others) |
| `--test-cases` | `docs/features/*/technical-spec.md` (+ `edge-cases.md`, promoted alongside) | feature-specs + core |
| `--design-intent` | `docs/system/architecture.md` + `docs/system/business-rules.md` + `docs/generated/entities.md` (ADRs + `business-context.md` optional enrichment) | core (parallel-safe w/ others; EXPERIMENTAL/report-only, F11) |
| `--api-contracts` | `docs/generated/route-list.md` + `entities.md` + `api-map.md` + `docs/system/permissions.md` | core (parallel-safe w/ others) |
| `--screen-specs` | `docs/generated/screen-list.md` | core (parallel-safe w/ others) |
| `--overview` | `docs/generated/feature-list.md` (+ optional system/, flows/, features/ enrichment) | core (presentation pass — re-shapes promoted docs/) |
| `--api-doc` | `docs/generated/route-list.md` (swagger/api-map/api-contracts optional enrichment) | core (deliverable pass — independent of `--api-contracts`) |

**Force restart:** delete `plans/<active>/artifacts/` → next no-args invocation starts fresh.

**`--artifact route-list` and probe manifest:** When re-running `--artifact route-list` after a prior probe (status `passed` or `skipped`), the orchestrator reuses the existing `_route-probe.json` sidecar without re-prompting. The probe gate is only re-issued when `probe_gate.status == "awaiting_user"` (resumed from halt) or when `--full` is combined with a bootable stack or `--probe-routes` flag. This ensures the Tier-1 manifest enriches W1 route-list even on partial re-runs.

## Preflight

1. Detect project root = CWD (must be under git control).
1.5. **State-schema gate (v11.0.0 — RT-F4).** If `docs/.rebuild-state.json` exists, read its
   `schema_version`. Absent or numerically `< 11.0.0` → **invalidate the preflight checkpoint**: ignore
   any persisted profile/probe_gate, and run the profile detection in step 2 fresh before continuing the
   wave graph (a pre-profile state carries no `profile_id`/encoding). `>= 11.0.0` → resume as normal.
2. **Stack-profile detection (v11.0.0 — ask-don't-abort).** Verify the working tree is non-empty
   (empty → ABORT with clear hint), then resolve a stack-profile rather than demanding a web manifest:
   ```
   const r = bash(`.claude/skills/.venv/bin/python3 \
     claude/skills/rebuild-spec/scripts/detect_stack_profile.py --root .`)
   if (r.exitCode === 2) { /* corrupt KIT profile — fatal, not a project condition */
     throw new Error("rebuild-spec: stack-profile load failed — fix the kit profile:\n" + r.stderr) }
   const detectJson = JSON.parse(r.stdout)  // exit 0 for every detection outcome incl. no-match
   ```
   - **≥1 profile matched** → use `detectJson.recommended_profile` (highest hits). Multiple matches →
     keep the `[MULTI_STACK]` annotation built from `detectJson.matched[]`; note it. A matched
     `web-js-ts` profile reproduces the prior web behavior exactly (regression-free).
   - **No profile matched** → do NOT abort. Behavior depends on interactivity:
     - Interactive → **`AskUserQuestion`** with three options: (a) pick a profile manually from
       `references/stack-profiles/`, (b) "treat as generic source" → `generic-source` profile, (c) abort.
       - **Tier-2 sniff sub-branch (Phase 09, Track D accept-path).** Tier 0/1 leaves the 3-option flow
         above completely unchanged. Only when `detectJson.ui_sniff.tier == 2` (cited, structurally-
         corroborated UI evidence) does a 4th option — **(d) "investigate as CLI/TUI"** — get added, with
         its untrusted-citation handling, `_ui_sniff_accept_lib.py` accept-path, and decline fall-through.
         Full procedure: load [`references/tier2-ui-sniff-accept.md`](./references/tier2-ui-sniff-accept.md).
     - **Non-interactive** (`--non-interactive` flag OR `REBUILD_NON_INTERACTIVE=1`) → apply
       `generic-source`, print `[WARN] non_interactive_fallback`, do NOT prompt, do NOT run any
       stack-specific extractor. If `detectJson.ui_sniff.tier == 2`, ADDITIONALLY print
       `[WARN] ui_sniff_tier2` with the cited signals (advisory log line only) — still NEVER prompts and
       NEVER invokes `_ui_sniff_accept_lib` (the accept-path digest is never built non-interactively).
   - Record the resolved `profile_id` + `detectJson.encoding` + `detectJson.detected_language_heading`;
     pass them to Wave 0.5 (`build_session_context.py --profile-id <id> --encoding <enc>`). Honor any
     `detectJson.warnings` (`file_cap_reached` → result partial; `encoding_unverified` → advisory;
     `component_group:` → a co-deployed frontend+backend product — see the **Product-group gate** in
     `references/multi-component-runbook.md`; on a single-component run it is advisory only).
2.5. **Multi-component auto-switch (v22.0.0).** A plain single run over a multi-executable repo
   (e.g. a Delphi repo with 20 `.dpr` under `PG/<MODULE>/` + shared `Common/` + a `DB/` tree) must
   NOT flatten every module into one mono doc set. The detector reports this via `detectJson.auto_switch`.
   - **IF** `detectJson.auto_switch === true` **AND** the user did NOT pass `--root <subrepo>` **AND**
     `.rebuild-components.json` does not already exist (idempotency — a prior run already switched):
     ```
     [INFO] multi-component detected ({detectJson.auto_switch_reason}): switching to --emit-manifest flow. Use --mono to override.
     ```
     Then proceed **as if the multi-component flags were set** — load `references/multi-component-runbook.md`
     and run the driver loop from Step 0 (`--emit-manifest` → `--batch` → `--aggregate`). The detector
     already emitted the component manifest + shared sidecar shapes; the runbook's Shared-layer pre-pass
     (Step 0.4) consumes `detectJson.shared`.
   - **ELSE** continue the legacy single-repo path below (steps 3–4).
   - `--mono` forces `auto_switch=false` at the detector (escape hatch — treat the repo as one
     monolithic component). `--root <subrepo>` is an explicit single-component scope and never auto-switches.
     `--profile <id>` pins the authoritative profile when Delphi+Oracle co-detect (sets `component_profile`).
   - **Idempotency:** if `.rebuild-components.json` already exists, load it and resume — do NOT re-detect/re-switch.
3. Resolve active plan path from `## Plan Context` hook; if none, fallback to `plans/<timestamp>-rebuild-spec/`.
3.5. **Bootstrap detection (v2.x upgrade):** If `.rebuild-state.json` absent AND `docs/specs/system-overview.md` or `feature-list.md` present AND `git log -1 -- docs/specs/` returns a SHA ≠ HEAD → prompt user to bootstrap state from git history or force full rebuild. See `references/pipeline.md` § Wave -2.
4. Ensure output dirs exist: `docs/system/`, `docs/generated/`, `docs/flows/`, `docs/features/`, `plans/<active>/artifacts/`.  <!-- layout-exempt: preflight step 4 — output dirs are this skill's own targets -->
5. **[GRAPHIFY-INTEGRATION] Knowledge Graph — ON BY DEFAULT, runs BEFORE Wave 0.** Always run exactly ONE command to build/refresh the graph (idempotent; lazily installs `graphifyy` into the kit venv if missing, (re)indexes the repo, updates `.gitignore` — all CODE-enforced). The script self-gates on config `graphify.enabled` (default true) and no-ops when disabled, so it is safe to run every time:
   ```
   .claude/skills/.venv/bin/python3 .claude/skills/rebuild-spec/scripts/graph_preflight.py
   ```
   (If the kit venv python is unavailable, use `python3`.) **When graphify is disabled** (config `graphify.enabled=false`, or env `GRAPHIFY_DISABLE=1` / `REBUILD_NO_GRAPH=1`) the script no-ops — no graph is built, nothing is installed, and every downstream wave behaves byte-identically to vanilla. It prints one status line; on any failure it degrades to "no graph" (vanilla). *(Note: PyPI package is `graphifyy` with double-y; module/command is `graphify`.)* When a graph results, downstream waves use it automatically:
   - **Wave 0 is REPLACED for $0**: `scripts/graph_to_scout.py` generates a contract-complete `scout-report.md` straight from `graph.json` (file inventory + BL grep), so the LLM scout subagent (the most expensive discovery step, 1-3M tokens) is skipped entirely — see `references/pipeline-w0-w5.md` Wave 0 block.
   - **W1 starts from machine-true drafts**: `scripts/graph_to_drafts.py` emits `_graph-drafts/{data-model,architecture}-draft.md` (class inventory with file:line + inherits; module-level Mermaid import graph) so those researchers verify & complete instead of building structure from scratch (best-effort; missing drafts → researchers work from templates as before).
   - **Post-promote coverage proof**: `scripts/graph_spec_coverage.py` (advisory, never blocks) machine-verifies the promoted spec against graph ground truth — every model class in code appears in `entities.md`, every route file in `route-list.md` — see `references/pipeline-w7-w9.md`.
   - The shared `_session-context.md` (built by `scripts/build_session_context.py`) emits graphify-first guidance gated on `graphify-out/graph.json` (suppressed when `REBUILD_NO_GRAPH=1`).
   No graph → behavior is byte-identical to vanilla. Output contract is unchanged in all cases: same 11 artifacts, same templates, same quality gates and reviewer checklist.

## Pipeline

Load on demand (not inlined here):
- `references/pipeline.md` — wave graph + always-loaded core. Load on-demand: pipeline-w0-w5.md, pipeline-dispatch-and-gates.md, pipeline-w5x-w6.md, pipeline-w7-w9.md, pipeline-screen-specs.md, pipeline-feature-specs.md, pipeline-flows-glossary.md
- `references/pipeline-dispatch-and-gates.md` — shared `profile`/`produce()` binding, Wave 0.6 structural extraction, and the canonical Renumber+Contiguity Gate. Loaded with pipeline-w0-w5.md (and any pass that applies the canonical gate).
- `references/artifact-sharding.md` — descriptor table, merge recipe, fragment contract, ID contiguity gate (renumber + validate after every sharded merge). Loaded when pre-gen estimate exceeds threshold for any artifact.
- `references/code-formats.md` — shared schema; pass to researcher
- `references/verification-checklist-universal.md` — universal rules + Pending Marker Rule (always load with any checklist file)
- `references/verification-checklist-core-artifacts.md` — W7a: 11 core artifact sections + Composite Detection + Failure Trap
- `references/verification-checklist-feature-spec.md` — FS.5: FeatureSpec + Deterministic Validator Coverage + Failure Trap
- `references/verification-checklist-screen-spec.md` — SS.2: ScreenSpec + Composite Detection + Failure Trap
- `references/verification-checklist-quality-gates.md` — W4.5 / W5.6 targeted gates only

### On-demand pipeline loading
Before dispatching W0–W5: Read `references/pipeline-w0-w5.md` AND `references/pipeline-dispatch-and-gates.md` (the latter binds `profile`/`produce()` + defines the canonical Renumber+Contiguity Gate the task chain applies by name).
Before dispatching W5.5 (feature existence gate): Read `references/pipeline-w5x-w6.md`.
Before dispatching W7a/W7.5/W8/W9 (core review/fix/promote): Read `references/pipeline-w7-w9.md`.
When `--feature-specs` or `--features` flag is set: Read `references/pipeline-feature-specs.md`.
When `--flows` flag is set: Read `references/pipeline-flows-glossary.md`.
When `--glossary` flag is set: Read `references/pipeline-flows-glossary.md`.
When `--jobs` flag is set: Read `references/pipeline-jobs.md`.
When `--test-cases` flag is set: Read `references/pipeline-test-cases.md`.
When `--design-intent` flag is set: Read `references/pipeline-design-intent.md` (EXPERIMENTAL — read the § EXPERIMENTAL status section in full before dispatching; the pass stops at the plan dir unless `--confirm-promote` or an interactive confirmation is given).
When `--api-contracts` flag is set: Read `references/pipeline-api-contracts.md`.
When `--screen-specs` flag is set: Read `references/pipeline-screen-specs.md`.
When `--overview` flag is set: Read `references/overview-pass.md`.
When `--api-doc` flag is set: Read `references/api-pass.md`.
When any multi-component flag is set (`--root` / `--batch` / `--aggregate` / `--emit-manifest` / `--manifest` / `--digest-collect` / `--primary-lang` / `--force-aggregate`) **OR when `detectJson.auto_switch === true` (Preflight 2.5 — a plain flagless run that auto-switches)**: Read `references/multi-component-runbook.md` (driver loop + Product-group/Reused gates + the **v19 scanner-only** flow — `--aggregate` emits ONLY `.system-scout-report.md` (FACTS data, no Mermaid) + `per-component-confidence.md` and creates NO documents; the **system-researcher** then CREATES the 6 `<name>.draft.md` from `templates/aggregate/` + the scout report + each component's docs, authoring the prose, **tables, AND Mermaid** (drawing charts from scout edges + docs-derived `[UNVERIFIED]` edges, safe labels) per `references/system-researcher-contract.md` (never declaring a read-available component "unobserved") + the **aggregate review→fix-cycle→promote gate** (Step 3.5 — a W7a-style `reviewer` pass over the 6 authored artifacts against `references/verification-checklist-system-synthesis.md`, `SY-R1..R8`, + a mechanical Mermaid-safety lint) + the multi-component flag table).
When `--lang <code>` targets a secondary language (translate path): Read `references/pipeline-translate.md`.
**[lang-sync-fix] ALSO read `references/pipeline-translate.md` on ANY primary pass when `docs/.rebuild-state.json` has a non-empty `translations` object** — primary passes run `translation_sync_gate.py` (plan + finalize) in their post-promote steps, echo the finalize stdout `Secondary languages:` line VERBATIM in their completion handoff, and MUST run `check_translation_gate.py --pass <name>` before writing the completion flag (exit 1 blocks completion). Without loading pipeline-translate.md, the invocation contract is missing and secondary mirrors silently stay primary-only. Check: `translations = JSON.parse(readFile("docs/.rebuild-state.json")).translations ?? {}`; if `Object.keys(translations).length > 0`, load the file before the pass's promote step.

Composite screen detection is automatic. See `references/composite-screen-detection.md` for the H1-H6 rules, execution order, 2-of-3 gate, tab short-circuit, and wizard sub-classification.

BehaviorLogic stability enforced via scout BL inventory (Wave 0) + 1-BL-per-file cardinality contract (Wave 2b) + reviewer cardinality cross-check (Wave 7a). See `references/bl-source-patterns.md`.

**A1 confidence-report companions (v25.2.0):** every promoted artifact across ALL passes — core, feature-specs, screen-specs, flows, glossary, api-contracts, and system-synthesis (aggregate) — gets a `confidence-report_<stem>.md` sidecar, deterministically derived from the artifact's own inline citations/markers (`scripts/derive_confidence_report.py` — no LLM, best-effort, never gates a pass). System-synthesis companions additionally carry a `--limitation-note synthesis` header caveat (their citation density is structurally lower — not comparable to per-feature scores). Advisory and internal-only, like `.nav-metadata.json` — excluded from `--overview`/doc-writer export. See `references/confidence-report-contract.md`.

**A3 Source Walkthrough + B4 DB Impact per Event (v26.0.0, BREAKING):** two NEW REQUIRED
sections — `## Source Walkthrough` (technical-spec.md AND screen-spec spec.md; ordered reading
list + call-hierarchy diagram + a pointer to the recast `## Source Code References` /
`## Source References` table, F15 DRY) and `## DB Impact per Event` (technical-spec.md ONLY;
top-level H2, one row per DB-writing event/endpoint). Gated by a DEDICATED validator
(`scripts/validate_reading_guide_db_impact.py`, wired at FS.2) with its own WARN-first
`*.pre_migration` degradation contract — NEVER added to `_spec_constants.REQUIRED_H2_TECH`
(that exact-order check has no degradation window; Decision 2). Migration:
`scripts/migrate-reading-guide-db-impact.py` flags un-migrated specs (cannot mechanically
backfill — requires re-reading source). See `references/confidence-report-contract.md` § A3
navigational entries (why these list entries never inflate the A1 citation-coverage stat).

**B5 `--design-intent` (v26.1.0, EXPERIMENTAL — report-only first release, F11):** infers
cross-cutting "why built this way" architectural rationale from ADRs (highest-trust, optional),
`architecture.md`/`business-rules.md`, and source-code patterns. Highest hallucination risk of
any pass in this skill, so it ships with three defenses: (a) every draft opens with an
EXPERIMENTAL/`[INFERRED]`-heavy disclaimer banner; (b) v1 writes ONLY to
`plans/<active>/artifacts/design-intent.md` — there is **no auto-promote path**; promotion to
`docs/system/design-intent.md` happens only via an explicit `AskUserQuestion` confirmation or a
follow-up `--design-intent --confirm-promote` invocation; (c) a NEW mode-agnostic validator
(`scripts/validate_design_intent_density.py`) gates every paragraph on citation-or-`[INFERRED]`,
regardless of `profile.re_contract` (distinct from `re-output-contract.md`'s RE-mode-only
density check). Graduation from EXPERIMENTAL to default-promote requires a 3-repo pilot with
`[INFERRED]` ≤25% and zero fabricated citations — see `CHANGELOG.md` v26.1.0 sub-entry 3. See
`references/pipeline-design-intent.md`.

**Default flow (no flags) — CORE artifacts only.** Wave DAG + per-wave dispatch bodies live in the
on-demand refs (always-loaded `references/pipeline.md` § Waves; `references/pipeline-w0-w5.md` for
W0–W5 + gates; `references/pipeline-w5x-w6.md` for W5.5/W5.6; `references/pipeline-w7-w9.md` for
review/fix/promote). Ordered shape:

0. **Profile manifest** — print produce/skip map; every `skip`-mapped wave's task + gate is NOT dispatched (`pipeline-w0-w5.md` § "Profile-driven dispatch").
1. **W0** scout → **W0.6** structural extraction (only when `profile.extractors` non-empty) → **W0.4** route probe (only when `profile.probe.bootable`) → **W0.5** `_session-context.md`.
2. **W1–W5** researcher chain (`blockedBy` per dep graph), with halt gates: **W1.5** DataModel, **W1.1** RouteList, **W2a.1** ScreenList, **W4.5** UserStories, **W5.5** existence, **W5.6** FeatureList.
3. **W7a** reviewer (11 core artifacts, parallel w/ W5 completion) → **W7.5** structural-fixer → **W8** fix fan-out (`REBUILD_W8_MAX_PARALLEL`; ≤`MAX_FIX_CYCLES=3`) → **W9** promote (`promote_drafts.py` + W9.5 reverse-index + `wave9-complete.flag` + Core Pass-completion handoff).

**Review zone (W7a-core):** LLM semantic checks on 11 core artifacts. **Pre-fix zone (W7.5):** deterministic structural safety net.

<!-- layout-exempt: standalone passes — docs/ paths are rebuild-spec's own input/output targets -->
**Standalone passes (separate invocations — NOT part of the default flow):**
- **`--feature-specs`:** FS.1–FS.7 fan-out, per-feature 4-file specs. Requires feature-list.md. See `references/pipeline-feature-specs.md`.
- **`--flows`:** FL.1–FL.5 process-flow synthesis. Requires `docs/features/*`. See `references/pipeline-flows-glossary.md`.
- **`--glossary`:** GL.1–GL.3 glossary synthesis. Requires `docs/features/*`. See `references/pipeline-flows-glossary.md`.
- **`--jobs`:** J.1–J.5 batch/background-job inventory (`docs/generated/job-list.md`). Requires `docs/generated/behavior-logic.md`. A re-projection of BL### entries filtered to job types — NO `docs/jobs/` namespace (F13). See `references/pipeline-jobs.md`.
- **`--test-cases`:** TC.1–TC.5 per-feature UT/IT/UAT test-case lists (`docs/features/{slug}/test-cases.md`, 5th SIDECAR file). Requires `docs/features/*`. An EXPAND-DETAILS pass over the already-cited `technical-spec.md`/`edge-cases.md` — fan-out shape identical to FS.1. See `references/pipeline-test-cases.md`.
- **`--design-intent` [EXPERIMENTAL]:** D.1–D.5 single-file "why built this way" synthesis (`docs/system/design-intent.md`). Requires core artifacts (architecture.md, business-rules.md, entities.md). No fan-out (mirrors the GL.1 glossary shape). **Report-only first release (F11b):** D.1–D.4 stop at `plans/<active>/artifacts/design-intent.md`; D.5 (promotion) runs ONLY on explicit confirmation (`AskUserQuestion` or `--confirm-promote`). See `references/pipeline-design-intent.md`.
- **`--screen-specs`:** SS.1–SS.3 screen specs. Requires `docs/generated/screen-list.md`. See `references/pipeline-screen-specs.md`.
- **`--overview`:** OV.1–OV.4 client-facing System Overview deliverable (`docs/<ProjectName>_System_Overview.md` + `.docx`). Presentation pass — re-shapes promoted `docs/`, never reads source. Requires `docs/generated/feature-list.md`. See `references/overview-pass.md`.
- **`--api-doc`:** Sun* API Design workbook (`docs/api/<System> - API Design.xlsx`, BM-2-901-52) via bundled-template clone + deterministic lint (B1) + optional LLM semantic review (B2). Requires `docs/generated/route-list.md` (swagger optional). Distinct from `--api-contracts`. See `references/api-pass.md`.

**Flag overrides:**

<!-- layout-exempt: flag overrides table — docs/ paths are rebuild-spec's own targets and prerequisites -->
| Flag | Effect |
|------|--------|
| _(none)_ | Core pass only: incremental if `docs/.rebuild-state.json` present; full otherwise. Reconcile preflight runs first; auto-resume if `TaskList` has pending tasks. Terminates at W7a-core + W9-core (no feature specs, flows, or glossary). |
| `--full` | Force full rebuild ignoring state. Alone → all 11 core artifacts. Combined with a pass flag (`--feature-specs` / `--flows` / `--glossary` / `--screen-specs`) → forces that pass to regenerate ALL its outputs, ignoring its incremental cursor. Mutually exclusive with `--since`. |
| `--since <sha>` | Override diff base SHA for incremental (custom starting point). Mutually exclusive with `--full` |
| `--dry-run` | Print planner decision JSON to stdout; no file writes, no wave dispatch |
| `--artifact NAME` | Skip to the wave owning NAME; reuse existing upstream artifacts if present. ABORT if upstream missing |
| `--feature-specs` | Run standalone feature-specs pass (FS.1–FS.7). Generates 4 files per F###. Requires `docs/generated/feature-list.md`. Incremental: regenerates only F### whose source changed since last pass. Loads `references/pipeline-feature-specs.md`. |
| `--features F###,...` | Scoped subset of `--feature-specs` pass (was: default-pipeline W6 narrowing). Emits one-time notice `[BEHAVIOR CHANGE v5]`. Warn + proceed. Loads `references/pipeline-feature-specs.md`. |
| `--flows` | Run standalone flows pass (FL.1–FL.5). Requires `docs/features/*/technical-spec.md`. Re-synths ALL flows if source changed since cursor. Loads `references/pipeline-flows-glossary.md`. |
| `--glossary` | Run standalone glossary pass (GL.1–GL.3). Requires `docs/features/*/business-context.md`. Loads `references/pipeline-flows-glossary.md`. |
| `--jobs` | Run standalone jobs pass (J.1–J.5). Requires `docs/generated/behavior-logic.md`. Produces `docs/generated/job-list.md` (JOB### inventory + per-job detail — single artifact, F13). Loads `references/pipeline-jobs.md`. |
| `--test-cases` | Run standalone test-cases pass (TC.1–TC.5). Requires `docs/features/*/technical-spec.md`. Produces `docs/features/{slug}/test-cases.md` (UT/IT/UAT, TC### per-feature reset — 5th SIDECAR file, never joins the mandatory 4-tuple or the promotion gate). Fan-out identical to FS.1 (one researcher per F###, wave-chained ≤5). Loads `references/pipeline-test-cases.md`. |
| `--design-intent` [EXPERIMENTAL] | Run standalone design-intent pass (D.1–D.5). Requires `docs/system/architecture.md` + `docs/system/business-rules.md` + `docs/generated/entities.md`. Single-file synthesis, no fan-out. **Report-only (F11b):** writes ONLY to `plans/<active>/artifacts/design-intent.md`; does NOT promote to `docs/system/design-intent.md` unless explicitly confirmed (see `--confirm-promote`). Loads `references/pipeline-design-intent.md`. |
| `--confirm-promote` | Paired with `--design-intent` ONLY. Non-interactive trigger for Wave D.5 (promotion of a previously-generated, previously-reviewed `plans/<active>/artifacts/design-intent.md` draft to `docs/system/design-intent.md`). No effect combined with any other flag. There is no other way to make this pass write to `docs/` — this is intentional (F11b). |
| `--resume` | Run reconcile preflight only — no new waves dispatched. Use after a killed session to sync TaskList with disk |
| `--probe-routes` | Wave 0.4 only: force bootability gate prompt → run Tier-1 CLI route lister → write `_route-probe.json` sidecar consumed by W1 route-list. Auto-triggered when a bootable stack lockfile is detected; use this flag to force the gate even on non-lockfile projects. If user chooses "Need to set up app first", pipeline halts with a checkpoint written to `probe_gate` in `.rebuild-state.json`; re-run `--artifact route-list` to resume. No-op if scout-report absent. |
| `--screen-specs` | Run standalone ScreenSpec pass (SS.1–SS.3). Requires `docs/generated/screen-list.md`. Incremental: regenerates only screens changed since last pass. Loads `references/pipeline-screen-specs.md`. |
| `--api-contracts` | Run the standalone api-contracts pass (AC.1 synthesis + AC.2 validator + AC.3 review + AC.5 promotion; historical numbering: W6.87 / W6.875). Off by default (token cost; not all projects need API contracts). Produces `docs/generated/api-contracts.md` capturing REST/GraphQL/gRPC request-response contracts. Loads `references/pipeline-api-contracts.md`. |
| `--overview` | Run the standalone overview pass (OV.1–OV.4). Synthesizes a single **client-facing System Overview** (11 sections, business-terminology) from the already-promoted `docs/` spec set and emits `docs/<ProjectName>_System_Overview.md` + a styled `.docx` deliverable. Presentation/synthesis pass — never reads source code. Hard token-leak gate (`extensions/scripts/verify_overview.py`) + reviewer cross-check before the `.docx` build (`extensions/scripts/build_overview_docx.py`, pandoc + stdlib). Requires `docs/generated/feature-list.md`. Loads `references/overview-pass.md`. |
| `--api-doc` [`--no-semantic-review`] | Run the standalone api-doc pass. Builds a **client-facing Sun* API Design `.xlsx`** (form BM-2-901-52) by cloning the bundled template and writing only cell values (format-identical output), one detail sheet per API operation. Source resolves as: explicit/auto swagger → else derived from `docs/generated/route-list.md` (+ api-map/api-contracts) via `extensions/api/build_api_doc.py` — works on any stack. Deterministic style + semantic lint (B1) are hard gates; the LLM semantic review (B2, `reviewer`) runs by default after SEAL, skip with `--no-semantic-review`. **Distinct from `--api-contracts`** (that emits Markdown contracts; this emits the Excel deliverable — both may run). Requires `docs/generated/route-list.md`; needs `openpyxl`+`PyYAML` (kit venv ships both). Loads `references/api-pass.md`. |
| `--lang <code>` | Output language selection. Accepts any code (lowercase-normalized + de-aliased: `jp`→`ja`, `cn`→`zh`, `kr`→`ko`, `vn`→`vi`; warns on non-standard). Dispatch: if `code == primary_lang` (or first run) → **inline generation** (prose in `<code>`, English skeleton); else → **translate-from-primary** (prose translated, skeleton byte-identical). First run sets `primary_lang` in state. **Location is mode-aware** (v10): single-lang en-primary → `docs/` root; adding the first secondary flips to per-lang, where every language incl. the primary lives at `docs/<code>/`. Computed by `resolve_docs_root` — never a flat `en→docs` literal. Loads `references/pipeline-translate.md` for translate path. Auto-syncs all existing secondary languages after any primary pass promotes (unless `REBUILD_AUTO_SYNC_TRANSLATIONS=0`). |
| `--system-flow` | **[DEPRECATED]** Exact no-op alias for --flows (identical output contract). system-flow.md is now emitted by --flows automatically. Emits a one-time notice `[DEPRECATED] --system-flow folded into --flows` then proceeds exactly as --flows. |
| `--non-interactive` | Suppress the preflight no-match `AskUserQuestion`. When detection matches no profile, silently apply `generic-source` (universal artifacts only, zero extractors) + print `[WARN] non_interactive_fallback`. For CI / `--auto` runs that must not block. Equivalent env var: `REBUILD_NON_INTERACTIVE=1`. |
| `--root` / `--batch` / `--aggregate` / `--emit-manifest` / `--manifest` / `--primary-lang` / `--force-aggregate` / `--digest-collect` | **Multi-component / system-of-systems flags** (monorepo, polyglot). Full per-flag semantics + the driver loop + the Product-group/Reused gates live in `references/multi-component-runbook.md` (loaded on-demand when any of these is set). A genuinely single-component repo never uses them; a multi-executable repo enters them automatically via auto-switch (Preflight 2.5) unless `--mono`. |
| `--mono` | **[v22.0.0]** Force the repo to be treated as ONE monolithic component: suppress the multi-component auto-switch (Preflight 2.5) even when ≥2 components are detected. The escape hatch when you genuinely want a single mono doc set over a multi-executable repo. Sets `detectJson.auto_switch=false`. |
| `--profile <id>` | **[v22.0.0]** Pin the authoritative stack-profile (e.g. `--profile delphi-vcl`) when Delphi+Oracle co-detect and a DB-heavy tree would otherwise make `oracle-plsql` the hit-count `recommended`. Disambiguates the `component_profile` that keys auto-switch + shared-layer exclusion (Finding 2). Also feeds `--legacy` (it already accepted `--profile`). |
| `--legacy` | Reverse-engineering preset for legacy non-web stacks. Sugar over the profile layer — sets NO new pipeline logic. **Additive merge (RT-F15):** (1) resolve the named profile (`--profile <id>` or auto-detect; defaults to the detected legacy profile); (2) `--legacy` then ADDS — it never removes a profile's declared `extractors`, only adds any missing structural extractors — and sets the boolean flags `probe.bootable=false` (skip Wave 0.4) + `re_contract=true` (enforce the RE output contract). Prints `[INFO] legacy_preset_applied`. `--legacy --profile oracle-plsql` → the profile's extractors + RE-contract both active, no duplicate extractors. Profile change with a stale `.rebuild-state.json` from another profile → `[WARN] profile_changed` + stale web-artifacts from the prior profile are no longer surfaced in navigation. |

**Artifact → wave lookup (for `--artifact NAME` — core artifacts only):**

<!-- layout-exempt: artifact→wave table — docs/ paths are rebuild-spec's own targets -->
| NAME | Wave | Upstream required | Pass |
|------|------|-------------------|------|
| `system-overview` | W1 | scout-report.md | core |
| `route-list` | W1 | scout-report.md | core |
| `data-model` | W1 | scout-report.md | core |
| `screen-list` / `screen-flow` | W2 | data-model.md + (route-view: route-list.md \| dfm-form: `_digest_extract_form_nav.json`) — produced whenever `screen_source != none`; route-list.md is NOT a prerequisite for non-web stacks | core |
| `behavior-logic` | W2 | screen-list.md + screen-flow.md | core |
| `permissions` | W3 | screen-list.md + behavior-logic.md | core |
| `user-stories` | W4 | permissions.md | core |
| `feature-list` | W5 | user-stories.md | core |
| `api-map` | W1+W2 | route-list.md + behavior-logic.md | core |
| `entities` / `overview` / `architecture` | W1 | scout-report.md | core |
| `api-contracts` | AC.1 | data-model.md + permissions.md + route-list.md + api-map.md + scout-report.md (run `--api-contracts`) | `--api-contracts` pass |
| `permissions-matrix` / `business-rules` | W3 | behavior-logic.md | core |
| `crud-matrix` | W1.b | `_digest_extract_data_flow.json` (Wave 0.6; profile extractors) | core (stack-specific) |
| `db-objects` | W1.c | `_digest_extract_sql_schema.json` (Wave 0.6; profile extractors) | core (stack-specific) |
| `technical-spec` / `business-context` / `screens` / `edge-cases` | FS.1 | feature-list.md (run `--feature-specs`) | `--feature-specs` pass |
| `process-flow` | FL.1 | docs/features/*/technical-spec.md (run `--flows`) | `--flows` pass |
| `system-flow` | FL.1 | all Tier-1 process-flows (≥2) | `--flows` pass |
| `glossary` | GL.1 | docs/generated/entities.md + docs/features/*/business-context.md (run `--glossary`) | `--glossary` pass |
| `job-list` | J.1 | docs/generated/behavior-logic.md (run `--jobs`) | `--jobs` pass |
| `test-cases` | TC.1 | docs/features/*/{technical-spec,edge-cases}.md (run `--test-cases`) | `--test-cases` pass |
| `design-intent` | D.1 | docs/system/architecture.md + business-rules.md + entities.md (run `--design-intent`) | `--design-intent` pass [EXPERIMENTAL, report-only until `--confirm-promote`] |

## Subagent contracts

**Core pass subagents:**

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| 0 | `/tkm:scan-codebase` | target dirs | `plans/<active>/artifacts/scout-report.md` |
| 0.4 | orchestrator (AskUserQuestion + probe_routes.py) | bootable lockfiles + `probe_gate` state | `_route-probe.json` sidecar + `probe_gate` in `.rebuild-state.json`; HALTS on `awaiting_user` |
| 0.5 | orchestrator (scripts) | scout-report.md + stackNote | `_session-context.md` + `_scout-bl-inventory.md` |
| 1–5 | `researcher` | scout report + template + `code-formats.md` | `plans/<active>/artifacts/<artifact>.md` |
| 1.1 | orchestrator (`validate_route_list.py`) | `route-list.md` | `validation-summary.json`; HALTS before W2 on critical |
| 1.5 | `reviewer` | `data-model.md` only | `data-model-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts W2 on critical |
| 2a.1 | orchestrator (`validate_screen_list.py`) | `screen-list.md` | `validation-summary.json`; HALTS before W2b/W3 on critical |
| 4.5 | `reviewer` | `user-stories.md` only | `user-stories-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts W5 on critical |
| 5.6 | `reviewer` | `feature-list.md` + US### headers + SCR### index | `feature-list-review.md` (frontmatter: `passed`, `issues`, `warnings`); halts core review on critical |
| 7a | `reviewer` | 11 core artifacts + `_scout-bl-inventory.md` + `verification-checklist-core-artifacts.md` | `core-review-report.md` → merged into `review-report.md` + `TaskUpdate(status=completed)` |
| 7.5 | orchestrator (`structural_fixer.py`) | core artifacts + review-report.md | fixed artifacts + `structural-fix-report.json` + decremented review-report |
| 8 | `implementer` | review-report.md + affected core drafts | updated drafts |
| 9 | `promote_drafts.py` + `doc-writer` | approved core drafts | layered paths per `docs-canonical-mapping.md` + `_promoted-sha256.txt` + `wave9-complete.flag`; calls `TaskUpdate(status=completed)` |

**Feature-specs / flows / glossary / jobs / test-cases / design-intent pass subagents** — full per-wave contract tables live in their pass references (loaded on flag, per "On-demand pipeline loading"): `references/pipeline-feature-specs.md` (FS.1–FS.7), `references/pipeline-flows-glossary.md` (FL.1–FL.5 flows + GL.1–GL.3 glossary), `references/pipeline-jobs.md` (J.1–J.5 jobs), `references/pipeline-test-cases.md` (TC.1–TC.5 test-cases), `references/pipeline-design-intent.md` (D.1–D.5 design-intent, EXPERIMENTAL — D.5 promotion is gated behind explicit confirmation, F11b).

**Screen-specs pass subagents (`--screen-specs`; see `references/pipeline-screen-specs.md`):**

| Wave | Subagent | Input | Output |
|------|----------|-------|--------|
| SS.1 | `researcher` (5/batch, batches wave-chained ≤5; standalone) | screen-list.md + data-model.md + screen-spec-template.md + contract | `plans/<active>/artifacts/screens/SCR###_Name/spec.md` |
| SS.2 | `reviewer` (5/batch, batches wave-chained ≤5; standalone) | ScreenSpec batches + `verification-checklist-screen-spec.md` | `screen-review-batch-NN.md` + `TaskUpdate(status=completed)` |

All subagents read `_session-context.md` first; only artifact-specific reads listed in Input column happen afterward.

## Task management

A plan file outlives the session; a task does not. So hydrate each wave as a chain
of tasks, and keep anything that must survive in the plan file.
Where the Task tools are missing — the VSCode extension, for one — fall back to `TodoWrite`.
See `references/pipeline-w0-w5.md` for `TaskCreate` examples.

## Resume & Reconcile

Three defenses against mid-pipeline context loss: (1) **Self-closing subagents** (FS.1, FL.1, GL.1, J.1, TC.1, D.1, W7a, W9) call `TaskUpdate(status=completed)` before returning. (2) **Completion sentinels** — `wave9-complete.flag` (core), `fs7-complete.flag` (feature-specs), `flows-complete.flag` (flows), `glossary-complete.flag` (glossary), `jobs-complete.flag` (jobs, F9 — `expectedOutput` = `docs/generated/job-list.md`), `test-cases-complete.flag` (test-cases, F9 — `expectedOutput` = per-feature `docs/features/{slug}/test-cases.md`), `design-intent-complete.flag` (design-intent, F9/F11b — EXPERIMENTAL: `expectedOutput` = the PLAN-DIR draft `plans/<active>/artifacts/design-intent.md` until a user-confirmed D.5 promote; `docs/system/design-intent.md` is NOT required for this pass's reconcile to consider it complete) are disk-level truth per pass. (3) **Reconcile preflight** — on every invocation, closes `in_progress` tasks whose expected output already exists on disk. For Wave 9 (core): checks flag OR all core docs promoted (no feature dirs required — v5.0.0). `--resume` runs preflight only. For FS.1 per-feature tasks, reconcile checks 4-file completeness + no `.pending`; partial output stays `in_progress`.
See `references/pipeline.md` → "Reconcile pattern" for `TaskList`/`TaskUpdate` examples.

## Edge Cases

- **Route probe requires user-confirmed bootability (Known Limitation):** The Tier-1 CLI probe cannot run autonomously — it requires the user to confirm the app is bootable. If the user must install dependencies first, the pipeline halts with a checkpoint (`probe_gate.status = "awaiting_user"` written to `docs/.rebuild-state.json`). Re-run `/tkm:rebuild-spec --artifact route-list` to resume at the gate; scout output is reused, no re-scan. WARNING: do NOT commit lockfile/dep churn from local setup to the repository.
- **`probe_gate` persists in `.rebuild-state.json`:** The `probe_gate` field survives session end. On `--artifact route-list` re-runs with a prior `passed`/`skipped` probe_gate, the sidecar manifest is reused without re-prompting. `--full` re-prompts and re-probes fresh **only when a bootable stack is detected or `--probe-routes` is passed** (pipeline condition: `(hasBootableStack || explicitProbeRoutes) && (!priorProbeGate || --full)`). On a non-bootable, non-flagged repo `--full` does not trigger the probe gate. A stale `awaiting_user` gate is cleared automatically on successful or declined probe.
- **Orphan `.pending` marker** → FS.1 partial: 4-file write incomplete OR researcher did not remove the marker on success. FS.5 emits `MISSING` for that fcode, FS.7 pre-flight gate blocks promotion. Recovery: rerun FS.1 for the affected fcode OR (after manually verifying all 4 files are complete) remove `.pending` and rerun FS.5. See `references/canonical-fcode-schema.md § Folder Lifecycle` + `references/verification-checklist-universal.md § Pending Marker Rule`.
- **Validator FAIL at W5.5** → orchestrator HALTS before core review (folder/slug drift). Unconditional — no env var, no opt-in.
- **Validator FAIL at FS.2** → orchestrator spawns `implementer` fix per failed F###; after 2 failed cycles escalate to fresh `researcher` re-draft. Unconditional.
- **Empty codebase** → ABORT at preflight; no placeholder docs.
- **Scaffold-only repo** (lockfile present but no source files) → preflight passes lockfile check but Wave 0 scout returns near-empty report. Researcher MUST write "No data" markers per artifact rather than fabricate content.
- **FeatureList has 0 F### codes** → core pass proceeds; `--feature-specs` warns and exits with 0 features.
- **Reviewer fails after 3 cycles** → escalate, leave drafts in `plans/<active>/artifacts/`, do NOT promote.
- **Subagent timeout (>15 min)** → re-run pre-gen estimate (`estimate_artifact_loc.py`); if `shard:true`, retry via chunked path (shell→fan-out→merge) instead of monolithic re-run. If a chunked run had a partial fragment timeout, re-dispatch ONLY the missing fragment then re-merge (idempotent — rebuilds whole file, no dup sections). Non-shardable artifact: retry once, then `TaskUpdate` failed; user decides resume.
- **Session context exhausted mid-pipeline** → tasks may remain `in_progress` despite output files existing on disk. Next invocation runs reconcile preflight (see Resume & Reconcile) to close them. Subagents self-close on the critical final wave to minimise orchestrator-liveness dependency.
- **Small codebase (screens < 30)** — W2a + W2b merged into single Wave 2 task (env: `REBUILD_W2_MERGE_THRESHOLD`; default 30).
- **GLOBAL PARALLEL CAP (v25.1.0, hardened v25.1.1):** `REBUILD_MAX_PARALLEL` (default 5) — never more than 5 subagents runnable at once, across the ENTIRE flow and every pass (core, feature-specs, screen-specs, flows, jobs J.1, test-cases TC.1, translate, aggregate, fix cycles). Enforcement pattern = **bounded-wave dispatch**: whenever a pass creates more than 5 sibling tasks, chunk them into waves of ≤`REBUILD_MAX_PARALLEL` and chain each wave on ALL task ids of the previous wave via `addBlockedBy`. This env IS read by the wave-rotation pseudocode (FS.1/FS.5/SS.1/SS.2, aggregate) — wave width is always `min(<per-pass batch env>, REBUILD_MAX_PARALLEL)`, so raising a batch-size env (workload per agent) can never widen concurrency past the cap. Do not raise `REBUILD_MAX_PARALLEL` above 5 without also verifying rate-limit headroom. Core Wave 1 additionally chains Wave1.c db-objects behind Wave1.b crud-matrix so legacy profiles (6 Wave-1 artifacts) stay ≤5.
- **FS.1 fan-out** → ALWAYS bounded (env: `REBUILD_FS_BATCH_SIZE`; default 5; legacy `REBUILD_W6_BATCH_SIZE` honored as a deprecated alias): ≤20 F### = one researcher per feature dispatched in chained waves of ≤5 (every task of wave i+1 `addBlockedBy` ALL tasks of wave i); >20 F### = batch tasks of 5 features each, chained sequentially — bounds peak context and rate-limit pressure. FS.5 reviews feature specs 5/reviewer, reviewer tasks themselves wave-chained at ≤5, after all FS.1 tasks complete. Core W7a reviews core artifacts independently.
- **W8 parallel cap:** `REBUILD_W8_MAX_PARALLEL=5` — max parallel W8 implementer tasks per fix cycle (default 5). **Clamped by the global cap** (effective width = `min(REBUILD_W8_MAX_PARALLEL, REBUILD_MAX_PARALLEL)`, applied in W8/FS.6/FL.4) — fix cycles are not exempt.
- **Shard parallel cap:** `REBUILD_SHARD_MAX_PARALLEL=5` — max parallel fragment researchers per shard batch (default 5). Clamped by the global cap in AC.1. Mirrors `REBUILD_FS_BATCH_SIZE` / `REBUILD_W8_MAX_PARALLEL` conventions. Used when pre-gen estimate triggers chunked artifact generation (`--api-contracts` may shard for large API surfaces; core artifacts shard when exceeding `docs.maxLoc`).
- **Env hygiene (v25.1.2):** every cap env parse guards junk values — `Math.max(1, parseInt(env ?? '5') || 5)` — so NaN/`0`/negative degrades to the default instead of silently disabling wave rotation (a broken env must never mean unbounded fan-out).
- **PASS one-liner format** — reviewer reports use `✓ <rule_id> @ <fcode>` line format under `## Passed Checks`. W7-merge rolls up consecutive same-rule fcodes into ranges.
- **Incremental mode (v3.1.0+)** — auto-engaged when `docs/.rebuild-state.json` present. Diffs source since last SHA; maps changed files to cascade chain (route/model → full W1→W5; screen/bg/perm → truncated chain; other → core review only). Only affected core waves dispatched. Feature-specs, flows, and glossary passes have their own per-pass cursors. Override: `--full`.
- **First-run guard** — incremental on fresh repo (no `docs/.rebuild-state.json`) → auto-fallback to full silently (no abort).
- **Manifest change** (package.json, composer.json, etc.) → auto-fallback to full.
- **Diff threshold** — diff > 30% of source files → auto-fallback to full (env: `REBUILD_INCREMENTAL_THRESHOLD`).
- **Unowned new source file** — new file not in scout-report → fallback full (FeatureList may be stale).
- **OOB edit detected** — a layered `docs/` artifact (`docs/generated/<artifact>.md`, `docs/system/<artifact>.md`) hand-edited between runs → `[OUT_OF_BAND_EDIT]` warning (non-blocking).  <!-- layout-exempt: OOB detection — docs/ paths are rebuild-spec's own managed artifacts -->
- **A1 confidence-report companion absent (v25.2.0, non-gating):** `incremental_planner.py`'s `_detect_confidence_report_missing()` scans core/feature/screen artifacts on every planner invocation, alongside (but structurally independent of) the OOB-edit scan below — a primary artifact present on disk whose `confidence-report_<stem>.md` sidecar is missing (pre-A1 corpus, or a prior best-effort write failure) prints `[CONFIDENCE_REPORT_MISSING] <artifact path>` to stderr. Unlike `[OUT_OF_BAND_EDIT]`, this NEVER feeds `_build_payload()` and NEVER triggers a fallback-to-full — print-only, zero effect on mode/exit code. See `references/confidence-report-contract.md`.
- **A3/B4 absent on an un-migrated spec (v26.0.0, WARN-first):** `validate_reading_guide_db_impact.py` (wired at FS.2) WARNs `reading_guide.pre_migration` / `db_impact.pre_migration` and exits 0 — never blocks a build. Run `migrate-reading-guide-db-impact.py --docs-root docs/` (or `docs/<lang>/`) to enumerate which specs still need a researcher re-run (it cannot backfill the content itself). A present-but-empty or non-table B4 body is real drift → CRITICAL, unlike the absent case.
- **Empty cascade** (all `other`-type files) → no core waves dispatched (only affected feature specs via reverse-index on `--feature-specs` pass).
- **v2.x upgrade** — `docs/specs/` present without `.rebuild-state.json` → orchestrator offers bootstrap prompt (Wave -2); user can pick fast-incremental (with hand-edit caveat) or safe-full path. If `git log` returns no SHA for `docs/specs/` or derived SHA = HEAD, bootstrap is skipped silently.
- **`--full` + `--since` mutually exclusive** → exit 2 with error.
- **Wave -1 hydrate** — copies non-affected artifacts from the layered `docs/` paths (`docs/system/`, `docs/generated/`, `docs/features/`, `docs/flows/`) to `plans/<active>/artifacts/` so downstream waves (reconcile, reviewer) see complete context.  <!-- layout-exempt: hydrate step — docs/ paths are rebuild-spec's own managed artifacts -->
- **Language-adaptive scanning scope**: Wave 0 scout detects project language from manifest files and outputs flat file inventory + scanned dirs. Wave 2 follows imports one level deep using language-specific mechanisms (see `references/pipeline-w0-w5.md` W2 task for full rules). Reviewer cross-validates via scout-report.md inventory — no hardcoded extension globs. If scout-report.md absent (`--artifact` entry point), content-completeness check is skipped with a warning. Pure UI/presentational components with no service calls are automatically compliant. Known limitation: barrel/re-export files (e.g. `index.ts`) re-exporting at depth 2 are not followed — flagged `[BARREL_IMPORT]` advisory.
- **REG### scoping**: every REG must have parent SCR in same ScreenList. Orphan REG (no parent SCR) → critical.
- **REG nesting**: forbidden. REG inside REG → critical.
- **Mutually-exclusive tab content** → SCR variants (SCR###a/b), NOT REG (H4 short-circuit; hard rule).
- **Wizard/stepper content** → H5 sub-classification: Case A (distinct UI+validation+action per step) → SCR variants. Case B (shared state/endpoint, visual phases) → composite SCR + child REGs. Default for ≥3-step wizards: Case B. Case A requires cited evidence. 2-step wizards: always Case B.
- **W1 researchers (SystemOverview, RouteList, DataModel) MUST NOT emit REG###.** REG### first appears in W2 ScreenList.
- **Partial-screen ownership**: F### with SCR###/REG### ref owns REG only, not the parent SCR. Screen shell must be owned by a separate F### with bare SCR### ref.
- **Region independence signals**: REG### is justified by any ≥1 of — distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Shared initial payload alone does NOT disqualify a split (see verification-checklist Trap 1 + Trap 3).
- **Feature specs (v4.0.0 — 4 audience-aware files per feature):** `technical-spec.md` (FR/BR/SM/ALG/INT/SC codes under `## Cross-Cutting Logic`; `## Polymorphic Behavior`; `## Key Entities`; `## Artifact References`); `business-context.md` (plain-language: `## Why It Matters`, `## Who Uses It`, `## What They Do` — no technical tokens); `screens.md` (`## Screen List`, `## User Journey`); `edge-cases.md` (table with Scenario/What Happens/User-Facing Message). `## Artifact References` replaces legacy two-section format — CRITICAL immediately on legacy. See `templates/technical-spec-template.md` + `templates/business-context-template.md`.
- **Decision Logic (DEC-###, v3.2.4+):** `feature-spec.md` now includes `## Cross-Cutting Logic > ### Decision Logic` — captures user-facing decisions with business-outcome scope (source-location-agnostic: component, saga, controller all valid Sources). 3 subtypes: `render`, `interaction`, `flow`. `user_visible_outcome` field required per DEC. Lazy-N/A and structural correctness enforced by `validate_feature_spec.py`. W7h reviewer rule covers semantic validation.
- **Flow slug collision (FL.1):** researcher emits slug matching existing `flows/` file → suffix `-2`; emit `[WARN] flow_slug_suffixed`. If existing file has `status: human-curated`, skip with `[INFO] flow_preserved`.
- **Partial FS.1 output (1-3 of 4 files missing):** treated as orphan `.pending` — researcher MUST NOT remove `.pending` until all 4 files (`technical-spec`, `business-context`, `screens`, `edge-cases`) exist and are non-empty.
- **DISC-### scope (v3.2.4+ updated D6):** DISC-### is for enum discriminators only — ≥2 distinct values with different behavioral outcomes. Boolean fields (`true`/`false` only) belong in Business Rules, NOT DISC. `validate_feature_spec.py` warns on boolean DISC entries (`FeatureSpec.disc_boolean`). Clean boundary: multi-value enum → DISC; boolean flag → BR; multi-predicate / interaction / flow → DEC.
- **Legacy plan layout (pre-v4.0.0):** `artifacts/features/{slug}/spec.md` detected → emit `[INFO] legacy_plan_detected`. Recommend `rm -rf artifacts/features/ && --features <all F###>` to regenerate. No auto-migration.
- **Output language — first run sets primary (v5.1.0):** `--lang vi` on a fresh repo → vi IS the primary, generated inline from source (no "run English first" step). A later `--lang jp` translates FROM vi. The primary language is recorded in `state.primary_lang` (set once, first run). Default (no `--lang`) → primary=en. Dispatch: `eff_lang == primary_lang` → inline generation (Path A); else → translate-from-primary (Path B). **Location is mode-aware** (v10, via `resolve_docs_root`): single-lang en-primary → `docs/` root; per-lang (≥1 secondary registered, or the `docs/<primary>/.layout-migrated` sentinel present) → `docs/<lang>/` for every language incl. the primary. The first secondary on an en-primary-at-root repo triggers a one-time atomic flip `docs/` → `docs/en/` (`migrate_docs_layout.py`). English skeleton (headings, code tokens, field labels, table headers, fenced code, frontmatter) preserved in ALL languages so existing validators run unchanged.
- **Auto-sync secondary languages (v5.1.0):** After ANY primary pass promotes, orchestrator automatically re-translates changed artifacts into every existing secondary mirror (`state.translations` keys). Scoped to the pass's changed artifacts only (not full re-translate). Failure of one language's sync is isolated: warn + leave stale + continue others; primary pass stays success. Env opt-out: `REBUILD_AUTO_SYNC_TRANSLATIONS=0` (writes `translation-stale.json` + handoff instead).
- **Outdated translation guard:** `--lang L` (secondary) when primary SHA moved ahead of `translations[L].translated_from_sha` → `[WARN] primary_ahead_of_translation` + recommendation. Proceeds (non-blocking).
- **Missing primary guard:** `--lang L` (secondary) but no primary docs exist → `"No <primary_lang> primary to translate from; run /tkm:rebuild-spec first"` + stop. Defensive; should be unreachable via normal dispatch.
- **Skeleton-identity validator:** `validate_translation_skeleton.py` checks that mirrors preserve the English skeleton byte-identical (headings, code tokens, field labels, table headers, fenced code, frontmatter) AND that the translated prose body stays within ±30% of the source body (catches dropped/padded paragraphs). CRITICAL on any drift. Replaces re-running full validators on mirrors.
- **Translation worker = Haiku:** the translate fan-out (TR.2/TR.3/auto-sync) runs on the `translator` agent (`model: haiku`); the two gates above are the quality net. Bound by the agent def, not a prose directive.
- **Translation scope = rebuild-spec only:** other skills don't translate. In per-lang mode the layered docs root is mode-aware kit-wide (see `_shared/docs-canonical-mapping.md` § Language layout); manage-docs **narrative** files (`project-roadmap.md`, `code-standards.md`, `system-architecture.md`, `deployment-guide.md`) stay English at `docs/` root (documented carve-out).

## Output

<!-- layout-exempt: output section — all docs/ paths are rebuild-spec's own promote targets -->
- Persistent:
  - `docs/system/{overview,architecture,glossary,permissions,business-rules}.md` — curated
  - `docs/generated/{route-list,api-map,permissions-matrix,entities,user-stories,feature-list}.md` — raw
  - `docs/generated/{crud-matrix,db-objects}.md` — extractor-digest-derived (stack-specific; produced when the profile's `extractors` run — Delphi/Oracle). CRUD matrix = feature×table C/R/U/D; DB-object catalog = tables/views/procs/sequences/triggers.
  - `docs/flows/<slug>.md` — AI-drafted cross-feature flows
  - `docs/features/<slug>/{technical-spec,business-context,screens,edge-cases}.md` — per feature (4 files)
  - `docs/decisions/ADR-*.md` — human only
- Drafts + reports: `plans/<active-plan>/artifacts/` (kept for audit).
- **Navigation layer (v11.2.0, updated v15.0.0; v24.0.0 extends to feature-/screen-specs):** at the END of
  a completed pass the orchestrator runs `scripts/build_navigation.py --pass-complete` — **every** pass that
  writes to `docs/` (core W9.6, **feature-specs FS.7, screen-specs SS.3**, and per-lang mirrors via translate
  Step 3.5), so the just-promoted `features/F###/` + `screens/SCR###/` dirs immediately surface in the
  reading-order README, the per-feature READMEs, and the features index → a `README.md` per `docs/` subdir (2-zone: only the
  region between `<!-- generated by rebuild-spec navigation -->` and `<!-- end-generated -->` is
  rewritten; user content below `end-generated` is preserved). **Root README behavior (v18.0.0):** in
  per-lang mode there is **no top-level `docs/README.md`** — a purely-generated root README is removed
  and a hand-written one is left untouched; the single entry point is `docs/<primary>/README.md`
  (was a ~3-line pointer in v15-v17). Single-lang behavior is unchanged. **DOCUMENT-MAP
  removed (v15.0.0):** `build_navigation.py` no longer writes `docs/DOCUMENT-MAP.md` or
  `docs/DOCUMENT-MAP.draft.md` (was write-only; no reader; machine state lives in `docs/.rebuild-state.json`).
  `META_FILES` still recognizes both names so migration deletes any stale copies on next run. `--pass-complete`
  is retained as an accepted no-op argument for backward compatibility. **Per-lang `components/` placement (v23.0.0 — single-source translate model):**
  component docs are written ONCE to the language-resolved source root: `docs/components/<name>/`
  for en single-lang; `docs/<primary>/components/<name>/` for non-en or per-lang repos.
  `resolve_component_paths` passes `primary_lang` to `resolve_docs_root` — the same resolver used
  by core/system artifacts. Secondary-lang component docs (`docs/<L>/components/<name>/`) are
  produced by the translation pipeline (`--lang <L> --root <name>`) and auto-synced on change;
  there is NO derived-view projection. The nav pass generates READMEs at the resolved component
  path. All writes go through `_resolve_guarded` (RT-F14). See `docs/decisions/ADR-0003`.
- Journal: auto-invoke `/tkm:write-journal` on completion (optional — skip silently if skill unavailable).

## References

- `references/stack-profiles/_schema.md` — stack-profile data schema (detection globs, source encoding, artifact map, extractor allowlist, trust boundary). `scripts/detect_stack_profile.py` + `scripts/_stack_profile_lib.py` load/match/validate; preflight resolves a profile here (ask-don't-abort).
- `references/multi-component-runbook.md` — multi-component / system-of-systems **runbook**: the `--emit-manifest`→`--batch`→`--aggregate` driver loop (incl. Step 1b per-pass auto-loop), the Product-group / Reused sub-root gates, the v18 scout-report→template→author flow (Step 3) + the review→fix→promote gate (Step 3.5), and the multi-component flag table (`--root`/`--batch`/`--aggregate`/`--emit-manifest`/`--manifest`/`--primary-lang`/`--force-aggregate`/`--digest-collect`). Load when any multi-component flag is set. Synthesis internals live in `system-synthesis-contract.md`.
- `references/system-synthesis-contract.md` — system-of-systems synthesis: neutral-digest schema, per-stack adapter convention (`scripts/_topology_adapter_{spring,nestjs,go}.py` + `extract_service_topology.py`), entity-correlation algorithm (independent heuristic, all-`[UNVERIFIED]` + consent gate, glossary as OUTPUT), Markdown-sanitize + Mermaid-injection + config credential-scrub gates, language-mapped output path + auto-migration, the v19 **scanner-only scout-report→author→review→promote** contract (Python emits FACTS data only — no Mermaid, no documents; the system-researcher CREATES the drafts and authors prose+tables+Mermaid after reading each component's docs; fidelity via review gate + a Mermaid-safety lint), run model (`--emit-manifest`/`--batch`/`--aggregate`, `_components_manifest_lib.py` atomic+lock). Synthesis: `scripts/synthesize_system.py` (+ `_system_synthesis_lib.py`, `_synthesis_scout_lib.py`, `_synthesis_render_lib.py`, `_synthesis_narrative_lib.py`, `_nav_metadata_lib.py`).
- `references/system-researcher-contract.md` — the **system-researcher** authoring contract (v18): inputs (scout report + templates + each component's docs), the 6 authored artifacts, the **[CRITICAL] read-the-components'-docs / never-declare-"unobserved"-blind** rule (`SY-R8`), fidelity rules (embed pinned `{{SCOUT}}` blocks verbatim), wording rubric, and reuse/update behaviour. Injected into the Step 3 researcher prompt.
- `references/verification-checklist-system-synthesis.md` — semantic review rules (`SY-R1..SY-R7`) for the aggregate review stage (Step 3.5): loaded ONLY by the `reviewer` that gates the 5 hybrid artifacts (overview / component-catalog / architecture / glossary / cross-service-flows) before promote. Mechanical artifacts are not reviewed.
- `references/re-output-contract.md` — RE-mode provenance contract (citation-mandatory + `[UNVERIFIED]` + citation-density check); active when `profile.re_contract` or `--legacy`. `scripts/build_navigation.py` (README per dir; v15.0.0: DOCUMENT-MAP generation removed) + `scripts/_path_lib.py` (`_resolve_guarded`, shared write-safety). `validate_source_citations.py --re-mode` runs the density check.
- `references/structural-extractor-contract.md` — Wave 0.6 structural-extractor plug-point: digest schema, `extract_sql_schema.py`/`extract_data_flow.py` (+ `_sql_parse_lib.py`/`_sql_dml_lib.py`/`_extractor_lib.py`), credential scrub (RT-F7), parse-coverage/dynamic-SQL (RT-F8), regex safety (RT-F9), identifier sanitize (RT-F10), checkpoint/manifest/stale (RT-F11). Drives `crud-matrix.md` + `db-objects.md`; validators `validate_crud_matrix.py` + `validate_db_catalog.py`.
- `references/code-formats.md` — F###/US###/SCR###/BL###/PERM### schema + valid criteria
- `references/verification-checklist-universal.md` — universal rules + Pending Marker Rule
- `references/verification-checklist-core-artifacts.md` — W7a core artifact rules (11 artifacts + Composite Detection)
- `references/verification-checklist-feature-spec.md` — FS.5 feature spec rules (Deterministic Validator Coverage + Failure Trap)
- `references/verification-checklist-screen-spec.md` — SS.2 screen spec rules
- `references/verification-checklist-quality-gates.md` — W4.5 / W5.6 targeted gates
- `references/pipeline.md` — wave dep graph, wave -2/planner/branch-on-mode, reconcile pattern, artifact paths (always loaded)
- `references/pipeline-w0-w5.md` — W0–W5 dispatch bodies (load before W0–W5)
- `references/pipeline-w5x-w6.md` — W5.5 feature existence gate + W5.6 FeatureList quality gate (load before those waves)
- `references/pipeline-w7-w9.md` — W7a/W7.5/W8/W9 core review/fix/promote dispatch bodies (load before those waves)
- `references/pipeline-feature-specs.md` — Feature-specs pass FS.1–FS.7 (load when `--feature-specs` or `--features` flag set)
- `references/pipeline-flows-glossary.md` — Flows pass FL.1–FL.5 + Glossary pass GL.1–GL.3 (load when `--flows` or `--glossary` flag set)
- `references/pipeline-jobs.md` — Jobs pass J.1–J.5 (load when `--jobs` flag set); `references/jobs-researcher-contract.md` — J.1 mandatory rules (read-only static scan, F7); `references/verification-checklist-jobs.md` — J.3 semantic rules (JOB-S1..JOB-S6)
- `references/pipeline-test-cases.md` — Test-cases pass TC.1–TC.5 (load when `--test-cases` flag set); `references/test-cases-researcher-contract.md` — TC.1 mandatory rules (UT/IT vs UAT citation-source split); `references/verification-checklist-test-cases.md` — TC.3 semantic rules (TC-S1..TC-S6)
- `references/pipeline-design-intent.md` — Design-intent pass D.1–D.5, EXPERIMENTAL/report-only (load when `--design-intent` flag set); `references/design-intent-researcher-contract.md` — D.1 mandatory rules (ADR-first source order, citation-or-`[INFERRED]` gate, non-duplication boundary); `references/verification-checklist-design-intent.md` — D.3 semantic rules (DI-S1..DI-S6); `scripts/validate_design_intent_density.py` — D.2 mode-agnostic citation-density gate (F11c)
- `references/pipeline-screen-specs.md` — Screen-Specs pass SS.1–SS.3 (load when `--screen-specs` flag set)
- `references/feature-spec-researcher-contract.md` — FS.1 mandatory rules; `references/bl-source-patterns.md` — per-stack BL file patterns (10 stacks incl. systemd-timer, Mode A+B)
- `references/spec-authoring-contract.md` — takumi greenfield spec authoring rules (draft frontmatter, authoring-mode inputs, gap schema, screen-spec scope, state-registration handoff)
- `references/spec-stage-procedure.md` — shared Stage 1.5 spec-authoring orchestration; consumed by takumi Stage 1.5 + tkm-plan spec gate. Step 0: enumerate-first scope assessment — (B) CLOSED conjunction smell-flag (ALWAYS-fire → force SYSTEM; NEVER-fire CRUD pairs → enumerate; gray zone → enumerate) then (A) intent enumeration (count ≥2 → SYSTEM default; =1 → SINGLE; `--fast` → always SINGLE). Emits `plans/<plan_dir>/spec/.intent-enum.json` as chokepoint artifact. Steps 0a–0b: feature-list draft + quality gate (SYSTEM only). Rest Point 1.5a: confirm feature set (BLOCKING incl. `--auto`). Steps 1–2.5: slug resolution, researcher fan-out, shape verification. Step 3: gap clarification + approval gate.
- `references/process-flow-researcher-contract.md` — FL.1 process-flow synthesis contract
- `references/canonical-fcode-schema.md` — fcode JSON schema + slug grammar + folder lifecycle; `references/incremental-state-schema.md` — state/index/plan JSON schemas
- `scripts/incremental_planner.py` — cascade-aware incremental planner (decision oracle for selective dispatch)
- `scripts/build_source_to_fcode.py` — per-pass reverse-index + state emitter; `--cursor` arg controls which state cursor is advanced (core: `last_rebuild_sha`; feature-specs: `last_feature_spec_run_sha`; flows: `last_flows_run_sha`; glossary: `last_glossary_run_sha`; jobs: `last_jobs_run_sha`; test-cases: `last_test_cases_run_sha`; design-intent: `last_design_intent_run_sha`, advanced ONLY at D.5 post-confirmation)
- `references/pipeline-translate.md` — Translate pass TR.0–TR.5 + auto-sync entry. Auto-sync now driven by `scripts/translation_sync_gate.py` (plan + finalize modes); handoff line emitted by script, not LLM. Load when `--lang` targets a secondary language, OR on any primary pass when `translations` in state is non-empty — see On-demand pipeline loading.
- `references/translation-contract.md` — Subagent rules for prose-only translation with skeleton preservation
- `scripts/validate_translation_skeleton.py` — Skeleton-identity + ±LOC body-ratio validator for translation mirrors
- `scripts/_lang_lib.py` — Language resolution helpers (`normalize_lang` w/ ISO alias de-aliasing, `resolve_docs_root` mode-aware, `detect_layout_mode`, `looks_unusual`)
- `scripts/migrate_docs_layout.py` — one-time single-lang→per-lang docs flip (`docs/`→`docs/<primary>/`), atomic+idempotent (sentinel + lock); `--rollback`, `--rename-alias jp:ja`
- `scripts/check_layout_paths.py` — recurring guard: fails on hardcoded `docs/system|features|generated|flows` without a `layout-exempt` annotation
- `agents/translator.md` — Haiku-bound prose-only translation worker (TR.2/TR.3/auto-sync)
- `scripts/` — deterministic validators (`validate_feature_existence.py`, `validate_feature_spec.py`, `validate_source_citations.py`, `validate_process_flow.py`, `validate_feature_screen_link.py` — v24 feature↔screen ID-link, WARN-capable, `validate_feature_api_link.py` — v25 feature↔API/route ID-link + twin-consistency, WARN-capable); shared libs (`_slug_lib.py`, `_summary_lib.py`, `_layout_lib.py`, `_nav_table_parse_lib.py`, `_route_link_lib.py`, `_nav_route_lib.py`); migration: `migrate-behavior-logic-rename.py`, `migrate_docs_layout.py`, `migrate-feature-screen-ids.py` (v24 SCR###-column + Feature backlink), `migrate-feature-api-ids.py` (v25 ROUTE###-column + Owner F### backfill); stdlib-only, no pip
- Canonical docs mapping: `claude/skills/_shared/docs-canonical-mapping.md` — single source of truth for topic → file ownership, stub rule, surgical-edit policy
