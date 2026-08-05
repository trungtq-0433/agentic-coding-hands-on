# Context Optimization

Stretch the usable window further with a handful of deliberate techniques.

## Four Core Strategies

| Strategy | Target | Reduction | When to Use |
|----------|--------|-----------|-------------|
| **Compaction** | Full context | 50-70% | Nearing the limit |
| **Observation Masking** | Tool outputs | 60-80% | Chatty outputs over 80% |
| **KV-Cache Optimization** | Repeated prefixes | 70%+ hit | Stable prompts |
| **Context Partitioning** | Work distribution | N/A | Tasks that can run in parallel |

## Compaction

As you near the ceiling, fold the context down into a summary.

**Priority**: Tool outputs → Old turns → Retrieved docs → Never: System prompt

```python
if context_tokens / context_limit > 0.8:
    context = compact_context(context)
```

**Preserve**: Key findings, decisions, commitments (drop the supporting detail)

## Observation Masking

Swap a bulky tool output for a short reference that stands in for it.

```python
if len(observation) > max_length:
    ref_id = store_observation(observation)
    return f"[Obs:{ref_id}. Key: {extract_key(observation)}]"
```

**Never mask**: anything the current task hinges on, the latest turn, reasoning still in play
**Always mask**: duplicated outputs, boilerplate, anything you have already summarized

## KV-Cache Optimization

Replay the cached Key/Value tensors whenever the prefix is byte-for-byte the same.

```python
# Cache-friendly ordering (stable first)
context = [system_prompt, tool_definitions]  # Cacheable
context += [unique_content]                   # Variable last
```

**Tips**: keep timestamps out of the stable sections, hold formatting steady, do not reshuffle structure

## Context Partitioning

Break the work apart across sub-agents, each with its own clean window.

```python
result = await sub_agent.process(subtask, clean_context=True)
coordinator.receive(result.summary)  # Only essentials
```

## Decision Framework

| Dominant Component | Apply |
|-------------------|-------|
| Tool outputs | Observation masking |
| Retrieved docs | Summarize, or split across agents |
| Message history | Compact, then summarize |
| Multiple | Combine strategies |

## Guidelines

1. Baseline the numbers before you touch anything
2. Compact first, mask second
3. Shape prompts so the cache stays warm
4. Partition before the window becomes a problem, not after
5. Watch whether the techniques keep paying off
6. Weigh the tokens you save against the quality you spend

## Related

- [Context Compression](./context-compression.md)
- [Memory Systems](./memory-systems.md)
