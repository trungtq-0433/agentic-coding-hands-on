# Verification Checklist: FeatureSpec (FS.5)
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

### FeatureSpec (per-feature, 4 files)

**Cross-refs:** the 9-artifact cross-ref subset (of the 11 core artifacts; excludes Architecture, SystemOverview, PermissionsMatrix).

#### Universal (all 4 files)
- File must exist; non-empty; no `{PLACEHOLDER}` literals outside fenced code/HTML comments.
- F### prefix in folder name matches canonical-fcodes.json slug.
- F### code, feature name, priority match FeatureList entry exactly.

#### TechnicalSpec (technical-spec.md)

**Required sections:** `## Overview` → `## Polymorphic Behavior` → `## Cross-Cutting Logic` → `## User Stories` → `## Key Entities` → `## Artifact References` → `## Assumptions` → `## Source Code References` → `## Unresolved Questions`

**v26.0.0 — additionally required (gated by a DEDICATED validator, NOT the exact-order check above — see Decision 2):** `## Source Walkthrough` (A3) and `## DB Impact per Event` (B4), both appended AFTER `## Unresolved Questions`. `scripts/validate_reading_guide_db_impact.py` enforces a WARN-first `*.pre_migration` degradation contract (see below) — these two headings are deliberately NEVER added to `_spec_constants.REQUIRED_H2_TECH`, so their absence never CRITICALs an un-migrated spec.

**Cross-Cutting Logic structure:** 7 required H3 subsections in order: `### Requirements`, `### Business Rules`, `### Decision Logic`, `### State Machines`, `### Algorithms`, `### External Integrations`, `### Verification`. Empty subsection MUST contain `None.`.

**User Stories structure:** ≥1 `### {US###_CODE} — {Title} (Priority: Pn)` block. Each block: `**What happens:**`, `**Why this priority:**`, `**Independent Test:**`, `**Acceptance Scenarios:**` (Given/When/Then), `**Requirements fulfilled:**` bullets are REQUIRED. `**Rules enforced:**`, `**State transitions:**`, `**Algorithms:**`, `**External integrations:**`, `**Verification:**` are OPTIONAL (omit when not applicable). `### Edge Cases` H3 MUST appear after last US block.

**Format checks:**
- F### code follows `F###_NameSlug`, matches FeatureList entry exactly (code + name + priority).
- US### / SCR### / REG### formats valid (reference code-formats.md).
- BR / SM / ALG / INT codes use `{PREFIX}-###_NameSlug`; per-spec unique; code appears with full `**Source:**` block exactly once.
- Each BR/SM/ALG/INT full block has `**Source:** path:start-end` citation (line range mandatory).
- Each BR/SM/ALG/INT full block has ≥1 `**Linked FR:** FR-###` referencing an FR in the same spec. (Mechanical insertion handled by `scripts/structural_fixer.py` at Wave 7.5; reviewer flags only when placeholder `FR-???` remains.)
- SM full block MUST contain a Mermaid `stateDiagram-v2` fenced block.
- Pseudocode blocks ≤20 lines; no literal `{lang}` in fence; no secrets/credentials.
- Each FR-### appears in exactly one of: a US's `**Requirements fulfilled:**` list OR Cross-Cutting `### Requirements` table.
- Every FR-### declared (whether under a US or in `## Cross-Cutting Logic > ### Requirements`) MUST be covered by ≥1 SC-### via the `(covers …)` back-ref. Uncovered FR = critical (verification missing).
- Each SC-### appears inline in a US's `**Verification:**` list OR in Cross-Cutting `### Verification`; has `(covers FR-### / BR-### / …)` back-ref to ≥1 code in the same spec.
- Cross-US reference format: `BR-### (see US###)` — reference-only, no Source block.
- No H2 heading named `## Requirements`, `## Business Rules`, `## State Machines*`, `## Algorithms*`, `## External Integrations*`, `## Success Criteria`, or `## How It Works`.
- No `## Appendix` heading in submitted draft.

