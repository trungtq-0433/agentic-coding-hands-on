# Results Logging

## TSV Format

A row for each round, tabs between fields, and a header line up top.

```
iteration	commit	metric	delta	status	description
```

### Column Definitions

| Column | Type | Notes |
|--------|------|-------|
| iteration | integer | Zero-based; round 0 is the baseline |
| commit | string | 7-char short SHA, or `-` when discarded or crashed |
| metric | float | Whatever the verify command read off |
| delta | float | Signed move from the previous best. Negative counts as a win when lower is better. `-` on the baseline row. |
| status | enum | One of the values listed below |
| description | string | A single sentence on what you tried |

### Status Values

| Status | Meaning |
|--------|---------|
| `baseline` | The first reading, taken before anything changed |
| `keep` | Gained ground, cleared the guard, committed |
| `keep (reworked)` | Tripped the guard at first, got reworked, then passed |
| `discard` | No gain, or a gain too small to clear min-delta |
| `guard-failed` | The metric improved but the guard came back non-zero, so it was reverted |
| `crash` | Verify errored out or ran past the timeout |
| `no-op` | A gain under min-delta — not a failure, just not enough to bank |

### Example Log

```tsv
iteration	commit	metric	delta	status	description
0	a1b2c3d	842	-	baseline	Initial bundle size measurement
1	e4f5a6b	810	-32	keep	Tree-shake unused lodash imports
2	-	798	-44	discard	Remove dead CSS — metric improved but below min-delta
3	c7d8e9f	771	-71	keep	Replace moment.js with day.js
4	-	-	-	crash	Build script errored on dynamic import rewrite
5	1a2b3c4	751	-91	guard-failed	Inline critical CSS — bundle smaller but tests failed
6	5d6e7f8	758	-84	keep (reworked)	Inline critical CSS with fallback (guard-safe version)
7	9a0b1c2	741	-101	keep	Lazy-load admin panel chunk
```

---

## Progressive Summaries

### Check-In Every 5 Rounds

Drop one of these after round 5, 10, 15, and so on:

```
--- Progress @ iteration 5 ---
Best so far: 751 (baseline: 842, -10.8%)
Kept: 3  |  Discarded: 1  |  Crashed: 1  |  Guard-failed: 1
Top strategy: dependency replacement (moment→day.js: -71)
```

### Final Summary

Print this when the loop wraps — whether the budget ran out or the goal was hit:

```
--- Final Summary ---
Baseline → Final: 842 → 741  (-11.9%, -101 units)
Iterations: 7 total  |  Kept: 4  |  Discarded: 1  |  Crashed: 1  |  Guard-failed: 1
Best single iteration: #7 lazy-load admin chunk (-20)
Worst outcome: #4 crash (build script)
Key insight: Dependency replacement yielded most gains; CSS inlining required guard-safe rework
```
