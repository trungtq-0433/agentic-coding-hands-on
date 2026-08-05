---
name: requesting-code-review
description: Reach for this as a task wraps, as a big feature lands, or just before a merge — it sends a reviewer subagent to weigh the implementation against the plan or the requirements before you carry on
---

# Requesting Code Review

Send in a reviewer subagent to catch trouble before it cascades downstream.

**Core principle:** Scout the ground first, then review — and review early and often.

## When to Request Review

**Mandatory:**
- At the end of every task in subagent-driven work
- Once a major feature is finished
- Before anything merges to main

**Optional but valuable:**
- When you're stuck and need fresh eyes
- Before a refactor, to set a baseline
- After untangling a hairy bug

## How to Request

**0. Scout edge cases first (NEW):**
```
Before the reviewer goes out, run /tkm:scan-codebase to surface:
- Every file the change touches — not only the ones you edited
- Data-flow paths at risk of breaking
- Edge cases and boundaries
- Side effects waiting to bite

See: references/edge-case-scouting.md
```

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch reviewer subagent:**

Use Task tool with `reviewer` type, fill template at `reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - what you just built
- `{PLAN_OR_REQUIREMENTS}` - what it's supposed to do
- `{BASE_SHA}` - the commit you started from
- `{HEAD_SHA}` - the commit you ended on
- `{DESCRIPTION}` - a one-line summary

**3. Act on feedback:**
- Critical gets fixed now
- Important gets fixed before you move on
- Minor goes on the list for later
- When the reviewer is wrong, push back — with the reasoning

## Example

```
[Task 2 done: add verify + repair functions]

You: Before I touch Task 3, send this through review.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch reviewer subagent]
  WHAT_WAS_IMPLEMENTED: verify + repair for the conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: added verifyIndex() and repairIndex(), covering 4 issue kinds

[Subagent comes back]:
  Holds up: clean structure, real tests behind it
  Issues:
    Important: no progress indicator on the long path
    Minor: hard-coded 100 as the reporting interval
  Verdict: clear to proceed

You: [wire in the progress indicator]
[on to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review at the close of EACH task
- Catch the problem before it compounds
- Fix it before the next task starts

**Executing Plans:**
- Review after each batch of three tasks
- Take the feedback, apply it, keep going

**Ad-Hoc Development:**
- Review before the merge
- Review when you're stuck

## Red Flags

**Never:**
- Wave off the review with "it's simple"
- Leave a Critical sitting
- Carry on with an Important still unfixed
- Argue with feedback that's actually right

**If reviewer wrong:**
- Push back, and bring the reasoning
- Point at the code or tests that prove it works
- Ask for clarification

See template at: requesting-code-review/reviewer.md