# PR Body Template

Reach for this shape whenever you open a PR through `gh pr create`.

## Template

```markdown
## Summary
<bullet points — infer from changelog entry or commit messages>

## Linked Issues
<list issues from Step 2>
- Closes #XX — <issue title>
- Relates to #YY — <issue title>
<or "No linked issues.">

## Pre-Landing Review
<findings from review step>
<format: "N issues (X critical, Y informational)" or "No issues found.">

<if informational issues exist, list them:>
- [file:line] Issue description

## Test Results
- [x] All tests pass (<count> tests, 0 failures)
<or>
- [x] Tests skipped (--skip-tests)

## Changes
<output of git diff --stat, trimmed to key files>

## Ship Mode
- Mode: <official|beta>
- Target: <target-branch>
```

## PR Title Format

```
type(scope): brief description
```

Read the type off what changed:
- `feat`: something new the code can now do
- `fix`: a bug put right
- `refactor`: shape changed, behavior held steady
- `perf`: a speed or efficiency win
- `chore`: upkeep — dependencies, config, housekeeping

## Example

```markdown
## Summary
- Add faceted filtering to the search results page
- Cache facet counts in Redis with a 60s TTL
- Add a clear-all-filters control to the results header

## Linked Issues
- Closes #71 — Faceted search for the product catalog
- Relates to #65 — Search performance under load

## Pre-Landing Review
Pre-Landing Review: 1 issue (0 critical, 1 informational)

- [src/search/facets.ts:88] Magic number 60 for the facet cache TTL
  Fix: Extract to named constant FACET_CACHE_TTL_SECONDS

## Test Results
- [x] All tests pass (58 tests, 0 failures)

## Changes
 src/search/facets.ts        | 74 +++++++
 src/search/query-builder.ts | 38 +++
 src/pages/results.tsx       | 41 ++++
 tests/search.test.ts        | 52 +++++
 4 files changed, 205 insertions(+)

## Ship Mode
- Mode: official
- Target: main
```

## Notes

- Keep each summary bullet to a single line — one change, one line
- Print the review outcome even when it's "No issues found" — proof the pass happened
- Quote the real test counts the run produced, never a guess
- A PR already open? Reach for `gh pr edit`, not `gh pr create`
- Never drop the linked-issues section — the paper trail matters
- Beta PRs aim at the dev/beta branch, never main
