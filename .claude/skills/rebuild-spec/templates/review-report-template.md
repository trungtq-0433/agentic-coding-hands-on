---
failed: 0
warnings: 0
missing: 0
result: PASS
---
<!--
`failed`: count of critical issues (0 = all pass).
`warnings`: count of warning issues.
`missing`: fcodes flagged MISSING due to `.pending` marker present in `artifacts/features/{slug}/` (verification-checklist-universal.md § Pending Marker Rule). Counts toward Wave 9 pre-flight gate halt conditions alongside `failed`.
`result`: PASS iff `failed === 0 && missing === 0`.
-->

# Review Report — Rebuild-Spec Artifacts

**Reviewer**: Staff Engineer (automated)
**Date**: {DATE}
**Scope**: All {N} core artifacts + {M} feature specs

---

## Summary

| Metric | Value |
|--------|-------|
| Artifacts reviewed | {N} core + {M} feature specs |
| Critical issues | {failed} |
| Warnings | {warnings} |
| Missing (`.pending` markers) | {missing} |
| Result | **{PASS\|FAIL}** |

---

## Critical Issues

<!-- List each critical issue as a subsection:
### C{N}: {Title} — {FIXED|OPEN}
- **Severity**: critical
- **Location**: `{artifact}:{line}`
- **Description**: ...
- **Fix**: ...

If none: write "_(none)_" -->

---

## Warnings

<!-- List each warning as a subsection:
### W{N}: {Title} — {FIXED|OPEN}
- **Severity**: warning
- **Location**: `{artifact}:{line}`
- **Description**: ...
- **Fix**: ...

If none: write "_(none)_" -->

---

## Passed Checks

<!-- Reviewer task closure: on successful write of this file, call
     TaskUpdate(status=completed) on your task id before returning. -->

Format: ONE LINE per passed rule per fcode. NO evidence prose. NO multi-line entries. NO grouping under headings.
Pattern: `✓ <rule_id> @ <fcode>` OR rolled-up: `✓ <rule_id> @ F###..F### (<N>/<N>)`.

Example:
✓ FeatureSpec.required_sections @ F001_Auth
✓ FeatureSpec.required_sections @ F002_Profile
✓ FeatureSpec.ccl_subsections @ F001_Auth..F030_Reports (30/30)

---

## Metrics

| Metric | Value |
|--------|-------|
| Feature Specs | {M} |
| User Stories | {US_COUNT} |
| Screens | {SCR_COUNT} |
| Background Logic Items | {BL_COUNT} |
| Permissions | {PERM_COUNT} |
| Backend Route Rows | {ROUTE_COUNT} |
| Frontend Pages | {PAGE_COUNT} |
| Data Model Entities | {ENTITY_COUNT} |
