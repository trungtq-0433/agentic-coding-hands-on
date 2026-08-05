<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: Core Artifacts (W7a)
<!-- Updated: Phase-02 strip — ProcessFlow section moved to verification-checklist-flows.md (loaded by --flows FL.3). Glossary section was not present here; GL-R1..GL-R6 live in verification-checklist-glossary.md (loaded by --glossary GL.2). -->
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope (default/core run):** SystemOverview, Architecture, RouteList, DataModel, ScreenList, ScreenFlow, BehaviorLogic, Permissions, PermissionsMatrix, UserStories, FeatureList.
**Profile-conditional artifacts (v21.0.0):** RouteList and ApiMap are reviewed ONLY when the profile produces them (`produce("route-list")` / `produce("api-map")` — web/route-view stacks). ScreenList and ScreenFlow are reviewed ONLY when `produce("screen-list")` is true (web route-view AND Delphi dfm-form; NOT headless screen_source:none). When an artifact was not produced, its file is absent — do NOT flag the absence and do NOT apply its rules. This mirrors the CrudMatrix/DbObjects "applied only when the file exists" pattern below.
Do NOT apply ProcessFlow rules (PF-S*) here — those are in `verification-checklist-flows.md`, loaded by the `--flows` pass FL.3.
Do NOT apply Glossary rules (GL-R*) here — those are in `verification-checklist-glossary.md`, loaded by the `--glossary` pass GL.2.

## Artifacts

### SystemOverview

**Cross-refs:** codebase package files (technology accuracy), FeatureList

**Required sections:** `# System Overview` (Project/Generated/Architecture Type) → `## Executive Summary` → `## System Architecture` → `### High-Level Architecture` (Mermaid graph TB) → `### Technology Stack` (Layer|Technology|Version) → `## Data Flow` (Mermaid sequenceDiagram) → `## Key Design Decisions` (min 2 × Context/Decision/Rationale) → `## Security Overview` → `## Scalability`

**Format checks:** both Mermaid diagrams present; Technology Stack has Layer/Technology/Version columns; heading hierarchy correct.

**Critical edge cases:**
- Missing Mermaid diagram → critical
- Technology documented but not in codebase → critical
- Technology in codebase but not documented → critical
- Mermaid syntax invalid → warning
- Key Design Decision missing Context/Decision/Rationale → warning

### Architecture

**Cross-refs:** codebase package/manifest files (tech stack accuracy), SystemOverview

**Required sections:** per `architecture-template.md` — `# Architecture` → `## System Architecture` (Mermaid graph) → tech-stack listing.

**Format checks:** at least one Mermaid diagram present and syntactically valid; tech stack entries match the codebase manifests.

**Critical edge cases:**
- Missing Mermaid diagram → critical
- Technology documented but not in codebase → critical
- Technology in codebase but not documented → critical
- Mermaid syntax invalid → warning

### RouteList

**Deterministic checks (`validate_route_list.py` — pre-W7a):** single header/preamble, no duplicate route IDs (Method+Path), handler citation presence, required sections. Rule IDs passing the validator are marked `[deterministic-pass]` — skip in semantic review.

**Cross-refs:** codebase routes (`**/routes*.{php,js,ts,rb}`, `**/api*.{php,js,ts}`), FeatureList

**Required sections:** per `route-list-template.md`

**Format checks:** route path format valid (`METHOD /path`); handler references match actual code.

**Cross-refs:** every route in codebase must appear here. **v25.0.0:** Backend Routes is 6-column (`Method | Path | Code | Owner F### | Handler | Middleware`); `Code` is the canonical `ROUTE###`, `Owner F###` carries the bare feature code that claims the route (`—` when unattributable; comma-separated for rare shared routes) — the forward (`technical-spec.md`/`behavior-logic.md` citation → RouteList) and reverse (`Owner F###` → FeatureList) directions, plus twin-consistency between them, are enforced by `validate_feature_api_link.py`.

**Critical edge cases:**
- Route in codebase but not documented → critical
- Route documented but no F### in FeatureList references it → critical
- Route path/method doesn't match actual code → warning
- Route format invalid → warning

### DataModel

**Cross-refs:** codebase model files (`**/models/**/*.{js,ts,php,rb}`, `**/entities/**/*.{js,ts,php}`), FeatureList

**Required sections:** per `data-model-template.md`

**Format checks:** entity/attribute format valid; relationship types correct.

