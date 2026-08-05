# Guarding Against Regressions, Reading Through Noise

## The Guard Pattern

Verify tells you the target moved. The guard tells you nothing else came loose in the process.

**Two jobs, kept apart:**
- Verify asks: did the number I'm chasing get better?
- Guard asks: did I break anything on the way?

### How It Works

1. At baseline, the guard has to exit 0 before the loop even begins — that's your clean starting line
2. Each round, once verify passes (Phase 5.5), run the guard — and do it *before* you decide keep or discard
3. A non-zero exit from the guard kicks off the recovery flow

### Guard Recovery Flow

```
Guard fails →
  revert to previous commit →
  rework attempt 1 (different approach) →
    if guard fails again →
  rework attempt 2 (minimal change) →
    if guard fails again →
  discard (log status: guard-failed)
```

**Rule:** A guard that can't pass at baseline gets fixed before the loop runs — you never loosen it to fit.

**Rule:** Guard files are hands-off. Test files, spec files, guard scripts — none of them get edited in the name of an optimization.

**Rule:** When the guard trips, it's the optimization that's wrong, not the guard.

### Common Guard Commands

| Stack | Guard Command | Notes |
|-------|--------------|-------|
| Node.js | `npm test` | Fires the Jest/Vitest suite |
| Python | `pytest` | The whole test suite |
| Go | `go test ./...` | Every package |
| Rust | `cargo test` | Unit and integration both |
| TypeScript | `tsc --noEmit && npm test` | Types first, then tests |
| Any | `npm run lint && npm test` | Lint and test in one shot |

### Picking the Right Guard

- Optimizing runtime code → guard with the full test suite
- Optimizing the build or bundle → guard with `tsc --noEmit` plus a smoke test
- Optimizing an ML pipeline → guard with the test suite plus a data-schema check
- Unsure → fall back to `npm test` / `pytest` / `go test ./...`

---

## Reading Through Noise

A jittery metric lies to you. What looks like a "5% improvement" can be pure measurement variance — and trusting it means keeping a change that did nothing.

### Noise Levels

| Level | What it looks like | How to handle it |
|-------|--------------------|------------------|
| Low | Output that never wavers (LOC, type errors, lint count) | One run, take it at face value |
| Medium | A little drift (build time ±5%, unit-test timing) | Run twice, keep the worse number |
| High | Real swings (API latency, benchmarks, ML accuracy) | Run 3–5 times, take the median |

### Multi-Run Median (High Noise)

```
runs = []
repeat 3-5 times:
  result = run verify command
  runs.append(result)
metric = median(runs)
```

Median over mean — a single freak spike can't drag the median around.

### Min-Delta Threshold

Keep an attempt only when the gain clears the threshold:

```
improvement = previous_best - new_metric   # for "lower is better"
if improvement < min_delta:
  status = no-op   # do not keep, but not a failure
```

**Sensible defaults, by noise level:**
- Low: 0 — every gain counts
- Medium: 1–2% of baseline
- High: 3–5% of baseline

### Confirmation Run

When the stakes are high — the last 3 rounds, or any jump over 20% — verify once more before you commit:

```
candidate looks good →
  run verify one more time →
  compare to initial measurement this iteration →
  if within 2% → confirm keep
  if outside 2% → treat as medium noise, average the two
```

### Environment Pinning (User Responsibility)

The loop has no grip on the machine it runs on — that part is on the user:
- Lock the random seeds for any ML workload
- Keep caches consistently warm (or consistently cold)
- Don't let background processes fight for the CPU
- Feed the same input data on every run

### Config Examples

**Low noise (lint errors):**
```
verify: eslint src --format json | jq '[.[] | .errorCount] | add'
noise: low
min_delta: 0
guard: npm test
```

**Medium noise (build time):**
```
verify: { start=$(date +%s%N); npm run build; echo $(( ($(date +%s%N) - start) / 1000000 )); }
noise: medium
runs: 2
min_delta: 200   # ms
guard: tsc --noEmit
```

**High noise (API latency):**
```
verify: wrk -t2 -c10 -d10s http://localhost:3000/api/health | grep 'Latency' | awk '{print $2}' | sed 's/ms//'
noise: high
runs: 5
min_delta: 5   # ms
guard: npm test
```
