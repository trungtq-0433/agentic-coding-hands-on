# Reporting Standards

A fixed shape for diagnostic and investigation reports. Trade grammar for brevity.

## When to Use

- Wrapping up a system investigation
- Summarizing what a debugging session turned up
- Writing an incident post-mortem
- Reporting the results of a performance analysis

## Report Structure

### 1. Executive Summary (3-5 lines)

- **Issue:** One line on what it is
- **Impact:** Who and what it hit, and how badly
- **Root cause:** One line on why
- **Status:** Resolved / Mitigated / Under investigation
- **Fix:** What you did, or what you recommend

### 2. Technical Analysis

**Timeline:**
```
HH:MM - Event description
HH:MM - Next event
...
```

**Evidence:**
- Log excerpts that matter (trimmed to the essential lines)
- Query results with the key metrics
- Error messages and stack traces
- Before-and-after comparisons

**Findings:**
- Each finding alongside the evidence that backs it
- Keep confirmed facts apart from hypotheses
- Flag correlation where you can't yet claim causation

### 3. Actionable Recommendations

**Immediate (P0):**
- [ ] The critical fix, with the steps to apply it

**Short-term (P1):**
- [ ] Follow-up improvements

**Long-term (P2):**
- [ ] Better monitoring and alerting
- [ ] Architecture improvements
- [ ] Preventive measures

For each one: what to do, why, the impact you expect, and an effort estimate (low/medium/high).

### 4. Supporting Evidence

- Log excerpts
- Query results and execution plans
- Performance metrics
- Test results and error traces
- Screenshots or diagrams where they help

### 5. Unresolved Questions

Set down whatever's still murky:
- What needs more digging
- Questions for the team
- Assumptions still waiting on validation

## Report File Naming

Follow the naming pattern from the `## Naming` section the hooks inject — it carries the full path and the computed date.

**Example:** `plans/reports/debugger-260205-2215-api-500-investigation.md`

## Writing Guidelines

- **Concise:** facts and evidence, not a story. Trade grammar for brevity
- **Evidence-backed:** every claim stands on a log, a metric, or a reproduction step
- **Actionable:** recommendations are specific, with clear next steps
- **Honest:** name the unknowns out loud — "likely cause" is not "confirmed cause"
- **Structured:** headers, tables, and bullets so it can be scanned

## Template

```markdown
# [Issue Title] - Investigation Report

## Executive Summary
- **Issue:**
- **Impact:**
- **Root cause:**
- **Status:**
- **Fix:**

## Timeline
- HH:MM -
- HH:MM -

## Technical Analysis
### Findings
1.
2.

### Evidence
[logs, queries, metrics]

## Recommendations
### Immediate (P0)
- [ ]

### Short-term (P1)
- [ ]

### Long-term (P2)
- [ ]

## Unresolved Questions
-
```
