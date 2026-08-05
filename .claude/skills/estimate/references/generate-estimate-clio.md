# Generate Estimate (Clio Mode) — Workflow Reference

Estimate development effort from Clio Function List using KB role-based formulas.
**Requires:** prior `function-list` step outputs in `outputs/`.

---

## Step 0: Load Config

1. Read `.estimate.yml` → `project_id` (fallback: `.clio.yml`)
2. If missing → ask user

---

## Step 1: Load Context

Read from `outputs/` using `project_id`:
- `function_list_{project_id}_*.csv` — required
- `screen_list_{project_id}_*.csv` — for context

Summarize project domain in ≤ 100 words.

---

## Step 2: Query Clio for Context (8 queries, sequential)

| # | Query Topic | Extract |
|---|-------------|---------|
| 1 | Technology stack, programming language, framework, frontend, backend, database | Tech stack → tech multiplier |
| 2 | Architecture patterns, design patterns, microservices | Complexity indicator |
| 3 | Testing requirements, QA, coverage, automation | Testing overhead |
| 4 | Reusable components, shared utilities, Springer extensions | Reusability discount |
| 5 | Team members, developers, personnel, roles | Team size + role availability |
| 6 | Developer level, experience, seniority, skill level | Experience multiplier tier |
| 7 | Project duration, timeline, man-month, deadline | Timeline constraints |
| 8 | Previous projects, historical data, past estimates, actual effort | Velocity calibration |

If a query returns empty: one broader follow-up; if still empty → use KB defaults for that factor.

---

## Step 3: Clarify Roles and Preferences

Ask (if not already answered via `estimate-config.yaml`):
1. Active roles: default FE, BE, QA — add Design, PM, BrSE, Infra, QA Auto if needed
2. Output language(s): Vietnamese, English, Japanese
3. Cost rate: man-day unit cost + currency (default ¥40,000/MD)
4. Experience level: junior / mid / senior / mixed

---

## Step 4: Map Function Types → KB Task Categories

For each row in `function_list_{id}.csv`:

| Clio Function Type | KB Task Category | Notes |
|--------------------|-----------------|-------|
| Authentication, Login, SSO | `authentication` | |
| CRUD screen, List/Detail/Edit | `crud` | Per screen or entity |
| Dashboard, Analytics | `reporting` | |
| File Upload/Download | `file_handling` | |
| Email, Notification | `notification` | |
| API endpoint, REST, GraphQL | `api` | |
| UI component, Layout | `ui_component` | |
| Search, Filter | `search` | |
| Admin panel, CMS | `admin` | |
| Infrastructure, Deploy | `infrastructure` | Infra role only |
| Unknown / Other | `general` | Use `medium` complexity |

---

## Step 5: KB Formula Estimation

Load [knowledge-base.md](knowledge-base.md) for YAML config values.
Load [estimation-formulas.md](estimation-formulas.md) for detailed formula reference.

**For each function:**

```
complexity = simple | medium | complex | very_complex
              (based on field count, integrations, business logic depth)

per_role_md = base[task_type] × complexity_mult × tech_mult × experience_mult × (1 + buffer_pct/100)
md          = round(per_role_md)
```

**Tech multiplier from queries:** derive from Stack Query (Query 1). If modern/familiar stack → 1.0; new/unfamiliar → 1.1–1.3.

**Experience multiplier from queries:** derive from Skill Query (Query 6):
- junior → 1.3 | mid → 1.0 | senior → 0.8 | mixed → 1.1

**Buffer:**
- Baseline: 15%
- Add +10% per risk flag (unclear requirements, new tech, performance-critical)
- Minimum: 10%

**Role assignment per function:**
- Use role-split heuristics from knowledge-base.md
- Only assign roles from confirmed active roles (Step 3)
- PM/BrSE overhead tasks may have `story_points: 0` — valid

**Story points → Fibonacci:** map `total_md * 2` → nearest Fibonacci (1,2,3,5,8,13,21).
Max 13 SP per task. If > 13 → split into 2–3 subtasks.

---

## Step 6: Risk Assessment

Load [risk-validation.md](risk-validation.md).

From Clio queries, identify:
- New/unfamiliar technology (Query 1/2)
- Tight timeline or high man-month requirements (Query 7)
- Junior-heavy team (Query 6)
- No historical data (Query 8 empty)

Score each risk: probability × impact. Suggest mitigations.

---

## Step 7: Write JSON Output

Follow [estimate-json-schema.md](estimate-json-schema.md) exactly.

```
output/<project-slug>/<name-slug>-estimate-<YYMMDD-HHMM>.json
```

**Template tier:**
- Full function list (≥ 10 functions) + screen list → `bidding`
- Screen list only or sparse function list → `quick`
- Minimal Clio data → `discovery`

Key fields:
```json
{
  "parameters": {
    "active_roles": ["fe","be","qa"],
    "role_names": {"fe":"Frontend","be":"Backend","qa":"QA Manual"}
  },
  "tasks": [{
    "story_points": 5,
    "total_md": 6,
    "is_dev_task": true,
    "effort": {
      "fe": {"base":2.0,"complexity":1.5,"experience":1.0,"buffer_pct":15,"md":3},
      "be": {"base":1.5,"complexity":1.2,"experience":1.0,"buffer_pct":15,"md":2},
      "qa": {"base":0.5,"complexity":1.0,"experience":1.0,"buffer_pct":15,"md":1}
    }
  }]
}
```

---

## Step 8: Render and Validate

```bash
python3 scripts/render-estimate.py output/<slug>/<name>-estimate-<ts>.json \
  -o output/<slug> -f md,xlsx,html

python3 scripts/validate-estimate.py output/<slug>/<name>-estimate-<ts>.json
```

HTML check:
```bash
node -e "const fs=require('fs'),h=fs.readFileSync('<html>','utf8'),m=h.match(/const DATA = (.+?);\n/s);try{JSON.parse(m[1]);console.log('HTML OK')}catch(e){console.error(e.message);process.exit(1)}"
```

---

## Step 9: Task Breakdown (Optional)

Ask: "Would you like a detailed task breakdown per team?"
If yes: `/task-breakdown output/<slug>/<name>-estimate-<ts>.json --level 3`
