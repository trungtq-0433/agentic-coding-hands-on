# User Stories

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

**Code Format**: All US codes MUST follow `US###_NameSlug` format (e.g., US001_Login, US002_ViewDashboard)

**US Types**:
- `ui` - User-facing stories (require Screen mapping)
- `system` - System stories: hook, event, observer, bg-job, trigger, etc. (no Screen mapping needed)

**Note**: Feature mapping is managed in FeatureList.md only. This document contains user stories without direct feature references. UI US require Screen mapping; system/bg-job US do not. `ui`-typed stories may map to `SCR###` or `SCR###/REG###`; non-`ui` types map to `SCR###` only (or omit).

## Interaction Inventory

> Complete this table BEFORE writing any US. One row per interactive element per screen.
> Source of truth for US count — every row maps to ≥1 US below (unless merge exception applies).
> See: references/user-stories-ipe-protocol.md for enumeration rules and merge exception.

| Screen | Element | Type | Action | Endpoint |
|--------|---------|------|--------|---------|
| {SCR###_Name} | {Button/Modal/InlineAction/BulkAction/Form} | {primary-action\|secondary-action\|destructive-action\|navigation\|system-action} | {what happens when triggered} | {METHOD /path or N/A} |

## User Story Index

| Code | Title | Type | Priority | Screens |
|------|-------|------|----------|---------|
| {US001_CODE} | {US001_TITLE} | {TYPE} | {PRIORITY} | {US001_SCREENS} |
| {US002_CODE} | {US002_TITLE} | {TYPE} | {PRIORITY} | {US002_SCREENS} |
| {US003_CODE} | {US003_TITLE} | {TYPE} | {PRIORITY} | {US003_SCREENS} |

---

{POPULATED_BY_FRAGMENTS}

## {US001_CODE}: {US001_TITLE}

**Type**: {TYPE}
**Interaction**: {primary-action|secondary-action|destructive-action|navigation|system-action}
**Priority**: {PRIORITY}
**Estimate**: {ESTIMATE}

### User Story

> Title must use ONE action verb. Anti-CRUD: "manage", "CRUD", compound "create/edit" are invalid.

As a {ROLE}, I want to {SINGLE-ACTION-VERB} {object} so that {BENEFIT}.

### Acceptance Criteria

- [ ] Criterion 1: {CRITERION_1}
- [ ] Criterion 2: {CRITERION_2}
- [ ] Criterion 3: {CRITERION_3}

### Technical Notes

- **Endpoint**: {ENDPOINT}
- **Data Required**: {DATA_REQUIRED}
- **Dependencies**: {DEPENDENCIES}

### Screens

- {SCR### | SCR###/REG###}: {SCR001_NAME}
- {SCR### | SCR###/REG###}: {SCR002_NAME}

### Background Logic

- {BL001_CODE}: {BL001_NAME}
- {BL002_CODE}: {BL002_NAME}

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | {GIVEN} | {WHEN} | {THEN} |
| Error Case | {GIVEN_ERROR} | {WHEN_ERROR} | {THEN_ERROR} |

---

## {US002_CODE}: {US002_TITLE}

**Type**: {TYPE}
**Interaction**: {primary-action|secondary-action|destructive-action|navigation|system-action}
**Priority**: {PRIORITY}
**Estimate**: {ESTIMATE}

### User Story

As a {ROLE}, I want to {SINGLE-ACTION-VERB} {object} so that {BENEFIT}.

### Acceptance Criteria

- [ ] Criterion 1: {CRITERION_1}
- [ ] Criterion 2: {CRITERION_2}

### Technical Notes

- **Endpoint**: {ENDPOINT}
- **Data Required**: {DATA_REQUIRED}
- **Dependencies**: {DEPENDENCIES}

### Screens

- {SCR### | SCR###/REG###}: {SCR001_NAME}

---

## {US003_CODE}: {US003_TITLE}

**Type**: {TYPE}
**Interaction**: {primary-action|secondary-action|destructive-action|navigation|system-action}
**Priority**: {PRIORITY}
**Estimate**: {ESTIMATE}

### User Story

As a {ROLE}, I want to {SINGLE-ACTION-VERB} {object} so that {BENEFIT}.

### Acceptance Criteria

- [ ] Criterion 1: {CRITERION_1}

### Technical Notes

- **Endpoint**: {ENDPOINT}
- **Data Required**: {DATA_REQUIRED}
- **Dependencies**: {DEPENDENCIES}

### Screens

- {SCR### | SCR###/REG###}: {SCR001_NAME}
- {SCR### | SCR###/REG###}: {SCR003_NAME}

---

## Screen → US Map

| Screen | US Codes |
|--------|---------|
| {SCR###_Name} | US001, US002, US003 |
| {SCR###_Name} | US004 |

> Screens with 0 US mapped → emit `[IPE_ZERO]` warning.

## Cross-Reference Validation

- [x] All US### codes are unique
- [x] All acceptance criteria are testable
- [x] All technical notes are complete
- [x] All US### codes are referenced in FeatureList.md
- [x] All `ui` US### mapped to SCR### or SCR###/REG### (parent SCR must exist in ScreenList; system US excluded)
- [x] All system US### have at least one BL### mapped (UI US excluded)