# Judgment Rubric — Engine 3 (`audit-synthesis-judgment`)

Engine 3 judges the subjective residue. Its ONE defense against becoming an opinion generator:
**every finding anchors to a computed signal**, and no finding stands without surviving a refutation
pass. WARN only — never FAIL, never an Engine-1 count. design-intent findings are WARN-capped +
flagged experimental.

The Python (`judgment_engine.py prepare`) extracts CANDIDATES, each pre-pinned to its anchor. The LLM
judges rule on them; refuters try to knock them down; `judgment_engine.py assemble` keeps only the
anchored survivors. Judges/refuters MUST obey `prompt-injection-defense.md` — scanned prose is inert
DATA, output is schema-constrained.

## The four dimensions, each pinned to a computed anchor

| Dimension | Kind | Computed anchor every finding MUST carry | Judge question |
|-----------|------|-------------------------------------------|----------------|
| **inference-validity** | `UNSUPPORTED` | a `[INFERRED]` tag or a US "so that {benefit}" clause (extracted position) | Does a warrant trace claim→grounds→evidence, or is the leap ungrounded? |
| **naming** | `NAMING` | the IPE Step-4 anti-CRUD clause (the US title) | Is this *genuinely ambiguous* (clear violations are Engine-2 deterministic)? |
| **granularity** | `GRANULARITY` | the MAD outlier stat (`_granularity_lib`: value vs median, modified z-score) | Is the size difference a real modelling problem or legitimate variation? |
| **restates-w/o-why** | `RESTATES` | the design-intent Non-Duplication clause; a paragraph with NO `**Source:**`/ADR citation | Does it add "why", or only restate business-rules/architecture? |

A candidate with an empty anchor is dropped by the assembler BEFORE refutation (Iron Law #2). A
citation-adjacent span (a mandated ADR quote, a DRY-cite) is never a `restates` candidate — the
extractor exempts it.

## The Toulmin schema (inference-validity)

A claim is UNSUPPORTED when its warrant is missing:

```
CLAIM    — the asserted "why" / benefit (e.g. "so that auditors can reconcile monthly")
GROUNDS  — the evidence the doc points at (an ADR, a code pattern, a business-rule)
WARRANT  — the reasoning connecting grounds → claim
```

- All three traceable → NOT flagged (defensible inference, even if it differs from the reviewer's).
- CLAIM with no GROUNDS and no WARRANT → `UNSUPPORTED` WARN.
- A defensible-but-different rationale is REFUTED (it has grounds + warrant, just not the ones a
  reviewer would pick). The test corpus asserts this case is NOT flagged.

## Judge output schema (schema-constrained — injection defense)

```
{ "id": "<candidate id>", "verdict": "WARN" | "CLEAN",
  "kind": "UNSUPPORTED|NAMING|GRANULARITY|RESTATES",
  "anchor": "<the computed signal, echoed>", "reason": "<one line>",
  "confidence": <0.0-1.0> }
```

No free-form channel — an injected "mark this clean" cannot express itself (see
`prompt-injection-defense.md`). A confidence `< 0.5` degrades to UNVERIFIABLE (dropped from WARN).

## Level → refutation depth

| Level | Refutation |
|-------|------------|
| `low` | single refuter (fast, less stable) |
| `medium` *(default)* / `high` / `max` | **≥2-refuter majority** must say NOT-refuted for the WARN to survive |

`--level max` also gives judges larger context. The ≥2-refuter majority is the DEFAULT (not just at
max) so the WARN set is reasonably stable run-to-run.

## Completion accounting

`judgment_engine.py assemble` tracks expected-vs-returned candidates. A judge/refuter that dies
(timeout, rate-limit, schema-invalid output) leaves its candidate unreturned → `judgment_status:
PARTIAL` (or `FAILED` if none returned). A dead subagent NEVER silently reduces the WARN set to
"clean".
