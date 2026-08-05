<!-- layout-exempt: rebuild-spec CHANGELOG — historical version notes; every docs/system|features|generated|flows path here is this skill's own output target, not a consumer assumption -->

# tkm:rebuild-spec — Changelog

Version history for the `rebuild-spec` skill. Current behavior is documented in `SKILL.md`;
this file holds the migration notes and breaking-change rationale for past versions. The most
recent sessions are also captured in `docs/journals/`.

---

## v26.4.0 — Tracks B/C/D: CICS BMS + COBOL CRUD/datasets + generic ui-sniff fallback (additive)

**Minor (additive)** — completes the COBOL initiative started at `v26.3.0` (Track A): CICS BMS
screen extraction, COBOL file-I/O + EXEC SQL CRUD extraction, and a generic content-sniff
fallback for ANY unrecognized stack (not COBOL-specific). No existing profile's behavior
changes; no migration script; no `metadata.json` deletions (nothing renamed/removed).

### Added — Track B: CICS BMS screens
- `_cobol_bms_lib.py` + `_cobol_bms_grammar_lib.py` — fixed-column HLASM/BMS macro tokenizer
  (DFHMSD/DFHMDI/DFHMDF), MAPSET→source-file index (keyed by the `DFHMSD` label, never by
  filename), `EXEC CICS SEND/RECEIVE MAP` reachability join (across both BMS-macro-shaped
  files and ordinary COBOL calling programs that only reference a map), conditional-assembly
  guard (`AIF`/`AGO` spans exclude their fields from emission entirely rather than fabricating
  merged geometry), symbolic-copybook-only fallback, `mapset_undefined` WARN. Flows through
  the SAME `cobol-screen` router and screen validators Track A shipped — mixed
  SCREEN-SECTION+BMS repos need no `--profile` pin.

### Added — Track C: COBOL CRUD / datasets
- `extract_cobol_data.py` + `_cobol_data_lib.py`/`_cobol_verb_lib.py`/`_cobol_sql_lib.py` —
  file-I/O verb → CRUD classification (WRITE→C, READ→R, REWRITE→U, DELETE→D) with
  OPEN-mode/ACCESS-mode/prior-READ state tracking (illegal-for-mode → WARN, never a false
  classification); `EXEC SQL...END-EXEC` pass (dialect-agnostic DB2/Pro*COBOL shape, cursor
  DECLARE/OPEN/FETCH/CLOSE, dynamic SQL → `[UNVERIFIED]`, never a fabricated table).
- `db_objects.kind` gains `"dataset"` (flat-file/VSAM COBOL data store) alongside the
  existing `"table"` — both `VALID_KINDS` and `SECTION_KIND_MAP` extended (the latter is the
  actual gate; `## Datasets` rows would otherwise be silently dropped) + a `## Datasets`
  section added to the db-object-catalog template.
- `cobol.json`: `crud-matrix`/`db-objects` flipped `skip`→`produce`, `extract_cobol_data`
  added to `extractors` — a real COBOL run now produces cited CRUD/db-objects artifacts.

### Added — Track D: generic content-sniff fallback (any unrecognized stack)
- `_content_sniff_lib.py`/`_content_sniff_signals_lib.py` — stdlib-only UI-evidence scan for
  a repo NO stack-profile recognizes: 9 signal families (C/Python/Perl/Java/VB6/TUI/shell/web
  CGI/COBOL-ish), a menu-loop structural detector, 3-tier confidence (0 silent / 1
  metadata-only / 2 cited-and-gated), false-positive guards, a generic-secret scrub
  (independent of `_sql_parse_lib`'s SQL-shaped scrub — this domain's secrets are CLI flags
  and env-var fallbacks, not connection strings).
- `detect_stack_profile.py`: new advisory `ui_sniff` key (root-level + per-component, only
  computed on a no-match — zero cost on any recognized stack); `SCHEMA_VERSION` → `22.1.0`.
- Preflight step 2 (SKILL.md): a Tier-2 verdict surfaces a 4th, cited, delimited option
  alongside the existing 3 — on ACCEPT, `_ui_sniff_accept_lib.py` builds a sparse
  `_digest_extract_ui_sniff.json` (every entry `unverified: true`) and a session-scoped
  profile override (`screen_source: "ui-sniff"`, never written to a kit profile file) that
  the EXISTING screen-production pipeline consumes unchanged. Non-interactive mode logs
  `[WARN] ui_sniff_tier2` and never prompts. Tier 0/1 → unchanged 3-option flow.
- **Accepted risk:** the content-sniff signal library is research-backed but not yet
  validated against a second real "unclear stack" corpus (none was available this session) —
  ships speculative v1, retune after real usage surfaces false positives/negatives.

### Notes
- Two-release COBOL rollout: `v26.3.0` shipped Track A (SCREEN SECTION) standalone so the
  user's confirmed priority didn't wait on the more speculative Tracks B/C/D; this release
  completes the set.
- Real anonymized fixtures for Tracks A/B (`tests/fixtures/cobol_real_sample/`,
  `tests/fixtures/cobol_screen_section/`, `tests/fixtures/cobol_mixed/`) were sourced from
  the user's actual AcuCOBOL/Micro Focus target repo per this initiative's validated
  fixture-sourcing decision; Track B (CICS BMS) and Track D fixtures are synthesized (the
  confirmed real target uses SCREEN SECTION, not mainframe CICS, and no second
  unrecognized-stack repo was available).

---

## v26.3.0 — Track A: COBOL SCREEN SECTION screen extraction (additive, standalone release)

**Minor (additive)** — brand-new `cobol` stack-profile + SCREEN SECTION screen extraction,
released as its own unit ahead of the full COBOL initiative's remaining tracks (CICS BMS,
CRUD/data extraction, generic-content-sniff fallback — those land together in a later MINOR).
No existing profile's behavior changes; no migration script. (Version note: `v26.2.0` is
already claimed by an unmerged `--package`/diagram-export branch in this repo's history — this
release takes the next free MINOR, `v26.3.0`, to avoid a future collision when that branch
lands.)

### Added
- New `cobol` stack-profile (`references/stack-profiles/cobol.json`) — detects `*.cbl`/`*.cob`/
  `*.cpy`/`*.bms`, `screen_source: "cobol-screen"` (screens-only at this release: crud-matrix/
  db-objects stay `skip` until the CRUD extractor ships).
- `extract_cobol_screen.py` — the COBOL screen router: macro-shaped anchored-regex dispatch
  (BMS-macro-shaped or `EXEC CICS SEND/RECEIVE MAP`-referencing files vs. `SCREEN SECTION`
  files, both-match merge), accumulate-then-`finalize()` contract, per-file byte cap,
  post-decode EBCDIC/binary sanity guard, exit-0-always.
- `_cobol_screen_section_lib.py` — SCREEN SECTION parser: `01`-level record → screen,
  ACCEPT/DISPLAY reachability + entry citation, PERFORM-chain flow edges (Delphi form-nav
  shape), `COPY` resolution against a bounded, realpath-containment-checked in-repo index
  (unresolved/escaped → `unverified` + cited, never a crash).
- `screen-list`/`screen-flow` validators extended (additive) to accept `screen-section` /
  `cics-bms` / `ui-sniff` screen kinds and COBOL source citation extensions.

### Notes
- The router's CICS BMS extraction path (`_cobol_bms_lib.py`) and the CRUD/data extractor
  already exist in this tree (built for engineering-parallelism reasons) but are not yet wired
  into `cobol.json`'s `produce`-declared artifacts — no artifact is declared `produce` whose
  extractor isn't live at this release. They ship in the next MINOR alongside the generic
  content-sniff fallback.
- `_stack_profile_lib.SCHEMA_VERSION` bumped to `22.1.0` (additive `ui_sniff` detection key,
  unrelated to this Track-A release — landed in the same working session).

---

## v26.1.1 — PR #176 review-fix cluster (patch)

**Patch (fix-only)** — closes all accepted findings from the max-level review of the
v25.2.0→v26.1.0 wave (4 Critical, 8 Important, 7 Minor). No template or schema change; no
migration; normal `tkm init` upgrade suffices.

