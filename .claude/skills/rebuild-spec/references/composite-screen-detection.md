# Composite-Screen Detection Rules (H1-H6)

Applied by: Wave 2 researcher on every screen file, unconditionally. Classification is authoritative.

**Execution order:** H6 → H4 → H5 → H2 → H3 → H1 → 2-of-3 gate.
H1–H6 are signal identifiers, not execution order — always follow the order above.

---

## Stack Probe

Your task description contains `Detected stack: {value}` — injected by the orchestrator from
`scout-report.md § ## Detected Language` (Wave 0 output). Use it to select signal rows in
per-stack tables below.

**Fallback** — if `Detected stack:` absent from task description → use JS/TS signals.

**MULTI_STACK** — when the value carries `[MULTI_STACK — all stacks: X, Y, ...]`, the
orchestrator has enumerated every root-level manifest. Apply union as follows:

1. Parse the `all stacks: X, Y, ...` comma-list from the note.
2. For every H-rule table below (H2 include/exclude, H3, H4, H5, H6), consult the row for
   EACH listed stack — not just the primary.
3. OR-merge their signal lists: a screen passes a rule if any listed stack's row matches.
4. For H2 imports: use the union of include patterns AND the union of exclude patterns
   from every listed stack (exclusion still wins on collision).
5. H6 distinct-route counting is stack-agnostic — counts route paths, not signals.

If `[MULTI_STACK]` is present but no `all stacks:` list (older runs), fall back to JS/TS only
and emit `[STACK_LIST_MISSING]` advisory note in the screen's classification justification.

**Non-exhaustive tables** — the per-stack signal tables in H2/H3/H4/H5/H6 below are
**starting examples**, not complete enumerations. Stack listed but library/naming differs
(custom UI lib, custom component names), or stack not listed at all (Solid.js, Qwik,
Phoenix LiveView, etc.) → use the `[SIGNAL_INFERRED]` protocol described below.

---

## Signal Inference Fallback

When per-stack tables (H2/H3/H4/H5/H6) have no row matching the screen's stack/library OR
the stack's row uses different naming than what the screen actually uses, the researcher
MAY classify based on the rule's `**Intent:**` if the screen's pattern matches semantically.

