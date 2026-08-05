# Screen List

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

**Code Format**: All codes MUST follow `SCR###_NameSlug` format (e.g., SCR001_LoginForm, SCR002_Dashboard) | `SCR###/REG###` for region-scoped references within a composite screen

**Note**: Feature mapping is managed in FeatureList.md only. UserStory mapping is done in UserStories.md (not in this document).

**Region Guidance**: Declare a Region only when it has ≥1 independence signal: distinct API endpoint (read or write), independent loading state, independent scroll container, independent auth / permission gate, distinct business workflow, distinct mutation surface / API cluster (distinct write endpoints or POST/PUT/DELETE namespace — even if the initial GET payload is shared), or distinct validation / action path. Shared initial payload does NOT disqualify a REG — if regions diverge on mutations, validation, or business workflow, they remain separate. Visual separation alone is NOT sufficient (trap 1).

**Region Cross-ref**: Region codes are per-screen; REG001 under SCR001 is distinct from REG001 under SCR002.

**REG Numbering**: Assign REG001, REG002, ... in top-to-bottom visual order as rendered at the screen's default viewport (desktop default if responsive). Ties broken by left-to-right reading order. Researcher documents source file:line for each REG to allow reviewer verification.

**Region Deprecation**: Regions table MAY include a `status` column with values `active` | `deprecated`. Deprecated regions keep their REG### number reserved (no renumbering); downstream refs remain valid; reviewer emits WARNING (not critical) until spec-wide cleanup.