**Cross-refs:** every model in codebase must appear here; DataModel does NOT contain F### mapping.

**Critical edge cases:**
- Entity in codebase but not documented → critical
- Entity documented but no F### in FeatureList references it → critical
- Attribute format invalid → warning
- Relationship doesn't match actual model → warning
- Entity in codebase has enum/constant-type field but no `**Discriminator Fields**` block → critical
- `**Discriminator Fields**` block present but DISC-### IDs not unique within document → critical
- DISC-### values list does not match actual enum definition in source (missing or extra values) → warning (reviewer reads model source to verify)
- DISC-### entry for a boolean field (only `true`/`false` values) → warning (boolean flags belong in Business Rules, not DISC; validator also flags via `FeatureSpec.disc_boolean`)
- `**Discriminator Fields**: None.` written for entity that has enum/constant-type fields in source → critical

### DataModel (W1.5 structural gate — scoped)

W1.5 reviewer checks ONLY these 5 items. Full DataModel review at W7a.

**Check 1 — Entity completeness (critical):**
- Each entity has name, description, at least one typed field
- Fail: entity with no fields, or entity with fields but no types documented

**Check 2 — DISC-### scope (critical):**
- Each DISC-### has ≥2 enum values with distinct behavioral outcomes
- Fail: DISC-### with `true`/`false` only (boolean flags belong in Business Rules)
- Fail: DISC-### with single value (not a discriminator — remove or expand)

**Check 3 — MODEL### uniqueness (critical):**
- No duplicate MODEL### codes across the document
- Fail: MODEL001 appears in two different entity blocks

**Check 4 — DISC-### anchor (critical):**
- Each DISC-### code is anchored to a specific entity's field
- Fail: DISC003 appears in Polymorphic section but no entity has a field mapped to DISC003

**Check 5 — Relationship completeness (warning):**
- Each relationship entry has source entity, target entity, cardinality
- Warning: missing cardinality

**Token budget:** data-model.md only. No cross-artifact loading.

### ScreenList

**Deterministic checks (`validate_screen_list.py` — pre-W7a):** single Screen Index section, no duplicate SCR### codes, no duplicate REG### within same parent SCR, every REG### has in-document parent SCR (orphan-REG = critical), required sections. Rule IDs passing the validator are marked `[deterministic-pass]`.

**Cross-refs:** screen/view/component source files inventoried in `scout-report.md` (reviewer uses W0 scout inventory — avoids framework-specific extension assumptions; exact dirs and extensions are project-language-dependent), FeatureList, RouteList

**Required sections:** per `screen-list-template.md`

**Format checks:** all SCR### codes follow `SCR###_NameSlug`; each screen has ≥1 US### mapped; each screen has a route in RouteList **(route-view stacks only — when `produce("route-list")` is false, e.g. Delphi `dfm-form`, there is no RouteList: SKIP this route check and instead require each screen to carry an invocation/source citation `file:line`)**.

**Cross-refs:** ScreenList does NOT contain F### or US### mapping (feature → FeatureList; US → UserStories).

**Critical edge cases:**
- Screen in codebase but not documented → critical
- Screen documented but no F### in FeatureList references it → critical
- Screen has no US### mapped → critical
- Screen has no route in RouteList → critical **[route-view only — gated on `produce("route-list")`; SKIP entirely when no RouteList is produced (Delphi `dfm-form`, headless). On those stacks the equivalent gate is: screen has no invocation/source citation `file:line` → critical. An `[UNVERIFIED]`-reachability screen is NOT a violation: it still carries a form-definition `file:line`.]**
- Service coverage: a service/API hook/helper module used by the screen's page file or its immediate component/partial/helper dependencies (per scout-report.md inventory) has no matching ROUTE### in RouteList AND no matching BL### in BehaviorLogic → critical **[route-view only — gated on `produce("route-list")`; when no RouteList is produced, require a matching BL### in BehaviorLogic alone]**
- SCR### format invalid → warning
- Router-outlet grouping [H6-VIOLATION]: a screen documented as composite (with REG regions) where the source file's primary content is a router outlet (per-stack H6 outlet signals in `composite-screen-detection.md § H6`) AND child routes each have a distinct URL path segment — should be separate SCR entries, not REG regions → critical
- Parent shell without own API: a screen with zero independent API calls (only renders router outlet) documented as its own SCR entry, with no persistent layout content (sidebar, timeline nav) → warning; shell context belongs in each child SCR description
- Over-merged screen [OVER-MERGED]: flag for researcher review → warning. Fires when ANY of the following is true: (a) single SCR contains a wildcard route pattern (`/x/*`, `/x/**`, `:splat`, `/...`) — must expand to concrete child routes per composite-screen-detection.md § Composite Hard Guard; (b) namespace-prefix covering ≥2 distinct controllers/handlers collapsed into one SCR — split per H6; (c) single SCR listing ≥3 URL patterns of structurally different depth (not just :id param variants — e.g. /batches, /compare, /batch-results under same parent path) — candidate for H6-split