**Protocol:**
1. Tag the classification with `[SIGNAL_INFERRED]` in ScreenList Notes.
2. Provide a 3-part justification (all three parts MANDATORY):
   - **Intent matched:** which H-rule's Intent the pattern fits (e.g., "H4 — mutually
     exclusive content panels switched by user selection, same URL")
   - **No-row reason:** why no per-stack row applies (e.g., "stack=Solid.js, no row in
     H4 table" or "stack=React, but project uses custom `<MyTabs>` not standard `<Tab>`")
   - **Observed pattern:** what was actually seen (e.g., "5 buttons each toggling
     visibility of one of 5 sibling divs via `signal()` state; only one visible at a time")
3. The classification follows the matched H-rule's outcome (SCR variants for H4/H5/H6
   short-circuits, region count for H3, etc.) — Intent governs, signal table is bypassed.

**Limits:**
- Do NOT use `[SIGNAL_INFERRED]` to bypass an existing per-stack row that DOES match —
  use the explicit row first.
- Do NOT use to upgrade atomic → composite without a clear H-rule Intent match.
- Justification must cite a specific H-rule (H2/H3/H4/H5/H6), not vague "looks composite".
  H1 has no signal table — `[SIGNAL_INFERRED]` is invalid for H1.
- In `[MULTI_STACK]` mode, if any listed stack's row already satisfies the rule via the
  union procedure, do NOT tag `[SIGNAL_INFERRED]` for the unmatched stacks.
- Tag is advisory; remove when a future skill update adds a per-stack row covering
  the same pattern.

---

## H6 — Router Outlet (SHORT-CIRCUIT, apply BEFORE H1-H4)

**Intent:** The screen file's primary content is a placeholder that delegates rendering
to child routes — each child has its own URL path segment and independent data fetch.

**Per-stack router outlet signals:**

| Stack | Outlet pattern in file | Route config location |
|-------|------------------------|----------------------|
| Vue/Nuxt | `<router-view>`, `<nuxt-child>` | `pages/` dir tree or `router.ts` / `routes.ts` |
| React | `<Outlet>` (v6), `<Switch><Route>` (v5) | `react-router-dom` route config |
| Angular | `<router-outlet>` | `RouterModule.forRoot` / `forChild` |
| Svelte/SvelteKit | `<slot>` in `+layout.svelte` | `+page.svelte` siblings in dir |
| Laravel/Blade | `@yield('content')` in master + `@extends` in child | `routes/web.php` route groups |
| Rails/ERB | `<%= yield %>` in `application.html.erb` | `config/routes.rb` nested resources |
| Django | `{% block content %}{% endblock %}` in base + `{% extends %}` in child | `urls.py` `include()` patterns |
| Go/template | `{{ template "content" . }}` in layout file | `mux.Handle` or framework router |
| Java/Thymeleaf | `th:replace` / `th:insert` in layout | `@GetMapping` in controller |
| Rust/Askama | `{% block content %}{% endblock %}` in base + `{% extends "base.html" %}` in child | `axum::Router` nested handlers (Leptos uses component-tree routing — H6 typically N/A) |

**Condition:** Route config shows ≥2 direct child routes each with (a) distinct URL path segment,
(b) distinct source file, (c) ≥1 distinct API call or mutation not shared with siblings.
→ Emit one SCR### per qualifying child route. Emit [H6] tag in ScreenList Notes. STOP.
→ Parent shell: SCR### only if independent data fetch OR persistent layout UI (sidebar, nav).
  Navigation-only shell → no SCR; document as shared layout context in child SCR descriptions.
→ DO NOT emit REG### for router-outlet children (distinct URLs, not content zones).

**Disambiguation from H4:** H4 fires on tab UI state (same URL). H6 fires on distinct route path.
Both present → apply H6 first; H4 sub-analysis within each H6 child.

**File-based routing (common stacks):**
  - Nuxt: `pages/foo/_id/index.vue` (shell with `<nuxt-child>`) + siblings = H6 children.
  - Rails/Laravel/Django: nested route group with own controller/view per child = H6 candidates.

**Shared data ≠ same screen.** Common params (ids, names) via URL or store are NOT evidence of
grouping. Route path is the authoritative screen boundary.

---

## H4 — Mutual-Exclusion Content Tabs (SHORT-CIRCUIT)

**Intent:** The screen renders mutually exclusive content panels on the SAME URL,
switched by user tab selection (not navigation).

**Per-stack signals:**

| Stack | Signals |
|-------|---------|
| React / Vue (component libs) | `<Tab>`, `<TabPanel>`, `<TabList>`, `<Tabs>` component names |
| Angular Material | `<mat-tab>`, `<mat-tab-group>`, `<mat-tab-label>` |
| Java/Vaadin | `Tab`, `TabSheet` components; Thymeleaf: `th:classappend` + `.active` on tab trigger |
| ARIA / native HTML | `role="tab"` + `role="tabpanel"` + `role="tablist"` attribute combination |
| Bootstrap / CSS-driven | `.nav-tabs`, `.tab-content`, `.tab-pane` CSS class pattern |
| Alpine.js | `x-data` with active-tab state + `x-show` / `@click` switching between panels |
| Rails/Stimulus | `data-controller="tabs"` + CSS `.tab-pane.active` toggling |
| HTMX / Go | `hx-target` + tab-like trigger with CSS class swap (`.tab-pane`) |
| Rust/Leptos | `<Tabs>`, `<Tab>` components (Leptos UI crates) |
| Blade/Bootstrap | `@foreach` over tab labels + `@if($activeTab === ...)` content blocks |

**Condition:** Any signal above present → emit SCR variants (SCR###a/b). STOP. No REG.
EXCLUDE: tab signals from H3 count.

---

## H5 — Wizard / Stepper

**Intent:** The screen renders a sequential multi-step workflow sharing the same URL
(or session-scoped POST cycle) but differing per step in layout/fields.

**Per-stack signals:**

| Stack | Signals |
|-------|---------|
| React / Vue (component libs) | `<Step>`, `<Stepper>`, `<WizardStep>`, `<Wizard>`, `<StepperPanel>` |
| Angular Material | `<mat-step>`, `<mat-stepper>` |
| Java/Spring | `@SessionAttributes` multi-form; Spring WebFlow `<view-state>`; Thymeleaf step fragments |
| ARIA / native HTML | `aria-valuenow` + `aria-valuemax` on progress element; `data-step` attributes |
| CSS classes | `.step`, `.wizard-step`, `.stepper-step`, `.step-active`, `.step--current` |
| URL pattern (server-side) | Sequential step URLs sharing session: `POST /wizard/step/1`, `GET /wizard/step/2` |
| Rails/Stimulus | `data-controller="wizard"` + session `current_step`; `wicked_wizard` gem |
| Laravel | `session(['step' => $step])` + multi-step POST to same controller |
| Django | `django-formtools` wizard view; `step` kwarg in URL pattern |
| Go/htmx | `hx-swap` + `?step=N` query param; sequential `POST /step/{n}` handlers |
| Rust/Leptos | `<Stepper>`, `<Step>` components; Axum session `step` key |

NOT a hard rule. Researcher MUST inspect step content and classify:

  **Case A** (distinct UI + distinct validation + distinct action/endpoint per step)
    → SCR variants (SCR###a/b/c), STOP. No REG. Requires explicit evidence citation in spec.
  **Case B** (shared state/endpoint, differs only in layout/fields)
    → composite SCR### with REG001_StepN children (proceed through H2/H3/H1).

  Defaults: 2-step wizards → Case B always.
           ≥3-step wizards → Case B default; Case A only with cited
           distinct-validation + distinct-endpoint evidence.

EXCLUDE: wizard/stepper signals from H3 count.

---

## H2 — Domain Module Imports Gate

**Intent:** The screen file imports ≥2 distinct domain/feature modules, indicating it
assembles multiple independent business-logic concerns.

**Per-stack include patterns (count imports matching these):**

| Stack | Count imports from |
|-------|-------------------|
| JS/TS | `features/*`, `modules/*`, `domains/*`, `@/features/*`, `@/modules/*` |
| PHP/Laravel | `App\Features\*`, `App\Modules\*`, `App\Domain\*`, `App\Services\{Feature}\*` (require feature sub-namespace; bare `App\Services\*` is too broad — fires on every controller) |
| Ruby/Rails | `require 'features/*'`; namespaced: `Features::*`, `Modules::*`, `Domain::*` |
| Python/Django | `from apps.<sub> import` / `from modules.<sub> import` / `from domain.<sub>` (where `<sub>` is any feature/domain sub-module name — match the import-path pattern, not the literal placeholder) |
| Java/Kotlin | `com.app.features.*`, `com.app.modules.*`, `com.app.domain.*` |
| Go | package paths `./features/*`, `./modules/*`, `./domain/*`, `./internal/domain/*` |
| Rust | `use crate::features::*`, `use crate::modules::*`, `use crate::domain::*` |

**Per-stack exclude patterns (do NOT count these):**

| Stack | Exclude |
|-------|---------|
| JS/TS | `ui/*`, `shared/*`, `design-system/*`, `@mui/*`, `@shopify/*`, `@chakra/*`, `@radix-ui/*`, `@ant-design/*` |
| PHP/Laravel | `Illuminate\*`, `App\Http\Middleware`, `App\Providers`, `App\Http\Requests` |
| Ruby/Rails | `ApplicationController`, `ActionController::*`, `ActiveRecord::*`, Rails framework |
| Python/Django | `django.*`, `rest_framework.*`, `typing`, stdlib modules |
| Java/Kotlin | `org.springframework.*`, `javax.*`, `jakarta.*` |
| Go | stdlib packages (`fmt`, `net/http`, etc.), `github.com/` third-party framework paths |
| Rust | stdlib (`std::*`), `actix_web::*`, `axum::*` framework primitives |

≥2 distinct include-pattern matches (after exclusions) = H2 pass.

---

## H3 — Semantic Content Regions

**Intent:** The screen contains ≥3 distinct named semantic content zones —
independently loadable or visually framed self-contained regions.

**Per-stack signals (count distinct occurrences):**

| Stack | Count these as region wrappers |
|-------|-------------------------------|
| React / Vue (component libs) | `<Card>`, `<Panel>`, `<Section>`, `<Widget>`, `<Aside>`, `<Box role="region">` |
| Angular Material | `<mat-card>`, `<mat-expansion-panel>`, `<mat-sidenav>` |
| Angular CDK / generic | `<cdk-accordion-item>`, `<cdk-accordion>` (CDK primitives, not Material-specific) |
| ARIA / native HTML | `<section>`, `<article>`, `<aside>`, `role="region"` attributes |
| CSS (framework-agnostic) | `.card`, `.panel`, `.widget` root elements (top-level class only, not nested) |
| Laravel/Blade | `@include('partials.card')`, `@component('panel')` — count distinct partial names |
| Rails/ERB | `render partial: 'widgets/chart'`, `render 'sections/table'` — count distinct partials |
| Django | `{% include 'partials/card.html' %}` — count distinct template names included |
| Go/template | `{{ template "card" . }}`, `{{ template "panel" . }}` — count distinct template calls |
| Java/Thymeleaf | `th:replace="~{fragments/card}"` — count distinct fragment refs |
| Rust/Leptos | `<Card>`, `<Section>`, `<Panel>` components; Askama: `{% block sidebar %}` |

≥3 distinct region wrappers (per stack column above) = H3 pass.

EXCLUDE: Tab/tabpanel signals (H4-only) and wizard/stepper wrappers (H5-only) from this count.

**Raw-div fallback:** H3=0 → gate falls back to H1+H2 only (see 2-of-3 Gate).
  Known Detection Limitation: raw `<div>` projects under-trigger H3. Tag as [H3_RAW_DIV].

---

## H1 — Feature Refs Tiebreaker

≥3 feature refs on screen file = H1 pass.

---

## 2-of-3 Gate

Flag composite iff 2-of-3 signals pass: **(H1∧H2) ∨ (H1∧H3) ∨ (H2∧H3)**.
Raw-div fallback: H3=0 → use H1+H2 only; both fail → atomic + warning.

---

## Composite Hard Guard

A composite SCR is valid **ONLY** when its source maps to exactly **ONE** view/page file.

Rules:
1. **≥2 view files under one namespace/route prefix → emit one SCR per file.** Apply H6 to determine child-route boundaries. Never collapse multiple view files into a single composite SCR.
2. **A wildcard route (`/x/*`, `/admin/**`, `:splat`, `/...`) MUST NOT be represented as a single SCR.** Wildcards mask an unknown number of concrete child routes. Expand to the concrete child routes listed in RouteList before emitting any SCR. Each concrete child route with a distinct view file = one SCR. If RouteList does not enumerate the child routes, flag `[WILDCARD_UNEXPANDED]` and request RouteList revision before proceeding.
3. **Namespace-prefix with ≥2 distinct controllers/handlers → N separate SCRs (one per handler), not one composite.** A shared URL prefix (e.g. `/admin/`) is not evidence of a composite screen; it is evidence of a route group. Apply H6.

Cross-reference: [H6](#h6--router-outlet-short-circuit-apply-before-h1-h4) governs router-outlet child decomposition. The Composite Hard Guard governs source-file-to-SCR cardinality. Both apply unconditionally.

---

## Additional Constraints

W1 researchers (SystemOverview, RouteList, DataModel) MUST NOT emit REG###.
REG### first appears in W2 ScreenList. Orphan REG### in W1 artifact → critical.
