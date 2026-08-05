---
name: receiving-code-review
description: Reach for this when review feedback lands on your desk and before you act on any of it — most of all when a note reads vague or technically shaky. The job is to weigh and verify, not to nod along.
---

# Code Review Reception

**Core principle:** Check it before you build on it. Ask before you fill the gap with a guess. Correctness outranks keeping things pleasant.

## Response Pattern

```
1. READ: Take in the whole note first; hold the reaction
2. UNDERSTAND: Put the ask in your own words — or ask if you can't
3. VERIFY: Hold it up against what the code actually does
4. EVALUATE: Does it hold for THIS codebase, specifically?
5. RESPOND: Either a technical yes or a reasoned no
6. IMPLEMENT: One change at a time, each one tested
```

## Forbidden Responses

❌ "You're absolutely right!" / "Great point!" / "Thanks for [anything]"
❌ "Let me implement that now" (before verification)

✅ Restate technical requirement
✅ Ask clarifying questions
✅ Push back with technical reasoning
✅ Just start working (actions > words)

## Handling Unclear Feedback

```
IF any item unclear:
  STOP - build nothing yet
  ASK for clarification on EVERY unclear item at once

WHY: The items often interlock. Grasp half of it and you build the wrong thing.
```

## Source-Specific Handling

**Human partner:** Trusted — once you understand it, build it; spare the performative thanks

**External reviewers:**
```
BEFORE implementing:
  1. Does it actually hold for THIS codebase?
  2. Would it break something already working?
  3. Is there a reason it's built the way it is now?
  4. Does it survive every platform and version we ship?

IF wrong: Push back, and bring the technical reasoning
IF can't verify: Name the limit, ask which way to go
IF conflicts with partner's decisions: Halt, talk it through first
```

## YAGNI Check

```
IF reviewer says "implement it properly":
  grep the tree for who actually calls it
  IF unused: "Nothing calls this. Cut it (YAGNI)?"
  IF used: then yes — implement it properly
```

## Implementation Order

```
1. Settle the unclear items FIRST
2. Work the order: blocking → simple → complex
3. Test them one by one
4. Confirm nothing regressed
```

## When To Push Back

- It would break something that works today
- The reviewer is missing context you have
- It adds an unused feature (YAGNI)
- It's simply wrong for this stack
- Legacy or compatibility constraints demand the current shape
- It cuts against a settled architectural call

**How:** Lead with the reasoning, ask pointed questions, point at the tests that prove it

## Acknowledging Correct Feedback

✅ "Fixed. [Brief description]"
✅ "Good catch - [issue]. Fixed in [location]."
✅ Just fix it (actions > words)

❌ ANY gratitude or performative expression

## Correcting Wrong Pushback

✅ "You were right - checked [X], it does [Y]. Implementing."
❌ Long apology, defending, over-explaining

## Quick Reference

| Mistake | Fix |
|---------|-----|
| Performative agreement | Restate the requirement, or just act |
| Building it blind | Verify against the codebase first |
| Batching with no tests | One change at a time |
| Taking the reviewer as right | Check whether it breaks anything |
| Dodging the pushback | Correctness beats comfort |

## Bottom Line

Feedback from outside is a proposal to weigh, never a command to obey.
Verify it. Question it. Then build.