**Cross-refs (9-artifact subset mandatory — of the 11 core artifacts; excludes Architecture, SystemOverview, PermissionsMatrix):**

| Field in spec | Must match |
|---------------|-----------|
| F### code, feature name, priority | FeatureList (exact match) |
| All SCR###/US###/ROUTE###/MODEL###/BL### listed in FeatureList for this F### | Present in spec |
| SCR### codes | Exist in ScreenList |
| US### codes | Exist in UserStories |
| Screen flow references | Match ScreenFlow |
| Routes referenced | Exist in RouteList. **v25.0.0:** `{ROUTE###}` citations in `## Artifact References`' Codes Used column resolve to `route-list.md`'s `Code` column, and (twin-consistency) the citing F### must be IN that route's `Owner F###` set (`validate_feature_api_link.py` enforces both). |
| Entities referenced | Exist in DataModel |
| BL### codes in Artifact References | Exist in BehaviorLogic |
| PERM### codes in Artifact References | Exist in Permissions |
| `**Source:** file:line` cited in BR/SM/ALG/INT blocks | File exists and cited range contains the described logic (reviewer reads to verify) |

Content grounded in actual source code (no fabricated details).

**Critical edge cases:**
- Technical spec missing / empty → critical
- F### not in FeatureList → critical
- Feature name or priority mismatch with FeatureList → critical
- Required section absent or out of order → critical (includes missing `## Polymorphic Behavior` / `## Key Entities` / `## Artifact References` / `## Assumptions` / `## Source Code References` / `## Unresolved Questions`)
- Legacy two-section format detected (`## Related Artifacts` + `## Spec Documents` both present) → **CRITICAL** immediately (no transition window — replace with `## Artifact References` table)
- `## Artifact References` present but missing required rows (System Overview, Feature List, Route List, Data Model, Screen List, Screen Flow, Behavior Logic, Permissions, User Stories) → critical
- `## Artifact References` Codes Used column contains bare REG### without parent SCR### prefix → critical
- Top-level deprecated heading present (`## Requirements` / `## Business Rules` / `## State Machines*` / `## Algorithms*` / `## External Integrations*` / `## Success Criteria` / `## How It Works`) → critical
- FR-### defined but not appearing under any US's `**Requirements fulfilled:**` list or under Cross-Cutting `### Requirements` → critical (orphan FR)
- FR-### declared in `## Cross-Cutting Logic > ### Requirements` but not referenced from any US's `**Requirements fulfilled:**` list AND not covered by any SC-### `(covers …)` back-ref → critical (zombie cross-cutting FR — declared but never consumed).
- FR-### declared anywhere (US or Cross-Cutting) but no SC-### `(covers …)` references it → critical (uncovered FR — no verification path).
- FR-### appearing BOTH under a US AND under Cross-Cutting → critical (ambiguous home)
- SC-### appearing in a dedicated top-level section → critical (must be inline under US or Cross-Cutting)
- SC-### without `(covers …)` back-ref → critical
- SC-### `(covers …)` references a code not defined in this spec → critical
- `## Polymorphic Behavior` section absent entirely → critical
- `## Polymorphic Behavior` present but Key Entities include entity with DISC-### in data-model.md AND section body is `N/A` → critical (false N/A)
- `## Polymorphic Behavior` has DISC-### subsection but one or more known values from data-model.md are missing → critical (incomplete coverage)
- `## Polymorphic Behavior` DISC-### subsection present but not all Key Entities' DISC-### are covered (subsection for DISC-001 present, DISC-002 from same entity missing) → critical
- `## Polymorphic Behavior` behavior cell is blank (empty string, not `unverified`) → warning
- `## Polymorphic Behavior` DISC-### subsection references a DISC-### not present in data-model.md for any entity in Key Entities → critical (phantom discriminator)

