# Core Sequential Thinking Patterns

The bread-and-butter moves: when to rewrite a step, when to split into branches.

## Revision Patterns

### Assumption Challenge
You leaned on something early; fresh data says it does not hold.
```
Thought 1/5: Assume X is bottleneck
Thought 4/5 [REVISION of Thought 1]: X adequate; Y is actual bottleneck
```

### Scope Expansion
The job turns out bigger than the framing you started with.
```
Thought 1/4: Fix bug
Thought 4/5 [REVISION of scope]: Architectural redesign needed, not patch
```

### Approach Shift
The first strategy cannot carry the requirements.
```
Thought 2/6: Optimize query
Thought 5/6 [REVISION of Thought 2]: Optimization + cache layer required
```

### Understanding Deepening
A later realization changes what the problem even is.
```
Thought 1/5: Feature broken
Thought 4/5 [REVISION of Thought 1]: Not bug—UX confusion issue
```

## Branching Patterns

### Trade-off Evaluation
Two candidates, each strong somewhere the other is weak.
```
Thought 3/7: Choose between X and Y
Thought 4/7 [BRANCH A]: X—simpler, less scalable
Thought 4/7 [BRANCH B]: Y—complex, scales better
Thought 5/7: Choose Y for long-term needs
```

### Risk Mitigation
Line up a fallback behind a primary path you are not sure of.
```
Thought 2/6: Primary: API integration
Thought 3/6 [BRANCH A]: API details
Thought 3/6 [BRANCH B]: Fallback: webhook
Thought 4/6: Implement A with B contingency
```

### Parallel Exploration
Two unrelated unknowns; work each on its own track.
```
Thought 3/8: Two unknowns—DB schema & API design
Thought 4/8 [BRANCH DB]: DB options
Thought 4/8 [BRANCH API]: API patterns
Thought 5/8: Integrate findings
```

### Hypothesis Testing
Several possible causes; rule them in or out one by one.
```
Thought 2/6: Could be A, B, or C
Thought 3/6 [BRANCH A]: Test A—not cause
Thought 3/6 [BRANCH B]: Test B—confirmed
Thought 4/6: Root cause via Branch B
```

## Adjustment Guidelines

**Raise the count when**: complexity shows up late, several concerns split apart, a claim still needs checking, or alternatives are worth laying out.

**Lower the count when**: one insight settles what you thought were many steps, the problem is plainer than expected, or adjacent steps fold into one.

**Example**:
```
Thought 1/5: Initial
Thought 3/7: Complexity (5→7)
Thought 5/8: Another aspect (7→8)
Thought 8/8 [FINAL]: Complete
```

## Anti-Patterns

**Premature Completion**: declaring done before checking → add a verification thought first.

**Revision Cascade**: rewriting again and again with no diagnosis → stop and name the root cause.

**Branching Explosion**: more branches than you can hold → cap at 2–3 and converge before opening new ones.

**Context Loss**: leaving earlier insights behind → cite the prior thought by number and carry it forward.
