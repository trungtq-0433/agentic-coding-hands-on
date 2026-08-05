---
name: tkm:ki-pm-estimate
description: "Read KPI Insight issue-estimate coverage and historical hours-per-point evidence. Use this when checking which synced issues lack estimates, estimate coverage by tracker type, estimate-based KPI measurement gaps, or historical discipline baselines/drift. Do not use for estimating a project/spec/WBS; use tkm:estimate for that."
argument-hint: "[coverage <project-code-or-id> --period <YYYY-MM> [filters] | baseline [--discipline <values>] [--period <value>] [--source <value>]]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["issue estimate coverage", "issues missing estimate", "estimate gaps", "hours per point", "estimate baseline", "estimate drift", "issue nào chưa estimate", "KPI Insight estimate"]
---

# KPI Insight Estimate Evidence

Read synchronized issue coverage and historical evidence. This release never
creates, fills, refreshes, or writes estimates.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Routing boundary

Use this skill for KPI Insight data already synchronized from trackers:

- estimate coverage;
- missing estimate candidates;
- historical hours-per-point themes/drift.

Use `tkm:estimate` instead for:

- estimating a PDF/spec/RFP;
- producing WBS/man-days;
- planning effort for a new feature.

The word “estimate” alone is insufficient to select this skill.

## Read-only boundary

Allowed:

- `kpi_issue_estimate_candidates`
- `kpi_issue_estimate_detail` when available and authorized
- `kpi_estimate_themes`

Never call:

- `kpi_issue_estimate_write`
- `kpi_issue_estimate_ai_fill`
- `kpi_estimate_mine`

If asked to fill/write/refresh, explain that this release is read-only and stop.
`kpi_issue_estimate_ai_fill` writes through a background job; it is not a
preview.

## Mode: coverage

Require:

- `period`;
- one project selector: `projectCode` or `projectId`.

Call:

```text
kpi_issue_estimate_candidates {
  projectCode?,
  projectId?,
  period,
  trackerTypes?,
  sourceType?,
  onlyMissing?
}
```

Use `onlyMissing=true` when the user asks for gaps. Preserve explicit filters.

Report only what the response supports:

- total/estimated/missing counts when returned;
- coverage percentage only when a trustworthy denominator exists;
- missing candidates by tracker type and apparent scope/size;
- affected estimate-based KPI measurement.

If the response contains only missing candidates, report the missing count. Do
not invent a total or percentage.

### Optional detail

Call:

```text
kpi_issue_estimate_detail {
  sourceType,
  issueRefs
}
```

Use detail only when issue body/content is necessary to distinguish important
candidates and the role/tool permits it. Limit `issueRefs` to relevant
candidates.

If detail is forbidden:

- keep the coverage summary;
- say issue-body detail is unavailable;
- do not fetch issue bodies from GitHub/Redmine/Jira directly.

Never turn detail into proposed estimates in this release.

## Mode: baseline

Call:

```text
kpi_estimate_themes {
  disciplines?,
  period?,
  source?
}
```

Report:

- evidence-bearing discipline/theme;
- hours-per-point only when returned;
- evidence period/source;
- history/drift and sample/coverage caveats.

Rules:

- Never invent an hours-per-point value.
- Treat an empty cache as no baseline evidence.
- Never call `kpi_estimate_mine` to populate an empty cache.
- A theme marked `baseline: false`, including AI comparison disciplines, is not
  the non-AI baseline.
- Do not use a historical baseline as a new project estimate without the
  estimation workflow and its requirements.

## Output

Keep chat under about 350 words.

Coverage:

```text
<project> · <period>
Coverage: <server-supported counts/percentage>
Important gaps: <tracker type + issue refs>
Measurement impact: <affected KPI/evidence>
Detail caveat: <forbidden/none>
```

Baseline:

```text
<filters>
Evidence base: <themes and returned rates>
Movement: <history/drift>
Coverage caveat: <sample/cache/source>
```

## Failure behavior

- Missing project/period in coverage: ask once.
- Empty candidates: report no matching missing estimates; do not imply the
  entire project is complete unless the response includes total coverage.
- Empty themes: report no mined evidence; do not refresh.
- Forbidden detail: degrade to candidate metadata.
- Any write request: refuse the mutation and keep the session read-only.
