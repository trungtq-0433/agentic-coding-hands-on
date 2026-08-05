# Answer Synthesis, Citation & Degradation

Turn routed evidence (from [`question-routing.md`](./question-routing.md)) into a trustworthy,
cited answer. Trust comes from **citation** — every claim points to its source so a BrSE/PM can
verify. This is the difference between this engine and a generic LLM guess.

## Citation Convention

> **Docs root is mode-aware** — see [`_shared/docs-canonical-mapping.md` § Language Layout](../../_shared/docs-canonical-mapping.md#language-layout) (single-lang → `docs/` root; per-lang → `docs/<primary>/`). Example paths below use `docs/` root (single-lang; common case).

<!-- layout-exempt: example citation paths below use docs/ root (single-lang; mode-aware pointer above) -->
- Cite inline at the point of claim: `… supports CSV export [docs/features/export/technical-spec.md].`
- Only cite files confirmed **PRESENT** by discovery. Never cite a path you did not actually read.
- Close every answer with a `## Sources` block:

  <!-- layout-exempt: Sources block example — shows docs/ root paths as citation examples (single-lang mode) -->
  ```
  ## Sources
  - docs/generated/feature-list.md (Specs layer)
  - docs/system-architecture.md (Docs layer)
  - Layers absent: Improvement Proposals (run /tkm:propose-improvements for opportunity analysis)
  ```

- For inferred claims (not directly stated in an artifact), tag with the
  [`confidence`](../../confidence/SKILL.md) taxonomy, e.g. `[INFERRED:0.6]`. Use sparingly —
  do not tag obvious facts.

## Answer-Mode Renderers

**Structured list** (feature list, improvement opportunities)
> One-paragraph summary, then a bullet/table list. Each item ends with its source.
> <!-- layout-exempt: example output block — paths are illustrative citations (single-lang mode) -->
> ```
> This product is a B2B invoicing platform. Core features:
> - Invoice generation — recurring + one-off [docs/generated/feature-list.md]
> - Payment reconciliation via Sepay webhook [docs/features/payments/technical-spec.md]
> ```

**Prose + diagram** (architecture, "draw the system")
> Narrative overview, then a fenced ` ```mermaid ` block built from structural evidence
> (`entities.md`, `route-list.md`, `screen-flow.md`). Follow [Mermaid conventions](../../preview-output/references/mermaid/overview.md)
> v11 syntax. If structure is only inferred from code, label the diagram `(inferred from codebase)`.

**Impact three-tier** (impact analysis)
> <!-- layout-exempt: example output block — paths are illustrative citations (single-lang mode) -->
> ```
> ### Directly affected (will break / must change)
> - route POST /invoices → handler reads Invoice.status [docs/generated/route-list.md]
> ### Indirectly affected (review)
> - reconciliation job consumes Invoice.status [docs/generated/behavior-logic.md]
> ### Verify manually (low confidence)
> - 3 code refs to `invoice.status` outside specs [INFERRED:0.5]
> ```

**Spec walkthrough** (feature detail)
> Summarize `features/F###/spec.md` section by section. **Preserve the schema codes** verbatim
> (FR/BR/SM/ALG/INT/SC). For a wireframe ask, **describe** layout from screen-list / screen specs —
> do not generate UI code (read-only stance).

## Degradation Ladder

Honesty over silence. Three rungs:

| Rung | Condition | Behavior |
|---|---|---|
| **PRESENT** | needed artifact found and it answers the question | answer from it, cite it |
| **PARTIAL** | some evidence, gaps remain | answer what's covered, name the gap, cite present files |
| **INSUFFICIENT** | docs present but don't answer the question at the depth asked | **targeted** code escalation (grep the named symbol → read its enclosing block), cite the code; full scan only under `--level max`. `--level low` does not escalate (answers from docs, notes the gap). See [`retrieval-strategy.md`](./retrieval-strategy.md) § Sufficiency Self-Check |
| **ABSENT** | needed layer missing entirely | best-effort from `tkm:scan-codebase` on live code, then append the advisory |

Advisory strings (reuse from [`artifact-discovery.md`](./artifact-discovery.md) § "Absent-Layer
Advisory"): Specs→`/tkm:rebuild-spec`, Docs→`/tkm:manage-docs init`, Improvement Proposals→`/tkm:propose-improvements`,
Plans→`/tkm:create-plan`. Always phrased as an optional deepening, not a blocker.

## Level-Aware Rendering & Verify

The processing level (`--level low|medium|high|max`, default `--level medium` — see
[`retrieval-strategy.md`](./retrieval-strategy.md)) shapes how much the answer says and whether it
verifies against code:

- **`--level low`** — answer only the question's core, terse, from docs/specs. No adjacent context, no code.
- **`--level medium`** *(default)* — answer + the **related/adjacent** context the asker didn't explicitly
  ask (who uses it, what it touches), still docs-first with targeted escalation when the gate fires.
  When the answer came from specs alone, append one line:
  *"Answered from specs; run `--level high` to verify against the source code."*
- **`--level high`** — detailed; after reaching source, **note the explicit code references** inline, then
  **spot-check the key claim against the cited code**: confirm the value/behavior you stated actually
  appears in the source. Tag confirmed claims plainly; flag mismatches with the
  [`confidence`](../../confidence/SKILL.md) taxonomy (`[INFERRED:0.x]`) and say what you could not confirm.
- **`--level max`** — thorough; synthesize across the **multiple read-only sub-agents'** findings (different
  angles) and the full scan, **cross-verify every specs-derived claim** against code, and tag any
  claim that the scan could not confirm. Note conflicting evidence explicitly.

Never run a full scan on `--level low`/`--level medium`/`--level high` just to verify — only `--level max` does the full
scan; that keeps the lower levels fast.

## Visual-Answer Rule

- Architecture / "draw" intents **emit a Mermaid diagram** via `preview-output` Mermaid conventions.
- Wireframe asks are answered **descriptively** from screen specs — layout, regions, components —
  never by writing frontend code.
- A diagram built from confirmed structural artifacts is unlabeled; one inferred from raw code is
  labeled `(inferred)` and its uncertain edges tagged `[INFERRED]`.

## Read-Only Guarantee

This skill **never edits project code or files**. It discovers, reads, reasons, and answers —
optionally producing diagrams and visual explanations as *output*. The old directive "do not start
implementing anything" still holds: answers and diagrams are allowed; touching the project's source
is not. If the asker wants implementation, point them to `/tkm:takumi`.
