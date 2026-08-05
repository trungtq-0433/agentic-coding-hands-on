# Process-Flow Researcher Contract (Wave 6.8 — rebuild-spec v4)

## Session Context

Read `plans/<active-plan>/artifacts/_session-context.md` FIRST before any other read.
Do NOT re-derive information already present there.

## Synthesis Sources (read ALL before inferring any flows)

Read these upstream artifacts from `plans/<active>/artifacts/`:
- `data-model.md` — entity definitions, state/enum fields, relationships (PRIMARY source for entity discovery)
- `screen-flow.md` — screen navigation graph (user-action trigger source)
- `behavior-logic.md` — BL### scheduled jobs, events, observers (scheduled/event trigger source)
- `business-rules.md` — system-level business rules (guard/invariant source)
- `feature-list.md` — F### inventory (feature cross-refs)
- `features/*/technical-spec.md` — per-feature specs with SM-###, BR-###, source citations

## Source Code Authorization

**AUTHORIZED to read source code directly** via Grep/Read tools:
- Enum definitions (state field value sets)
- Controller/service methods (transition triggers + guards)
- Job/command handlers (scheduled transition logic)
- Model scopes/relationships (state queries)

This is a source-READ contract, not a pure-synthesis contract. Use upstream artifacts for discovery; verify in code.

## Output

One file per qualifying entity state machine: `plans/<active>/artifacts/flows/<slug>.md`.
Template: `templates/process-flow-template.md`.

After all Tier-1 files are written, **also emit** `plans/<active>/artifacts/flows/system-flow.md` per `templates/system-flow-template.md` **when ≥2 Tier-1 flows were produced** (skip with an `[INFO] system_flow_skipped: <2 flows` note otherwise).

If no entities pass the gate, emit zero Tier-1 files. See Completion Marker below.

### Confidence Companion (advisory sidecar)

`confidence-report_<slug>.md` (one per Tier-1 flow file, plus `confidence-report_system-flow.md`
for the Tier-2 file) is NOT part of the researcher's output above. It is emitted automatically by
`scripts/derive_confidence_report.py` (a deterministic script, not authored by the researcher)
after each flow file is promoted (Wave FL.5) — a citation-coverage sidecar, never gated, never
asserted. See `references/confidence-report-contract.md` for the full derivation rules and the A1
correctness-verification boundary.

## Trigger Gate (STRICT — hard-omit)

An entity qualifies for a process-flow iff its state field has:
- **>=2 transitions** (edges in the state machine), AND
- **>=2 distinct trigger types** from: `user-action | scheduled | event | derived`

Below threshold = **zero output** for that entity. No partial flow, no thin placeholder, no "minimal" version. The guard-cascade value (if any) is captured in the thin template variant by the researcher's judgment, not by default.

**Exception — thin variant:** if the entity's state field fails the trigger gate but has **guard or cascade rules** affecting other entities (e.g., Template active/inactive cascading to TemplateGroup), the researcher MAY emit a thin flow using `depth: thin` in frontmatter and the Guard & Cascade Rules table instead of States + Transitions. This is opt-in per researcher judgment, not automatic.

## FLOW### Code Grammar

Format: `FLOW###_NameSlug` — 3-digit zero-padded, project-scoped (unique across all flows in the project).

Regex: `^FLOW\d{3}_[A-Za-z0-9]+$`

- Sequential assignment in order of discovery (FLOW001, FLOW002, ...).
- IDs do NOT reset per entity or feature.
- Slug derived from entity + lifecycle concept (e.g., `EvaluationCycle`, `ParticipantReview`).
- MUST NOT contain shell metacharacters (enforced by regex).

## Collision Rule

- If `<slug>.md` does not exist → create it.
- If `<slug>.md` exists with no frontmatter OR `status: ai-draft` → overwrite (re-draft).
- If `<slug>.md` exists with `status: human-curated` → MUST NOT overwrite; emit `[INFO] flow_preserved: <slug>`.
- If name collision after normalization → suffix `-2`, `-3`, ...; emit `[WARN] flow_slug_suffixed: <slug>`.

## Citation Rule (anti-hallucination)

**Every transition row in the Transitions table MUST carry a `Source` cell with `file:line` or `file:start-end`.**

- If a transition cannot be source-cited → it is NOT a transition. Move it to `## Open Questions` with the evidence gap noted.
- An unsourced row in the Transitions table = **CRITICAL** contract violation.
- In-state recurring behaviors (non-transition jobs) also require source citations.
- Cross-flow handoff rows in system-flow also require source citations.

## Liveness Rule (stuck-state surfacing)

For EVERY non-terminal stored state, verify in source that at least one exit transition has a guard satisfiable WITHOUT manual intervention, OR that a manual exit exists. A state fails liveness when BOTH hold:

- it is entered by a `scheduled` or `event` trigger (an automated processing state), AND
- its only exit depends on a side-effect that can fail (queue job, external call, clone/snapshot) with no compensating retry / timeout / failure transition in code.

Also flag an automated exit whose guard is **unconditional** while entry performs a fallible side-effect (race risk — e.g. `locked -> start` unconditional vs a clone-snapshot that may not have completed).

When a state fails liveness, record it under `## Open Questions` with a fixed `LIVENESS:` prefix, citing the entry transition and the missing/unsafe exit. **Do NOT invent a recovery transition** — surface the risk, never fabricate the edge.

The Wave 6.85 validator emits a deterministic backstop warning (`ProcessFlow.possible_stuck_state`) for any non-terminal state that is a transition target with no outgoing transition. Resolve it by adding the `LIVENESS:` note or declaring the state terminal in the States prose.

