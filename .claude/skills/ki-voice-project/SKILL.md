---
name: tkm:ki-voice-project
description: "Read KPI Insight CSS and IS feedback for one project, including score trends, detailed Q&A/comments, cached assessment, CSS×IS comparison, and optional KPI–survey alignment. Use this when asking what customers or the team said about a project, survey comments, project quality, or CSS/IS alignment."
argument-hint: "<project-id> [--type css|is|both] [--campaign <id> | --period <period>] [--last <N>] [--align-kpi]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["project CSS", "project IS", "customer feedback", "team feedback", "survey comments", "CSS IS comparison", "KPI survey alignment", "khách hàng và team nói gì"]
---

# KPI Insight Voice Project

Read one project's survey evidence without laundering comments or overstating a
small sample.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and MCP-only.
- Quote substantive comments in the original language with a short gloss.
- Never attribute a response to a named individual.
- One or two respondents represent only the respondents, not an organization.
- If one survey side is missing, say so.

## Resolve

Require `rubato_project_id`.

Modes:

- CSS: default when the user does not mention internal/team feedback.
- IS: explicit internal/team intent.
- Both: explicit `both` or wording such as “customers and team”.
- Alignment: explicit KPI/CSS/IS comparison intent or `--align-kpi`.

## Fetch survey evidence

```text
get_project_quality {
  rubato_project_id,
  last_n_periods?
}

get_project_quality_detail {
  rubato_project_id,
  campaign_id?,
  period?,
  survey_type
}
```

Fetch only the requested survey side(s). Use trend to provide proportion and
detail to explain the latest/selected point.

For cached CSS assessment when relevant:

```text
get_assessment {
  scope: "project",
  scope_id: <rubato_project_id>,
  feature: "css_assessment",
  period?
}
```

Treat assessment as optional cached commentary. Never replace raw
question/answer evidence with an invented AI summary.

## Read comments

1. Group by business theme, not question number.
2. Keep the strongest representative quote per theme.
3. Preserve the original text and add a short gloss only when needed.
4. Flag a free-text value that appears to be a leaked multiple-choice option.
5. Never assert who wrote a comment.

## Compare CSS and IS

Use both sides only when both contain measured data:

| CSS | IS | Cautious reading |
|---|---|---|
| Low | Low | Both measured sides report difficulty |
| Low | High | Customer and internal perception differ |
| High | Low | Customer result is positive while internal experience is strained |
| High | High | Both measured sides are positive |

Use server status/band when available; do not impose numeric cutoffs. Describe a
perception gap, not its cause.

## Align KPI with surveys

Call:

```text
get_project_health {
  rubato_project_id,
  period: "last_3_sprints"
}
```

Then compare the three-sprint delivery shape with measured CSS/IS periods:

- State exactly how many sprints and respondents were used.
- Do not compute a three-sprint average when fewer than three comparable
  results exist.
- Do not claim alignment/gap from one or two survey respondents.
- Do not infer causality between KPI and survey movement.

## Output

```text
<project> · <campaign/period>
Coverage: CSS <n> · IS <n>
Trend: <measured periods and direction>
Customer themes: <quotes + gloss>
Internal themes: <quotes + gloss>
Cross-read/alignment: <bounded observation>
Evidence caveats: <missing side, small sample, stale cache>
```

Keep chat under about 400 words unless the user explicitly asks for all Q&A.

## Failure behavior

- Empty survey metrics: report unmeasured; do not substitute project health.
- Detail forbidden: report score/coverage only when those fields are accessible.
- Cached assessment empty: continue with raw measured evidence.
- Alignment health forbidden: do not derive KPI state from survey text.
