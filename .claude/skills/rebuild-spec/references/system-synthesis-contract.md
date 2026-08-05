<!-- layout-exempt: synthesis contract — docs/system|components paths are rebuild-spec's own output targets -->
# System-Synthesis Contract (Phase D)

Phase D adds a **system-of-systems synthesis layer** for multi-repo polyglot projects (microservices,
each sub-repo a different stack). The run model changes from "one root run generates everything" to
**per-sub-repo run (`--root`, Phase R) + one synthesis pass at the root**. The root does NOT regenerate
a service's internals (that is the component run) — it **synthesizes** system-level content no single
repo contains: service catalog, interaction/topology graph, canonical shared-entity model,
cross-service flows, system glossary, per-component confidence.

The keystone: **extractor PER-STACK → emit a STACK-NEUTRAL digest → one synthesis pass over neutral
digests only.** One schema, N adapters, one pass — never special-case a stack inside synthesis (avoids
N² blowup). Cross-service edges that static analysis cannot confirm → `[UNVERIFIED]`; never draw a
phantom edge.

## Neutral-digest schema (`_service-digest.json`, one per component)

```json
{
  "service": "orders",
  "role": "domain-service",
  "generated_at": "2026-06-22T09:00:00Z",
  "source_sha": "<sha256 of the component's source tree>",
  "rpc": [{ "name": "PlaceOrder", "direction": "inbound", "message": "PlaceOrderReq" }],
  "topic": [{ "name": "order.placed", "role": "producer", "event": "OrderPlaced" }],
  "entity": [{ "name": "Order", "id_field": "orderId", "id_type": "uuid",
              "visibility": "internal" }]
}
```

- `generated_at` (ISO) + `source_sha` are **REQUIRED** (provenance + stale detection).
- `topic[].role` ∈ `{producer, consumer}`. `rpc[].direction` ∈ `{inbound, outbound}`.
- `entity[].visibility` ∈ `{public, internal, private}` (default `internal`). Only `public` entities
  (or human-confirmed ones) graduate from an `[UNVERIFIED]` correlation suggestion in
  `data-ownership-map.md` to a confirmed cross-service entity.
- **Synthesis reads ONLY neutral digests** — never a service's source. Adapters are the only code that
  touches stack idioms.

### Field-length caps (RT2-F7 — schema-check is NOT a trust boundary)

Shape-check alone is insufficient against a hostile/bloated digest. Reject a digest that violates:
- `service` ≤ 128 chars; each `rpc`/`topic`/`entity` name ≤ 256 chars; each array ≤ 1000 entries.
A violation → reject the digest with a clear error (do not silently truncate).

## Adapters (RT2-F8 — each is a NEW file, scoped to the project's real stacks)

`extract_service_topology.py` dispatches per-component to a per-stack adapter that maps stack idioms to
the neutral schema. The adapter framework did not exist before Phase D — each adapter is a new file and
documents **signal read → field emitted**:
- `_topology_adapter_spring.py` — `@KafkaListener`/`KafkaTemplate`/`.proto` → `topic(role)` + `rpc`
- `_topology_adapter_nestjs.py` — `@EventPattern`/`@MessagePattern`/`@nestjs/microservices` → `topic` + `rpc`
- `_topology_adapter_go.py` — `segmentio/kafka-go`/`sarama`/gRPC stub → `topic` + `rpc`

Write adapters ONLY for stacks the real project uses (the user supplies the list at forge time). A stack
with no adapter → emit `[SIGNAL_INFERRED]` (reuse the existing marker from
`api-contract-source-patterns.md`); never write a speculative adapter.

## Security (BOTH gates are NEW — not inherited from Phase B)

- **Credential scrub is a SEPARATE pass in `extract_service_topology.py` (RT2-F12).** It reads a NEW
  surface — service config (`application.yml`/`.properties`/`.env`) → broker URLs, SASL jaas, discovery
  tokens. Phase B's `_sql_parse_lib.scrub_credentials` does NOT cover this. Strip connection-string /
  SASL / password / token BEFORE writing `_service-digest.json`. Forbidden patterns: broker URL with
  embedded creds, `sasl.jaas.config=...`, `*.password=...`, `*.token=...`, bearer tokens.
- **Markdown-sanitize is a SEPARATE gate in `_system_synthesis_lib.py` (RT2-F6).** The digest crossing
  into the synthesis output is a NEW trust boundary. Strip/escape `|`, newline, backtick, `[](...)`,
  `<...>` for EVERY string field before render. This contract enumerates which fields render verbatim
  (none — all string fields are sanitized) vs structured (counts, enums).
