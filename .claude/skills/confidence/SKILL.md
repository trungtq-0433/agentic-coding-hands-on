---
name: tkm:confidence
description: "Confidence taxonomy for agent outputs. Tags findings as EXTRACTED/INFERRED/AMBIGUOUS with 0-1 scores. Reference skill — other skills import this convention."
argument-hint: "[--help]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: project-context-management
triggers: ["confidence level", "EXTRACTED", "INFERRED", "AMBIGUOUS", "evidence taxonomy", "how sure"]
---

# Confidence Taxonomy

Standard convention for tagging agent outputs with confidence levels. Not a tool — a **reference skill** that other skills use.

## When to Use

- Generating reports, findings, analysis outputs
- Code review findings
- Debugging root cause analysis
- Architecture discovery results
- Any assertion about code behavior that isn't 100% certain

## When NOT to Use

- Pure code generation (the code works or doesn't)
- User-facing UI text
- Trivial/obvious observations (don't tag `[EXTRACTED:1.0]` on everything)

## Taxonomy

| Level | Score Range | Meaning | Example |
|-------|-----------|---------|---------|
| **EXTRACTED** | 0.9-1.0 | Found directly in code/data | `Function calls db.query()` |
| **INFERRED** | 0.5-0.89 | Reasonable deduction from evidence | `Module likely handles auth based on naming + imports` |
| **AMBIGUOUS** | 0.0-0.49 | Uncertain, flag for human review | `Legacy util may be dead code` |

## Output Format

Inline tag after each finding:

```
- Auth middleware uses JWT tokens [EXTRACTED:1.0] (src/auth/middleware.ts:15)
- Billing module likely checks permissions via auth [INFERRED:0.7] (no direct import found)
- Legacy utils may be unused [AMBIGUOUS:0.3] (referenced in old tests only)
```

## Integration Guide

Skills that should use this taxonomy:
- `tkm:review-code` → tag each finding
- `tkm:fix-bug` → tag root cause confidence
- `tkm:scan-codebase` → tag file relevance when using graph
- `tkm:takumi` → tag architecture insights in plans

## Guidelines

1. **Don't over-tag**: skip obvious things (syntax errors are always EXTRACTED)
2. **Score honestly**: prefer lower scores over false confidence
3. **Include evidence**: brief reason after the tag
4. **AMBIGUOUS = action needed**: these findings need human verification

See `references/taxonomy.md` for full specification and decision tree.
