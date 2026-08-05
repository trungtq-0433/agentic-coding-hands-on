<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Design Intent

**Project**: {PROJECT_NAME}
**Generated**: {DATE}
**Status**: EXPERIMENTAL — report-only (see disclaimer below)

<!-- disclaimer:start -->
> **⚠ EXPERIMENTAL — read before trusting anything below.**
>
> This document infers "why the system was built this way" — architecture choices, patterns,
> and trade-offs — from ADRs (when present), curated docs, and source-code patterns. This is
> the highest-hallucination-risk artifact this skill produces: "why" claims are inherently more
> inferential than the structural "what" claims in every other artifact.
>
> - Every claim below either cites its source (`ADR-###`, `business-rules.md`,
>   `architecture.md`, or a `file:line`) or is tagged **`[INFERRED]`** with a one-line reason.
>   An uncited, untagged assertion is a contract defect, not an acceptable shortcut.
> - This report is written to the **plan directory only** on first generation. It is
>   **NOT auto-promoted** to `docs/system/design-intent.md` — promotion happens only after a
>   human explicitly confirms the content is accurate and useful (see the pass's completion
>   handoff). Treat every reading of this file as a DRAFT until that confirmation has happened.
> - Graduation from EXPERIMENTAL to default-promote requires a pilot across 3 repos of
>   differing stacks with `[INFERRED]` ≤25%, zero fabricated citations, and human confirmation —
>   see `CHANGELOG.md` v26.1.0 sub-entry 3 for the full criteria. Until then, treat this
>   artifact as advisory, not authoritative.
<!-- disclaimer:end -->

**Non-duplication boundary**: this file holds ONLY cross-cutting **architectural rationale** —
the "why" behind a choice spanning multiple rules/entities/layers. It does not restate
`business-rules.md`'s per-rule As-Is/To-Be content or `architecture.md`'s structure/stack
description — it may cite either, never re-narrate them.

---

## Architecture Choices

{One subsection per major architectural choice (e.g. "Why event-driven for order processing",
"Why soft-delete instead of hard-delete"). Each claim cites an ADR / business-rules.md /
architecture.md / file:line, OR is tagged [INFERRED] with a one-clause reason.}

### {Choice Name}

{1-2 paragraph rationale. Example citation shapes:
- "Per ADR-003 (`docs/decisions/ADR-003-event-driven-orders.md`), ..."
- "The repeated soft-delete column (`deleted_at`) across 6 models (e.g. `app/models/order.rb:4`)
  suggests [INFERRED] — no ADR or comment found — that hard deletes were avoided to preserve
  audit history."}

---

## Patterns & Trade-offs

{Cross-cutting patterns detected in source (CQRS, event-sourcing, config-driven feature flags,
etc.) and the trade-off they represent. Same citation-or-[INFERRED] discipline.}

---

## [INFERRED] Appendix

{Roll-up list of every [INFERRED]-tagged claim above, for quick scan. One line each:
"- [INFERRED] <claim> — <reasoning> (see § <section>)"}

---

## Open Questions

{Anything the researcher could not resolve — a pattern with no clear rationale, an apparent
ADR/code divergence, insufficient signal to say anything beyond "no distinctive architectural
choice detected for X". An honest "not enough signal" note is REQUIRED over fabricated narrative.}

---

## Handoff Summary

- **ADR-citation ratio**: {N}/{M} claims cite an ADR directly; the rest cite business-rules.md,
  architecture.md, a file:line, or are `[INFERRED]`.
- **[INFERRED] ratio**: {P}% of claims are `[INFERRED]` (no ADR/docs/code citation available).
- **Zero-signal note**: {state explicitly if this repo had no ADRs and few distinctive patterns
  — do not pad the file to look substantive.}
