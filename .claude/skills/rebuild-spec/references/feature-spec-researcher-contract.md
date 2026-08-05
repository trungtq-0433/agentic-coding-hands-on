<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Researcher Contract (Wave 6 — rebuild-spec v4.0.0)

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other artifact read.
Do NOT re-derive information already present there.

## Mandatory Context Inputs (read ALL before drafting any file)

Read these upstream artifacts from `plans/<active>/artifacts/` before writing anything:
- `scout-report.md` — codebase map
- `screen-flow.md` — screen navigation graph
- `user-stories.md` — US### inventory
- `permissions-matrix.md` — PERM### roles (raw matrix; PERM### codes live here, not in the curated `permissions.md`)
- `business-rules.md` — system-level plain-language rules (W3 output). MUST NOT contradict these in `business-context.md`
- `flows/*.md` — cross-feature process-flows (FL.1 output; directory may be empty on first FS.1 run). Check if this F### participates in any flow via the flow file's frontmatter `source:` list. If yes → cross-reference in `business-context.md` (plain language, no codes).
- `feature-list.md` — F### inventory + canonical slugs

**PASS-2 LARGE SPEC:** If dispatcher provides a `PASS_1_DRAFT` path, read that file using Read tool with specific offset/limit per section. Append SM/ALG/INT sections to `technical-spec.md`. Do NOT inline its full content into memory.

## Output Files (4 mandatory)

Each F### produces 4 files under `plans/<active>/artifacts/features/{slug}/`:

1. `technical-spec.md` — Tech audience (Dev/QA/SA). All FR/BR/SM/ALG/INT codes, source citations, key entities.
2. `business-context.md` — Non-tech audience (PM/BA/Client). Plain language. See Forbidden Tokens below.
3. `screens.md` — `## Screen List` table + `## User Journey` per feature.
4. `edge-cases.md` — Test scenarios + error states extracted from technical spec.

### Confidence Companion (advisory sidecar)

`confidence-report_technical-spec.md` is NOT one of the 4 mandatory files above. It is emitted
automatically by `scripts/derive_confidence_report.py` (a deterministic script, not authored
by the researcher) after `technical-spec.md` is promoted — a citation-coverage sidecar, never
gated, never asserted. See `references/confidence-report-contract.md` for the full derivation
rules and the A1 correctness-verification boundary.

### Sidecar Files (guard against future confusion)

`docs/features/{slug}/test-cases.md` (v26.1.0 B6, opt-in `--test-cases` pass) is a 5th file that
lives in the SAME per-feature directory as the 4 mandatory files above, but it is **SIDECAR** —
same principle as the A1 confidence-report companion, different reason (test-cases.md is a real
researcher-authored deliverable that simply arrives on a separate, later, optional pass, not a
machine-derived stat). It is NEVER added to the `FEATURE_FILES` 4-tuple (`scripts/_slug_lib.py`),
never checked by `check_promotion_gate.py`, and never part of `scaffold_spec.py`'s 4-file
scaffold. Do NOT treat its absence as `MISSING` in any feature-spec review. See
`references/test-cases-researcher-contract.md` for the pass that produces it.

## Section Ownership Matrix

| Source section | File owner | Notes |
|---|---|---|
| Overview | `technical-spec.md` | Tech narrative |
| Why This Exists | `business-context.md` | Plain language; no codes |
| Who Uses It | `business-context.md` | Plain personas |
| Business Workflow | `business-context.md` | Plain numbered steps; NO table.column refs |
| Screen Flow | `screens.md` | `## Screen List` table + `## User Journey` |
| Polymorphic Behavior | `technical-spec.md` | DISC-### tables |
| Cross-Cutting Logic (FR/BR/SM/ALG/INT) | `technical-spec.md` | Source citations live here only |
| User Stories (G/W/T + endpoints) | `technical-spec.md` | US### codes, FR refs |
| Edge Cases (from User Stories) | `edge-cases.md` | Lifted to own file; min 3 UI / 1 background |
| Key Entities | `technical-spec.md` | Table refs |
| Artifact References | `technical-spec.md` | Code lists, updated paths to new layered structure |
| Assumptions | `technical-spec.md` | Tech assumptions |
| Source Code References | `technical-spec.md` | Path:line; NEVER copy to other 3 files |
| Unresolved Questions | `technical-spec.md` (tech) + `business-context.md` (business-side) | Split if both classes present |
| Source Walkthrough (A3, v26.0.0) | `technical-spec.md` | Reading order + call hierarchy; recasts the Source Code References table (adds Order column) — do NOT author a second file-list table |
| DB Impact per Event (B4, v26.0.0) | `technical-spec.md` | One row per DB-writing event/endpoint; NEVER copied to `screens.md` (screen-spec stays UI-scoped) |

