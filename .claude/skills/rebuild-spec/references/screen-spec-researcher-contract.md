# Screen Spec Researcher Contract (Wave 2.5 — rebuild-spec)

Consumed by W2.5 researcher subagents generating per-screen ScreenSpec artifacts.
Activated only when `--screen-specs` flag is set.

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST. Then read the target SCR### section from `screen-list.md` and the relevant entity sections from `entities.md` (data model). Do NOT re-derive information already in the session context.

Note the project stack (frontend framework + backend language) from session-context.md. JS/TS (Vue/React) patterns are shown as primary examples throughout; inline `(stack: ...)` notes in each section provide alternatives for Python, Rails, PHP, and other stacks.

**v24.0.0 — Feature backlink (header, MANDATORY):** the screen-spec header MUST carry `**Feature**: F###_Name` (placed directly under `**Screen**`) — the feature that OWNS this screen, sourced from `screen-flow.md` § Feature Entry Points (`**Owned screens**`) or `feature-list.md`. It is the inverse of the `SCR###` column in that feature's `screens.md`, and MUST resolve to a `feature-list.md` row (`validate_feature_screen_link.py` enforces it both ways).

## Purpose Extraction Rule

Write 1 sentence in plain language: who uses this screen (role/persona), what they accomplish (goal), and when they encounter it (entry point or trigger).

**Voice:** User-narrative, not implementation-narrative.
- REJECT: "The Vue page renders a `FormContainer` with `useFormStore` composable..."
- ACCEPT: "Survey participants complete and submit assigned questionnaire forms from this screen."

**Source signals:** Page title, route name, primary CTA button label, primary form submit handler or main action event.
**N/A:** NOT allowed. If purpose is unclear from code, write `[UNVERIFIED] {best-effort description} — needs domain confirmation.`

## Scope Boundary (CRITICAL)

**ScreenSpec documents UI-LAYER behaviour only.**

