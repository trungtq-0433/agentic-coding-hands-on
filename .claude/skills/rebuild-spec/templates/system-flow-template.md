<!-- AI draft — Tier-2 synthesis. Emitted by the --flows pass when ≥2 Tier-1 process-flows qualify. -->

---
status: ai-draft
kind: system-flow
composes:
  - FLOW###_{FlowSlug}     # list every Tier-1 process-flow composed here
generated: "{DATE}"
---

# System Flow --- {Title: How One {Process} Runs End-to-End}

> This is **not** another state machine. It is the **synthesis**: how the per-process flows
> nest, hand off, and trigger each other to produce one continuous business process.
> Each box below is a full flow defined in its own file; this page is the wiring.

## Lanes

<!-- One row per lane. Group flows by who/what drives them and when they run. -->

| Lane | Driven by | Flow | Time vs Action |
|------|-----------|------|----------------|
| **{LaneName}** | {actor or mechanism} | [FLOW### {FlowName}]({filename}.md) | {time / action} |

---

## Master Composition Diagram

<!-- flowchart showing how lanes connect. Each subgraph = one lane.
     Solid arrows = data/state handoff. Dashed arrows = precondition/guard.
     Double arrows = hosts (concurrent nesting). -->

```mermaid
flowchart TB
    subgraph LANE_A[" {Lane A name} "]
        A1["{FLOW### summary}"]
    end

    subgraph LANE_B[" {Lane B name} "]
        direction LR
        B1["{state}"] -->|{trigger}| B2["{state}"]
    end

    A1 -. "{precondition relationship}" .-> B1
    B2 == "{hosting relationship}" ==> C1
```

---

## Cross-Flow Handoffs

<!-- The wiring --- what one flow does to another. EVERY row needs a Source file:line. -->

| # | Source flow / event | --> Target flow | Mechanism | Source |
|---|---------------------|-----------------|-----------|--------|
| H1 | {FLOW### event/state} | {FLOW### entry/guard} | {how the handoff works} | `{file}:{line-range}` |

---

## State-Field Inventory (stored vs derived audit)

<!-- Reconciliation gate: every STORED state field must appear in exactly one Tier-1 flow;
     every DERIVED label must be marked as a view, never a state. -->

| Field | Entity | Flow | Stored? |
|-------|--------|------|---------|
| `{field}` | {Entity} | FLOW### | yes stored |
| `{derived_label}` | --- | FLOW### dashboard | no **derived** ({source helper/method}) |

---

## Open Questions (cross-cutting)

<!-- Ambiguities that span multiple flows or concern cross-flow invariants.
     Write `None.` if all resolved. -->

- {Cross-flow invariant gap, timing mismatch, or unguarded handoff}