- **Mermaid-injection is a SEPARATE gate (v13, red-team #3) — `sanitize_field` is Markdown-only.** A raw
  service name inside a Mermaid node can break out of the diagram. `mermaid_safe_id` reduces node ids to
  `[A-Za-z0-9_-]` (all-unsafe → `svc`, collisions de-duped); `mermaid_safe_label` quotes labels and maps
  `"` → `#quot;`. EVERY Mermaid node id and label routes through these.

## Correlation algorithm (RT2-F15 — defined BEFORE forge, breaks the glossary↔correlation cycle)

Entity correlation across services runs on an **independent heuristic** — it does NOT take the glossary
as input. The glossary is an **OUTPUT** that records each suggestion + the human verdict.
- **Candidate match** when: normalized-name similarity ≥ threshold (default: case-fold + strip
  `_`/`-` + singularize → exact match, OR Jaro-Winkler ≥ 0.92) AND type-compatible (same family:
  `uuid`/`string` compatible; `int*`/`long` compatible; mismatched families → flag mismatch).
- **EVERY auto match is `[UNVERIFIED]`.** There is no "confident auto-merge." A match is a *suggestion*
  surfaced in the `data-ownership-map.md` correlation table for a **cross-service consent gate** — a
  human confirms it. Conservative by default: when unsure, emit `[UNVERIFIED]`.
- Exact numeric thresholds live here and are tuned at forge time; default conservative.

## Run model (BLOCK-by-default aggregate — RT2-F11)

Three steps, all built on Phase R's `--root` (D does NOT re-implement path plumbing):
1. **Step 0 — `detect_stack_profile.py <root> --emit-manifest`** → `.rebuild-components.json` run-plan:
   `[{path, profile, role, size_est, timeout_hint, max_loc, status:pending|done|failed, sha?}]`.
   `<name>` derived path-based (`_path_lib.component_name`, RT2-F14) + preflight collision check.
   `detect` stays ADDITIVE (RT2-F4): it KEEPS `recommended_profile` (single) and ADDS `components[]`.
2. **Step 1 — driver = stateless `--batch <manifest>` (RT2-F3):** each call processes exactly ONE
   `pending` component (runs its `--root`) then exits, writing `status=done(+sha)`|`failed(+reason)`.
   Driver loop: `while pending: rebuild-spec --batch <manifest>`. Trivially resumable, failure-isolated,
   fresh context per component. Timeout is a GATE (RT2-F13): a component whose session dies without
   writing status within `timeout_hint` → `failed reason=session_terminated`. Manifest writes are
   atomic + locked (RT2-F5). Per-component runs emit `_service-digest.json` (scrub pass RT2-F12).
2b. **Step 1b — per-pass driver = `--batch <manifest> --pass <name>` (v16.1.0):** after Step 1 drives
   every component's CORE done, this loop drives the remaining passes per component the SAME way. For
   `pass in [feature-specs, screen-specs, flows, glossary]`, `while pending(pass)` each call processes
   EXACTLY ONE eligible component (runs `--<pass> --root <comp>` in a fresh context) then writes
   `pass_status[<name>]=done|failed` and exits. Primitives in `scripts/_manifest_pass_status_lib.py`:
   `next_pending_pass(manifest, pass)` / `mark_pass_done(manifest, comp, pass)` /
   `mark_pass_failed(manifest, comp, pass, reason)` / `pass_summary(manifest)` (resume report). NOTE the
   arg types: the read fns (`next_pending_pass`, `pass_summary`) take a LOADED list (call `load_manifest`
   first); the write fns (`mark_pass_done`, `mark_pass_failed`) take the on-disk manifest PATH. Eligibility
   = core `status=="done"` (reused/excluded loại) AND every **prereq** pass done AND this pass `pending`.
   **DAG prereqs:** `flows`/`glossary` require `feature-specs`; `feature-specs`/`screen-specs` need only
   core. Pass "done" carries **no sha** — output is a docs tree, idempotent + disk-verifiable (unlike core,
   which pins `_service-digest.json`'s sha). Nested-merge writes are atomic + locked, never clobbering
   sibling passes; `emit_manifest` is unchanged (`pass_status` absent ≡ all-pending). Orthogonal to Step 2
   (`--aggregate` consumes only the core digest); `--lang` runs LAST, once, over the whole tree.
3. **Step 2 — `rebuild-spec --aggregate <root>`** (alias `--synthesize`): **BLOCK by default** — a
   missing/incomplete component digest → `[BLOCKED] component_incomplete: <name>`. `--force-aggregate`
   = degraded-proceed (synthesize over `done` components, banner-list the skipped). `synthesize_system.py`
   embeds a manifest-snapshot hash in the output header; a component sha changed since the last
   synthesis → `[WARN] stale_digest` (RT2-F10). `--manifest <path>` overrides the default root-level
   `.rebuild-components.json`; `--digest-collect <dir>` + `--max-digest-age` gather polyrepo digests.

## Output — system layer, language-mapped path (v13)

Centralized at the monorepo root: `docs/components/<name>/` (per component) + the synthesis layer.
The synthesis layer is written to the **language-mapped** docs root (v13 — was a hardcoded flat
`docs/system/`):
- `synthesize_system.py` resolves the root via `_lang_lib.detect_layout_mode` + `resolve_docs_root`
  over an **absolute** `docs_base`. en single-lang → `docs/system/` (byte-identical, no-op). Per-lang
  (a non-en primary, or en with a registered secondary) → `docs/<primary>/system/`.
- **`primary_lang` discovery:** majority across the component `docs/components/<name>/.rebuild-state.json`
  files (+ the root state); none → `en`; conflict → majority + `[WARN] lang_conflict` (never block).
  `--primary-lang <code>` overrides; any value passes `normalize_lang` (path-guard) before it touches a
  path (`ValueError` = hard abort). The whole resolved root is guarded with `_path_lib._resolve_guarded`.
- **Auto-migration (BREAKING → 13.0.0):** a per-lang project still flat at `docs/` with no sentinel →
  auto-invoke `migrate_docs_layout` (en primary → `flip`; non-en → `relocate_to_primary`) to relocate
  every flat language layer into `docs/<primary>/`, write the `.layout-migrated` sentinel (idempotent),
  THEN write artifacts there. No silent fork; no orphaned flat copy.

### Artifacts (v16 — parity-renamed to match the per-component tier)

Mechanical (written directly as `<name>.md`, overwritten on re-run):
- `per-component-confidence.md` — per-component extraction-confidence (pure numbers, no prose surface).

Facts file (machine-generated, not authored, not promoted):
- `.system-scout-report.md` — the authoritative facts the researcher reads (see the contract section above).

Authored by the system-researcher from `templates/aggregate/<name>-template.md` + the scout report + the
components' docs (the researcher CREATES `<name>.draft.md` — prose, tables, AND Mermaid; promoted to
`<name>.md` after review — see below):
- `overview.md` — project purpose + scope + primary actors + services-at-a-glance.
- `component-catalog.md` — domain / entities / contracts / stack / role per component, PLUS Dependencies
  (resolved out-neighbours), a Module link (`../components/<name>/`), and an authored **Responsibility** cell
  per component derived from reading that component's docs (a reused component is read, never left thin).
- `architecture.md` — **folds the former `interaction-graph.md`**: researcher-drawn Mermaid topology/layer
  graphs + edge table (statically-observed + docs-derived `[UNVERIFIED]`, no phantom edges) + fan-in/out +
  self-loops, PLUS narrative explaining the system shape (supplemented from the components' docs).
- `glossary.md` — shared/ambiguous terms (correlation OUTPUT).
- `cross-service-flows.md` — end-to-end sagas (researcher-drawn saga sequence + narrative).
- `data-ownership-map.md` — **replaces `canonical-entity-model.md`**: entity ownership (owner = the declaring
  service) + cross-service correlation suggestions (`[UNVERIFIED]`, consent gate) + event producer→consumers.
  Authored tables + prose (v18 — was mechanical in v16/v17).

**Renamed (v16 parity):** `system-overview`→`overview`, `service-catalog`→`component-catalog`,
`system-glossary`→`glossary`; `interaction-graph` FOLDED into `architecture`. No migration of existing
on-disk aggregate files (none exist — Validation S1); renderers emit the v16 names from the start.

**Dropped/folded (red team):** `dependency-matrix` (→ fan-in/out, in `architecture`), `system-contracts`
(redundant with component-catalog "Contracts Exposed"), `system-nfr-ops` (deferred — near-empty).

## Scout-report → author → review → promote contract (v19.0.0 — Python is scanner-only)

Python no longer builds the aggregate documents **or their tables/diagrams**. `--aggregate` is the
scanner: it computes the FACTS and writes them to `.system-scout-report.md` as **DATA tables only** (no
Mermaid) — services table with per-component `reused` flag + **absolute docs path**, the `[UNVERIFIED]`
edge list, fan-in/out, self-loops, entity-ownership, correlation candidates, event flows, per-component
confidence — plus the mechanical `per-component-confidence.md`. **It creates no `<name>.draft.md`.**
- **Authoring = the system-researcher LLM pass** (not Python): the orchestrator spawns the researcher per
  `system-researcher-contract.md`. The researcher CREATES each `<name>.draft.md` from
  `templates/aggregate/<name>-template.md` + the scout report + the components' docs — authoring the prose,
  **building the tables, AND drawing the Mermaid** (topology/layer/saga). It **reads each component's own
  docs at the scout-report docs path** to supplement the heuristic edges — mandatory for every
  `reused`/docs-derived component (`SY-R8`) — and the docs-derived edges it adds appear in BOTH the prose
  and the charts (this is how a reused component's missing edges finally reach the diagrams). Python
  provides the scout facts + templates + the promote validator; it does NOT render any document content.
- **Fidelity = review gate + lint, not mechanical pinning (v19 decision):** every node/edge/entity the
  researcher draws must trace to a scout fact OR a cited component doc (no phantom edges — `SY-R2`);
  docs-derived edges stay `[UNVERIFIED]` + carry a `source:` citation (`SY-R8`). The reviewer enforces this
  (`SY-R6`). **Mermaid safety:** the researcher must use safe node ids/labels (strip/escape
  `"`/`|`/`` ` ``/`[`/`]`/`<`/`>`); a mechanical **Mermaid-safety lint** at promote re-checks every Mermaid
  fence and fails on an unsafe label (validation, not generation — the only Python touching the authored docs).
- **Wording rubric (v17.0.0):** the researcher writes for **a new engineer** — full plain-language
  sentences, **active voice**, **every acronym/term defined on first use**, **no raw symbol/ID dumps**, and
  every `[UNVERIFIED]` qualifier preserved. Stated operationally in `multi-component-runbook.md` Step 3.
- **Review gate (v17.0.0; v19 retarget):** between authoring and promote, the **6 authored artifacts** pass a
  W7a-style reviewer→fix-cycle (`MAX_FIX_CYCLES = 3`)→ gate against
  `verification-checklist-system-synthesis.md` (`SY-R1..SY-R8`). See `multi-component-runbook.md`
  Step 3.5; the canonical loop is `pipeline-w7-w9.md`. Only the mechanical `per-component-confidence.md` is
  not reviewed.
- **Promote gate:** `_synthesis_narrative_lib.validate_filled_scaffold(draft)` must return an empty
  violation list (no `{{FILL}}`/`[FILL]`/`{{SCOUT}}` marker remains **AND** every Mermaid fence passes the
  safety lint) **AND** the review report must read `failed == 0` before the orchestrator promotes
  `<name>.draft.md` → `<name>.md`.
  After the rename completes, **MANDATORY**: run the deterministic draft-purge step:
  ```
  python3 purge_system_drafts.py \
      --system-dir docs/<lang>/system \
      --docs-root docs/<lang>
  ```
  The purge deletes each `*.draft.md` whose promoted sibling (`<name>.md`) exists; drafts with no
  sibling are preserved (safety invariant: absent sibling means promote did not happen). This step
  must be a deterministic script invocation — not an LLM file-op — so it is auditable and
  re-runnable without side-effects.
- **Stale guard:** the snapshot hash folds in the synthesis format version, so a format change (not just
  a source change) trips `[WARN] stale_digest`.
- **Confidence companions (v25.2.0, in-v1):** immediately after the draft-purge step, run
  `derive_confidence_report.py --limitation-note synthesis` once per promoted `<name>.md` (all 6
  authored artifacts; `per-component-confidence.md` is excluded — it is mechanical, not authored
  prose). Best-effort, advisory, never gates promotion — same sidecar contract as every other pass.
  The `--limitation-note synthesis` flag injects a mandatory header caveat (synthesis artifacts
  are citation-sparser than per-feature specs; their coverage stat is not comparable to per-feature
  scores). See `references/confidence-report-contract.md` and
  `references/multi-component-runbook.md` § Step 3.5 for the wiring.

## ID namespacing

Each component prefixes its IDs (`ORD-F001`, `PAY-F001`). The contiguity/renumber gate runs
**per-component scope**, never global — otherwise `F001` is ambiguous across services. Synthesis uses
the prefix for cross-ref without collision.

## Boundaries (do NOT mix)

- **Shared API/DB** integration → anchored by the shared schema (CRUD matrix, Phase B — intra-service).
- **Microservice (DB-per-service)** → no shared schema; anchored by contract + topic + entity-ID
  correlation (this contract — `architecture` topology + `data-ownership-map`). CRUD matrix per-service is
  intra-service; the inter-service map is a DIFFERENT artifact.
