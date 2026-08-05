# Systematic Debugging

A four-phase discipline that forces you to prove the root cause before you reach for a fix.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Until Phase 1 is behind you, you have no business proposing a fix.

## The Four Phases

Each phase closes before the next one opens.

### Phase 1: Root Cause Investigation

**BEFORE you attempt ANY fix:**

1. **Read the error carefully** - Don't glance past warnings or errors; read every line of the stack trace
2. **Reproduce it reliably** - Can you trigger it on demand? What are the exact steps? Can't reproduce it → go collect more data
3. **Check what changed** - Git diff, recent commits, fresh dependencies, config edits
4. **Gather evidence across components**
   - At EACH component boundary: log what goes in and out, confirm the environment carries through
   - One run to surface evidence of WHERE it breaks
   - THEN read that evidence to name the failing component
5. **Trace the data flow** - Where is the bad value born? Walk up the call stack until you reach the source (see root-cause-tracing.md)

### Phase 2: Pattern Analysis

**Find the pattern before you touch anything:**

1. **Find code that works** - Locate similar, working code in the same codebase
2. **Read the reference in full** - Take in the working implementation COMPLETELY; understand it before you borrow from it
3. **List the differences** - Every difference, however tiny — never wave one off as "that couldn't matter"
4. **Map the dependencies** - What other components, settings, config, or environment does it lean on?

### Phase 3: Hypothesis and Testing

**Work like a scientist:**

1. **State one hypothesis** - "I think X is the root cause because Y" — concrete, not hand-wavy
2. **Test it minimally** - The SMALLEST change that tests the idea, one variable at a time
3. **Confirm before moving on** - Worked? → Phase 4. Failed? → a NEW hypothesis. DON'T pile on more fixes
4. **When you don't know** - Say "I don't understand X" plainly, don't bluff, ask for help

### Phase 4: Implementation

**Repair the root cause, never the symptom:**

1. **Write a failing test** - Simplest reproduction, automated where you can — you MUST have it before fixing
2. **Apply one fix** - Address the root cause you found, ONE change, no "while I'm in here" extras
3. **Confirm the fix** - Does the test pass? Anything else broken? Is the issue truly gone?
4. **If the fix misses**
   - STOP. Count it: how many fixes have you tried?
   - Under 3: back to Phase 1 and re-analyze with what you now know
   - **3 or more: STOP and question the architecture**
5. **After 3+ failed fixes: question the architecture**
   - The tell: each fix uncovers another shared-state or coupling problem somewhere else
   - STOP and challenge the fundamentals: is the pattern sound? Is the architecture wrong?
   - Talk it through with your human partner before another fix

## Red Flags - STOP and Follow Process

If you hear yourself thinking:
- "Quick patch now, I'll investigate later"
- "Let me just change X and see"
- "Stack up a few changes, then run tests"
- "Skip the test, I'll eyeball it"
- "Probably X — I'll fix that"
- "I don't fully get it but this might do it"
- "One more attempt" (after 2+ already)

**Every one means:** STOP. Back to Phase 1.

## When Your Human Partner Says You're Off Track

- "Is that not happening?" - You assumed instead of checking
- "Will it show us...?" - You should have gathered evidence
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question the fundamentals, not just the symptom
- "We're stuck?" (frustrated) - The approach isn't working

**Hear any of these:** STOP. Back to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "It's simple, I can skip the process" | Simple issues have root causes too |
| "Emergency — no time for process" | Systematic beats guess-and-check on the clock |
| "Try this first, investigate after" | The first fix sets the pattern — get it right from the start |
| "One more attempt" (after 2+ failures) | 3+ failures means an architectural problem |

## Real-World Impact

What debugging sessions show:
- Systematic approach: a fix in 15-30 minutes
- Random fixes: 2-3 hours of thrashing
- Fixed on the first try: 95% vs 40%
- Fresh bugs introduced: near zero vs routine
