# Code Formats & Valid Requirements

Shared schema for rebuild-spec artifacts. Loaded by researcher and reviewer subagents.

## Code Formats

| Type | Format | Example | Scope |
|------|--------|---------|-------|
| Feature | `F###_NameSlug` | F001_Auth | project |
| User Story | `US###_NameSlug` | US001_Login | project |
| Screen | `SCR###_NameSlug` | SCR001_LoginScreen | project |
| Region | `REG###_NameSlug` | REG001_Header | per-screen |
| Background Logic | `BL###_NameSlug` | BL001_ScheduledReport | project |
| Permission | `PERM###_NameSlug` | PERM001_ViewReports | project |
| Discriminator | `DISC-###` | DISC-001 | project |
| Decision Logic | `DEC-###_NameSlug` | DEC-001_PostSubmitRouting | per-spec |
| Business Rule | `BR-###_NameSlug` | BR-001_OrderMinItems | per-spec |
| State Machine | `SM-###_NameSlug` | SM-001_OrderLifecycle | per-spec |
| Algorithm | `ALG-###_NameSlug` | ALG-001_DiscountCalc | per-spec |
| Integration | `INT-###_NameSlug` | INT-001_StripeCharge | per-spec |
| Data Model Entity | `MODEL###_EntityName` | MODEL001_User | project |
| Process Flow | `FLOW###_NameSlug` | FLOW001_EvaluationCycle | project |

**Scope legend:** `per-screen` — ID namespaced under parent SCR###; same REG### may reappear under different SCR### without collision.

**Contiguity invariant:** project-scoped global schemes (F/US/SCR/BL/PERM/MODEL/FLOW) are contiguous 001..N in final artifacts (enforced by renumber gate + `validate_id_contiguity.py`). Per-screen REG### contiguous within each SCR###. Per-spec BR/SM/ALG/INT/DEC/FR not globally renumbered.

**Composite cross-ref parsing:** references of the form `SCR###/REG###` or `SCR###, SCR###/REG###` (comma-separated mixed refs) MUST split on `,` first (to separate multiple refs), then split each token on `/`. Left token = SCR### (must exist in ScreenList main index); right token (if present) = REG### (per-screen scope, must exist in that screen's Regions subsection). Validate left and right tokens independently. Grep-style validators looking for bare `SCR\d{3}` patterns MUST also match `SCR\d{3}(/REG\d{3}_\w+)?` when processing feature-list, user-stories, permissions artifacts.

### Discriminator Fields (DISC-###)

DISC-### codes identify enum/discriminator fields in the data model. Assigned by the W1 DataModel researcher; referenced by FS.1 feature spec researchers and W7a / FS.5 reviewers.

**Format:** `DISC-###` (3-digit zero-padded). Unique within a single `data-model.md` document. Not per-spec — project-scoped.

**Qualifies as a discriminator (enum OR boolean single-field):**
- Enum column in DB schema (`ENUM(...)`, `CHECK (col IN (...))`, TypeScript `enum`, Python `Enum`, etc.)
- String/integer field with a fixed value set enforced at application level (model constants, `const STATUS = [...]`, etc.)
- Boolean field that drives single-field conditional rendering or behavior (`survey.published`, `question.required`) — 2-row table (true/false)
- Field that drives `switch`/`case` or `if/elsif` branching on its value in controllers or services — where different values produce meaningfully different behavior (render path, validation, persistence, side effects)

