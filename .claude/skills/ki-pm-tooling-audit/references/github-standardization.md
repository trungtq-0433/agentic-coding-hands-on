# GitHub Project standardization

Use this reference to explain the setup/practice split. KPI Insight MCP is the
source of truth for the current result.

## Tier A — setup

### A1–A8 project configuration

Check the server-returned checklist for:

- Status field.
- Sprint/iteration field.
- Estimate field.
- Spent-time field.
- Required closed-status options.
- Story Point field.
- Priority/start/due-date fields.
- Linked repository and label-to-tracker mapping.

### A9–A10 labels

Use `get_github_label_compliance`. Render the returned label state and missing
requirements. Common server states include:

- `fully_standard`
- `partial_standard`
- `non_standard`

Do not reproduce or run the server's label-mapping implementation. This skill
grades; it never creates or renames labels.

## Tier B — runtime practice

Use `get_github_project_hygiene` for each requested month. The response can
cover assignment, sprint, status, estimates, spent time, stale work, reopen
signals, and label usage.

Read a multi-month sequence as:

- improving;
- flat;
- declining;
- not measurable.

Use server-returned `compliant`, `score_pct`, and checklist values. Do not apply
a separate hard-coded scoring band.

If `total_issues = 0`, the month is not measurable. It is not a failure.

## Prioritization

Prioritize missing requirements by downstream KPI impact:

1. Missing estimate/spent/sprint/status data that blocks measurement.
2. Missing tracker mapping that misclassifies work.
3. Practice gaps that distort a measured month.
4. Cosmetic naming differences.

Name the gap and affected measurement. Do not claim that a proposed change has
already been applied.
