# Step 0: Scope Challenge

This runs ahead of research or design. The point is to nail down what's actually being asked before you spend hours on it.

## Skip Conditions

Don't bother with Step 0 when:
- `--level low` is explicitly on (the user has already signalled they want it lean)
- The task is plainly trivial — one-file fix, typo, config tweak
- The user says "just plan it", "quick", or something with the same urgency
- The description runs under 20 words and leaves nothing in doubt

## The 3 Questions

Answer these tightly before any planning:

### 1. What already exists?
- Comb the codebase for anything that already solves part or all of the sub-problems
- Look at the utilities, services, and patterns you could reuse as-is
- Raise a flag if the plan is about to rebuild something that's already here

### 2. What is the minimum change set?
- Pick out the work that could wait without holding the core goal hostage
- Catch the scope creep — the nice-to-haves wearing a requirement's clothes
- Be hard-nosed about what's genuinely needed versus what's just wishful

### 3. Complexity check
- Plan reaches past **8 files**? Push back — can the same goal land in fewer?
- Plan adds more than **2 new classes/services**? That's a smell. Earn each one.
- Plan runs over **3 phases**? See whether any of them fold together.

## Scope Modes

With the 3 questions answered, put the choice to the user through `AskUserQuestion`:

**Header:** "Scope Challenge"
**Question:** "Based on analysis, how should we scope this plan?"

| Option | Label | Description |
|--------|-------|-------------|
| A | **SCOPE EXPANSION** | Dream big — explore the 10-star version, research deeply, add delight features |
| B | **HOLD SCOPE** | Scope is right — focus on bulletproof execution, edge cases, test coverage |
| C | **SCOPE REDUCTION** | Strip to essentials — defer everything non-blocking, minimal phases |

## After Selection

### EXPANSION selected
- Nudge toward `--level high` (or add `--two`) if neither is set yet
- Let research roam into alternatives and the features sitting next door
- Tag any "stretch" items in the plan plainly as such
- A longer phase list is fine here

### HOLD selected
- Carry on with whatever level auto-detection landed on
- Honor the scope to the letter — no quiet trimming, no quiet padding
- Spend the effort on failure modes, edge cases, and test coverage
- Keep the phase count ordinary

### REDUCTION selected
- Nudge toward `--level low` if it isn't set yet
- Pitch the leanest version that still hits the core goal
- Push everything non-critical down into the "NOT in scope" section
- Fewer phases, a simpler architecture

## Critical Rule

**Whatever mode the user picks, hold to it.**

Don't:
- Quietly shrink the scope after the user chose HOLD or EXPANSION
- Quietly grow it after the user chose REDUCTION
- Reopen the scope argument in a later review section

Make your scope case once, here in Step 0. After that, commit to the chosen scope and do your best work inside it.

## Output Format

When the scope challenge is settled, print a short summary before moving on:

```
Scope Challenge:
- Existing code: [what was found that's reusable]
- Minimum changes: [what's essential vs deferrable]
- Complexity: [estimated files, new abstractions]
- Selected mode: [EXPANSION/HOLD/REDUCTION]
```

From here, move on to mode detection and the research phase.
