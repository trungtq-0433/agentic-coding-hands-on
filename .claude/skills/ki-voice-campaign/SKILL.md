---
name: tkm:ki-voice-campaign
description: "Analyze KPI Insight CSS or IS survey campaigns, response coverage, scores, division/SDM/customer breakdowns, and cross-campaign trends. Use this when reviewing a CSS campaign, IS campaign, NPS, survey response rate, survey trend, or campaign comparison. Customer views remain role-restricted."
argument-hint: "[--type css|is] [--campaign <id> | --period <period> --market <market>] [--by division|sdm|customer | --trend [scope]]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["CSS campaign", "IS campaign", "survey campaign", "survey trend", "response rate", "NPS", "campaign breakdown", "khảo sát CSS", "khảo sát nội bộ"]
---

# KPI Insight Voice Campaign

Read survey coverage and results at campaign/portfolio altitude.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and MCP-only.
- Report coverage before score.
- Never average an average.
- Keep CSS and IS semantics separate.
- Never reconstruct a restricted customer view from project names.
- Do not generalize a trend from one or two respondents.

## Resolve mode and selector

Select:

- CSS overview → `get_css_campaign_overview`;
- IS overview → `get_is_campaign_overview`;
- trend → `get_survey_trend`.

For a campaign overview, require one:

- `campaign_id`; or
- `period` plus `market`.

Ask once if neither can be resolved. Do not send an empty request merely because
the JSON schema has no required fields. If both forms are explicit, prefer
`campaign_id`.

Default `survey_type=css` only when the wording does not mention internal/team
survey. Preserve a user-specified CSS/IS type.

## Fetch overview

```text
get_css_campaign_overview {
  campaign_id?
  period?
  market?
}

get_is_campaign_overview {
  campaign_id?
  period?
  market?
}
```

Read server totals, coverage, score, and breakdown fields. Do not assume every
field exists in both survey types.

### CSS

- Report response coverage and average CSS score.
- Report NPS only when returned.
- Customer breakdown is commercially sensitive and Admin/BOD-only.

### IS

- Report internal response coverage and score.
- Do not attach NPS or customer semantics.
- Do not infer an individual employee's response.

## Fetch trend

```text
get_survey_trend {
  survey_type?
  scope?
  scope_id?
  market?
  last_n?
}
```

Require/derive a meaningful scope. If the wording does not establish company,
division, SDM, or another current schema scope, ask once.

For each period/bucket show:

- respondents/eligible when available;
- average score;
- missing or low-coverage state.

Describe direction only across comparable periods with adequate coverage.

## Break down

- Division/SDM: name at most two or three meaningful deviations from the
  campaign result, each with coverage.
- Customer: use only the field returned by the server. If absent/forbidden,
  report unavailable for the current role and continue without it.
- Project comment/Q&A requests belong to `tkm:ki-voice-project`.

Any bucket with fewer than three respondents can be displayed, but label it too
small for trend/generalization.

## Output

Keep chat under about 400 words:

```text
<CSS|IS> · <campaign/period> · <market/scope>
Coverage: <responded>/<eligible>
Score: <server average> [NPS only for CSS when returned]
Notable: <up to three buckets + coverage>
Trend: <comparable-period direction or insufficient evidence>
Role/data caveats: <restricted, absent, small sample>
```

## Failure behavior

- Invalid/missing selector: ask for campaign ID or period+market.
- Forbidden sensitive field: do not fail the entire non-sensitive report.
- Empty campaign: report no responses/data for the selector.
- Tool absent: report the requested CSS/IS/trend capability unavailable.