**Content depth checks (CRITICAL — these catch shallow/generic specs):**
- `## Cross-Cutting Logic > ### Business Rules` with <3 BRs for UI features → warning (shallow extraction)
- BR/SM/ALG/INT block missing `**Source:** file:line-range` citation → critical
- `**Source:**` cites a non-existent file or invalid/unverified range → critical
- User Story missing `**What happens:**` / `**Why this priority:**` / `**Independent Test:**` → critical
- User Story acceptance scenarios without Given/When/Then structure → warning (vague criteria)
- User Story missing `**Endpoints**: METHOD /path` for its routes → warning
- `### Edge Cases` section missing → critical (must appear under `## User Stories`)
- `### Edge Cases` with <3 rows for UI features or <1 for background features → critical (shallow)
- Edge case rows missing HTTP status code or specific error message → warning
- `## Key Entities` missing or has 0 entity rows → critical
- `## Key Entities` without database table names (just model codes) → warning
- `## Key Entities` with <3 entities for non-trivial features → warning (likely incomplete)
- `## Source Code References` missing or has 0 entries → critical
- `## Source Code References` with <3 entries → warning (likely incomplete)
- `## Source Code References` entries without file path line ranges → warning
- `## Assumptions` missing or has 0 entries → warning
- `## Assumptions` with <2 entries for non-trivial features → warning
- `## Unresolved Questions` missing → warning (expected for complex features)
- `## Artifact References` missing or has 0 rows → critical
- `## Artifact References` missing System Overview or Feature List rows → critical (both are always-required, always-reviewed)
- `## Artifact References` Codes Used column empty for non-overview rows when feature uses that artifact → warning (should list specific codes)
- Same BR/SM/ALG/INT code with `**Source:**` line appearing in 2+ places → critical (duplicate full block; secondary occurrences must be reference-only)
- Cross-Cutting subsection blank (no `None.` under empty H3) → critical
- Any SCR###/US###/ROUTE###/MODEL###/BL### from FeatureList absent in spec → critical
- BR/SM/ALG/INT referencing FR-### not in same spec → critical
- Cross-spec BR/SM/ALG/INT ref (e.g., "see BR-001 in F002") → critical
- SM full block missing Mermaid `stateDiagram-v2` → critical
- Secret/credential leaked in pseudocode → critical
- `## Appendix` heading present in submitted draft → critical
- `### Edge Cases` promoted to H2 or missing from `## User Stories` → critical
- Cross-US reference using a format other than `BR-### (see US###)` (e.g., `BR-### from US###`, `see BR-001`) → warning
- Pseudocode block > 20 lines → warning
- Pseudocode fence contains literal `{lang}` placeholder → warning
- US without priority → warning
- Legacy `## Related Artifacts` section present (deprecated) → **CRITICAL** (no transition window — use `## Artifact References` table)
- Legacy `## Spec Documents` section present (deprecated) → **CRITICAL** (no transition window — use `## Artifact References` table)
- `## Source Walkthrough` (A3, v26.0.0) entirely absent → warning `reading_guide.pre_migration` (un-migrated doc, non-blocking)
- `## Source Walkthrough` present but body empty → critical `reading_guide.malformed`
- `## Source Walkthrough` present but only the unfilled `{...}` template placeholder → warning `reading_guide.unmapped`
- `## Source Walkthrough` reading-list entry cites with `**Source:**` instead of `**File:**` → warning (pollutes the A1 confidence-report citation-coverage stat; see `references/confidence-report-contract.md` § A3 navigational entries)
- `## DB Impact per Event` (B4, v26.0.0) entirely absent → warning `db_impact.pre_migration` (un-migrated doc, non-blocking)
- `## DB Impact per Event` present but body empty, or non-N/A prose with no parseable table → critical `db_impact.malformed`
- `## DB Impact per Event` table present but only placeholder rows → warning `db_impact.unmapped`
- `## DB Impact per Event` row's Operation cell has a blank Source (no `file:line` citation, no `[INFERRED]` tag) → warning `db_impact.uncited`
- `## DB Impact per Event` nested under `## Cross-Cutting Logic` instead of top-level H2 → warning (validator symmetry with A3; keeps `REQUIRED_CCL_H3` untouched)

