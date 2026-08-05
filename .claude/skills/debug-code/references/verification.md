# Verification Before Completion

Run the check, read its output, and only then say the work passed.

## Core Principle

**Evidence first, claims second — every time.**

Calling work done without checking isn't a shortcut. It's a lie.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the check in this very message, you can't say it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | A prior run, "should pass" |
| Linter clean | Linter output: 0 errors | A partial check, guesswork |
| Build succeeds | Build command: exit 0 | Linter green, logs that look fine |
| Bug fixed | Original symptom retested: passes | Code edited, fix assumed |
| Regression test works | Red-green cycle verified | One green run |
| Agent completed | VCS diff shows the changes | Agent reports "success" |
| Requirements met | Checklist walked line by line | The tests being green |

## Red Flags - STOP

- Hedging with "should", "probably", "seems to"
- Celebrating before you've checked ("Great!", "Perfect!", "Done!")
- About to commit/push/open a PR without a check
- Taking an agent's success report on faith
- Leaning on a partial check
- Telling yourself "just this once"
- Tired and wanting to be finished
- **ANY phrasing that implies success when no check has run**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the check |
| "I'm confident" | Confidence isn't evidence |
| "Just this once" | No exceptions |
| "The linter passed" | A linter isn't a compiler |
| "The agent said success" | Confirm it yourself |
| "A partial check is enough" | Partial proves nothing |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks right"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I wrote the regression test" (with no red-green run)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "The linter passed" (a linter doesn't compile anything)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, so the phase is done"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Take the agent's report at its word
```

## When To Apply

**ALWAYS before:**
- ANY flavor of success or completion claim
- ANY note of satisfaction
- ANY upbeat statement about where the work stands
- Committing, opening a PR, marking a task done
- Picking up the next task
- Handing work to agents

**The rule covers:**
- Exact phrases
- Paraphrases and synonyms
- Anything that hints at success
- ANY message implying the work is done or correct

## The Bottom Line

**Verification has no shortcut.**

Run the command. Read what it prints. THEN state the result.

Non-negotiable.
