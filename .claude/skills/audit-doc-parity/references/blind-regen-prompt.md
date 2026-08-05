# Blind-Regen Subagent Contract — `audit-doc-parity`

This is the prompt contract for the **blind regeneration** stage — the heart of the architecture and
the anchoring defeat. One subagent per feature unit. The orchestrator fills the `{...}` slots from
`doc-units.json` and dispatches in bounded batches.

## The one rule that defines this skill

> **The regen agent NEVER sees the doc.** It receives only code regions. It re-describes what the code
> does into the structured schema. If it could see the doc, it would anchor to the doc's claims and the
> skill collapses back into W7a. (Iron Law #1.)

The orchestrator MUST pass only the code regions — never the doc path, never the doc text, never the
doc's field values. The agent's output is then diffed against the doc it never read.

## Prompt template

```
You are re-describing source code into a structured behavioral schema. You have NOT seen any
documentation for this code and you MUST NOT look for any — describe ONLY what these code regions do.

## Unit
{unit_id}  —  artifact type: {artifact_type}

## Code regions (the ONLY thing you may read)
{for each region: path, line range, and the extracted code text — citation span + enclosing block}

## Your task
Re-describe the behavior in these regions into the comparable field set for `{artifact_type}` defined
in references/regen-schema-contract.md. Emit JSON: { "unit", "artifact", "items": [ {kind, id, fields, evidence} ] }.

## Hard rules
1. EVERY asserted behavior MUST carry a code line citation in `evidence` (path:start-end). An assertion
   you cannot cite is DROPPED — or, if you are confident it is real but cannot pin the line, emit it with
   "confidence": "inferred". NEVER fabricate a citation.
2. Describe only what the code provably does. Do not infer intent, motivation, or expected volume.
3. For OUTPUT-producing operations, populate the `output` sub-fields (format, columns, encoding, naming,
   response_shape, payload) ONLY where the code provably builds them (a header literal, a BOM write, a
   filename template). Leave a sub-field absent if the code does not show it. (materiality-filter.md)
4. Reachability (legacy group D): if a region is behind a feature flag, in a dead/commented branch, or a
   v1/v2 duplicate, NOTE it — set "confidence": "ambiguous" and add "reachability": "<why uncertain>".
   Do NOT silently treat dead code as live behavior.
5. Non-source behavior (legacy group B): SQL / cron / shell / config-as-code / logic-bearing templates
   are valid behavior sources — re-describe them like any code. A binary/opaque/undecodable region you
   cannot read → emit { "kind": "...", "id": "...", "fields": {}, "evidence": "<path>", "confidence": "unverifiable" }.
6. Tag confidence with the `confidence` taxonomy semantics: extracted (read straight from code) /
   inferred (deduced) / ambiguous (uncertain — needs human / dead-code).

## Output
Return ONLY the JSON object. No prose, no markdown fences around it — your entire reply IS the JSON.
```

## What the orchestrator extracts as "code regions"

Per `scope_doc_units.py`: each region = the **citation span + its enclosing function/class block**
(NOT the whole file — cost). A region over the file-size cap falls back to the cited span alone with
`truncated: true` logged. The agent sees those regions and nothing else.

## Fan-out

Bounded-batch per the kit convention — env `AUDIT_PARITY_MAX_PARALLEL` (default 5) and
`AUDIT_PARITY_BATCH_SIZE` (default 5). One agent per feature unit. System-level units
(behavior-logic, api, data-models) are single units and may run in the same batch pool.