#### BusinessContext (business-context.md)

**Required sections:** `## Why It Matters` → `## Who Uses It` → `## What They Do`

- Plain-language rubric (reviewer manual check):
  - **Persona clarity**: each persona named with role + concrete action; not "the user" only.
  - **Workflow specificity**: numbered steps use business verbs ("submits", "approves"), NOT technical verbs ("POST", "dispatches").
  - **Jargon score**: zero forbidden tokens (auto-validated by `validate_feature_spec.py`); plus subjective check for terms like "endpoint", "schema", "controller".
- "Why It Matters" must reference real user problem, not "system feature".
- If feature participates in a cross-feature flow → plain-language cross-ref to `flows/{slug}.md` present.
- Rubric scoring: 0–3 per criterion; threshold ≥2 = pass.

**Critical edge cases:**
- Required section absent → critical
- Forbidden token detected outside fenced code/HTML comments → critical (auto-validated)
- "Why It Matters" reads as fabricated rationale → warning

#### Screens (screens.md)

**Required sections:** `## Screen List` → `## User Journey`

- Screen List table present for UI/mixed features; "N/A — background feature" for background-only.
- **v24.0.0:** Screen List is 4-column (`Screen Name | SCR### | What User Sees | What User Can Do`); each `SCR###` resolves to a `screen-list.md` row (`validate_feature_screen_link.py`).
- User Journey numbered steps reference screen names but NOT routes/endpoints.

**Critical edge cases:**
- Required section absent → critical
- Screen List missing for UI feature → critical
- SCR### column present but a code does not resolve to screen-list.md → critical (`link.scr_unresolved`); column entirely absent on an un-migrated doc → warning (`link.pre_migration`, non-blocking)
- User Journey references routes/endpoints instead of screen names → warning

#### EdgeCases (edge-cases.md)

- Single table; columns: Scenario | What Happens | User-Facing Message.
- ≥3 rows for UI features; ≥1 row for background.
- "User-Facing Message" must be plain language; "HTTP 400" alone is REJECTED.

**Critical edge cases:**
- Table missing or has 0 rows → critical
- <3 rows for UI features → critical
- "User-Facing Message" contains raw HTTP code without explanation → warning

### FlowsDraft (per inferred flow, `flows/{slug}.md`)

**Cross-refs:** UserStories, ScreenFlow

