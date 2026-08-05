# Memory Systems

Ways to hold context that outlive the window itself.

## Memory Layer Architecture

| Layer | Scope | Persistence | Use Case |
|-------|-------|-------------|----------|
| L1: Working | Current window | None | Reasoning in flight |
| L2: Short-Term | Session | Session | Carrying a task forward |
| L3: Long-Term | Cross-session | Persistent | User preferences |
| L4: Entity | Per-entity | Persistent | Staying consistent |
| L5: Temporal Graph | Time-aware | Persistent | Facts that change over time |

## Benchmark Performance (DMR Accuracy)

| System | Accuracy | Approach |
|--------|----------|----------|
| Zep | 94.8% | Temporal knowledge graphs |
| MemGPT | 93.4% | Hierarchical memory |
| GraphRAG | 75-85% | Knowledge graphs |
| Vector RAG | 60-70% | Embedding similarity |

## Vector Store with Metadata

```python
class MetadataVectorStore:
    def add(self, text, embedding, metadata):
        doc = {
            "text": text, "embedding": embedding,
            "entities": metadata.get("entities", []),
            "timestamp": metadata.get("timestamp")
        }
        self.index_by_entity(doc)

    def search_by_entity(self, entity, k=5):
        return self.entity_index.get(entity, [])[:k]
```

## Temporal Knowledge Graph

```python
class TemporalKnowledgeGraph:
    def add_fact(self, subject, predicate, obj, valid_from, valid_to=None):
        self.facts.append({
            "triple": (subject, predicate, obj),
            "valid_from": valid_from,
            "valid_to": valid_to or "current"
        })

    def query_at_time(self, subject, predicate, timestamp):
        for fact in self.facts:
            if (fact["triple"][0] == subject and
                fact["valid_from"] <= timestamp <= fact["valid_to"]):
                return fact["triple"][2]
```

## Memory Retrieval Patterns

| Pattern | Query | Use Case |
|---------|-------|----------|
| Semantic | "Similar to X" | General recall |
| Entity-based | "About user John" | Consistency |
| Temporal | "Valid on date" | Evolving facts |
| Hybrid | Combine above | Production |

## File-System-as-Memory

```
memory/
├── sessions/{id}/summary.md
├── entities/{id}.json
└── facts/{timestamp}_{id}.json
```

## Guidelines

1. Begin with the file system as memory — it is the plainest thing that works
2. Layer in vector search once scale demands it
3. Index by entity to keep references consistent
4. Add temporal awareness for facts that drift
5. Run consolidation to keep the store healthy
6. Measure how accurately retrieval lands

## Related

- [Context Fundamentals](./context-fundamentals.md)
- [Multi-Agent Patterns](./multi-agent-patterns.md)
