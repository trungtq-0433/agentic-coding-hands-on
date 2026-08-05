---
match: 0
drift: 0          # doc claim ≠ code → CRITICAL
fabricated: 0     # doc claim has no code basis → CRITICAL
missing: 0        # documentation-worthy code absent from doc → warning
unverifiable: 0   # no citation / unreadable / stale anchor / dead code → warning
parity_score: 0.0 # match / (match+drift+fabricated) — verifiable claims only
result: PASS      # PASS iff drift==0 && fabricated==0
---
<!--
Machine-readable contract. A consumer (rebuild-spec W9, CI, a human) branches on `result` + `drift`/`fabricated`.
`parity_score` excludes UNVERIFIABLE and MISSING from the denominator so the number stays honest.
Assembled by scripts/assemble_parity_report.py from post-adjudication verdict JSON — never hand-edited.
-->

# Parity Report — {project} docs ↔ code

**Date**: {DATE} · **Scope**: {N} features, {C} claims checked · **Mode**: {sweep | --feature F### | --path <doc>}

---

## Summary

| Verdict | Count |
|---------|-------|
| MATCH | {match} |
| DRIFT | {drift} |
| FABRICATED | {fabricated} |
| MISSING | {missing} |
| UNVERIFIABLE | {unverifiable} |
| **Result** | **{PASS\|FAIL}** |

---

## Critical — Doc lies (DRIFT / FABRICATED)

<!-- One subsection per critical finding. All four faces are mandatory. If none: "_(none)_". -->

### C{n}: {unit}.{field} — {DRIFT|FABRICATED}
- **Doc**: `{doc_location}`
- **Doc says**: "{doc_says}"
- **Code reality**: `{evidence_line}` — {code_reality}
- **Verdict**: {DRIFT|FABRICATED} · **Severity**: {critical} ({domain}) · **Confidence**: {EXTRACTED:0.9} · **Adjudicated**: yes

---

## Warning — Coverage gaps (MISSING) / UNVERIFIABLE

<!-- One subsection per warning finding. If none: "_(none)_". -->

### W{n}: {unit}.{behavior} — MISSING
- **Code**: `{evidence_line}` — {code_reality}
- **Materiality**: {why documentation-worthy — route / data mutation / external side-effect / output sub-field}
- **Verdict**: MISSING · **Severity**: warning · **Confidence**: {EXTRACTED:0.9}

### W{n}: {unit}.{field} — UNVERIFIABLE
- **Doc**: `{doc_location}`
- **Reason**: {no citation | unreadable/encoding | stale anchor | dead/unreachable code}
- **Verdict**: UNVERIFIABLE · **Severity**: warning

---

## Verified (MATCH)

<!-- ONE LINE per matched claim, rolled up like rebuild-spec "Passed Checks". No prose. -->
✓ {unit}.{field} @ {unit}
✓ {unit}.routes @ F001..F030 (30/30)

---

## Metrics

| Metric | Value |
|--------|-------|
| Features audited | {N} |
| Claims checked | {C} |
| Parity score | {parity_score}% |
| Critical (DRIFT+FABRICATED) | {drift+fabricated} |
| Warnings (MISSING+UNVERIFIABLE) | {missing+unverifiable} |
