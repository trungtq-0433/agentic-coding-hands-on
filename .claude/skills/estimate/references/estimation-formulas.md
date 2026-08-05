# Estimation Formulas

Step-by-step calculation methodology for project estimates.

## Core Formula

```
estimate_days = base_effort × complexity_factor × tech_multiplier × experience_factor × (1 + buffer)
```

### Components

1. **Base Effort**: Man-days from knowledge-base.md by task type
2. **Complexity Factor**: Product of applicable complexity multipliers
3. **Tech Multiplier**: Product of tech stack multipliers
4. **Experience Factor**: Team profile adjustment
5. **Buffer**: Risk-based buffer percentage

## Story Point Mapping

Story points use Fibonacci sequence for relative sizing:

| Story Points | Man-Days | Complexity |
|--------------|----------|------------|
| 1 | 0.5 | Trivial task |
| 2 | 1.0 | Simple task |
| 3 | 1.5 | Small feature |
| 5 | 2.5 | Medium feature |
| 8 | 4.0 | Large feature |
| 13 | 6.5 | Complex feature |
| 21 | 10.5 | Epic (should split) |

**Conversion**: 1 SP ≈ 0.5 man-days

## Calculation Examples

### Example 1: Simple CRUD Endpoint

```
Task: Create user CRUD API
Base effort: 1.0 days (crud.standard)
Complexity: 1.0 (simple)
Tech: 1.0 (familiar stack)
Experience: 1.0 (mid-level team)
Buffer: 20%

Estimate = 1.0 × 1.0 × 1.0 × 1.0 × 1.2 = 1.2 days
Story Points = round(1.2 / 0.5) = 2 SP
```

### Example 2: Complex Feature with New Tech

```
Task: Payment integration with Stripe
Base effort: 5.0 days (payments.integration)
Complexity: 1.5 (medium) × 1.4 (unclear requirements) = 2.1
Tech: 1.2 (moderate familiarity)
Experience: 1.3 (junior team)
Buffer: 30% (high risk)

Estimate = 5.0 × 2.1 × 1.2 × 1.3 × 1.3 = 21.3 days
Story Points = round(21.3 / 0.5) = 43 SP → Split into smaller tasks
```

### Example 3: Authentication System

```
Task: OAuth + MFA authentication
Base effort: 3.0 (oauth_single) + 2.0 (mfa) = 5.0 days
Complexity: 2.5 (complex) × 1.3 (compliance) = 3.25 → capped at 3.0
Tech: 1.1 (auth0)
Experience: 0.8 (senior team)
Buffer: 25%

Estimate = 5.0 × 3.0 × 1.1 × 0.8 × 1.25 = 16.5 days
Story Points = round(16.5 / 0.5) = 33 SP → Consider splitting
```

## Complexity Factor Calculation

Multiply all applicable factors, cap at 3.0x:

```python
complexity = min(3.0,
    base_complexity
    × requirements_clarity
    × integration_complexity
    × performance_requirements
    × security_requirements
)
```

## Experience Factor Calculation

```python
experience = (
    experience_level_multiplier
    × domain_familiarity_multiplier
    × team_size_multiplier
)
```

## Buffer Selection Guide

| Confidence | Buffer | When to Use |
|------------|--------|-------------|
| High | 15% | Clear requirements, familiar tech, experienced team |
| Medium | 25% | Some unknowns, manageable risks |
| Low | 40% | Significant unknowns, high-risk areas |

## Validation Rules

Before finalizing estimates:

1. **No task > 13 SP** - Split larger tasks
2. **Buffer ≥ 10%** - Always include buffer
3. **SP/Man-Days ratio** - Should be ~0.5 (±30%)
4. **Complexity distribution** - 20-50% simple, 30-50% medium, 10-30% complex
5. **Testing phase** - Must be ≥15% of development time
