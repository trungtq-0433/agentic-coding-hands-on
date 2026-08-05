<!-- layout-exempt: extractor contract — docs/generated/{crud-matrix,db-objects}.md are rebuild-spec's own output targets -->
# Structural-Extractor Contract (Phase B)

rebuild-spec already runs deterministic extraction BEFORE the LLM (`build_source_to_fcode.py`
+ 20+ validators). Phase B **formalizes** that into a per-profile **structural-extractor plug-point**
(#3 — NOT a rewrite) and adds two deterministic-digest-derived artifacts: the **CRUD matrix** (#4)
and the **DB-object catalog** (#9). Extractors parse text → emit a neutral **digest**; the LLM
consumes the digest to write the artifact (every claim citation-bound); a deterministic validator
gates the result. This preserves the extraction-first + provenance philosophy already in place.

## What is an extractor

Each extractor is one script `extract_<kind>.py` that:
- takes `--root <project>`, `--plan-dir <active plan>`, `--encoding <primary>` (+ `--fallback`),
- reads source via `decode_source()` (`_extractor_lib.py`) — encoding-aware, never raw `open()`,
- parses **line-by-line streaming** (RT-F9 — never slurp a whole file into one regex match),
- emits a **digest shard** `plans/<active>/artifacts/_digest_<extractor>.json` (atomic rename),
- updates `plans/<active>/artifacts/_extraction-manifest.json`,
- exits 0 (advisory) — a per-file parse failure is a `[WARN]`, never a crash.

A profile declares which extractors run via its `extractors: []` field (Phase A allowlist:
`ALLOWED_EXTRACTORS` in `_stack_profile_lib.py`). Web profiles declare `extractors: []` → Wave 0.6
is skipped cleanly (guard `extractors.length > 0`, RT-F1).

## Digest schema (neutral, shared by both extractors)

```json
{
  "extractor": "extract_data_flow",
  "generated_at": "2026-06-22T09:00:00Z",
  "source_tree_hash": "<sha256 of sorted path+mtime list>",
  "units": [
    {
      "path": "src/Orders.pas",
      "uses": ["DB", "OrderTypes"],
      "db_ops": [
        { "table": "ORDERS", "op": "C", "columns": ["ID","TOTAL"], "line": 142,
          "citation": "src/Orders.pas:142", "confidence": "high" }
      ],
      "forms": ["TOrderForm"],
      "parse_coverage": { "static_sql_found": 3, "dynamic_sql_detected": true, "confidence": "low" }
    }
  ],
  "db_objects": [
    { "kind": "table", "name": "ORDERS", "columns": ["ID","TOTAL","STATUS"],
      "citation": "ddl/orders.sql:1" }
  ],
  "warnings": ["parse_timeout: src/Huge.pas", "potential_credential_in_citation: ddl/conn.sql:8"]
}
```

- `op` ∈ `{C, R, U, D}` (INSERT→C, SELECT→R, UPDATE→U, DELETE→D). MERGE/UPSERT → emit both C and U.
- `kind` ∈ `{table, view, sequence, trigger, procedure, package, function, dataset}`. `dataset` = a
  flat-file/VSAM COBOL data store (SELECT/FD-declared, no DDL).
- `confidence` ∈ `{high, medium, low}`. Dynamic SQL ⇒ `low` + `[UNVERIFIED]` carried into the artifact.
- `extract_sql_schema` populates `db_objects` (+ minimal `units`); `extract_data_flow` populates
  `units[].db_ops` (+ `parse_coverage`). Both may emit `warnings`.
- **Object purpose is NOT in the digest.** The digest is deterministic structure only; the
  `## purpose` text in `db-objects.md` is derived by the W1.c LLM step from the object's
  name/columns/cited DDL comments (purpose-from-evidence) — there is no `purpose_hint` field.

## Checkpoint + freshness (RT-F11)

- Each extractor writes its OWN shard `_digest_<extractor>.json` via **atomic rename** (`.tmp` →
  `os.replace`). Never a shared digest file → no cross-extractor clobber.
- `_extraction-manifest.json`: `{ "<extractor>": { "completed": true, "file_count": N, "error_count": M,
  "generated_at": ISO } }`. Wave 0.6 is complete ONLY when every declared extractor is `completed: true`.
  Resume skips an extractor already `completed: true`.
- `source_tree_hash` + `generated_at` let W1.b/W1.c detect a **stale digest**: digest older than the
  newest source mtime, or `source_tree_hash` mismatch → emit `[WARN] stale_digest` (advisory).

## Security & safety (mandatory)

- **Credential scrub (RT-F7).** `_sql_parse_lib.py` runs a scrub pass on every line BEFORE the line
  (or any substring) becomes a citation or enters the digest. Redact the VALUE, keep context:
  - `IDENTIFIED BY <secret>` → `IDENTIFIED BY <redacted>`
  - `PASSWORD=<secret>` / `PWD=<secret>` → `PASSWORD=<redacted>`
  - JDBC / connection strings (`jdbc:...`, `Data Source=...;Password=...`) → host kept, secret redacted
  - `IP:port:user:pass` tnsnames-style tuples → credential field redacted
  Any redaction → push `[WARN] potential_credential_in_citation: <citation>` to `warnings`.
- **Regex safety on 714K LOC (RT-F9).** Parse line-by-line; FORBID greedy multiline (`[\s\S]*`, `.*`
  spanning lines); use anchored `re.MULTILINE` patterns; enforce a **per-file timeout** (`signal.alarm`
  on POSIX; a line-count / byte ceiling fallback elsewhere) → on timeout push `[WARN] parse_timeout:
  <path>` and skip the file (never hang, never crash the run).
- **Identifier sanitize before Markdown (RT-F10).** Before any identifier (table/column/object name)
  is rendered into a Markdown table cell: strip/escape `|` (→ `\|` or removed), newline → space,
  backtick removed, truncate to a max length. Guarantees the generated table stays column-aligned and
  `validate_crud_matrix.py` never misreads columns.
- **Parse coverage + dynamic SQL (RT-F8).** Flag a unit `dynamic_sql_detected: true` when it builds SQL
  at runtime (`TQuery.SQL.Add`, string concatenation feeding a query, `Format('...%s...')`,
  `ExecuteDirect(<var>)`). Such units get `confidence: low` and every derived db_op carries
  `[UNVERIFIED]`. A unit with `dynamic_sql_detected: true` AND zero static db_ops is a likely
  false-negative → `validate_crud_matrix.py` emits a WARN.
- Extractors **read + parse text only** — never execute SQL, never connect to a DB, never run source.
- `decode_source()` falls back to `errors="replace"` after trying primary then fallback encoding, and
  logs `[WARN] decode_fallback: <path>` — extraction proceeds on best-effort text.

## Artifacts

### CRUD matrix → `docs/generated/crud-matrix.md`
Feature × table grid with C/R/U/D cells + a `columns` column, plus a **Cross-Module** section listing
tables touched by ≥2 features. Every cell is citation-bound. The LLM writes it from
`_digest_extract_data_flow.json`. Template: `templates/crud-matrix-template.md`.

**Shard by FEATURE range, NOT by domain (RT-DOC-b).** A table can belong to multiple features, so a
by-domain shard would duplicate or drop rows. Shard on `F###` ranges (same as feature-list). The
**Cross-Module** section is built in a **post-merge** pass over the merged matrix — never per-shard.

### DB-object catalog → `docs/generated/db-objects.md`
Lists tables / views / stored-procs / sequences / triggers / datasets with purpose-from-evidence +
citation. Deterministic from DDL (`extract_sql_schema`) or COBOL FD/SELECT clauses
(`extract_cobol_data`, `dataset` kind), high confidence, minimal LLM. Template:
`templates/db-object-catalog-template.md`.

`db-objects` is a raw DDL catalog; `data-model` (MODEL###) is the semantic entity model — they
cross-reference by table NAME, never by shared ID.

## Validators (deterministic gates)

- `validate_crud_matrix.py`: every CRUD cell has a citation; every referenced table exists in
  `db-objects.md` OR `data-model.md`; `op` ∈ C/R/U/D; identifiers Markdown-safe (no column drift);
  WARN on a unit with `dynamic_sql_detected: true` but 0 CRUD cells (RT-F8).
- `validate_db_catalog.py`: object names unique per kind; `kind` valid; every object cited;
  identifiers Markdown-safe.

Both follow the existing validator convention: `--summary-out <path>`, exit 0 (PASS/WARN) / exit 1
(critical FAIL) / exit 2 (internal error).

## Downstream consumer: Phase D neutral-digest

The Phase D system-synthesis layer is a legitimate downstream consumer of this structural digest:
`extract_service_topology.py` reads a component's structural digest (+ its contract/config) and, via a
per-stack adapter, emits a **stack-neutral** `_service-digest.json` (see
`references/system-synthesis-contract.md`). The adapter plugs into this digest — it does NOT re-extract
or re-implement structure. One structural digest → N adapters → one synthesis pass.
