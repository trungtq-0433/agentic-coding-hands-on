# Screen Flow

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

**Code Format**: All SCR codes MUST follow `SCR###_NameSlug` format (e.g., SCR001_LoginForm, SCR002_Dashboard) | `SCR###/REG###` for region-scoped transitions

<!-- STACK-AWARE SECTIONS (v21.0.0) — keyed on the profile's `screen_source`:
     • route-view (web): author EVERY section below exactly as shown (unchanged behavior).
     • dfm-form (Delphi/VCL desktop): a desktop app has no routes/URLs/HTTP guards/`beforeunload`.
       KEEP: `## Navigation Map` (Mermaid form→form graph from the nav digest), `## Feature Entry
              Points` (route-free shape below), `## Screen Access Paths`, `## Screen Transitions`,
              `## Region Transitions`, `## Error Handling Flows`, `## Circular Dependencies Check`.
       OMIT entirely (do NOT emit empty stubs, do NOT fabricate web content):
              `## Authentication Flow`, `## Guard Logic`, `## Deep-Link State Restoration`,
              `## Unsaved-Changes Protection`, `## Extraction Signatures`.
       The Navigation Map edges come from `_digest_extract_form_nav.json`; each edge is a
       Show/ShowModal/CreateForm call. Label edges with the trigger control + cite `file:line`.
       A form with no static inbound edge is drawn with an `[UNVERIFIED]` entry node — never dropped.
     ONE template, conditional sections — do NOT fork a parallel desktop template. -->

## Navigation Map

```mermaid
graph TD
    A[{START}] -->|Entry| B[{SCR001_NAME}]
    B -->|Action 1| C[{SCR002_NAME}]
    B -->|Action 2| D[{SCR003_NAME}]
    C -->|Back| B
    D -->|Back| B
```

## Feature Entry Points

{Populated by FS.1 researchers (feature-specs pass) AFTER feature-list.md exists. W2 ScreenFlow researcher leaves this section as the placeholder below — do NOT populate it during W2.}

{POPULATED_BY_W6}

{FS.1 researcher pattern: each FS.1 researcher emits a fragment file `plans/<active>/artifacts/_feature-entry-points/F###.md` (one file per feature, no write contention). After all FS.1 tasks complete, the orchestrator consolidates all fragment files into this section (FS.1.5).}

{Template for each feature subsection — written into the fragment file:}

### F###_{name}

