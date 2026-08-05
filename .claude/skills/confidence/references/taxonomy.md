# Confidence Taxonomy — Full Specification

## Levels

### EXTRACTED (0.9-1.0)
**Definition:** Information found directly in source code, configuration, or data. No inference needed.

**When to use:**
- Function/class exists at specific location
- Import statement links two modules
- Config value is set to specific value
- Test explicitly asserts behavior
- Error message appears in logs

**Score guide:**
- 1.0 — directly observed in code (line number available)
- 0.95 — observed in generated/compiled output
- 0.9 — observed in documentation that matches code

### INFERRED (0.5-0.89)
**Definition:** Reasonable deduction from available evidence. Not directly stated but logically follows.

**When to use:**
- Module likely handles X based on naming + imports
- Function probably called from Y (call graph analysis)
- Performance bottleneck suspected from code pattern
- Cross-module dependency implied but not directly imported
- Design pattern detected from structural analysis

**Score guide:**
- 0.85-0.89 — strong evidence from multiple signals
- 0.7-0.84 — moderate evidence, single strong signal
- 0.5-0.69 — weak evidence, pattern-based guess

### AMBIGUOUS (0.0-0.49)
**Definition:** Uncertain. Could go either way. Requires human verification.

**When to use:**
- Dead code detection (might be used dynamically)
- Race condition possibility (depends on runtime)
- Security concern that may be mitigated elsewhere
- Legacy code purpose unclear
- Naming suggests one thing, implementation does another

**Score guide:**
- 0.4-0.49 — leaning toward true but not confident
- 0.2-0.39 — could go either way
- 0.0-0.19 — barely worth mentioning, included for completeness

## Decision Tree

```
Is the fact directly visible in source code?
├── YES → EXTRACTED (0.9-1.0)
└── NO → Is there strong supporting evidence?
    ├── YES (multiple signals) → INFERRED (0.7-0.89)
    ├── SOME (one signal) → INFERRED (0.5-0.69)
    └── NO (pattern/heuristic only) → AMBIGUOUS (0.0-0.49)
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Tag every line with [EXTRACTED:1.0] | Only tag non-obvious findings |
| Use INFERRED when you actually saw it in code | Use EXTRACTED — be accurate |
| Score 0.9 for gut feelings | Score honestly, prefer lower |
| Skip evidence after tag | Always include brief reason |
| Use AMBIGUOUS to avoid commitment | AMBIGUOUS means "needs human review", not "I'm lazy" |

## Per-Skill Examples

### tkm:review-code
```
- Missing null check at auth.ts:45 [EXTRACTED:1.0]
- Possible memory leak in event listener cleanup [INFERRED:0.7] (no removeListener found)
- This abstraction might be over-engineered [AMBIGUOUS:0.4] (used in 2 places, could simplify)
```

### tkm:fix-bug
```
- Root cause: unhandled promise rejection at api.ts:120 [EXTRACTED:1.0]
- Contributing factor: race condition in cache invalidation [INFERRED:0.65]
- Possibly related: similar bug in legacy module [AMBIGUOUS:0.3]
```

### tkm:scan-codebase (with graph)
```
- src/auth/middleware.ts — directly relevant (god node, 47 connections) [EXTRACTED:1.0]
- src/billing/utils.ts — likely related via permissions check [INFERRED:0.7]
- src/legacy/helpers.ts — possibly connected (cross-community edge) [AMBIGUOUS:0.35]
```

### tkm:takumi (plan insights)
```
- Critical file: src/db/client.ts (38 dependencies) [EXTRACTED:1.0]
- Hidden dependency: billing→auth permissions check [INFERRED:0.7]
- Phase boundary: auth cluster and billing cluster are separate communities [EXTRACTED:0.95]
```
