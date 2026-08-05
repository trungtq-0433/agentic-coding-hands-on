# Permissions Matrix

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

> **Raw PERM### matrix.** Machine-generated inventory of every permission item with full
> per-permission detail. The plain-language curated view lives at
> [permissions.md](../system/permissions.md). Write THIS file FIRST, then derive the curated
> view from it.

**Code Format**: All codes MUST follow `PERM###_NameSlug` format (e.g., PERM001_ViewReports, PERM002_EditUsers)

**Permission Types**:
- `route-guard` - Route-level authorization middleware
- `screen-permission` - UI element visibility/enabled rules
- `action-permission` - Button/action execution rules
- `data-permission` - Field-level access control
- `role-based` - Role-based access control rules
- `resource-ownership` - Owner/resource relationship checks
- `field-permission` - Column/field visibility rules
- `api-scope` - API scope/token permission
- `feature-flag` - Runtime-evaluated flag from a feature flag service or config
- `experiment` - A/B test variant assignment gate
- `env-gate` - Hardcoded check against an environment variable (fixed at deploy time)
- `locale-gate` - UI branch conditioned on the active locale or language setting

**source field** (required for `feature-flag`, `experiment`, `env-gate`, `locale-gate` types only):
- **`source:`** — file:line where the gate is referenced (traceability anchor)

**Note**: Feature mapping is managed in FeatureList.md. This document contains permission items without direct feature references.

## Permissions Index

| Code | Name | Type | Enforced At |
|------|------|------|-------------|
| {PERM001_CODE} | {PERM001_NAME} | {TYPE} | {ENFORCED_AT} |
| {PERM002_CODE} | {PERM002_NAME} | {TYPE} | {ENFORCED_AT} |
| {PERM003_CODE} | {PERM003_NAME} | {TYPE} | {ENFORCED_AT} |

---

## {PERM001_CODE}: {PERM001_NAME}

**Type**: {TYPE}
**Enforced At**: {ENFORCED_AT}

### Description

{DESCRIPTION}

### Related Routes

- ({ROUTE_METHOD}) {ROUTE_PATH}

### Related Screens

- {SCREEN_CODE | SCR###/REG###} - {SCREEN_NAME}

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| {ROLE_1} | {✓/✗} | {CONDITIONS} |
| {ROLE_2} | {✓/✗} | - |

### Related Modules

- {MODULE_1}
- {MODULE_2}

---

## {PERM002_CODE}: {PERM002_NAME}

**Type**: {TYPE}
**Enforced At**: {ENFORCED_AT}

### Description

{DESCRIPTION}

### Related Routes

- ({ROUTE_METHOD}) {ROUTE_PATH}

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| {ROLE_1} | {✓/✗} | {CONDITIONS} |

### Related Modules

- {MODULE_1}

---

## {PERM003_CODE}: {PERM003_NAME}

**Type**: {TYPE}
**Enforced At**: {ENFORCED_AT}

### Description

{DESCRIPTION}

### Related Screens

- {SCREEN_CODE} - {SCREEN_NAME}

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| {ROLE_1} | {✓/✗} | {CONDITIONS} |

---

## Summary

- **Total Permission Items**: {TOTAL_PERMISSIONS}
- **By Type**: route-guard: {N}, screen-permission: {N}, action-permission: {N}, data-permission: {N}, role-based: {N}, resource-ownership: {N}, field-permission: {N}, api-scope: {N}, feature-flag: {N}, experiment: {N}, env-gate: {N}, locale-gate: {N}

---

## Cross-Reference Validation

- [x] All PERM### codes are unique
- [ ] All PERM### codes are referenced in FeatureList.md (verified in Step 8)
- [x] All related route references are valid (RT### in RouteList)
- [x] All related screen references are valid (SCR### or SCR###/REG### in ScreenList; PERM### may target a region (SCR###/REG###) for region-scoped auth gating (e.g., admin-only sidebar) — UI hiding only; server enforcement required)
- [x] All related module references are valid
- [x] No orphaned permission references

---

## Client-Side Gate Types

The four types below (`feature-flag`, `experiment`, `env-gate`, `locale-gate`) are client-side gates — they control rendering or behavior without involving server-side role/permission checks. They share the same PERM### code format but require a `source:` field for traceability.

### feature-flag

A runtime-evaluated flag looked up from a feature flag service or config at request/render time. The value can change without a deploy. Capture the flag name only; do not link to any external service dashboard.

```markdown
### PERM-042 — `enable-new-checkout`
**type:** feature-flag
**trigger:** checked when user navigates to `/checkout`
**source:** `src/routes/checkout.tsx:23` (`useFlag('enable-new-checkout')`)
**effect:** `true` → renders `<CheckoutV2/>`; `false` → renders `<CheckoutV1/>`
```

### experiment

An A/B test variant assignment gate. Capture the experiment name and variant identifiers found in code; do not query the test platform.

```markdown
### PERM-043 — `checkout-cta-copy`
**type:** experiment
**trigger:** evaluated on checkout page mount
**source:** `src/features/checkout/CheckoutPage.tsx:45` (`useExperiment('checkout-cta-copy')`)
**effect:** variant `control` → "Complete Purchase"; variant `treatment` → "Buy Now"
```

### env-gate

A hardcoded check against an environment variable (`NODE_ENV`, `APP_ENV`, `RAILS_ENV`, etc.). The value is fixed at deploy time, not runtime.

```markdown
### PERM-044 — production analytics gate
**type:** env-gate
**trigger:** app bootstrap
**source:** `src/lib/analytics.ts:12` (`if (process.env.NODE_ENV === 'production')`)
**effect:** analytics tracking enabled only in production; skipped in dev/test
```

### locale-gate

A UI branch conditioned on the active locale or language setting.

```markdown
### PERM-045 — JP-only payment methods
**type:** locale-gate
**trigger:** payment methods list render
**source:** `src/features/checkout/PaymentMethods.tsx:88` (`if (locale === 'ja-JP')`)
**effect:** shows Konbini payment option only when locale is `ja-JP`
```

---

## Extraction Signatures

Use these patterns to locate client-side gates in source code. All signatures match function/method names only — do not hard-code library names.

### feature-flag
Match function calls: `useFlag|useFeature|isEnabled|featureFlag\(|checkFlag`
Capture: first string argument (the flag name). Skip if no string literal arg present.

### experiment
Match function calls: `useExperiment|getVariant|abTest\(|experiment\.variant|useAbTest`
Capture: first string argument (experiment name) + all variant string values found nearby.

### env-gate
Match comparisons against: `process\.env\.|import\.meta\.env\.|ENV\[|os\.environ\[`
followed by `===`, `==`, `!==`, `in (...)`, or conditional block.
Capture: env var name + compared value.

### locale-gate
Match comparisons against: `i18n\.locale|currentLocale|getLocale\(\)|locale\s*===|lang\s*===`
Capture: locale/language value being compared.

---

<!--
=============================================================================
APPENDIX — WORKED EXAMPLE (Reference Only; DELETE THIS HTML-COMMENT BLOCK
BEFORE SUBMITTING REAL PERMISSIONS. Fabricated codes used here —
PERM004, SCR001/REG002_MetricsPanel — must NOT appear in the generated output.)
=============================================================================

**Region-scoped PERM example**: `PERM004` targets `SCR001/REG002_MetricsPanel` (role: admin; hides region for non-admin). Server-side enforcement must not rely solely on UI hiding.

=============================================================================
-->