- Frontmatter present: `status: ai-draft | human-curated`; `source: [US###, SCR###, ...]`; `generated: ISO-8601`.
- Slug kebab-case ≤40 chars; no collision with existing flow file (unless suffixed -2/-3 with `[WARN]`).
- Spans ≥2 features (cross-feature requirement); single-feature flows belong in feature's screens.md.
- Plain-language: same forbidden-tokens regex as BusinessContext. Any match = critical.
- "Open Questions" section present (may be `None.`).
- `## Diagram` section present after `## Steps`; contains a fenced ` ```mermaid ` block with at least 3 lines (non-empty diagram).
- Mermaid block opens with `flowchart TD` directive.
- Simplified flows (>10 steps or >3 diamonds): mermaid block contains `%% simplified: complex flow` comment on first line inside the block.
- `flows/.completed` marker present after FL.1 completes (former W6.8) (zero-byte if flows emitted; contains `no_flows_inferred` if zero-output).

> **Note:** process-flow files are reviewed by the flows pass FL.3 reviewer (see `pipeline-flows-glossary.md`); the FL.2 liveness validator (former W6.85) enforces deterministic citation/format checks before FL.3.

**Critical edge cases:**
- Frontmatter missing or malformed → critical
- `source:` entries empty → critical
- Transition row without `file:line` citation → critical (contract violation)
- Forbidden token in prose → critical
- `.completed` marker absent after FL.1 task completes (former W6.8) → warning (task may have failed silently)
- Derived view modeled as stored state → critical (fabricated state)

### Large Feature Handling

- If feature dir total > 500 lines across 4 files, orchestrator reduces FS.5 batch size to 2-3 features.
- W7a reviewer processes core artifacts >600 lines section-by-section. Reviewer agent MUST NOT skip sections — receives section range in TaskCreate description.
- Large output (>400 lines per file) triggers 2-pass drafting: Pass 1 = structure + entities + BR; Pass 2 = SM/ALG/INT. File path reference, not inlined.


## Deterministic Validator Coverage

These `rule_id`s are pre-checked by `scripts/validate_*.py` BEFORE the FS.5 reviewer runs. When `fs-validation-summary.json` reports a rule as `PASS`, the reviewer marks that rule `[deterministic-pass]` and focuses on semantic depth instead. When a rule is `FAIL`, the orchestrator dispatches an `implementer` fix cycle before FS.5 runs (see `pipeline-feature-specs.md § Wave FS.2`).

| rule_id | validator script | severity |
|---------|------------------|----------|
| existence.folder_missing | validate_feature_existence.py | critical |
| existence.folder_incomplete | validate_feature_existence.py | critical |
| existence.slug_format | validate_feature_existence.py | critical/warning |
| existence.orphan_folder | validate_feature_existence.py | warning |
| existence.canonical_missing | validate_feature_existence.py | warning |
| FeatureSpec.required_sections | validate_feature_spec.py | critical |
| FeatureSpec.ccl_subsections | validate_feature_spec.py | critical |
| FeatureSpec.ccl_blank | validate_feature_spec.py | critical |
| FeatureSpec.screen_flow_crossref | validate_feature_spec.py | critical |
| FeatureSpec.bw_steps | validate_feature_spec.py | critical |
| FeatureSpec.deprecated_headings | validate_feature_spec.py | critical |
| FeatureSpec.no_appendix | validate_feature_spec.py | critical |
| FeatureSpec.edge_cases | validate_feature_spec.py | critical |
| FeatureSpec.f_code_format | validate_feature_spec.py | critical |
| FeatureSpec.sm_mermaid | validate_feature_spec.py | critical |
| FeatureSpec.pseudocode_length | validate_feature_spec.py | warning |
| FeatureSpec.pseudocode_fence | validate_feature_spec.py | warning |
| Universal.no_placeholder | validate_feature_spec.py | critical |
| citation.file_missing | validate_source_citations.py | critical |
| FeatureSpec.linked_fr_missing | validate_feature_spec.py | critical |
| FeatureSpec.disc_boolean | validate_feature_spec.py | warning |
| citation.range_invalid | validate_source_citations.py | critical |
| citation.range_inverted | validate_source_citations.py | critical |
| citation.path_traversal | validate_source_citations.py | critical |
| citation.unreadable | validate_source_citations.py | warning |
| FeatureSpec.br_linked_fr_present | structural_fixer.py | critical |
| FeatureSpec.polymorphic_behavior_present | validate_feature_spec.py | critical |
| FeatureSpec.decision_logic_section_present | validate_feature_spec.py | critical |
| FeatureSpec.dec_blocks_well_formed | validate_feature_spec.py | critical/warning |
| FeatureSpec.dec_lazy_na | validate_feature_spec.py | warning |
| FeatureSpec.missing_client_behavior_anchor | validate_feature_spec.py | critical |
| bc.missing | validate_feature_spec.py | critical |
| bc.missing_h2 | validate_feature_spec.py | critical |
| bc.forbidden_token | validate_feature_spec.py | critical |
| screens.missing | validate_feature_spec.py | critical |
| screens.missing_h2 | validate_feature_spec.py | critical |
| edge_cases.missing | validate_feature_spec.py | critical |
| edge_cases.few_rows | validate_feature_spec.py | warning |
| BehaviorLogic.file_schema_missing | validate_behavior_logic.py | warning |
| FeatureSpec.alg_file_schema_missing | validate_feature_spec.py | warning |
| link.route_unresolved | validate_feature_api_link.py | critical |
| link.feature_unresolved | validate_feature_api_link.py | critical |
| link.owner_mismatch | validate_feature_api_link.py | critical |
| link.pre_migration | validate_feature_api_link.py | warning |
| link.unmapped | validate_feature_api_link.py | warning |
| link.inventory_absent | validate_feature_api_link.py | warning |
| gate.files_incomplete | check_promotion_gate.py | critical |
| gate.pending_marker | check_promotion_gate.py | critical |
| gate.validation_summary | check_promotion_gate.py | warning |
| reading_guide.pre_migration | validate_reading_guide_db_impact.py | warning |
| reading_guide.malformed | validate_reading_guide_db_impact.py | critical |
| reading_guide.unmapped | validate_reading_guide_db_impact.py | warning |
| db_impact.pre_migration | validate_reading_guide_db_impact.py | warning |
| db_impact.malformed | validate_reading_guide_db_impact.py | critical |
| db_impact.unmapped | validate_reading_guide_db_impact.py | warning |
| db_impact.uncited | validate_reading_guide_db_impact.py | warning |

> **Note:** `FeatureSpec.polymorphic_behavior_present` only checks section presence (not N/A validity or value coverage — those require semantic reading). The validator checks: `## Polymorphic Behavior` heading exists in the spec file.

