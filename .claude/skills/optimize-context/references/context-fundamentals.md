# Context Fundamentals

Context is everything you hand the model to get a task done — the whole input, nothing left implicit.

## Anatomy of Context

| Component | Purpose | Token Impact |
|-----------|---------|--------------|
| System Prompt | Who the agent is, its limits and rules | Stable, cacheable |
| Tool Definitions | Action contracts, params and returns | Grows with capabilities |
| Retrieved Docs | Domain knowledge, fetched just-in-time | Variable, selective |
| Message History | Conversation state and task progress | Accumulates over time |
| Tool Outputs | What actions hand back | 83.9% of typical context |

## Attention Mechanics

- **U-shaped curve**: The two ends pull more attention than anything sitting between them
- **Attention budget**: n tokens means n^2 pairwise relationships, and the budget thins as the count climbs
- **Position encoding**: Interpolation stretches to longer sequences, but quality slips as it does
- **First-token sink**: The BOS token soaks up an outsized share of attention

## System Prompt Structure

```xml
<BACKGROUND_INFORMATION>Domain knowledge, role definition</BACKGROUND_INFORMATION>
<INSTRUCTIONS>Step-by-step procedures</INSTRUCTIONS>
<TOOL_GUIDANCE>When/how to use tools</TOOL_GUIDANCE>
<OUTPUT_DESCRIPTION>Format requirements</OUTPUT_DESCRIPTION>
```

## Progressive Disclosure Levels

1. **Metadata** (~100 words) - Stays resident the whole time
2. **SKILL.md body** (<5k words) - Loads the moment the skill fires
3. **Bundled resources** (Unlimited) - Pulled in only on demand

## Token Budget Allocation

| Component | Typical Range | Notes |
|-----------|---------------|-------|
| System Prompt | 500-2000 | Steady — tune it once |
| Tool Definitions | 100-500 per tool | Hold the count under 20 |
| Retrieved Docs | 1000-5000 | Load only what is needed |
| Message History | Variable | Fold down at 70% |
| Reserved Buffer | 10-20% | Headroom for the reply |

## Document Management

**Strong identifiers**: name it `customer_pricing_rates.json`, never `data/file1.json`
**Chunk at semantic boundaries**: split on paragraphs and sections, not on a character count
**Include metadata**: carry the source, the date, and a relevance score

## Message History Pattern

```python
# Summary injection every 20 messages
if len(messages) % 20 == 0:
    summary = summarize_conversation(messages[-20:])
    messages.append({"role": "system", "content": f"Summary: {summary}"})
```

## Guidelines

1. Treat the window as finite — each extra token returns less
2. Park the must-read material where attention concentrates
3. Reach large documents through the file system rather than inlining them
4. Preload what stays constant; fetch what changes only when needed
5. Plan against a stated token budget, not a vague sense of room
6. Track usage and fire compaction triggers in the 70-80% band

## Related Topics

- [Context Degradation](./context-degradation.md) - Failure patterns
- [Context Optimization](./context-optimization.md) - Efficiency techniques
- [Memory Systems](./memory-systems.md) - External storage
