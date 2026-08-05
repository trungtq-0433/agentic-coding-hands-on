# Improvement Proposal — {PROJECT_NAME}

_Generated {ISO_DATE}. Use context: **{internal|hybrid|customer-facing}**. Based on repository analysis._

## Technical

### {Aspect Title #1} · {N} items · max={high|medium} · effort={range}
<!-- aspect-id: {slug} -->

#### {Short title of technical item #1}

- **Value:** {high | medium}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {no | very-low | low | medium | high}

#### {Short title of technical item #2}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

### {Aspect Title #2} · {N} items · max={high|medium} · effort={range}
<!-- aspect-id: {slug} -->

#### {Short title of technical item #1}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

<!-- … all surviving aspect sections (H2 → H3) and items (H3 → H4) demoted by the Step 5a combine script (`scripts/combine_proposals.py`) … -->

## Business

<!-- The `## Business` section is OMITTED entirely when no business proposal exists
     (non-SDD repo or business track BLOCKED). When omitted, the dedup marker below
     is written as `<!-- dedup: applied (n=0) -->` directly (no dedup agent runs). -->

### {Aspect Title #1} · {N} items · max={high|medium} · effort={range}
<!-- aspect-id: {slug} -->

#### {Short title of business item #1}

- **Value:** {high | medium}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {no | very-low | low | medium | high}

#### {Short title of business item #2}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

### {Aspect Title #2} · {N} items · max={high|medium} · effort={range}
<!-- aspect-id: {slug} -->

#### {Short title of business item #1}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

<!-- … all surviving aspect sections (H2 → H3) and items (H3 → H4) demoted by the Step 5a combine script (`scripts/combine_proposals.py`) … -->

<!-- ============================================================
     EMPTY-SECTION FALLBACK (after Step 5b dedup)
     ============================================================
     If a section ends up with zero items after dedup/reclassify, REPLACE every `### <Aspect>`
     block in that section with the single placeholder line:

       Technical empty → `_All technical items were covered by the Business section via cross-track dedup._`
       Business  empty → `_All business items were covered by the Technical section via cross-track dedup._`
-->

<!-- dedup: pending -->
<!-- Dedup marker semantics + schema rules: see references/combine-proposals.md and references/dedup.md. -->