**Does NOT qualify:**
- String/integer fields with unbounded/arbitrary values (free-text names, amounts, URLs)
- Fields used only for display labels with no behavioral branching
- Multi-field conditions (those are DEC-###, not DISC-###)

**Assignment:** DataModel researcher assigns DISC-### IDs sequentially in order of discovery across all entities (DISC-001, DISC-002, ...). IDs do not reset per entity.

**Scope legend:** `project` — DISC-### IDs are globally unique within a data-model.md document; not per-entity namespaced.

### Per-Spec Scope (BR / SM / ALG / INT / DEC)

`BR-###`, `SM-###`, `ALG-###`, `INT-###`, `DEC-###` IDs are LOCAL to a single feature spec. A `BR-001` in `F001_Auth/spec.md` is unrelated to `BR-001` in `F002_Profile/spec.md`. Similarly, `DEC-001` in `F001_Auth/spec.md` is unrelated to `DEC-001` in `F014_SurveyTaking/spec.md`. Cross-spec references (e.g., "see DEC-001 in F002") are INVALID and will be flagged critical by the reviewer. Placement note: DEC-### codes appear under `## Cross-Cutting Logic > ### Decision Logic`. BR/SM/ALG/INT/SC codes appear inline under their owning US in `## User Stories`, or under `## Cross-Cutting Logic` for concerns spanning ≥2 USs. Dedicated top-level sections for these prefixes are NOT used (reviewer flags critical if present). FR placement rule (authoritative): see `references/feature-spec-researcher-contract.md § Placement Rules` — summary: FR-### MUST appear under EXACTLY ONE of US Requirements OR Cross-Cutting Logic; appearing in both = CRITICAL. <!-- canonical-source: feature-spec-researcher-contract.md § Placement Rules -->

#### DEC-### Required Fields

Every DEC-### block MUST include:
- `**subtype:**` — list of `render`, `interaction`, `flow` (≥1, comma-separated if multiple)
- `**Triggers in:**` — screen code + triggering event/lifecycle
- `**Involved entities:**` — entity.field names driving the decision
- `**user_visible_outcome:**` — 1-sentence justification of business relevance (why this is a DEC, not plumbing)
- `**Source:**` — `file:line-range` (source-location-agnostic — saga/component/controller all valid)
- Pseudocode block ≤8 lines in pseudo or js/ts/py hint

## Background Logic Types

Canonical 10 types — language-neutral. Single source of truth for template, checklist, and agent prompts.

| Type | Description |
|------|-------------|
| custom-command | CLI commands |
| event-listener | Event-driven handlers |
| integration | Third-party integrations (external API clients) |
| mail | Email sending logic |
| middleware | Request/response processing chain (non-auth) |
| notification | In-app / push notification logic |
| observer | Model lifecycle hooks (created/updated/deleted) |
| queue-worker | Background job workers (async queue consumers) |
| scheduled-job | Cron-like scheduled tasks |
| webhook | Incoming/outgoing webhook handlers |

Auth/permission middleware → Permissions artifact only.

## Background Logic Item Fields

Required fields on every BL item (v2.9.0+). Enforced by Wave 7a reviewer (missing = critical).

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| `**Source File**` | Relative path from repo root | `app/Jobs/SendInvoice.php` | Must match scout BL inventory entry path |
| `**Source Symbol**` | Class, `Class::method`, or `module::function` | `SendInvoice` / `MailService::sendWelcome` | Mode A: class name; Mode B: class + method |

## Permission Types

| Type | Description |
|------|-------------|
| route-guard | Route-level authorization middleware |
| screen-permission | UI element visibility/enabled rules |
| action-permission | Button/action execution rules |
| data-permission | Field-level access control |
| role-based | Role-based access control rules |
| resource-ownership | Owner/resource relationship checks |
| field-permission | Column/field visibility rules |
| api-scope | OAuth/API scope permission |
| feature-flag | Runtime-evaluated flag from a feature flag service or config (requires `source:` field) |
| experiment | A/B test variant assignment gate (requires `source:` field) |
| env-gate | Hardcoded check against an environment variable; fixed at deploy time (requires `source:` field) |
| locale-gate | UI branch conditioned on the active locale or language setting (requires `source:` field) |

## Authorization System Types

| Type | Description | Indicators |
|------|-------------|------------|
| rbac | Role-Based Access Control | Roles (admin, user, manager), role assignments |
| abac | Attribute-Based Access Control | Policies, attributes (department, owner, status) |
| acl | Access Control List | Explicit user permissions, permission matrices |
| ownership | Resource Ownership | owner_id, created_by, can_edit rules |
| hybrid | Mixed (RBAC + Ownership) | Roles combined with ownership checks |
| other | Custom/Other | Custom permission logic |

## Valid Feature Requirements

A valid Feature MUST satisfy ALL 4 criteria:

| Criteria | Check | Invalid Example | Valid Example |
|----------|-------|----------------|--------------|
| Single Intent | One capability, no "and/or" | "Authentication and Authorization" | "Authentication" |
| Clear Flow | Input → Process → Output defined | "User management" | "User Login: credentials → validate → session" |
| Independently Testable | Can test in isolation | "All CRUD operations" | "Create User", "Delete User" |
| Agent Implementable | Single task chain | "Manage entire system" | "View User Profile" |

Invalid: "Admin Management" (too broad), "CRUD Operations" (not user-facing), "Settings & Configuration & Notifications" (multiple intents).

Valid: `F001_Auth` (login/logout/session), `F002_UserProfile` (view and edit), `F003_ProductSearch` (search with filters).

## Valid User Story Requirements

A valid User Story MUST satisfy ALL 4 criteria:

| Criteria | Check | Invalid Example | Valid Example |
|----------|-------|----------------|--------------|
| Single Action | One user action | "Login and view dashboard" | "Login" |
| Independent | No dependency on other US | "Reset password after login" | "Request Password Reset" |
| Testable | Clear pass/fail outcome | "User is happy" | "User receives email" |
| Observable Result | UI/API/data/state change | "System works" | "User sees confirmation message" |

**US Types**: `ui` US require at least one `SCR###` or `SCR###/REG###` mapping. `system` US require at least one BL### mapping.

## Valid Screen Requirements

| Criteria | Check |
|----------|-------|
| Has Route | Screen must have a route in RouteList |
| Has US Mapping | Screen must have at least one US### mapped |

F### mapping is NOT in Screen/ScreenList. FeatureList is the ONLY document that maps features to other artifacts.

## Valid Code Logic Block Requirements (BR / SM / ALG / INT)

A valid BR / SM / ALG / INT block (inside a feature spec) MUST satisfy ALL 4 criteria:

| Criteria | Check | Invalid | Valid |
|----------|-------|---------|-------|
| Has Source | `**Source:** {path}:{start}-{end}` present | missing or just file with no line range | `**Source:** src/auth/login.controller.ts:42-61` |
| Has Description | Non-placeholder narrative explaining intent | `**Rule:** {RULE_NAME}` left unfilled | narrative sentence explaining when/why the rule fires |
| Has Body | Pseudocode ≤20 lines OR Mermaid `stateDiagram-v2` (SM only) | empty code fence or >20 lines of raw source | compact pseudocode capturing intent |
| Has Linked FR | `**Linked FR:** FR-###` with ≥1 FR defined in same spec | links to FR in another spec | `**Linked FR:** FR-002` present in same spec |

**Additional rules:**
- BR / SM / ALG / INT IDs unique within the spec.
- SM MUST include a Mermaid `stateDiagram-v2` block (prose alone is not enough).
- Pseudocode MUST NOT contain secrets, credentials, API keys observed in source — redact.
- `file:line-range` cited in `**Source:**` MUST exist and contain the referenced logic (reviewer verifies via Read).

## Valid Background Logic Requirements

| Criteria | Check |
|----------|-------|
| Has Type | Must use a valid type (see Background Logic Types table) |
| Has Trigger | Must have a trigger condition |
| Has US Mapping | Must have at least one system US### mapped |

## Validation Rule Patterns

Detection patterns for validation rules in source code:

| Pattern | Example | Framework |
|---------|---------|-----------|
| `@NotNull`, `@Required` | `@NotNull` | Java, Kotlin |
| `NOT NULL` | `name VARCHAR(255) NOT NULL` | SQL |
| `unique` constraint | `UNIQUE(email)` | SQL |
| `@Unique` | `@Unique` | Various |
| `min/max` | `min: 1, max: 100` | JS/TS validators |
| `@Min`, `@Max` | `@Min(0) @Max(120)` | Java |
| `length` | `length: { min: 2, max: 50 }` | JS/TS |
| `@Size` | `@Size(min=2, max=50)` | Java |
| `pattern` / `regex` | `pattern: /^[a-z]+$/i` | JS/TS |
| `@Pattern` | `@Pattern(regexp="^[A-Z]")` | Java |
| `email` validator | `type: 'email'` | JS/TS |
| `@Email` | `@Email` | Java |
| `required` | `required: true` | JSON Schema |
| `allowNull: false` | `allowNull: false` | Sequelize |
| `validate: { notNull }` | `validate: { notNull: true }` | Sequelize |
