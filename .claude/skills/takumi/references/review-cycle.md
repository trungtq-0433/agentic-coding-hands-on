# The Master's Inspection

A craftsman does not release work that has not been examined.
The inspection cycle is where craft becomes quality.

## Interactive Inspection (max 3 cycles)

```
cycle = 0
LOOP:
  1. Spawn reviewer → score, critical_count, warnings, suggestions

  2. DISPLAY FINDINGS:
     ┌─────────────────────────────────────────┐
     │ Inspection Results: [score]/10          │
     ├─────────────────────────────────────────┤
     │ Summary: [what was forged], tempering   │
     │ [X/X passed]                            │
     ├─────────────────────────────────────────┤
     │ Critical Defects ([N]): MUST FIX        │
     │  - [defect] at [file:line]              │
     │ Concerns ([N]): SHOULD FIX             │
     │  - [concern] at [file:line]             │
     │ Refinements ([N]): CONSIDER             │
     │  - [suggestion]                         │
     └─────────────────────────────────────────┘

  3. AskUserQuestion (header: "Inspect & Approve"):
     IF critical_count > 0:
       - "Fix critical defects" → fix, re-run tempering, cycle++, LOOP
       - "Fix all issues" → fix all, re-run tempering, cycle++, LOOP
       - "Approve anyway" → PROCEED
       - "Abort" → stop
     ELSE:
       - "Approve" → PROCEED
       - "Address concerns" → fix, cycle++, LOOP
       - "Abort" → stop

  4. IF cycle >= 3 AND user selects fix:
     → "⚠ 3 inspection cycles completed. Final decision required."
     → AskUserQuestion: "Approve with noted concerns" / "Abort workflow"
```

## Auto-Inspection (for auto discipline)

```
cycle = 0
LOOP:
  1. Spawn reviewer → score, critical_count, warnings

  2. IF score >= 9.5 AND critical_count == 0:
     → Auto-approve, PROCEED

  3. ELSE IF critical_count > 0 AND cycle < 3:
     → Auto-fix critical defects
     → Re-run tempering
     → cycle++, LOOP

  4. ELSE IF critical_count > 0 AND cycle >= 3:
     → ESCALATE TO USER

  5. ELSE (no critical, score < 9.5):
     → Approve with concerns logged, PROCEED
```

## Critical Defect Definition

A defect that must be remedied before the work leaves the workshop:
- Security: XSS, SQL injection, OWASP vulnerabilities
- Performance: bottlenecks, inefficient algorithms
- Architecture: violations of established patterns, excessive coupling
- Principles: YAGNI, KISS, DRY violations

## Output Formats

- Waiting: `⚒ Stage 5: Inspected — [score]/10 — AWAITING approval`
- After fix: `⚒ Stage 5: [old]/10 → Fixed [N] defects → [new]/10 — Approved`
- Auto-approved: `⚒ Stage 5: Inspected — 9.8/10 — Auto-approved`
- Approved: `⚒ Stage 5: Inspected — [score]/10 — Approved`
