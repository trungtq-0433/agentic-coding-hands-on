# Review Cycle

How to handle reviewer results, tuned to the active mode.

## Autonomous Mode

```
cycle = 0
LOOP:
  1. Run the reviewer → score, critical_count, warnings, suggestions

  2. IF score >= 9.5 AND critical_count == 0:
     → Output: "✓ Review [score]/10 - Auto-approved"
     → PROCEED to next step

  3. ELSE IF critical_count > 0 AND cycle < 3:
     → Output: "⚙ Auto-fixing [N] critical issues (cycle [cycle+1]/3)"
     → Resolve the critical issues
     → Re-run the tests
     → cycle++, GOTO LOOP

  4. ELSE IF cycle >= 3:
     → ESCALATE to the user via AskUserQuestion
     → Show the findings
     → Options: "Fix manually" / "Approve anyway" / "Abort"

  5. ELSE (score < 9.5, no critical):
     → Output: "✓ Review [score]/10 - Approved with [N] warnings"
     → PROCEED (warnings noted, not blocking)
```

## Human-in-the-Loop Mode

```
ALWAYS:
  1. Run the reviewer → score, critical_count, warnings, suggestions

  2. Show the findings:
     ┌─────────────────────────────────────┐
     │ Review: [score]/10                  │
     ├─────────────────────────────────────┤
     │ Critical ([N]): [list]              │
     │ Warnings ([N]): [list]              │
     │ Suggestions ([N]): [list]           │
     └─────────────────────────────────────┘

  3. Use AskUserQuestion:
     IF critical_count > 0:
       - "Fix critical issues"
       - "Fix all issues"
       - "Approve anyway"
       - "Abort"
     ELSE:
       - "Approve"
       - "Fix warnings/suggestions"
       - "Abort"

  4. Act on the answer:
     - Fix → implement, re-test, re-review (3 cycles max)
     - Approve → proceed
     - Abort → halt the workflow
```

## Quick Mode Review

Same logic as Autonomous, with three dials turned:
- Lower bar: a score of 8.5 or better passes
- One auto-fix cycle, then escalate
- Eyes on: correctness, security, no regressions

## Critical Issues (Always Block)

- Security holes (XSS, SQL injection, OWASP)
- Performance bottlenecks (O(n²) where O(n) is reachable)
- Architecture violations
- Anything risking data loss
- Breaking changes shipped without a migration
