---
name: tkm:ki-pm-tooling-audit
description: "Audit whether a KPI Insight project's GitHub Project is configured to the standard and followed in practice. Use this when checking GitHub Project setup, custom fields, required statuses, label compliance, A1–A10 checks, monthly hygiene, or tooling-adoption trend."
argument-hint: "<project-id> [--months <N>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["GitHub Project standard", "tooling audit", "project setup", "label compliance", "GitHub hygiene", "A1-A10", "board adoption", "GitHub Project đúng chuẩn"]
---

# KPI Insight Tooling Audit

Separate configuration from day-to-day adoption.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).
Load these references when rendering detailed checks:

- [`references/github-standardization.md`](references/github-standardization.md)
- [`references/github-standardization-checks.md`](references/github-standardization-checks.md)

## Rules

- Stay read-only and MCP-only.
- Grade the board; never edit a field, option, repository, or label.
- Treat a non-GitHub source as out of scope, not a failing grade.
- Use server `compliant`, `score_pct`, status, and checklist fields.
- Do not substitute direct `gh` inspection when a tool is absent/unavailable.

## Resolve

Require `rubato_project_id`. Default `--months` to the three previous complete
months. Reject non-positive windows.

## Tier A — setup

Call:

```text
get_github_project_standardization { rubato_project_id }
get_github_label_compliance { rubato_project_id }
```

Render:

- each applicable A1–A8 check;
- missing required field/status/repository mapping;
- A9–A10 label state;
- missing required labels and mapping recommendation returned by the server.

Do not hide missing items behind a percentage. If a tool returns both a score
and checklist, show the checklist as the decision surface.

If either tool reports that the source is not GitHub, stop and report out of
scope.

## Tier B — practice

For every month in the selected window call:

```text
get_github_project_hygiene {
  rubato_project_id,
  month,
  year
}
```

Use returned monthly values without recomputing a new canonical score.

Classify the sequence:

- improving;
- declining;
- flat;
- not measurable.

If `total_issues = 0`, mark that month not measurable. Never score it as zero or
failure.

## Prioritize

Return at most three priorities, ordered by measurement impact:

1. gaps that block estimate/effort/sprint/status-based KPIs;
2. tracker/label mapping gaps that misclassify work;
3. declining runtime practice;
4. cosmetic differences.

Say what should be configured or followed; do not claim the change was made.

## Output

```text
<project> · GitHub Project audit · <N months>
Setup: <server summary>
Missing required: <specific checklist items>
Labels: <server status and missing items>
Practice: <monthly sequence and trend>
Not measurable: <zero-issue months>
Priorities: <up to three gaps + affected measurements>
```

## Failure behavior

- Tool absent: report the unavailable tier and stop that tier.
- Forbidden/not found: report it; do not use GitHub directly.
- GitHub upstream unavailable: report source availability.
- Null rule: show `No data` and exclude it from client-side counts.
