# Verdict Taxonomy — `audit-doc-parity`

The structured field-level diff (regen JSON ↔ doc JSON) assigns exactly one verdict per compared
field. Severity is **blast radius**, not phrasing. These five verdicts are the report's vocabulary.

## The five verdicts

| Verdict | Fires when | Direction | Default severity |
|---------|-----------|-----------|------------------|
| **MATCH** | Doc field and regen field agree on the behavior | doc ≡ code | — (rolled up) |
| **DRIFT** | Doc asserts a value; regen asserts a *different* value | doc ≠ code | **critical** |
| **FABRICATED** | Doc asserts a behavior; regen has *no* corresponding code basis | doc → ∅ | **critical** |
| **MISSING** | Regen asserts a documentation-worthy behavior the doc omits | code → ∅ | warning |
| **UNVERIFIABLE** | No citation, unreadable/encoding-ambiguous source, stale anchor, or dead/unreachable code | — | warning |

- **DRIFT vs FABRICATED:** DRIFT means the code *does* something here, just not what the doc says
  (wrong auth role, wrong validation rule). FABRICATED means the doc invents a behavior with no code
  at the cited location at all. Both are doc-lies → critical.
- **MISSING** is gated by the materiality filter (`materiality-filter.md`) — only documentation-worthy
  behavior. Field-level MISSING fires when a documented operation under-describes a *provably
  extractable* output contract (see materiality-filter § Output contracts).
- **UNVERIFIABLE** is the safe sink for every ambiguity (Iron Law DON'T). It NEVER becomes a false
  DRIFT/MISSING. See `legacy-considerations.md`.

## Severity rubric (blast radius)

| Severity | Domain of the drifted/fabricated field |
|----------|----------------------------------------|
| **critical** | auth / permissions / data mutation / security / money / external side-effect with payload |
| **warning** | descriptive, cosmetic, non-security metadata, coverage gap (MISSING), unverifiable |

Severity is independent of confidence: a high-confidence cosmetic drift is still a warning; a
medium-confidence auth drift is still critical (and the adjudication tie-break decides whether it
survives at all).

## Confidence

Every finding carries a `confidence` tag from the [`confidence`](../../confidence/SKILL.md) taxonomy:
`[EXTRACTED:0.9-1.0]` (read straight from code), `[INFERRED:0.5-0.89]` (deduced), `[AMBIGUOUS:0.0-0.49]`
(uncertain). A verdict whose confidence falls below the floor (`< 0.5`) does NOT assert DRIFT/MISSING —
it degrades to UNVERIFIABLE (see pipeline § confidence floor).

## parity_score

```
parity_score = match / (match + drift + fabricated)
```

- Counts **verifiable** claims only — UNVERIFIABLE and MISSING are excluded from the denominator so
  the number stays honest (an undocumented behavior is not a doc *lie*; an unreadable citation is not
  evidence of accuracy either).
- Range `0.0`–`1.0`; `1.0` = every verifiable doc claim matched code.

## result

```
result: PASS  iff  drift == 0 && fabricated == 0
result: FAIL  otherwise
```

MISSING and UNVERIFIABLE do **not** flip `result` to FAIL on their own — they are warnings a human
weighs. Only a doc that *lies* (DRIFT/FABRICATED) fails parity. This makes the frontmatter a clean
machine gate: a consumer (rebuild-spec W9, CI) branches on `result` + the `drift`/`fabricated` counts.
