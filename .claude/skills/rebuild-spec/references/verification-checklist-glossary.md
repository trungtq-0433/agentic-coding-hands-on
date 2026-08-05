<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: Glossary (--glossary pass, GL.2)
<!-- Created: Phase-02 strip — GL-R1..GL-R6 carved from GL.2 inline rules in pipeline-flows-glossary.md -->
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the `--glossary` pass reviewer (GL.2). Do NOT load in the default (core) W7a run.

## Glossary

**Cross-refs:** `docs/generated/entities.md` (entity names, field names), `docs/features/*/business-context.md` (term usage)

**Semantic review rules (GL-R1..GL-R6):**
- [ ] **GL-R1 Entity coverage:** every entity in `docs/generated/entities.md` must have an entry. Missing entity → critical.
- [ ] **GL-R2 No technical jargon in definitions:** definitions must be readable by a non-developer (no raw SQL, no framework-specific terms, no internal code identifiers as the primary explanation). Jargon as the entire definition with no plain-language counterpart → warning.
- [ ] **GL-R3 No duplicated entries:** two entries for the same term (exact or near-synonym) → critical (merge or alias). Technical alias field used to point to the canonical entry is acceptable.
- [ ] **GL-R4 Term sourcing:** each term must appear in >=1 of: `docs/generated/entities.md` OR >=2 `docs/features/*/business-context.md` files. A term present in only 1 business-context with no entity counterpart → warning (candidate for removal or consolidation).
- [ ] **GL-R5 Alphabetical order:** terms not sorted alphabetically → warning. Reviewer notes first out-of-order entry.
- [ ] **GL-R6 Used-in accuracy:** F### codes listed in "Used in:" must exist in `docs/generated/feature-list.md`. Orphan F### → critical.

**Critical edge cases:**
- Glossary absent after GL.1 → critical
- Entry missing "Definition:" field → critical
- "Used in:" field contains code that is not an F### (e.g., SCR### or BL###) → warning

**Advisory (non-defect):** `confidence-report_glossary.md` beside the promoted glossary is an
optional, best-effort sidecar (`scripts/derive_confidence_report.py`, v25.2.0). Its absence is
NOT a defect — do NOT flag a missing companion as a review finding. See
`references/confidence-report-contract.md`.
