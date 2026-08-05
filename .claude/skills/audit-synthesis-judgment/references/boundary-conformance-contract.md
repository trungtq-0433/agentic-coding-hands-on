# Boundary-Conformance Contract — Engine 2 (`audit-synthesis-judgment`)

Engine 2 answers ONE question, deterministically: **did `user-stories.md` actually apply the
per-stack IPE Step-3 merge rule and the Step-4 anti-CRUD rule?** It does NOT re-derive the
partition (that path was killed by the red-team — there is no doc-side interaction-level alignment
key, and the 86-vs-354 root cause is already fixed upstream in the IPE protocol). It audits
*conformance* to the already-fixed rule, from the artifact's own declared tables.

**WARN / UNVERIFIABLE only. NEVER FAIL. Engine-2 findings NEVER increment Engine-1's
orphan/phantom/redundancy counts.** This is the load-bearing no-cross-feed invariant.

## What it parses (the artifact's own tables)

From `user-stories-template.md`:
- **Interaction Inventory** — `Screen | Element | Type | Action | Endpoint`. One row per interaction.
- **Screen → US Map** — `Screen | US Codes`. The count of US per screen.
- **US titles** — `## US###...: <title>` headers.

Template placeholder rows (carrying `{TOKEN}`) and header rows are skipped. A row missing columns
is ignored.

## Checks

### Anti-CRUD (Step-4) — stack-agnostic

Every US title must contain exactly ONE action verb. Reject:
- CRUD-lump terms: `Manage`, `Management`, `Administer`, `CRUD`, `Handle`, `Maintain`.
- Compound verbs: `Create/Edit`, `Add and Remove`, `X & Y`.

→ `NAMING` WARN, citing IPE Step-4. Runs for every stack (Step-4 is stack-independent).

### Merge / split (Step-3) — route-view / dfm-form only

Per screen, compare the mapped US count `M` against the minimum justified by the Inventory:

```
destructive      = interactions with Type == destructive-action   (each ALWAYS its own US — Step 1)
non_destructive  = the rest
min_justified    = |distinct Endpoint among non_destructive| + |destructive|
N                = total interactions for the screen
```

| Condition | Finding | Clause cited |
|-----------|---------|--------------|
| `M == 0, N > 0` | `MISSING_US` WARN | Step-5 (screen has interactions, no US — IPE_ZERO) |
| `0 < M < min_justified` | `OVER_MERGE` WARN | Step-3 (b) — endpoint identity — or Step-1 (destructive) |
| `M > N` | `UNDER_SPLIT` WARN | Step-3 (identical interactions over-split) |
| `min_justified ≤ M ≤ N` | conformant | — (no finding) |

**Per-stack condition (b) keying** — the Endpoint column carries the stack's identity key:
- `route-view` (web): the HTTP endpoint (method + path). Two interactions merge only if identical.
- `dfm-form` (Delphi/VCL): the event-handler procedure. The Endpoint column holds the `On*` proc
  citation. Same-table is NOT same-key (that was the 86-vs-354 over-merge failure mode).

The check is **conservative** — conditions (a) same-actor and (c) same-data-flow cannot be verified
deterministically from the tables, so Engine 2 only flags violations of condition (b) (endpoint /
handler identity) and the Step-1 destructive rule. Those are the mechanically-provable ones; the
subjective residue is Engine 3's job.

## Ambiguity → UNVERIFIABLE (never a guess)

- A non-destructive interaction with a **blank Endpoint** → the screen's merge check is UNVERIFIABLE
  (can't apply condition (b)); no guessed OVER_MERGE.
- **Absent** Interaction Inventory or Screen→US Map (older corpus) → the whole merge/split check is
  UNVERIFIABLE for that artifact; do NOT fabricate interactions from source.
- **Unsupported `screen_source`** (`none` for oracle-plsql/generic, `cobol-screen`) → merge/split
  UNVERIFIABLE (no upstream Step-3 condition (b) specified); anti-CRUD (Step-4) still runs.

## screen_source resolution

`--screen-source` explicit > `--stack <name>` profile's `screen_source` field > default `route-view`
(logged). Invoked from the rebuild-spec handoff, `--stack` is passed, so the keying is exact.

## Relationship to W5.6 / W4.5

Those in-pipeline gates run while the generator grades itself (anchoring-biased). Engine 2 runs
**external + post-hoc** and cites the exact clause. Phase-06's fixture must show at least one
conformance miss the in-pipeline gates let through; if it cannot, Engine 2 is recorded
confirmatory-only and flagged for a v1.1 value review.