### Fixed — markdown scanning (C1, I1, I3 + minors)
- New shared `scripts/_md_scan_lib.py` (fence-aware iteration for ``` and ~~~, HTML-comment
  strip, escaped-pipe table-row split) — single primitive for the recurring fence-blindness
  bug class.
- `validate_reading_guide_db_impact.py`: section body no longer truncated by `#`-lines inside
  code fences (an unfilled A3/B4 scaffold hidden behind a fence now WARNs instead of passing);
  B4 table extraction fence-masked; `\|` in cells no longer shifts columns; tolerant
  `data_rows()` used for separator-less tables.
- `validate_job_list.py` / `validate_test_cases.py`: fenced example headings/rows and
  HTML-commented template appendices no longer parse as live content.
- `derive_confidence_report.py`: `~~~` fences supported; `<!-- disclaimer:start/end -->`
  boilerplate no longer inflates the Claims↔Evidence table.
- `validate_design_intent_density.py`: `{...}` scaffold placeholders stripped before density
  checks (parity with derive_confidence_report).

### Fixed — credential gate (C4 + minor)
- `_credential_scrub_lib.py` split into recall-focused scrub patterns (adds `auth` vocab —
  `REDIS_AUTH=…` now caught; segment-boundary key matching — `BYPASS_HEALTHCHECK` no longer
  redacted) and precision-focused gate patterns (`assert_no_secrets` flags only
  assignment-shaped literal leaks; Bearer-token / service-account prose no longer fails the
  jobs promotion gate). Quoted `Environment="K=v"` redaction keeps the closing quote.

### Fixed — fan-out integrity (C2, I2, I7)
- `pipeline-jobs.md` J.1-merge reconciles fragment count against `_slice-plan.json` and HALTs
  (no marker, no cleanup) on a partial fragment set; `validate_job_list.py` adds reverse
  `JobList.bl_uncovered` WARN (qualifying BL### without a JOB###) and `JobList.index_drift`
  WARN (Job Index ↔ section parity).
- `pipeline-test-cases.md` TC.2 reconciles per-feature `.test-cases-completed` sentinels and
  the completion handoff reports the actual promoted count from the validation summary.

### Fixed — promotion gates & contracts (C3, I4, I5, I8)
- `pipeline-design-intent.md` D.5 re-reads the validator summary and review report from disk,
  so a fresh `--confirm-promote` invocation gates correctly (mirrors J.5/TC.5).
- Jobs preflight ABORT message names `behavior-logic.md` (was `entities.md`).
- Removed the false "dedup already checked [deterministic-pass]" claim (JOB-S4 semantic review
  remains authoritative for dedup).
- Design-intent contract citations no longer point at an ephemeral `plans/` research file.

### Fixed — citation regexes (I6 + minors)
- `validate_design_intent_density.py` accepts Delphi/Oracle citations
  (`pas|dpr|dfm|sql|pks|pkb|pls`); `validate_test_cases.py` requires a path shape for
  `file:line` citations (bare `Note:1` no longer counts); multi-token `**BL Ref**` values are
  all validated; `migrate-reading-guide-db-impact.py` reports unreadable specs as their own
  tally category (exit-0 contract unchanged).

---

## v26.1.0 — Wave 3: A2 jobs pass + B6 test-cases pass + B5 design-intent pass (additive)

**Additive (minor)** — three new opt-in standalone passes land strictly sequentially
(file-ownership collision on shared files forbids parallel execution) but ship together as
ONE consumer-facing release: one `tkm init` re-run covers all three, not three separate ones.
This entry accumulates sub-entries as each phase lands; do not treat a partial sub-entry list
as the final v26.1.0 shape until all three are present.

### Additive — A2 `--jobs` standalone pass (sub-entry 1 of 3)

- **New standalone pass `--jobs`** (J.1–J.5): scans `docs/generated/behavior-logic.md` for
  BL### entries typed `scheduled-job`/`queue-worker`/`custom-command` and expands each into a
  per-job detail section — inventory table + per-job `## Purpose` / `## Schedule / Trigger` /
  `## Data Touched` / `## Failure / Retry Behavior` — all in ONE artifact,
  `docs/generated/job-list.md`. This is a re-projection of the existing Wave-0 BL inventory, NOT
  a new detection surface (same relationship `--screen-specs` has to `screen-list.md`).
- **No `docs/jobs/` namespace** (reversed from an earlier design during red-team review): a
  dedicated namespace would have added 4 wiring touches (mapping row, `MOVED_LAYERS`,
  `check_layout_paths.py`, layout-exempt audit) for a low-volume artifact. `job-list.md` lives
  under the existing `docs/generated/` namespace, already translation-covered by
  `_translation_sync_lib.py::_DOC_AREAS`. `JOB###` codes are in-file row IDs, file-global (never
  reset per type or directory).
- **New systemd-timer detection row** in `references/bl-source-patterns.md` — the only genuinely
  new detection surface this pass adds (`.service`/`.timer` unit file pairs).
- **New deterministic validator `scripts/validate_job_list.py`**: JOB### regex + file-global
  uniqueness, `**Source**` citation presence, `**BL Ref**` presence/shape/resolution against
  `behavior-logic.md`, and a hard CRITICAL secrets gate wiring
  `_credential_scrub_lib.py::assert_no_secrets()` over the promoted output.
- **`_credential_scrub_lib.py` extended** to recognize `.service`/`.timer` unit files
  (`is_config_file()`) and to redact systemd `Environment=<KEY>=<value>` lines whose KEY carries
  abbreviated credential vocabulary (`pass`/`pwd`/`secret`/`token`/`key`/`credential`/`dsn`) not
  already caught by the pre-existing password/token/secret patterns.
- **Jobs researcher contract** (`references/jobs-researcher-contract.md`): READ-ONLY static
  scan — NEVER executes target build/task tooling (no `rake -T`/`crontab -l`/`systemctl`),
  mirroring `references/structural-extractor-contract.md`'s "never execute" rule. Job
  identifiers are slug-sanitized (mirrors the `FLOW###`/`F###` grammar).
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `jobs` (needs only core — same prereq class as `screen-specs`);
  `references/pipeline.md::passPresent` gains a `jobs` key; `docs/generated/` was already
  covered by the translation discovery registry, so no change was needed there.
  `references/multi-component-runbook.md` Step 1b enumeration gains `jobs`.
- **Promotion wiring**: `promote_drafts.py` gains `--scope jobs` (mirrors `--scope glossary`
  exactly) + `_layout_lib.py::LAYERED_PATH_MAP["job-list.md"]`; `build_source_to_fcode.py` gains
  `--cursor jobs` (advances `last_jobs_run_sha`, refreshes `doc_shas["job-list.md"]`, additive —
  no state-schema migration).
- **Resume & Reconcile**: `jobs-complete.flag` added to the completion-sentinel enumeration;
  `expectedOutput` for this pass = `docs/generated/job-list.md`.
- Nav: `job-list.md` added to `_nav_strings.py::READING_ORDER` (layer 4, conditional) +
  matching `artifact_descriptions["job_list"]` in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`) + `_nav_lib.py::_ARTIFACT_DESCRIPTIONS["job-list.md"]`.
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Job inventory | docs/generated/job-list.md`) + a proportionate bump-ledger entry (**minor**
  for rebuild-spec; no bump for other consumers — an additive new output path, no existing
  consumer's resolved path changes).
- **Bounded-wave fan-out (F10)**: J.1 counts qualifying BL### entries directly (no
  `estimate_artifact_loc.py` wiring needed for this cheap count over an already-small artifact);
  ≤5 entries dispatches a single researcher task (the common case); >5 dispatches a
  shell+fragment+merge fan-out wave-chained at `min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)`
  (reuses the existing env, no new `REBUILD_JOBS_BATCH_SIZE`), each wave `addBlockedBy` ALL prior
  wave task-ids per the v25.1.2 hardening.
- **Not wired in v1** (documented, deliberate scope decision): `job-list.md` does NOT route
  through `estimate_artifact_loc.py`'s pre-gen LOC-estimate/shard-branch machinery (the fan-out
  above triggers on entry COUNT, not estimated LOC), and `JOB###` is NOT registered in
  `_id_schemes_lib.py`'s generic `ARTIFACT_OWNS`/renumber registry. `validate_job_list.py` does
  its own JOB### uniqueness check directly, the same way `validate_behavior_logic.py` and
  `validate_process_flow.py` self-check their own ID schemes. `references/artifact-sharding.md`
  carries a Descriptor Table row documenting this as a known v1 scope boundary, not an oversight.

### Additive — B6 `--test-cases` standalone pass (sub-entry 2 of 3)

- **New standalone pass `--test-cases`** (TC.1–TC.5): derives UT/IT/UAT test-case lists per
  feature by EXPANDING the already-cited `docs/features/{slug}/technical-spec.md` (BR-###/
  SM-###/DEC-###/DISC-### codes) and `edge-cases.md` (already test-case-shaped negative-path
  rows), with optional `screens.md`/`business-context.md` enrichment for UAT scenarios. Output:
  `docs/features/{slug}/test-cases.md`, a 5th per-feature file, **SIDECAR** — never joins the
  `FEATURE_FILES` 4-tuple or the promotion gate. Fan-out shape is identical to FS.1 (one
  researcher per F###, wave-chained ≤`min(REBUILD_FS_BATCH_SIZE, REBUILD_MAX_PARALLEL)` — reuses
  the existing env, no new `REBUILD_TESTCASES_BATCH_SIZE`).
- **TC### ID grammar**: `^TC\d{3}$`, resets per feature (same per-parent-reset exception class as
  `REG###` resetting per `SCR###`) — the ID Contiguity Gate exception sentence in
  `references/artifact-sharding.md` now names `TC###` alongside `REG###`.
- **Citation-source split (anti-hallucination)**: UT/IT rows must cite a `BR-###`/`SM-###`/
  `DEC-###`/`DISC-###` code, a `file:line`, or an `edge-cases.md` row; UAT rows must cite a
  `screens.md`/`business-context.md` section — never a bare code. A mismatch is a CRITICAL
  finding in `scripts/validate_test_cases.py`, not a style nit — it is the exact risk this split
  exists to guard against.
- **New deterministic validator `scripts/validate_test_cases.py`**: TC### regex + per-feature
  uniqueness, Type∈{UT,IT,UAT}, Traces-to presence + citation-source-family match, and a
  coverage-gap WARN cross-referencing every BR/SM/DEC/DISC code in `technical-spec.md` against
  the test cases that trace to it (a code may be deliberately excluded via a `[NO_TEST_CASE]`
  marker in `test-cases.md`'s `## Coverage Notes` section — WARN, non-halting; 100% coverage is
  not always achievable or desired).
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `test-cases` (requires `feature-specs` — same DAG class as flows/glossary);
  `references/pipeline.md::passPresent` gains a `test-cases` key; `docs/features/*/*.md` was
  already covered by the translation discovery registry (`_translation_sync_lib.py::_DOC_AREAS`),
  so no code change was needed there. `references/multi-component-runbook.md` Step 1b
  enumeration gains `test-cases`.
- **Promotion wiring — verified, no new `--scope` literal needed**: `promote_drafts.py`'s
  `--scope features` walks the ENTIRE `artifacts/features/{fcode}/` source directory
  (`os.walk`) and copies whatever is present — directory-scoped, not a fixed filename list.
  Since TC.1 writes ONLY `test-cases.md` into that draft folder, an incremental `--scope
  features` promote copies it into `docs/features/{fcode}/` additively, alongside the
  pre-existing 4 files. `build_source_to_fcode.py` gains `--cursor test-cases` (advances
  `last_test_cases_run_sha`; no `doc_shas` entry — per-feature sidecar, not a single core
  artifact — falls into the same "preserve prior entirely" branch as flows/feature-specs).
- **Resume & Reconcile**: `test-cases-complete.flag` added to the completion-sentinel
  enumeration; `expectedOutput` for this pass = per-feature `docs/features/{slug}/test-cases.md`
  (mirrors FS.7's per-fcode reconcile shape, not J.5's single-file shape).
