# KPI Insight KPI reference

Use this reference to resolve KPI names and explain business meaning. Use the
MCP response—not this file—for the current value, status, direction, threshold,
band, and freshness.

## Interpretation contract

1. Treat server fields as canonical.
2. If a value, status, or threshold is null, report it as missing/unmeasured.
3. Never restore a numeric threshold from memory or this reference.
4. Read quality flags before ranking or recommending action.
5. Distinguish open-sprint measurements from completed-sprint outcomes.
6. Treat a small denominator as insufficient evidence for a trend.
7. For cumulative KPIs, separate historical contribution from current-sprint
   movement.

## Legato delivery and quality KPIs

### `LEG_ISSUE_CLOSED_RATIO`

- Meaning: proportion of sprint work closed relative to work assigned.
- Formula concept: closed issues divided by in-sprint issues.
- Direction: in-range; use the server response for the current band.
- Trap: an open sprint is incomplete by definition. Do not call a temporary
  ratio a delivery failure.

### `LEG_QAB_PROP`

- Meaning: QA bugs relative to delivered engineering effort.
- Formula concept: QA bugs divided by actual effort hours.
- Direction: lower is generally better.
- Trap: missing effort logs can inflate the result.

### `LEG_QA_BUG_HANDLING`

- Meaning: share of delivery effort consumed by fixing QA bugs.
- Formula concept: QA-bug fixing effort divided by delivery and bug-fixing
  effort.
- Direction: use the server response; very low values may indicate missing logs
  rather than excellent quality.

### `LEG_UAT_BUG_RATIO`

- Meaning: bugs that escaped internal QA and were found in UAT.
- Formula concept: UAT bugs divided by QA plus UAT bugs.
- Direction: lower is generally better.
- Trap: tiny bug counts do not support a trend.

### `LEG_TASK_EST_ACCURACY`

- Meaning: actual task/QA-bug effort relative to estimated effort.
- Formula concept: actual hours divided by estimated hours for the measured
  work.
- Direction: in-range.
- Trap: open sprints and missing time logs make a low interim ratio
  non-diagnostic.

## DORA and engineering operations KPIs

### `deploy_frequency`

- Meaning: production deployment cadence.
- Direction: higher is generally better.
- Trap: compare like periods and confirm production deployment detection.

### `lead_time_changes`

- Meaning: time from code change to production.
- Direction: lower is generally better.
- Trap: source/integration gaps can make the period incomplete.

### `change_fail_rate`

- Meaning: share of deployments that fail or require remediation.
- Direction: lower is generally better.
- Trap: confirm the denominator before interpreting a percentage.

### `cycle_time`

- Meaning: elapsed time from pull-request open to merge.
- Direction: lower is generally better.
- Trap: distinguish review bottlenecks from intentionally paused work.

## Largo productivity-shape KPIs

These metrics describe work shape, not individual performance.

### `LAR_SPRINT_AVG_CLOSED_STORY_EFFORT`

- Meaning: average actual effort per closed story.
- Trap: unusually high values can reflect oversized stories or blockers;
  unusually low values can reflect story-definition or logging problems.

### `LAR_SPRINT_AVG_CLOSED_TASK_EFFORT`

- Meaning: average actual effort per closed task.
- Trap: do not infer productivity without scope/quality context.

### `LAR_SPRINT_AVG_CLOSED_BUG_FIXING_EFFORT`

- Meaning: average actual effort per fixed bug.
- Trap: severity and technical debt affect comparability.

### `LAR_SPRINT_AVG_KLCC_CH_ASSIGNED_EFFORT`

- Meaning: source-code change volume relative to assigned effort.
- Trap: code volume is not delivered value.

### `LAR_SPRINT_QA_UAT_BUG_DENSITY`

- Meaning: QA/UAT bug density relative to source-code change volume.
- Direction: lower is generally better.

### `LAR_SPRINT_QA_UAT_BUG_DENSITY_EFFORT`

- Meaning: QA/UAT bug density relative to effort when code-volume data is not
  usable.
- Direction: lower is generally better.

## Quality flags

| Flag | Interpretation |
|---|---|
| `UNREALISTIC_RATIO` | The ratio may be inflated by work added and closed in the same sprint |
| `UNTRACKED_EFFORT` | Missing spent-time logs can invalidate effort-based KPIs |
| `UNTRACKED_BUG_EFFORT` | Bug handling can be undercounted |
| `MISSING_ESTIMATION` | Estimate-based KPIs are incomplete |
| `SUSPICIOUS_SPENT_TIME` | Logged effort appears incomplete relative to the work |

When a flag affects a KPI, lead with the measurement limitation. Do not rank an
unmeasured project against clean projects.
