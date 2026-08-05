---
name: tkm:ki-voice-action-plan
description: "Evaluate KPI Insight survey follow-ups and SCAR action plans against comments, incidents, target KPIs, due dates, and final results. Use this when checking whether an action plan worked, SCAR/follow-up status, overdue actions, evidence alignment, or target achievement. Read-only."
argument-hint: "[project-id] [--include-inactive] [--limit <N>]"
metadata:
  author: takumi-agent-kit
  version: "0.1.0"
module: mcp-external-tools
triggers: ["SCAR action", "follow-up status", "action plan effectiveness", "overdue action", "survey action plan", "target achievement", "action có hiệu quả"]
---

# KPI Insight Voice Action Plan

Check whether follow-up actions match available evidence and measured targets.

Before calling tools, read
[`skills/_shared/extras/kpi-insight/kpi-insight-mcp-connection.md`](../_shared/extras/kpi-insight/kpi-insight-mcp-connection.md).

## Rules

- Stay read-only and MCP-only.
- Judge evidence alignment, not effort or intent.
- Never assert root cause from correlation.
- Keep overdue and failed/unachieved separate.
- A target without `final_value` is unmeasured, not failed.
- Use the actual schema field `include_inactive`; never send
  `include_closed`.

## Fetch follow-ups

```text
get_followup_status {
  rubato_project_id?,
  include_inactive?,
  limit?
}
```

Omit project only when the user explicitly asks for every follow-up visible to
their current token.

For each returned target, preserve:

- `kpi_id`;
- `baseline_value`;
- `target_value`;
- `direction`;
- `final_value`;
- `achieved`.

## Fetch evidence selectively

Use only evidence relevant to returned follow-ups:

```text
get_project_quality_detail {
  rubato_project_id,
  survey_type: "css"
}

get_project_incidents {
  rubato_project_id,
  period?
}

get_kpi_status {
  rubato_project_id,
  kpi_id
}
```

Do not call every evidence tool when there are zero follow-ups. Do not fetch a
KPI unrelated to a target.

## Run four checks

### 1. Stated cause vs evidence

Compare the plan's stated cause with survey/incident evidence. Say:

- supported;
- contradicted;
- insufficient evidence.

Never replace this with “the real cause is”.

### 2. Action vs stated cause

Check whether the action logically addresses its own stated cause. Keep this
separate from whether the cause is correct.

### 3. Target movement

Compare baseline, target, final value, direction, and server `achieved`:

- use `achieved` when present;
- null final → unmeasured;
- avoid recomputing a status when the server already provides it.

### 4. Liveness

Use due date, status, review status, and checkpoint:

- overdue/open;
- completed/reviewed;
- inactive;
- no checkpoint.

Do not count overdue as failed unless the result actually supports failure.

## Output

```text
<scope> · <follow-up count>
Evidence-aligned and measured: <count/examples>
Aligned but unmeasured/not moved: <count/targets>
Evidence mismatch: <plan statement vs evidence>
Overdue/open: <count>
Next review questions: <up to three, tied to specific follow-ups>
```

Quote customer evidence verbatim when used, without naming an individual.

## Failure behavior

- Zero follow-ups: report none in scope and stop before evidence calls.
- Forbidden: report the blocked scope; do not widen it.
- Missing final KPI: mark unmeasured.
- Evidence tool absent: mark that check incomplete rather than failing the plan.