> **Note:** `FeatureSpec.decision_logic_section_present` checks `### Decision Logic` H3 presence in CCL (covered by `FeatureSpec.ccl_subsections`). `FeatureSpec.dec_blocks_well_formed` checks structural fields per DEC block (subtype, Triggers in, user_visible_outcome, Source, pseudocode ≤8 lines). `FeatureSpec.dec_lazy_na` uses grep to flag JSX-ternary patterns when section says N/A — raises warning for reviewer attention (not auto-fail). Source-file location is NOT validated per scope-agnostic rule. `FeatureSpec.missing_client_behavior_anchor` checks for `**Client behavior:** see` anchor block in `## Cross-Cutting Logic` — mandatory even when all linked sections (behavior-logic.md, permissions.md, screen-flow.md) are N/A.

Rules NOT in this table remain reviewer-only (e.g., FR/SC coverage cross-refs, BR depth heuristics, cardinality cross-check, composite detection — these need semantic judgement).


## Failure Trap Assertions

- **Trap 1 (proliferation):** every REG has ≥1 independence signal, drawn from: distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Missing signal → critical. Visual separation alone is NOT sufficient.
- **Trap 2 (tab/stepper misclassification):** mutually-exclusive tab content declared as REG (not SCR variants) → critical. Wizard/stepper content: Case A emitted without cited distinct-validation + distinct-endpoint evidence → warning (prompt researcher to re-evaluate as Case B). 2-step wizard emitted as Case A → critical.
- **Trap 3 (shared data):** collapse two REG candidates into one Feature ONLY when they share ALL of: read surface (same GET endpoint/store) AND write surface (same mutations) AND business workflow. Shared initial payload alone does NOT disqualify a split — if regions diverge on write endpoints, validation rules, action paths, or business workflow, they remain separate. Researcher self-check advisory (NOT reviewer-enforceable critical — reviewer cannot inspect codebase at review time).
- **Trap 4 (LOC-based over-split):** LOC is NOT a composite signal. H3 uses named wrapper components only. Advisory note: flag any ScreenList entry where the researcher's justification cites line count rather than named wrappers or import count.
- **Trap 5 (spec orphan):** every REG### in ScreenList must have an owner annotation (can be `TBD`) → critical if owner annotation missing entirely.
- **Trap 6 (inferred-signal abuse):** `[SIGNAL_INFERRED]` tag without all 3 justification parts (Intent matched, No-row reason, Observed pattern) → critical. Tag citing H1 (which has no signal table) → critical; H2–H6 only. Tag used to bypass a per-stack row that DOES match the screen's stack/library naming → critical (researcher must use explicit row first). Tag count exceeding `max(5, ceil(0.10 × SCR_count))` across the entire ScreenList document → warning (suggests per-stack tables need updating or stack/library not covered).
