---
name: tkm:solve-problem
description: When the work refuses to move — a tangle that keeps growing, a problem that has already eaten three attempts — reach here. Named techniques for the distinct ways a problem stalls: complexity spirals, innovation blocks, repeating patterns, assumptions that box you in, simplification cascades, and scale uncertainty.
argument-hint: "[problem description]"
metadata:
  author: takumi-agent-kit
  version: "2.0.0"
module: specialized-output
triggers: ["stuck", "can't figure out", "recurring problem", "break the pattern"]
---

# The Impossible Joint

Sooner or later the bench hands you a joint that looks like it cannot be cut: two faces that refuse to meet, a constraint that seems to forbid every move, a problem that has already swallowed three attempts.
A skilled hand does not lean harder on the chisel. They stop, ask *why* the joint keeps failing, rethink what it actually has to do, and find the route that was always there — hidden only by the belief that one route was all there was.

What follows is a set of deliberate moves, one per flavor of stuck. Each is aimed at a particular way work jams up.

## When to Apply

Reach for these when you hit:
- **Complexity spiraling** - the same idea coded several ways, special cases multiplying, branches everywhere
- **Innovation blocks** - the usual answers fall short and you need a genuine leap
- **Recurring patterns** - the same trouble keeps surfacing in different corners, solved fresh each time
- **Assumption constraints** - cornered into "the only way", unable to challenge the premise
- **Scale uncertainty** - no clear read on whether it holds in production, edge cases still dark
- **General stuck-ness** - jammed, but unsure which move fits

## Quick Dispatch

**Read the symptom, pick the move:**

| Stuck Symptom | Technique | Reference |
|---------------|-----------|-----------|
| Same thing implemented 5+ ways, growing special cases | **Simplification Cascades** | `references/simplification-cascades.md` |
| Conventional solutions inadequate, need breakthrough | **Collision-Zone Thinking** | `references/collision-zone-thinking.md` |
| Same issue in different places, reinventing wheels | **Meta-Pattern Recognition** | `references/meta-pattern-recognition.md` |
| Solution feels forced, "must be done this way" | **Inversion Exercise** | `references/inversion-exercise.md` |
| Will this work at production? Edge cases unclear? | **Scale Game** | `references/scale-game.md` |
| Unsure which technique to use | **When Stuck** | `references/when-stuck.md` |

## Core Techniques

### 1. Simplification Cascades
Find one insight eliminating multiple components. "If this is true, we don't need X, Y, Z."

**Key insight:** Everything is a special case of one general pattern.

**Red flag:** "Just need to add one more case..." (repeating forever)

### 2. Collision-Zone Thinking
Force unrelated concepts together to discover emergent properties. "What if we treated X like Y?"

**Key insight:** Revolutionary ideas from deliberate metaphor-mixing.

**Red flag:** "I've tried everything in this domain"

### 3. Meta-Pattern Recognition
Spot patterns appearing in 3+ domains to find universal principles.

**Key insight:** Patterns in how patterns emerge reveal reusable abstractions.

**Red flag:** "This problem is unique" (probably not)

### 4. Inversion Exercise
Flip core assumptions to reveal hidden constraints. "What if the opposite were true?"

**Key insight:** Valid inversions reveal context-dependence of "rules."

**Red flag:** "There's only one way to do this"

### 5. Scale Game
Test at extremes (1000x bigger/smaller, instant/year-long) to expose fundamental truths.

**Key insight:** What works at one scale fails at another.

**Red flag:** "Should scale fine" (without testing)

## Application Process

1. **Name the stuck-type** - which symptom above does this match?
2. **Open the matching guide** - pull the full technique from `references/`
3. **Work it through** - walk its process step by step
4. **Write down what you learn** - both the wins and the dead ends
5. **Stack moves when needed** - some problems yield only to two techniques together

## Combining Techniques

The pairings that earn their keep:
- **Simplification + Meta-pattern** - spot the shared pattern first, then collapse every instance of it
- **Collision + Inversion** - borrow a metaphor, then flip the assumptions it smuggles in
- **Scale + Simplification** - push to the extreme; what survives shows what you can cut
- **Meta-pattern + Scale** - take the universal pattern and stress it at the limits

## References

Pull the detailed guides as the problem calls for them:
- `references/when-stuck.md` - Dispatch flowchart and decision tree
- `references/simplification-cascades.md` - Cascade detection and extraction
- `references/collision-zone-thinking.md` - Metaphor collision process
- `references/meta-pattern-recognition.md` - Pattern abstraction techniques
- `references/inversion-exercise.md` - Assumption flipping methodology
- `references/scale-game.md` - Extreme testing procedures
- `references/attribution.md` - Source and adaptation notes
