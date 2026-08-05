# Adjudication Protocol — `audit-doc-parity`

The blind-regen → diff pass is the *primary* judgment, made without anchoring. But the regen agent can
hallucinate (assert a behavior the code does not have) — that would surface as a false DRIFT/FABRICATED.
Adjudication is the **backstop**: one focused pass, on flagged items only, that re-reads BOTH the doc
and the code to confirm a *real* divergence before it is finalized.

> Iron Law #3: NEVER finalize a DRIFT/FABRICATED verdict without the adjudication tie-break.
> **Anchoring is confined HERE — to tie-breaks only — never the primary judgment.**

## When it runs

- On every flagged **DRIFT** and **FABRICATED** (the critical, doc-lies verdicts).
- NOT on MATCH (nothing to confirm), NOT on MISSING/UNVERIFIABLE (warnings; a tie-break would only add
  cost — MISSING is already materiality-gated, UNVERIFIABLE is already the safe sink).
- At `--level high`, also spot-check a sample of MATCH (catch a regen that rubber-stamped).
- At `--level max`, run two independent adjudication passes; disagreement → degrade to UNVERIFIABLE.

## The adjudication pass

For each flagged item, one agent receives **both sides** and answers a single question:

```
A field-level diff flagged a potential {DRIFT|FABRICATED}. Confirm whether this is a REAL divergence
or an artifact of wording / a regen miss.

## Doc says ({doc_path}:{line})
{doc field value}

## Code at {evidence_path}:{range}
{code text}

## Regen described
{regen field value}

Decide:
- CONFIRM  — the code genuinely does NOT match the doc claim (real DRIFT/FABRICATED). Quote the code line that proves it.
- REFUTE   — the divergence is wording-only, a synonym, or the regen missed/misread the code. The doc is actually correct.
- DEGRADE  — you cannot tell from the code alone (stale anchor, dead code, ambiguous) → UNVERIFIABLE.

Return JSON: { "decision": "CONFIRM|REFUTE|DEGRADE", "evidence_line": "path:N", "reason": "<one line>", "confidence": <0-1> }.
Default to DEGRADE over CONFIRM when uncertain — a parity tool dies on its first wrong finding.
```

## Resolution

| Adjudication decision | Final verdict |
|-----------------------|---------------|
| CONFIRM | the flagged DRIFT/FABRICATED stands (with the adjudicator's evidence line) |
| REFUTE | reclassify to **MATCH** (the regen erred, not the doc) |
| DEGRADE | reclassify to **UNVERIFIABLE** |
| confidence `< 0.5` on a CONFIRM | degrade to UNVERIFIABLE (confidence floor) |

A DRIFT/FABRICATED that has NOT passed adjudication MUST NOT appear in the report as critical — it is
either confirmed, refuted to MATCH, or degraded to UNVERIFIABLE. This is what keeps the false-finding
rate controlled (design § Success Criteria) and what separates this skill from a noisier first-pass diff.
