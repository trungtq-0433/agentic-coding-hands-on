# Tool Design

Build tools an agent can actually wield well.

## Consolidation Principle

One broad, capable tool beats a scatter of narrow ones. **Target**: cap it at 10-20 tools.

## Architectural Reduction Evidence

| Metric | 17 Tools | 2 Tools | Improvement |
|--------|----------|---------|-------------|
| Time | 274.8s | 77.4s | 3.5x faster |
| Success | 80% | 100% | +20% |
| Tokens | 102k | 61k | 37% fewer |

**Key**: Strong docs do the work that tool sophistication was trying to.

## When Reduction Works

**Prerequisites**: docs are solid, the model is capable, the problem is navigable
**Avoid when**: the system is messy, the domain is specialized, or a mistake is unsafe

## Description Engineering

Make every description answer four questions:
1. **What** does the tool do?
2. **When** should it be reached for?
3. **What inputs** does it take?
4. **What** comes back?

### Good Example

```json
{
  "name": "get_customer",
  "description": "Retrieve customer profile by ID. Use for order processing, support. Returns 404 if not found.",
  "parameters": {
    "customer_id": {"type": "string", "pattern": "^CUST-[0-9]{6}$"},
    "format": {"enum": ["concise", "detailed"]}
  }
}
```

### Poor Example

```json
{"name": "search", "description": "Search for things", "parameters": {"q": {}}}
```

## Error Messages

```python
def format_error(code, message, resolution):
    return {
        "error": {"code": code, "message": message,
                  "resolution": resolution, "retryable": code in RETRYABLE}
    }
# "Use YYYY-MM-DD format, e.g., '2024-01-05'"
```

## Response Formats

Give callers a choice between concise and detailed:

```python
def get_data(id, format="concise"):
    if format == "concise":
        return {"name": data.name}
    return data.full()  # Detailed
```

## Guidelines

1. Fold tools together, aiming for 10-20
2. Let each description cover all four questions
3. Spell parameter names out in full
4. Write errors the agent can recover from
5. Offer both a concise and a detailed format
6. Put the tools in front of an agent before you ship them
7. Start lean and add a tool only once it has earned the slot

## Related

- [Context Fundamentals](./context-fundamentals.md)
- [Multi-Agent Patterns](./multi-agent-patterns.md)
