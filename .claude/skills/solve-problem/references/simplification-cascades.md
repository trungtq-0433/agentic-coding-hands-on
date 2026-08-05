# Simplification Cascades

Find one insight eliminating multiple components. "If this is true, we don't need X, Y, Z."

## Core Principle

Finish the sentence **"everything here is a special case of..."** and watch the complexity fall away.

One abstraction that pulls its weight beats ten clever hacks.

## When to Use

| Symptom | Action |
|---------|--------|
| Same thing implemented 5+ ways | Abstract the common pattern |
| Growing special case list | Find the general case |
| Complex rules with exceptions | Find rule with no exceptions |
| Excessive config options | Find defaults working for 95% |

## The Pattern

**Watch for:**
- The same concept built more than once, each slightly different
- Special-case handling scattered through the code
- "A, B, C, and D each need their own treatment..."
- Rules dense with exceptions

**Then ask:** "What if, underneath, these are all the same thing?"

## Examples

### Example 1: Stream Abstraction
- **Before:** Separate handlers for batch/real-time/file/network data
- **Insight:** "All inputs are streams - just different sources"
- **After:** One stream processor, multiple stream sources
- **Eliminated:** 4 separate implementations

### Example 2: Resource Governance
- **Before:** Session tracking, rate limiting, file validation, connection pooling (all separate)
- **Insight:** "All are per-entity resource limits"
- **After:** One ResourceGovernor with 4 resource types
- **Eliminated:** 4 custom enforcement systems

### Example 3: Immutability
- **Before:** Defensive copying, locking, cache invalidation, temporal coupling
- **Insight:** "Treat everything as immutable data + transformations"
- **After:** Functional programming patterns
- **Eliminated:** Entire classes of synchronization problems

## Process

1. **List variations** - What's implemented multiple ways?
2. **Find essence** - What's the same underneath?
3. **Extract abstraction** - What's the domain-independent pattern?
4. **Test fit** - Do all cases fit cleanly?
5. **Measure cascade** - How many things become unnecessary?

## Red Flags

Signs you're missing a cascade:
- "Just need to add one more case..." (repeating forever)
- "These are similar but different" (maybe they're the same?)
- Refactoring feels like whack-a-mole (fix one, break another)
- Growing configuration file
- "Don't touch that, it's complicated" (complexity hiding pattern)

## Success Metrics

- **Chase 10x wins, not 10% trims**
- Score it by how much you can delete, not what you add
- More lines gone than lines written
- Config knobs retired
- Special cases folded into one

## Remember

- The pattern is almost always already there — recognition is the whole job
- A real cascade looks obvious once you've found it
- Sanity-check it: "does this one form cover every existing case?"
- Write the insight down so the next person doesn't rediscover it cold