## Forbidden Tokens (business-context.md only)

See HTML-commented block at top of `templates/business-context-template.md`.
Self-check regex against drafted prose BEFORE writing. Any match = CRITICAL; rewrite in plain language.
Cross-references to `flows/` ARE ALLOWED: "This feature is part of [Name] — see `flows/{slug}.md`".

## Source Citations

`**Source:** path:line-start-end` MUST appear ONLY in `technical-spec.md`.
Citation validator (FS.2) only scans `technical-spec.md`; source citations in the other 3 files = CRITICAL contract violation.

## Mandatory Source-Code Reading

- MUST read actual source code files (controllers, models, jobs, services, Vue/React pages) for every feature — NOT just summarize from upstream artifacts.
- Use Grep/Read tools to find real controllers, models, jobs, routes for this F###.
- Extract specifically: file paths with line ranges, method names, table/column names, HTTP status codes for error cases, job class names, event names.
- If a file cannot be read, note it under `## Unresolved Questions` in `technical-spec.md`.

## Discriminator Coverage (CRITICAL)

After identifying Key Entities, MUST check `data-model.md` for discriminator fields:

1. For each entity in `## Key Entities`, read its `**Discriminator Fields**` block in `data-model.md`.
2. If ANY entity has DISC-### entries → MUST write `## Polymorphic Behavior` in `technical-spec.md` with one subsection per DISC-###.
3. Cover ALL values listed in `data-model.md`. Missing a known value = CRITICAL reviewer rejection.
4. Include ≥1 edge case per variant in the `### Edge Cases` table; lift these rows to `edge-cases.md` as well.
5. Each behavior cell MUST be grounded in source code. Write `unverified` if not confirmable — do NOT leave blank or fabricate.

**N/A fallback** — only valid when Key Entities have zero DISC-### in `data-model.md`:
`N/A — no discriminator fields in Key Entities.`

**Section is ALWAYS present in `technical-spec.md`.** Omitting `## Polymorphic Behavior` = CRITICAL.

#### SM `kind` Classification

For every extracted SM-###, set `**kind:**` as the first metadata line after the heading:
- **`entity`** — state field is persisted (DB column, ORM attribute, model field, type in `data-model.md`).
- **`ui`** — state is component-local (useState, ref, computed, signal — NOT persisted beyond render cycle).
- If same concept has both, document as 2 separate SM-### blocks.
- **Threshold:** only classify `kind: ui` for state machines with ≥3 states OR ≥2 transitions.

## Decision Logic Extraction (DEC-###)

DEC-### captures decisions with **user-visible business outcome** — regardless of source file location.

### Scope

Scope is **outcome-based, source-location-agnostic**. Ask: "Does this decision change what the user sees, does, or where they go?" If yes → DEC candidate. If no → skip.

### Subtype Signatures

**render:** JSX/template trees with conditional rendering involving ≥2 predicates OR non-single-field predicates. SKIP single-field conditions (→ DISC). SKIP cosmetic toggles.

**interaction:** Event handlers where body reveals/hides substantive UI or focuses meaningful sections. SKIP form-field two-way binding. SKIP loading spinners.

**flow:** Functions advancing user position: `setStep`, `next()`, `router.push(...)`, conditional wizard page rendering. SKIP cross-feature navigation (→ `screen-flow.md`).

### Anti-examples (skip — plumbing)

`if isLoading → show spinner` | `if api.success → dispatch` | `if !error → show data` | `if token expired → refresh` | `if response.status === 200` | `debounce(handler, 300)` | `if cache hit → return cached`

