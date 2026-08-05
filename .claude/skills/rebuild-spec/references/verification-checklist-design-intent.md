<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: Design Intent (`--design-intent` pass, D.3, EXPERIMENTAL)

See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the `--design-intent` pass reviewer (D.3). Do NOT load in the default
(core) W7a run.

## DesignIntent

**Cross-refs:** `docs/decisions/ADR-*.md` (highest-trust, human-authored), `docs/system/
architecture.md`, `docs/system/business-rules.md`, `docs/features/*/business-context.md`.

**Deterministic checks (D.2 `validate_design_intent_density.py` — pre-D.3):** paragraph-level
citation-or-`[INFERRED]` density scan (mode-agnostic — always runs, not RE-mode-gated), skipping
the EXPERIMENTAL disclaimer banner, fenced code, headings, and tables. Rule IDs passing D.2 are
marked `[deterministic-pass]` — skip in semantic review.

**Semantic review rules (DI-S1..DI-S6):**
- [ ] **DI-S1 Citation accuracy (spot-check):** for >=2 cited claims, Read the cited ADR /
  `business-rules.md` section / `architecture.md` section / `file:line` and verify it actually
  supports the claim made. A citation that does not support its claim → critical.
- [ ] **DI-S2 `[INFERRED]` reasoning present:** every `[INFERRED]`-tagged claim carries an actual
  one-clause reasoning, not a bare tag. A bare `[INFERRED]` with no "why inferred" clause →
  critical.
- [ ] **DI-S3 ADR never contradicted:** no claim overrides, contradicts, or "improves on" a
  quoted ADR's stated rationale. A code-vs-ADR divergence must be noted as an observation, not
  silently resolved in the code's favor → critical if the ADR's position is silently dropped.
- [ ] **DI-S4 DRY — no re-narration:** `## Architecture Choices` / `## Patterns & Trade-offs`
  must not be a restatement of `business-rules.md`'s As-Is/To-Be prose or `architecture.md`'s
  structure description with no added "why". A paragraph that only restates existing content →
  critical (DRY violation, non-duplication boundary).
- [ ] **DI-S5 Disclaimer banner intact (F11a):** the EXPERIMENTAL disclaimer banner at the top
  of the file is present, unmodified in substance, and wrapped in the
  `<!-- disclaimer:start -->` / `<!-- disclaimer:end -->` markers the density validator relies on
  to skip it. A removed or shrunk banner → critical.
- [ ] **DI-S6 No fabricated zero-signal narrative:** when the codebase genuinely has few
  distinctive architectural patterns and no ADRs, the artifact says so plainly (Open Questions /
  zero-signal note) rather than padding with generic, could-apply-to-any-codebase prose. Generic
  filler presented as specific insight → critical.

**Critical edge cases:**
- Any prose paragraph (≥12 words, outside the disclaimer/fences/headings/tables) with zero
  citation AND no `[INFERRED]` tag → critical (D.2 hard gate).
- `.design-intent.completed` marker absent after D.1 → warning.
- Disclaimer banner missing or its HTML-comment markers altered → critical (DI-S5).

**Advisory (non-defect):** `confidence-report_design-intent.md` is an optional, best-effort
sidecar emitted ONLY after promotion (`scripts/derive_confidence_report.py`), not part of the
plan-dir draft. Its absence pre-promotion is NOT a defect — do not flag it.

**Report-only status (F11b — do not flag as a defect):** this artifact intentionally stops at
the plan directory and is NOT copied to `docs/system/design-intent.md` by this pass's own D.4
wave. That is the correct, designed behavior — do not treat "not yet in docs/" as a missing
output. Promotion happens only via an explicit, separately-confirmed follow-up step.

## Failure Trap Assertions (DesignIntent-specific)

- **Trap — silent ADR override:** a claim that quietly adopts the code's apparent behavior over
  an ADR's stated rationale, with no divergence noted, looks like a well-cited claim but is
  actually suppressing the higher-trust source → critical.
- **Trap — inference laundering:** a claim citing a `file:line` that shows a generic pattern
  (e.g. any `has_many` association) as if it were evidence of a deliberate architectural choice,
  when the citation doesn't actually support "why" — only "what exists" → critical (DI-S1).
