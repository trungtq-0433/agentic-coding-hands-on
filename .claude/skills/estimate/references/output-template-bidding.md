# Bidding-Grade Estimation Template

For full project estimates intended for client proposals or cross-team comparison. Sections marked (if available) are included only when input provides the data.

## Markdown Template

```markdown
# Project Estimate: {project_name}

**Generated**: {date}
**Estimator**: {estimator}
**Confidence Level**: {confidence} (±{range}%)
**Source Document**: {source}

---

## Executive Summary

| Metric | {Plan A name} | {Plan A + AI} | {Plan B name} | {Plan B + AI} | Original A | Original B |
|--------|---------------|---------------|---------------|---------------|------------|------------|
| **FE MD** | | | | | | |
| **BE MD** | | | | | | |
| **QA MD** | | | | | | |
| **{Other Role} MD** | | | | | | |
| **Total MD** | | | | | | |
| **Total SP** | | | | | | |
| **Buffer** | | | | | | |
| **Cost** | | | | | | |
| **Risk Level** | | | | | | |

> Key finding: {1-2 sentence comparison with original if reviewing existing estimate}

## Estimation Parameters

### Formula
estimate_days = base_effort × complexity × tech_multiplier × experience × (1 + buffer)

### Project-Level Multipliers
| Factor | Value | Rationale |
|--------|-------|-----------|
| Frontend | {x}x | {reason} |
| Backend | {x}x | {reason} |
| Database | {x}x | {reason} |
| Team Familiarity | {x}x | {reason} |
| Experience Level | {x}x | {reason} |
| Domain Familiarity | {x}x | {reason} |
| Team Size | {x}x | {reason} |
| AI Reduction | {x}x | Applied to dev tasks only |

### Per-Task Complexity Factors
| Factor | Value | Scope |
|--------|-------|-------|
| Requirements clarity | {x}x | {which tasks} |
| Integration complexity | {x}x | {which tasks} |
| Security/Compliance | {x}x | {which tasks} |

---

## Plan Comparison (if multiple plans)

| Category | Feature | Plan A | Plan B | Notes |
|----------|---------|--------|--------|-------|
| {cat} | {feature} | ● / △ / ✕ | ● / △ / ✕ | {scope difference} |

Legend: ● = full scope, △ = reduced scope, ✕ = excluded

---

## Actors (if available)

| ID | Actor | Type | Description | Primary Functions | Volume |
|----|-------|------|-------------|-------------------|--------|
| A-{n} | {name} | Human / External System | {desc} | {features} | {frequency} |

---

## User Stories (if available)

| ID | Phase | Actor | Story | Priority | Release |
|----|-------|-------|-------|----------|---------|
| US-{n} | {phase} | {actor} | As {who}, I want {what}, because {why} | Must/Should/Nice | Phase {n} |

---

## Screen List (if available)

| # | Screen ID | Screen Name | Device | Level | WF (MD) | UI (MD) | Total (MD) | Notes |
|---|-----------|-------------|--------|-------|---------|---------|------------|-------|
| {n} | {id} | {name} | SP/PC | Low/Mid/High | {wf} | {ui} | {total} | {notes} |

---

## Tech Stack (if available)

| # | Layer | Technology | Version | Rationale | Alternatives Considered | Risk |
|---|-------|-----------|---------|-----------|------------------------|------|
| {n} | {layer} | {tech} | {ver} | {why chosen} | {rejected + why} | {risk} |

---

## Detailed Task Estimates

Group by category. For each category use a sub-heading and table:

### {Category Name} ({total_md} MD / {total_sp} SP)

| ID | Task | FE | BE | QA | {Other} | **Total** | SP | Orig MD | Notes |
|----|------|-----|-----|-----|---------|-----------|-----|---------|-------|
| {id} | {name} | {fe_md} | {be_md} | {qa_md} | {other_md} | **{total_md}** | {sp} | {orig} | {notes} |

SP markers: tasks > 13 SP get ⚡ and MUST be split into subtasks (except PM tasks).

**Note**: Only active roles from `parameters.active_roles` appear as columns. Tasks show effort only for roles actually involved.

### Summary by Category

| Category | FE | BE | QA | {Other} | **Total MD** | My SP | Original MD | Delta | Delta % |
|----------|-----|-----|-----|---------|--------------|-------|-------------|-------|---------|
| {cat} | {fe} | {be} | {qa} | {other} | **{md}** | {sp} | {orig} | {+/-n} | {%} |
| **Total (no AI)** | **{fe}** | **{be}** | **{qa}** | **{other}** | **{md}** | **{sp}** | | | |
| **Total (with AI)** | **{fe}** | **{be}** | **{qa}** | **{other}** | **{md}** | **{sp}** | **{orig}** | **{+/-n}** | **{%}** |

### With vs Without AI

| Scope | Without AI (MD) | With AI (MD) | Savings (MD) |
|-------|-----------------|--------------|--------------|
| Dev tasks | {md} | {md} | {-n} |
| Non-dev tasks | {md} | {md} | 0 |
| **Total** | **{md}** | **{md}** | **{-n}** |

---

## Scope Reductions (if Plan B / budget-constrained)

| Reduction | Impact (MD) |
|-----------|------------|
| {what was cut} | -{n} MD |

### Cost Analysis

| Scenario | MD | Cost | Within Budget? |
|----------|----|------|----------------|
| Without AI | {md} | {cost} | ✅ / ❌ |
| With AI ({n}%) | {md} | {cost} | ✅ / ❌ |

---

## Non-Functional Requirements (if available)

| ID | Category | Requirement | Target | Implementation | Priority | Status |
|----|----------|-------------|--------|----------------|----------|--------|
| NFR-{n} | {cat} | {req} | {target} | {how} | Must/Should | Confirmed / ⚠ TBD |

---

## Infrastructure (if available)

### Components
| # | Component | Category | Service | Role | Redundancy | NFR |
|---|-----------|----------|---------|------|------------|-----|
| {n} | {name} | {cat} | {service} | {role} | {redundancy} | {nfr_ids} |

### Monthly Cost
| # | Category | Service | Spec | Prod (¥/mo) | Stg (¥/mo) | Notes |
|---|----------|---------|------|-------------|------------|-------|
| {n} | {cat} | {svc} | {spec} | {prod} | {stg} | {notes} |

---

## Phase 2+ Reference Estimates (if multi-phase)

| ID | Task | My MD | SP | Original MD | Notes |
|----|------|-------|-----|-------------|-------|
| {id} | {name} | {md} | {sp} | {orig} | {notes} |

---

## Risk Assessment

### Risk Matrix
| # | Risk | Category | Probability | Impact | Score | Mitigation |
|---|------|----------|------------|--------|-------|------------|
| R{n} | {risk} | {cat} | {1-5} | {1-5} | {PxI} | {mitigation} |

### TBD Items (⚠)
| Item | Status | Risk Impact | Recommendation |
|------|--------|-------------|----------------|
| {item} | ⚠ {status} | {impact} | {action} |

## Comparison with Original (if reviewing existing estimate)

| Area | My Estimate | Original | Reason |
|------|-------------|----------|--------|
| {area} | {my_md} MD | {orig_md} MD | {why different} |

### Validation Checks
| Check | Result | Status |
|-------|--------|--------|
| No task > 13 SP | {result} | ✅ / ⚠ |
| Buffer ≥ 10% | {result} | ✅ / ⚠ |
| SP/MD ratio ≈ 0.5 | {result} | ✅ / ⚠ |
| Testing ≥ 15% of dev | {result} | ✅ / ⚠ |

## Assumptions & Recommendations

- Assumptions: {list}
- Recommendations: {list}
- Unresolved questions: {list}
```
