---
name: tkm:ki-kpi-insight
description: "Read cached KPI Insight Bot Insight cards for a project and organize them by prevention theme. Use this when reviewing Bot Insight, AI advisory cards, chronic KPI patterns, prevention themes, or questions about what KPI Insight recommends for a project."
argument-hint: "<project-id> [--period <YYYY-MM>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["Bot Insight", "KPI Insight cards", "AI advisory", "prevention themes", "chronic KPI pattern", "Bot Insight nói gì"]
---

# KPI Insight Bot Insight

Read cached advisory cards. Never create or refresh an assessment.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and cache-only.
- Call `get_assessment`; do not analyze raw KPIs to imitate Bot Insight.
- Do not retry an empty cache hoping it changes.
- Preserve critical wording and the card's situation → impact →
  recommendation structure.
- Treat forbidden as terminal for the project.

## Prevention themes

| Theme | Meaning |
|---|---|
| `SPRINT_STUCK` | Sprint progress is stuck |
| `HIGH_SPEED_LOW_QUALITY` | Delivery speed is outrunning quality |
| `HIGH_TECH_DEBT` | Technical debt is constraining delivery |
| `WRONG_ESTIMATION` | Actual work and estimates mismatch |
| `BUG_LEAKAGE_TO_UAT` | Bugs escape to UAT |
| `TOO_MUCH_REWORK` | Rework consumes delivery |
| `QA_COVERAGE_GAP` | QA coverage/capacity may be insufficient |
| `OVER_ESTIMATION_WASTE` | Estimates carry excess padding |
| `SOURCE_CODE_INFLATION` | Change volume is high relative to value |
| `PROCESS_BOTTLENECK` | Work is queuing at a process stage |

Non-problem states:

- `SPRINT_HEALTHY`: report healthy and stop inventing concerns.
- `WAITING_FOR_DATA`: report an operations/data freshness problem, not a
  delivery failure.

Treat a theme repeated for three or more periods as chronic. Ask what was
already tried; do not simply repeat the original recommendation.

## Fetch

```text
get_assessment {
  scope: "project",
  scope_id: <rubato_project_id>,
  feature: "bot_insight",
  period?
}
```

Require a project ID. Only project scope is supported by this workflow. If the
server reports another scope unsupported, surface that result without summing
projects.

## Read

1. Group cards by theme, not severity.
2. Treat multiple cards of one theme as one pattern with multiple evidence
   points.
3. Lead with the most repeated/chronic theme.
4. Preserve card recommendations; do not soften or add unsupported causes.
5. Close with generation time/freshness.

## Output

Keep the response under about 300 words:

```text
<project> · Bot Insight · generated <date>
Primary pattern: <theme, card count, chronic state>
- <situation → impact → recommendation>
Other patterns: <one line each>
Cache/data note: <empty, stale, or none>
```

An empty cache is a valid answer: say no cached Bot Insight is available. Do not
write one yourself or call a write/refresh tool.
