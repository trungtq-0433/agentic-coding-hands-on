# Coverage Contract — Engine 1 (`audit-synthesis-judgment`)

Engine 1 is the **only** FAIL source. Everything it emits traces to a machine fact. This contract
pins down exactly what it checks, which validators it calls, how it degrades, and when
`--strict-coverage` turns a missing graph into a hard FAIL.

## What Engine 1 checks

| Check | Signal | Bucket |
|-------|--------|--------|
| **Code-level orphan** | a `graph.json` node whose `source_file` is absent from `_source-to-fcode.json` AND unmentioned in any in-scope doc AND material | FAIL (`orphans`) |
| **Phantom** | an artifact `**Source:** file:line` citation whose file carries no `graph.json` node, in a graph-complete language | FAIL (`phantoms`) |
| **Literal duplicate artifact** | two distinct artifact paths with byte-identical (whitespace-normalized) content above the meaningful-length threshold | FAIL (`redundancy`) |
| **Validator roll-up** | the enumerated subset's `--summary-out` JSON | **advisory only — never a FAIL** |

### Why orphan is narrowed to code-level (not W7a's job)

W7a already gates cross-artifact reference completeness (route/entity/screen/US with no `F###` →
critical). Engine 1 does NOT re-derive those. It covers the gap W7a leaves: a **source file/symbol
with no doc trace at all** — code that exists and is graph-indexed but that no feature spec cites and
no doc mentions. That is a partition hole (a feature the synthesis missed), invisible to a
cross-artifact reference check.

## Symbol-level materiality (not just path globs)

Orphan candidates pass a **symbol-level** filter (mirrors `audit-doc-parity/references/materiality-filter.md`,
extended to symbols). Exempt (logged, never silent — see `orphans_filtered` in the findings JSON):

- **Path-level:** `tests/`, `spec/`, `mocks/`, `fixtures/`, `vendor/`, `third_party/`, `node_modules/`,
  `dist/`, `build/`, `generated/`, `migrations/`, `__pycache__/`, `.venv/`; `*_test.*`, `*.test.*`,
  `*.spec.*`, `*.min.*`, `*.d.ts`, `*_pb2.py`.
- **Symbol-level:** private/non-exported symbols (leading single `_`), framework hooks / entrypoints
  (`main`, `__init__`, `setUp`, `tearDown`, `conftest`, …).

A symbol surviving the filter with zero doc trace is a material orphan → FAIL.

## The enumerated validator subset (advisory roll-up)

19 of the 20 `validate_*.py` share the `--summary-out` schema (`_summary_lib`: `overall_status`,
`totals.{critical,warning}`, `validators{}`); **`validate_translation_skeleton.py` has NO
`--summary-out`** (its args are `--primary`/`--mirror`) and is therefore never called here.

Engine 1 calls **only the judgment-relevant subset** — the validators that speak to partition / US /
inference soundness — and merges their summaries as **advisory context, never a FAIL source**
(a FAIL comes only from orphan/phantom/redundancy). Best-effort: a validator that errors or is
absent is recorded `ran: false` with a reason; the engine never crashes on it.

| Validator | Invoked with | Why in-subset |
|-----------|-------------|---------------|
| `validate_source_citations` | `--docs-root` | citation integrity underlies every anchor this skill relies on |
| `validate_feature_spec` | `--docs-root` | per-feature spec integrity ↔ the feature partition |
| `validate_design_intent_density` | `--design-intent-file` (when present) | the inference-citation gate Engine 3 judges on top of |
| `validate_feature_existence` | `--plan-dir` (when given) | feature-list ↔ spec existence (partition completeness) |
| `validate_id_contiguity` | `--artifact user-stories --plan-dir` (when given) | US/F### numbering gaps = a dropped partition unit |

**Excluded (15), by design:** `validate_route_list`, `validate_screen_list`, `validate_screen_flow`,
`validate_api_map`, `validate_api_contracts`, `validate_crud_matrix`, `validate_db_catalog`,
`validate_behavior_logic`, `validate_process_flow`, `validate_job_list`, `validate_test_cases`,
`validate_reading_guide_db_impact`, `validate_feature_api_link`, `validate_feature_screen_link` —
these are **structural/format** gates that W7a and the rebuild-spec pipeline own; they do not bear on
synthesis *judgment*. `validate_translation_skeleton` — excluded (no `--summary-out`).

## Graph-state degradation (never a silent PASS)

`graph.json` is a gitignored, session-local build artifact. "No graph" usually means "not built this
session", not "stack unsupported". All degraded states set `coverage_status` LOUDLY (distinct from
`result`) and make the affected orphan/phantom findings UNVERIFIABLE, never FAIL:

| State | Detection | Effect |
|-------|-----------|--------|
| **ABSENT** | `graph.json` missing/unreadable | orphan/phantom UNVERIFIABLE; `coverage_status: UNVERIFIABLE` |
| **EMPTY** | present, 0 nodes | same as ABSENT |
| **PARTIAL** | a repo language has zero graph nodes | that language's files UNVERIFIABLE (no false orphan, no false phantom) |
| **STALE** | graph build-commit (if stamped) ≠ `git HEAD` | orphan/phantom UNVERIFIABLE |
| **OK** | present, non-empty, all repo langs represented, not stale | orphan/phantom FAIL-eligible |

**Empty-index guard [RT-C5]:** the core-only pass emits `_source-to-fcode.json` empty-but-valid before
`--feature-specs` runs. Empty index AND no `docs/features/` → orphan check is UNVERIFIABLE (never mass
FAIL). Engine 1 calls `graph_preflight.py` itself first (unless `--no-preflight`), mirroring
rebuild-spec's always-run build.

## `--strict-coverage` + the `graphable` field

Default OFF. When ON, a missing/partial/stale/empty graph on a **graphable** stack becomes a hard FAIL
(`coverage_status: FAIL`) — a CI guard against "the tool silently didn't run".

`graphable` resolution:
1. `--stack <name>` → read `graphable` from `rebuild-spec/references/stack-profiles/<name>.json`.
2. Otherwise infer from repo languages: graphable iff any of
   `python, javascript, typescript, java, go, ruby, php, csharp` is present. COBOL / Pascal(Delphi) /
   PL-SQL are **not** graphable — a missing graph there is EXPECTED, and `--strict-coverage` does NOT
   FAIL (it stays UNVERIFIABLE).

The `graphable` field is added to the five stack-profile JSONs (`web-js-ts`, `generic-source` →
`true`; `cobol`, `delphi-vcl`, `oracle-plsql` → `false`).

## The no-cross-feed invariant

Engine 2 (`MISSING_US`/`UNDER_SPLIT`/…) and Engine 3 (all tags) are stochastic/advisory. Their
signals NEVER increment `orphans`/`phantoms`/`redundancy`. FAIL is Engine-1 deterministic computation
alone. Enforced structurally: the assembler reads FAIL counts only from the coverage engine's JSON.
