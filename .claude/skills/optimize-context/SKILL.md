---
name: tkm:optimize-context
description: Optimize the context window to prevent token waste — monitor usage, optimize consumption, debug context failures. Use when context percentage is high, rate limits loom, or agent memory architecture needs tuning.
argument-hint: "[topic or question]"
metadata:
  author: takumi-agent-kit
  version: "1.0.0"
module: project-context-management
triggers: ["context full", "token limit", "optimize context", "memory management"]
---

# Arranging the Workshop

Reach into a drawer crammed with the wrong things and the cut waits while you dig. A bench you cannot read costs you before the work even starts.
The context window is that bench, and each token that does not earn its place is a chisel laid where the plane should be.
The craft here is restraint: hand the model the smallest set of tokens that still carries the signal, so its thinking lands on the problem instead of sifting through clutter.

## When to Activate

- Building or troubleshooting agent systems
- Performance is hitting context ceilings
- Trimming cost or latency
- Wiring up multi-agent coordination
- Standing up memory layers
- Measuring how an agent performs
- Shipping LLM-driven pipelines

## Core Principles

1. **Quality over volume** - A few high-signal tokens outperform a wall of text
2. **Attention runs out** - The U-shaped curve rewards the start and the finish, not the middle
3. **Progressive disclosure** - Bring information in only at the moment it is needed
4. **Isolation prevents degradation** - Hand separable work to sub-agents
5. **Measure before optimizing** - You cannot tune what you have not baselined

**IMPORTANT:**
- Sacrifice grammar for the sake of concision.
- Ensure token efficiency while maintaining high quality.
- Pass these rules to subagents.

## Quick Reference

| Topic | When to Use | Reference |
|-------|-------------|-----------|
| **Fundamentals** | Learning how context is built and how attention behaves | [context-fundamentals.md](./references/context-fundamentals.md) |
| **Degradation** | Chasing failures — lost-in-middle, poisoning | [context-degradation.md](./references/context-degradation.md) |
| **Optimization** | Compaction, masking, caching, partitioning | [context-optimization.md](./references/context-optimization.md) |
| **Compression** | Drawn-out sessions, summarization tactics | [context-compression.md](./references/context-compression.md) |
| **Memory** | Holding state across sessions, knowledge graphs | [memory-systems.md](./references/memory-systems.md) |
| **Multi-Agent** | Coordination patterns, walling off context | [multi-agent-patterns.md](./references/multi-agent-patterns.md) |
| **Evaluation** | Grading agents, LLM-as-Judge, metrics | [evaluation.md](./references/evaluation.md) |
| **Tool Design** | Folding tools together, writing descriptions | [tool-design.md](./references/tool-design.md) |
| **Pipelines** | Building projects, batch processing | [project-development.md](./references/project-development.md) |
| **Runtime Awareness** | Quota limits, watching the context window | [runtime-awareness.md](./references/runtime-awareness.md) |

## Key Metrics

- **Token utilization**: Flag at 70%, start optimizing at 80%
- **Token variance**: Accounts for 80% of how agents perform
- **Multi-agent cost**: roughly 15x a single agent
- **Compaction target**: 50-70% smaller for under 5% quality loss
- **Cache hit target**: 70%+ when the workload is stable

## Four-Bucket Strategy

1. **Write**: Park context outside the window (scratchpads, files)
2. **Select**: Bring back only what the task needs (retrieval, filtering)
3. **Compress**: Shrink the token count without losing the meaning (summarization)
4. **Isolate**: Fan the work out to sub-agents (partitioning)

## Anti-Patterns

- Dumping everything in rather than choosing what matters
- Burying the must-read facts in the middle
- Letting context fill to the limit with no compaction in place
- Running one agent on work that could fan out
- Shipping tools whose purpose you cannot read off the description

## Guidelines

1. Anchor the critical material at the head and tail of the context
2. Kick off compaction once utilization sits in the 70-80% band
3. Treat sub-agents as context boundaries, not personas
4. Spec every tool against the 4-question framework (what, when, inputs, returns)
5. Optimize the token cost of finishing a task, not of a single request
6. Confirm behavior with probe-based evaluation
7. Watch KV-cache hit rates once you are in production
8. Begin lean; earn each added layer of complexity

## Runtime Awareness

A PostToolUse hook feeds usage awareness into the session on its own:

```xml
<usage-awareness>
Claude Usage Limits: 5h=45%, 7d=32%
Context Window Usage: 67%
</usage-awareness>
```

**Thresholds:**
- 70%: WARNING - time to weigh optimization/compaction
- 90%: CRITICAL - act now

**Data Sources:**
- Usage limits: Anthropic OAuth API (`https://api.anthropic.com/api/oauth/usage`)
- Context window: Statusline temp file (`/tmp/sk-context-{session_id}.json`)

## Scripts

- [context_analyzer.py](./scripts/context_analyzer.py) - Gauges context health and spots degradation
- [compression_evaluator.py](./scripts/compression_evaluator.py) - Scores how well compression held up
