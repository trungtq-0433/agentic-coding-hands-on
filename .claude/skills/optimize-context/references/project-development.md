# Project Development

Take an LLM-powered project from first idea through to deployment.

## Task-Model Fit

**LLM-Suited**: pulling things together, judgment calls, prose output, batches that tolerate a few misses
**LLM-Unsuited**: exact arithmetic, real-time work, zero-error demands, deterministic output

## Manual Prototype First

Run a single example through the target model by hand before you automate anything.

## Pipeline Architecture

```
acquire → prepare → process → parse → render
 (fetch)  (prompt)   (LLM)   (extract) (output)
```

Stages 1, 2, 4, 5 run deterministic and cheap | Stage 3 is the non-deterministic, expensive one

## File System as State

```
data/{id}/
├── raw.json      # acquire done
├── prompt.md     # prepare done
├── response.md   # process done
└── parsed.json   # parse done
```

```python
def get_stage(id):
    if exists(f"{id}/parsed.json"): return "render"
    if exists(f"{id}/response.md"): return "parse"
    # ... check backwards
```

**Benefits**: safe to re-run, easy to resume, easy to inspect

## Structured Output

```markdown
## SUMMARY
[Overview]

## KEY_FINDINGS
- Finding 1

## SCORE
[1-5]
```

```python
def parse(response):
    return {
        "summary": extract_section(response, "SUMMARY"),
        "findings": extract_list(response, "KEY_FINDINGS"),
        "score": extract_int(response, "SCORE")
    }
```

## Cost Estimation

```python
def estimate(items, tokens_per, price_per_1k):
    return len(items) * tokens_per / 1000 * price_per_1k * 1.1  # 10% buffer
# 1000 items × 2000 tokens × $0.01/1k = $22
```

## Case Studies

**Karpathy HN**: 930 items chewed through for $58 in 1hr across 15 workers
**Vercel d0**: cutting 17 tools down to 2 took success from 80% to 100% and ran 3.5x faster

## Single vs Multi-Agent

| Factor | Single | Multi |
|--------|--------|-------|
| Context | Fits window | Exceeds |
| Tasks | Sequential | Parallel |
| Tokens | Limited | 15x OK |

## Guidelines

1. Prove it by hand before you automate it
2. Lay the work out as the 5-stage pipeline
3. Keep state on disk, in files
4. Shape the output with structure
5. Price the run before you start it
6. Stay single-agent until the work genuinely needs more

## Related

- [Context Optimization](./context-optimization.md)
- [Multi-Agent Patterns](./multi-agent-patterns.md)