### DISC vs DEC Boundary

- Single-field enum (≥2 named values, distinct outcomes) → **DISC**
- Boolean flag → Business Rule or FR note, NOT DISC
- ≥2 predicates OR interaction-driven OR flow-step routing → **DEC**

### Required Output Fields per DEC

Each DEC-### block MUST include: `**subtype:**`, `**Triggers in:**` (SCR### + event), `**Involved entities:**`, `**user_visible_outcome:**` (1 sentence), `**Source:**` (file:start-end), pseudocode block ≤8 lines.

### N/A Fallback Rule

`N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.` is ONLY valid if zero non-plumbing user-facing branches AND no multi-predicate/interaction/flow decisions. MUST scan all implicated source files first.

## Discriminator Coverage (CRITICAL)

After identifying Key Entities, you MUST check data-model.md for discriminator fields:

1. For each entity in `## Key Entities`, read its `**Discriminator Fields**` block in data-model.md.
2. If ANY entity has DISC-### entries → you MUST write `## Polymorphic Behavior` with one subsection per DISC-###.
3. Cover ALL values listed in data-model.md. Missing a known value = CRITICAL reviewer rejection.
4. Include ≥1 edge case per variant in the `### Edge Cases` table (e.g., what happens when a record arrives with an unexpected/deprecated value).
5. Each behavior cell must be grounded in source code. Write `unverified` if you cannot confirm from code — do NOT leave blank or fabricate.

**N/A fallback** — only valid when Key Entities have zero DISC-### in data-model.md:
`N/A — no discriminator fields in Key Entities.`

**Section is ALWAYS present.** Omitting `## Polymorphic Behavior` entirely = CRITICAL.

#### SM `kind` Classification

For every extracted SM-###, set `**kind:**` as the first metadata line after the heading:
- **`entity`** — state field is persisted (DB column, ORM attribute, model field, type defined in data-model.md). Look for: database enum columns, ActiveRecord state machine, ORM status fields, type aliases in data-model.md.
- **`ui`** — state is component-local (useState, ref, computed, signal, local var — NOT persisted beyond the render cycle). Look for: form submission status, modal open/close, panel collapsed, loading/error/success cycles.
- If the same concept has both (entity status + UI loading mirror), document as 2 separate SM-### blocks.
- **Threshold:** only classify `kind: ui` for state machines with ≥3 states OR ≥2 transitions. Smaller cases stay implicit in BR-### rules.

### Client-Side Logic Extraction (→ behavior-logic.md § Client-Side Logic)

Scan for these 5 patterns in client/frontend source files. For each found, add an entry to the `## Client-Side Logic` section of `behavior-logic.md`:

**Debounce / Throttle**
Signature: `setTimeout`/`clearTimeout` wrapping a handler, `debounce(fn, ms)`, `throttle(fn, ms)`, `useDebounce`, `useDebouncedCallback`
Capture: trigger location (file:line), delay value, what action is debounced.

**Optimistic UI**
Signature: state mutation applied before `await`, with a catch/rollback block; `useOptimistic`, `optimisticUpdate`
Capture: trigger (user action), optimistic state change, rollback target, API endpoint.

**Polling**
Signature: `setInterval` calling an API, recursive `setTimeout` + API call, `refetchInterval`, `usePolling`
Capture: interval duration, condition to stop polling, API called.

**Upload Progress**
Signature: `XHR.upload.onprogress`, `axios onUploadProgress`, `fetch` with streaming body, `useUpload`, `onProgress`
Capture: trigger action, progress state field name, error path.

**Realtime**
Signature: `new WebSocket(...)`, `new EventSource(...)`, `useWebSocket`, ActionCable subscribe, Pusher subscribe, SSE listener
Capture: channel/URL pattern, trigger (mount/user action), reconnect strategy, teardown (unmount handler).

If a pattern is absent in the entire codebase, write `N/A — no {pattern} patterns detected.` in the corresponding subsection.

### Client-Side Gate Extraction (→ permissions.md)

