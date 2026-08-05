# Internal Analysis Report Templates

Structure for the internal analysis report generated during discovery. AI fills each section based on parsed document content and gap analysis.

## Report Structure

```markdown
# Discovery Analysis: {Project Name}

**Date:** {YYYY-MM-DD}
**Source Documents:** {list of parsed files}
**Analyst:** AI-assisted discovery

---

## 1. Document Quality Assessment

| Metric | Value |
|--------|-------|
| Completeness | {Low|Medium|High} — {percentage}% of typical spec coverage |
| Clarity | {Vague|Moderate|Clear} — {rationale} |
| Detail Tier | {discovery|quick|bidding} |
| Page/Screen Count | {N explicit, M inferred} |

**Assessment Notes:**
- {bullet points on what's well-documented vs missing}

---

## 2. Feature Inventory

| # | Feature/Module | Screens | Complexity | Confidence | Gap Level |
|---|----------------|---------|------------|------------|-----------|
| 1 | {name} | {count} | {S/M/L/XL} | {High/Med/Low} | {None/Minor/Major} |

**Complexity mapping:**
- **S** = Simple CRUD, static pages
- **M** = Standard features with validation, relationships
- **L** = Complex logic, integrations, real-time
- **XL** = Custom engines, AI/ML, marketplace logic

**Confidence** = how well the spec describes this feature (High = detailed, Low = inferred)

**Gap Level** = how much info is missing for estimation (None = ready, Major = needs answers)

---

## 3. Identified Integrations

| Service/API | Purpose | Auth Method | Complexity | Notes |
|-------------|---------|-------------|------------|-------|
| {name} | {what it does} | {API key/OAuth/unknown} | {S/M/L} | {known constraints} |

---

## 4. Risk Flags

### Assumptions Made
- {assumption} — **Impact if wrong:** {consequence}

### Unclear Scope
- {item} — **Needs:** {what info is missing}

### Technical Risks
- {risk} — **Mitigation:** {suggestion}

---

## 5. Recommended Configuration

| Parameter | Recommendation | Rationale |
|-----------|---------------|-----------|
| Template Tier | {discovery/quick/bidding} | {based on doc quality} |
| Active Roles | {FE, BE, QA, ...} | {based on feature types} |
| Complexity Class | {standard/complex/enterprise} | {based on integrations, scale} |
| Suggested Buffer | {15-30%} | {based on uncertainty level} |

---

## 6. Q&A Coverage Summary

| Priority | Count | Addressed Features |
|----------|-------|-------------------|
| Critical | {N} | {feature list} |
| High | {N} | {feature list} |
| Medium | {N} | {feature list} |
| **Total** | **{N}** | |

### Features Without Questions
- {list any features that don't need clarification — already well-specified}
```

## Guidance for AI

- **Completeness %**: Count how many of these are present in the spec: user stories, screen list, tech stack, NFR, actor list, data model, API spec, wireframes, business rules. Each = ~12.5%.
- **Detail Tier**: Use `discovery` if source is a pitch deck or business consultation. `quick` if explicit requirements but limited detail. `bidding` if ≥3 of the above items are present.
- **Screen Count**: Count explicitly mentioned screens. Infer additional screens from feature descriptions (e.g., "user management" implies list + detail + create/edit screens).
- **Role Recommendation**: Map feature types to roles — file uploads suggest infra, complex UI suggests design, multi-language suggests BrSE, etc.
