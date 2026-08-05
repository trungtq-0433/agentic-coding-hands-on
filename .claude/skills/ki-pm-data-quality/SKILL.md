---
name: tkm:ki-pm-data-quality
description: "Check whether KPI Insight data for a month is trustworthy before health or performance analysis. Use this when investigating data anomalies, missing or distorted KPI data, sync-quality questions, 'can I trust this month's numbers', or SDM/project-set data hygiene."
argument-hint: "--month <M> --year <YYYY> [--sdm <me|email|uuid> | --projects <ids>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["data anomalies", "data quality", "can I trust these numbers", "số liệu có đáng tin", "missing KPI data", "distorted KPI", "monthly data hygiene"]
---

# KPI Insight Data Quality

Check measurement trust before interpreting project performance.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and MCP-only.
- An anomaly is a measurement problem, not a performance failure.
- Never repair data or guess the value a source should have produced.
- Let the server enforce SDM/admin scope. Stop on forbidden.
- Do not rank projects whose measurement is blocked.

## Resolve

Require `month` and `year`. If absent, ask once and suggest the previous
complete month.

Support exactly one optional scope:

- own portfolio: no identity selector;
- named SDM: `sdm_email` or `sdm_user_id`;
- explicit projects: `rubato_project_ids`.

Do not combine selectors unless the user explicitly requests an intersection
and the current schema supports it.

## Fetch

```text
get_data_anomalies {
  month,
  year,
  sdm_email?,
  sdm_user_id?,
  rubato_project_ids?
}
```

Inspect the runtime schema before calling. If the current role cannot use the
requested selector, report forbidden and stop rather than widening to all
projects.

## Classify by consequence

Group returned anomalies by what they do to decisions:

| Class | Meaning | Reporting rule |
|---|---|---|
| Blocks measurement | Required source/date/estimate/sync data is absent | Name the project unmeasured and exclude it from ranking |
| Distorts measurement | Partial/duplicate/misaligned data skews a value | Show the value only with the caveat |
| Cosmetic | Optional mapping/naming drift does not change the metric | Note once; do not escalate |

Prefer consequence fields returned by the server. If the response does not
provide enough evidence to classify an item, label it `unclear impact` instead
of guessing.

## Produce action-oriented output

Keep chat under about 300 words:

```text
<scope> · <month/year>
Cannot measure: <projects and specific reasons>
Measured with distortion: <projects and reading caveat>
Cosmetic/unclear: <summary>
Clean: <count when the response supports it>
Source-side follow-up: <owner/action only when evidence identifies it>
```

Name the likely source owner only when the anomaly identifies the source:

- project planning fields → project/PL owner;
- tracker sync/integration → integration owner;
- unknown source → do not assign blame.

## Failure behavior

- Empty result: report no anomalies returned for the requested scope/period.
- Forbidden: report the requested scope is unavailable to the current role.
- Missing tool: report capability unavailable; do not infer anomalies from
  health reports.
- Null project/impact: retain the anomaly as unresolved metadata, not a clean
  result.