<!-- route-view (web): -->
- **Entry screen**: {SCR###_Name} — `{/initial/route}`
- **Owned screens**:
  - {SCR###_Name} — `{/route/path}` (atomic | composite)
- **Exit screens**: {SCR###_Name} (on {action/completion})

<!-- dfm-form (Delphi): replace the route with the invoking caller (no URL exists) —
- **Entry form**: {SCR###_Name} — invoked by {CALLER_FORM/UNIT} via {Show|ShowModal|CreateForm} — `{file}:{line}`
- **Owned forms**:
  - {SCR###_Name} (atomic | composite) — `{file}:{line}`
- **Exit forms**: {SCR###_Name} (on {action/completion})
-->


---

{POPULATED_BY_FRAGMENTS}

## Screen Access Paths

| From Screen | To Screen | Action/Trigger | Conditions | Region |
|-------------|-----------|----------------|------------|--------|
| {START} | {SCR001_CODE} | Initial load | None | |
| {SCR001_CODE} | {SCR002_CODE} | {ACTION} | {CONDITION} | |
| {SCR001_CODE} | {SCR003_CODE} | {ACTION} | {CONDITION} | |
| {SCR002_CODE} | {SCR001_CODE} | Back button | None | |
| {SCR003_CODE} | {SCR001_CODE} | Back button | None | |

> Region column: fill with `SCR###/REG###` for region-scoped transitions; leave blank for whole-screen transitions.

## Screen Transitions

### {SCR001_CODE} ({SCR001_NAME})

**Entry Points**:
- Direct URL access
- From external link
- From {SCR003_CODE}

**Exit Points**:
- To {SCR002_CODE}: {REASON}
- To {SCR003_CODE}: {REASON}

**Decision Points**:
- {DECISION_1}: If {CONDITION} → {SCR002_CODE}, else → {SCR003_CODE}

---

### {SCR002_CODE} ({SCR002_NAME})

**Entry Points**:
- From {SCR001_CODE}: {ACTION}

**Exit Points**:
- To {SCR001_CODE}: Back navigation

**Decision Points**:
- None

---

### {SCR003_CODE} ({SCR003_NAME})

**Entry Points**:
- From {SCR001_CODE}: {ACTION}

**Exit Points**:
- To {SCR001_CODE}: Back navigation

**Decision Points**:
- None

---

## Region Transitions

> Region transitions are typically client-state (no URL change); document only transitions that change user-visible state within the region or cross region boundary.

| From Region | To Target | Action/Trigger | Client-State Only |
|-------------|-----------|----------------|-------------------|
| SCR001_AdminDashboard/REG001 (UserPanel) | MOD003_AddUser (modal) | Click "Add User" button | Yes |
| SCR001_AdminDashboard/REG002 (MetricsPanel) | SCR007_MetricDetail (full screen) | Click metric row | No (URL changes) |

---

## Authentication Flow

```mermaid
graph LR
    A[Public] -->|No Auth| B[{SCR001_Name}]
    A -->|Requires Auth| C[Login]
    C -->|Success| D[{SCR002_Name}]
    C -->|Fail| B
    D -->|Logout| B
```

| Screen | Authentication Required | Authorization Level |
|--------|------------------------|-------------------|
| {SCR001_CODE} | No | Public |
| {SCR002_CODE} | Yes | User |
| {SCR003_CODE} | Yes | Admin |

---

## Error Handling Flows

| Screen | Error | Handling | Scope |
|--------|-------|----------|-------|
| {SCR001_CODE} | Network Error | Show retry dialog | screen |
| {SCR002_CODE} | Auth Expired | Redirect to login | screen |
| {SCR003_CODE} | Not Found | Show 404 screen | screen |
| SCR001_AdminDashboard | Metrics load failure | Show inline error in MetricsPanel | region:REG002 |

> Scope values: `screen` (affects entire screen) | `region:REG###` (error contained within the named region).

---

## Circular Dependencies Check

- [x] No circular dependencies detected
- [x] All screens have valid entry/exit points
- [x] All navigation paths terminate

---

## Guard Logic

Route guards intercept navigation to enforce conditions beyond authentication — loading required data, checking permissions, or applying business rules. Document each guard found on any route.

### GUARD-### — {guard name} on {ROUTE### or path}
**trigger:** `{beforeRouteEnter | canActivate | middleware | loader | before_action | etc.}`
**source:** `{file:line}`
**logic:**
```pseudo
if (!condition_a) → redirect /target-a
if (!condition_b) → redirect /target-b
```
**failure path:** `{redirect target, toast + stay, or error component}`

---

**Example:**

### GUARD-001 — AdminOnly on /admin/*
**trigger:** `canActivate` (Angular) / `beforeEnter` (Vue Router)
**source:** `src/router/guards/admin.guard.ts:18`
**logic:**
```pseudo
if (!currentUser) → redirect /login
if (!currentUser.hasRole('admin')) → redirect /403
```
**failure path:** unauthenticated → `/login`; unauthorized → `/403`

---

*If no route guards detected:* `N/A — no route guards detected.`

---

## Deep-Link State Restoration

Document screens where URL parameters or path segments reconstruct non-trivial UI state on direct visit (bookmarked URL, shared link, browser refresh). This is distinct from simple routing — it means the app reads URL params and rehydrates view state from them.

### {SCR### or screen name}
**URL pattern:** `{path pattern with param placeholders}`
**State restored:**

| Param | Restores | Default if missing |
|-------|----------|--------------------|
| {param} | {UI element / state field} | {default value} |

**Failure mode:** `{what happens when param is invalid or missing — silently ignored, redirect, error boundary}`

---

**Example:**

### SCR-004 — OrderListScreen
**URL pattern:** `/orders?status={s}&sort={field}&page={n}`
**State restored:**

| Param | Restores | Default if missing |
|-------|----------|--------------------|
| status | filter dropdown selection | "all" |
| sort | column sort direction | "created_at desc" |
| page | pagination position | 1 |

**Failure mode:** unrecognized `status` value silently defaults to "all"; invalid `page` resets to 1

---

*If no URL-driven state restoration detected:* `N/A — no URL-driven state restoration detected.`

---

## Unsaved-Changes Protection

Document screens and forms that warn the user before discarding unsaved input — via browser `beforeunload`, route-leave guards, or modal close intercepts.

### {SCR### or form name}
**trigger:** `{beforeunload | route leave guard | modal close handler | component unmount}`
**source:** `{file:line}`
**dirty detection:** `{field-level comparison | form library isDirty flag | manual boolean flag}`
**prompt:** `"{exact warning text shown to user, or 'browser default' if native dialog}"`

---

**Example:**

### SCR-007 — OrderEditForm
**trigger:** `beforeunload` + route leave guard (`useBeforeUnload`)
**source:** `src/features/orders/OrderEditForm.tsx:203`
**dirty detection:** React Hook Form `formState.isDirty`
**prompt:** "You have unsaved changes. Are you sure you want to leave?"

---

*If no unsaved-changes protection detected:* `N/A — no unsaved-changes guards detected.`

---

## Extraction Signatures

Framework-agnostic identifier patterns for locating the above constructs.

### Guard Logic
Function/method definitions tied to a route: `beforeEnter|canActivate|middleware|loader|before_action|authenticate|authorize` — check if called from a router config or route registration.

### Deep-Link State Restoration
URL param reads at component mount synced to state: `useSearchParams|useQuery|router\.query|URLSearchParams|params\[|$route\.query` — look for these at top of component with corresponding `setState` or reactive assignment.

### Unsaved-Changes Protection
`beforeunload|onbeforeunload|usePrompt|useBeforeUnload|leaveGuard|isDirty|formState\.isDirty|data-turbo-confirm` — presence confirms protection; absence is a potential gap to flag.