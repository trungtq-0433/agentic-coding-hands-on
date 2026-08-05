---
name: tkm:think-sequential
description: Reason through a hard problem one checkable step at a time, free to backtrack and rewrite earlier steps. Reach for it on multi-step reasoning, testing a hypothesis, planning that expects to change, splitting a tangled problem into parts, and correcting course mid-way.
license: MIT
argument-hint: "[problem to analyze step-by-step]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: planning-architecture
triggers: ["think through step by step", "complex problem", "analyze carefully", "reason through"]
---

# Measuring Twice

The master measures twice not because they doubt the first measurement, but because the cost of cutting is higher than the cost of checking.
Sequential thought is that discipline: forming a step, testing it against what is known, correcting before the next step, arriving at the cut only when the measurement is right.

Tackle a hard problem as a chain of small, checkable thoughts — each one resting on the last, each one open to correction, the running count adjusting as the work tells you more.

## When to Apply

- Breaking a tangled problem into parts you can reason about one at a time
- Planning where you expect to backtrack and rewrite earlier steps
- Work that may need a mid-course correction once you see further in
- Problems whose true shape only emerges as you dig
- Long solutions where you must carry context forward across many steps
- Chasing down a bug or root cause by floating and testing hypotheses

## Core Process

### 1. Start with Loose Estimate
```
Thought 1/5: [Initial analysis]
```
Treat the total as a guess, not a contract — revise it the moment the work tells you otherwise.

### 2. Structure Each Thought
- Name the earlier thought you are building on
- Take on a single concern, not three at once
- Say plainly what you assume, what you doubt, what just clicked
- Hand off cleanly: point at what the next thought must settle

### 3. Apply Dynamic Adjustment
- **Expand**: hidden complexity surfaced → raise the total
- **Contract**: it is simpler than you feared → lower the total
- **Revise**: a new insight breaks an earlier step → flag the revision
- **Branch**: more than one route forward → lay them side by side

### 4. Use Revision When Needed
```
Thought 5/8 [REVISION of Thought 2]: [Corrected understanding]
- Original: [What was stated]
- Why revised: [New insight]
- Impact: [What changes]
```

### 5. Branch for Alternatives
```
Thought 4/7 [BRANCH A from Thought 2]: [Approach A]
Thought 4/7 [BRANCH B from Thought 2]: [Approach B]
```
Weigh the branches against each other in the open, then commit with the reason for the choice stated.

### 6. Generate & Verify Hypotheses
```
Thought 6/9 [HYPOTHESIS]: [Proposed solution]
Thought 7/9 [VERIFICATION]: [Test results]
```
Keep cycling guess against test until one holds up.

### 7. Complete Only When Ready
Mark final: `Thought N/N [FINAL]`

Stop only when:
- The solution has been checked, not merely proposed
- Every concern that mattered has been handled
- You actually trust the answer
- Nothing is still left hanging

## Application Modes

**Explicit**: show the thought markers when the problem is gnarly enough to earn visible reasoning, or when the user asks to see the steps.

**Implicit**: run the same discipline in your head for ordinary work — let it sharpen the answer without spilling the scaffolding into the reply.

## Scripts (Optional)

Two helper scripts, for when you want the steps validated or kept on record:
- `scripts/process-thought.js` — checks each thought's structure and keeps a running history
- `scripts/format-thought.js` — renders a thought for display (box / markdown / simple)

Usage examples live in README.md. Reach for them when you need validation or persistence; otherwise just apply the method by hand.

## References

Pull these in when a topic needs more depth:
- `references/core-patterns.md` — the everyday revision & branching shapes
- `references/examples-api.md` — worked API-design walkthrough
- `references/examples-debug.md` — worked debugging walkthrough
- `references/examples-architecture.md` — worked architecture-decision walkthrough
- `references/advanced-techniques.md` — spiral refinement, hypothesis testing, convergence
- `references/advanced-strategies.md` — uncertainty, revision cascades, meta-thinking
