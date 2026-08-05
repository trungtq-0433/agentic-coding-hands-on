# Sequential Thinking — Advanced Techniques

Heavier moves for problems the basic patterns cannot hold.

## Spiral Refinement

Circle back to the same idea, each pass carrying more understanding than the last.

```
Thought 1/7: Initial design (surface)
Thought 2/7: Discover constraint A
Thought 3/7: Refine for A
Thought 4/7: Discover constraint B
Thought 5/7: Refine for both A and B
Thought 6/7: Integration reveals edge case
Thought 7/7: Final design addressing all constraints
```

**Use for**: systems whose constraints reveal themselves only as you build.
**Key**: each return tightens the design — it does not start over.

## Hypothesis-Driven Investigation

Float an explanation, test it, sharpen it, test again.

```
Thought 1/6: Observe symptoms
Thought 2/6 [HYPOTHESIS]: Explanation X
Thought 3/6 [VERIFICATION]: Test X—partial match
Thought 4/6 [REFINED HYPOTHESIS]: Adjusted Y
Thought 5/6 [VERIFICATION]: Test Y—confirmed
Thought 6/6 [FINAL]: Solution based on verified Y
```

**Use for**: debugging, root-cause work, diagnostics.
**Pattern**: propose → test → refine → re-test, around the loop.

## Multi-Branch Convergence

Open the alternatives in full, then build the best from their parts.

```
Thought 2/8: Multiple viable approaches
Thought 3/8 [BRANCH A]: Approach A benefits
Thought 4/8 [BRANCH A]: Approach A drawbacks
Thought 5/8 [BRANCH B]: Approach B benefits
Thought 6/8 [BRANCH B]: Approach B drawbacks
Thought 7/8 [CONVERGENCE]: Hybrid combining A's X with B's Y
Thought 8/8 [FINAL]: Hybrid superior to either alone
```

**Use for**: hard calls where no single option is clearly ahead.
**Key**: the blend often beats either branch standing alone.

## Progressive Context Deepening

Build the picture in layers — abstract first, concrete last.

```
Thought 1/9: High-level problem
Thought 2/9: Identify major components
Thought 3/9: Zoom into component A (detailed)
Thought 4/9: Zoom into component B (detailed)
Thought 5/9: Identify A-B interactions
Thought 6/9: Discover emergent constraint
Thought 7/9 [REVISION of 3-4]: Adjust for interaction
Thought 8/9: Verify complete system
Thought 9/9 [FINAL]: Integrated solution
```

**Use for**: laying out a system, deciding architecture, stitching pieces together.
**Pattern**: whole → parts → detail → interactions → integration.

## Reference

For Uncertainty Management, Revision Cascade Management, Meta-Thinking Calibration, and Parallel Constraint Satisfaction, see `advanced-strategies.md`.
