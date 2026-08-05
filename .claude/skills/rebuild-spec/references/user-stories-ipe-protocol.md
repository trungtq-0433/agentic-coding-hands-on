# User Stories — Interaction Point Enumeration (IPE) Protocol

Loaded by Wave 4 researcher. Run ALL steps BEFORE writing any US###.

## Step 1 — Enumerate interaction points per screen

For each SCR### in ScreenList, scan the screen's source file. List ALL interactive elements:

| Category | Examples |
|----------|---------|
| CTA buttons | Create, Save, Submit, Export, Import, Download, Upload, Send, Approve, Reject |
| Modal/dialog triggers | any btn that opens a modal, dialog, drawer, or bottom sheet |
| Inline row actions | Edit, Delete, View, Clone, Archive, Toggle, Status-change per row |
| Bulk actions | checkbox + bulk Delete/Export/Assign operations |
| Destructive actions | Delete, Remove, Revoke, Deactivate — **ALWAYS** a separate US |
| Form submissions | distinct submit paths with different endpoints |
| Filter/Search panels | complex filter panels with own state + API call |
| Navigation actions | user-initiated link-outs (not passive routing) |

### Step 1 (stack-aware) — interaction vocabulary per `screen_source`

The table above is the **route-view (web)** vocabulary — use it unchanged for web stacks. For other
screen sources, enumerate the stack's native interactive controls instead (a `.dfm` form has no DOM):

| `screen_source` | Where interactions live | Interactive controls to enumerate |
|-----------------|-------------------------|-----------------------------------|
| `route-view` (web) | the view/component source file | the categories in the table above (DOM CTAs, modals, row actions, …) |
| `dfm-form` (Delphi/VCL) | the `.dfm` layout + its paired `.pas` unit | `TButton`, `TBitBtn`, `TSpeedButton`, `TMenuItem`, `TAction`/`TActionList` items, popup-menu items — each paired with its `On*` event handler (`OnClick`, `OnExecute`) in the `.pas`. Each control+handler = one interaction point; cite the handler `file:line`. |

A `dfm-form` control with no wired `On*` handler is inert decoration — do NOT count it as an interaction.

## Step 2 — Write Interaction Inventory table

Fill the **Interaction Inventory** table in `user-stories-template.md` BEFORE writing any US.
One row per interactive element: `Screen | Element | Type | Action | Endpoint`.

**Interaction types:**
- `primary-action` — main CTA on screen (Create, Save, Submit)
- `secondary-action` — supporting action (Export, Filter, View Detail)
- `destructive-action` — irreversible (Delete, Remove, Revoke, Deactivate)
- `navigation` — user-initiated screen transition (not passive routing)
- `system-action` — triggers background/async work (Import, Sync, Send notification)

## Step 3 — One US per interaction (default rule)

Each distinct interaction → its own US###.

The **merge exception** is per-stack — pick the block matching the profile's `screen_source`. The
all-3-must-hold structure is identical across stacks; only condition (b) is stack-specific. Conditions
(a) and (c) never change.

**Merge exception — `route-view` (web)** — combine into one US ONLY when ALL 3 hold:
- (a) same actor/role
- (b) same HTTP endpoint (method + path identical)
- (c) same data flow (no conditional branching between the interactions)

If ANY condition fails → separate US.

**Merge exception — `dfm-form` (Delphi/VCL)** — combine into one US ONLY when ALL 3 hold:
- (a) same actor/role
- (b) **same event-handler procedure** (both controls invoke the SAME `On*` proc — e.g. two buttons
  wired to one shared `OnClick`, or two menu items on one `TAction.OnExecute`). **NOT** "same table" —
  same-table is far too coarse (every button touching one DB table would vacuously merge → drastic
  over-merge, the 86-vs-354 failure mode). A desktop app has no HTTP endpoint, so endpoint identity is
  inapplicable; handler identity is its faithful analogue.
- (c) same data flow (no conditional branching between the interactions)

If ANY condition fails → separate US.

### Step 3 (dfm-form only) — materiality filter + form-variant dedup

These two reductions apply ONLY to `dfm-form` (Delphi/VCL) enumeration. They keep the US count in the
realistic band (the audit's ~150–250 for a 440-form repo) instead of either starving (86) or
1:1-exploding (354). Web (`route-view`) US generation is UNAFFECTED — skip this step for web.

**(i) Materiality filter** — drop non-material form FAMILIES from US enumeration, identified by name
prefix. Conservative default = exactly these 5 prefixes:

| Prefix | Family (excluded) |
|--------|-------------------|
| `FPrt` | print / report-preview forms |
| `FSel` | selector / picker dialogs |
| `FDlg` | generic dialogs |
| `FSub` | subordinate / embedded helper forms |
| `FCal` | calendar / date-picker popups |

Reuse the scout File-Inventory tags from the `.dfm` classification (Phase 02) to identify form names;
do NOT re-scan source. Emit ONE log line recording what was filtered — never silent truncation:
`[IPE_MATERIALITY] excluded N forms by prefix: FPrt(x), FSel(y), FDlg(z), FSub(a), FCal(b)`.
Borderline/ambiguous helpers (e.g. `FCtrlm`) stay **material** (the threshold is the audit's open
question — err toward inclusion).

**(ii) Form-variant dedup** — collapse same-base-name numeric/suffix variants into ONE US:
`FHotelm` + `FHotelm2` → one; `FTkyo` + `FTkyo1` + `FTkyo2` → one; `FSnamm` + `FSnamm2` → one.
Heuristic: identical base name with a trailing digit/short suffix. Record the merge in the US Notes:
`[IPE_VARIANT_MERGE] FTkyo ← FTkyo1, FTkyo2`.

### Step 3 (oracle-plsql / headless) — system-action US, not screen US

A stack with `screen_source: none` (oracle-plsql, generic) has no ScreenList, so IPE Step 1 has no
screen anchors. Its user-reachable logic — PL/SQL procedures, functions, triggers invoked on a user's
behalf, and DataModule-hosted `TAction`/report logic flagged `[reachable]` by the scout — surfaces as
**`system-action` US authored into behavior-logic / feature-list**, NOT screen-list. Each such US cites
the defining `file:line`. This is how a headless backend still yields user stories without fabricating
a screen artifact. **Exception (Phase 09, Track D):** a `none`-profile repo is not investigated further
by default — UNLESS a Tier-2 content-sniff surfaces cited, structurally-corroborated evidence AND the
user accepts it, in which case `screen_source` becomes `"ui-sniff"` for that run and Step 1 resumes
with the sparse, all-`[UNVERIFIED]` ScreenList `_ui_sniff_accept_lib` produced.

## Step 4 — Anti-CRUD naming

US title MUST contain exactly ONE action verb.

| Bad (reject) | Good (accept) |
|-------------|--------------|
| "Manage Users" | "Create User", "Edit User Profile", "Delete User Account" |
| "User CRUD" | one US per verb |
| "Create/Edit User" | split into 2 separate US |
| "User Management" | name the specific action |

Template: `As a {ROLE}, I want to {SINGLE-VERB} {object} so that {benefit}.`

## Step 5 — Minimum threshold check

- Screen with N interactions documented → expect **≥N US** (unless merge exception in Step 3 applies)
- Screen with 0 interactions found → emit `[IPE_ZERO]` in US### Notes, flag for researcher review
- At end of artifact, add **Screen→US Map**: `SCR### → US001, US002, US003`
