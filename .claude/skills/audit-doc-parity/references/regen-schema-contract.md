# Regen Schema Contract — `audit-doc-parity`

The single source of truth for the **comparable field set**. The blind-regen agent MUST emit these
fields (from code only), and `parse_doc_schema.py` MUST extract the same fields (from the doc). The
field-level diff compares them name-for-name. **If the two sides disagree on field names, the diff is
noise** — pin every field to its rebuild-spec template field (DRY; schema-drift is the #1 risk).

Each comparable item carries an `evidence` field: the `**Source:**`-style `path:start-end` the value was
read from. On the regen side this is mandatory (Iron Law #2); on the doc side it is the parsed citation.

JSON shape per unit (one feature unit = one regen agent):

```json
{
  "unit": "F012_OrderExport",
  "artifact": "technical-spec",
  "items": [ { "kind": "FR", "id": "FR-001", "fields": {...}, "evidence": "src/...:88-95" } ]
}
```

`kind` namespaces the item so diff compares like with like. Below: per artifact, the `kind`s and the
`fields` each must carry, anchored to the template.

---

## 1. `technical-spec` → `technical-spec-template.md`

| kind | Comparable fields | Template anchor |
|------|-------------------|-----------------|
| `FR` | `description`, `endpoint` (METHOD PATH), `handler`, `verifiable` | § Requirements table / "Requirements fulfilled" (`FR-0XX`) |
| `BR` | `applies_to`, `rule`, `linked_fr` | § Business Rules (`BR-001`) |
| `DEC` | `subtype` (render\|interaction\|flow), `triggers_in`, `involved_entities`, `user_visible_outcome` | § Decision Logic (`DEC-001`) |
| `SM` | `kind` (entity\|ui), `states`, `transitions` (from→to, guard, side_effect) | § State Machines (`SM-001`) |
| `ALG` | `input`, `output`, `complexity`, `description` | § Algorithms (`ALG-001`) |
| `INT` | `type`, `target`, `trigger`, `payload`, `failure_handling` | § External Integrations (`INT-001`) |
| `ENTITY` | `entity` (model/class name), `table`, `key_columns`, `purpose` (read/write) | § Key Entities table |
| `SC` | `condition`, `covers` | § Verification (`SC-0XX`) |

**Output-contract sub-fields** (materiality-filter): when an `FR`/`ALG`/`INT` produces a material output,
its `fields` also carry an `output` object — `{ format, columns, encoding, naming, response_shape,
payload }` — each populated ONLY if extractable from code. The doc side parses the same from `**Output:**`
/ INT `**Payload**` / FR response descriptions. This is where field-level MISSING fires. (Note: the
rebuild-spec `**Output:** {shape summary}` field at `technical-spec-template.md:213` is one line — a
template-faithful doc can still under-describe an export; that under-description surfaces here as MISSING
sub-fields, not as a depth grade.)

## 2. `behavior-logic` → `behavior-logic-template.md`

| kind | Comparable fields | Template anchor |
|------|-------------------|-----------------|
| `BL` | `type` (canonical 10), `trigger`, `payload`, `source_symbol`, `related_routes`, `related_models` | `## {BL###}` block: **Type/Trigger/Payload/Source File/Source Symbol** |

`payload` matters for `event-listener`/`notification`/`webhook`/`mail` (async contract). One BL per
inventory entry (Rule C1) — do not aggregate. `source_symbol` is the diff anchor for stale-citation
re-anchoring.

## 3. `api` → `api-contracts-template.md`

| kind | Comparable fields | Template anchor |
|------|-------------------|-----------------|
| `ENDPOINT` | `method`, `path`, `auth` (required role/guard), `request_shape`, `response_shape`, `status_codes`, `error_envelope` | § REST Endpoints `### {ROUTE} — {METHOD} {/path}` |
| `GQL` | `operation` (query\|mutation), `name`, `args`, `return_shape` | § GraphQL Operations |
| `GRPC` | `service_method`, `streaming`, `request`, `response` | § gRPC Methods |

`auth` is critical-severity (blast radius). `response_shape`/`error_envelope` carry output sub-fields.

## 4. `data-models` → `data-model-template.md`

| kind | Comparable fields | Template anchor |
|------|-------------------|-----------------|
| `ENTITY` | `attributes` (name, type, constraints), `relationships` | § Entities `### {ENTITY}` attribute table |
| `DISC` | `field`, `values` | § Discriminator Fields table |
| `VALIDATION` | `field`, `constraint`, `error_message` | § Validation Rules table |

`constraint` (PK/FK/NOT NULL/unique) and `VALIDATION` rules are data-integrity → critical when drifted.

## 5. `screen-spec` → `screen-spec-template.md`

| kind | Comparable fields | Template anchor |
|------|-------------------|-----------------|
| `FLOW_BRANCH` | `decision_point`, `condition`, `outcome` | § User Flow > Branches table |
| `DATA_FIELD` | `binding`, `source`, `format`, `empty_behavior`, `cross_ref` | § Data Inventory table |
| `UI_STATE` | `state`, `trigger`, `visual_behavior`, `user_action` | § UI States table |
| `VALIDATION` | `field`, `required`, `constraints`, `error_message`, `async_check` | § Validation & Error Feedback |

Screen-spec is mostly `warning` severity (presentational) EXCEPT `VALIDATION` constraints and any
`auth`-bearing flow branch (critical).

---

## Diff rules (consumed by `pipeline.md` step 3)

- Compare only items of the **same `kind`** matched by `id`/anchor (FR-001 ↔ FR-001), or by
  symbol/path when ids are absent (BL by `source_symbol`, ENDPOINT by `method`+`path`).
- A field present on both sides, values agree → `MATCH`.
- A field present on both, values differ → `DRIFT`.
- An item the **doc** asserts, regen has none (no code at the cited region) → `FABRICATED`.
- An item the **regen** asserts (material per `materiality-filter.md`), doc has none → `MISSING`.
- A documented item whose `output` sub-fields are present in regen but absent/under-described in the
  doc → field-level `MISSING` on those sub-fields.
- No citation / unreadable / stale-anchor / dead-code-only → `UNVERIFIABLE` (never DRIFT/MISSING).

## Artifact discovery map (consumed by `scope_doc_units.py`)

| Doc path pattern | Artifact type | Granularity |
|------------------|---------------|-------------|
| `docs/features/{F###_Slug}/technical-spec.md` | `technical-spec` | one unit per feature |
| `docs/features/{F###_Slug}/screens.md` (or `screen-spec.md`) | `screen-spec` | folded into the feature unit |
| `docs/system/behavior-logic.md` / `docs/generated/behavior-logic.md` | `behavior-logic` | one unit (system) |
| `docs/generated/api-*.md` / `api-contracts.md` / `api-map.md` | `api` | one unit (system) |
| `docs/generated/entities.md` / `data-model.md` | `data-models` | one unit (system) |

**Docs root is layout-aware.** The `docs/` prefix above is the *resolved* docs root, not a literal
hardcode: `_citation_lib.resolve_docs_root()` reads `primary_lang`/`translations` from the rebuild-state
file and resolves to `docs/` (en single-lang) or `docs/<primary>/` (non-en primary, or per-lang) via
rebuild-spec's canonical `_lang_lib` — see `_shared/docs-canonical-mapping.md` § Language Layout. The
patterns are globbed relative to that resolved root.

Narrative docs (`system-overview.md`, `business-context.md`, `architecture.md` prose) are **out of
scope** — no structured field set → no field-diff possible (design § Coverage).
