---
name: tkm:auto-research
description: "Turn a number into a goal and let repetition close the gap — a self-running loop that edits, measures, then keeps or rolls back each attempt over N tries. Reads its own git trail to learn what worked. Reach for it on coverage, latency, bundle weight, or any metric a script can read off as one figure."
argument-hint: "[Goal/Metric description] or inline config block"
metadata:
  author: takumi-agent-kit
  attribution: "Core patterns adapted from autoresearch by Udit Goenka (MIT)"
  license: MIT
  version: "1.0.0"
module: testing-code-quality
triggers: ["improve coverage", "optimize bundle", "iterative improvement", "auto-optimize", "N iterations"]
---

# The Autonomous Refinement Loop

> Pin down a target, give it a number a machine can read, make the reading cheap — and improvement stops needing your hand on the wheel.

Watch a smith hammer the same edge morning after morning and you see why repetition teaches: each stroke is measured against the last, so the hand learns exactly what changed it.
The loop here borrows that rhythm for code — make a single edit, take a single reading, render a single verdict, and go round again until the target is met or the seam runs dry.

## When to Use

- There is a number you want to move — coverage, bundle weight, ESLint count, Lighthouse score, anything a script can read off
- You want the work to run itself across N rounds, no babysitting between them
- Every attempt is committed, so a regression can be rolled straight back out
- You are sweeping a field of possible edits and want each one judged the same way

## When Not to Use

| Situation | Better Tool |
|-----------|-------------|
| The goal is a matter of taste ("make it cleaner") | `tkm:takumi` |
| You already know the bug's root cause | `tkm:fix-bug` or `tkm:debug-code` |
| It's a one-off — nothing to repeat | `tkm:takumi` |
| There is no hard number tracking progress | `tkm:takumi --interactive` |
| The edits would land outside any fixed scope | manual approach |

## Configuration

Pulled from the user's message. Anything required but missing is collected in one **batched** `AskUserQuestion`.

### Required

| Field | Description | Example |
|-------|-------------|---------|
| `Goal` | Plain-language statement of what should get better | `"Increase test coverage in src/utils"` |
| `Scope` | Glob(s) marking which files the loop may touch | `"src/utils/**/*.ts"` |
| `Verify` | Shell command whose stdout is **one number** | `"npx jest --coverage --json \| jq '.coverageMap \| .. \| .s? \| to_entries \| map(.value) \| (map(select(.>0)) \| length) / length * 100' \| tail -1"` |

### Optional

| Field | Default | Description |
|-------|---------|-------------|
| `Guard` | none | Command that catches regressions (exit 0 = clean) |
| `Iterations` | 10 | Ceiling on how many rounds run |
| `Noise` | medium | How much metric jitter to expect: `low` / `medium` / `high` |
| `Min-Delta` | 0 | Smallest gain that still counts as moving forward |
| `Direction` | higher | Which way is winning — `higher` or `lower` |

## Setup

If any required field is absent, gather them in a single prompt:

```
AskUserQuestion({
  questions: [
    { question: "Which number are we trying to move? (e.g. 'test coverage in src/utils')", field: "Goal" },
    { question: "Where is the loop allowed to edit? (glob, e.g. 'src/utils/**/*.ts')", field: "Scope" },
    { question: "Give the verify command — its stdout must be a lone number", field: "Verify" },
    { question: "Any guard command to catch regressions? (optional — Enter to skip)", field: "Guard" }
  ]
})
```

## The Loop Protocol

The complete eight-phase walkthrough lives in [`references/autonomous-loop-protocol.md`](references/autonomous-loop-protocol.md).

**Rules that hold no matter what:**
- One self-contained edit per round — if you cannot say what you did in a single sentence free of the word "and", it's two rounds, not one.
- Commit first, verify second — git is where the loop remembers, not a parachute you reach for afterward.
- Guard files stay untouched — never reach into anything the guard command inspects.
- Roll back with `git revert`, not `git reset` — the trail stays intact.

## Results Log

Every round tacks one TSV row onto `loop-results.tsv` in the working directory:

```
iteration	commit	metric	delta	status	description
0	a1b2c3d	80.0	-	baseline	initial measurement
1	e4f5a6b	82.4	+2.4	keep	add null checks to parser.ts
2	-	81.9	-0.5	discard	extract helper function
```

See [`references/autonomous-loop-protocol.md`](references/autonomous-loop-protocol.md) — Phase 7 for full schema.

## When the Loop Stalls

| Condition | Action |
|-----------|--------|
| 5 discards in a row | Step back, read the pattern, change tack — other files, other approach |
| 10 discards in a row | Halt — write up what you found and hand it back to the user |

## Example Invocations

### 1. Increase test coverage

```
/tkm:auto-research
Goal: Push src/utils test coverage up from roughly 60% toward 80%
Scope: src/utils/**/*.ts, tests/utils/**/*.test.ts
Verify: npx jest tests/utils --coverage --coverageReporters=json-summary 2>/dev/null | node -e "const d=require('./coverage-summary.json');console.log(d.total.lines.pct)"
Guard: npx tsc --noEmit && npx jest --passWithNoTests
Iterations: 15
Direction: higher
```

### 2. Reduce bundle size

```
/tkm:auto-research
Goal: Bring the main bundle under 200KB
Scope: src/**/*.ts, src/**/*.tsx
Verify: npx vite build 2>/dev/null | grep "dist/index" | awk '{print $2}' | sed 's/kB//'
Guard: npx tsc --noEmit
Direction: lower
Min-Delta: 0.5
```

### 3. Eliminate ESLint errors

```
/tkm:auto-research
Goal: Take the ESLint error count in src/api down to zero
Scope: src/api/**/*.ts
Verify: npx eslint src/api --format=json 2>/dev/null | node -e "const r=require('/dev/stdin');console.log(r.reduce((a,f)=>a+f.errorCount,0))" || echo 999
Direction: lower
Iterations: 20
```

## Honest Limitations

- Taste and aesthetics are off-limits — there's no number to chase
- It won't touch a file outside the declared `Scope`
- It won't touch anything the `Guard` command leans on
- A win is never promised — some metrics simply hit a wall
- The repo must be a **git repository with a clean working tree** before the first round
- The `Verify` command has to finish in **under 30 seconds**, or the loop drags too much to be worth it
- Rounds run one after another, never side by side — that's deliberate, since each round reads what the last one left behind

## References

- [`references/autonomous-loop-protocol.md`](references/autonomous-loop-protocol.md) — the eight phases end to end, the keep/discard matrix, and the traps to dodge
- [`references/git-memory-pattern.md`](references/git-memory-pattern.md) — leaning on git history as memory between rounds, revert over reset, commit style
- [`references/guard-and-noise.md`](references/guard-and-noise.md) — using a guard to block regressions and reading metrics through the noise
- [`references/results-logging.md`](references/results-logging.md) — the TSV layout and the running summaries
- [`references/metric-library.md`](references/metric-library.md) — ready-made verify commands grouped by domain
