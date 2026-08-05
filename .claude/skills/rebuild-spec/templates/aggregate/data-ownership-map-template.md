# Data Ownership Map

<!-- authored by rebuild-spec system-researcher from .system-scout-report.md + component docs -->
<!-- snapshot-hash: {{FILL: copy the snapshot-hash value from .system-scout-report.md}} -->

> **[UNVERIFIED]** — cross-service entity correlations are heuristic suggestions behind a human consent
> gate. The owner of an entity is the service that declares it.

## Entity Ownership

{{FILL: BUILD the entity-ownership table from the scout report (Entity | Owner Service | ID Field |
ID Type | Visibility). Then a short paragraph per owning service summarizing the entities it owns and
their role — grounded in that component's entities/data-model docs you read.}}

## Cross-Service Correlation Suggestions

{{FILL: BUILD the correlation table from the scout report (all [UNVERIFIED]); if none, say so. Then one
line per suggestion on whether the two entities plausibly refer to the same concept, read from both
components' docs. Never assert a confirmed merge.}}

## Event Producers → Consumers

{{FILL: BUILD the event-flow table from the scout report, then SUPPLEMENT consumers/producers you found
by reading the components' docs (the thin digest often misses Kafka consumers — e.g. a reused service
that consumes a topic the scout shows with no consumer). Cite the doc; keep [UNVERIFIED]. One line per
event on what it carries and why.}}
