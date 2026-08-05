# Category And Format Rules

## Normalized Spec Shape

For create mode, build `specs.md` with these sections:

1. `Screen Overview`
2. `UI Elements`
3. `Validation Rules`
4. `User Interactions`
5. `Functional / Business Rules`
6. `Security Considerations`

Use this normalized shape even if the raw design description mixes business rules and security notes together.

## ACCESSING Boundary

- Scope: access control, authentication, authorization, direct access, and navigation entry paths only.
- Source sections: `Screen Overview` and `Security Considerations`.
- Allowed category values:
  - `Check access permission`
  - `Check navigation path`
  - `Check authentication`
- Add rows only when the source is explicit.
- If the current screen is modal-only, do not create direct URL access tests.
- Do not include layout checks, validation checks, or business interactions here.

## GUI Boundary

- Scope: appearance, visibility, placeholder text, default state, and explicit visual state rules only.
- Allowed category values:
  - `Check layout`
  - `Initialize`
- Mandatory row: `Check layout | Screen-wide layout | Overall structure`
- Additional rows only when the source is explicit:
  - `Initialize | [Element] | Placeholder text`
  - `Initialize | [Element] | Default value/state`
  - `Check layout | Empty state | No data`
  - `Check layout | Data-present state | With data`
  - `Check layout | Responsive | Breakpoints/layout reflow`
  - `Initialize | [Group] | Truncation`
  - `Initialize | [Group] | Max visible items`
  - `Initialize | [Group] | Conditional visibility`
  - `Initialize | [Group] | Disabled boundary state`
  - `Initialize | [Group] | Active/inactive styling`
  - `Initialize | [Group] | Hover tooltip/preview`
- Never create per-element layout rows such as `Check layout | [Element] | Visibility and position`.
- Never verify business correctness in GUI cases.

### Repeated Item Assertion Rule

If the source explicitly lists sub-elements inside a repeated card, row, list item, or tile, assert those sub-elements in one of these places only:

1. The single screen-wide layout testcase, or
2. One consolidated `Data-present state` testcase.

Do not split repeated-item presence into micro-cases.

### Enumerated Control Group Rule

If the source explicitly lists a finite set of toolbar or action-group controls, verify presence only in one of these places:

1. The single screen-wide layout testcase, or
2. One consolidated `Data-present state` testcase.

Do not create a separate GUI testcase per control.

## FUNCTION Boundary

- Scope: validation, interactions, business logic, branching, state transitions, list behavior, cross-component effects, navigation behavior, and explicit error handling.
- Source sections: `Validation Rules`, `User Interactions`, `Functional / Business Rules`, plus behavior-scoped rules from `Security Considerations`.
- Allowed category families:
  - `Check data validation`
  - `Check component interaction`
  - `Check business logic`
  - `Check branching condition`
  - `Check state transition`
  - `Check list behavior`
  - `Check cross-component effect`
  - `Check navigation behavior`
  - `Check error handling`
- Add rows only for behaviors explicitly present in the source.

### Validation Rule Names

Use the closest explicit rule label:

- `Required`
- `Min length`
- `Max length`
- `Format`
- `Allowed values`
- `Range/Boundary`
- `Cross-field dependency`
- `Uniqueness`
- `Nullable/Empty handling`

### Interaction Rule Names

Prefer the source verb. If the source is generic, use one of:

- `Open`
- `Close`
- `Submit`
- `Confirm`
- `Cancel`
- `Select`
- `Filter apply`
- `Copy`
- `Toggle`
- `Navigate`
- `Upload`
- `Download`
- `Search`
- `Expand/Collapse`

### Collection Rule Strategy

If a list, grid, menu, carousel, or other collection is described:

- Use per-item rows only when the source explicitly enumerates a finite set of item names or IDs.
- Use consolidated rows only when items are dynamic or data-driven.
- Never invent item names or counts.

### Validation Coverage Rule

For every explicit validation rule that survives category generation:

- create at least one valid testcase, and
- create at least one invalid or boundary testcase.

Do not collapse those two intents into one testcase.

### Forbidden Unless Explicit

- Network/offline/timeouts
- Server error families
- Spam/debounce/rate-limiting
- Gestures not described in source
- Session-expired behavior unless stated

## categories.md Contract

- `categories.md` must contain exactly three sections: `ACCESSING`, `GUI`, `FUNCTION`.
- Each section must use the table header `Category | Sub Category | Sub Sub Category`.
- Do not emit duplicate tuples.
- Viewpoints may refine names and completeness only; they may not add new behavior.

## Markdown Testcase Table Contract

Use this exact column order in testcase markdown tables:

`TC_ID | Page_Name | Category | Sub_Category | Sub_Sub_Category | Test_Objective | Precondition | Test_Data | Steps | Expected_Result | Specs | Priority | Testcase_Type | Test_Result | Executed_Date | Tester | Note`

### Cell Rules

- `Expected_Result`: short phrase only, not a full sentence.
- `Steps`: numbered actions separated by `<br>`.
- `Priority`: `High`, `Medium`, or `Low`.
- `Specs`: `Yes` only when the behavior is explicit in source.
- Leave `Test_Result`, `Executed_Date`, `Tester`, and `Note` empty.

### ID Rules

- Create mode:
  - `TC_[SCREEN]_ACC_###`
  - `TC_[SCREEN]_GUI_###`
  - `TC_[SCREEN]_FUN_###`
- Update mode:
  - Preserve existing IDs.
  - Allocate new IDs by incrementing the highest matching family already present in `base_testcases.md`.
  - When a new or changed validation rule appears, ensure both valid and invalid or boundary coverage exist after the update.

### Testcase_Type Rules

- ACCESSING rows: `Access control and security`
- GUI rows: `User interface`
- FUNCTION rows must use exactly one of:
  - `Normal_Billing`
  - `Normal_Login`
  - `Normal_Email`
  - `Normal_Others`
  - `Abnormal_Billing`
  - `Abnormal_Login`
  - `Abnormal_Email`
  - `Abnormal_Others`
  - `Data and Database Integrity Testing`
  - `Load Testing`
  - `Stress Testing`

## Final CSV Contract

### Header

Use this exact header once:

`Section,TC_ID,Page_Name,Category,Sub_Category,Sub_Sub_Category,Test_Objective,Precondition,Test_Data,Steps,Expected_Result,Specs,Priority,Testcase_Type,Test_Result,Executed_Date,Tester,Note`

### Encoding Rules

- First column must be `ACCESSING`, `GUI`, or `FUNCTION`.
- Replace `<br>` with actual newline characters inside CSV cells.
- Quote any multiline or comma-containing cell.
- Write blank fields as blank cells.

### Consolidation Rules

Use these rules whenever a mode requires deduplication or merge cleanup:

1. Normalize whitespace and obvious synonyms.
2. Canonicalize intent from section, category tuple, page name, objective, and expected result.
3. Deduplicate semantic duplicates by keeping the row that is:
   - explicit in source,
   - shorter and clearer,
   - less repetitive,
   - higher priority when still tied.
4. Resolve cross-section collisions with this precedence:
   - auth/redirect/navigation -> `ACCESSING`
   - layout/placeholder/default/visual state -> `GUI`
5. Keep the smallest testcase set that still preserves every source-backed intent.

### Final Ordering

- Section order: `ACCESSING`, `GUI`, `FUNCTION`
- Then `Category`, `Sub_Category`, `Sub_Sub_Category`
- In create mode, reassign final CSV IDs sequentially within each section after consolidation.
- In update mode, preserve existing IDs unless you must allocate new ones.