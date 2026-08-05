# Inversion Exercise

Flip core assumptions to reveal hidden constraints and alternative approaches. "What if the opposite were true?"

## Core Principle

**Inversion drags hidden assumptions into the light.** Turn the rule on its head and now and then the upside-down version is the one that's actually true.

## When to Use

| Symptom | Action |
|---------|--------|
| "There's only one way" | Flip the assumption |
| Solution feels forced | Invert the constraints |
| Can't articulate why necessary | Question the "must" |
| "This is just how it's done" | Try the opposite |

## Quick Reference

| Normal Assumption | Inverted | What It Reveals |
|-------------------|----------|-----------------|
| Cache to reduce latency | Add latency to enable caching | Debouncing patterns |
| Pull data when needed | Push data before needed | Prefetching, eager loading |
| Handle errors when occur | Make errors impossible | Type systems, contracts |
| Build features users want | Remove features users don't need | Simplicity >> addition |
| Optimize for common case | Optimize for worst case | Resilience patterns |

## Process

1. **List core assumptions** - What "must" be true?
2. **Invert each systematically** - "What if opposite were true?"
3. **Explore implications** - What would we do differently?
4. **Find valid inversions** - Which actually work somewhere?
5. **Document insights** - What did we learn?

## Detailed Example

**Problem:** Users say the app feels slow

**Normal approach:** make everything faster
- Add caching
- Optimize queries
- Use CDN
- Reduce bundle size

**Inverted approach:** put deliberate slowness in a few chosen spots
- **Debounce search** - Add latency → enable better results (wait for full query)
- **Rate limit requests** - Add friction → prevent abuse, improve for others
- **Lazy load content** - Delay loading → reduce initial load time
- **Progressive rendering** - Show slower → perceived performance

**Insight:** slowness, placed on purpose, can be the thing that improves the experience

## Valid vs Invalid Inversions

**Valid inversion example:**
- Normal: "Store data in database"
- Inverted: "Derive data on-demand instead of storing"
- Valid when: Computation cheaper than storage, data changes frequently

**Invalid inversion example:**
- Normal: "Validate user input"
- Inverted: "Trust all user input"
- Invalid because: Security vulnerability, not context-dependent

**Test validity:** Does the inversion work in ANY context? If yes, it's valid somewhere.

## Common Inversions

- **Eager → Lazy** (or vice versa)
- **Push → Pull** (or vice versa)
- **Store → Compute** (or vice versa)
- **Optimize → Simplify** (or vice versa)
- **Add features → Remove features** (or vice versa)

## Red Flags

You need inversion exercise when:
- "There's only one way to do this"
- Forcing solution that feels wrong
- Can't articulate why approach is necessary
- "This is just how it's done"
- Stuck on unquestioned assumptions

## Remember

- Not every flip holds up — probe where it breaks
- A flip that works somewhere is telling you the rule was context-bound all along
- Once in a while the opposite simply *is* the answer
- Treat every "it must be" as a claim to be tested
- Keep notes on the flips that worked and the ones that didn't — both teach