| Belongs in ScreenSpec | Belongs in Feature Spec |
|----------------------|------------------------|
| UI states (loading/empty/error/success) | Server-side validation rules (BR/SM/ALG) |
| Client-side form validation (field constraints, async checks) | Business workflow (BR/SM/ALG) |
| Interaction patterns (optimistic update, infinite scroll) | Background logic (BL###) |
| ARIA roles, keyboard navigation, focus management | Decision logic (DEC-###) |
| Client-side conditional rendering (role gates, feature flags, breakpoints) | FR/BR/SM/ALG/INT/SC codes |
| Screen-specific UI state machines | Cross-feature navigation (→ screen-flow.md) |
| Server-side validation feedback visible to the user (error messages, toasts, banners) | Server-side validation logic itself |

**Never write FR/BR/SM/ALG/INT/SC codes in ScreenSpec.** Cross-reference `entities.md` for server-side field constraints (do not re-state them — reference the source).

## Mandatory Source-Code Reading

- You MUST read the actual source code files (controllers, models, jobs, services,
  Vue/React pages) for every screen — NOT just summarize from upstream artifacts.
- Use Grep/Read tools to find the real page/view files, form schemas, state managers for this SCR###.
- Extract specific: file paths with line ranges, component names, prop names, API call sites.
- If you cannot read a file, note it under `## Unresolved Questions`.

**Import Discovery Rule:** After reading the page/view file, collect all non-vendor component imports (JS/TS: `./` or `@/`; Python templates: `{% include %}`/`{% extends %}`; Ruby: `render partial:`/`require_relative`; PHP/Blade: `@include`/`@component`/`@extends`; generic: include/import/require patterns). For each imported component file:
1. Grep for async/form signals — JS/TS: `useQuery|useMutation|axios|\$fetch|api\.|useForm`; htmx: `hx-get|hx-post`; generic: `\.get(\|\.post(\|fetch(\|validate\|rules` *(omit Vue-only `emit\(` and `v-model` — too broad)*
2. If matched AND file > 20 lines → read lines containing the matched pattern ±30 lines of context
3. Document behavior-relevant findings under the appropriate section (UI States, Validation, Interaction Patterns)
4. If file cannot be read: add to `## Unresolved Questions` as `(not read — referenced by import)`

**Depth:** 1 level only (page imports → components; do NOT follow component-to-component imports).

**Exception — file-exchange server actions:** when a §B Server-side action endpoint is file-producing/consuming (path/handler contains `export|import|download|upload`, or Content-Type is multipart/file), follow the backend handler (controller → job/service, bounded to that chain) far enough to identify the file schema. Cross-reference the feature's `BL-### File Schema` rather than re-deriving the column list (DRY). If the file-generation code cannot be reached within the controller→service chain, escalate under `## Unresolved Questions` — never silently omit.

## Extraction Signatures

### 4.0 User Flow

**Scope:** Within-screen interactions only. Cross-screen navigation (router transitions to other SCR###) is documented in `screen-flow.md` — NOT here.

**Source signals — happy path:**
- Primary CTA handler (button onClick / form onSubmit / link click) and what UI state it produces on this screen
- Step controllers: `currentStep`, `wizardStep`, `step` state variable; conditional render gated on step value (stays on same screen)
- Inline state transitions: `setIsEditing(true)` → form replaces read-only view; `showConfirm` → confirmation panel appears
- Async submission feedback: spinner → success toast → form reset (all observable on this screen)

**Source signals — branches:**
- Validation early-exit before submit (returns without API call)
- Conditional render based on form state: error inline vs. success panel
- Permission gates that swap visible region (e.g., admin sees extra panel)
- Empty/error/loading state branches (cross-ref UI States section — but mention the user-visible branch here)

**Exclude:**
- `router.push(...)` / `navigate(...)` / `Inertia.visit(...)` to a different route → belongs in screen-flow.md
- Cross-screen redirects on success → mention as terminal step (e.g., "submit → redirect to {SCR###}"), do NOT detail the next screen

**[WARN_ADVISORY]:** If `screen-flow.md` is already loaded in context, spot-check that User Flow terminal steps align with navigation events in screen-flow.md. This is advisory only — do NOT load screen-flow.md solely for this check.

**Format:**
- Happy Path: numbered prose steps. Each step = ONE observable user action OR ONE system response visible on this screen.
- Branches: table with Decision point | Condition | Outcome on this screen | Source.

**Stack-specific signals:**
- JS/TS (Vue/React): `useState`, `ref()`, `reactive()`, `currentStep`, event handlers on root template
- Python templates (Django/Jinja): form POST → re-render with errors; `{% if form.errors %}` branches
- Rails/PHP: form `action` POST → controller re-renders same view with `@errors` / `$errors`
- htmx: `hx-post` returning partial → swap target; `hx-trigger` chains

**N/A:** `N/A — single-action screen, no branches` — valid only when screen has exactly 1 CTA AND no `currentStep`/`isEditing`/conditional render based on form state.

**[UNVERIFIED]:** Use when a branch outcome is inferred (e.g., toast text not readable from source).

### 4.1 Screen Layout (+ Layout Regions sub-table)

**Prose paragraph (required, 2–4 sentences):** Read page/view file root template/JSX. Name major regions (header, sidebar, main content, modals/drawers). Note fixed/sticky/scrollable positioning; responsive breakpoint signals (CSS class names, `useBreakpoint`, media queries). Cite layout root file:line in trailing parenthetical.

**ASCII sketch (required):**

After the prose paragraph, draw top-level regions as ASCII boxes under `### Layout Sketch`:
- Label each box: `R{N}: {Name} ({position})` — e.g., `R1: Top Nav (fixed-top)`
- Region IDs (R1, R2, …) MUST match the Layout Regions table that follows
- Use dashed lines (`- - -`) for conditionally visible regions (e.g., sidebar that collapses on mobile)
- Use nested boxes for floating/overlapping regions (modals, drawers, toast stack)
- Width/height proportions approximate — pixel-perfect not required
- Minimum 2 boxes (one per region in Layout Regions table)
- Read root container CSS class names to infer the flex/grid axis (row vs. column splits)

**Stack notes for sketch:**
- Tailwind: `flex flex-row` → horizontal split; `flex flex-col` → vertical stack; `fixed inset-0` → full-screen overlay
- CSS Grid: `grid-template-areas` directly maps to region layout
- SSR/templates: read outer `<div>` / `<section>` class names + partial structure

**Layout Regions sub-table (required, ≥2 rows):**

Extract one row per top-level region. For each region:
- **Region ID:** sequential R1, R2, R3, … (stable within this spec only)
- **Name:** human label (Top Nav, Sidebar, Main Content, Footer Toolbar, Modal Stack)
- **Position:** `fixed-top` | `sticky` | `static` | `absolute` (read from CSS/utility classes — Tailwind `fixed top-0`, Bootstrap `sticky-top`, plain CSS `position: fixed`)
- **Scrollable:** `yes` | `no` (read from `overflow-y-auto`, `overflow-scroll`, or container with explicit height + overflow)
- **Key Components:** comma-separated component names imported and rendered in this region (use the Import Discovery Rule output — already collected)
- **Responsive Behavior:** breakpoint visibility (`hidden md:block`, `lg:flex`), drawer collapse (`hamburger-sm`), or fluid behavior (`max-w-7xl`, `w-full`)

**Stack notes:**
- SSR/template (Django/Rails/Blade): `Key Components` may be partial names (`_sidebar.html.erb`, `@include('partials.nav')`, `{% include "header.html" %}`) or CSS class selectors when partials are not used
- htmx-driven: regions with `hx-target` are independent scroll/swap units — flag in Responsive Behavior column

**N/A:** NOT allowed. Layout is always documentable. If page imports a layout wrapper not readable, write `[UNVERIFIED]` row + escalate as Unresolved Question.

Cite layout root file:line in parent prose's trailing parenthetical. Per-region citations optional unless a region maps to a non-obvious file (different partial).

### 4.2 UI States

Scan page/view file and immediate dependencies for async signals:

- Loading: `isLoading`, `loading`, skeleton components, `Suspense`, spinner
- Empty: `isEmpty`, `data.length === 0`, empty-state components, zero-results branches
- Error: `isError`, `error !== null`, error boundary, catch blocks in data hooks
- Success: toast calls, `showSuccess`, confirmation components, mutation success handlers
- Custom: any named state not covered above (`isDraft`, `isPending`, etc.)

**Depth rule:** Scan for async calls by frontend paradigm — SPA (Vue/React/Angular): `axios|fetch|useQuery|useMutation|asyncData|\$fetch|API\.|api\.`; htmx-driven: `hx-get|hx-post|hx-patch|hx-delete|hx-trigger`; Turbo (Rails): `data-turbo-stream`; generic: `\.get(\|\.post(\|\.put(\|\.delete(` — produce ≥1 error row per distinct async endpoint + ≥1 empty row per data-displaying region. For each state: record trigger, visual component, user actions, source file:line.

**N/A:** `N/A — no async ops` — valid only when grep returns zero async matches AND screen renders no list/data block.

### 4.3 Validation & Error Feedback

**Sub-table A — Client-side:**
Scan for client-side validation (runs in browser — backend validation rules belong in Feature Spec, not here) — JS/TS: `useForm`, `Formik`, `react-hook-form`, `vee-validate`, `VueUseForm`, Zod/Yup/Joi; all stacks: HTML5 `required`/`pattern`/`min`/`max`; generic: `validate|rules|constraints`. For each field: name, type, required, constraints, async check endpoint, error message string.

**N/A (A):** `N/A — no client-side form validation detected.`

**Section B — Server-side (per-action blocks):**

Signature: action handler containing `await {api}.{method}(...)` combined with `.catch` / try-catch / `.then(err => ...)` that surfaces a user-visible error (toast, banner, inline message).

For each action, produce one block:
- **Endpoint:** HTTP method + path (from `axios`/`$fetch`/`api.` call site)
- **Request:** field names the UI sends (from call argument object; skip auth headers). If payload is assembled in a composable beyond Import Discovery depth, write `[UNVERIFIED] — payload assembled outside 1-level read depth; see Unresolved Questions`.
- **Success:** HTTP code + outcome visible to user (redirect URL, toast text, state change)
- **Errors:** HTTP code(s) + user-visible message text. Use `[UNVERIFIED]` when message is server-driven and not readable from source.

**Server-side escalation (before [UNVERIFIED]):** if an error message is server-driven, first locate and read the endpoint's backend validator class (FormRequest / request-validator / serializer / DTO). If read → extract the real message (no `[UNVERIFIED]`). Only if the class cannot be found or read may you write `[UNVERIFIED]`, and you MUST add a matching `## Unresolved Questions` entry naming the endpoint + the validator path you could not reach. (stack: Laravel `app/Http/Requests/*Request.php`; Rails strong params / `validates` in model; DRF serializer `*Serializer`; NestJS DTO `class-validator` decorators; Zod/Yup schema on the route handler — non-exhaustive.)

*Cross-ref: `verification-checklist-screen-spec.md` row 25 covers documentation presence for server-side-only validation rules — a related but distinct concern from the escalation-attempt requirement above.*

- **Trigger:** gesture that fires the action (button click, form submit, keyboard shortcut)
- **Source:** file:line of the action handler

For file-producing/consuming endpoints (see Import Discovery Rule exception above), add a line `File schema: see BL-### File Schema (behavior-logic.md)` instead of restating columns.

**N/A (B):** `N/A — no submit-style action handlers detected.`

### 4.4 Interaction Patterns

Extract non-trivial patterns: optimistic update, infinite scroll, drag-drop, debounced search, keyboard shortcut.

**Format MUST be behavior-first:** `**{User behavior — observable outcome}** — source: {file:line}`

Implementation details (handler name, store action) may appear in trailing parenthetical — NEVER first.

- REJECT: "Root `div` has `@click='resetTarget'` which calls `store.dispatch(...)`..."
- ACCEPT: "Clicking outside any group deselects it — source: questions.vue:2"

Researcher MUST reformulate any handler-first extraction before writing.

**N/A:** `N/A — no non-trivial interaction patterns detected (only standard form input bindings).`

### 4.5 Accessibility

Always produce the 4-row table (Aspect | Status | Notes). Bare `N/A — no ARIA attributes detected` is BANNED at section level.

Per-row scan signatures:
- **ARIA roles/labels:** `aria-\w+|role=` across component files
- **Keyboard navigation:** explicit `keydown|keyup|keypress|tabindex` handlers
- **Focus management:** `\.focus\(\)|focus-trap|useFocus|autofocus`
- **Screen reader:** `<label>` linkage, semantic landmarks (`role="main"`, `role="dialog"`)

When all 4 status cells are absent/unmanaged/unknown, append:
`[NO_A11Y_DETECTED] — accessibility audit needed before production release.`

### 4.6 Conditional Rendering

Scan for runtime gates by type:

- **auth:** `hasRole`, `currentUser.role`, `can(`, `ability.can`, `isAdmin`, permission-based visibility
- **feature-flag:** `useFlag`, `useFeature`, `isEnabled`, `featureFlag(`, `checkFlag`
- **responsive:** CSS-in-JS breakpoint checks, `useMediaQuery`, `useBreakpoint`, Tailwind responsive classes controlling visibility
- **legacy:** condition that compares against a string constant name (e.g., `status === 'LEGACY_MODE'`) with no feature-flag API
- **hardcoded-id:** condition that compares a route param, entity ID, or field value against a numeric/string literal (e.g., `Number($route.params.form) === 458`)

**Notes column rules:**
- `auth` type → Notes MUST state: "Consequence if bypassed: {redirect / 403 / data exposure}". If consequence cannot be determined from source, write `[UNVERIFIED] consequence — needs security review`.
- `hardcoded-id` or `legacy` type → Notes MUST contain: `[NEEDS_DOMAIN_CONFIRMATION] — {description of what this gate does}; unknown whether legacy bug, feature flag, or intentional design`
- `feature-flag` / `responsive` → Notes optional

**N/A:** `N/A — no conditional rendering detected.`

### 4.7 Component Variants (optional)

**Trigger:** component imported on this screen also appears in ≥2 other screens in ScreenList AND renders ≥2 visual variants based on a discriminating field.

Scan: component file's render switch (`v-if`, switch statement, ternary chain) keyed off a prop value.

Output: screen-specific props/slots only. Reference DISC-### in data-model.md OR feature-spec § Polymorphic Behavior for variant business rules. DO NOT re-document the component's universal behavior.

**Omit section entirely when criteria not met** — this is the only optional section.

### 4.8 Source References

- Minimum 1 entry: the page/view file
- List every file actually read while extracting (not aspirational paths)
- If a file should exist but could not be found, log under Unresolved Questions — never fabricate

### 4.9 Security Surface

**Trigger:** Populate when Conditional Rendering has ≥1 `auth`-type row OR a route guard / navigation guard is found in the router config for this screen's route.

**Scan for:**
- Route-level guards (find router/routes config, check this screen's route entry): JS/TS: `src/router/index.{js,ts}` — grep `beforeEnter|meta\.requiresAuth|meta\.roles|router\.beforeEach`; Python: grep `@login_required|LoginRequiredMixin` in views/urls; Rails: grep `before_action :authenticate` in controllers; PHP: grep `->middleware('auth')` in route files; generic: grep `auth|guard|middleware` on route entries
- Component-level guards (auth conditional gating component render): JS/TS: `v-if="isAuthenticated"`, `can('action','resource')`; Python: `{% if user.is_authenticated %}`; Rails: `if current_user.admin?`; PHP: `@auth`/`@can` Blade directives; generic: conditional block keyed on auth/permission check
- Data-access guards: API calls that return 403 when unauthorized (document the permission boundary)

**For each guard, record:**
- Guard expression or middleware name
- Type: `auth` (login required) | `permission` (role/ability check) | `role` (specific role required)
- Consequence if bypassed: what a non-authorized user would see or access. If not determinable from static analysis, write `[UNVERIFIED] server enforcement — static analysis cannot confirm API middleware`.

**N/A:** `N/A — no auth guards or permission checks detected on this screen.`
Valid only when: Conditional Rendering has zero `auth`-type rows AND router config has no guard for this route.

### 4.10 Data Inventory

**Scope:** UI-displayed fields only. Document what the user sees. Type/nullable/server constraints belong in `entities.md` — reference, do not copy.

**Source signals — bindings:**
- JS/TS (Vue): `{{ field }}`, `v-text="field"`, `:value="field"`, `v-model="field"` (templates)
- JS/TS (React/JSX): `{field}`, `value={field}`, `{user.name}`, `{data?.email}`
- Python (Django/Jinja): `{{ field }}`, `{{ object.field }}`, `{{ user.name }}`
- Rails ERB: `<%= field %>`, `<%= @user.name %>`
- PHP/Blade: `{{ $field }}`, `{!! $field !!}`, `{{ $user->name }}`
- htmx: `hx-vals` payload (sent fields) + response template's bindings (displayed fields)

**Source signals — computed:**
- JS/TS: `computed(() => ...)`, `useMemo(...)`, getter functions
- Template-level: `{{ user.firstName + " " + user.lastName }}`, `{{ price | currency }}`

**Per-field extraction:**
- **Field:** the binding name as it appears in source (e.g., `user.email`, `order.totalCents`, `formData.title`)
- **Display Label:** the visible label text (read adjacent `<label>` tag, table `<th>` header, or aria-label)
- **Source:** one of:
  - `API field` — comes from API response (cite endpoint or response shape)
  - `route param` — `$route.params.X`, `useParams().X`, controller route binding
  - `store state` — Vuex/Pinia/Redux/store reference
  - `computed` — derived from other fields (cite derivation file:line in trailing parenthetical)
- **Format:** how the field is rendered (date format like `YYYY-MM-DD`, currency symbol, truncation `…`, raw string)
- **Empty Behavior:** what user sees when field is null/empty/undefined (`—`, `Not set`, hidden, fallback text)
- **Cross-ref:** `MODEL###.field` if the field maps to a documented entity attribute; `N/A` for transient UI-only fields (form state)

**Cap:** Max 20 primary fields per screen. For dense screens (data tables with many columns), group repetitive patterns as one row with `{field_1..N}` notation + note in trailing comment.

**Do NOT include:**
- **Editable form input fields** — those belong in `## Validation & Error Feedback`. Skip any field with a corresponding `<input>`, `<textarea>`, `<select>`, or equivalent writable binding.
- DB constraints (NOT NULL, FK, unique) — that's data-model.md territory
- Server-side validation rules — that's Feature Spec
- Fields that exist in API response but are NOT rendered to user
- Layout/styling fields (`className`, `style`)

**N/A:** `N/A — screen displays no dynamic data (static marketing/error page)` — valid only after scanning source confirms zero bindings/interpolations.

**[UNVERIFIED]:** Use for format inferred from binding name without confirmed formatter call. Example: `[UNVERIFIED] currency format — needs runtime confirmation`.

### 4.11 Source Walkthrough (A3, v26.0.0)

**Scope:** UI-layer only, mirroring §4.8 — this screen's own files, not the owning feature's
server-side files (those belong in the feature's `technical-spec.md` § Source Walkthrough).

Ordered reading list covering the files in §4.8 Source References (data model cross-ref →
entry point → view → interaction logic), 1 file per step, with a 1-sentence "why start here."
Cite each entry with `**File:**` (NOT `**Source:**` — keeps this navigational list out of the
A1 confidence-report citation-coverage stat; see `references/confidence-report-contract.md` §
A3 navigational entries). Followed by a `### Call Hierarchy` diagram (ASCII or Mermaid: page/view
→ component → store/hook) and a pointer line: "see `## Source References` above" — do NOT
author a second, independent file list (F15 DRY; §4.8's list is numbered/ordered already).

**MANDATORY — no N/A fallback.** Every screen has source to walk through (at minimum the
page/view file from §4.8).

**Gated by:** `scripts/validate_reading_guide_db_impact.py` (dedicated validator, WARN-first
`*.pre_migration` degradation contract — screen-spec has no other Python structural validator
today).

## N/A Fallback Master Rule

Researcher MUST scan source file + immediate imports before writing any N/A. N/A is valid only after confirming absence — not as a default. At least one section MUST be populated (all-N/A = reviewer warning).

| Section | Exact N/A string |
|---------|-----------------|
| Purpose | N/A — not allowed; write [UNVERIFIED] if unclear |
| User Flow | `N/A — single-action screen, no branches` |
| Screen Layout | N/A — not allowed; escalate as Unresolved Question |
| Layout Regions (sub-table) | N/A — not allowed; minimum 2 rows required |
| Data Inventory | `N/A — screen displays no dynamic data (static marketing/error page)` |
| UI States | `N/A — no async ops` |
| Validation A (client) | `N/A — no client-side form validation detected.` |
| Validation B (server) | `N/A — no submit-style action handlers detected.` |
| Interaction Patterns | `N/A — no non-trivial interaction patterns detected (only standard form input bindings).` |
| Accessibility | No section-level N/A; always write 4-row table |
| Conditional Rendering | `N/A — no conditional rendering detected.` |
| Component Variants | Omit section entirely |
| Security Surface | `N/A — no auth guards or permission checks detected on this screen.` |
| Source Walkthrough (A3) | N/A — not allowed; every screen has source to walk through |

## [UNVERIFIED] Marker Protocol

Use `[UNVERIFIED]` when a value is observable only at runtime and cannot be confirmed from source alone.

**Format:** `[UNVERIFIED] {best-effort description} — needs runtime confirmation`

**Example:** `[UNVERIFIED] "Email already registered" toast — needs runtime confirmation`

- Distinct from **N/A** — N/A means "scanned, confirmed absent"; [UNVERIFIED] means "likely present, not confirmable from static analysis"
- Distinct from **fabrication** — fabrication is banned; [UNVERIFIED] is a tracked best-effort with explicit caveat
- Use for: exact server error message text, toast duration, animation timing, backend-driven content
- For server-side error messages, `[UNVERIFIED]` is valid ONLY after attempting to read the backend FormRequest/validator class (see §4.3 Section B escalation). Unattempted → reviewer warning.

**Canonical trailing phrase variants:**
- `— needs runtime confirmation` — use when value is observable at runtime (toast text, animation timing)
- `— needs domain confirmation` — use when value requires domain expert input (purpose, business intent)

## [NEEDS_DOMAIN_CONFIRMATION] Marker Protocol

Use `[NEEDS_DOMAIN_CONFIRMATION]` when a condition's intent cannot be determined from static analysis alone and requires domain expert input.

**When to use:** Conditional Rendering rows where `type` is `hardcoded-id` or `legacy`.

**Canonical format:** `[NEEDS_DOMAIN_CONFIRMATION] — {what this gate does}; unknown whether legacy bug, feature flag, or intentional design`

**Example:** `[NEEDS_DOMAIN_CONFIRMATION] — hides form for form ID 458; unknown whether legacy bug, feature flag, or intentional design`

- Distinct from `[UNVERIFIED]` — [UNVERIFIED] means "likely present but unconfirmable from source"; [NEEDS_DOMAIN_CONFIRMATION] means "present and confirmed, but purpose is unknown"
- Always include a description of what the gate does — never write bare `[NEEDS_DOMAIN_CONFIRMATION]`

## SHARED_COMPONENT Extraction Rule

A component is SHARED when it appears in ≥2 screens in ScreenList.

For shared components on this screen, document ONLY:
- Props this screen passes to the component
- Slot content this screen injects
- Events this screen handles from the component

DO NOT re-document the component's universal behavior. Defer to:
- DataModel DISC-### entry (for discriminator-driven variants)
- Feature spec § Polymorphic Behavior (for cross-feature variant logic)

## H6 Shell Screen Protocol

**Trigger:** Screen tagged `[H6]` in screen-list.md, OR screen file's primary template contains a router outlet (`<nuxt-child>`, `<router-view>`, `<Outlet>`, `<router-outlet>`) with ≥2 child routes in route config.

**Problem this solves:** H6 shell files have minimal logic (persistent nav + outlet). Standard extraction produces: Screen Layout = nav component only, all other sections = N/A. The spec must communicate orchestration purpose and child route structure.

### 1. Purpose
Write as navigation orchestration — not feature description:
> "{Persona} navigates between {child screen names} via the {nav component name}. The {nav} persists across all child routes while content in the main region updates per active route."

### 2. Screen Layout
- **R1 (persistent UI):** Name the component, describe behavior (static/data-driven), note scroll axis (horizontal/vertical), note if data-driven (then add loading row to UI States). Cite file:line.
- **R2 (outlet):** Write exactly: "R2: child outlet — delegates rendering to [{SCR###a} / {SCR###b}] per active route. No direct content rendered here."

### 3. Child Routes (MANDATORY for H6 shells)
Add `## Child Routes` section in the spec (placed between `## Screen Layout` and `## User Flow`). Read route config to enumerate:

| Route | SCR | URL | Notes |
|-------|-----|-----|-------|
| {label visible in nav} | SCR###a | /path/a | {one-line child purpose} |

**Route config locations by stack:**
- Nuxt 2: infer from `pages/` directory structure (subdirectory = child route)
- Vue Router: `src/router/index.{js,ts}` or `routes.ts` — `children:` array under parent route
- React Router v6: `react-router-dom` route config — `<Outlet>` parent children
- Angular: `RouterModule.forChild` children array

### 4. UI States
- Shell-level only. DO NOT document child screen states here.
- If persistent nav loads data asynchronously → add loading/error row for it.
- If persistent nav is fully static → `N/A — no async ops` is valid (no scan of child files required).

### 5. Interaction Patterns
Navigation actions qualify as non-trivial interaction patterns:
- `**Clicking a {circle/tab/step} in the {nav name} navigates to {SCR###} at {URL}** — source: {file:line}`
- Include keyboard navigation if the nav supports it.

### 6. Validation & Error Feedback
`N/A` for both A and B is expected — shell screens have no forms. Do not scan child files to fill this.

### 7. Source References
Always include:
- Shell layout file
- Route config file (where child routes are defined)

### Shell vs Child Boundary (CRITICAL)
Shell spec documents: persistent UI + navigation patterns + child route enumeration.
Shell spec does NOT include: forms, data tables, modals, or async calls specific to child screens.
Reviewer flags child-screen content in shell spec as scope violation.

## H6 Child Screen Context

**Trigger:** Screen is a child route inside an H6 shell (parent shell SCR### tagged `[H6]` in screen-list.md AND this screen's route is in parent's Child Routes table).

**Protocol:**

1. **Screen Layout** — Open with one sentence: "Renders inside [parent SCR###_Name] shell at the child outlet (R2). The shell's persistent [nav component] is always visible." Then document this screen's own content (form fields, data table, etc.) — DO NOT re-describe the parent's persistent nav.

2. **Source References** — Add the parent shell file as a context reference (not as the primary source): `Parent shell context: {parent-layout-file}:{line}`.

3. **Navigation entry/exit** — Document only the screen's own navigation triggers (submit, next-step button). Timeline-click navigation belongs in the parent shell spec, not here.

4. **Scope** — Child screen spec documents the screen's own forms/data/interactions in full. The shell's persistent nav is referenced, not re-documented.

**Reviewer rule:** Child spec MUST NOT contain a full description of the shell's Timeline/sidebar/header — only a one-line context reference. Full re-documentation → warning.

## Output Path

Draft: `plans/<active-plan>/artifacts/screens/{SCR###_Name}/spec.md`

<!-- layout-exempt: rebuild-spec promote target for ScreenSpec — definitional output path, mode-resolved at runtime -->
Final (promoted by Wave SS.3): `docs/screens/{SCR###_Name}/spec.md`

### Confidence Companion (advisory sidecar)

`confidence-report_spec.md` is NOT part of the researcher's output above. It is emitted
automatically by `scripts/derive_confidence_report.py` (a deterministic script, not authored
by the researcher) after `spec.md` is promoted — a citation-coverage sidecar, never gated,
never asserted. See `references/confidence-report-contract.md` for the full derivation rules
and the A1 correctness-verification boundary.

## Task Closure

Call `TaskUpdate(status=completed)` on this task BEFORE returning.
