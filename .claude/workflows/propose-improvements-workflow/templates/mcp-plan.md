# MCP Fetch Plan — {MCP_SERVER}

<!-- Phase A Step K (`--mcp`). Authored by the K-mcp-plan subagent (mcp-manager) after discovering
     the server's capabilities. Drives the K-mcp-fetch subagent: each "Fetch task" below produces
     exactly one DISTILLED file (templates/mcp-fetch-item.md) under plans/external-knowledge/mcp/.
     DO NOT hand-edit. -->

## Server capabilities

<!-- One line per callable tool / readable resource the server exposes. input-schema = required arg
     keys, or "none". Distilled from discovery — list only what is relevant to fetching project info. -->
- {tool|resource name}: {what project info it provides} · input-schema: {arg keys | none}

## Project context

- Project: {repo folder name / project identity}
- Focus: {focus area parsed off the input, or "none"}
- Scope args: {non-secret --mcp-arg keys applied, or "none"}

<!-- NOTE: the plan stage runs in parallel with the scout, so the bare folder name above is only a
     query-scoping hint. The authoritative target-identity descriptor (tech stack + product name +
     distinguishing facts) is derived from scout-report.md by K-mcp-fetch and drives the relevance
     gate (S5) — a folder name alone cannot discriminate the target from a same-named other product. -->

## Fetch tasks

<!-- Each task = one fetch operation = one output file. The NN prefix is a filename LABEL only, NOT an
     execution-order dependency — K-mcp-fetch runs every task IN PARALLEL (one agent per task).
     Output filename = plans/external-knowledge/mcp/<NN>-<slug>.md where <slug> is a short kebab descriptor.

     MUST — task independence: every task's Call + Args are fully determined HERE at plan time and MUST
     NOT depend on any other task's output. If a fetch genuinely needs a prior result (e.g.
     list-then-get), collapse BOTH operations into ONE task (the executor performs the chain
     internally). Scope each task to a DISTINCT project aspect (its Goal) so outputs do not duplicate
     facts — there is NO cross-task dedup at execution time; distinct-aspect scoping is the only
     overlap control. -->

### task-01 {slug}
- Call: {tool | resource name}
- Args: {key=value, … | none}
- Goal: {which project aspect this retrieves — architecture, requirements, domain, integrations, …}
- Output: plans/external-knowledge/mcp/01-{slug}.md

### task-02 {slug}
- Call: {…}
- Args: {…}
- Goal: {…}
- Output: plans/external-knowledge/mcp/02-{slug}.md

## Coverage

- Covered: {project aspects the tasks above will retrieve}
- Gaps / unavailable: {info the server cannot supply, or "none"}
