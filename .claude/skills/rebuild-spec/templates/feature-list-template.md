<!--
Wave 5 also emits plans/<active-plan>/artifacts/_canonical-fcodes.json
(canonical fcode + slug + related-code source for validators and FS.1 fan-out)
AND pre-creates plans/<active-plan>/artifacts/features/{slug}/ folders with
.pending markers. See references/canonical-fcode-schema.md.
-->

# Feature List

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Analysis Scope**: {SCOPE}

**Code Format**: All codes MUST follow `F###_NameSlug` format (e.g., F001_Auth, F002_UserProfile)
**Screen Code Format**: All screen codes MUST follow `SCR###_NameSlug` format (e.g., SCR001_LoginForm)
**User Story Code Format**: All US codes MUST follow `US###_NameSlug` format (e.g., US001_Login)
**Background Logic Code Format**: All BL codes MUST follow `BL###_NameSlug` format (e.g., BL001_ScheduledReport)
**Permission Code Format**: All PERM codes MUST follow `PERM###_NameSlug` format (e.g., PERM001_ViewReports)

**Feature Types**:
- `ui` - Feature has UI screens (SCR###)
- `background` - Feature only has background logic (BL###, no SCR###)
- `mixed` - Feature has both UI screens and background logic

**Related Screens column format**: Accepts `SCR###`, `SCR###/REG###`, or mixed comma-separated (e.g., `SCR001, SCR002/REG003`). Tokenizer splits on `,` then on `/`. No intra-screen shorthand (`SCR###/REG001+REG002` invalid) — enumerate each ref explicitly.

**Partial-screen ownership note**: A feature with only a `SCR###/REG###` ref owns the region, NOT the parent SCR. The screen shell (`SCR###`) must be owned by a separate F### with a bare `SCR###` ref (typically a layout/dashboard feature).

**Cross-reference**: See ScreenList Regions subsection for region definitions and the `REG###_NameSlug` registry.

## Feature Hierarchy

**Note**: Features are sorted by priority from highest to lowest (P0 → P1 → P2 → P3). Priority levels:
- **P0**: Core functionality, blocking issues, or essential features
- **P1**: High priority, significant features
- **P2**: Medium priority, standard features
- **P3**: Low priority, nice-to-have features

| Code | Name | Type | Language | Workspace | Priority |
|------|------|------|----------|-----------|----------|
| {F001_CODE} | {F001_NAME} | {TYPE} | {LANGUAGE} | {WORKSPACE} | {PRIORITY} |
| {F002_CODE} | {F002_NAME} | {TYPE} | {LANGUAGE} | {WORKSPACE} | {PRIORITY} |
| {F003_CODE} | {F003_NAME} | {TYPE} | {LANGUAGE} | {WORKSPACE} | {PRIORITY} |

## Feature Details

{POPULATED_BY_FRAGMENTS}

### {F001_CODE}: {F001_NAME}

**Type**: {TYPE}
**Description**: {DESCRIPTION}

**Workspace**: {WORKSPACE}
**Languages**: {LANGUAGES}
**Components**: {COMPONENT_COUNT}

**Related Screens**:
- {SCR001_CODE}: {SCR001_NAME}
- {SCR002_CODE}: {SCR002_NAME}

**Related User Stories**:
- {US001_CODE}: {US001_NAME}
- {US002_CODE}: {US002_NAME}

**Related APIs/Routes**:
- ({ROUTE001_METHOD}) {ROUTE001_PATH}
- ({ROUTE002_METHOD}) {ROUTE002_PATH}

**Related Data Models**:
- {MODEL001_ENTITY}
- {MODEL002_ENTITY}

**Related Background Logic**:
- {BL001_CODE}: {BL001_NAME}
- {BL002_CODE}: {BL002_NAME}

**Related Permissions**:
- {PERM001_CODE}: {PERM001_NAME}
- {PERM002_CODE}: {PERM002_NAME}

---

### {F002_CODE}: {F002_NAME}

**Type**: {TYPE}
**Description**: {DESCRIPTION}

**Workspace**: {WORKSPACE}
**Languages**: {LANGUAGES}
**Components**: {COMPONENT_COUNT}

**Related Screens**:
- {SCR003_CODE}: {SCR003_NAME}

**Related User Stories**:
- {US003_CODE}: {US003_NAME}

**Related APIs/Routes**:
- ({ROUTE003_METHOD}) {ROUTE003_PATH}

**Related Data Models**:
- {MODEL003_ENTITY}

**Related Background Logic**:
- {BL003_CODE}: {BL003_NAME}

**Related Permissions**:
- {PERM003_CODE}: {PERM003_NAME}

---

<!--
=============================================================================
APPENDIX — WORKED EXAMPLE (Reference Only; DELETE THIS HTML-COMMENT BLOCK
BEFORE SUBMITTING A REAL FEATURE LIST. Fabricated codes used here —
SCR001, SCR002, REG003 — must NOT appear in the generated output.)
=============================================================================

### F007_NotificationCenter

**Type**: ui
**Description**: Notification center spanning the top-bar region of the admin dashboard and the sidebar alert region of the metrics panel.

**Workspace**: {WORKSPACE}
**Languages**: {LANGUAGES}
**Components**: {COMPONENT_COUNT}

**Related Screens**:
- SCR001/REG003: NotificationBanner (composite screen; feature owns this region only — SCR001_AdminDashboard shell owned by separate layout feature)
- SCR002/REG001: SidebarAlerts (composite screen; feature owns this region only — SCR002 shell owned by separate layout feature)

**Related User Stories**:
- {US###_CODE}: {US###_NAME}

**Related APIs/Routes**:
- ({ROUTE_METHOD}) {ROUTE_PATH}

**Related Data Models**:
- {MODEL###_ENTITY}

**Related Background Logic**:
- {BL###_CODE}: {BL###_NAME}

**Related Permissions**:
- {PERM###_CODE}: {PERM###_NAME}

=============================================================================
-->

## Summary

- **Total Features**: {TOTAL_FEATURES}
- **Total Screens**: {TOTAL_SCREENS}
- **Total User Stories**: {TOTAL_USER_STORIES}
- **Total Routes**: {TOTAL_ROUTES}
- **Total Data Models**: {TOTAL_DATA_MODELS}
- **Total Background Logic**: {TOTAL_BACKGROUND_LOGIC}
- **Total Permissions**: {TOTAL_PERMISSIONS}
- **Languages Detected**: {LANGUAGES_LIST}

## Cross-Reference Validation

- [x] All F### codes are unique
- [x] All F### codes are referenced in UserStories.md
- [x] All screen references are valid (SCR### or SCR###/REG### in ScreenList; bare-SCR refs and region refs both accepted)
- [x] All user story references are valid (US### in UserStories)
- [x] All route references are valid (ROUTE### in RouteList)
- [x] All data model references are valid (MODEL### in DataModel)
- [x] All behavior logic references are valid (BL### in BehaviorLogic)
- [x] All permission references are valid (PERM### in Permissions)
- [x] Every US has a parent feature (F###)
- [x] Every screen has a parent feature (F###)
- [x] Every route maps to a feature (F###)
- [x] Every data model maps to a feature (F###)
- [x] Every background logic maps to a feature (F###)
- [x] Every permission maps to a feature (F###)
