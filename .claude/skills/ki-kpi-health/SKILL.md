---
name: tkm:ki-kpi-health
description: "Read KPI Insight delivery health for a project, SDM portfolio, or division. Use this when checking project health, sprint status, KPI overview, burndown, team MM/capacity, milestones/releases, integration/sync status, SDM monthly health, or division health. Use KPI Insight MCP only."
argument-hint: "[project-id | --sdm <me|email|uuid> | --division <code>] [--period <value>] [--burndown|--team-effort|--milestones|--integration] [--html]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["project health", "KPI health", "dự án đang khỏe", "sprint health", "burndown", "team MM", "team capacity", "milestones", "integration status", "SDM portfolio", "division health"]
---

# KPI Insight Health

Read delivery health at the caller's altitude without expanding the request into
unrelated reports.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).
Before interpreting KPIs, read
[`skills/_shared/extras/kpi-insight/kpi-insight-kpi-reference.md`](../_shared/extras/kpi-insight/kpi-insight-kpi-reference.md).

## Rules

- Stay read-only and use KPI Insight MCP only.
- Treat server value, status, threshold, band, direction, and freshness as
  canonical.
- Lead with quality flags. Mark affected KPIs unmeasured; do not rank them
  against clean data.
- Stop a forbidden scope. Never reconstruct it from another response.
- Write a file only when `--html` is explicit.
- Describe team effort as aggregate capacity shape, never individual
  performance or productivity.

### Mandatory evidence gate

Run this gate before drafting the verdict or "Needs attention":

- Mark a numeric claim **Measured** only when its own response supplies the
  scope, period, and operands needed for the interpretation.
- For `planned=0` and `completed=0`, write:
  `Burndown: Unmeasured (0/0); no delivery conclusion.`
- For a zero KPI without supporting counts, write:
  `Server status: <status>; causal interpretation unavailable.`
- Do not turn zero/absent operands into "zero issue closure", "no issues
  closed", "no work completed", "no code changes", "no defects", or an
  equivalent causal claim.
- Preserve the server lifecycle status. Never call an `ended` sprint active,
  open, in-flight, or incomplete.
- If the evidence cannot pass this gate, make data insufficiency the verdict;
  do not list the unsupported operational claim under "Needs attention".

### Runtime model requirement

Health verdicts and multi-source synthesis are release-validated on Opus. On a
smaller model, return source-labeled raw facts and data caveats only; do not
issue a health verdict. Ask the caller to rerun on Opus for interpretation.

## Resolve scope and intent

Ask once if no project, SDM, or division scope can be resolved.

| Scope/intent | Call |
|---|---|
| Project snapshot | `get_project_health` |
| One KPI needs brief context | `get_kpi_status` |
| Sprint burndown | `get_sprint_burndown` |
| Team capacity/MM | `get_team_effort` |
| Releases/milestones | `get_project_milestones` |
| Tracker/source/sync | `get_project_integration_status` |
| SDM projects | `get_sdm_projects` |
| SDM monthly roll-up | `get_sdm_monthly_report` |
| Division monthly roll-up | `get_center_monthly_report` |
| Explicit raw monthly detail | `get_admin_report_raw_data` |

Use only the calls required by the user's intent. A default project request
calls `get_project_health`; it does not automatically fetch burndown, effort,
milestones, and integration.

### Period defaults

- Project: use `period=last_sprint`. Call it completed only if the response
  confirms completion.
- SDM/division: use the previous complete month.
- Custom project window: supply `period=custom` plus `date_from` and `date_to`.
- State the resolved period once at the top.

### Identity and role

- `--sdm me`: call `get_sdm_projects` without an identity selector.
- Named SDM: pass the explicit email/UUID; let the server enforce role.
- Division: require division, month, and year.
- Zero projects is a valid answer. Do not widen the query.

## Fetch and interpret

### Project snapshot

Call:

```text
get_project_health {
  rubato_project_id,
  period,
  date_from?,
  date_to?
}
```

Use `get_kpi_status` only for a KPI worth one short explanation. Route a request
for ticket-level causes to `tkm:ki-kpi-drilldown`.

Report:

1. Measurement trust and source freshness.
2. Overall verdict from measured KPIs.
3. Up to three items needing attention.
4. What remains healthy/measured.

Do not call a one-sprint movement a trend. Require multiple comparable periods.

### Cross-source consistency gate

Keep each tool response in a separate evidence lane identified by tool, scope,
period, and stable IDs such as `sprint_id`, milestone ID, or source ID. A shared
display name such as "Sprint 24" does not prove that two responses cover the
same window.

Before reporting any issue count, ratio, or percentage:

1. Cite the originating tool and period.
2. Verify that numerator, denominator, and percentage come from that same
   evidence lane.
3. Treat an absent, zero, or null denominator as unmeasured. Do not derive a
   percentage or describe delivery success/failure from `0/0`.
4. If stable IDs differ, are missing, or cannot be linked explicitly by the
   server, report the values separately. Never combine burndown totals with
   milestone issue counts.
5. If two lanes conflict, name the inconsistency as a data caveat. Do not
   reconcile, average, or select one silently.

Never translate a KPI value of zero into "zero issues", "no work completed",
"no source changes", or "no defects" unless that same response provides the
supporting count or denominator. Quote a server status such as `critical`, but
do not invent its operational cause. An absent `quality_flags` field is
unknown, not "none".

### Burndown

Call `get_sprint_burndown { rubato_project_id, sprint_id? }`.

- Preserve server dates and scope.
- If no daily data exists, report that explicitly.
- Do not fabricate an ideal line or derive it from closed-issue ratio.

### Team effort

Call:

```text
get_team_effort {
  rubato_project_id,
  month?,
  year?,
  trailing_months?
}
```

Report total MM, headcount, job-type allocation, and available trend. Do not:

- name/infer members;
- rate a job type containing one person;
- use MM as a proxy for value or productivity.

### Milestones

Call `get_project_milestones { rubato_project_id, period? }`. Separate:

- upcoming;
- overdue;
- completed;
- no milestone data.

Do not infer release risk without dates/status in the response.

### Integration

Call `get_project_integration_status { rubato_project_id }`. Report:

- active source/tracker;
- last successful sync;
- configuration or sync error;
- data freshness implications.

Do not debug through direct GitHub/DB access.

### Portfolio and division

Use roll-up tools first. Call `get_admin_report_raw_data` only when the caller
explicitly needs a field missing from the roll-up and their role permits it.

At SDM/division altitude, name projects and aggregate caveats. Do not dump
tickets, members, or every sprint.

## Output

Keep default chat under about 400 words:

```text
<scope> · <period>
Verdict: <one repeatable sentence>
Needs attention:
- <what, distance/status, project or sprint>
Measured and healthy: <one line>
Data caveats: <flags, freshness, missing periods>
```

For `--html`, load
[`references/html-report.md`](references/html-report.md), generate the local
report, then return its path. Keep the chat summary.

## Failure behavior

- Missing MCP/server/tool: follow the shared connection reference.
- Forbidden: name the blocked scope and stop it.
- Null value/threshold: show `No data`; do not use a static number.
- Empty burndown/milestones/projects: report a successful empty result.
