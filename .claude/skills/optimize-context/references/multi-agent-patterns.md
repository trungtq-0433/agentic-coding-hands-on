# Multi-Agent Patterns

Spread the work over several windows so context stays clean and the system can grow.

## Core Insight

A sub-agent earns its place by **walling off context**, not by playing a character.

## Token Economics

| Architecture | Multiplier | Use Case |
|--------------|------------|----------|
| Single agent | 1x | Simple tasks |
| Single + tools | ~4x | Moderate complexity |
| Multi-agent | ~15x | When context must be isolated |

**Key**: 80% of the swing in performance traces back to token usage.

## Patterns

### Supervisor/Orchestrator

```python
class Supervisor:
    def process(self, task):
        subtasks = self.decompose(task)
        results = [worker.execute(st, clean_context=True) for st in subtasks]
        return self.aggregate(results)
```

**Pros**: tight control, easy to keep a human in the loop | **Cons**: one chokepoint, meaning drifts as it relays

### Peer-to-Peer/Swarm

```python
def process_with_handoff(agent, task):
    result = agent.process(task)
    if "handoff" in result:
        return process_with_handoff(select_agent(result["to"]), result["state"])
    return result
```

**Pros**: no single point of failure, scales out | **Cons**: coordination gets hairy

### Hierarchical

Layered as Strategy → Planning → Execution
**Pros**: each layer owns one concern | **Cons**: you pay a coordination tax

## Context Isolation Patterns

| Pattern | Isolation | Use Case |
|---------|-----------|----------|
| Full delegation | None | Most raw capability |
| Instruction passing | High | Straightforward tasks |
| File coordination | Medium | When state is shared |

## Consensus Mechanisms

```python
def weighted_consensus(responses):
    scores = {}
    for r in responses:
        weight = r["confidence"] * r["expertise"]
        scores[r["answer"]] = scores.get(r["answer"], 0) + weight
    return max(scores, key=scores.get)
```

## Failure Recovery

| Failure | Mitigation |
|---------|------------|
| Bottleneck | Fix output schemas, add checkpoints |
| Overhead | Clean handoffs, batch the calls |
| Divergence | Set boundaries, check for convergence |
| Errors | Validate, trip circuit breakers |

## Guidelines

1. Go multi-agent to isolate context, never to act out roles
2. Take the ~15x token bill knowingly, as the price of the payoff
3. Wire in circuit breakers
4. Let files hold any state two agents share
5. Make the handoffs unambiguous
6. Check the output as it crosses from one agent to the next

## Related

- [Context Optimization](./context-optimization.md)
- [Evaluation](./evaluation.md)
