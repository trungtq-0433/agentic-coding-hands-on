# Iron Laws — `audit-doc-parity`

Each rule maps to a real failure mode — no generic platitudes. Violating a NEVER collapses
the skill back into the W7a reviewer it was built to surpass (claim-existence + wording, never
claim-truth; anchoring bias). These are inlined verbatim into SKILL.md "Critical Rules".

## 🚫 NEVER (violation → skill collapses back into W7a)

1. **NEVER** let the regen agent see the doc before re-describing the code. *(This IS the architecture — the anchoring defeat.)*
2. **NEVER** assert a regenerated behavior without a code line citation. *(Anti-hallucination pillar #1.)*
3. **NEVER** finalize a DRIFT/FABRICATED verdict without the adjudication tie-break. *(Anti-false-finding.)*
4. **NEVER** mutate doc or code — report-only (emitter, not gated consumer, like `review-code`).
5. **NEVER** emit MISSING for non-documentation-worthy code (materiality filter).
6. **NEVER** grade subjective spec depth/sufficiency. Under-detail is flagged ONLY when the missing detail is provably extractable from code (else = W7a noise).

## ⚠️ DON'T

- Don't read whole files to regen — scope to citation + enclosing block (cost).
- Don't run the default sweep without the estimate gate (step 0).
- Don't field-diff free prose — only structured-schema fields (noise).
- Don't guess the code region when a citation is absent → mark `UNVERIFIABLE` (v1).
- Don't assert DRIFT/MISSING on an ambiguous legacy signal → degrade to `UNVERIFIABLE`. A parity tool dies on its first wrong finding.

## ✅ DO

- Reuse rebuild-spec templates as the regen schema (DRY).
- Tag every finding with the `confidence` taxonomy (EXTRACTED / INFERRED / AMBIGUOUS).
- Emit machine-readable frontmatter so the report can act as an optional gate.
- Severity = blast radius (auth / data / security / money = critical; descriptive = warning).
