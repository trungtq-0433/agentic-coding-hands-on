# Verdict Taxonomy — `audit-synthesis-judgment`

Judgment auditing has no golden answer to diff against — audit-doc-parity's MATCH/DRIFT/FABRICATED
taxonomy assumes a code ground truth and is insufficient here. A well-drawn feature boundary that
differs from what a reviewer would have drawn is a **defensible divergence**, not a lie. So the
taxonomy is deliberately small: **3 effective buckets**. Everything finer is a *tag*, never a verdict.

## The three buckets

| Bucket | Fires when | Flips `result`? | Emitted by |
|--------|-----------|-----------------|------------|
| **FAIL** | a **material** code-level orphan or phantom, a **literal duplicate artifact** emitted twice, or `--strict-coverage` on a `graphable: true` stack with a missing/partial graph | **YES** | **Engine 1 ONLY** |
| **WARN** | a boundary/conformance/granularity/naming/inference issue that survived its refutation/clause anchor | never | Engine 2, Engine 3 |
| **UNVERIFIABLE** | no/empty/partial/stale `graph.json`, empty-but-valid `_source-to-fcode.json` (core-only run), or ambiguous artifact text | never (except the `--strict-coverage` case, which is a FAIL) | any engine |

There is **no `judgment_score`**. The boolean `result` + the per-bucket counts are the entire machine
contract. A single number would invite tuning a threshold and would paper over the FAIL/WARN distinction
that the whole design rests on.

## Sub-kind tags (NOT verdicts)

Each finding carries a `kind` tag describing *what* was found. Tags never change the bucket:

| Tag | Bucket | Engine | Meaning |
|-----|--------|--------|---------|
| `ORPHAN` | FAIL | 1 | source symbol present in the graph, absent from `_source-to-fcode.json`, zero doc mention |
| `PHANTOM` | FAIL | 1 | cited `file:line` resolves to no graph node (complete-graph language only) |
| `DUP_ARTIFACT` | FAIL | 1 | the same artifact emitted twice (literal duplicate) |
| `OVER_MERGE` | WARN | 2 | two interactions merged into one US despite failing an IPE Step-3 condition |
| `UNDER_SPLIT` | WARN | 2 | two interactions with identical (actor, endpoint/handler, data-flow) split across different US |
| `NAMING` | WARN | 2/3 | US title with ≠1 action verb or a CRUD-lump name (IPE Step-4) |
| `MISSING_US` | WARN | 2 | a screen with N interactions and < N US with no Step-3 merge justification |
| `UNSUPPORTED` | WARN | 3 | an inferred claim ("why"/"so that") with no traceable warrant (Toulmin gap) |
| `GRANULARITY` | WARN | 3 | a feature far coarser/finer than the set median (statistical outlier) |
| `RESTATES` | WARN | 3 | a paragraph restating another artifact with no added "why" (citation-adjacent spans exempt) |

`MISSING_US` / `UNDER_SPLIT` (Engine 2, stochastic-adjacent) and every Engine-3 tag are WARN — they
**NEVER** increment the Engine-1 FAIL counts (`orphans`/`phantoms`/`redundancy`). This is the
load-bearing no-cross-feed invariant.

## Severity (blast radius, on WARN findings)

| Severity | Domain of the WARN |
|----------|--------------------|
| **high** | auth/permission/data-mutation/money boundary mis-drawn; a hallucinated rationale for a security choice |
| **medium** | a mis-merged CRUD interaction, a granularity outlier on a core feature |
| **low** | cosmetic naming, a restatement with no security/data impact |

Severity tags a WARN for human triage; it never promotes a WARN to FAIL.

## `result` rule

```
result: FAIL  iff  (orphans > 0 || phantoms > 0 || redundancy > 0)
                   || (--strict-coverage && graph missing/partial on a graphable stack)
result: PASS  otherwise
```

- `orphans`/`phantoms`/`redundancy` count **material, Engine-1, deterministic** findings only. An
  orphan/phantom counted as `unverifiable` (empty index, partial/absent/stale graph) is NOT in these
  counts.
- `boundary_warn` + `inference_warn` (Engine 2/3) NEVER flip `result`.
- `unverifiable` NEVER flips `result` (except the `--strict-coverage` graphable case).

## `coverage_status` — loud, distinct from `result`

`coverage_status: OK | UNVERIFIABLE | FAIL` is a **top-level frontmatter field** that the report and the
handoff surface prominently. A no-graph / empty-index / partial-graph run yields `result: PASS` +
`coverage_status: UNVERIFIABLE` — so a consumer can never mistake "nothing to fail on because we
couldn't check" for "verified clean". This is the whole defense against a silent PASS on the
COBOL/Delphi/core-only repos this skill targets.

## Engine-completion accounting

`boundary_status` and `judgment_status` (`OK | PARTIAL | FAILED`) report whether Engine 2 / Engine 3
actually completed. A judge/refuter subagent that dies (timeout, rate-limit) must NOT silently reduce
the WARN set to "clean" — it flips the engine's status to `PARTIAL`/`FAILED`, visible in the report.

## Confidence

Every Engine-3 finding carries a `confidence` tag from the [`confidence`](../../confidence/SKILL.md)
taxonomy: `[EXTRACTED:0.9-1.0]`, `[INFERRED:0.5-0.89]`, `[AMBIGUOUS:0.0-0.49]`. A finding below the
floor (`< 0.5`) does not assert a WARN — it degrades to UNVERIFIABLE.
