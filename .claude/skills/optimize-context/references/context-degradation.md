# Context Degradation Patterns

As the window fills, quality erodes in ways you can predict — it slides along a continuum, it does not flip off all at once.

## Degradation Patterns

| Pattern | Cause | Detection |
|---------|-------|-----------|
| **Lost-in-Middle** | U-shaped attention | Recall of buried facts falls 10-40% |
| **Context Poisoning** | Errors snowball through back-reference | Hallucinations stick even after correction |
| **Context Distraction** | Noise drowns the signal | One distractor is enough to hurt output |
| **Context Confusion** | Several tasks blur together | Wrong tool calls, requirements bleed |
| **Context Clash** | Facts contradict each other | Outputs conflict, reasoning wobbles |

## Lost-in-Middle Phenomenon

- Anything parked in the middle loses 10-40% of its recall
- The model pours a huge slice of attention into the first token (the BOS sink)
- The longer the context runs, the less attention the middle tokens can claim
- **Mitigation**: Keep the critical material at the head and the tail

```markdown
[CURRENT TASK]              # Beginning - high attention
- Critical requirements

[DETAILED CONTEXT]          # Middle - lower attention
- Supporting details

[KEY FINDINGS]              # End - high attention
- Important conclusions
```

## Context Poisoning

**Entry points**:
1. Tool outputs that come back malformed or carry errors
2. Retrieved docs holding wrong or stale facts
3. Model-written summaries that smuggle in hallucinations

**Detection symptoms**:
- Tasks that used to succeed start coming back worse
- Tools get picked or parameterized wrong
- Hallucinations that refuse to clear

**Recovery**:
- Cut the history back to before the poison entered
- Add an explicit note and ask for a re-evaluation
- Reset to a clean window, carrying forward only what you have verified

## Model Degradation Thresholds

| Model | Degradation Onset | Severe Degradation |
|-------|-------------------|-------------------|
| GPT-5.2 | ~64K tokens | ~200K tokens |
| Claude Opus 4.5 | ~100K tokens | ~180K tokens |
| Claude Sonnet 4.5 | ~80K tokens | ~150K tokens |
| Gemini 3 Pro | ~500K tokens | ~800K tokens |

## Four-Bucket Mitigation

1. **Write**: Stash it outside the window (scratchpads, files)
2. **Select**: Pull back only what bears on the task (retrieval, filtering)
3. **Compress**: Trim the token count (summarization)
4. **Isolate**: Hand pieces to sub-agents (partitioning)

## Detection Heuristics

```python
def calculate_health(utilization, degradation_risk, poisoning_risk):
    """Health score: 1.0 = healthy, 0.0 = critical"""
    score = 1.0
    score -= utilization * 0.5 if utilization > 0.7 else 0
    score -= degradation_risk * 0.3
    score -= poisoning_risk * 0.2
    return max(0, score)

# Thresholds: healthy >0.8, warning >0.6, degraded >0.4, critical <=0.4
```

## Guidelines

1. Track how performance moves with context length
2. Keep the critical material at the head and the tail
3. Compact before degradation sets in, not after
4. Vet retrieved docs before they enter the window
5. Version your facts so stale copies cannot clash with fresh ones
6. Segment the work so tasks do not blur into confusion
7. Build so that when it does degrade, it degrades gracefully

## Related Topics

- [Context Optimization](./context-optimization.md) - Mitigation techniques
- [Multi-Agent Patterns](./multi-agent-patterns.md) - Isolation strategies
