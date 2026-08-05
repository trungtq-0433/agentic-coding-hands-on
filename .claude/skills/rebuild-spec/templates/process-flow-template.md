<!-- AI draft — human renames/refines. Large flows (>400 lines) chunk into sub-flow files. -->

---
status: ai-draft
kind: process-flow
subject_entity: "{ENTITY_NAME}"
state_field: "{FIELD_NAME}"              # singular when one state machine; use state_fields[] for multi-track
# state_fields: ["{FIELD_A}", "{FIELD_B}"]  # OPTIONAL: multi-track — entity runs >1 state machine at once
# parent_flow: FLOW###_{ParentSlug}       # OPTIONAL: this flow runs inside another flow's state
# runs_inside_state: "{STATE}"            # OPTIONAL: which parent state hosts this sub-flow
# sub_flows: [FLOW###_{ChildSlug}]        # OPTIONAL: child flows nested inside a state of this flow
# derived_views: ["{VIEW_A}", "{VIEW_B}"] # OPTIONAL: UI labels computed at read-time, NOT stored states
# spans_entities: ["{ENTITY_A}", "{ENTITY_B}"]  # OPTIONAL: cross-entity process touching >1 model
# depth: thin                             # OPTIONAL: entity has state field but fails trigger gate
source:
  data-model: ["{ENTITY_A}", "{ENTITY_B}"]
  behavior-logic: [BL###]                 # omit section if none
  screens: [SCR###_{ScreenName}]          # omit section if none
  features: [F###_{FeatureName}]
generated: "{DATE}"
---

# {FLOW_CODE} --- {Flow Name}

> {1-3 sentence summary: what this flow tracks, what drives it (time vs action), and why it
> matters. If it nests inside a parent, state which parent state hosts it. If it has sub-flows,
> name them. If it is thin/below gate, say so and state what value it provides instead.}

**Subject entity:** `{Entity}` . **State field:** `{field}`
**Enum source:** `{path/to/enum/file}` --- `{comma-separated enum values}`

---

## States

<!-- One row per stored state. derived_views go in a separate section, NOT here. -->

| State | Meaning | Who acts here | Invariant / what is allowed |
|-------|---------|---------------|----------------------------|
| `{state_name}` | {what this state means} | {actor: manager / system / user} | {what holds true; what actions are available} |

`{entry_state}` is the entry state. `{terminal_state}` is the terminal state{--- note absorbing vs non-absorbing if relevant}.

---

## State Diagram

<!-- Use stateDiagram-v2. For multi-track entities, use concurrent regions with -- separator.
     For sub-flows nested inside a state, use the state {} block.
     Every edge label = the trigger from the Transitions table. -->

```mermaid
stateDiagram-v2
    [*] --> {entry_state}: {creation trigger}
    {state_a} --> {state_b}: {trigger label}
    {terminal_state} --> [*]
```

<!-- MULTI-TRACK EXAMPLE (use when state_fields has >1 entry):
```mermaid
stateDiagram-v2
    state {Entity} {
        state "Track A --- {field_a} ({label})" as A {
            [*] --> {state}
        }
        --
        state "Track B --- {field_b} ({label})" as B {
            [*] --> {state}
        }
    }
```
-->

---

## Transitions

<!-- Trigger types: user-action | scheduled | event | derived
     EVERY row MUST have a Source file:line. No source = Open Question, not a transition row. -->

| # | From --> To | Trigger type | Trigger | Guard (must hold) | Side effects | Source |
|---|-----------|--------------|---------|-------------------|--------------|--------|
| T1 | `{from} -> {to}` | {trigger_type} | {what fires the transition} | {precondition or ---} | {state changes, jobs dispatched, or ---} | `{file.ext}:{line-range}` |

### In-state recurring behaviors (NOT transitions)

<!-- OPTIONAL: list scheduled jobs / events that fire INSIDE a state without changing it.
     Omit this section entirely if there are none. -->

- BL### `{JobName}` ({schedule}) --- {what it does}

---

## Entry Contract

<!-- OPTIONAL: under what conditions this flow starts. Required for sub-flows. Omit for top-level
     flows where creation (T1) is the entry. -->

{Parent flow / event that must occur before this flow's entry state is reached.}

## Exit Contract

<!-- OPTIONAL: what this flow's terminal state feeds into. Omit if terminal is a dead end. -->

{What downstream flow or process consumes this flow's terminal state.}

---

## Outcomes

<!-- OPTIONAL: possible end-states of the business process this flow represents.
     Use when the flow has meaningful success/partial/failure modes. -->

- **Success:** {what happened}
- **Partial:** {what partially completed and why}
- **Reopened:** {if terminal state is non-absorbing, how it can revert}

---

## Composition Map

<!-- OPTIONAL: only for flows that have sub-flows or are part of a composition.
     Show nesting + which states host which child flows. -->

```
{FLOW_CODE} {Flow Name}  ({Entity}.{field})        <-- this file
  +-- state: {hosting_state}  (hosts, concurrent)
       +-- FLOW### {ChildName}   ({ChildEntity}.{child_field})
  precondition: FLOW### {SetupName}  ({guard relationship})
```

---

## Guard & Cascade Rules

<!-- OPTIONAL: for thin/below-gate flows where the value is in guard/cascade rules rather
     than a full state diagram. Use INSTEAD of States + Transitions sections. -->

| # | Edge | Actor | Guard | Cascade / side effect | Source |
|---|------|-------|-------|----------------------|--------|
| 1 | `{from} -> {to}` | {actor} | {precondition} | {cascading state changes} | `{file}:{line-range}` |

---

## Open Questions

<!-- Ambiguities that need domain expert or stakeholder input.
     Write `None.` if all questions resolved.
     LIVENESS: prefix a row when a non-terminal state has no safe automated exit
     (fallible side-effect or unconditional race) — see contract Liveness Rule.
     SM cross-ref: if this flow restates an entity SM-###, add `see SM-### in F###`
     in the body and trim the duplicated transition table (contract DRY boundary). -->

- **Q:** {question about guard, transition, or cross-flow invariant}
- **LIVENESS:** {non-terminal state that may get stuck — entry trigger + missing/unsafe exit, with source}