Scan for runtime gates that affect UI rendering. Use these function-name signatures — do NOT hard-code library names:

**feature-flag:** `useFlag|useFeature|isEnabled|featureFlag\(|checkFlag` — capture first string argument (flag name), file:line, effect (what branch differs).

**experiment:** `useExperiment|getVariant|abTest\(|experiment\.variant|useAbTest` — capture experiment name, variant identifiers found in code.

**env-gate:** comparison against `process\.env\.|import\.meta\.env\.|ENV\[|os\.environ\[` followed by `===`/`==`/`in (...)` — capture env var name, compared value, effect.

**locale-gate:** comparison against `i18n\.locale|currentLocale|getLocale\(\)|locale\s*===|lang\s*===` — capture locale value, effect.

Name-only rule: capture the flag/experiment name found in source. Do NOT look up the flag's configuration in LaunchDarkly, Statsig, or any external service.
If none found: write `N/A — no {type} gates detected.` for each absent type.

### Screen-Flow Client-Side Extraction (→ screen-flow.md)

**Guard Logic**
Signature: function/method definitions tied to route entry: `beforeEnter|canActivate|middleware|loader|before_action|authenticate|authorize` — check if registered in router config or route annotation.
For each guard: record GUARD-### id, trigger hook name, source file:line, pseudocode logic (if/redirect chains), failure path.
N/A rule: only write `N/A — no route guards detected.` after confirming no route-level interception exists (check router config files, not just component code).

**Deep-Link State Restoration**
Signature: URL param reads at component mount → state sync: `useSearchParams|useQuery|router\.query|URLSearchParams|params\[|$route\.query`
For each screen: record URL pattern, table of param → UI state, default-if-missing, failure mode.
N/A rule: write `N/A — no URL-driven state restoration detected.` only if no URL params are read into component state.

**Unsaved-Changes Protection**
Signature: `beforeunload|onbeforeunload|usePrompt|useBeforeUnload|leaveGuard|isDirty|formState\.isDirty|data-turbo-confirm`
For each form/screen: record trigger, source, dirty detection method, exact prompt text.
N/A rule: write `N/A — no unsaved-changes guards detected.` only after checking all forms with user input.

### Client Behavior Anchor (→ technical-spec.md § Cross-Cutting Logic)

Every feature spec MUST include the client behavior anchor block in `## Cross-Cutting Logic`, even if all 3 linked artifacts have mostly N/A content. The anchor links are relative from `docs/features/{slug}/technical-spec.md`:

```markdown
---

**Client behavior:** see
[`behavior-logic.md`](../../generated/behavior-logic.md) (client-side patterns — debounce, optimistic UI, polling, upload, realtime),
[`permissions.md`](../../system/permissions.md) (feature flags / experiments / env / locale gates),
[`screen-flow.md`](../../generated/screen-flow.md) (guards / deep-link state restoration / unsaved-changes protection).
```

This anchor is always present. The linked files may have N/A sections — that is fine and correct.

## Decision Logic Extraction (DEC-###)

DEC-### captures decisions with **user-visible business outcome** — regardless of which file the code lives in. Component files, saga files, controller files, route guards — all valid Sources if the decision changes what the user sees, does, or where they go.

### Scope statement

Scope is **outcome-based**, **source-location-agnostic**. The question is: "Does this decision change what the user sees, interacts with, or where they navigate?" If yes → DEC candidate. If no → skip.

### Subtype signatures (extraction patterns)

**render — multi-predicate render branches:**
- JSX/template trees with conditional rendering involving ≥2 predicates OR non-single-field predicates
- Signature: `{(condA && condB) ? <A/> : <B/>}`, `v-if="condA && condB"`, computed render props using ≥2 entity fields, switch statement rendering different components
- SKIP single-field conditions — those go to DISC (enum or boolean)
- SKIP cosmetic toggles (class names, padding, color only)

**interaction — event handlers with visible business meaning:**
- Event handlers (`onClick`, `onChange`, `onSelect`, `onKeyDown`) where body reveals/hides substantive UI, focuses a new input, or shows/hides meaningful sections
- SKIP form-field two-way binding (input value mirrors state only)
- SKIP loading spinner reveals (`isLoading ? <Spinner/> : ...`)
- SKIP error toast displays (those are error-handling, separate section)

