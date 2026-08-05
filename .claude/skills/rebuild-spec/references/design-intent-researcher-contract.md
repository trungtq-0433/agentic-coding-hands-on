# Design-Intent Researcher Contract (Wave D.1 — rebuild-spec v26.1.0, EXPERIMENTAL)

## EXPERIMENTAL status (F11)

This pass ships EXPERIMENTAL/report-only. Do not treat this contract's citation discipline as
optional polish — it is the reason the pass is allowed to exist at all. See
`references/pipeline-design-intent.md` § EXPERIMENTAL status for the full graduation contract.

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other read.
Do NOT re-derive information already present there.

## Synthesis Sources — READ IN THIS ORDER (highest-trust first)

1. **`docs/decisions/ADR-*.md`** — human-authored, HIGHEST TRUST. Quote directly (short
   verbatim excerpt + citation to the ADR filename). NEVER override, contradict, or
   "improve on" an ADR's stated rationale — if the code appears to diverge from an ADR, note
   the divergence as an `[INFERRED]` observation, do not silently pick a side.
2. **`docs/system/architecture.md`** + **`docs/system/business-rules.md`** — already-promoted
   curated narratives. As-Is/To-Be sections in business-rules.md already capture some rationale;
   architecture.md's tech-stack/layer choices are a citable source for "why this stack".
3. **Source code** — AUTHORIZED for cross-cutting architectural pattern detection (grep for
   idioms: CQRS, event-sourcing, soft-delete, feature flags, config-driven behavior switches).
   Cite `file:line` for every pattern claim.
4. **`docs/features/*/business-context.md`** — optional enrichment. Per-feature "why" prose
   already synthesized; roll up recurring cross-feature themes, cite the source feature file.

`docs/generated/entities.md` may be read for vocabulary (entity/field names) but is not itself a
citation source for "why" claims — it describes structure, not rationale.

## Citation-or-[INFERRED] Gate (STRICT — load-bearing, not optional)

Every claim in the output MUST carry ONE of:
- An ADR citation (`ADR-###` filename reference, ideally with a short direct quote).
- A `business-rules.md` or `architecture.md` citation (section/heading reference).
- A `file:line` code citation (concrete pattern evidence).
- OR be tagged `[INFERRED]` with a one-clause reasoning note explaining WHY it's inferred
  (e.g. "[INFERRED] — no ADR or comment found; inferred from the repeated soft-delete column
  pattern across 6 models").

An assertion with NONE of the above is a contract violation — `validate_design_intent_density.py`
(Wave D.2) gates this deterministically and will FAIL the pass. This mirrors the RE-mode
`[UNVERIFIED]` discipline in `references/re-output-contract.md`, loosened because "why" claims
are inherently more inferential than RE-mode's structural claims — inference is allowed, silent
assertion is not.

## ADR-Graceful Degradation

ADRs are rare and optional (human-authored, most repos have none). When absent, lean more on
source-code pattern inference — this legitimately RAISES the `[INFERRED]` ratio; do not manufacture
a citation to avoid it. Surface the resulting ratio in the handoff (see pipeline file), e.g.
"3/18 claims cite an ADR; the rest are code-pattern or business-rules.md inferences."

## Non-Duplication Boundary (DRY — vs business-rules.md and architecture.md)

`design-intent.md` is the ONLY place for cross-cutting **architectural rationale** — the "why"
behind a choice that spans multiple rules/entities/layers. It must NOT re-narrate:
- `business-rules.md`'s per-rule As-Is/To-Be content (that stays there — this file may CITE it,
  never restate it).
- `architecture.md`'s structure/stack description (that stays there — this file may reference a
  named layer/component, never re-describe its shape).

A paragraph that only restates an existing artifact's content with no added "why" is a DRY
violation — the reviewer (Wave D.3) flags it against `verification-checklist-design-intent.md`.

## Output

Single file: `plans/<active>/artifacts/design-intent.md`. Template:
`templates/design-intent-template.md` (opens with the EXPERIMENTAL disclaimer banner, F11a — do
NOT remove or shrink it).

No fan-out (`--design-intent` is single-file synthesis, mirrors the GL.1 glossary shape — a small
artifact built on one coherent, cross-cutting judgment call, not something that benefits from
splitting across researchers). Zero-signal repos (no ADRs, no distinctive patterns beyond generic
CRUD) still emit the file with an honest `## Open Questions` note — never fabricate architectural
narrative to fill the file.

### Confidence Companion (advisory sidecar — only after promotion)

`confidence-report_design-intent.md` is NOT part of the researcher's output above. If/when this
artifact is later promoted (post user-confirmation, F11b), `scripts/derive_confidence_report.py`
emits the sidecar automatically — deterministic, never gated. See
`references/confidence-report-contract.md`.

## Completion Marker

After the file is fully written, write:

```
plans/<active>/artifacts/.design-intent.completed
```

## See Also

- `references/pipeline-design-intent.md` — the 3-wave pass body (D.1–D.4)
- `references/re-output-contract.md` — the citation/`[UNVERIFIED]` discipline this mirrors
- `templates/design-intent-template.md` — output template + disclaimer banner
- `scripts/validate_design_intent_density.py` — Wave D.2 deterministic gate (F11c)
