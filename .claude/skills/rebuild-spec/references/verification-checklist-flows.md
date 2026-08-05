<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Verification Checklist: ProcessFlow (--flows pass, FL.3)
<!-- Created: Phase-02 strip — carved from verification-checklist-core-artifacts.md § ProcessFlow -->
See verification-checklist-universal.md for Universal rules and Pending Marker Rule.

**Scope:** Loaded ONLY by the `--flows` pass reviewer (FL.3). Do NOT load in the default (core) W7a run.

## ProcessFlow

**Cross-refs:** `docs/generated/entities.md` (entity state fields, enums), `docs/system/business-rules.md` (scheduled jobs), `docs/features/*/technical-spec.md` (SM-### blocks)

**Deterministic checks (FL.2 `validate_process_flow.py` — pre-FL.3):** citation presence per transition row, FLOW### regex + uniqueness, state-in-enum-or-derived, `.completed` marker, strict gate (>=2 transitions AND >=2 trigger types), `possible_stuck_state` (liveness backstop, warning), `sm_crossref_missing` (SM/FLOW DRY, warning), `SystemFlow.composes_missing`, `SystemFlow.composes_insufficient`, `SystemFlow.handoffs_missing`, `SystemFlow.handoff_citation_missing`, `SystemFlow.inventory_missing`, `SystemFlow.inventory_incomplete`, `SystemFlow.phantom_flow_ref`. Rule IDs passing FL.2 are marked `[deterministic-pass]` — skip in semantic review.

**Semantic review rules (PF-S1..PF-S6):**
- [ ] **PF-S1 Citation accuracy (spot-check):** for >=2 transitions per flow, Read the cited `file:line` and verify the code actually contains the transition logic (guard, state mutation, job dispatch). Cited line is a comment or unrelated code → critical.
- [ ] **PF-S2 No fabricated/derived-as-stored states:** cross-check `## States` table against `docs/generated/entities.md` entity definition. A state listed as stored that does not appear as a DB column/enum value → critical (fabricated state). A dashboard display label (computed in a helper/view) modeled as a stored state → critical.
- [ ] **PF-S3 Strict gate respected:** if a flow file exists with < 2 transitions OR < 2 distinct trigger types (user-action, scheduled, event, derived), it should have been hard-omitted → critical. Exception: files with `depth: thin` in frontmatter are allowed if they contain Guard & Cascade Rules table instead of Transitions.
- [ ] **PF-S4 Cross-flow handoff verification (system-flow):** FL.2 already checks citation *presence/shape* (`SystemFlow.handoff_citation_missing`). For ≥2 handoff rows, **Read the cited `file:line` and confirm the code contains the handoff logic** (same obligation as PF-S1 for Tier-1 transitions). Then verify *plausibility* — timing assertions (e.g. 'X does not wait for Y') must be verifiable from code or moved to Open Questions. Additionally, for each `SystemFlow.inventory_incomplete` warning, confirm it is a formatting false-positive (e.g. entity-prefixed field name) and document the match — do NOT dismiss unchecked (Finding 5/SI-5).
- [ ] **PF-S5 Liveness:** for each `possible_stuck_state` warning, confirm the state either carries a `LIVENESS:` note in Open Questions (entry trigger + missing/unsafe exit) or is genuinely terminal (then mark it terminal in the States prose to clear the warning). A non-terminal automated state with a fallible/unconditional exit and no note → flag.
- [ ] **PF-S6 SM cross-ref:** for each `sm_crossref_missing` warning, confirm the flow either adds the `see SM-### in F###` reference and trims the duplicated transition table, or the overlap is a genuine false match (different entity sharing generic state names) — document which.

**Critical edge cases:**
- Transition row without `file:line` citation → critical (contract violation)
- FLOW### code not matching `^FLOW\d{3}_[A-Za-z0-9]+$` → critical
- Duplicate FLOW### code across flow files → critical
- Derived view (computed at read-time) modeled as stored state → critical (fabricated state)
- Sub-threshold flow present (fails >=2-transitions-AND->=2-trigger-types gate) → critical
- `.completed` marker absent after FL.1 → warning

**Advisory (non-defect):** `confidence-report_<slug>.md` beside a promoted flow file is an
optional, best-effort sidecar (`scripts/derive_confidence_report.py`, v25.2.0). Its absence is
NOT a defect — do NOT flag a missing companion as a review finding. See
`references/confidence-report-contract.md`.

## Failure Trap Assertions (ProcessFlow-specific)

- **Trap 5 (fabricated process-flow states):** a state listed in `## States` that is not a DB column/enum value AND not declared in `derived_views` frontmatter → critical. Dashboard labels computed at read-time (e.g., `TrackingHelper::getTrackingFinalizing`) are views, not states. Modeling them as states fabricates a machine that does not exist in code.