<!-- ANTI-COMPRESSION RULE: One SCR per distinct view/page file. Do NOT collapse a namespace or
     wildcard route (e.g. /admin/system/*) into a single composite SCR. ≥2 view files under one
     namespace/route prefix → emit one SCR per file (apply H6). A wildcard route as a single SCR
     is FORBIDDEN — expand to concrete child routes from RouteList first.
     See: composite-screen-detection.md § Composite Hard Guard -->

<!-- STACK-AWARE SECTIONS (v21.0.0) — keyed on the profile's `screen_source`:
     • route-view (web): author EVERY section below exactly as shown (unchanged behavior).
     • dfm-form (Delphi/VCL desktop): screens are .dfm TForm units, NOT routed views. Therefore:
         - OMIT the `### Routes/URLs` section from every SCR block (a desktop form has no URL).
           Replace it with `### Invocation` listing how the form is reached, from the
           form-nav digest (_digest_extract_form_nav.json):
             ### Invocation
             - Invoked by: {CALLER_FORM/UNIT} via {Show|ShowModal|CreateForm} — `{file}:{line}`
             - Reachability: static | [UNVERIFIED] (no static inbound edge — dynamic/RTTI or dead)
         - In the Components table, `Type` is the VCL control class (TButton, TDBGrid, TEdit, …).
         - In Cross-Reference Validation, the "route URLs properly formatted" check is N/A — replace
           with "All invocation edges cite file:line".
         - Every SCR row + every Invocation edge MUST cite `file:line` (RE contract).
     A form with no proven static inbound edge is still listed, marked `[UNVERIFIED]` — never dropped.
     This is ONE template with conditional sections — do NOT fork a parallel desktop template. -->
## Screen Index

| Code | Name | Type | Components | Data Displayed |
|------|------|------|------------|----------------|
| {SCR001_CODE} | {SCR001_NAME} | {TYPE} | {COUNT} | {DATA_COUNT} |
| {SCR002_CODE} | {SCR002_NAME} | {TYPE} | {COUNT} | {DATA_COUNT} |
| {SCR003_CODE} | {SCR003_NAME} | {TYPE} | {COUNT} | {DATA_COUNT} |

---

{POPULATED_BY_FRAGMENTS}

## {SCR001_CODE}: {SCR001_NAME}

**Type**: {TYPE}

### Description

{DESCRIPTION}

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| {COMPONENT_1} | {TYPE} | {PURPOSE} |
| {COMPONENT_2} | {TYPE} | {PURPOSE} |

### Data Displayed

- Data Entity 1: {ENTITY}
- Data Entity 2: {ENTITY}

### Routes/URLs

- {URL_1}
- {URL_2}

### Related Screens

- {SCR002_CODE}: {SCR002_NAME} (navigation)
- {SCR003_CODE}: {SCR003_NAME} (parent)

### Regions (composite screens only; omit for atomic)

| Code | Label | Owner | Independence Signals |
|------|-------|-------|---------------------|
| REG001 | {REGION_1_LABEL} | {F###_FeatureCode} | {SIGNAL_1} |
| REG002 | {REGION_2_LABEL} | {F###_FeatureCode} | {SIGNAL_2} |

---

## {SCR002_CODE}: {SCR002_NAME}

**Type**: {TYPE}

### Description

{DESCRIPTION}

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| {COMPONENT_1} | {TYPE} | {PURPOSE} |

### Data Displayed

- Data Entity 1: {ENTITY}

### Routes/URLs

- {URL_1}

### Related Screens

- {SCR001_CODE}: {SCR001_NAME} (parent)

---

## {SCR003_CODE}: {SCR003_NAME}

**Type**: {TYPE}

### Description

{DESCRIPTION}

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| {COMPONENT_1} | {TYPE} | {PURPOSE} |

### Data Displayed

- Data Entity 1: {ENTITY}

### Routes/URLs

- {URL_1}

### Related Screens

- {SCR001_CODE}: {SCR001_NAME} (navigation)

---

## SCR001_AdminDashboard (composite — dashboard)

**Type**: composite

### Description

Admin dashboard with independently-loaded user and metrics panels.

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| UserPanel | panel | Displays user list from `/api/users` |
| MetricsPanel | panel | Displays metrics data from `/api/metrics` |

### Data Displayed

- Data Entity 1: User records
- Data Entity 2: Metrics aggregates

### Routes/URLs

- `/admin/dashboard`

### Related Screens

- SCR007_MetricDetail: MetricDetail (drill-down from MetricsPanel)

### Regions

| Code | Label | Owner | Independence Signals |
|------|-------|-------|---------------------|
| REG001 | UserPanel | F003_UserManagement | own endpoint `/api/users`; own loading state |
| REG002 | MetricsPanel | F004_MetricsReporting | own endpoint `/api/metrics`; independently scrollable |
| REG003 | NotificationBanner | F007_NotificationCenter | independent endpoint `/api/notifications`; own loading state |
| REG004 | QuickActions | F008_QuickActions | shared bootstrap GET `/api/dashboard`; distinct mutation surface `POST /api/actions/*`; distinct validation |

---

## SCR002_MetricsPanel (composite — independent metrics region)

**Type**: composite

### Description

Metrics panel component with independent data loading and scroll behavior. Often used as a region within larger dashboard screens.

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| MetricsGrid | grid | Displays metrics cards |
| FilterBar | bar | Filters metrics by date range |

### Data Displayed

- Data Entity 1: Metrics aggregates
- Data Entity 2: Trend data

### Routes/URLs

- `/api/metrics`

### Related Screens

- SCR001_AdminDashboard: AdminDashboard (may appear as region)

### Regions

| Code | Label | Owner | Independence Signals |
|------|-------|-------|---------------------|
| REG001 | SidebarAlerts | F007_NotificationCenter | independent endpoint `/api/alerts`; own loading state |

---

## SCR005_OnboardingWizard (composite — wizard, H5 Case B)

**Type**: composite

### Description

Multi-step onboarding wizard. Steps share a single submit endpoint (`/api/onboarding/submit` on final step) — classifies as Case B per H5: composite SCR with step REGs. Case A (distinct endpoints per step) would require cited source evidence per D6b.

### Components

| Component | Type | Purpose |
|-----------|------|---------|
| StepIndicator | nav | Shows progress through steps |
| StepContent | container | Renders active step region |

### Data Displayed

- Data Entity 1: Account info (step 1)
- Data Entity 2: User preferences (step 2)
- Data Entity 3: Confirmation summary (step 3)

### Routes/URLs

- `/onboarding`

### Related Screens

- SCR001_AdminDashboard: AdminDashboard (post-onboarding redirect)

### Regions

| Code | Label | Owner | Independence Signals |
|------|-------|-------|---------------------|
| REG001 | Step1_AccountInfo | F010_Onboarding | client-state only; shared endpoint /api/onboarding/submit on final step |
| REG002 | Step2_Preferences | F010_Onboarding | client-state only; shared endpoint /api/onboarding/submit on final step |
| REG003 | Step3_Confirmation | F010_Onboarding | client-state only; shared endpoint /api/onboarding/submit on final step |

> Note: wizard-step regions share parent wizard state; all steps write to a single `/api/onboarding/submit` endpoint on final step (source file:line citation required for Case B classification).

---

## Summary

- **Total Screens**: {TOTAL_SCREENS}

---

## Cross-Reference Validation

- [x] All SCR### codes are unique
- [x] All SCR### codes are referenced in ScreenFlow.md
- [x] All related screen references are valid
- [x] All route URLs are properly formatted  <!-- route-view only; dfm-form: replace with "All invocation edges cite file:line" -->
- [x] All SCR### codes are referenced in FeatureList.md
- [x] No orphaned screen references
