# GitHub Project audit checks

Load this reference when rendering detailed A/B checklists.

## MCP tools

| Tool | Purpose |
|---|---|
| `get_github_project_standardization` | A1–A8 project configuration |
| `get_github_label_compliance` | A9–A10 label set and mapping |
| `get_github_project_hygiene` | Monthly runtime practice |

The tools are deployed on the current KPI Insight MCP. Still check availability
for older environments.

## Detailed flow

### 1. Resolve

- Require `rubato_project_id`.
- Default trend window to three complete months.
- A non-GitHub source is out of scope, not non-compliant.

### 2. Fetch Tier A

Call standardization and label compliance once. Preserve:

- checklist item identifier;
- pass/applicable state;
- expected/actual field when returned;
- `missing_required`;
- label status and mapping recommendations.

Do not reduce the result to a percentage only.

### 3. Fetch Tier B

Call hygiene once for each month in the selected window. Preserve:

- `total_issues`;
- `compliant`;
- `score_pct`;
- individual rule results;
- source caveats.

Do not average monthly averages into a new canonical score. Describe the
sequence or use raw totals only when the response supplies a valid denominator.

### 4. Present

```text
<project> · GitHub Project audit · <N months>
Setup: <summary>
Missing required: <items or none>
Labels: <server state>
Practice trend: <improving|flat|declining|not measurable>
Priorities: <up to three gaps and downstream KPI impact>
```

## Failure handling

| Situation | Action |
|---|---|
| Required tool absent | Report capability unavailable and stop that tier |
| `forbidden` | Report insufficient project scope and stop |
| `project_not_found` | Ask the user to verify `rubato_project_id` |
| Non-GitHub source | Report out of scope |
| GitHub unavailable | Report upstream availability; do not use `gh` as fallback |
| `total_issues = 0` | Render `No measurable issues` |
| Rule value null | Render `No data`; exclude it from any client-side count |
