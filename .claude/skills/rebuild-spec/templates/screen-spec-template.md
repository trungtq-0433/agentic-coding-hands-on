<!-- Contract: references/screen-spec-researcher-contract.md -->

# {SCR###_Name} — Screen Spec

**Screen**: {SCR###_CODE}: {NAME}
**Feature**: {F###_NAME}
**Type**: {atomic|composite}
**Route**: {URL}
**Generated**: {DATE}

<!-- **Feature** is the F###_NameSlug (from feature-list.md) that OWNS this screen — the
     inverse of the SCR### column in that feature's screens.md. MUST resolve to a row in
     feature-list.md (validate_feature_screen_link.py enforces this). -->

## Purpose

{1 sentence: who uses this screen, what they accomplish, and when they encounter it. Plain language — no component names, no technical internals.}

## Screen Layout

{2–4 sentences naming major regions (header, sidebar, main content area, modals/drawers). Note fixed/sticky positioning and responsive breakpoints if present. Cite layout root file:line in trailing parenthetical.}

<!-- N/A is NOT allowed here. If layout is truly unreadable, escalate as Unresolved Question instead. -->

### Layout Sketch

```
┌─────────────────────────────────────────┐
│  R1: {Name} ({fixed-top|sticky|static}) │
├──────────────┬──────────────────────────┤
│ R2: {Name}   │ R3: {Name} (scrollable)  │
│ ({position}) │                          │
└──────────────┴──────────────────────────┘
```

<!-- Required: ASCII box diagram of top-level regions. Label each box with Region ID (R1, R2, …) matching the Layout Regions table. Use dashed lines (- - -) for conditionally visible regions. Nested boxes for modals/drawers that float above main layout. Proportions approximate — not pixel-perfect. -->

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | {e.g., Top Nav} | {fixed-top \| sticky \| static} | {yes \| no} | {component names from imports} | {visible-md+ \| hamburger-sm \| always} |
| R2 | {e.g., Main Content} | {static} | {yes \| no} | {component names} | {fluid \| max-width-Xpx} |

<!-- Required: ≥2 rows (at minimum: top container + content area). Even fullscreen/modal screens have an outer wrapper + content region. -->
<!-- For SSR/template-rendered screens, Key Components may be CSS class names or template partial names. -->
<!-- Source citation: parent prose cites layout root; per-region citations optional unless region maps to a non-obvious file. -->

<!-- ## Child Routes: EMIT ONLY FOR H6 SHELL SCREENS
     Trigger: screen tagged [H6] in screen-list.md
     Source: read route config to enumerate child routes -->

## Child Routes

| Route | SCR | URL | Notes |
|-------|-----|-----|-------|
| {label in nav} | SCR###a | {/path/a} | {one-line child purpose} |
| {label in nav} | SCR###b | {/path/b} | {one-line child purpose} |

<!-- Route config source: {file}:{line} -->

## User Flow

> **Scope:** within-screen interactions only. Cross-screen navigation belongs in `screen-flow.md`. Reference region names from `### Layout Regions` above when describing where actions occur.

### Happy Path

1. {Numbered step — user action observable on this screen, referencing region if relevant (e.g., "User clicks Submit in R2 Main Content")}
2. {Next step — system response visible on this screen}
3. {... continue until terminal state or hand-off to another screen}

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| {step number/label} | {condition checked} | {visible outcome — alt UI state, inline error, secondary CTA} | `{file}:{line}` |

{`N/A — single-action screen, no branches`} *(use when screen has 1 primary CTA and no conditional sub-flows)*

<!-- Format note: numbered prose for happy path; table for branches. No Mermaid — per-feature flows live in screen-flow.md. -->
<!-- [WARN_ADVISORY]: if screen-flow.md is already in context, spot-check that terminal steps here align with navigation events there. Not a required cross-ref load. -->

## Data Inventory

> **Scope:** read-only displayed fields only. Editable form input fields are documented in `## Validation & Error Feedback` — do NOT duplicate them here. Document what the user sees, not DB constraints. Cross-ref `data-model.md` MODEL### for type/nullable/server-side rules.

| Field | Display Label | Source | Format | Empty Behavior | Cross-ref |
|-------|---------------|--------|--------|----------------|-----------|
| {variable/binding name} | {visible label or column header} | {API field \| route param \| store state \| computed} | {date format \| currency \| truncation \| raw} | {dash \| placeholder text \| hidden} | {MODEL###.field or `N/A`} |

<!-- Required: list every distinct read-only field rendered to the user. Skip editable inputs — those belong in Validation & Error Feedback. -->
<!-- Cap: max 20 primary fields. For dense screens with repetitive patterns, group as `{field_1..N}` with a single row + note. -->
<!-- Computed fields: `Source: computed` + show derivation in trailing parenthetical citing file:line. -->
<!-- DO NOT copy type/nullable from data-model.md — reference MODEL###.field in Cross-ref column. -->

{`N/A — screen displays no dynamic data (static marketing/error page)`} *(use only after confirming source has no bindings/interpolations)*

## UI States

> **Required rows:** loading + ≥1 error (per async call) + ≥1 empty (per data-displaying region) + saving/submitting + success/redirect. Write `N/A — no async ops` only if screen has zero API calls.

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | API in-flight | skeleton/spinner | none | `{file}:{line}` |
| empty | 0 results | empty-state illustration + CTA | {CTA label} | `{file}:{line}` |
| error | API error / network | error message + retry | retry | `{file}:{line}` |
| saving | mutation in-flight | button spinner / disabled form | none | `{file}:{line}` |
| success | mutation complete | toast / inline confirmation | dismiss | `{file}:{line}` |
| {custom} | {trigger} | {behavior} | {action} | `{file}:{line}` |

## Validation & Error Feedback

### A) Client-side

| Field | Type | Required | Constraints | Async Check | Error Message |
|-------|------|----------|-------------|-------------|---------------|
| {field} | {type} | yes/no | {min/max/regex} | {endpoint if any} | {message} |

{`N/A — no client-side form validation detected.`}

### B) Server-side

<!-- One block per submit-style action. -->

#### {Action name}
- **Endpoint:** `{METHOD /path}`
- **Request:** `{field1, field2, ...}` *(fields the UI sends)*
- **Success:** `{HTTP code}` → {outcome: redirect / toast / state change}
- **Errors:** `{code}` {user-visible message or toast text} | `{code}` {message}
- **Trigger:** {gesture — button click / form submit / keyboard shortcut}
- **Source:** `{file}:{line}`

{`N/A — no submit-style action handlers detected.`}

## Interaction Patterns

<!-- Format: "**{User behavior — observable outcome}** — source: {file:line}" -->
<!-- BAD: "Root div has @click='resetTarget' which calls store.dispatch..." -->
<!-- GOOD: "Clicking outside any group deselects it — source: questions.vue:2" -->

- **{User behavior — observable outcome}** — source: `{file}:{line}`

{`N/A — no non-trivial interaction patterns detected (only standard form input bindings).`}

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | {present\|absent\|partial} | {aria-label, role=, aria-labelledby usage} |
| Keyboard navigation | {supported\|not implemented\|unknown} | {tab order, shortcut keys} |
| Focus management | {managed\|unmanaged} | {modal/drawer focus trap, autofocus} |
| Screen reader compatibility | {unknown\|tested} | {label linkage, semantic landmarks} |

{When all status cells are absent/unmanaged/unknown: `[NO_A11Y_DETECTED] — accessibility audit needed before production release.`}

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| {role/flag/breakpoint/literal} | {auth\|feature-flag\|responsive\|legacy\|hardcoded-id} | {component} | {component} | {consequence of bypass for auth; [NEEDS_DOMAIN_CONFIRMATION] for hardcoded-id/legacy} |

{`N/A — no conditional rendering detected.`}

## Component Variants

<!-- Omit this section if no shared polymorphic component renders on this screen. -->

| Component | Discriminating field | Variants on this screen | Screen-specific props/slots | Cross-ref |
|-----------|---------------------|------------------------|----------------------------|-----------|
| {ComponentName} | {prop/field} | {variant-a, variant-b} | {props this screen passes} | DISC-### |

<!-- Cross-ref: prefer DISC-### from data-model.md when available. DO NOT restate variant business rules — reference only. -->

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|------------------------|
| {expression / route guard / middleware name} | {auth\|permission\|role} | {redirect / 403 from API / data exposure} |

{`N/A — no auth guards or permission checks detected on this screen.`}

<!-- When not triggered (no auth-type CR rows, no route guards found): use the N/A string above. When triggered: replace the placeholder row with real guard entries. -->
<!-- For each guard, note server enforcement: "[UNVERIFIED] server enforcement — static analysis cannot confirm API middleware" when unknown. -->

## Source References

<!-- v26.0.0 (A3, F15 DRY): numbered = the reading-order recast (1 = read first). This list IS
## Source Walkthrough's related-files table — do NOT author a second, independent file list. -->

1. Page/View: `{file}:{line}`
2. Form schema / validation: `{file}:{line}`
3. State management: `{file}:{line}`

{List every file read to produce this spec, in recommended reading order. Minimum 1 entry (the
page/view file). DO NOT fabricate paths.}

## Source Walkthrough

<!-- v26.0.0 (A3, renamed from "Code Reading Guide" per F15). NEW REQUIRED section, gated by
scripts/validate_reading_guide_db_impact.py (dedicated validator, WARN-first `*.pre_migration`
degradation contract — screen-spec has no other Python structural validator today). -->

{Ordered reading list (data model → entry point → view → logic) covering the files above, 1 file
per step, with a 1-sentence "why start here." Cite each file with the `**File:**` label (NOT
`**Source:**` — keeps this navigational list out of the A1 confidence-report citation-coverage
stat; see `references/confidence-report-contract.md` § A3 navigational entries). Cross-reference
`entities.md` MODEL### for the data layer — this screen has no server-side data layer of its own.}

1. **File:** `{path/to/page-view-file.ext:start-end}` — {why start here: the page/view component itself}
2. **File:** `{path/to/component-file.ext:start-end}` — {next: a key imported component}

### Call Hierarchy

{ASCII or Mermaid diagram of the render/interaction chain — page/view → component(s) → store/hook.}

```text
{Page/View} -> {Component} -> {Store/Hook}
```

**Related files:** see `## Source References` above (already numbered in reading order — F15
DRY, one list not two).
