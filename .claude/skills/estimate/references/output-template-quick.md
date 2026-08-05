# Quick Estimation Template

For brief specs / few requirements / early-stage estimates.

## Markdown Template

```markdown
# Project Estimate: {project_name}

**Generated**: {date}
**Confidence Level**: {confidence}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Story Points | {total_sp} |
| Total Man-Days | {total_days} |
| Buffer | {buffer}% |
| Risk Level | {risk_level} |

## Requirements Breakdown

| ID | Requirement | Priority | Complexity | FE | BE | QA | **Total MD** | SP |
|----|-------------|----------|------------|-----|-----|-----|--------------|-----|
| R1 | {title} | {priority} | {complexity} | {fe} | {be} | {qa} | **{days}** | {sp} |

**Note**: Role columns (FE/BE/QA/etc.) reflect active roles from `parameters.active_roles`. Only populated for roles involved in that task.

## Phase Breakdown

| Phase | SP | Days | % of Total |
|-------|-----|------|------------|
| Analysis & Design | {sp} | {days} | {pct}% |
| Development | {sp} | {days} | {pct}% |
| Testing | {sp} | {days} | {pct}% |
| Deployment | {sp} | {days} | {pct}% |

## Risk Assessment

| Risk | Category | Impact | Score | Mitigation |
|------|----------|--------|-------|------------|
| {risk_name} | {category} | {impact} | {score} | {mitigation} |

## Assumptions

- {assumption_1}
- {assumption_2}
```

## JSON Schema & Generator

For Excel/PDF output, write a JSON matching the template fields then run:

```bash
python3 skills/estimate/scripts/generate-excel-pdf.py estimate.json -o ./output -f xlsx,pdf
```

JSON keys: `project_name`, `generated_date`, `confidence_level`, `summary` (total_story_points, total_man_days, buffer_percentage, risk_level), `requirements[]` (id, title, priority, complexity, story_points, man_days), `phases[]` (name, story_points, man_days, percentage), `risks[]` (name, category, impact, probability, score, mitigations[]), `assumptions[]`, `architecture.tech_stack` (frontend[], backend[], database[], infrastructure[]).
