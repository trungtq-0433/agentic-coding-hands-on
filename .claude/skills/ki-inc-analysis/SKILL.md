---
name: tkm:ki-inc-analysis
description: "Analyze KPI Insight incidents for one project, a project set, division, or company: counts, severity, MTTR/MTTD mean and median, detection source, trends, causes, open follow-up, and 5-why status. Use this when investigating incident analysis, outages, MTTR, MTTD, severe incidents, or incident trends."
argument-hint: "[project-id | --projects <ids> | --division <code> | --company] [--from <date> --to <date>] [--bucket week|month|quarter] [--date-field occurred_at|created_at|resolved_at] [--followup]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["incident analysis", "MTTR", "MTTD", "outage trend", "severe incidents", "5-why status", "incident follow-up", "phân tích sự cố"]
---

# KPI Insight Incident Analysis

Analyze incidents as system outcomes, never personal failures.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and MCP-only.
- Remain blameless; never name or infer an individual.
- Show free-text incident titles only in explicit one-project scope.
- At division/company scope, use aggregate/redacted output.
- Keep occurred, created, and resolved windows distinct.
- Treat cause fields as hints, not proven root causes.

## Resolve scope

Choose exactly one:

| Scope | Tool |
|---|---|
| One project | `get_project_incidents` |
| Explicit project set | `get_incident_analytics` |
| Division | `get_incident_analytics` |
| Company | `get_incident_analytics` |

Ask once when scope is ambiguous. Do not enumerate accessible projects to
simulate a division/company query.

## Project/raw mode

Call:

```text
get_project_incidents {
  rubato_project_id,
  period: {
    start,
    end,
    date_field
  }?
}
```

Choose `date_field` by the question:

- what happened → `occurred_at`;
- what was filed → `created_at`;
- what was closed → `resolved_at`.

Never mix fields silently.

### Row cap

One call can return at most 500 incidents. If the result indicates truncation
or the requested range is too broad, split it into non-overlapping time slices,
fetch each once, deduplicate by stable incident identity, then compute.

### Compute

For raw project rows:

- MTTR = mean and median service-impact/downtime duration in hours.
- MTTD = mean and median of detected time minus occurred time.
- Exclude rows missing required fields and state the excluded count.
- Keep environments separate.

Do not use ticket lifetime as MTTR.

## Aggregate mode

Call:

```text
get_incident_analytics {
  scope?,
  division?,
  rubato_project_ids?,
  period?,
  bucket?
}
```

Use server-computed counts, mean, median, correlations, and 5-why/follow-up
fields. Do not recompute aggregate metrics from partial project data.

Support `week`, `month`, or `quarter` buckets when the runtime schema permits.

At division/company scope:

- do not print incident title;
- do not print customer/system-identifying free text;
- report only aggregate categories and redacted examples already provided by
  the server.

## Read

Prioritize:

1. severity mix and movement;
2. mean plus median MTTR/MTTD;
3. customer/team/monitoring detection share when returned;
4. repeated layer/job-type/environment hints;
5. open/unresolved and 5-why status.

Calendar quarters are the default. Ask before applying a fiscal calendar.

## Output

Use a compact table:

```text
| Period | Incidents | MTTR mean | MTTR median | MTTD mean | MTTD median | Note |
```

Then add:

- abnormal period/severity movement;
- detection-source movement;
- repeated cause hints, labeled as hypotheses;
- excluded/missing data;
- open/5-why follow-up state.

Do not prescribe detailed remediation unsupported by the evidence.

## Failure behavior

- Empty result: report zero incidents in the exact scope/window.
- Forbidden: report scope unavailable; do not reconstruct it.
- Missing timestamps: exclude from the affected metric and count exclusions.
- Tool absent: report project or aggregate capability unavailable.