**flow — multi-step / navigation / step routing:**
- Functions/handlers advancing user position in a flow: `setStep(...)`, `next()`, `history.push(...)`, `router.push(...)`, `redirect(...)`, conditional rendering of next/previous wizard page
- In-feature scope: stays within feature (multi-step wizard advance, sub-screen routing, post-action navigation)
- SKIP cross-feature navigation — that is screen-flow.md territory
- SKIP error redirects to global error pages — that is error-handling territory

### Anti-examples (skip these — they are plumbing)

```pseudo
❌ if isLoading → show spinner          (loading toggle — not decision)
❌ if api.success → dispatch SUCCESS    (dispatch wrapper — not decision)
❌ if !error → show data                (presence check — not branching)
❌ if token expired → refresh token     (fetch mechanic — not user-facing)
❌ if response.status === 200 → ...     (HTTP plumbing)
❌ if user.locale === 'en' → load 'en'  (i18n routing — not business)
❌ debounce(handler, 300)               (timing wrapper)
❌ if cache hit → return cached         (cache mechanic)
```

If uncertain, ask: **"Does this affect what the user SEES, DOES, or WHERE they go?"** If no → skip.

### DISC vs DEC boundary

- Single-field condition with **enum type** (≥2 named values with distinct behavioral outcomes) → **DISC**
- Boolean flag (`is_published: boolean`, `is_active: boolean`) → **Business Rule** or FR note, NOT DISC
- ≥2 predicates OR interaction-driven OR flow-step routing → **DEC**

Examples:
- `if question.type === 'multiple choice' → render MultipleChoice` → DISC (single enum field)
- `if survey.published === true → show banner` → Business Rule (single boolean, no DISC code needed)
- `order.status` enum with values `pending / shipped / cancelled` each affecting UI → DISC (enum ≥2 values)
- `user.is_admin === true → show admin panel` → DEC-interaction or Business Rule depending on complexity; NOT DISC
- `if user.role === 'admin' AND survey.published_at !== null → show MetricsPanel` → DEC (multi-predicate render)
- `on option select: if option.is_other_option → reveal CommentInput` → DEC (interaction reveal)
- `on submit success: if survey.type === 'mbti' → push('/result')` → this is single-field but it's a navigation flow decision — DEC-flow (navigation post-action with meaningful routing)

`N/A — no discriminator fields in Key Entities.` is valid when Key Entities have zero DISC-### entries in data-model.md. Boolean fields are NOT DISC-### — their absence from Polymorphic Behavior is correct.

### Multi-subtype guidance

If a decision spans ≥2 dimensions (e.g. a Submit button that both validates form AND advances wizard), declare `subtype: render, flow`. The pseudocode block captures both dimensions together.

### Required output fields per DEC

