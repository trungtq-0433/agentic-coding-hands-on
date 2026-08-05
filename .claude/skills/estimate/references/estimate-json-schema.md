# Estimate JSON Schema

The AI outputs this JSON as the single source of truth. Renderers transform it into markdown and Excel.

## Structure

```json
{
  "template_tier": "discovery | quick | bidding",
  "project_name": "string",
  "generated_date": "YYYY-MM-DD",
  "estimator": "string",
  "confidence": { "level": "Low|Medium|High", "range_pct": 25 },
  "source_document": "string",

  "parameters": {
    "active_roles": ["fe", "be", "qa_manual"],
    "role_names": {
      "fe": "Frontend",
      "be": "Backend",
      "qa_manual": "QA (Manual)"
    },
    "project_multipliers": [
      { "name": "Frontend", "key": "tech_frontend", "value": 1.0, "rationale": "..." }
    ],
    "per_task_factors": [
      { "name": "Requirements clarity", "value": 1.2, "scope": "which tasks" }
    ],
    "cost_per_md": 40000,
    "cost_per_md_by_role": {
      "pm": 50000,
      "brse": 60000
    },
    "currency": "JPY"
  },

  "options": [
    {
      "id": "A",
      "name": "Full Phase 1 Scope",
      "subtitle": "All Requirements",
      "ai_reduction_pct": 20,
      "categories": [
        {
          "name": "User Management",
          "tasks": [
            {
              "id": "2.1",
              "name": "Login page with OAuth",
              "effort": {
                "fe": { "base": 1.5, "complexity": 1.1, "experience": 1.0, "buffer_pct": 15, "md": 2 },
                "be": { "base": 2.75, "complexity": 1.2, "experience": 1.0, "buffer_pct": 15, "md": 4 },
                "qa_manual": { "base": 0.75, "complexity": 1.0, "experience": 1.0, "buffer_pct": 10, "md": 1 }
              },
              "total_md": 7,
              "story_points": 13,
              "original_md": 7,
              "is_dev_task": true,
              "notes": "OAuth + password login",
              "split_recommended": false
            }
          ]
        }
      ]
    },
    {
      "id": "B",
      "name": "Budget-Constrained",
      "subtitle": "¥5M Target",
      "budget_target": 5000000,
      "ai_reduction_pct": 20,
      "scope_reductions": [
        { "item": "MFA removed", "impact_md": -3 }
      ],
      "tasks": [
        {
          "id": "2.1",
          "name": "Login page (simplified)",
          "effort": {
            "fe": { "md": 1 },
            "be": { "md": 3 },
            "qa_manual": { "md": 1 }
          },
          "total_md": 5,
          "story_points": 8,
          "option_a_md": 7,
          "reduction_reason": "OAuth only, no password"
        }
      ]
    }
  ],

  "future_phases": [
    {
      "name": "Phase 2 — Future Expansion",
      "tasks": [
        {
          "id": "3.5",
          "name": "Corporate eKYB",
          "effort": {
            "be": { "md": 4 },
            "fe": { "md": 2 }
          },
          "total_md": 6,
          "story_points": 13,
          "original_md": 4,
          "notes": "Complex verification flow"
        }
      ]
    }
  ],

  "risks": [
    {
      "id": "R1",
      "description": "API plan renewal",
      "category": "External",
      "probability": 4,
      "impact": 4,
      "score": 16,
      "mitigation": "Build abstraction layer"
    }
  ],

  "tbd_items": [
    { "item": "API renewal", "status": "Unconfirmed", "risk_impact": "High", "recommendation": "Confirm ASAP" }
  ],

  "comparison": [
    { "area": "Auth (2.1)", "my_md": 7, "original_md": 5, "reason": "+2 MD: OAuth complexity" }
  ],

  "validation_checks": [
    { "check": "No task > 13 SP", "result": "All passed", "status": "pass" }
  ],

  "assumptions": ["string"],
  "recommendations": ["string"],
  "unresolved_questions": ["string"]
}
```

## Field Rules

### Required (all tiers)
- `template_tier`, `project_name`, `generated_date`
- At least one entry in `options`
- `parameters.active_roles` (ordered list of role slugs)
- `parameters.role_names` (slug → display name)
- `assumptions` (at least 1)

### Bidding tier requires
- `parameters` with `project_multipliers` and `per_task_factors`
- Option A `categories[].tasks[]` with full formula fields in `effort`: `base`, `complexity`, `experience`, `buffer_pct`
- `risks` with probability/impact scoring
- `validation_checks`

### Quick tier minimal
- Single option with flat `tasks[]` (no categories nesting needed)
- `risks` without scoring (just description + mitigation)
- No `parameters.project_multipliers`, `comparison`, `tbd_items`

### Discovery tier
- Same structure as quick tier, plus:
- `parameters.confidence_pct` (integer, 30-50 range typical)
- `parameters.input_type` (e.g., "business_consultation", "strategy_proposal")
- `parameters.sub_systems` (array of sub-system slugs, e.g., ["loopa", "ec-platform"])
- `parameters.estimate_ranges` with `optimistic`, `most_likely`, `pessimistic` objects (each has `total_md` and `total_sp`)
- Tasks may use `categories[]` to group by sub-system
- Each task should have `source` field (string) indicating which page/diagram the feature was inferred from
- Buffer 20-40% (higher than quick/bidding due to inferred requirements)

### Task fields — Option A (formula-driven)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Task ID (e.g. "2.1", "5.1b") |
| `name` | string | yes | Task name |
| `effort` | object | yes | Dict keyed by role slug |
| `total_md` | integer | yes | Sum of all `effort[role].md` |
| `story_points` | integer | yes | Fibonacci SP mapping (task-level) |
| `original_md` | integer | no | Original estimate MD (for comparison) |
| `is_dev_task` | boolean | yes | true = AI reduction applies |
| `notes` | string | no | Task notes |
| `split_recommended` | boolean | no | true if SP > 13 |

### Effort role entry (Option A)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base` | number | yes | Base effort in MD for this role |
| `complexity` | number | yes | Combined complexity multiplier |
| `experience` | number | yes | Experience multiplier |
| `buffer_pct` | number | yes | Buffer percentage (15 = 15%) |
| `md` | integer | yes | `round(base * complexity * experience * (1 + buffer_pct/100))` |

### Task fields — Option B (simplified)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Task ID |
| `name` | string | yes | Task name |
| `effort` | object | yes | Dict keyed by role slug, each with only `md` |
| `total_md` | integer | yes | Sum of all `effort[role].md` |
| `story_points` | integer | yes | Option B SP |
| `option_a_md` | integer | yes | Option A total MD (for comparison) |
| `reduction_reason` | string | yes | Why reduced |

### Computed by renderers (do NOT include in JSON)
- Category subtotals (per-role and grand total)
- With/without AI totals
- Cost calculations (use `cost_per_md` or `cost_per_md_by_role`)
- Delta and delta %
- SP/MD ratio

## Validation Rules

- Every role in `effort` keys must be in `parameters.active_roles`
- `total_md` must equal `sum(effort[role].md for role in effort)`
- Each role `md` must equal `round(base * complexity * experience * (1 + buffer_pct/100))` (Option A, tolerance of 1)
- At least one role entry in `effort` for every task
- Only include roles that actually have effort for a task (no zero-effort roles)

## Rendering

```bash
python3 scripts/render-estimate.py estimate.json -o ./output -f md,xlsx
python3 scripts/render-estimate.py estimate.json -f md
python3 scripts/render-estimate.py estimate.json -f xlsx
python3 scripts/validate-estimate.py estimate.json
```
