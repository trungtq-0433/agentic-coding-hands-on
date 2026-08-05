# Architecture

<!-- authored by rebuild-spec system-researcher from .system-scout-report.md + component docs -->
<!-- snapshot-hash: {{FILL: copy the snapshot-hash value from .system-scout-report.md}} -->

> **[UNVERIFIED]** — all cross-service edges are heuristic suggestions. A statically-unresolved gRPC
> target is omitted; a Kafka producer↔consumer match is by topic name only. Confirm with a human.

## System shape — and why

{{FILL: 2-4 paragraphs. Explain the SHAPE of the system (entry/gateway, source of truth, data store)
and WHY the dependencies point the way they do. Read each component's docs to ground this.}}

## Topology

{{FILL: DRAW a Mermaid `flowchart LR`. Nodes = every service in the scout report's Services table.
Edges = the scout report's edge list PLUS any cross-service edge you found by reading the components'
docs (esp. reused ones). Label each docs-derived edge and keep it [UNVERIFIED]. Use SAFE node labels —
strip/escape `"`,`|`,`[`,`]`,`` ` ``,`<`,`>`; never emit a raw service name that could break the diagram.
Do NOT invent an edge with no basis in the scout facts or a cited doc.}}

## Cross-service edges (observed + docs-derived)

{{FILL: BUILD a Markdown table | From | To | Type | Label | Source | Status |. Include the scout edges
(Source = static) AND docs-derived edges (Source = the component doc path, Status = [UNVERIFIED]).
Then one plain-language line per edge on its business meaning. NEVER call a component "isolated"/"not
observed" unless you read its docs and found none.}}

## Layer diagram

{{FILL: DRAW a Mermaid `flowchart TB`, role-tiered (Entry/Gateway → Services → Data/Clients), with the
same edges. Safe labels. Then a short paragraph reading the layers.}}

## Methods/contracts exposed without an observed caller

{{FILL: list any exposed RPC/topic with no caller found AFTER reading the owning component's docs, and
what its likely purpose is. Keep [UNVERIFIED].}}

## Fan-in / fan-out

{{FILL: BUILD the fan-in/fan-out table from the scout report, then one paragraph interpreting the
dependency picture — corrected by what the docs revealed (note where scout counts undercount because the
digest was thin).}}
