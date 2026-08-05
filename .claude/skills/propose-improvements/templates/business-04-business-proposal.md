# Business Proposal — {PRODUCT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from improvement artifact; combiner Step 5a parses for cross-track consistency. -->

_{tagline — vocabulary gated by use-context; see template footer rules below}_

## {Aspect Title #1} · {N} items · max={high|medium} · effort={<min>|<min>–<max>}
<!-- aspect-id: {slug} -->

### {Short title of item #1}

- **Value:** {high | medium — copied verbatim from the improvement file; `low` items are filtered out by Step 3.4}
- **Need:** {business gap + concrete evidence: spec ID, market signal, competitor reference, or direct quote from the improvement file}
- **Benefits:** {customer-facing value tied to a real outcome — vocabulary gated by use-context, see footer; 1-3 sentences}
- **Proposed solution:** {product-level change, consistent with the spec's feature vocabulary; names the concrete addition/modification; 1-3 sentences}
- **Engineering effort hint:** {no | very-low | low | medium | high — copied verbatim from the improvement file}

### {Short title of item #2}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

## {Aspect Title #2} · {N} items · max={high|medium} · effort={…}
<!-- aspect-id: {slug} -->

### {Short title of item #1}

- **Value:** {…}
- **Need:** {…}
- **Benefits:** {…}
- **Proposed solution:** {…}
- **Engineering effort hint:** {…}

<!-- … one ## block per aspect with ≥1 surviving high/medium entry; aspects with zero entries omitted.
     Cross-aspect order = ascending NN- prefix from source aspect filename in 03-improvement/.
     Within-aspect order = Value desc → Engineering effort hint asc → source order tiebreak. -->

<!-- ============================================================
     ZERO-ITEM FALLBACK
     ============================================================
     If ZERO items survived selection (no aspect has any high/medium entry), REPLACE every
     `## <Aspect Title>` block above with the single line below (still preceded by the
     `**Use context:**` marker line):

         _No critical business improvements identified at this time._

     This unusual output is the correct output — do not fabricate items to fill the slot. -->

<!-- ============================================================
     SCHEMA RULES (MANDATORY)
     ============================================================
     - One `##` block per **aspect group**, one `### ` block per item within.
     - Aspect rollup heading format: `## <Aspect Title> · <N> items · max=<high|medium> · effort=<min>|<min>–<max>`.
       N = count of surviving items in this aspect. max = high if any item is high, else medium.
       effort = min(efforts)–max(efforts) over surviving items (no<very-low<low<medium<high); single value when min==max.
     - Immediately after each `## ` heading, emit `<!-- aspect-id: <slug> -->` on its own line.
       The slug is the aspect-id value (sanitised to `^[a-z0-9-]+$`) — machine-parsed by
       combine / dedup / validation.
     - Each item has FIVE bullets in EXACT order: Value, Need, Benefits, Proposed solution, Engineering effort hint.
     - No extra bullets ("Timeline:", "Effort:", "Price:", "Next steps:", "Category:" etc.).
       `**Category:**` is no longer emitted — aspect-id is propagated via the `<!-- aspect-id: <slug> -->`
       comment under each `## ` heading.
     - `**Value:**` and the aspect-id comment are machine-parsed by combine / dedup / validation.
     - The `**Use context:** <value>` line MUST appear directly under the H1.
     - Project name = the one used in the improvement file.
     - Cross-aspect order = ascending NN- prefix from source aspect filename in 03-improvement/.
       Within-aspect order = Value desc → Engineering effort hint asc → source order tiebreak. -->

<!-- ============================================================
     TAGLINE + BENEFITS VOCABULARY BY USE-CONTEXT
     ============================================================
     internal:
       Tagline: _Spec-driven analysis distilled to the <N> highest-value internal-product improvements for this customer._
       Benefits vocabulary: operational efficiency | risk reduction | compliance | employee productivity |
                            platform capability | time-to-market for dependent teams
       NO item may propose monetization, pricing, or tiering changes.

     hybrid:
       Tagline: _Spec-driven analysis distilled to the <N> highest-value enterprise / partner / self-host improvements for this customer._
       Benefits vocabulary: enterprise deal-size unlock | partner-adoption expansion | self-host packaging |
                            differentiation | compliance | operational efficiency | platform capability
       NO item may target mass-market consumer funnels.
       Enterprise / self-host / partner monetization items ARE allowed.

     customer-facing:
       Tagline: _Spec-driven analysis distilled to the <N> highest-value business improvements for this customer._
       Benefits vocabulary (full): revenue | retention | conversion | differentiation | compliance |
                                   deal-size unlock | churn reduction
-->
