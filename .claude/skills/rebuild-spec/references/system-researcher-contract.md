<!-- layout-exempt: rebuild-spec owns all docs/system|components paths — references here are output targets or internal definitions -->
# System-Researcher Contract (Phase D — aggregate tier, rebuild-spec v18.0.0)

The aggregate tier no longer builds its documents in Python (v19). Python is the **scanner**: it computes
the **facts** (the scout report — DATA only, no diagrams). YOU, the system researcher, **author** the
whole document — prose, **tables, AND the Mermaid diagrams** — from those facts AND the components' own
docs. This mirrors the per-component researcher (`feature-spec-researcher-contract.md`): scout facts in,
authored document out, reviewer gates the result.

## Inputs (read ALL before authoring anything)

1. **`.system-scout-report.md`** (same `system/` dir) — the authoritative facts, Python-computed, as
   DATA TABLES (no Mermaid): services + roles + stacks + **`reused` flag** + **absolute docs path per
   component**, the edge list (`[UNVERIFIED]`-tagged), fan-in/out, self-loop topics, entity ownership,
   correlation candidates, event flows, per-component confidence.
2. **The artifact template** — `templates/aggregate/<name>-template.md`. READ it and CREATE
   `<name>.draft.md` by authoring content into its structure (Python does NOT pre-create the draft).
3. **Each component's own docs** — at the docs path the scout report lists per component. **Reading these
   is MANDATORY (see "Read the components' docs" below) — not optional context.**

## Output files (you CREATE each `<name>.draft.md`; the orchestrator promotes to `<name>.md` after review)

| File | What you author |
|------|-----------------|
| `overview.draft.md` | purpose, scope, primary actors, the services-at-a-glance table (one-line duty per service) |
| `component-catalog.draft.md` | per-component domain/entities/contracts/stack/role/deps/module-link + a **Responsibility** prose cell each |
| `architecture.draft.md` | the topology + layer narrative — *why* the system is shaped this way; embeds the pinned Mermaid + edge table |
| `glossary.draft.md` | shared/ambiguous terms, each defined and disambiguated across the services it appears in |
| `cross-service-flows.draft.md` | each end-to-end saga named and described (ordering, handoffs, failure handling) |
| `data-ownership-map.draft.md` | entity ownership + correlation suggestions in prose (every `[UNVERIFIED]` kept) |

`per-component-confidence.md` is NOT yours — it is a mechanical numbers table Python writes directly.

### Confidence Companion (advisory sidecar, in-v1)

`confidence-report_<name>.md` — one per promoted aggregate artifact (`overview.md`,
`component-catalog.md`, `architecture.md`, `glossary.md`, `cross-service-flows.md`,
`data-ownership-map.md`) — is NOT one of the 6 drafts you author above. It is emitted
automatically by `scripts/derive_confidence_report.py --limitation-note synthesis` (a
deterministic script, not authored by you) after each `<name>.draft.md` is promoted to
`<name>.md` (Step 3.5 Promote gate) — a citation-coverage sidecar, never gated, never asserted.
Unlike the per-feature/per-screen companions, this one carries a mandatory limitation-note
header (synthesis artifacts have structurally sparser citations than per-feature specs — do not
compare the two coverage stats). See `references/confidence-report-contract.md` for the full
derivation rules and the A1 correctness-verification boundary.

## [CRITICAL] Read the components' docs — never declare "unobserved" blind

The scout report's edge list is **heuristic and incomplete** — `synth_digest_from_docs.py` parses a thin
neutral digest and routinely misses real cross-service relationships, especially for **reused /
docs-derived** components.

- For **every** component — and **without exception for any `reused: true` component** — you MUST OPEN and
  READ its docs (`architecture.md`, `api-map.md`, `behavior-logic.md`, `entities.md`, `route-list.md`,
  any `system/` narrative) at the docs path the scout report gives, and mine them for cross-service
  relationships, owned entities, contracts, and responsibilities to **supplement** the scout facts.
- You may assert that a component has **no** cross-service edge ONLY after reading its docs and finding
  none. **It is a CRITICAL contract violation** to write *"chưa quan sát được" / "not observed" /
  "isolated" / "no confirmed edges"* about a component whose docs you did not read. A reused component is
  never described as standing apart until its docs are read.
- When the docs reveal a relationship the scout report missed, ADD it — tag it `[UNVERIFIED]` (docs-derived,
  not statically confirmed at the system level) and cite the component doc it came from
  (`source: components/<name>/.../architecture.md`).

## Fidelity rules (the reviewer enforces these — `SY-R2`, `SY-R3`, `SY-R6`, `SY-R8`)

- **You DRAW the tables and the Mermaid yourself** from the scout facts + the components' docs — there are
  no pinned blocks to copy (v19). Fidelity is your responsibility and the reviewer's, not a mechanical pin:
  - **Every node/edge/entity/topic must trace** to a scout-report fact OR a component doc you read (cite the
    doc). Do NOT invent a service, edge, entity, or topic with no basis. No phantom edges.
  - A relationship that is in the scout report = statically observed; one you add from a component's docs =
    docs-derived → tag it `[UNVERIFIED]` and cite the doc. Charts and tables should include BOTH (this is how
    a reused component's missing edges finally appear in the diagram, not just the prose).
  - **Mermaid must be syntactically valid and use SAFE labels.** Strip/escape `"` `|` `[` `]` `` ` `` `<` `>`
    in any node id/label; never emit a raw service/entity name that could break out of the diagram. A
    mechanical lint also checks this at promote — but write safe labels from the start.
- **Keep every `[UNVERIFIED]` qualifier.** A heuristic edge stays hedged; never launder it into asserted fact.

## Wording rubric (write for a new engineer)

Full plain-language sentences · active voice · define every acronym/term on first use · NO raw symbol/ID
dumps standing in for prose (a bare list of RPC names is not a Responsibility) · explain *why*, not only
*what*. The template's `{{FILL: ...}}` markers tell you what each section needs; replace every one.

## Reuse / update of an existing document (req #1 — adopt, don't discard)

When a prior `<name>.md` already exists (reused or being updated), READ it first and **build on it** — keep
its accurate prose and human edits, refresh only what the current facts changed. A file whose frontmatter
carries `doc_lock: user` is off-limits: do not rewrite it; note any drift under `## Unresolved Questions`.

## Optional: why-read-here annotations for the system README (C-faithful)

After authoring the 6 drafts, you may write a sibling file `.nav-why.json` in the `system/` directory
to supply grounded, 1-line "why-read-here" clauses for the reading-order table in the aggregate
`system/README.md`. These replace the static fallback clauses for any file you annotate.

**Format** — a flat JSON object mapping filename to a 1-line causal reason:

```json
{
  "overview.md": "Read first — this system spans N services and the overview names each one.",
  "architecture.md": "Read after the catalog because the layer diagram labels the exact components listed there."
}
```

**Rules:**
- One line per entry; no multi-line values.
- Causal wording: explain *why* this doc is read at this point *relative to the previous one*.
- You only need to annotate docs you have a grounded reason for; omitted files fall back to
  the static clause automatically.
- The clause is sanitized at render time (HTML-unsafe chars stripped).
- If you do not write `.nav-why.json`, the static clauses are used and no feature is lost.

## Status

Close with `**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED`, a one-line summary, and any concerns
(e.g. a component whose docs could not be read → say which, never silently fall back to "unobserved").
