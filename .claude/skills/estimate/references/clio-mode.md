# Clio Mode — Workflow Reference

Pipeline for generating estimation artifacts from Sun* Clio Knowledge Graph.

**Requires:** Clio MCP server configured + `.estimate.yml` with `project_id`.

---

## Setup Check

1. Read `.estimate.yml` → extract `project_id` (fallback: `.clio.yml`)
2. If neither exists → ask user for `project_id`
3. Verify `clio_query` MCP tool is available
4. If MCP missing → error: "Clio MCP not configured. See SKILL.md → Setup → Clio Mode."

---

## Pipeline (Full Run — `/tkm:estimate`)

Run steps **in order** — each depends on the previous:

| Step | Mode | Reference | Output |
|------|------|-----------|--------|
| 1 | project-profile | [generate-project-profile.md](generate-project-profile.md) | `outputs/project_profile_{id}.csv` + Excel |
| 2 | user-story | [generate-user-story.md](generate-user-story.md) | `outputs/user_stories_{id}.md` |
| 3 | screen-flow | [generate-screen-flow.md](generate-screen-flow.md) | `outputs/screen_list_{id}.csv` + `screen_flow_{id}.md` |
| 4 | function-list | [generate-function-list.md](generate-function-list.md) | `outputs/function_list_{id}.csv` + `function_summary_{id}.md` |
| 5 | estimate | [generate-estimate-clio.md](generate-estimate-clio.md) | JSON → MD + Excel + HTML |

Steps 1 and 2 are standalone. Steps 3 → 4 → 5 are sequential (each requires prior output).

---

## Single Mode Run

```
/tkm:estimate project-profile
/tkm:estimate user-story
/tkm:estimate screen-flow
/tkm:estimate function-list
/tkm:estimate estimate
```

For single mode: load only the relevant reference above. Skip upstream steps if their outputs exist.

---

## Estimation Formula (Step 5)

Clio Mode uses the same KB role-based formula as Spec Mode:

```
per_role_md = base × complexity × tech × experience × (1 + buffer_pct/100)
total_md    = sum of all role MDs
story_points → Fibonacci mapping (1,2,3,5,8,13,21) — 1 SP ≈ 0.5 MD
```

Requirements come from Clio KG queries (not parsed documents). All KB parameters loaded from `references/knowledge-base.md`.

---

## Output Format

Estimate step produces the **same JSON schema** as Spec Mode — fully compatible with `render-estimate.py`.

**Template tier selection for Clio projects:**
- Full function list present → `bidding`
- Screen flow only, no function list → `quick`
- Minimal data (no screen flow) → `discovery`

---

## Rules

- All Clio queries run **sequentially** (never in parallel)
- No fabrication — only include data returned by `clio_query`
- If query returns empty/unclear: one broader follow-up; if still empty → mark `unknown`
- `project_id` required at all times
- All output files → `outputs/` in CWD
