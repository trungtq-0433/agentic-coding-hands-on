---
name: tkm:ki-kpi-drilldown
description: "Explain one KPI Insight metric for one project: business meaning, current server threshold/status, numerator and denominator, and the tickets driving it. Use this when asking 'why is this KPI warning/critical', KPI threshold questions, bug leakage, issue-closed ratio, estimation accuracy, or ticket breakdown."
argument-hint: "<kpi-id-or-name> <project-id> [--sprint <id>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["KPI drilldown", "why is this KPI critical", "vì sao KPI", "KPI threshold", "ticket breakdown", "bug leakage", "issue closed ratio", "estimation accuracy"]
---

# KPI Insight Drilldown

Explain one KPI and the tickets that produce it.

Read:

- [`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md)
- [`skills/_shared/extras/kpi-insight/kpi-insight-kpi-reference.md`](../_shared/extras/kpi-insight/kpi-insight-kpi-reference.md)

## Rules

- Stay read-only and MCP-only.
- Never recompute or correct the server KPI.
- Read current value/status/threshold/direction from the response.
- Use the shared reference only for name resolution, meaning, and traps.
- If ticket detail is forbidden, do not summarize an inaccessible list.

## Resolve

Require:

- one KPI ID or unambiguous KPI name;
- one `rubato_project_id`.

If two KPI aliases match, ask which one. Do not choose the first.

## Fetch

```text
get_kpi_status {
  rubato_project_id,
  kpi_id,
  sprint_id?
}

get_kpi_ticket_breakdown {
  rubato_project_id,
  kpi_id,
  sprint_id?
}
```

Call status first. If status is forbidden/not found, stop before breakdown.

## Explain in order

1. **Meaning** — one business sentence.
2. **Measurement** — value, server status/band, direction, and threshold when
   present.
3. **Composition** — server-returned numerator/denominator and exclusions.
4. **Drivers** — at most two or three tickets that materially affect the
   breakdown.
5. **Mechanical change** — describe what would change the metric from the
   returned components; do not prescribe a generic “improve quality”.
6. **Trust** — quality flags, missing estimates/effort, open sprint, and small
   denominator.

Do not call a ratio based on a tiny denominator a trend. For cumulative KPIs,
separate old contribution from current-sprint movement.

## Output

Keep the response under about 300 words, in the user's language:

```text
<KPI> · <project> · <sprint>
Meaning: ...
Current: <value/status/server threshold>
Why: <numerator>/<denominator> · <dominant tickets>
What changes it: <mechanical action>
Data caveat: <flags or none>
```

If value or threshold is null, say it is unavailable. Never insert a numeric
fallback.
