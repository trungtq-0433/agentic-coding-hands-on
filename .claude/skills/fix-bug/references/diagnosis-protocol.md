# Diagnosis Protocol

A method for tracking root causes. It trades ad-hoc guessing for investigation that rests on evidence.

## Core Principle

**NEVER guess at root causes.** Reason your way to hypotheses, then hold each one against the evidence.

## Pre-Diagnosis: Snapshot the State (MANDATORY)

Before a single probe, photograph the broken state as it stands — that's your baseline:

```
1. Capture the error messages verbatim (copy-paste, never paraphrase)
2. Capture failing test output (the full command plus its output)
3. Capture the stack traces that matter
4. Capture the relevant log snippets, timestamps and all
5. Capture git status / recent work: git log --oneline -10
```

Step 5 (Verify) leans on this baseline — you MUST diff before against after.

## Diagnosis Chain (Follow in Order)

### Phase 1: Observe — What is really going on?

Read; don't assume. Use `tkm:debug-code` (systematic-debugging Phase 1).

- What does the error message say, exactly?
- Where does it land? (file, line, function)
- When did it first appear? (check `git log`, `git bisect`)
- Does it reproduce every time?
- Expected behavior versus actual behavior?

### Phase 2: Hypothesize — What could be behind this?

Activate `tkm:think-sequential` skill. Reason the hypotheses into shape.

**Structured hypothesis formation:**
```
For each hypothesis:
  1. State the hypothesis clearly
  2. What evidence would CONFIRM it?
  3. What evidence would REFUTE it?
  4. How to test it quickly?
```

**Hypotheses usually fall into:**
- A recent change dragged in a regression (`git log`, `git diff`)
- Data or state out of sync (bad input, stale cache, a race)
- Environment drift (dependency version, config, platform)
- A validation gap (missing null check, type guard, boundary)
- A wrong assumption (API contract, data shape, ordering)

### Phase 3: Test — Hold each hypothesis to the evidence

Spawn parallel `Explore` subagents to weigh every hypothesis at once:

```
// Launch in SINGLE message — max 3 parallel agents
Task("Explore", "Test hypothesis A: [specific search/check]", "Verify H-A")
Task("Explore", "Test hypothesis B: [specific search/check]", "Verify H-B")
Task("Explore", "Test hypothesis C: [specific search/check]", "Verify H-C")
```

**Read each result:**
- CONFIRMED: the evidence backs this as root cause → move on to tracing
- REFUTED: the evidence cuts against it → drop it, note why
- INCONCLUSIVE: not enough data → sharpen the hypothesis or gather more

### Phase 4: Trace — Walk the root cause chain

Use `tkm:debug-code` (root-cause-tracing technique). Trace backward:

```
Symptom (where the error shows)
  ↑ Immediate cause (what tripped the error)
    ↑ Contributing factor (what laid the bad state down)
      ↑ ROOT CAUSE (the original trigger — fix this one)
```

**Rule:** NEVER patch where the error surfaces. Follow it back to the source.

### Phase 5: Escalate — When the hypotheses run dry

If 2+ hypotheses come back REFUTED:
1. Auto-activate `tkm:solve-problem` skill
2. Run the Inversion Exercise: "How would I cause this bug on purpose?"
3. Run the Scale Game: "Does it break at 1 item? 100? 10000?"
4. Weigh environmental factors (timing, concurrency, platform)

If 3+ fix attempts fail after the diagnosis:
1. STOP, right then
2. Put the architecture on trial — is the design itself broken?
3. Talk it through with the user before another swing

## Diagnosis Report Format

```markdown
## Diagnosis Report

**Issue:** [one-line description]
**Pre-fix state captured:** Yes/No

### Root Cause
[Plain account of the root cause, followed back to where it started]

### Evidence Chain
1. [Observation] → pointed to hypothesis [X]
2. [Test result] → confirmed/refuted [X]
3. [Trace] → root cause at [file:line]

### Affected Scope
- Files: [list]
- Functions: [list]
- Dependencies: [list]

### Recommended Fix
[What to change and the reasoning — aimed at the root cause, not the symptom]

### Prevention Needed
[Which guards/tests to leave behind so it can't recur]
```

## Quick Mode Diagnosis

For throwaway issues (type errors, lint, syntax), the diagnosis shrinks to:

1. Read the error message
2. Find the affected file(s) from the scout results
3. Name the root cause (on simple issues it's usually plain)
4. Skip the parallel hypothesis testing
5. Still capture the pre-fix state for verification