Each DEC-### block MUST include:
- `**subtype:**` — list (≥1, comma-separated: `render`, `interaction`, `flow`)
- `**Triggers in:**` — screen code (SCR###) + triggering event or lifecycle hook
- `**Involved entities:**` — `Entity.field` names that drive the branching
- `**user_visible_outcome:**` — 1-sentence justification (what changes for the user)
- `**Source:**` — `file/path.js:start-end` (read actual line range; source location NOT validated — saga ok)
- Pseudocode block ≤8 lines (`pseudo` or `js`/`ts`/`py` hint)

### N/A fallback rule

`N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.` is ONLY valid if the feature has **zero** non-plumbing user-facing branches AND no multi-predicate / interaction / flow decisions. Researcher MUST scan all source files implicated by the feature before writing N/A. If component files contain JSX ternaries with ≥2 predicates, N/A is invalid.

## Scope & Codes

- All FR/BR/SM/ALG/INT/SC codes are LOCAL to this feature. Cross-spec refs (e.g., "see BR-001 in F002") = INVALID.
- Every BR/SM/ALG/INT block MUST cite `**Source:** path/to/file.ext:start-end`. NEVER fabricate paths or line ranges. Confirm each by reading the range.
- BR/SM/ALG/INT heading MUST use `### {PREFIX}-###_NameSlug` (e.g., `### BR-001_OrderMinItems`).
- Pseudocode ≤20 lines per block. Use a concrete language hint (ts/py/php/go) or `text`. NEVER leave `{lang}` literally.
- Pseudocode MUST NOT embed secrets or credentials.

## Placement Rules

- FR-### MUST appear under EXACTLY ONE of: (a) a US's `**Requirements fulfilled:**` list, OR (b) `## Cross-Cutting Logic > ### Requirements` (for FRs spanning ≥2 USs equally). Appearing in both or neither = CRITICAL.
- BR/SM/ALG/INT defined under a US apply PRIMARILY to that US. Another US MAY reference by code only: `BR-001 (see US001)`. No duplicate Source block. Applies to ≥2 USs equally → move to `## Cross-Cutting Logic`.
- SC-### appears inline under the US it validates (`**Verification:**`), OR under `## Cross-Cutting Logic > ### Verification` for global SCs. No standalone `## Success Criteria` heading.

## Depth Requirements (CRITICAL — incomplete sections = reviewer rejection)

- `## Business Workflow` in `business-context.md`: MUST use numbered steps (≥3 for non-trivial features). Each step references specific entities found in source code. Generic prose without specifics = REJECTED.
- `## Cross-Cutting Logic > ### Business Rules` in `technical-spec.md`: extract ALL guards, validations, constraints. Each BR needs exact behavior + HTTP status code + verified `**Source:**`. Aim ≥3 BRs per UI feature; ≥1 per background feature.
- `## User Stories` in `technical-spec.md`: each US MUST have `**What happens:**`, `**Why this priority:**`, `**Independent Test:**`, Given/When/Then acceptance scenarios, `**Endpoints**: METHOD /path`.
- `edge-cases.md`: MUST contain ≥3 rows for UI features; ≥1 for background features.
- `## Key Entities` in `technical-spec.md`: table MUST list ALL database tables this feature reads/writes; ≥3 entities for non-trivial features.
- `## Source Code References` in `technical-spec.md`: MUST list primary controller(s), model(s), job(s), service(s), page/component file(s) with paths and line ranges. ≥3 entries required.
- `## Assumptions` in `technical-spec.md`: ≥2 entries for any non-trivial feature.
- `## Unresolved Questions`: list anything not verifiable from source. ≥1 entry expected for complex features.
- `## Source Walkthrough` (A3, v26.0.0) in `technical-spec.md`: ordered reading list (data model → entry point → view → business logic), 1 file per step, each cited `**File:** path:line-range` (NOT `**Source:**` — see below) + a 1-sentence "why start here"; a call-hierarchy diagram (ASCII or Mermaid); a pointer to the recast `## Source Code References` table. MANDATORY — no N/A fallback (every feature has source to walk through).
- `## DB Impact per Event` (B4, v26.0.0) in `technical-spec.md`: one row per user action/endpoint/job that WRITES to the database (`Event/Endpoint | Table | Columns | Operation | Value Derivation | Source`). Read-only queries are out of scope. `N/A — read-only feature, no DB writes.` is the ONLY valid fallback, and only after confirming zero writes.

## Per-File Rules

### technical-spec.md

- All H2 sections from Section Ownership Matrix that map here MUST be present.
- Source citations (`**Source:** path:line-start-end`) live here and ONLY here.
- SM Mermaid state diagrams, DEC blocks, DISC tables all belong here.
- `## Client Behavior Anchor` MUST appear in `## Cross-Cutting Logic` even if all linked artifacts are mostly N/A.
- `## Artifact References` is a single merged 4-column table: `Artifact | File | Codes Used | Reviewed`. Always include System Overview and Feature List. LEGACY two-section format (`## Related Artifacts` + `## Spec Documents`) = CRITICAL.
- Artifact References now point to layered paths: `docs/features/{slug}/technical-spec.md`, `docs/system/overview.md`, `docs/generated/route-list.md`.
- **v25.0.0:** the `API Map` row's Codes Used column carries `{ROUTE###}` — despite the row label, these codes are NOT checked against `api-map.md` (which has no code scheme); they are the bridge to `route-list.md`'s `Code` column, the inverse of that table's `Owner F###` cell. Every cited `ROUTE###` MUST resolve to a `route-list.md` row, and the citing F### must appear in that route's `Owner F###` set (`validate_feature_api_link.py` enforces both directions + twin-consistency). `api-map.md`/`api-contracts.md` remain separate, unbound views.
- **v26.0.0 — `## Source Walkthrough` (A3):** cite each reading-list entry with `**File:**`, NEVER `**Source:**` — `derive_confidence_report.py`'s `CITATION_RE` only matches the literal `**Source:**` token, so using a different label keeps this navigational list out of the A1 citation-coverage stat (see `references/confidence-report-contract.md` § A3 navigational entries). Gated by `scripts/validate_reading_guide_db_impact.py`, a DEDICATED validator with a `*.pre_migration` WARN-first degradation contract — this heading is NEVER added to `_spec_constants.REQUIRED_H2_TECH` (Decision 2).
- **v26.0.0 — `## DB Impact per Event` (B4):** every Operation cell's Source is either a `file:line` citation (backtick-wrapped) or an explicit `[INFERRED]` tag — never leave it blank (`validate_reading_guide_db_impact.py` WARNs `db_impact.uncited` on a blank Source cell). Same dedicated validator + degradation contract as A3. Top-level H2 (not nested under `## Cross-Cutting Logic` — keeps `REQUIRED_CCL_H3` untouched).

### business-context.md

- MUST include all H2 sections per template: Why It Matters, Who Uses It, What They Do.
- Run forbidden-tokens self-check before writing.
- If feature participates in a flow → add plain-language cross-reference: "This feature is part of [Name] — see `flows/{slug}.md`".
- Unresolved Questions (business-side) if applicable.
- MUST NOT contain FR/BR/SM/ALG/INT codes or source citations.

### screens.md

- `## Screen List` table (4-column: `Screen Name | SCR### | What User Sees | What User Can Do`, per `templates/screens-template.md`) MANDATORY for UI/mixed features. **v24.0.0:** the `SCR###` column carries the canonical `SCR###_NameSlug` from `screen-list.md` — it is the bridge to `docs/screens/SCR###_Name/spec.md` and the inverse of that spec's `**Feature**` backlink. Every code MUST resolve to a `screen-list.md` row (`validate_feature_screen_link.py` enforces this). Heading MUST be `## Screen List` (NOT "Screen Route Table") — `validate_feature_spec.py` REQUIRED_H2_SCR enforces `## Screen List` → `## User Journey`. Routes live in `route-list.md`, not this table.
- Write `N/A — background feature; no user-facing screens.` for background-only features.
- User Journey numbered steps MUST reference screen names, NOT routes or endpoints.
- List owned screens with route path and atomic/composite annotation.

### edge-cases.md

- Single table: `Scenario | What Happens | User-Facing Message`.
- ≥3 rows for UI features; ≥1 for background-only features.
- "User-Facing Message" MUST be plain language. Raw HTTP status codes in this column = REJECTED.
- Include edge cases lifted from DISC-### variants and DEC-### branches.

## Folder Lifecycle (4-file atomicity)

Wave 5 creates `{slug}/.pending`. On successful researcher run:

1. Write all 4 files.
2. Verify all 4 are non-empty:
   `[ -s technical-spec.md ] && [ -s business-context.md ] && [ -s screens.md ] && [ -s edge-cases.md ]`
3. If all pass → `rm .pending`. If ANY fail → leave `.pending` intact. FS.5 will mark MISSING.
4. Partial writes (e.g., only 3 files written) MUST leave `.pending` — do NOT remove on partial success.

## Task Closure

On successful 4-file write + `rm .pending`: call `TaskUpdate(status=completed)` on this task id BEFORE returning.

## See Also

- `process-flow-researcher-contract.md` (Wave 6.8 process-flow synthesis)
- `references/canonical-fcode-schema.md` § Folder Lifecycle
- `references/verification-checklist-universal.md` § Pending Marker Rule
