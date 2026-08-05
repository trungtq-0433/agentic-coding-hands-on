---
name: verification-before-completion
description: Reach for this the moment you're about to call something done, fixed, or green — and before any commit or PR. Run the command, read the output, and only then make the claim. Evidence comes before the assertion, always.
---

# Verification Before Completion

## Overview

Calling work done before you've checked isn't moving fast — it's lying.

**Core principle:** The evidence comes first, every single time.

**Skirt the letter of this rule and you've broken its spirit too.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

No verification command run in this very message? Then you have no standing to say it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: Which command would actually prove this?
2. RUN: Execute the FULL command, fresh and complete
3. READ: All of the output — exit code, failure count, the lot
4. VERIFY: Does what you just read back up the claim?
   - If NO: Report the real state, with the evidence
   - If YES: Make the claim, and attach the evidence
5. ONLY THEN: Make the claim

Skip a step and you're lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- The words "should", "probably", "seems to" creeping in
- Celebrating before the check ("Great!", "Perfect!", "Done!", etc.)
- Reaching for commit/push/PR with nothing verified
- Taking an agent's "success" at face value
- Leaning on a partial check
- Telling yourself "just this once"
- Tired, and wanting it to be over
- **ANY phrasing that implies success when no verification has run**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Why This Matters

What the failure record keeps showing:
- the partner says "I don't believe you" — and the trust is gone
- undefined functions go out the door — and crash on arrival
- requirements ship missing — and the feature is half-built
- a false "done" burns time → redirect → rework
- it breaks the one rule that doesn't bend: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY flavor of "it works" or "it's done"
- ANY note of satisfaction
- ANY upbeat read on the state of the work
- A commit, a PR, a task marked complete
- Stepping to the next task
- Handing work off to an agent

**The rule reaches:**
- The exact phrases
- Their paraphrases and synonyms
- Anything that merely implies success
- ANY message that hints the work is done or correct

## The Bottom Line

**Verification has no shortcut.**

Run the command. Read what comes back. THEN state the result.

There is no exception to this.