- Nav: `test-cases.md` added to `scripts/_nav_feature_lib.py::FEATURE_FILE_ORDER` (presence-pruned,
  listed last) + matching `file_purposes["test-cases.md"]` entry in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`). No top-level `READING_ORDER` entry needed — it rides
  the existing `features/*/` glob (unlike `job-list.md`, which is a top-level single artifact).
- **Sidecar guardrail (F1/F15)**: `test-cases.md` is explicitly documented as NOT part of
  `_slug_lib.py::FEATURE_FILES`, `check_promotion_gate.py`, or `scaffold_spec.py`'s 4-file
  scaffold — a sidecar note was added to `references/feature-spec-researcher-contract.md`
  mirroring the A1 confidence-report companion precedent. Regression tests assert this boundary
  in both `test_check_promotion_gate.py` and `test_validate_test_cases.py`.
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Feature test-cases | docs/features/{slug}/test-cases.md`) + a surgical-edit-rule row +
  a proportionate bump-ledger entry (**minor** for rebuild-spec; no bump for other consumers —
  folded into the same v26.1.0 already recorded for the jobs sub-entry, no separate version
  number).
- **CSV export explicitly OUT OF SCOPE v1**: zero prior CSV precedent anywhere in this kit
  (only `.xlsx` via `--api-doc`); Markdown is the sole primary output.

### Additive — B5 `--design-intent` standalone pass, EXPERIMENTAL (sub-entry 3 of 3)

- **New standalone pass `--design-intent`** (D.1–D.5): infers cross-cutting "why the system was
  built this way" architectural rationale from ADRs (highest-trust, optional), `architecture.md`
  + `business-rules.md`, source-code patterns (`SOURCE CODE: AUTHORIZED`, like FL.1/GL.1), and
  optional `business-context.md` enrichment. Single-file synthesis, NO fan-out — mirrors the
  GL.1–GL.3 glossary shape (the simplest 3-wave precedent), not `--overview`'s cluster fan-out.
  Output: `docs/system/design-intent.md`.
- **EXPERIMENTAL — this is the highest-hallucination-risk pass in the kit ("why" is inherently
  more inferential than every other artifact's structural "what")**, so it ships with three
  deliberate defenses instead of default-promote:
  1. **(F11a) Disclaimer header** — every draft opens with an EXPERIMENTAL/`[INFERRED]`-heavy
     banner (`templates/design-intent-template.md`), wrapped in
     `<!-- disclaimer:start/end -->` markers the density validator relies on to skip it.
  2. **(F11b) Report-only first release — NO auto-promote path anywhere.** D.1–D.4 write and
     review the artifact ONLY inside `plans/<active-plan>/artifacts/design-intent.md`. Promotion
     to `docs/system/design-intent.md` happens ONLY via D.5, reachable exclusively through an
     interactive `AskUserQuestion` "yes" or the explicit `--design-intent --confirm-promote`
     flag. `promote_drafts.py`'s `design-intent` scope is deliberately excluded from `--scope
     all`/`core` — no other pass's promote step can accidentally publish it.
  3. **(F11c) NEW mode-agnostic density validator** `scripts/validate_design_intent_density.py`
     — flags asserted-as-fact, zero-citation paragraphs in ANY run mode. This is a genuinely NEW
     script, NOT a reuse of `re-output-contract.md`'s density check (that check is gated on
     `profile.re_contract`/RE-mode and would never fire for a normal `--design-intent` run — the
     original research suggestion to reuse it did not hold up under review).
- **Citation-or-`[INFERRED]` gate (load-bearing)**: every claim in the researcher contract
  (`references/design-intent-researcher-contract.md`) must cite an ADR, `business-rules.md`,
  `architecture.md`, or a `file:line`, OR be tagged `[INFERRED]` with a one-clause reason.
  Source order is ADR (quote directly, never override) → architecture.md/business-rules.md →
  source code → `business-context.md`. Degrades gracefully when ADRs are absent (the common
  case — most repos have none): leans on code-pattern inference, surfaces the resulting
  ADR-citation ratio in the handoff (e.g. "3/18 claims cite an ADR").
- **Non-duplication boundary (DRY, vs `business-rules.md`/`architecture.md`)**: design-intent
  holds ONLY cross-cutting architectural rationale; it may cite either existing artifact, never
  re-narrate their content. Documented as a Disambiguation note in
  `claude/skills/_shared/docs-canonical-mapping.md` — the same pattern the mapping file already
  uses for `docs/system/architecture.md` vs `docs/system-architecture.md`.
- **New-pass registry wiring**: `scripts/_manifest_pass_status_lib.py::PASS_NAMES`/
  `PASS_PREREQS` gain `design-intent` (needs only core — same prereq class as `jobs`/
  `screen-specs`, no feature-specs dependency); `references/pipeline.md::passPresent` gains a
  `design-intent` key; `docs/system/` was already covered by the translation discovery registry
  (`_translation_sync_lib.py::_DOC_AREAS` globs `system/*.md`), so no code change was needed
  there. `references/multi-component-runbook.md` Step 1b enumeration gains `design-intent`
  (per-component — each component gets its own draft + its own D.4 confirmation gate; see the
  aggregate-tier note below).
- **Promotion wiring**: `promote_drafts.py` gains `--scope design-intent` — structurally
  identical to `--scope glossary`/`--scope jobs` EXCEPT it is deliberately never included in
  `("all", ...)` (F11b) — plus `_layout_lib.py::LAYERED_PATH_MAP["design-intent.md"]`;
  `build_source_to_fcode.py` gains `--cursor design-intent` (advances
  `last_design_intent_run_sha`, refreshes `doc_shas["design-intent.md"]`, additive — no
  state-schema migration; only ever invoked at D.5, post-confirmation).
- **Resume & Reconcile**: `design-intent-complete.flag` added to the completion-sentinel
  enumeration; `expectedOutput` for this pass = the PLAN-DIR draft
  `plans/<active-plan>/artifacts/design-intent.md` (NOT `docs/system/design-intent.md`) — a
  never-promoted, report-only run is a complete, valid pass state. This is the whole point of
  F11b, not a gap.
- Nav: `design-intent.md` added to `_nav_strings.py::READING_ORDER` (layer 4, num 19,
  conditional — appended at the tail alongside `job-list.md` to avoid renumbering every
  downstream entry, mirroring the A2 precedent rather than design-intent's more natural layer-1
  placement) + matching `artifact_descriptions["design_intent"]` in all three locale modules
  (`_nav_strings_en.py`/`_vi.py`/`_ja.py`) + `_nav_lib.py::_ARTIFACT_DESCRIPTIONS["design-intent.md"]`.
  Layer-4 placement means it carries no `reading_why` clause (that block is layer-1-3 only by
  contract — enforced by `test_nav_reading_why.py`).
- `claude/skills/_shared/docs-canonical-mapping.md` gains one row
  (`Design intent (EXPERIMENTAL) | docs/system/design-intent.md`) + the Disambiguation note
  above + a proportionate bump-ledger entry (**minor** for rebuild-spec; no bump for other
  consumers — folded into the same v26.1.0 already recorded for the jobs/test-cases sub-entries,
  no separate version number).
- **Aggregate-tier design-intent = follow-up (Decision 4, scope boundary — NOT built in v1)**:
  a 7th aggregate artifact (system-researcher-authored, cross-component "why", alongside the
  existing `overview`/`component-catalog`/`architecture`/`glossary`/`cross-service-flows`/
  `data-ownership-map` six) is explicitly deferred. v1 is single-component/system-level only —
  each multi-component member gets its own per-component draft via Step 1b, never a
  cross-component synthesis. The 6-artifact aggregate contract itself is untouched.
- **Go/no-go graduation criteria = follow-up gate (F11d, quantified, NOT executed in v1)**: this
  pass graduates from EXPERIMENTAL to default-promote ONLY when, across **3 pilot repos of
  differing stacks**, ALL hold: (1) `[INFERRED]` ratio ≤25% of claims per repo; (2) zero
  fabricated citations — spot-checked via an `audit-doc-parity` run (or equivalent
  citation-existence check) on each pilot output; (3) a human reviewer confirms the artifact is
  useful, not generic boilerplate. Record pilot results before flipping any default — accepted
  trade-off: this pass may stay EXPERIMENTAL longer than a typical additive pass.
- **Multi-component `design-intent` per-component caveat**: `references/multi-component-runbook.md`
  Step 1b's `--batch --pass design-intent` driver step reuses the same per-component
  eligibility/DAG machinery as `jobs`/`test-cases`, but each component's own D.4/D.5 report-only
  → confirm-promote gate is independent — confirming promotion for one component's draft does
  NOT confirm any other component's.

## v26.0.0 — A3 Source Walkthrough + B4 DB Impact per Event (BREAKING)

**BREAKING** — two new REQUIRED sections change the shape of both spec templates, plus a new
dedicated validation gate. Same class as v24.0.0: the WARN-first degradation contract softens
the *rollout* for un-migrated repos, but the kit still calls this BREAKING because the template
shape changed and a new validator was wired into an existing gate (FS.2).

### Breaking — A3 Source Walkthrough + B4 DB Impact per Event

- **`templates/technical-spec-template.md`** gains two new top-level H2 sections, appended
  after `## Unresolved Questions`: `## Source Walkthrough` (A3 — ordered reading list, per-file
  "why start here," call-hierarchy diagram, and a pointer to the `## Source Code References`
  table, which is re-cast in place with a new **Order** column so there is one related-files
  table, never two) and `## DB Impact per Event` (B4 — one row per DB-writing event/endpoint:
  `Event/Endpoint | Table | Columns | Operation | Value Derivation | Source`, `Source` a
  `file:line` citation or `[INFERRED]`; `N/A — read-only feature, no DB writes.` when a feature
  performs zero writes). B4 is a top-level H2, not nested under `## Cross-Cutting Logic` —
  validator symmetry with A3, and keeps `_spec_constants.REQUIRED_CCL_H3` untouched (no reason
  to widen the BREAKING radius onto that exact-order check too).
- **`templates/screen-spec-template.md`** gains `## Source Walkthrough` (A3 only — B4 stays
  feature-spec-only; DB writes are out of ScreenSpec's UI-layer scope). `## Source References`
  is re-cast from a bullet list to a numbered list (the reading order) — same one-list DRY rule.
- **A3 renamed from "Code Reading Guide"** (an earlier working name) to **"Source Walkthrough"**
  to avoid colliding with the unrelated v24 nav "reading guide" feature (per-artifact
  `reading_why` clauses, `_nav_feature_lib.py`).
- **New validator `scripts/validate_reading_guide_db_impact.py`** (WARN-capable, NON-halting):
  covers BOTH families from one script. Degradation contract — absent section on an
  un-migrated doc → WARN `reading_guide.pre_migration` / `db_impact.pre_migration` (never
  breaks the build); present-but-empty or a non-table B4 body (and not `N/A`) → CRITICAL
  `*.malformed` (real drift); present-but-only-placeholder → WARN `*.unmapped`; a B4 row whose
  Source cell is blank (no citation, no `[INFERRED]`) → WARN `db_impact.uncited`. Deliberately
  NEVER added to `_spec_constants.REQUIRED_H2_TECH` — that exact-order check has no degradation
  window (Decision 2, harsher than v24.0.0's own precedent). A permanent regression test
  (`test_spec_constants.py::TestF8RegressionGuard`) asserts the two new headings are never added
  there. Wired into the FS.2 feature-specs gate (mirrors `validate_feature_screen_link.py`'s
  wiring shape exactly, including its scope limitation: a `--screen-specs`-only run that never
  runs `--feature-specs` does not exercise this gate).
- **New migration `scripts/migrate-reading-guide-db-impact.py`** (idempotent, non-destructive):
  unlike the v24 SCR###/Feature migration, A3/B4 content cannot be mechanically backfilled from
  existing doc text — it requires re-reading source, i.e. the researcher, not a script. This
  script only reports which specs still lack the sections (`[WARN] ... requires re-running
  researcher pass`); it never edits a file. Exit 0 always.
- **`scaffold_spec.py::_render_technical_spec` patched** to append the A3/B4 skeletons after
  its `REQUIRED_H2_TECH` render loop — the scaffolder renders from the constants list, not from
  the template files, so without this fix a fresh draft would permanently lack both sections.
  (No screen-spec equivalent exists to patch — `scaffold_spec.py` never renders
  `docs/screens/SCR###/spec.md`.)
- **`references/confidence-report-contract.md`** amended: A3's reading-list entries are
  navigational (file-existence pointers), not factual claims — they cite with `**File:**`, never
  `**Source:**`, so `derive_confidence_report.py`'s `CITATION_RE` (anchored on the literal
  `**Source:**` token) never counts them. No parser code change was needed; the fix lives
  entirely in the authoring contract. B4 rows, by contrast, ARE genuine claims — a B4
  `[INFERRED]` tag correctly counts as an uncited claim, unchanged.
- **Translation contract:** no new skeleton rule needed. B4's table shape is fully covered by
  the existing generic Table Cell Rule (header row verbatim; code/enum/path cells verbatim;
  narrative cells translated) — `Event/Endpoint`/`Table`/`Columns`/`Operation`/`Source` cells are
  code-like or path-like (verbatim); `Value Derivation` is narrative (translated). The recast
  `## Source Code References` `Order` column is a bare digit, likewise already covered.
- Contracts + checklists updated (`feature-spec-researcher-contract.md`,
  `screen-spec-researcher-contract.md`, `pipeline-feature-specs.md`,
  `verification-checklist-feature-spec.md`, `verification-checklist-screen-spec.md`).

**Migration:** run `migrate-reading-guide-db-impact.py --docs-root docs/` (or `docs/<lang>/`)
after upgrading to see which specs still need a researcher re-run; the script makes no changes
itself. Pre-migration repos keep building (validator WARNs, never FAILs, on the absent case).

---

## v25.2.0 — A1 confidence-report sidecar: all passes (additive)

**Non-breaking** — a new deterministic, best-effort companion file per artifact. No template
shape change, no promotion-gate change, no required-file-list change (same class as v24.1.0).

### Added

- **`scripts/derive_confidence_report.py`:** new deterministic script (no LLM, no source
  re-read, no network) that parses ONE promoted artifact's own inline `**Source:** file:line`
  citations (→ `○`) and `[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` marker tags
  (→ `△`) into a Claims ↔ Evidence table, and writes `confidence-report_<artifact-stem>.md`
  beside the artifact. Per-section exhaustive (not sampled, unlike the acsim precedent it
  improves on). `confidence_derived = claims_with_evidence / claims_total` (`null` when the
  artifact carries no citations or markers). Best-effort: any I/O or parse error is swallowed,
  the script always exits 0, and it never fails the pass that called it.
- **`templates/confidence-report-template.md`** — the companion skeleton (frontmatter +
  self-reported-coverage disclaimer + Claims ↔ Evidence table + Missing Info + Risk Flags). No
  standalone "human reviewer checklist" section — the table is supporting evidence for the
  existing verification-checklist / W7a review flow, not a replacement for it.
- **`references/confidence-report-contract.md`** — the shared derivation contract: status
  mapping, `confidence_derived` formula, per-section exhaustiveness, the A1
  correctness-verification boundary (self-reported citation-coverage stat only — see
  `claude/skills/audit-doc-parity/` for blind truth checks), the prompt-injection rule for any
  future LLM-authored companion prose, and the internal-only/export-exclusion rule.
- **Wired into every promote wave:** core-artifact promote (Wave 9, `pipeline-w7-w9.md`),
  feature-specs promote (FS.7, `pipeline-feature-specs.md`), screen-specs promote (SS.3,
  `pipeline-screen-specs.md`), flows promote (FL.5) and glossary promote (GL.3, both in
  `pipeline-flows-glossary.md`), api-contracts promote (AC.5, `pipeline-api-contracts.md`), and
  system-synthesis promote (`multi-component-runbook.md` § Step 3.5) — each runs the script once
  per just-promoted artifact, immediately after `promote_drafts.py` (or, for system-synthesis,
  immediately after the draft-purge step).
- **`--limitation-note synthesis` flag (in-v1, validated decision):** system-synthesis/aggregate
  companions (`overview`, `component-catalog`, `architecture`, `glossary`, `cross-service-flows`,
  `data-ownership-map`) carry an extra mandatory header caveat — their citation density is
  structurally lower than a per-feature/per-screen artifact's, so the coverage stat is not
  comparable across tiers. See `references/confidence-report-contract.md` § Limitation-note
  header.
- **Reconcile-time advisory:** a primary artifact present with its companion absent (pre-A1
  corpus, or a prior best-effort write failure) emits a one-line, non-gating
  `[WARN] confidence_report_missing` notice on the next reconcile preflight.
- **Reviewer advisory:** `verification-checklist-flows.md` and `verification-checklist-glossary.md`
  now note that a missing companion is advisory, not a defect — reviewers must not flag its
  absence.

### Sidecar contract (never gated)

Treated exactly like `.nav-metadata.json`: always-regenerated, purely advisory, and
deliberately NOT added to `FEATURE_FILES` (`scripts/_slug_lib.py`), `check_promotion_gate.py`,
the `.pending` 4-file liveness check, or `.rebuild-state.json`. Excluded from `--overview` /
doc-writer export (the pass's enrichment reads are an explicit 4-file enumeration, not a
glob). Auto-mirrored by the translation pipeline with zero new skeleton rule — the claims
table reuses existing header/separator/file-path/enum verbatim rules.

### Implementation

- `test_derive_confidence_report.py`: frontmatter math, `○`/`△` legend, disclaimer-header
  presence, best-effort behavior on an unwritable path, a regression guard proving the companion
  never enters `FEATURE_FILES` or the promotion gate, a flows-companion case, a
  glossary-companion case, and the `--limitation-note synthesis` header-injection behavior.
- Verified `_translation_sync_lib.py`'s `_DOC_AREAS` (`system/*.md`, `generated/*.md`,
  `flows/*.md`) already glob-discover companions in `docs/flows/` and `docs/system/` with zero
  code change — same auto-mirror as the core/feature/screen companions.
- No breaking changes to template shapes or validator-stage gates.

**Version bump:** `25.1.2` → **`25.2.0`** (minor, additive).

---

## v25.1.2 — cap clamps + env hygiene (PR-review fixes, patch)

Four findings from the PR #169 external review (APPROVE-with-comments). Orchestration-prose only.

- **W8-family clamp (Medium).** W8/FS.6/FL.4 fix-cycle wave width used `REBUILD_W8_MAX_PARALLEL`
  raw — setting it to 10 exceeded the cap the invariant text promised ("every pass … fix cycles").
  Effective width is now `min(REBUILD_W8_MAX_PARALLEL, REBUILD_MAX_PARALLEL)`; AC.1's
  `REBUILD_SHARD_MAX_PARALLEL` gets the same clamp.
- **Env hygiene (Minor).** `parseInt(env ?? '5')` let junk/`0`/negative envs produce NaN/0 wave
  widths — `idx % NaN` never fires, silently disabling wave rotation (unbounded fan-out). All cap
  env parses now guard: `Math.max(1, parseInt(env ?? '5') || 5)` (junk/0 → default 5; negative →
  clamped to 1 — either way never cap-off). Includes TR.2's `BATCH_SIZE`/`MAX_AGENTS`.
- **Translate derivation rule (Minor).** `langs × agents ≤ 5` was a bare constraint statement; the
  orchestrator now DERIVES `effectiveLangs = max(1, min(TRANSLATE_MAX_PARALLEL, floor(REBUILD_MAX_PARALLEL / TRANSLATE_MAX_AGENTS)))`
  instead of trusting the env pair.
- **Wave-1 headroom warning (Low).** Legacy profiles sit at exactly 5/5 — a maintenance comment at
  Wave1.c now forbids adding a new sibling on `scoutTaskId` (chain new Wave-1 artifacts instead).

## v25.1.1 — global-cap hardening (review fixes for v25.1.0, patch)

Four defects surfaced by a review of v25.1.0 before merge. Orchestration-prose only — no
artifact format change, no migration.

- **Core Wave-1 overflow (Important).** On legacy profiles producing crud-matrix + db-objects,
  SIX Wave-1 tasks were blocked on `scoutTaskId` — exceeding the cap the release declares.
  Wave1.c db-objects is now chained behind Wave1.b crud-matrix
  (`addBlockedBy: [crudMatrixTaskId ?? scoutTaskId]`); the core-pass antichain stays ≤5.
- **Three shard fan-outs missed the SEQUENTIAL wording (Important).** The v25.1.0 inline edits
  covered data-model / route-list / user-stories / feature-list but NOT screen-list+flow /
  behavior-logic / api-map — while this changelog claimed the inverse list. All seven inline
  shard task descriptions now carry "SEQUENTIAL BATCHES … batch i+1 only after ALL of batch i";
  the v25.1.0 entry below is corrected.
- **`REBUILD_MAX_PARALLEL` was a phantom env (Minor).** Documented as an env but read nowhere.
  The wave-rotation pseudocode now reads it (FS.1/FS.5/SS.1/SS.2, aggregate).
- **Wave width conflated with batch size (Minor).** FS.5/SS.1/SS.2 rotated waves on their
  batch-size envs — raising a batch size (workload knob) silently widened concurrency past 5.
  Wave width is now `min(<batch env>, REBUILD_MAX_PARALLEL)` in FS.1 and plain
  `REBUILD_MAX_PARALLEL` for FS.5/SS.1/SS.2 reviewer/batch waves; the aggregate
  system-researcher waves use `REBUILD_MAX_PARALLEL` instead of borrowing
  `REBUILD_W8_MAX_PARALLEL`.

## v25.1.0 — global 5-subagent parallel cap (bounded-wave dispatch)

Field evidence: `--feature-specs` on a 12-feature repo spawned 12 concurrent async researchers —
the FS.1 rule "≤20 F### → flat fan-out" only activated the batch cap above 20 features, and five
other fan-outs had the same shape (batched on paper, unchained in dispatch). New invariant:
**never more than 5 subagents runnable at once, anywhere in the flow** (`REBUILD_MAX_PARALLEL=5`,
SKILL.md § GLOBAL PARALLEL CAP). Orchestration-only change — no artifact format change, no
migration needed.

- **Bounded-wave dispatch (new global rule).** Any pass creating >5 sibling tasks chunks them
  into waves of ≤5; every task of wave i+1 is `addBlockedBy` ALL tasks of wave i (never just the
  last — that lets waves overlap).
- **FS.1** — flat fan-out branch (≤20 F###) removed: per-feature tasks are now wave-chained at
  ≤`REBUILD_FS_BATCH_SIZE` (default 5). The >20 batch branch is unchanged (already sequential).
  Mirrored in `spec-stage-procedure.md` SYSTEM fan-out and SKILL.md § caps.
- **FS.5 / SS.1 / SS.2** — reviewer/batch tasks were all-unblocked-at-once (ceil(N/5) concurrent);
  now wave-chained at ≤5.
- **W8 / FS.6** — `chunk(affectedFiles, REBUILD_W8_MAX_PARALLEL)` was a no-op (every fix task
  shared one blocker); batches now chained.
- **FL.4** — flow fix fan-out was entirely uncapped; now wave-chained at ≤`REBUILD_W8_MAX_PARALLEL`.
- **AC.1** — batches chained on the LAST task of the previous batch only (overlap race); now
  chained on ALL of it.
- **Translate** — `REBUILD_TRANSLATE_MAX_PARALLEL` default 3 → **1** (langs sequential);
  documented constraint: langs × per-lang agents ≤ 5.
- **Shard fan-outs** — batches explicitly SEQUENTIAL and counted toward the global cap
  (`artifact-sharding.md § Batching`, all shard types). Inline task-description wording landed in
  v25.1.0 for data-model / route-list / user-stories / feature-list; the remaining three
  (screen-list+flow / behavior-logic / api-map) were completed in v25.1.1.
- **Aggregate system-researcher** — "one per artifact" capped at 5 concurrent (6 artifacts →
  wave of 5 + wave of 1).

## v25.0.1 — route-link parser/migration hardening (patch)

Five Critical defects surfaced by a max-level adversarial review of v25.0.0's new
`_route_link_lib.py` scanner and `migrate-feature-api-ids.py` writer — all reachable from
ordinary authoring patterns, not contrived input. No format change (route-list.md's Backend
Routes column shape is unchanged); bug-fix only.

- **Fence-scoping (C1).** `_all_backend_routes_tables` (validator/nav) and
  `_locate_backend_routes_tables` (migration) had no awareness of fenced code blocks, so a
  fenced ` ```markdown ` example table shown under `## Backend Routes` (illustrating the
  expected shape) was scanned as a REAL sub-table — leaking a fabricated `ROUTE###`/`F###` into
  the inventory/owner-map, shifting migration's numbering, and risking a spurious
  `link.feature_unresolved` FAIL. Both scanners now skip fenced regions (`_id_schemes_lib
  .segment_text` in the validator/nav path; a new `_fenced_line_indices()` helper reusing the
  same primitive in migration).
- **Pipe-in-cell write corruption (C2).** Migration's `backfill_route_list` split each row on
  `|` and blindly inserted the new columns at a fixed index; an unescaped `|` inside a Path or
  Handler cell (e.g. a regex-alternation route constraint) shifted every cell after it, writing
  a permanently corrupted row. Now: header cell count is captured per table span, and any data
  row whose cell count doesn't match is left byte-identical and reported via a WARN (never
  written corrupted).
- **4-digit code overflow (C3).** `_ROUTE_PREFIX`/`_F_PREFIX` (`\bROUTE\d{3}`/`\bF\d{3}`) lacked
  the `(?![0-9])` boundary `_id_schemes_lib.token_re()` already solved elsewhere, so `ROUTE1000`
  silently truncated to the wrong code `ROUTE100` — a real collision risk past 999 routes. Both
  patterns now reuse `token_re()` (wrapped `re.IGNORECASE` to preserve existing case-insensitive
  matching): a 4+ digit code simply does not match, instead of mismatching.
- **Duplicate ROUTE### last-wins (C4).** `build_route_owner_map` overwrote on a duplicate
  `ROUTE###` across two `### File:` sub-tables, silently dropping the first owner and risking a
  false `link.owner_mismatch` against the legitimate one. `build_route_owner_map_with_dups` now
  unions owners across duplicates and returns the duplicate set; the validator raises a new
  critical `link.route_duplicate` for each (the template's "contiguous and global" ROUTE###
  contract makes a duplicate itself a defect). `build_route_owner_map` remains as a back-compat
  wrapper.
- **Missing-separator row drop (C5).** An unconditional `table[2:]` slice (4 call sites across
  `_route_link_lib.py`, `_nav_route_lib.py`, and migration's positional `pos==1` handling) assumed
  the `|---|` separator row is always present; when hand-edited or malformed input omits it, the
  first real data row was silently dropped, producing a false `link.route_unresolved` FAIL (lib/
  nav) or a corrupted synthetic-separator insertion (migration). New shared `data_rows(table)`
  primitive in `_nav_table_parse_lib.py` checks the separator's shape before skipping; migration
  gained the matching `has_sep` branch.

`_route_link_lib.py` stays at the 200-LOC ceiling (the C5 fix's `table[2:]` sites were replaced
with calls to the new shared `data_rows()`, keeping the module itself lean); `validate_feature_api_link.py`
grew by 4 lines for `link.route_duplicate`. Regression tests reproduce all 5 reviewer fixtures
(fenced example table, pipe-in-path row, `ROUTE1000`, cross-table duplicate, missing-separator
table) across the validator, migration, and nav paths, plus a migrate→validate end-to-end pair
(including a missing-separator variant). 2258 pytest green (2242 prior + 16 new).

---

## v25.0.0 — feature↔API/route ID binding (BREAKING)

**BREAKING** — mirrors the v24.0.0 feature↔screen pattern one layer further out: `route-list.md`
gains a mandatory code column and a mandatory owner column, and a deterministic validator now
enforces both directions plus twin-consistency from day one.

### Breaking — feature↔API/route binding (Phase 1)

- **`route-list-template.md`** Backend Routes table gains two columns:
  `Method | Path | Code | Owner F### | Handler | Middleware`. `Code` is the canonical `ROUTE###`
  (contiguous, global, same shape as `SCR###`/`F###`); `Owner F###` carries the bare feature code
  that claims the route, `—` when unattributable (shared/infra routes), or comma-separated
  multi-owners for rare shared routes (e.g. `F001, F003`).
- **`_id_schemes_lib.py`** gains the `ROUTE` scheme (`WORD###`, global scope) and a new
  `ARTIFACT_OWNS["route-list"] = ["ROUTE"]` entry; `SIBLING_MATRIX["ROUTE"]` is scoped to
  `feature-list.md` + `behavior-logic.md` only — `technical-spec.md` is per-feature (out of this
  global-artifact matrix's reach) and `screen-flow.md` was excluded (no real `ROUTE###` citation,
  only an optional either/or in a `GUARD-###` heading).

### New validator `validate_feature_api_link.py`

- forward — `technical-spec.md` / `behavior-logic.md` `{ROUTE###}` citations (Artifact References'
  Codes Used column) resolve to `route-list.md`'s `Code` column.
- reverse — `route-list.md`'s `Owner F###` cell(s) (multi-owner comma/slash aware) resolve to
  `feature-list.md`.
- twin — a feature's forward `ROUTE###` citation must appear in that route's reverse `Owner F###`
  set; a silent double-claim across features is a real correctness bug, not a WIP state (the
  exact lesson PR #158 forced for feature↔screen, extended one layer out).
- Degradation contract: no `Code`/`Owner F###` columns at all → WARN `link.pre_migration`
  (never breaks the build); a present-but-unresolvable code → critical `link.route_unresolved` /
  `link.feature_unresolved`; a mapped route whose owner disagrees with a citing feature → critical
  `link.owner_mismatch`; an empty/placeholder Owner cell on a migrated table → soft `link.unmapped`
  WARN (an unclaimed `—` owner is NOT a twin-consistency mismatch); either inventory file (
  `route-list.md` / `feature-list.md`) absent entirely → WARN `link.inventory_absent` (missing ≠
  drift). Wired into the FS.2 feature-specs gate right after `validate_feature_screen_link.py`.

### New migration `migrate-feature-api-ids.py`

- Idempotent PER-TABLE backfill: a `route-list.md` can be half-migrated (one `### File:`
  sub-table already coded, another not) — each sub-table's own header decides whether it is
  touched; `ROUTE###` numbering stays globally contiguous by seeding from the highest existing
  code across all sub-tables.
- Ownership is DERIVED, not read from an existing bridge (unlike the screen migration's
  `screen-flow.md` "Owned screens" source): every `docs/features/F###/technical-spec.md`'s
  Artifact References citations are inverted into `{ROUTE### -> [citing F###]}` via the SAME
  shared parser (`_route_link_lib.artifact_ref_cited_routes`) the validator uses, so migration
  attribution and validator citation-detection can never disagree. Zero-citation routes get `—`;
  multi-citing routes get a comma-joined owner list.
- Non-destructive: only inserts the `Code`/`Owner F###` columns, never rewrites existing
  Method/Path/Handler/Middleware cells. No `technical-spec.md` files found (bridge absent) →
  WARN + exit 0, no changes ("run the feature-specs pass first").

### Nav wiring (Phase 4)

- New `_nav_route_lib.py`: per-feature Route/API table, presence-pruned (renders only when the
  feature has ≥1 resolvable `ROUTE###` citation), resolving Method+Path labels across every
  Backend Routes sub-table; every row links to the single shared `../../generated/route-list.md`
  (no per-route spec files exist, unlike screens/`SCR###`/`spec.md`).
- `_nav_feature_lib.py`'s `relationship_legend` gate extended to `{5, 7, 9}` — reuses
  `route-list.md`'s existing reading-order gate number 9, no new gate invented.
- All 3 locale string modules (`_nav_strings_{en,vi,ja}.py`) updated in lockstep: the
  `relationship_map` bullet now names `ROUTE###` explicitly (was a vague "route" mention) and
  states that `api-map.md`/`api-contracts.md` remain separate, unbound views; new
  `feature_readme` keys `routes_heading` / `col_route` / `col_route_owner` / `col_route_spec`.

### Out of scope

- `api-map.md` and `api-contracts.md` are **NOT** bound by this release. They are derived/grouped
  views with their own separate code schemes (`{ROUTE_CODE}`/`{GQL_CODE}`/`{GRPC_CODE}` in
  `api-contracts.md`, no codes at all in `api-map.md`) — cross-checking them against
  `route-list.md` is a candidate follow-up, not part of v25.0.0.

### Contracts + checklists updated

`verification-checklist-core-artifacts.md`, `verification-checklist-feature-spec.md`,
`feature-spec-researcher-contract.md`, `pipeline-feature-specs.md`, `technical-spec-template.md`,
`behavior-logic-template.md`.

**Version bump:** `24.1.0` → **`25.0.0`** (major, breaking — new required schema element + gate,
matching the severity class of v24.0.0's own bump).

---

## v24.1.0 — file-schema field + file-endpoint reading scope + twin-consistency reviewer rule (additive)

**Non-breaking** — purely additive improvements to file-exchange documentation, backend reading scoping, and template consistency checking.

### Added

- **File Schema field (BL + ALG):** `behavior-logic-template.md` (BL blocks) and `technical-spec-template.md` (`### ALG-###_Name` Algorithm blocks) each gain an identical `**File Schema**` field — a `| Column | Type | Required | Notes |` table documenting the internal column/header contract of an import/export file (CSV/XLSX), populated only when the block's Type/description matches file-exchange vocabulary (`import, export, csv, xlsx, upload, download, bulk`); `N/A — not a file-exchange type` otherwise. Byte-identical table format in both templates — no format drift between BL and ALG.
- **Bounded backend-reading exception:** `screen-spec-researcher-contract.md`'s Import Discovery Rule (frontend-only, 1-level-deep) gains a narrow exception — when a screen's server-side action is file-producing/consuming (export/import/download/upload path or multipart/file Content-Type), the researcher MUST follow the backend handler one controller→job/service hop to identify the file schema, then **cross-reference** the feature's `BL-### File Schema` rather than re-deriving the column list (DRY). If the backend file-generation code is unreachable within that bound, the researcher escalates via `## Unresolved Questions` instead of silently omitting.
- **Two new validator rules (both warning-severity, non-halting):**
  - `BehaviorLogic.file_schema_missing` in `validate_behavior_logic.py` — flags a BL block whose own Type + description matches file-exchange vocabulary but whose own `**File Schema**` field is left unpopulated (or misuses the `N/A` string despite the vocab match).
  - `FeatureSpec.alg_file_schema_missing` in `validate_feature_spec.py` — the same check applied to `### ALG-###_Name` blocks in `technical-spec.md`.
  Both share one detection helper (`_file_schema_lib.py`) for the vocabulary match and "populated schema" test — no duplicated heuristic. Both rules registered in `verification-checklist-feature-spec.md`'s Deterministic Validator Coverage table.
- **W7i twin-consistency reviewer rule:** `verification-checklist-screen-spec.md` gains a new reviewer-only rule (`W7i`, no Python validator) enforcing that create/edit screen pairs sharing the same `**Feature**` backlink remain consistent on § A) Client-side validated field names — divergences without a stated reason are flagged as a warning. Registered in the checklist's summary table.
- **Server-side validator-class escalation:** `screen-spec-researcher-contract.md` §4.3 Section B now requires the researcher to first attempt to locate and read the endpoint's backend validator class (FormRequest / request-validator / serializer / DTO) before writing `[UNVERIFIED]` on a server-driven error message. If found, the real message is extracted (no `[UNVERIFIED]`); if the class is genuinely unreachable, `[UNVERIFIED]` stands but MUST be paired with a matching `## Unresolved Questions` entry naming the endpoint and the path that couldn't be reached.

### Implementation

- New shared library `_file_schema_lib.py` for File Schema field parsing and validation across BL + ALG contexts.
- New test files: `test_validate_behavior_logic.py`, `test_validate_feature_spec.py`, and `test_file_schema_lib.py` (21 new test cases covering the two validator rules + shared lib).
- No breaking changes to template shapes or validator-stage gates; all new rules are warning-severity and non-halting.

**Version bump:** `24.0.0` → **`24.1.0`** (minor, additive).

---

## v24.0.0 — feature↔screen ID binding + thickened feature/screen reading guide (BREAKING)

**BREAKING** — the two ID systems are now bound both ways, changing two templates and
adding a validation gate. Additive reading-guide work (A1–A6) ships in the same release.

### Breaking — feature↔screen binding (Phase B)

- **`screens-template.md`** Screen List gains an `SCR###` column:
  `Screen Name | SCR### | What User Sees | What User Can Do`. The code is the canonical
  `SCR###_NameSlug` from `screen-list.md` — the bridge to `docs/screens/SCR###_Name/spec.md`.
- **`screen-spec-template.md`** header gains `**Feature**: F###_Name` — the owning feature,
  the inverse of the SCR### column.
- **New validator `validate_feature_screen_link.py`** (WARN-capable, NON-halting): forward
  (screens.md SCR### ∈ screen-list.md) + reverse (screen-spec **Feature** ∈ feature-list.md).
  Degradation contract: a missing column/backlink on an un-migrated doc → WARN
  `link.pre_migration` (never breaks the build); a present-but-unresolvable code → FAIL
  (`link.scr_unresolved` / `link.feature_unresolved`). Wired into the FS.2 feature-specs gate.
- **New migration `migrate-feature-screen-ids.py`** (idempotent, non-destructive): backfills
  the SCR### column (resolved via screen-list.md by name) and the **Feature** backlink
  (sourced from `screen-flow.md` § Feature Entry Points `**Owned screens**`). Absent bridge →
  reports and exits 0 with no changes. Only inserts a column/line — never rewrites prose cells.
- Contracts + checklists updated (`feature-spec-researcher-contract.md`,
  `screen-spec-researcher-contract.md`, `pipeline-feature-specs.md`,
  `verification-checklist-feature-spec.md`, `verification-checklist-screen-spec.md`).

### Additive — feature/screen reading guide (Phases A1–A6)

- **A1** per-artifact causal "why read this here" clauses (`reading_why`) appended to the
  single-component index layer-1-3 rows (mirrors aggregate `reading_order_rows`).
- **A2** multi-line "how to read a feature" traversal block (`feature_traversal`) replacing the
  single buried note; teaches the feature → screen → SCR### path.
- **A3** static ID-relationship legend (`relationship_map`) — F### ⇄ SCR### ⇄ US### ⇄ route.
- **A4** per-feature `README.md` inside `docs/features/F###_Slug/` — 4-file reading order +
  best-effort Screen → SCR### → spec table (column-aware).
- **A5** `docs/features/README.md` feature index (was suppressed; now generated from F### subdirs).
- **A6** `new_dev` role line now points into the feature traversal (gated on the features entry).
- New modules: `_nav_feature_lib.py`, `_nav_table_parse_lib.py`. All 3 locales
  (`_nav_strings_{en,vi,ja}.py`) edited in lockstep; parity tests enforce skeleton identity.

### Nav refresh on the standalone feature-/screen-specs passes

- The **feature-specs (FS.7)** and **screen-specs (SS.3)** passes now run `build_navigation.py` after
  promote (mirroring the core-pass W9.6 step), so the newly-promoted `docs/features/F###/` +
  `docs/screens/SCR###/` dirs immediately surface in the reading-order README, the per-feature READMEs
  (A4), and the features index (A5). Previously these passes promoted the dirs but left the README
  stale until the next core pass. Primary root is refreshed directly (mode-aware `docs_root`);
  secondary-lang mirrors continue to refresh via the translation auto-sync Step 3.5.

**Migration:** run `migrate-feature-screen-ids.py --docs-root docs/` (or `docs/<lang>/`) once
after upgrading; re-run is a no-op. Pre-migration repos keep building (validator WARNs, never FAILs).

---

## v23.0.0 — component per-lang placement: single-source translate model (BREAKING)

**BREAKING** — three tracks shipped together. `SYNTHESIS_FORMAT_VERSION` → `22.0.0` (trips
`[WARN] stale_digest` on existing aggregate state, forcing re-synthesis after migration).

### Track 1 — Component placement model (P04/P05/P07)

Per-component docs are now written ONCE to the language-resolved source root:
- `docs/components/<name>/` for en single-lang (byte-identical to v22 — no change)
- `docs/<primary>/components/<name>/` for non-en or per-lang repos (v23 BREAKING)

`resolve_component_paths` passes `primary_lang` to `resolve_docs_root` — the same resolver
used by core/system artifacts. **The derived-view projection (ADR-0002 rung-1/2/3) is
deleted.** There is no `docs/<primary>/components/` rebuilt by the aggregate; it is written
directly by `--root`/`--batch` runs.

Secondary-lang component docs at `docs/<L>/components/<name>/` are produced by the
translation pipeline (`--lang <L> --root <name>`) and auto-synced on change via
`translation_sync_gate.py` (`_DOC_AREAS` now includes `"components"`). Every secondary-lang
component doc is a real translation — the rung-3 "dùng tạm" fallback is gone.

### Track 2 — Derived-view shadow purge (P06)

`_component_view_lib.py` and the projection entry-point in `_component_placement_lib.py`
deleted. Test file `tests/test_component_placement.py` removed. All three recorded in
`claude/metadata.json → deletions`.

### Track 3 — Reading-guide / nav fixes (P04/P07)

`build_navigation.py` generates READMEs at the resolved per-lang component path. The
`--aggregate` `system/README.md` reading-guide no longer references a derived-view path.

### One-time migration (existing non-en repos)

`_component_migrate_lib.migrate_components_to_lang` runs automatically on the FIRST
`--aggregate` call when `primary_lang != en` and `docs/components/` still exists (the old
v20/v22 root location). Guarded by sentinel `docs/<primary>/.components-migrated-v23`.

| Scenario | What happens |
|----------|--------------|
| `docs/components/` absent (new or already clean v23 repo) | no-op; sentinel written |
| Only `docs/components/` present | atomic `os.rename` root → lang; sentinel written |
| Both trees present, byte-identical | `shutil.rmtree` root copy; sentinel written |
| Both trees present, files differ | keep both; `[WARN]`; sentinel NOT written — re-run after resolving manually |
| `primary_lang == "en"` | no-op; en source stays at `docs/components/` by design |

**Root `docs/README.md` pruning:** after a successful migration a purely-generated pointer
README at the root is deleted; a hand-written one is never touched.

### ADR

ADR-0002 superseded by **ADR-0003** (`docs/decisions/ADR-0003.md`). ADR-0002 kept as
immutable history with a superseded banner.

---

## v22.0.0 — auto-detect multi-component + shared-layer attachment (BREAKING)

A single `rebuild-spec` run over **one repo holding N independent executables** (Ishindenshin: 20
Delphi `.dpr` under `PG/<MODULE>/` + a shared `PG/Common/` + an Oracle `DB/{TABLE,SP,VIEW}/<MODULE>/`
tree) used to flatten every module into ONE mono doc set — the multi-component machinery was opt-in by
flag and never auto-triggered. v22 closes that gap with three moves, all inside the existing
multi-component machinery.

**BREAKING:** a plain `/tkm:rebuild-spec` over a multi-executable `one-spec-per-unit` repo now
**auto-switches** into the `--emit-manifest`→`--batch`→`--aggregate` loop instead of producing one mono
doc set. Escape hatch: `--mono`.

- **Auto-switch (Phase 03/04).** `detect_stack_profile.py` resolves a `component_profile` — a matched
  `one-spec-per-unit` profile that claims ≥2 component roots — and emits `auto_switch` + `auto_switch_reason`.
  SKILL.md Preflight 2.5 prints `[INFO] multi-component detected (…): switching to --emit-manifest flow`
  and enters the driver loop. Bypasses: `--mono`, an explicit `--root <subrepo>`, an existing
  `.rebuild-components.json` (idempotent).
- **Executable-manifest boundary (Phase 01/02).** New optional profile field `component_boundary_globs`
  (`["*.dpr","*.dproj","*.dpk"]` on `delphi-vcl`) marks a component root by executables only — a dir with
  only `.pas` is no longer claimed. `find_components` gains keyword-only `boundary_globs`/`shared_abspaths`/
  `warnings` (default-None = byte-identical legacy behavior; all existing call sites unaffected).
- **Shared-layer marker (Phase 01/03/05).** New optional profile field `shared_layer_dirs`
  (`["Common","DB"]`) — those dirs are scanned ONCE and attributed to each component, never claimed as
  their own component (Layer-1 exclusion runs before the marker check, defeating the oracle co-detection
  of `DB/`). Surfaced as `detectJson.shared` and written to a SIDECAR `.rebuild-components-shared.json`
  (the component manifest stays a JSON ARRAY — Finding 1). A suppressed dir emits `shared_layer_excluded`
  so a real module named `DB`/`Common` is not silently dropped (Finding 4).
- **Deterministic DB attribution (Phase 05).** `_shared_attribution_lib.matches_module_label` (full-segment
  equality — `POS` ≠ `POSDEN`) drives a per-component FILTERED view of the shared-DB digest, attributing
  `DB/<TYPE>/<MODULE>` objects to `PG/<MODULE>` by the declared module-name convention. The Step-0.4
  shared pre-pass runs at the ROOT plan-dir (distinct from each component's → no `is_extractor_completed`
  collision; the `--out-suffix` idea was dropped).
- **`--profile <id>` (Phase 03).** Pins the authoritative profile when Delphi+Oracle co-detect and a
  DB-heavy tree would otherwise make `oracle-plsql` the hit-count `recommended` (Finding 2).
- **Detect output `schema_version` → 22.0.0.** Additive (new `component_profile`/`auto_switch`/`shared`
  fields); `recommended_profile` unchanged for legacy callers. `SYNTHESIS_FORMAT_VERSION` /
  state schema UNCHANGED (no synthesis-output or state-shape change). New file:
  `scripts/_shared_attribution_lib.py`.

Red-team hardened (`reviewer-260629-1508`): 2 BLOCKERS (manifest-array sidecar, component_profile vs
hit-count winner) + 3 majors folded into the design before build.

## v21.0.1 — extractor + contiguity fixes from real Delphi/Oracle run (patch)

Five bugs surfaced validating v21 on a real Delphi+Oracle (Shift-JIS) ERP repo on a
case-sensitive Linux FS. No output-format change (`SYNTHESIS_FORMAT_VERSION` stays `21.0.0`).

- **Case-insensitive extractor globs.** `fnmatch(fn, glob)` with lowercase globs (`*.sql`,
  `*.pas`) silently skipped uppercase `.SQL`/`.PAS` files on case-sensitive filesystems —
  near-empty digests (1 table instead of 461). Filename is now lowercased before matching in
  `extract_sql_schema.py`, `extract_data_flow.py`, and `_extractor_lib.py` (`source_tree_hash`).
- **Oracle leading-comma columns.** `_COL_DEF` in `_sql_parse_lib.py` required a line to start
  with whitespace, so leading-comma DDL (`,\tCAPTION VARCHAR2(40)`) parsed only the first column.
  `_COL_DEF`/`_COL_SKIP` now accept a leading comma.
- **Contiguity duplicate false-positives (hybrid heading/prose rule).** `validate_id_contiguity.py`
  counted *every* prose occurrence of a code as a definition, so summary-table rows,
  `**Dependencies**:` cross-links, `F001–F045` ranges and format examples all read as duplicates.
  Now: if a code appears as a Markdown **heading** at all, its duplicate count is judged by heading
  occurrences only (table/bullet refs ignored); if it **never** appears as a heading (table-defined
  schemes like `route-list` / `crud-matrix`), it falls back to all-prose counting so genuine
  duplicate rows are still caught. Two headings for one code remains the canonical duplicate.
- **Stack-specific core artifacts promoted.** `crud-matrix.md` and `db-objects.md` (extractor-
  digest-derived) added to `_layout_lib.py`'s layout map and `promote_drafts.py`'s promote list,
  so Delphi/Oracle runs place and promote them like other core artifacts.

Regression tests added: `TestParseColumnLine` (leading-comma), `test_uppercase_extension_detected`,
heading-based duplicate fixtures, plus `test_heading_defined_with_many_refs_not_duplicate` and
`test_table_defined_scheme_duplicate_via_fallback` in `test_validate_id_contiguity.py`. 1955 pytest green.

---

## v21.0.0 — screen-artifact unify (non-web) + IPE stack-aware US generation (BREAKING)

**BREAKING** — non-web stacks now gain a screen artifact. `SYNTHESIS_FORMAT_VERSION` → `21.0.0`.

**Motivation.** On a real Delphi+Oracle ERP repo, `delphi-vcl` skipped the whole
`route-list/screen-list/screen-flow/api-map` cluster (`class: web`) → **no screen artifact**, and
US generation (screen-anchored) starved to **86 US for 440 material forms** (~20–35% coverage). v21
gives desktop stacks a screen artifact and makes US enumeration run per-form, without touching the
(correct) web path.

**What changed:**
- **New profile field `screen_source`** (`route-view` | `dfm-form` | `none`; `form-module` reserved).
  `screen-list`/`screen-flow` are produced **iff** `screen_source != none`, *overriding* their
  `artifact_map.action`. `route-list`/`api-map` stay web-only (governed by `artifact_map`). The
  `produce()` helper is the single source of truth. Profiles: web-js-ts→`route-view`,
  delphi-vcl→`dfm-form`, oracle-plsql/generic-source→`none`.
- **Anti-skip hardening (self-consistency).** First real Delphi run silently skipped screens: the
  orchestrator read `delphi-vcl.json`'s `screen-list/screen-flow → {action:skip, class:web}` and the
  "non-web project → skip web artifacts" heuristic, ignoring the subtle `screen_source` override. Fixed
  three ways so the produce decision is unmissable: (1) `delphi-vcl.json` now sets those two to
  `action:"produce"` — the profile reads truthfully (schema adds a **self-consistency rule**:
  `screen_source != none` ⇒ map them `produce`); (2) an explicit MANDATORY rule at the `produce()`
  binding in `pipeline-dispatch-and-gates.md` — the skip decision is `produce()`/`screen_source` ONLY,
  NEVER `class:web` and NEVER "route-list was skipped"; (3) SKILL.md's artifact→wave table no longer
  lists `route-list.md` as a screen prerequisite for non-web stacks (source is the form-nav digest).
- **Scout `.dfm` root-kind classification** — `object X: TBaseClass` header decides the tag:
  TForm→`screen`, TFrame→`screen-embedded`, TDataModule→`datamodule` (+`[reachable]`). Never by
  extension. `count_screen_files.py` regex tightened (`\tscreen(?![-\w])`) so `screen-embedded`/
  `datamodule` no longer inflate the visual-screen count.
- **New extractor `extract_form_nav.py`** — parses `.pas` Show/ShowModal/CreateForm, resolves
  target form→unit, builds a reachability closure from the `.dpr` root form, emits
  `_digest_extract_form_nav.json` (forms + edges, each citing `file:line`). Unreachable/indirect →
  `reach: unverified` (included, never dropped). Wired into `delphi-vcl` extractors + allowlist.
- **Route/api-map decoupling** (the part that actually unblocks Delphi): W9 `allCoreDocsPromoted`
  asserts route-list/api-map/screen-list/screen-flow only when `produce()`; the W7a reviewer
  artifact list is built from produce()-true artifacts; the verification-checklist SCR→RouteList
  cross-check + service-coverage rule are gated on `produce("route-list")`; `validate_screen_list.py`
  gains `--screen-source` (skips the route-specific `no_wildcard_route` check off route-view, keeps
  all structural checks). Without this, a perfect Delphi run HALTED at Wave 9.
- **Stack-aware templates** — screen-list/screen-flow carry conditional STACK-AWARE directives:
  `dfm-form` omits Routes/URLs, Authentication Flow, Guard Logic, Deep-Link, Unsaved-Changes,
  Extraction Signatures; uses a caller-based Invocation/Entry-form shape (no fork — one template).
- **IPE stack-aware** — Step 1 vocabulary enumerates `.dfm` controls (TButton/TAction/TMenuItem…+
  On* handlers) for dfm-form; Step 3 merge key is per-stack (web=same HTTP endpoint, dfm-form=same
  event-handler proc — NOT same table); materiality filter drops FPrt/FSel/FDlg/FSub/FCal families;
  form-variant dedup collapses `FHotelm`+`FHotelm2`; Oracle PL/SQL reachable logic → system-action
  US in behavior-logic/feature-list. Web split rule textually unchanged. `IPE_MERGE_CANDIDATE`
  reviewer rule updated to the per-stack key.
- **RE citation** — `validate_source_citations.py --re-mode` now counts screen-list/screen-flow
  toward citation density (when present on disk). `[UNVERIFIED]` reachability rows are valid (they
  carry a form-definition `file:line`). Advisory WARN, never HALT.

**Migration.** Existing Delphi docs lack screen-list/screen-flow. On the next run the orchestrator
backfills them: when `produce("screen-list")` is true but `docs/generated/screen-list.md` is absent
while core docs exist, Wave 2 screen-artifact generation is scheduled (see `pipeline.md` §
"v21.0.0 screen-artifact migration"). Additive — no prior artifact is deleted. Web output is
byte-comparable to pre-v21 (regression suite green); oracle-plsql still emits no screen artifact.
Because `screen_source` is a new resolved-profile field, the profile/state schema version bumps in
lockstep: `_stack_profile_lib.SCHEMA_VERSION` and `.rebuild-state.json`'s `STATE_SCHEMA_VERSION`
→ `21.0.0` (RT-F4). On resume, a state `< 21.0.0` invalidates the preflight checkpoint and
re-resolves the profile, so a pre-`screen_source` checkpoint cannot silently fail-close screens to
`"none"`.

**US recovery.** Delphi US count recovers from 86 toward the audited ~150–250 band (post
materiality-merge + variant-dedup), not the 354 1:1 upper bound.

---

## v20.0.0 — per-component language-aware placement: source-vs-derived-view (BREAKING)

**BREAKING** — components layout semantics change. `SYNTHESIS_FORMAT_VERSION` → `20.0.0`.

`--aggregate` now builds a **derived view** `docs/<primary>/components/<name>/` from the
lang-agnostic source `docs/components/<name>/` using a rung-selected per-component slice.
The source is NEVER mutated. Stale orphan dirs are pruned atomically each run.

**Source-vs-derived-view model (ADR-0002):**
- **Source of truth:** `docs/components/<name>/` — per-component `--root`/`--batch` runs
  always write here (unchanged). Lang-agnostic, ping-pong-safe.
- **Derived view:** `docs/<primary>/components/<name>/` — rebuilt atomically each aggregate
  run (temp-dir + rename swap; orphan prune). Not a symlink — a real committed copy.
- **Rung selection:** rung-1 (has `<L>/` mirror → flatten to view root, mirror wins on
  collision); rung-2 (primary_lang == L → copy base, exclude sibling lang dirs); rung-3
  (no `<L>` content → copy primary base + `[WARN] lang_fallback`).
- **Legacy converge:** a stray `docs/<primary>/components/` from a prior v15 run is moved
  back to `docs/components/` (source) on the first aggregate run.

**LANGUAGE_LAYERS split:**
- `MOVED_LAYERS` = `("system", "generated", "flows", "features", "screens")` — flip/relocate
  move ONLY these layers. `components` is no longer relocated by the layout flip.
- `LANGUAGE_LAYERS` kept as backward-compat alias (includes `components`) for rollback.

**Digest collection:** always reads from SOURCE `docs/components/` (lang-agnostic) regardless
of layout mode. Prior v15 code read from `docs/<primary>/components/` in per-lang mode.

See `docs/decisions/ADR-0002` (supersedes ADR-0001's deferred-flatten stance — the flatten
IS done, but only in the derived view, never in the source).

---

## v19.0.0 — aggregate tier: Python is scanner-only (BREAKING)

**BREAKING** — completes v18's Python-removal. Python no longer generates ANY aggregate document
content (prose, tables, OR Mermaid). `SYNTHESIS_FORMAT_VERSION` → `19.0.0`.

`--aggregate` is now purely the scanner: writes `.system-scout-report.md` as **data tables only**
(no Mermaid) + mechanical `per-component-confidence.md`, and creates **no `.draft.md`**. The
**system-researcher** CREATES each of the 6 system docs from `templates/aggregate/<name>-template.md`
+ the scout report + the components' docs — authoring prose, **building tables, and drawing the
Mermaid itself** (topology/layer/saga). Docs-derived edges now appear IN the charts (v18 had them in
prose only, because Python drew the chart from the thin digest before the docs were read — the root
cause of the stale-chart problem).

- **Removed (Python):** `_build_topology_mermaid_block`/`_build_layer_mermaid_block`/
  `_build_saga_sequence_block`, `render_draft_from_template`, `load_aggregate_template` from
  `_synthesis_scout_lib.py`; the 6-draft emission loop from `synthesize_system.py`.
- **Fidelity → review gate + lint** (was mechanical pinning): new `lint_mermaid_safety()` scans
  authored Mermaid fences for unsafe raw chars; `validate_filled_scaffold(draft)` (single-arg) flags
  leftover `{{FILL}}`/`{{SCOUT}}` + lint violations before promote. `SY-R6` rewritten for LLM-drawn
  charts (every edge traces to scout/cited-doc; no phantom edges; `[UNVERIFIED]`+cited; valid+safe).
- **Templates rewritten:** drop `{{SCOUT}}`; `{{FILL}}` now instructs "BUILD the table" / "DRAW the Mermaid".

Validated end-to-end on `wsm_platform` (reviewer `failed:0`; charts now carry the employee Kafka/gRPC
edges). 1906 pytest green.

**Housekeeping (post-v19):** removed the orphaned Phase-08 reused-mirror trió —
`scripts/mirror_reused_component.py` + `scripts/_reused_mirror_lib.py` +
`scripts/tests/test_reused_mirror_lib.py` — and pruned the runbook's "Delete-original gate" prose. The
CLI was implemented + tested but never invoked (no import, no orchestration reference); the live reused
path is `synth_digest_from_docs.py` (Step 0.5). No behaviour change (it was never called). 1889 green.

---

## v18.0.0 — LLM-authored aggregate tier (scout-report + template) + read-reused-docs (BREAKING)

**BREAKING** — the aggregate (`--aggregate`) tier no longer builds its documents in Python.
`SYNTHESIS_FORMAT_VERSION` → `18.0.0` (forces re-synthesis on the next run).

New model: Python computes facts → `.system-scout-report.md` (services table with `reused` flag +
absolute docs path, edge/fan-in-out/entity/correlation/event tables, pinned topology/layer/saga
Mermaid, confidence) → emits the 6 system docs as `<name>.draft.md` from
`templates/aggregate/<name>-template.md` with `{{SCOUT}}` fact-blocks pre-substituted verbatim
(Python-pinned diagrams/tables = provably faithful). The new **system-researcher**
(`references/system-researcher-contract.md`) AUTHORS the `{{FILL}}` prose, then the v17 Step 3.5
review→fix→promote gate runs (now `SY-R1..R8` over 6 authored artifacts).

- **[Critical rule] Read reused docs — never declare "unobserved" blind.** The researcher MUST read
  each component's docs (without exception for any `reused`/docs-derived component) at the scout-report
  docs path and supplement the heuristic edge list. Calling a read-available component
  "isolated/unobserved" = CRITICAL (`SY-R8`). Root cause: `synth_digest_from_docs.py`'s thin digest
  (WSM `ssv-wsm-employee` had `topic=0` → looked isolated; its docs reveal Kafka consume/produce +
  gRPC to auth & gateway).
- **Removed:** Python scaffold builders (`render_system_overview_scaffold` etc., `render_service_catalog`,
  `render_data_ownership_map`, `render_system_architecture`) and the orphaned `_synthesis_render_topology.py`
  (builders moved to new `_synthesis_scout_lib.py`). `data-ownership-map.md` is now authored; only
  `per-component-confidence.md` stays mechanical.
- **Promote gate:** `validate_filled_scaffold` now flags any remaining `{{FILL}}`/`[FILL]`/`{{SCOUT}}`;
  the H2 add/drop lock is dropped.
- **Per-lang root README removed:** `build_navigation.py` no longer writes a root `docs/README.md` in
  per-lang mode (was a ~3-line pointer in v15-v17). `resolve_root_readme_removal()` deletes a
  purely-generated root README, preserves a hand-written one. Sole entry: `docs/<primary>/README.md`.

Validated end-to-end on `wsm_platform` (1905 pytest green; reviewer `failed:0`).

---

## v17.0.0 — aggregate-tier quality: review gate, charts, reasoned nav, entity dedup (BREAKING)

**BREAKING** — the aggregate (`--aggregate`) promote gate changed. Hybrid artifacts are no longer
promoted on narrative-fill alone; a new **review→fix-cycle→promote** stage (Step 3.5) now stands
between fill and promote. A run whose hybrid drafts fail review after `MAX_FIX_CYCLES = 3` preserves
the drafts and escalates instead of promoting. Output paths are unchanged.

Four fixes, sourced from a real `wsm_platform` aggregate run:

- **Review subsystem + wording rubric (D).** New `references/verification-checklist-system-synthesis.md`
  (`SY-R1..SY-R7`: readability, factual consistency vs digests, `[UNVERIFIED]` honesty, entity-name
  sanity, no-empty-glossary-without-reason, chart coherence, read-first reasoning). The aggregate
  narrative-fill now runs a W7a-style `reviewer`→bounded fix-cycle (mirrors `pipeline-w7-w9.md`,
  reuses `_review_report_lib.mutate_review_report`)→promote gate over the 5 hybrid artifacts; the
  mechanical `per-component-confidence.md` / `data-ownership-map.md` are not reviewed. A human-readability
  **wording rubric** (active voice, define terms, no raw symbol dumps, audience = new engineer) is now
  part of the fill contract — the cheapest quality win. Orchestrator-driven; no new Python.
- **Charts for prose sections (B).** `architecture.md` `## Layer Diagram & Data Flows` now carries a
  role-tiered Mermaid `flowchart TB` (gateway → services → frontend); `cross-service-flows.md` sagas now
  carry a Mermaid `sequenceDiagram` — both scaffolded mechanically (injection-safe) before the fill
  narrative, kept under existing H2 so the promote gate's H2-lock holds.
- **Reasoned reading-order + README dedup (C).** Synthesis writes a side-channel
  `docs/<lang>/system/.nav-metadata.json` (ranked by role tier → fan-in, reused last, with a rationale
  key); `system/README.md` renders a "which service to read first + why" section (lang-aware, omitted
  when the metadata is absent). The parent `docs/<lang>/README.md` is now a thin pointer to
  `system/README.md` instead of duplicating the full reading-order table.
- **Entity dedup + dirty-name filter (A).** `entity_ownership` dedups by canonical `(owner, name)` and
  a shared `_canonical_entity_name` helper drops doc-section headings lifted as entity names
  ("Entity Relationship Diagram", "Entities", "Summary", "Validation Rules") and collapses
  `MODELnnn — X` / `X` variants. Filtered at both the parse source (`parse_entities`) and downstream.
  Plus a per-lang **components relocation** fix: a stray `docs/components` left at the root when the
  system dir was already migrated is now relocated to `docs/<lang>/components` (idempotent, reusing
  `_catchup_components`), independent of the `needs_migration` gate that previously skipped it.

New module `scripts/_nav_metadata_lib.py`. No files removed (no `metadata.json` deletions).

## v16.4.0 — docs refactor (multi-component runbook extracted; no behavior change)

Thinned the always-loaded `SKILL.md` by extracting the ~95-line **Multi-component runbook** block and
the 9 multi-component flag rows (`--root`/`--batch`/`--aggregate`/`--emit-manifest`/`--manifest`/
`--primary-lang`/`--force-aggregate`/`--digest-collect`) into a new on-demand reference
`references/multi-component-runbook.md`. `SKILL.md` keeps a ~6-line stub + a single pointer flag row +
a new "On-demand pipeline loading" directive (load the reference when any multi-component flag is set).
Single-repo runs (the common case) no longer carry monorepo-only detail in context. The
recommended-pass-sequence and all single-repo/pass flags (`--legacy`, `--lang`, `--non-interactive`, …)
stay inline. **No pipeline logic changed** — pure documentation reorganization; every gate, flag, and
contract is preserved verbatim in the reference. Synthesis internals remain in
`system-synthesis-contract.md`; the runbook now cross-links to it.

## v16.1.0 — additive (per-pass batch driver)

`--batch` gains `--pass <feature-specs|screen-specs|flows|glossary>` so the multi-component runbook
can auto-loop the remaining passes per component (Step 1b), the same way core is looped — durable
per-pass status, failure-isolation, cross-session resume. Core `--batch` (no `--pass`) is
BYTE-IDENTICAL; manifest entries gain nested `pass_status`/`pass_fail_reason` (absent ≡ pending —
back-compat). DAG: `flows`/`glossary` require `feature-specs`; `feature-specs`/`screen-specs` need
only core done. Reused/excluded components skip every pass; a pass "done" carries NO sha (output is a
disk-verifiable docs tree). Primitives in `scripts/_manifest_pass_status_lib.py`
(`next_pending_pass`/`mark_pass_done`/`mark_pass_failed`/`pass_summary`). `--aggregate` is orthogonal
(consumes only the core digest); `--lang` still runs last, once, over the whole tree.

## v16.0.0 — BREAKING CHANGE (aggregate doc-tier parity)

The `--aggregate` artifact names are renamed to PARITY with the per-component tier:
`system-overview.md`→`overview.md`, `service-catalog.md`→`component-catalog.md`,
`system-glossary.md`→`glossary.md`; the standalone `interaction-graph.md` is FOLDED into a NEW
`architecture.md` (mechanical topology + edges + fan-in/out + self-loops, plus a hybrid narrative
section). `data-ownership-map.md`, `per-component-confidence.md`, `cross-service-flows.md` keep their
names. The component-catalog gains Dependencies + Module-link + Responsibility (hybrid-fill) columns;
the aggregate `system/README.md` is rewritten to a numbered reading-order table + role reading-paths +
components pointer + principles (no more flat `## Files` list). No migration of existing on-disk
aggregate files (none exist — Validation S1); renderers emit the v16 names from the start and
`_is_aggregate_root` detects on `component-catalog.md` (the unique aggregate artifact —
`architecture.md` is shared with the single-component tier). See
`references/system-synthesis-contract.md`.

## v15.0.0 — per-lang aggregate layout / DOCUMENT-MAP removal

`build_navigation.py` no longer writes `docs/DOCUMENT-MAP.md` or `docs/DOCUMENT-MAP.draft.md` (was
write-only; no reader; machine state lives in `docs/.rebuild-state.json`). `META_FILES` still
recognizes both names so migration deletes any stale copies on next run. In per-lang mode the
top-level `docs/README.md` collapses to a ~3-line pointer to `docs/<primary>/README.md`; the whole
`components/` container relocates to `docs/<primary>/components/`. See `docs/decisions/ADR-0001`.

## v13.1.0 — top-level reading-order `docs/README.md` index (additive)

The navigation pass (`build_navigation.py`) writes a top-level `docs/README.md` "Documentation Index —
Reading Order" landing page — for the primary root AND every `docs/<lang>/` mirror (`--lang`).
Per-language labels, a "Read by role" guide (new-dev / reviewer / PM number-paths), per-layer intros,
and an ordered 4-layer table of concrete one-line descriptions render deterministically (no LLM);
absent artifacts (and the role-path numbers pointing at them) are pruned; 2-zone user tail preserved.
Prose lives in per-language locale modules (`_nav_strings_<lang>.py`); structure + role number-paths in
`_nav_strings.py`; the renderer in `_nav_index.py`.

## v13.0.0 — BREAKING CHANGE (system layer: language-mapped + richer)

`--aggregate` now writes the system layer to the **language-mapped** docs root — `docs/system/` for an
en single-lang repo (byte-identical, no change) but `docs/<primary>/system/` for a per-lang project,
with `primary_lang` discovered by majority across the component `.rebuild-state.json` files (conflict →
majority + `[WARN] lang_conflict`; `--primary-lang` overrides). A flat legacy tree on a per-lang project
is auto-migrated (`migrate_docs_layout`) before writing — no orphaned flat copy. The artifact set is
recut (red-team): `interaction-graph.md` gains a Mermaid topology + fan-in/out summary + self-loop note;
`canonical-entity-model.md` is replaced by `data-ownership-map.md` (ownership + correlation + event
producer→consumers); and `system-overview.md`, `system-glossary.md`, `cross-service-flows.md` are
**hybrid** — Python writes `<name>.draft.md` (idempotent; unfilled markers → `[WARN]
unfilled_scaffold`), a narrative-fill agent completes the prose, then the orchestrator promotes to
`<name>.md` after the post-fill validator passes. See `references/system-synthesis-contract.md`.

## v12.0.0 — BREAKING CHANGE (system-of-systems / multi-component)

The run model gains a multi-component shape for monorepo / polyglot microservice repos: **per-sub-repo
run + one root synthesis pass**, instead of a single root run. `detect_stack_profile.py` now ALSO emits
`components[]` (additive — `recommended_profile` is unchanged, so single-repo callers do not break); a
stateless driver `--batch <manifest>` processes one component per invocation; `--aggregate <root>`
synthesizes the system layer (v12 used `service-catalog.md`, `interaction-graph.md`, … — v16 uses
v16-parity names) over the per-component neutral digests. BREAKING is in the multi-component RUN MODEL
(new flags + the per-component `docs/components/<name>/` layout), NOT in the `detect` output shape.
Single-repo runs (no `--root`/`--batch`/`--aggregate`) are unchanged. See
`references/system-synthesis-contract.md`.

## v11.0.0 — BREAKING CHANGE (stack-profile layer)

Preflight no longer hard-aborts on a missing web manifest. A **stack-profile** (data file under
`references/stack-profiles/*.json`) declares detection globs, source encoding, artifact map, and probe
behavior; legacy non-web stacks (Delphi, Oracle PL/SQL) now run. No profile match → AskUserQuestion
(pick / generic / abort), never auto-abort. **State migration (RT-F4):** `.rebuild-state.json` carries
`schema_version`; resuming a pre-11.0.0 state invalidates the preflight checkpoint and re-runs
`detect_stack_profile.py` + profile-resolve before continuing the wave graph. A pass interrupted under
≤10.x re-runs preflight.

## v5.0.0 — BREAKING CHANGE (CORE-only default)

Default run now produces CORE artifacts only (no feature specs, process-flows, or glossary). Use
`--feature-specs`, `--flows`, `--glossary` standalone passes for those outputs. `--features F###` is
redefined as a scoped subset of `--feature-specs` (was: default-pipeline W6 narrowing). Migration: run
core pass first, then the new passes in order.

## v4.0.0 — per-feature 4-file specs

Per-feature specs split into 4 audience-aware files; `docs/system/architecture.md` and
`docs/generated/permissions-matrix.md` are generated/promoted; process-flows synthesized at FL.1 with an
FL.2 liveness validator (historical numbering: W6.8 / W6.85).
