# Test Report Format

The QA report's fixed shape. Trade grammar for concision.

## Template

```markdown
# Test Report — {date} — {scope}

## Test Results Overview
- **Total**: X tests
- **Passed**: X | **Failed**: X | **Skipped**: X
- **Duration**: Xs

## Coverage Metrics
| Metric   | Value | Threshold | Status |
|----------|-------|-----------|--------|
| Lines    | X%    | 80%       | PASS/FAIL |
| Branches | X%    | 70%       | PASS/FAIL |
| Functions| X%    | 80%       | PASS/FAIL |

## Failed Tests
### `test/path/file.test.ts` — TestName
- **Error**: Error message
- **Stack**: Relevant stack trace (truncated)
- **Cause**: Brief root cause analysis
- **Fix**: Suggested resolution

## UI Test Results (if applicable)
- **Pages tested**: X
- **Screenshots**: ./screenshots/
- **Console errors**: none | [list]
- **Responsive**: checked at [viewports] | skipped
- **Performance**: LCP Xs, FID Xms, CLS X

## Build Status
- **Build**: PASS/FAIL
- **Warnings**: none | [list]
- **Dependencies**: all resolved | [issues]

## Critical Issues
1. [Blocking issue description + impact]

## Recommendations
1. [Actionable improvement with priority]

## Unresolved Questions
- [Any open questions, if any]
```

## Guidelines

- List every failed test with its error message — no detail summarized away
- Coverage: name the actual files/functions left bare, not bare percentages
- Screenshots: drop the paths right into the report so they're one click off
- Recommendations: order them by what they cost (critical > high > medium > low)
- Keep the report under 200 lines — break it into sections when the scope runs wide
- Name the report by the pattern the hooks drop into the `## Naming` section
