# Git as Long-Term Memory

Across rounds, the git history is the only memory the loop keeps. Open it every single time.

---

## Required Reads — Every Iteration

No exceptions — these run first thing in Phase 1 (Review):

```bash
git log --oneline -20              # what changed and in what order
git diff HEAD~1                    # exact diff of last iteration
cat loop-results.tsv               # metric trend + keep/discard record
```

Read as a set, they settle three questions:
1. **What landed?** (kept rows carrying a positive delta)
2. **What bounced?** (discarded rows, especially file paths that keep recurring)
3. **Which way is it heading?** (the last five deltas — gaining speed, flat, or slipping back?)

---

## Pattern Recognition

### Lean Into What Worked

- A file category that improved → reach for its neighbors
- A technique that paid off (say, edge-case tests) → take it to functions you haven't touched yet
- One module behind the biggest deltas → put it at the front of the queue

### Steer Clear of What Didn't

- A file-plus-technique pair you already discarded → don't run it again
- Edits that moved nothing (a refactor that leaves the metric flat) → skip them unless the guard demands it
- A metric that keeps see-sawing on one file → leave it be and work elsewhere

### Spot Diminishing Returns

When the last five kept rounds all sit under `delta < Min-Delta * 2`, the easy gains are spent. Read that as a cue to:
- Widen out to neighboring files
- Trade the technique for a different one
- Tell the user you've plateaued instead of grinding on

---

## Stuck Detection Integration

Carry a running count of back-to-back discards across phases — a shell variable or a temp file does the job:

```bash
CONSEC_DISCARDS=0   # reset on keep, increment on discard

# After Phase 6 decision:
if kept; then
  CONSEC_DISCARDS=0
else
  CONSEC_DISCARDS=$((CONSEC_DISCARDS + 1))
fi

# Phase 8 checks:
[ $CONSEC_DISCARDS -ge 5 ]  && shift_strategy
[ $CONSEC_DISCARDS -ge 10 ] && stop_loop
```

---

## Revert vs Reset

Default to `git revert`. Drop to `git reset` only when a revert hits a conflict.

| Command | Keeps history | Safe for pattern analysis | When to reach for it |
|---------|---------------|--------------------------|----------------------|
| `git revert HEAD --no-edit` | Yes | Yes | The normal discard path |
| `git reset --hard HEAD~1` | No | No | Only when revert conflicts |

Here's why: `git log --grep="loop(iter-"` only works while the history is whole. A reset erases the record of what you tried, and later rounds quietly lose the ability to read patterns out of it.

---

## Commit Message Convention

```
loop(iter-N): <one-line description of the change>
```

Examples:
```
loop(iter-3): add null guard to parseToken in lexer.ts
loop(iter-7): split large test fixture into focused unit cases
loop(iter-12): remove unused lodash import reducing bundle 1.2kB
```

With that prefix in place, the log can be queried surgically:

```bash
# All loop commits
git log --oneline --grep="loop(iter-"

# Only kept changes (cross-reference with loop-results.tsv)
git log --oneline --grep="loop(iter-" | head -20
```

A reverted commit stays on the record under git's usual revert message:
```
Revert "loop(iter-4): ..."
```

That's by design — the discards are as much a part of the experiment log as the keeps.
