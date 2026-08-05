# Risk Patterns & Validation Thresholds

Load this when performing risk assessment (Step 6) and final validation.

## Technical Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| integration complexity | high | 1.3x |
| new technology | medium | 1.4x |
| performance requirements | high | 1.25x |
| security sensitive | critical | 1.35x |

## Scope Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| unclear requirements | high | 1.5x |
| scope creep | medium | 1.2x |
| complex business logic | medium | 1.3x |

## Resource Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| team availability | high | 1.4x |
| skill gaps | medium | 1.35x |

## External Risks

| Risk Type | Impact | Probability Multiplier |
|-----------|--------|------------------------|
| vendor dependency | medium | 1.25x |
| regulatory compliance | high | 1.3x |

## Validation Thresholds

### Estimate Bounds

| Metric | Min | Max | Warning |
|--------|-----|-----|--------|
| Story Points (per req) | 1 | 21 | >13 |
| Man-Days (per req) | 0.25 | 20 | >10 |

### Ratio Checks

- **SP to Man-Days ratio**: 0.5 (1 SP ≈ 0.5 days)
- **Tolerance**: ±30%
