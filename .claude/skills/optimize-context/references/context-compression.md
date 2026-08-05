# Context Compression

How to keep a long session alive once it outgrows the window.

## Core Insight

Tune the **tokens-per-task** — what it costs to reach the finish — not the tokens of any one request.
Squeeze too hard and the re-fetching it forces will cost you more than holding the material would have.

## Compression Methods

| Method | Compression | Quality | Best For |
|--------|-------------|---------|----------|
| **Anchored Iterative** | 98.6% | 3.70/5 | Best balance |
| **Regenerative Full** | 98.7% | 3.44/5 | Readability |
| **Opaque** | 99.3% | 3.35/5 | Max compression |

## Anchored Iterative Summary Template

```markdown
## Session Intent
Original goal: [preserved]

## Files Modified
- file.py: Changes made

## Decisions Made
- Key decisions with rationale

## Current State
Progress summary

## Next Steps
1. Next action items
```

**On compression**: Fold fresh content into the sections that already exist — don't rebuild them from scratch.

## Compression Triggers

| Strategy | Trigger | Use Case |
|----------|---------|----------|
| Fixed threshold | 70-80% utilization | The default choice |
| Sliding window | Keep last N turns + summary | Back-and-forth chat |
| Task-boundary | At logical completion | Multi-step workflows |

## Artifact Trail Problem

This is the dimension that scores worst (2.2-2.5/5.0). A coding agent has to keep an explicit ledger of:
- Which files it created, changed, or read
- Function and variable names, plus error messages

**Solution**: give the summary a section dedicated to artifacts.

## Probe-Based Evaluation

| Probe Type | Tests | Example |
|------------|-------|---------|
| Recall | Factual retention | "What was the error?" |
| Artifact | File tracking | "Which files modified?" |
| Continuation | Task planning | "What next?" |
| Decision | Reasoning chains | "Why chose X?" |

## Six Evaluation Dimensions

1. **Accuracy** - Is the technical detail right
2. **Context Awareness** - Does it still hold the conversation state
3. **Artifact Trail** - File tracking (weak almost everywhere)
4. **Completeness** - How much ground it covers
5. **Continuity** - Can work pick up where it left off
6. **Instruction Following** - Were the constraints honored

## Guidelines

1. Reach for anchored iterative when you want the best quality-per-token
2. Keep an explicit artifact-tracking section alive
3. Fire compression once utilization hits 70%
4. Merge into the existing sections instead of regenerating them
5. Judge with probes, not lexical overlap scores

## Related

- [Context Optimization](./context-optimization.md)
- [Evaluation](./evaluation.md)
