---
orphans: {N}          # code-level, material → FAIL if >0
phantoms: {N}         # material, complete-graph only → FAIL if >0
redundancy: {N}       # LITERAL duplicate artifact only → FAIL if >0
boundary_warn: {N}    # Engine 2 IPE-conformance (over/under-merge, naming) → WARN
inference_warn: {N}   # Engine 3 (UNSUPPORTED / granularity / restates / naming) → WARN
unverifiable: {N}     # no/empty/partial graph, empty index, ambiguous
coverage_status: {OK|UNVERIFIABLE|FAIL}     # LOUD, distinct from result — never silently PASS
boundary_status: {OK|PARTIAL|FAILED}        # engine-completion accounting
judgment_status: {OK|PARTIAL|FAILED}        # engine-completion accounting
result: {PASS|FAIL}
---

# Synthesis Judgment Report — scope: {SCOPE}

**Date**: {DATE} · **Result**: {RESULT} · **Coverage status**: {COVERAGE_STATUS}

> This report is emitted, not enforced. The consumer (rebuild-spec handoff, CI, a human) reads
> `result` + `coverage_status` and decides. `result: FAIL` fires ONLY on a deterministic Engine-1
> defect (or `--strict-coverage` on a graphable stack with a missing graph). WARN never flips result.

---

## Summary

| Bucket | Count |
|--------|-------|
| orphans (FAIL) | {N} |
| phantoms (FAIL) | {N} |
| redundancy (FAIL) | {N} |
| boundary WARN | {N} |
| inference/judgment WARN | {N} |
| unverifiable | {N} |
| **Result** | **{RESULT}** |

---

## FAIL — deterministic coverage defects (Engine 1)

### Orphans (code with no doc trace)
{ORPHANS}

### Phantoms (doc cites code with no graph node)
{PHANTOMS}

### Literal duplicate artifacts
{DUPLICATES}

---

## WARN — boundary / judgment (advisory, never flips result)

{WARN_FINDINGS}

---

## UNVERIFIABLE (loud — not a verified PASS)

{UNVERIFIABLE}

---

## Engine-completion status

- coverage_status: **{COVERAGE_STATUS}**
- boundary_status: **{BOUNDARY_STATUS}**
- judgment_status: **{JUDGMENT_STATUS}**

## How to remediate

- FAIL orphans/phantoms → cite the missing source in a feature spec, or remove the phantom citation.
- `coverage_status: UNVERIFIABLE` → build the graph (`graph_preflight`) and run `--feature-specs` first, then re-audit.
- WARN → a human weighs each; none blocks. design-intent WARNs are experimental.
