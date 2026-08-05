---
name: spec-compliance-review
description: The opening pass — confirm the build matches the spec or plan it was meant to satisfy, before anyone weighs in on quality
---

# Spec Compliance Review

## Purpose

Confirm the work does what was asked BEFORE you start judging how it's written.
Elegant code that solves the wrong problem is still the wrong code.

## When to Use

- Once you've built features off a plan
- Ahead of the code-quality pass
- Whenever a plan or spec governs the work under review

## Process

1. **Load spec/plan** — Open the plan.md or phase file that set out this work
2. **List requirements** — Pull out every requirement and acceptance criterion
3. **Check each requirement** against what was actually built:
   - There? → PASS
   - Absent? → MISSING (fix it before the quality pass)
   - Showed up but isn't in the spec? → EXTRA (mark for removal unless there's a reason)
4. **Verdict:**
   - Everything required is present, nothing extra slipped in → PASS → on to the quality review
   - Something required is missing → FAIL → implementer fixes → review again
   - Unjustified extras → WARN → raise it with the user

## Checklist Template

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | [from spec] | PASS/MISSING/EXTRA | [evidence] |

## Red Flags

- Waving off the spec pass because "the code looks good"
- Letting extra features ride without a spec reason
- Treating this pass as optional
- Grading code quality before spec compliance is settled
