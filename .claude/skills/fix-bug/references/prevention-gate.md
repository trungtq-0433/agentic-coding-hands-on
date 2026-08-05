# Prevention Gate

Once the bug is fixed, slam the door on its whole family. This step is MANDATORY.

## Core Principle

A fix with no prevention is half-finished. Patch only the symptom and the same pattern comes back around — count on it.

## Prevention Requirements (Apply Every One That Fits)

### 1. Regression Test (ALWAYS required)

Every fix MUST ship with a test that:
- **Fails** when the fix is absent (proof the test actually catches the bug)
- **Passes** when the fix is present (proof the fix actually works)

```
With no test framework on hand:
  → Drop in an inline check or assertion at the very least
  → Flag it in the report: "No test framework — added runtime assertion"
```

### 2. Defense-in-Depth Validation (When applicable)

Stack the layered validation from the `tkm:debug-code` defense-in-depth technique:

| Layer | Apply When | Example |
|-------|-----------|---------|
| **Entry point validation** | Fix touches user/external input | Turn bad input away at the API boundary |
| **Business logic validation** | Fix touches data processing | Assert the data is sane for the operation |
| **Environment guards** | Fix touches env-sensitive operations | Block dangerous ops in the wrong context |
| **Debug instrumentation** | Fix was painful to diagnose | Capture logging/context for next time |

**Rule:** Few fixes need all four layers. Use the ones that fit — but weigh each one before moving on.

### 3. Type Safety (When applicable)

| Scenario | Prevention |
|----------|-----------|
| Null/undefined was the culprit | Add strict null checks; lean on `??` or `?.` |
| Wrong type slipped through | Add a type guard or runtime validation |
| Missing property | Make the field required on the interface/type |
| Implicit any | Pin down explicit types |

### 4. Error Handling (When applicable)

| Scenario | Prevention |
|----------|-----------|
| Unhandled promise rejection | Wire up `.catch()` or try/catch |
| Missing error boundary | Add an error boundary component |
| Silent failure | Make the failure log loudly |
| No fallback for external dependency | Add a timeout plus a fallback |

## Verification Checklist (Clear Before Closing Step 5)

```
□ Pre-fix state on record? (error messages, test output)
□ Fix landed on the ROOT CAUSE (not the symptom)?
□ Fresh verification run? (identical commands to the pre-fix run)
□ Before/after comparison written down?
□ Regression test in place? (red without the fix, green with it)
□ Defense-in-depth layers weighed? (applied where they fit)
□ No fresh warnings/errors introduced?
□ Parallel verification green? (typecheck + lint + build + test)
```

## Output Format

```
Prevention measures applied:
- Regression test: [test file:line] — pins [specific scenario]
- Guard added: [file:line] — [what the guard does]
- Type safety: [file:line] — [what got tightened]
- Error handling: [file:line] — [what got wired in]

Before/After comparison:
- Before: [the exact error/failure]
- After: [the exact success output]
```

## Quick Mode Prevention

For throwaway issues (type errors, lint), prevention shrinks to:
- Regression test: optional — the type system already plays that role
- Parallel verification: typecheck + lint, nothing more
- Defense-in-depth: skip — it buys nothing on a type fix
- Still demand the before/after comparison of typecheck output
