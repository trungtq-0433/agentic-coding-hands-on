# Autonomous Loop Protocol

Eight phases, walked top to bottom on every round. Take them in sequence and skip none.

---

## Phase 0: Precondition Checks (first iteration only)

A one-time gate before the loop turns. If any check fails, stop and say why plainly.

1. Confirm current directory is a git repository (`git rev-parse --git-dir`)
2. Confirm working tree is clean (`git status --porcelain` → empty output)
3. Confirm current HEAD is on a named branch (not detached)
4. Check no stale lock files (`loop-results.tsv.lock`)
5. Resolve scope glob — confirm at least one file matches
6. Dry-run verify command — confirm it exits 0 and outputs a number
7. Dry-run guard command (if set) — confirm it exits 0
8. Record **baseline metric** as iteration 0 in `loop-results.tsv`

---

## Phase 1: Review

Take stock before every round — even when it feels like nothing moved since last time.

```bash
git log --oneline -20              # recent history
git diff HEAD~1                    # last change detail
cat loop-results.tsv               # full results so far
```

Look for the signal in it:
- Which kinds of files or functions actually paid off?
- What kept getting thrown back?
- Is the number climbing, flattening out, or bouncing around?

---

## Phase 2: Ideate

Settle on **ONE** sharp change. Guiding rules:

- **Lean into** whatever the winning rounds had in common
- **Steer clear** of replays that already failed (same file, same move)
- **The one-sentence test:** if describing the edit needs an "and", it's really two edits — split them across rounds.
- Aim where the leverage is — the thinly covered file, the heaviest bundle contributor, the worst offender for lint
- Three discards deep on one spot? Move — different file, different technique

---

## Phase 3: Modify

- Touch only what `Scope` permits
- **Leave alone** every file the `Guard` command reads
- Confirm it still parses after the edit (`tsc --noEmit`, or whatever the language's checker is)
- Stay small — a single logical unit, nothing more

---

## Phase 4: Commit

Land the commit **before** you verify. Git is your undo lever here, not a save you make once you already know the outcome.

```bash
git add <changed files>
git commit -m "loop(iter-N): <one-line description>"
```

The `loop(iter-N):` prefix is what lets you filter these out of the log down the road.

---

## Phase 5: Verify

Fire the verify command you configured and pull the number out of its output.

```bash
RESULT=$(eval "$VERIFY_CMD")
DELTA=$(echo "$RESULT - $PREV_METRIC" | bc)
```

### Crash Recovery

| Outcome | Meaning | Action |
|---------|---------|--------|
| Exit 0, number printed | Success | Proceed to Phase 5.5 / 6 |
| Exit 0, no number | Bad command | Log `error:no-number`, revert, fix verify cmd |
| Exit non-zero | Verify crash | Log `error:verify-crash`, revert, treat as discard |
| Timeout (>30s) | Too slow | Log `error:timeout`, abort loop, surface to user |

---

## Phase 5.5: Guard (optional — skip if no Guard configured)

Once verify is done, run the guard.

```bash
eval "$GUARD_CMD"
GUARD_EXIT=$?
```

| Guard Exit | Action |
|------------|--------|
| 0 (pass) | Proceed to Phase 6 |
| Non-zero (fail) | Revert commit, rework change (max 2 rework attempts), then discard |

Out of rework attempts? Mark it discarded with reason `guard-fail` and carry on to Phase 7.

---

## Phase 6: Decide

### Decision Matrix

| Metric Direction | Delta vs Min-Delta | Guard | Decision |
|------------------|--------------------|-------|----------|
| higher is better | delta ≥ Min-Delta | pass | **KEEP** |
| higher is better | delta < Min-Delta | pass | **DISCARD** (no progress) |
| lower is better  | delta ≤ -Min-Delta | pass | **KEEP** |
| lower is better  | delta > -Min-Delta | pass | **DISCARD** (no progress) |
| any | any | fail | **DISCARD** (guard fail) |
| any | verify crash | n/a | **DISCARD** (error) |

### Keep

- Set `PREV_METRIC` to the value you just measured
- Zero out the consecutive-discard counter

### Discard

```bash
git revert HEAD --no-edit    # preferred: preserves history
# fallback only if revert conflicts:
# git reset --hard HEAD~1
```

- Bump the consecutive-discard counter by one

---

## Phase 7: Log

Add a single TSV row to `loop-results.tsv`:

```
{iteration}\t{commit}\t{metric}\t{delta:+.2f}\t{status}\t{description}
```

Example:
```
3	c7d8e9f	84.7	+2.3	keep	add branch coverage to tokenizer edge cases
4	-	84.7	+0.0	discard	extract shared assertion helper
```

---

## Phase 8: Repeat or Stop

Go round again only when every one of these holds:
- Rounds run so far < the configured max
- Fewer than 10 discards back to back
- No interrupt from the user (look for a `loop-stop` file or a Ctrl-C)

### Stuck Detection

| Consecutive Discards | Action |
|----------------------|--------|
| 5 | Analyze `loop-results.tsv` for patterns → shift strategy (different scope area, different technique) |
| 10 | **STOP** — surface findings to user, recommend manual intervention |

### Final Report

However the loop ends — budget spent, stuck, or cut short — close it out:

```
Loop complete: N iterations, K kept, best metric: X (baseline: Y, delta: +Z)
Kept changes: [list commit hashes and descriptions]
Discarded: [count] iterations
Recommendation: [continue / diminishing returns / target met]
```

---

## Anti-Patterns

| Anti-Pattern | Why It Backfires | Do This Instead |
|--------------|------------------|-----------------|
| Several edits in one round | You can't tell which edit moved the number | Keep it to one self-contained change |
| Verifying before committing | A mid-run crash leaves nowhere to fall back to | Commit first, every time |
| Editing files the guard checks | The guard stops meaning anything once you alter what it inspects | Treat guard files as read-only |
| `git reset` where `git revert` belongs | Wipes history and blinds future pattern analysis | Reach for `git revert` |
| Breezing past the Phase 1 review | You re-walk dead ends and burn rounds | Read the log and the diff first |
| Brushing off `Min-Delta` | Tiny wobbles masquerade as progress | Pick a threshold that means something |
