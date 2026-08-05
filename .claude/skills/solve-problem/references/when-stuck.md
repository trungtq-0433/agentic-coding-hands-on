# When Stuck - Problem-Solving Dispatch

Being stuck is not one thing — it comes in kinds, and each kind answers to a different move. Find the symptom, then pick the move that fits it.

## Dispatch Flowchart

```
YOU'RE STUCK
│
├─ Complexity spiraling? Same thing 5+ ways? Growing special cases?
│  └─→ USE: Simplification Cascades
│
├─ Can't find fitting approach? Conventional solutions inadequate?
│  └─→ USE: Collision-Zone Thinking
│
├─ Same issue different places? Reinventing wheels? Feels familiar?
│  └─→ USE: Meta-Pattern Recognition
│
├─ Solution feels forced? "Must be done this way"? Stuck on assumptions?
│  └─→ USE: Inversion Exercise
│
├─ Will this work at production? Edge cases unclear? Unsure of limits?
│  └─→ USE: Scale Game
│
└─ Code broken? Wrong behavior? Test failing?
   └─→ USE: Debugging skill (systematic-debugging)
```

## Stuck-Type → Technique Map

| How You're Stuck | Symptom Details | Use This |
|------------------|-----------------|----------|
| **Complexity spiraling** | Same thing 5+ ways, growing special cases, excessive if/else | simplification-cascades.md |
| **Need innovation** | Conventional inadequate, can't find fitting approach, need breakthrough | collision-zone-thinking.md |
| **Recurring patterns** | Same issue different places, reinventing wheels, déjà vu feeling | meta-pattern-recognition.md |
| **Forced by assumptions** | "Must be done this way", can't question premise, forced solution | inversion-exercise.md |
| **Scale uncertainty** | Production unclear, edge cases unknown, unsure of limits | scale-game.md |
| **Code broken** | Wrong behavior, test failing, unexpected output | debugging skill |

## Process

1. **Name the stuck-type** - which symptom above is yours?
2. **Open that move** - read its reference file
3. **Run it** - follow the process it lays out
4. **Log the attempt** - what moved, what didn't?
5. **Still jammed?** - switch to another move, or stack two

## Combining Techniques

A handful of problems give way only to two moves working together:

- **Simplification + Meta-pattern** - Find pattern → simplify all instances
- **Collision + Inversion** - Force metaphor → invert assumptions
- **Scale + Simplification** - Test extremes → reveal what to eliminate
- **Meta-pattern + Scale** - Universal pattern → test at extremes

## When Nothing Works

When every move comes up empty:
1. **Reframe the problem** - are you even solving the right one?
2. **Borrow another set of eyes** - say it out loud to someone
3. **Step away** - distance has a way of handing you the answer
4. **Shrink the scope** - crack a smaller version first
5. **Interrogate the constraints** - real, or just assumed?

## Remember

- Match the symptom to the move
- One move at a time
- Reach for a second only when the first stalls
- Keep a record of what you tried
- Stuck is a moment, not a verdict
