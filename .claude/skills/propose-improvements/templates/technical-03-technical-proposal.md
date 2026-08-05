# Technical Proposal — {PROJECT_NAME}
**Use context:** {internal|hybrid|customer-facing}
<!-- REQUIRED: copy verbatim from improvement artifact; combiner Step 5a parses for cross-track consistency. -->

_{tagline — vocabulary gated by use-context; see template footer rules below}_

## {Aspect Title #1} · {N} items · max={high|medium} · effort={<min>|<min>–<max>}
<!-- aspect-id: {slug} -->

### {Short title of item #1}

- **Value:** {high | medium — copied verbatim from the improvement file; `low` filtered out by Step 4.3}
- **Need:** {problem/gap + concrete evidence: path:line, metric, graph node ID, or direct quote from the improvement file}
- **Benefits:** {customer-facing value tied to a real signal — vocabulary gated by use-context, see footer; 1-3 sentences}
- **Proposed solution:** {technology-consistent with the detected stack; 1-3 sentences; names the concrete change (e.g., "introduce Redis-backed rate limiter in `src/api/middleware/`") not just a direction}
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
     Cross-aspect order = ascending NN- prefix from source aspect filename.
     Within-aspect order = Value desc → Engineering effort hint asc → source order tiebreak. -->

<!-- ============================================================
     ZERO-ITEM FALLBACK
     ============================================================
     If ZERO items survived selection (no aspect has any high/medium entry), REPLACE every
     `## <Aspect Title>` block above with the single line below (still preceded by the
     `**Use context:**` marker line):

         _No critical technical improvements identified at this time._

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
     - No extra bullets ("Notes:", "Next steps:", "Timeline:", "Category:" etc.).
       `**Category:**` is no longer emitted — aspect-id is propagated via the `<!-- aspect-id: <slug> -->`
       comment under each `## ` heading.
     - `**Value:**` and the aspect-id comment are machine-parsed by combine / dedup / validation.
     - The `**Use context:** <value>` line MUST appear directly under the H1.
     - Project name = the one used in the improvement file.
     - Cross-aspect order = ascending NN- prefix from source aspect filename.
       Within-aspect order = Value desc → Engineering effort hint asc → source order tiebreak. -->

<!-- ============================================================
     TAGLINE + BENEFITS VOCABULARY BY USE-CONTEXT
     ============================================================
     internal:
       Tagline: _Repository analysis distilled to the <N> highest-leverage internal-platform improvements for this customer._
       Benefits vocabulary: reliability | operational efficiency | risk reduction | compliance |
                            employee productivity | platform capability |
                            time-to-market for dependent teams
       NO item may propose public-API productization, SDK distribution, marketplace listings,
       or consumer funnel changes.

     hybrid:
       Tagline: _Repository analysis distilled to the <N> highest-leverage enterprise / partner / self-host technical improvements for this customer._
       Benefits vocabulary: reliability | enterprise deal-size unlock | partner-adoption expansion |
                            self-host packaging | differentiation | compliance |
                            operational efficiency | platform capability
       Items may target enterprise hardening, partner API, self-host tooling.
       Items may NOT target consumer-tier funnels.

     customer-facing:
       Tagline: _Repository analysis distilled to the <N> highest-leverage technical improvements for this customer._
       Benefits vocabulary (full): reliability | speed | cost | compliance | time-to-market |
                                   retention | revenue | differentiation
-->
