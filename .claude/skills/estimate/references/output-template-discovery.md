# Discovery-Phase Estimation Template

For business consultation documents, high-level proposals, or early-stage discussions where no detailed technical specification exists. Requirements are **inferred from business context** (diagrams, market analysis, customer hearings, concept descriptions).

## When to Use

Input has **none or ≤1** of {user stories, screen list, tech stack, NFR, actor list} AND contains primarily:
- Business model / strategy diagrams
- Market analysis / customer hearing data
- High-level system concept (screenshots, flow diagrams)
- No function list, no API spec, no wireframes

## Key Differences from Quick Template

| Aspect | Quick | Discovery |
|--------|-------|-----------|
| Requirements source | Stated in spec | Inferred from business context |
| Confidence level | Medium (60-80%) | Low (30-50%) |
| Buffer | 10-20% | 20-40% (higher uncertainty) |
| Estimation basis | Feature list → effort | System concept → feature inference → effort |
| Scope sections | Single system | May cover multiple sub-systems / cases |
| Assumptions weight | Supporting | Critical — drive the entire estimate |

## Markdown Template

```markdown
# Discovery-Phase Estimate: {project_name}

**Generated**: {date}
**Confidence Level**: {confidence} (Discovery-phase — requirements inferred from business context)
**Input Type**: Business consultation / proposal document

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Story Points | {total_sp} |
| Total Man-Days | {total_days} |
| Buffer | {buffer}% |
| Risk Level | {risk_level} |
| Confidence | {confidence}% |

> **Note**: This estimate is based on inferred requirements from a business-level document, not a technical specification. Actual effort may vary significantly once detailed requirements are defined.

## Document Analysis

### Input Quality Assessment
- Document type: {type — e.g., business consultation, strategy proposal}
- Technical detail level: {low / medium}
- Ambiguity level: {high / medium}
- Sub-systems identified: {count}

### Inferred System Scope
{Description of what systems/features were inferred from the business context}

## Sub-System Estimates

### {Sub-system 1 Name}

**Inferred from**: {which pages/diagrams/sections}

| ID | Feature (Inferred) | Source | Complexity | FE | BE | QA | **Total MD** | SP |
|----|-------------------|--------|------------|-----|-----|-----|--------------|-----|
| F1.1 | {feature} | {P3 diagram / P8 screenshot} | {complexity} | {fe} | {be} | {qa} | **{days}** | {sp} |

### {Sub-system 2 Name}

(Same structure as above)

## Phase Breakdown

| Phase | SP | Days | % of Total |
|-------|-----|------|------------|
| Discovery & Requirements Definition | {sp} | {days} | {pct}% |
| Architecture & Design | {sp} | {days} | {pct}% |
| Development | {sp} | {days} | {pct}% |
| Testing & QA | {sp} | {days} | {pct}% |
| Deployment & Handover | {sp} | {days} | {pct}% |

## Risk Assessment

| Risk | Category | Impact | Score | Mitigation |
|------|----------|--------|-------|------------|
| Requirements volatility — business-level input, detailed spec TBD | Scope | High | {score} | Plan dedicated discovery/requirements phase |
| {risk_name} | {category} | {impact} | {score} | {mitigation} |

## Critical Assumptions

> These assumptions have outsized impact on this estimate. If any are wrong, the estimate should be revised.

1. **{assumption}** — {impact if wrong}
2. **{assumption}** — {impact if wrong}

## Recommendation

{Recommend next steps: e.g., conduct detailed requirements workshop, create screen list, define API contracts before committing to this estimate}

## Estimate Ranges

Given the discovery-phase nature, provide ranges instead of single-point estimates:

| Scenario | Man-Days | Story Points | Confidence |
|----------|----------|-------------|------------|
| Optimistic | {min_days} | {min_sp} | Best case — minimal scope changes |
| Most Likely | {mid_days} | {mid_sp} | Expected with normal discovery |
| Pessimistic | {max_days} | {max_sp} | Significant scope expansion after requirements clarification |
```

## JSON Schema Addition

For discovery-phase estimates, the JSON schema adds:

```json
{
  "template_tier": "discovery",
  "parameters": {
    "confidence_pct": 35,
    "input_type": "business_consultation",
    "sub_systems": ["loopa", "ec-platform"],
    "estimate_ranges": {
      "optimistic": { "total_md": 100, "total_sp": 80 },
      "most_likely": { "total_md": 150, "total_sp": 120 },
      "pessimistic": { "total_md": 220, "total_sp": 170 }
    }
  }
}
```

## Buffer Guidelines for Discovery

| Ambiguity Level | Recommended Buffer |
|-----------------|-------------------|
| High (no screen list, no API spec) | 30-40% |
| Medium (some UI mockups or partial spec) | 20-30% |
| Low (near-complete but informal spec) | 15-20% |
