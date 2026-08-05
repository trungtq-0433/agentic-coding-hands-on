# Context And Objective

Load this file for both create and update modes.

## Mission

- Build the strongest possible understanding of the target behavior from the smallest sufficient set of allowed sources.
- Synthesize ticket facts, feature specs, screen specs, rules, and data-state clues into one coherent testcase context.
- Optimize for accuracy, not ritual. Choose the search and reading order that best fits the current anchors.

## Autonomous Search Model

- Start from the strongest anchors available:
  - explicit `F###`, `SCR###`, `US###`, `PERM###`
  - ticket issue statement, repro steps, expected result, or root-cause notes
  - routes, dialogs, actor realms, entities, tables, or field/state names
- Follow the cheapest path that can ground the current uncertainty.
- Search across the allowlisted source set adaptively. Do not treat the listed artifacts as a mandatory read order.
- Stop expanding once behavior, scope, and state are grounded well enough to generate non-invented testcases.

## Synthesis Objective

- End with one unified understanding per target feature.
- Merge these viewpoints when present:
  - user-visible behavior
  - access and role constraints
  - branching and regression boundaries
  - data-state and persistence behavior
- The matched feature spec remains the behavior boundary. Optional sibling docs may clarify or constrain explicit behavior, but they must not expand coverage beyond what the matched feature spec or ticket explicitly supports.
- Prefer explicit facts over broad summaries.

## DB Awareness

Actively look for DB-related specifications whenever the target behavior touches any of these:

- create, update, delete, restore, or copy flows
- soft delete, hard delete, hidden flags, validity flags, status transitions
- data visibility or filtering driven by persisted state
- stale records, cleanup, migration, maintenance, backfill, or sync issues
- batch jobs, background reconciliation, or derived records
- joins, ownership, contract existence, relationship eligibility, or data integrity rules

Potential DB-signal sources include:

- `entities.md`
- `behavior-logic.md`
- entity, table, field, and flag names in feature specs
- ticket SQL snippets, data samples, deleted flags, timestamps, or maintenance notes

Only generate DB verification steps for entities, tables, relationships, flags, or state transitions explicitly named in the matched feature spec or ticket. Use `entities.md` and `behavior-logic.md` to clarify those named items, not to widen coverage to every related table.

## Concrete Output Rule

When DB state matters, the final testcases must include concrete DB verification steps.

- Use explicit table, entity, field, or state names when the source provides them.
- If the exact table or field is unknown, describe the persistence check at the most concrete explicit state level available.
- Avoid vague wording like `Check DB`.
- Prefer checks such as:
  - record exists or does not exist
  - flag changes from one explicit value to another
  - hidden or deleted records are excluded from the UI or downstream flow
  - related records are created, updated, skipped, or left untouched
  - cleanup or maintenance is required or not required

Use `Data and Database Integrity Testing` when DB validation is the primary assertion.

## Boundaries

- Autonomous search does not permit invented behavior.
- DB awareness does not permit raw SQL dumping into final testcases unless the user explicitly requests it.
- If the allowed sources cannot ground the DB behavior safely, ask for clarification instead of guessing.