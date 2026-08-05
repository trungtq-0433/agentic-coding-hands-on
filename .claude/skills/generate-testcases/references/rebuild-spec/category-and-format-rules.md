# Category And Format Rules

## Normalized Source Summary Shape

In whole-project mode, apply this file independently to each resolved feature during batch fan-out. Do not merge categories across different features into one suite.

For both create and update modes, build `source-summary.md` with these sections:

1. `Ticket Focus` when a ticket input exists
2. `Feature Overview`
3. `Screen And Route Inventory`
4. `Validation Rules`
5. `User Interactions`
6. `Functional / Business Rules`
7. `Database And Data-State Notes` when relevant
8. `Security And Access Considerations`

`Ticket Focus` should summarize only explicit ticket facts relevant to testcase generation:

- ticket issue statement
- ticket preconditions
- reproduction path
- actual result
- expected result
- regression or data-maintenance notes

`Database And Data-State Notes` should summarize only explicit persistence facts relevant to testcase generation:

- entities, tables, and relationships
- creation, update, delete, restore, hide, or sync rules
- soft-delete or hard-delete behavior
- validity, hidden, or lifecycle flags
- DB-side eligibility checks or data maintenance notes

Use this normalized shape even if the raw feature spec mixes acceptance scenarios, rules, edge cases, assumptions, and screen flow details together.

## ACCESSING Boundary

- Scope: access control, authentication, authorization, session requirements, direct access, redirect gates, and navigation entry paths only.
- Source sections: `Ticket Focus`, `Feature Overview`, `Screen And Route Inventory`, and `Security And Access Considerations` when relevant.
- Allowed category values:
  - `Check access permission`
  - `Check navigation path`
  - `Check authentication`
  - `Check session handling`
- Add rows only when the source is explicit.
- If the feature contains only authenticated screens, do not invent public direct-access cases.
- Do not include layout checks, input validation checks, or business interactions here.

## GUI Boundary

- Scope: screen inventory presence, appearance, visibility, placeholder text, default state, and explicit visual-state rules only.
- Allowed category values:
  - `Check layout`
  - `Initialize`
- Mandatory row:
  - `Check layout | Feature-wide screen inventory | Overall structure`
- Additional rows only when the source is explicit:
  - `Initialize | [Screen or Element] | Placeholder text`
  - `Initialize | [Screen or Element] | Default value/state`
  - `Check layout | [Screen] | Empty state`
  - `Check layout | [Screen] | Data-present state`
  - `Initialize | [Group] | Conditional visibility`
  - `Initialize | [Group] | Disabled boundary state`
- If the feature spans multiple screens, keep one feature-wide layout case unless the source names distinct screen-level UI rules that justify extra rows.
- If the ticket describes one broken visual state, add only the rows needed to cover that state and its explicit variants.
- Never create a GUI testcase per screen just because the feature references multiple screens.
- Never verify business correctness in GUI cases.

## FUNCTION Boundary

- Scope: validation, interactions, business logic, branching, state transitions, list behavior, cross-screen effects, navigation behavior, and explicit error handling.
- Source sections: `Ticket Focus`, `Validation Rules`, `User Interactions`, `Functional / Business Rules`, `Database And Data-State Notes`, plus behavior-scoped rules from `Security And Access Considerations`.
- Allowed category families:
  - `Check data validation`
  - `Check data persistence`
  - `Check component interaction`
  - `Check business logic`
  - `Check branching condition`
  - `Check state transition`
  - `Check list behavior`
  - `Check cross-component effect`
  - `Check cross-screen effect`
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
- `Accept`
- `Redirect`

### Validation Coverage Rule

For every explicit validation rule that survives category generation:

- create at least one valid testcase, and
- create at least one invalid or boundary testcase.

Do not collapse those two intents into one testcase.

### Ticket Coverage Rule

When a ticket input exists and it provides enough detail:

- add at least one reproduction testcase for the ticket scenario, and
- add at least one fix-validation or regression testcase for the explicit expected behavior.

Do not add ticket-driven rows when the ticket lacks explicit evidence for them.

### Database Coverage Rule

When the source indicates persistence or data-state behavior:

- actively look for DB-related specs within the allowlisted source set,
- add DB-focused testcase rows when the DB state is itself part of the behavior under test, and
- include concrete DB verification steps in the final testcase steps and expected results.

Concrete DB verification means naming the explicit entity, table, relationship, flag, or state transition when the source provides it. Avoid vague wording like `check DB`.

### DB Concreteness Threshold

- Good: `Verify users.status changes from pending to active`.
- Acceptable: `Verify a new user record exists in users`.
- Acceptable: `Confirm deleted_at is populated for the matched contract record`.
- Too vague: `Check DB updated correctly`.
- Too vague: `Verify data persisted`.

### Forbidden Unless Explicit

- Network/offline/timeouts
- Server-error families
- Rate limiting or anti-spam
- Background jobs not tied to the matched feature
- Performance thresholds
- Session concurrency rules beyond what the source states

## categories.md Contract

- `categories.md` must contain exactly three sections: `ACCESSING`, `GUI`, `FUNCTION`.
- Each section must use the table header `Category | Sub Category | Sub Sub Category`.
- Do not emit duplicate tuples.
- Do not let optional sibling docs add new behavior beyond what the matched feature spec supports.

## Markdown Testcase Table Contract

Use this exact column order in testcase markdown tables:

`TC_ID | Page_Name | Category | Sub_Category | Sub_Sub_Category | Test_Objective | Precondition | Test_Data | Steps | Expected_Result | Specs | Priority | Testcase_Type | Test_Result | Executed_Date | Tester | Note`

### Page_Name Rules

- If a testcase maps to exactly one explicit screen, use that screen name.
- If a testcase maps to one explicit `SCR###/REG###` region, use the region label.
- Otherwise use the feature name.

### Cell Rules

- `Expected_Result`: short phrase only, not a full sentence.
- `Steps`: numbered actions separated by `<br>`.
- When DB verification is required, include a distinct verification step that names the explicit persisted state to confirm.
- `Priority`: `High`, `Medium`, or `Low`.
- `Specs`: `Yes` only when the behavior is explicit in source.
- Leave `Test_Result`, `Executed_Date`, `Tester`, and `Note` empty.

### ID Rules

- Create mode:
  - `TC_[FEATURECODE]_ACC_###`
  - `TC_[FEATURECODE]_GUI_###`
  - `TC_[FEATURECODE]_FUN_###`
- Update mode:
  - Preserve existing IDs.
  - Allocate new IDs by incrementing the highest matching family already present in `base-testcases.md`.

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

Use `Data and Database Integrity Testing` whenever DB validation is the primary assertion.

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
   - auth/redirect/session/navigation gate -> `ACCESSING`
   - layout/screen inventory/placeholder/default/visual state -> `GUI`
   - rule execution, branching, persistence, or outcome validation -> `FUNCTION`
5. Keep the smallest testcase set that still preserves every source-backed intent.

### Final Ordering

- Section order: `ACCESSING`, `GUI`, `FUNCTION`
- Then `Category`, `Sub_Category`, `Sub_Sub_Category`
- In create mode, reassign final CSV IDs sequentially within each section after consolidation.
- In update mode, preserve existing IDs unless you must allocate new ones.