### ScreenFlow

**Deterministic checks (`validate_screen_flow.py` — pre-W7a):** single Navigation Map section, no duplicate SCR### in Screen Transitions subsections, required sections (Navigation Map, Screen Access Paths, Screen Transitions). Rule IDs passing the validator are marked `[deterministic-pass]`.

**Cross-refs:** ScreenList (SCR### completeness), FeatureList

**Required sections:** per `screen-flow-template.md` (includes `## Feature Entry Points` H2)

**Format checks:** all SCR### in flow exist in ScreenList; navigation transitions documented.

**Cross-refs:** every SCR### in ScreenList must appear in ScreenFlow.

**Critical edge cases:**
- SCR### in ScreenList but not in ScreenFlow → critical
- SCR### in ScreenFlow but no F### in FeatureList references it → critical
- Circular navigation dependency → critical
- Screen transition doesn't match actual navigation → warning
- Auth flow not documented → warning
- `## Feature Entry Points` section absent from screen-flow.md → warning
- `## Feature Entry Points` has raw `{POPULATED_BY_W6}` token (not an HTML comment) → critical (W9 default promotion should have replaced it — re-run W9 or run `--feature-specs` pass to populate real content)

### BehaviorLogic

**Deterministic checks (`validate_behavior_logic.py` — pre-W7a):** single Behavior Logic Index section, no duplicate BL### codes, Source File/Source Symbol presence per BL section, optional 1-BL-per-scout-inventory-entry cardinality (when `--scout-bl-inventory` passed). Rule IDs passing the validator are marked `[deterministic-pass]`.

**Cross-refs:** RouteList (ROUTE### refs), DataModel (MODEL### refs), FeatureList, scout-report.md `## Background Logic Source Inventory`

**Required sections:** `# Background Logic` → `## Background Logic Index` (Code|Name|Type|Trigger) → `## Background Logic Details` → `## Summary` → `## Cross-Reference Validation`

**Format checks:** all BL### follow `BL###_NameSlug`; codes unique; valid Type values (canonical 10): `custom-command`, `event-listener`, `integration`, `mail`, `middleware`, `notification`, `observer`, `queue-worker`, `scheduled-job`, `webhook`; each item has Type + Trigger + Description + Related Modules + Source File + Source Symbol.

**Cross-refs:** referenced ROUTE### must exist in RouteList; referenced MODEL### must exist in DataModel; overlap check: same name+different BL### or >50% keyword overlap = critical.

**Critical edge cases:**
- Duplicate BL### codes → critical
- BL### format invalid → critical
- Missing Type, Trigger, or Description → critical
- Invalid Type value (not in canonical 10) → critical
- BL item missing `Source File` field → critical
- BL item missing `Source Symbol` field → critical
- BL item `Source Symbol` containing multi-symbol delimiter — `,`, `;`, or whitespace-bounded ` and ` / ` & ` / ` + ` → critical (aggregation; split into separate BL items). `/` is excluded (overlaps composite refs / paths); `+`/`&` only count when surrounded by whitespace to avoid false-positives on Swift `MyClass+Extension` and similar single-symbol forms.
- Referenced ROUTE### not in RouteList → warning
- Referenced MODEL### not in DataModel → warning
- BL Source File not found in scout BL inventory → warning (researcher must justify in Description)
- Payload presence — notification/event/webhook BL items that dispatch async data SHOULD carry `**Payload**` (channel/topic + data fields); missing on those types → warning (not critical — extraction is best-effort). Scheduled-job/middleware/custom-command types are exempt.

**Cardinality Cross-Check** (load scout `## Background Logic Source Inventory` before running):

Run per-stack, then take MAX gap across stacks (do NOT OR-merge — see bl-source-patterns.md § Multi-Stack Handling).

1. **Total count gap** — for each stack subsection: `gap = abs(inventory_count − bl_count) / max(inventory_count, 1) × 100`. Both undershoot and overshoot count. Bounds use strict-inequality semantics — boundary values fall in the lower band.
   - `gap ≤ 5%`: PASS
   - `5% < gap ≤ 15%`: warning + list uncovered entries (or BL items not backed by inventory)
   - `gap > 15%`: critical
   - Small-project floor: if `max(inventory_count, bl_count) < 20`, switch to absolute thresholds — `abs gap ≤ 2`: PASS; `2 < abs gap ≤ 4`: warning; `abs gap > 4`: critical.
   - **Overshoot diagnosis** (bl_count > inventory_count): surplus is either (a) duplicate BLs sharing a Source File with no distinct Source Symbol → critical (Rule C1 violation), or (b) BL items without inventory backing → check Rule 3.
2. **Category drop** — for each category present in inventory with ≥ 1 entry: artifact must have ≥ 1 BL of matching type. Category present in inventory but 0 BL of that type → critical.
3. **Source File check** — BL item with no `Source File` field → critical (already covered above). BL Source File not in any inventory entry → warning.
4. **Orphan file** — inventory entry with no matching BL Source File → critical (one finding per orphaned file).
5. **Inferred ratio (per stack)** — applies ONLY to stacks listed in `references/bl-source-patterns.md` table AND NOT the `### Unknown` no-manifest subsection. Stacks outside the table (e.g., Phoenix Elixir) and `### Unknown` are exempt — 100% inferred is expected and Rule 5 does not fire. For applicable stacks: `inferred_ratio = signal_inferred_count / stack_inventory_count` (both counts read from scout report § Background Logic Source Inventory, same stack subsection). Strict-inequality semantics — boundary values fall in the lower band. Thresholds preliminary; calibrate after smoke test.
   - **Guard (applied AFTER exemption check):** if `stack_inventory_count == 0`, skip ratio check (division undefined). If also `signal_inferred_count > 0`, that is a scout self-contradiction → critical.
   - `ratio ≤ 20%`: PASS
   - `20% < ratio ≤ 50%`: warning ("verify Mode A globs / Mode B grep coverage; non-standard libraries may be legitimate")
   - `ratio > 50%`: critical ("scout likely skipped per-stack patterns; re-scan required")
6. **Exclusion-pattern leak** — BL Source File matching scout filename-level exclusions → critical (scout-side filter failure; researcher cannot fix — re-run scout). Patterns:
   - **Test files (per language):** `*Test.{php,java,kt}`, `*Tests.cs`, `*_spec.rb`, `test_*.py`, `*_test.py`, `*_test.go`, `*.test.{ts,tsx,js,jsx}`, `*.spec.{ts,tsx,js,jsx}`, `tests/*.rs`
   - **Abstract bases:** `Abstract*.{php,java,kt,ts,cs}`, `*Base.{php,java,kt,ts,cs}`
   - **Vendor paths:** `vendor/`, `node_modules/`, `Pods/`, `.venv/`, `target/`
   LOC and auth-classification checks remain scout-side; if a leaked file passes filename heuristics, surface in next re-scan.

Reviewer output format for Cardinality Cross-Check:

```markdown
### BehaviorLogic Cardinality
- Inventory total: {N}
- Artifact BL count: {N}
- Gap: {X}% ({PASS|WARNING|CRITICAL})
- Missing categories: {type1, type2, ...} or none
- Orphan files: {path1}, {path2}, ... or none
```

Multi-stack example: "Laravel gap 2%, NestJS gap 67% (CRITICAL); max=67% → CRITICAL"

### Permissions

Curated, plain-language view (promoted to `docs/system/permissions.md`). Derived FROM PermissionsMatrix.

**Cross-refs:** PermissionsMatrix (must be consistent with the raw matrix it derives from)

**Required sections:** per `permissions-template.md` — `# Permissions` → `## Authorization System Type` → `## Curated View` → `## Access Boundaries` → `## Special Conditions`

**Format checks:** valid Auth System Type: `rbac`, `abac`, `acl`, `ownership`, `hybrid`, `other`; Curated View is plain language.

**Critical edge cases:**
- Missing Authorization System Type section → critical
- Invalid Authorization System Type value → critical
- Contains `PERM###` codes or raw matrix tables (belong in PermissionsMatrix, not the curated view) → critical
- Curated View contradicts PermissionsMatrix roles → warning

### PermissionsMatrix

Raw PERM### matrix (promoted to `docs/generated/permissions-matrix.md`). Written FIRST; the curated Permissions view is derived from it.

**Cross-refs:** RouteList (ROUTE### refs), ScreenList (SCR### refs), FeatureList

**Required sections:** `# Permissions Matrix` → `## Permissions Index` (Code|Name|Type|Enforced At) → `### PERM###: Name` subsections → `## Summary` → `## Cross-Reference Validation`

**Format checks:** all PERM### follow `PERM###_NameSlug`; codes unique; valid Permission Type: `route-guard`, `screen-permission`, `action-permission`, `data-permission`, `role-based`, `resource-ownership`, `field-permission`, `api-scope`, `feature-flag`, `experiment`, `env-gate`, `locale-gate`; each item has Type + Enforced At + Description + Related Modules; for traditional types also Permission Rules matrix; for client-side gate types (`feature-flag`, `experiment`, `env-gate`, `locale-gate`) use `source:` field instead of Permission Rules matrix.

**Cross-refs:** referenced ROUTE### must exist in RouteList; referenced SCR### must exist in ScreenList; overlap check same as BehaviorLogic.

**Critical edge cases:**
- Duplicate PERM### codes → critical
- PERM### format invalid → critical
- Missing Type, Enforced At, Description, or Permission Rules → critical
- Same route/screen with conflicting permissions → warning
- Referenced ROUTE### not in RouteList → warning
- Referenced SCR### not in ScreenList → warning

### UserStories

**Cross-refs:** ScreenList (SCR### count + refs), BehaviorLogic (BL### refs), Permissions (actor split), FeatureList

**Required sections:** per `user-stories-template.md`

**Format checks:** all US### follow `US###_NameSlug`; `ui` type US has ≥1 SCR### in Screens section; `system` type US has ≥1 BL### in Background Logic section; UI US count ≥ SCR### count in ScreenList.

**Cross-refs:** actor split — if Permissions shows different roles have different access → verify US split by actor.

**Critical edge cases:**
- UI US count < UI Screen count → critical
- US### not referenced by any F### in FeatureList → critical
- UI US### has no SCR### mapped → critical
- System US### has no BL### mapped → critical
- Referenced SCR### not in ScreenList → warning
- Referenced BL### not in BehaviorLogic → warning
- US combines multiple user actions (compound title with "and"/"or", multiple verbs, or CRUD grouping like "manage"/"CRUD"/"create/edit/delete") → critical
- US title uses compound/vague action verbs ("manage", "handle", "CRUD", "create/edit", "create or edit") → critical; split into separate US per verb
- US title contains "/" separating two actions (e.g., "Create/Edit User") → critical
- Destructive action (Delete/Remove/Revoke/Deactivate) visible on a screen with no dedicated US → critical [IPE_MISSING_DESTRUCTIVE]
- Screen with ≥3 distinct buttons/actions in source but only 1 US mapped → warning [IPE_SPARSE]; note screen for researcher re-pass
- Interaction Inventory table absent or empty when UI screen count > 0 → warning
- Two US sharing the same merge key AND actor → warning [IPE_MERGE_CANDIDATE]; verify merge exception applies (same data flow required). **Merge key is per-stack (v21.0.0, per `screen_source`):** `route-view` (web) → identical HTTP endpoint (method + path); `dfm-form` (Delphi) → same event-handler procedure (NOT same table — same-table over-merges). Apply the key matching the run's profile; on a `dfm-form` run, endpoint identity never holds, so checking it would never fire — use handler identity.
- Multiple distinct actors combined in single US (e.g., "Admin and User") → warning
- Acceptance criteria vague/non-testable → warning
- US missing priority → warning

### UserStories (W4.5 quality gate — scoped)

W4.5 reviewer checks ONLY these 5 items. Full UserStories review at W7a.

**Check 1 — Single intent (critical):**
- Each US### has exactly one user action in goal
- Fail: "create, edit, and delete" in one story; "as well as" joining distinct actions
- Only flag critical when verbs describe CLEARLY DISTINCT independent actions

**Check 2 — Human actor (critical):**
- Actor is a named human role (user, admin, manager, guest)
- Fail: actor is "system", "app", "platform", or missing

**Check 3 — Outcome present (warning):**
- "so that..." or equivalent user-visible value statement
- Warning: story missing outcome

**Check 4 — Overly broad scope (warning):**
- Goal uses generic management verb without specific action
- Warning: "manage all user data", "administer the system"
- Acceptable: "manage my account settings" (specific resource, clear scope)

**Check 5 — US### uniqueness (critical):**
- No duplicate codes
- Fail: US005 appears twice

**Token budget:** user-stories.md only.

### FeatureList

**Cross-refs:** UserStories, ScreenList, RouteList, DataModel, BehaviorLogic, Permissions (all codes cross-validated)

**Required sections:** `# Feature List` → `## Feature Hierarchy` (Code|Name|Type|Language|Workspace|Priority) → `## Feature Details` → `## Summary` → `## Cross-Reference Validation`

**Format checks:** all F### follow `F###_NameSlug`; codes unique; valid Type: `ui`, `background`, `mixed`; feature names specific (not "Management", "CRUD").

**Feature type rules:** `ui` → SCR### required; `background` → BL### required, no SCR###; `mixed` → SCR### + BL### both required. PERM### optional for all types.

**Valid feature criteria (all 4):** Single Intent, Clear Flow (input→process→output), Independently Testable, Agent Implementable. Same name+different F### or >50% keyword overlap = critical.

**Cross-refs:**
- All US###/SCR###/ROUTE###/MODEL###/BL###/PERM### in feature must exist in their source artifact
- Every BL### in BehaviorLogic must be referenced by ≥1 F### (orphan BL### → missing-feature-log)
- Every PERM### in Permissions must be referenced by ≥1 F### (orphan PERM### → missing-feature-log)
- Read missing-feature-log at start → report each item as critical → clear log

**Critical edge cases:**
- Duplicate F### codes → critical
- Feature with multiple intents or no clear flow → critical
- Orphaned US###/SCR###/ROUTE###/MODEL### in feature → critical
- BL### in BehaviorLogic not mapped to any F### → critical
- PERM### in Permissions not mapped to any F### → critical
- Feature name vague → warning


<!-- ProcessFlow section moved to verification-checklist-flows.md (Phase-02 strip).
     Loaded only by the --flows pass (FL.3). Do NOT add ProcessFlow rules back here. -->

### ApiContracts

**Scope:** Applied ONLY by the `--api-contracts` pass reviewer (AC.3, via section targeting). Core W7a SKIPs this section (see `pipeline-w7-w9.md`). Wave naming: AC.1 synthesis / AC.2 validator / AC.3 review (historical numbering: W6.87 / W6.875 / W7a).

**Cross-refs:** data-model.md (MODEL### Backed-by refs), permissions.md (PERM### auth refs), route-list.md + api-map.md (endpoint identity)

**Required sections:** `## Conventions` (Shared Messages/Types + Global Error Contract) + at least one kind section (`kind: rest`, `kind: graphql`, or `kind: grpc`) per detected API kind in scout-report.md `## Detected API Kind`.

**Deterministic checks (AC.2 `validate_api_contracts.py` — pre-AC.3):** section presence, kind-tag validity, Source citation presence, duplicate key detection, shared-type-defined-once, completed marker, empty-surface handling. Rule IDs passing AC.2 are marked `[deterministic-pass]` — skip in semantic review.

**Semantic review rules (AC.3):**
- [ ] **AC-S1 Citation accuracy (spot-check):** for >=2 entries per kind section, Read the cited `file:line` and verify the code actually contains the endpoint/operation/RPC definition. Cited line is a comment or unrelated code -> critical.
- [ ] **AC-S2 No fabricated request/response fields:** cross-check response surface against actual transformer/SDL/proto source. A field listed in the response that does not appear in the source -> critical (fabricated surface).
- [ ] **AC-S3 Auth norm accurate:** REST routes without auth middleware must record `none` (not blank). GraphQL `@can` directives must map to correct PERM###. gRPC trusted-internal pattern must be stated explicitly ("trusted-internal — no per-call auth; scoping via payload field") — missing this note -> critical (hidden security boundary).
- [ ] **AC-S4 DRY — no re-listed entity columns:** entries must list response surface (transformer/resolver output), not raw entity columns from data-model.md. Entry that duplicates MODEL### field definitions instead of saying "Backed by MODEL###" -> warning (DRY signal; adjudicated by reviewer, not a HALT).

**Critical edge cases:**
- Entry missing `Source: file:line` citation -> critical
- Kind section missing `kind:` tag or invalid kind value -> critical
- Duplicate entry Key within a kind section -> critical
- Empty API surface (no entries) but file present without `_(no synchronous API surface detected)_` marker -> critical
- Empty surface with correct marker -> warning (not critical — library/CLI projects legitimately have no API)
- `.api-contracts.completed` marker absent after AC.1 -> warning
- Shared type from Conventions re-defined with field list inside an entry -> warning (DRY signal; reviewer adjudicates, not a HALT)
- `[INFERRED-from-stub]` confidence tag -> no issue (explicitly allowed; imported proto/SDL source may be absent)


### CrudMatrix (v11.1.0 — stack-specific; produced only when the profile runs extractors)

**Scope:** Applied ONLY when `docs/generated/crud-matrix.md` exists (Delphi/Oracle profiles). Core W7a
skips it for web profiles. Deterministic gate: `validate_crud_matrix.py` (citation per cell, table
cross-ref, op token C/R/U/D, Markdown column safety, dynamic-SQL-zero-CRUD WARN — RT-F8). Source of
truth: `_digest_extract_data_flow.json` (never the LLM's memory).

**Semantic review rules:**
- [ ] **CM-S1 Citation accuracy (spot-check):** for ≥2 CRUD cells, Read the cited `file:line` and verify the operation (INSERT/SELECT/UPDATE/DELETE) on that table actually exists there. Cited line unrelated → critical.
- [ ] **CM-S2 No fabricated ops:** every C/R/U/D cell must trace to a digest `db_op`. A cell with no digest backing → critical (fabricated).
- [ ] **CM-S3 [UNVERIFIED] preserved:** cells derived from `dynamic_sql_detected`/`confidence: low` units must carry `[UNVERIFIED]`. Dropping the marker → critical (false confidence on dynamic SQL).
- [ ] **CM-S4 Cross-Module accuracy:** the Cross-Module section lists tables touched by ≥2 features; built post-merge over the merged matrix (RT-DOC-b). A table here must actually appear in ≥2 feature rows → warning if not.

### DbObjects (v11.1.0 — stack-specific; produced only when the profile runs extractors)

**Scope:** Applied ONLY when `docs/generated/db-objects.md` exists. Deterministic gate:
`validate_db_catalog.py` (unique object names per kind, valid kind, citation present, identifier
Markdown-safe). Source of truth: `_digest_extract_sql_schema.json`.

**Semantic review rules:**
- [ ] **DB-S1 Citation accuracy (spot-check):** for ≥2 objects per kind, verify the cited DDL `file:line` defines that object. Unrelated → critical.
- [ ] **DB-S2 Purpose-from-evidence:** the `purpose` field must derive from the object's name/columns/comments in source, not be invented. Speculative purpose with no evidence → warning.
- [ ] **DB-S3 No credential leak (RT-F7):** no connection string / password / `IDENTIFIED BY` secret appears verbatim in any citation or purpose. A leaked secret → critical (scrub failed upstream — surface, do not promote).
- [ ] **DB-S4 db-objects ↔ data-model boundary:** db-objects is a raw DDL catalog; cross-references data-model MODEL### by table NAME only, never by shared ID. ID-mixing → warning.


## Composite Detection Rules

Rules fire unconditionally on every pipeline invocation. No opt-in flag.

- [ ] **H4 short-circuit respected (tabs only):** mutually-exclusive tab content (per-stack tab signals in `composite-screen-detection.md § H4`) → SCR variants (SCR###a/b), not REG. Hard rule; overrides all other heuristics for tab-style screens. Reviewer selects signals from the row matching the task's `Detected stack:` value.
- [ ] **H5 wizard/stepper classification:** screens with wizard/stepper signals (per-stack signals in `composite-screen-detection.md § H5`) MUST cite classification evidence in spec. Case A (SCR variants) requires explicit citation of distinct validation rules AND distinct API endpoints AND distinct user action per step. Case A without cited evidence → warning (researcher should re-evaluate as Case B). 2-step wizards defaulting to Case A → critical (must be Case B). ≥3-step wizards default to Case B (composite SCR + step REGs).
- [ ] **H3 region count excludes H4/H5 signals:** tab signals (H4) and wizard/stepper signals (H5) — per per-stack tables in `composite-screen-detection.md § H4` and `§ H5` — MUST NOT count toward H3 (any stack).
- [ ] **H2 module count uses per-stack include/exclude tables:** only domain/feature module imports count toward H2; UI-library and framework-primitive imports are excluded. Reviewer applies the include/exclude row matching the task's `Detected stack:` value — see per-stack tables in `composite-screen-detection.md § H2`.
- [ ] **2-of-3 signal gate applied:** composites cite which 2 signals passed (H1∧H2, H1∧H3, or H2∧H3). Screens not meeting gate → emit bare SCR###.
- [ ] **Raw-div fallback noted when H3=0:** if H3 yields 0, gate uses H1+H2 only. If both H1 and H2 also fail → emit atomic + warning. Known Detection Limitation documented in spec output.
- [ ] **FeatureList composite-ref tokenizer (C3):** FeatureList Related Screens tokenizer splits on `,` then on `/`. Left token = SCR### (must exist in ScreenList main index). Right token (if present) = REG### (must exist in that screen's Regions subsection). Both tokens validated independently. Missing REG### under valid SCR### → critical.
- [ ] **Malformed composite ref (M3):** malformed composite refs (`SCR001REG001` missing `/`, `SCR001/` missing REG, `SCR/REG001` missing digits, `SCR001/REG` missing digits) → critical. Regex: `^SCR\d{3}_\w+(/REG\d{3}_\w+)?$` must match.
- [ ] **W1 no-REG rule (M5):** W1 artifacts (SystemOverview, RouteList, DataModel) MUST NOT contain REG### codes. REG### first appears in W2 ScreenList. Orphan REG### in W1 artifact → critical.
- [ ] **Partial-screen ownership (CE3):** each SCR### must have ≥1 F### owning the screen shell (bare SCR### ref in FeatureList Related Screens); each REG### must have ≥1 F### owning it (SCR###/REG### ref). An F### with only SCR###/REG### refs does NOT own the parent SCR.
- [ ] **SIGNAL_INFERRED cap and justification:** `[SIGNAL_INFERRED]` tag in ScreenList Notes signals researcher used `composite-screen-detection.md § Signal Inference Fallback`. Tag MUST cite an H-rule in H2–H6 (H1 has no signal table — inference invalid for H1). Each occurrence MUST carry a 3-part justification (Intent matched / No-row reason / Observed pattern). Missing any part → critical. Count `[SIGNAL_INFERRED]` occurrences across the entire ScreenList document; threshold = `max(5, ceil(0.10 × SCR_count))` — exceeding triggers warning (over-reliance on inference; per-stack tables likely outdated or stack uncovered).


## Failure Trap Assertions

- **Trap 1 (proliferation):** every REG has ≥1 independence signal, drawn from: distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), distinct validation / action path. Missing signal → critical. Visual separation alone is NOT sufficient.
- **Trap 2 (tab/stepper misclassification):** mutually-exclusive tab content declared as REG (not SCR variants) → critical. Wizard/stepper content: Case A emitted without cited distinct-validation + distinct-endpoint evidence → warning (prompt researcher to re-evaluate as Case B). 2-step wizard emitted as Case A → critical.
- **Trap 3 (shared data):** collapse two REG candidates into one Feature ONLY when they share ALL of: read surface (same GET endpoint/store) AND write surface (same mutations) AND business workflow. Shared initial payload alone does NOT disqualify a split — if regions diverge on write endpoints, validation rules, action paths, or business workflow, they remain separate. Researcher self-check advisory (NOT reviewer-enforceable critical — reviewer cannot inspect codebase at review time).
- **Trap 4 (LOC-based over-split):** LOC is NOT a composite signal. H3 uses named wrapper components only. Advisory note: flag any ScreenList entry where the researcher's justification cites line count rather than named wrappers or import count.
- **Trap 5 (fabricated process-flow states):** a state listed in `## States` that is not a DB column/enum value AND not declared in `derived_views` frontmatter → critical. Dashboard labels computed at read-time (e.g., `TrackingHelper::getTrackingFinalizing`) are views, not states. Modeling them as states fabricates a machine that does not exist in code.
- **Trap 6 (spec orphan):** every REG### in ScreenList must have an owner annotation (can be `TBD`) → critical if owner annotation missing entirely.
- **Trap 7 (inferred-signal abuse):** `[SIGNAL_INFERRED]` tag without all 3 justification parts (Intent matched, No-row reason, Observed pattern) → critical. Tag citing H1 (which has no signal table) → critical; H2–H6 only. Tag used to bypass a per-stack row that DOES match the screen's stack/library naming → critical (researcher must use explicit row first). Tag count exceeding `max(5, ceil(0.10 × SCR_count))` across the entire ScreenList document → warning (suggests per-stack tables need updating or stack/library not covered).