## Derived vs Stored Rule

- **Stored states** (DB column, enum, model field) go in `## States` and `state_field`/`state_fields` frontmatter.
- **Derived views** (computed at read-time from other fields, shown in UI dashboards but never persisted) go in `derived_views` frontmatter and are documented in a separate section, NOT in the States table.
- Modeling a derived view as a stored state = **CRITICAL** (fabricated state).
- When in doubt, verify: grep for writes to the field. If only reads/computations → derived.

## Time-Derived Gating States

A derived (non-stored) condition is normally excluded from `## States`. **EXCEPTION:** if a time-derived condition GATES transitions across >1 feature (e.g. a form's open/close window computed from `start_date`/`end_date` gating review submission across multiple features), it must be visible — otherwise it falls through the Derived-vs-Stored exclusion and disappears.

Emit a `thin` flow (frontmatter `depth: thin`) using the **Guard & Cascade Rules** table to document the gate. It is a guard, not a stored state — do NOT add it to the States table — but it must be documented so consumers can see what blocks the transitions it governs.

## Multi-Track Entities

When a single entity runs >1 independent state machine (e.g., `EvaluationPair` with `status` + `review_status` + confirm flags):

- Use `state_fields: [field_a, field_b]` (plural) in frontmatter.
- Use concurrent regions (`--` separator) in the `stateDiagram-v2` diagram.
- Document each track in its own `## Track X — field (label)` section with independent States + Transitions tables.
- All tracks live in ONE file (they are one entity, not separate flows).

## Cross-Entity Processes

When a process spans >1 entity's state fields (e.g., finalizing touches `EvaluationParticipant`, `PairTemplateGroup`, `EvaluationResult`):

- Use `spans_entities: [EntityA, EntityB]` in frontmatter.
- The PRIMARY entity (whose state field is the subject) owns the FLOW### file.
- Secondary entity transitions appear in the Transitions table with the entity name prefixed.
- If a secondary entity's machine is complex enough to qualify on its own → separate FLOW### file + cross-ref.

## Sub-Flow / Composition

- **Parent declares:** `sub_flows: [FLOW###_Child]` in frontmatter.
- **Child declares:** `parent_flow: FLOW###_Parent` and `runs_inside_state: {state}` in frontmatter.
- Sub-flows are hosted inside a parent state and run concurrently with the parent.
- Sub-flows do NOT gate the parent (parent advances on its own triggers, independent of child completion) unless explicitly guarded.

## Entry & Exit Contracts

- **Entry contract:** required for sub-flows and cross-entity handoffs. States what upstream event/state must hold before this flow's entry state is reached.
- **Exit contract:** required when the terminal state feeds a downstream flow. States what the terminal state produces for consumers.
- Top-level flows where creation (T1) is the entry need no explicit entry contract.

## Plain Language

Apply the forbidden-tokens regex from `templates/business-context-template.md` to all prose (description, state meanings, trigger descriptions).
Any match = CRITICAL; rewrite in plain language.
Technical codes (FLOW###, BL###, SCR###, F###) in frontmatter and source citations are exempt.

## Completion Marker

After all flow files are emitted (including the zero-output case), write:

```
plans/<active>/artifacts/flows/.completed
```

- Non-zero output: zero-byte file.
- Zero output (no entities pass gate): file content = `no_flows_inferred`.

The marker distinguishes "FL.1 not run yet" from "FL.1 ran and found nothing."
MUST NOT write the marker before all flow files are fully written.

## Tier-2 System-Flow (default, when ≥2 Tier-1 flows)

After ALL Tier-1 process-flows are written, when ≥2 flows qualified:

1. Read all emitted `flows/*.md` files.
2. Synthesize `flows/system-flow.md` per `templates/system-flow-template.md`.
3. Every cross-flow handoff row MUST cite `file:line` (same citation rule as Tier-1).
4. The state-field inventory MUST list every stored field from all Tier-1 flows + mark derived views.

If fewer than 2 Tier-1 flows qualified, do NOT emit `system-flow.md` (a cross-flow synthesis needs ≥2 flows).

## SM-### vs FLOW### (DRY boundary)

- `SM-###` = per-spec state machine (inside `features/{slug}/technical-spec.md`). Scoped to one feature.
- `FLOW###` = project-scoped process-flow (in `flows/`). May span features, may compose SM-###.
- If an entity's state machine is already documented as SM-### in a feature spec, the FLOW### file MUST cross-reference it (`see SM-### in F###`) but MUST NOT duplicate the full transition table. Add only: cross-feature transitions, scheduled-job edges, and cross-entity handoffs that the per-spec SM-### cannot express.
- If an entity appears in only one feature and has no cross-feature/scheduled edges → SM-### is sufficient; no FLOW### needed (it would duplicate).
- **Enforcement:** the cross-reference is the literal string `see SM-### in F###` somewhere in the FLOW### body (any `SM-\d{3}` token satisfies it). The Wave 6.85 validator emits `ProcessFlow.sm_crossref_missing` (warning) when a FLOW###'s state set overlaps an entity-kind SM-### by >=3 states and the flow body carries no SM-### reference. Resolve by adding the cross-ref and trimming the duplicated transition table.

## See Also

- `references/code-formats.md` — FLOW### row in Code Formats table
- `templates/process-flow-template.md` — Tier-1 output template
- `templates/system-flow-template.md` — Tier-2 output template
- `templates/business-context-template.md` — forbidden-tokens regex source
