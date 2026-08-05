# Improvement Aspect — Test Coverage

**Track:** technical · **Aspect:** 03 of 14 · **Slug:** `test-coverage`
**Read first:** `references/technical/02-improvement.md` — Shared rules, Ownership map, Entry format, and Value rubric apply unconditionally.
**Output:** `plans/improvement-proposal/technical/02-improvement/03-test-coverage.md`
**Template:** `templates/technical/02-improvement/03-test-coverage.md`

## Goal
Enumerate test-coverage improvement opportunities: unit/integration/e2e presence, coverage gaps, critical untested paths, flaky tests, missing test types for the discovered stack.

## Intake gate
Owns ALL testing concerns exclusively. Unit tests, integration tests, e2e tests, coverage-target gaps, missing test scaffolding, flaky-test rehab, test strategy, and test infrastructure concerns ALL belong to this aspect. This is the single authority on testing scope. Aspects 02-code-quality and 04-ci-cd MUST NOT emit entries whose primary remedy is writing or fixing tests, raising coverage targets, or adding test types.
