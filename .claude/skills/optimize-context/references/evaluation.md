# Evaluation

Put a method behind judging how an agent performs and whether your context choices paid off.

## Key Finding: 95% Performance Variance

- **Token usage**: 80% of variance
- **Tool calls**: ~10% of variance
- **Model choice**: ~5% of variance

**Implication**: getting the token budget right beats reaching for a bigger model.

## Multi-Dimensional Rubric

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Factual Accuracy | 30% | Checked against ground truth |
| Completeness | 25% | How much of the ask it covers |
| Tool Efficiency | 20% | Did it pick the right tools |
| Citation Accuracy | 15% | Do the sources back the claims |
| Source Quality | 10% | Are the sources authoritative |

## Evaluation Methods

### LLM-as-Judge

Watch for the judge's biases:
- **Position**: whatever sits first tends to win
- **Length**: the longer answer scores higher
- **Self-enhancement**: the judge favors its own output
- **Verbosity**: more detail reads as more correct

**Mitigation**: swap the positions, and prompt against the bias

### Pairwise Comparison

```python
score_ab = judge.compare(output_a, output_b)
score_ba = judge.compare(output_b, output_a)
consistent = (score_ab > 0.5) != (score_ba > 0.5)
```

### Probe-Based Testing

| Probe | Tests | Example |
|-------|-------|---------|
| Recall | Facts | "What was the error?" |
| Artifact | Files | "Which files modified?" |
| Continuation | Planning | "What's next?" |
| Decision | Reasoning | "Why chose X?" |

## Test Set Design

```python
class TestSet:
    def sample_stratified(self, n):
        per_level = n // 3
        return (
            sample(self.simple, per_level) +
            sample(self.medium, per_level) +
            sample(self.complex, per_level)
        )
```

## Production Monitoring

```python
class Monitor:
    sample_rate = 0.01  # 1% sampling
    alert_threshold = 0.85

    def check(self, scores):
        if avg(scores) < self.alert_threshold:
            self.alert(f"Quality degraded: {avg(scores):.2f}")
```

## Guidelines

1. Judge the outcome first; only drop to step-by-step when you must
2. Score against a rubric with several dimensions
3. Defang the LLM-as-Judge biases
4. Draw test cases across a spread of difficulty
5. Keep monitoring running, not one-off
6. Put token efficiency at the center — it is 80% of the variance

## Related

- [Context Compression](./context-compression.md)
- [Tool Design](./tool-design.md)
