# Hot-Topic Detection

After collection + dedup, before synthesis, group the NEW+UPDATE items into topical clusters and rank them by
"heat". The top cluster auto-becomes the deep-dive subject (Tier 2). This is an **agent-native** step — no
script; you read the items and judge.

## Clustering

Read each item's title + summary + source + score. Group into 5–10 coherent topical clusters. A cluster is a
theme several items orbit, e.g.:
- "open-weight frontier models" (DeepSeek V4, Qwen 3.7, GLM-5.2, Mistral Apache-2.0…)
- "agentic-coding convergence" (Cursor, Claude Code, Codex, opencode…)
- "agent memory governance" (papers + repos + HN threads on shared agent memory)

Prefer a few meaningful clusters over many thin ones. Drop singletons that share no theme into the skim list.

## Heat score

For each cluster, estimate:

```
heat = item_count
     × cross_source     (distinct sources/platforms — 5 sources beats 5 items from one blog)
     × recency          (weight the last few days higher than the window edge)
     × avg_score        (the two-stage score average of its members)
     × avg_weight/3     (mean source `weight` of members, normalised — a cluster carried by
                         weight-5 R&D sources outranks one driven by weight-1 hype channels)
```

You do not need exact arithmetic — rank clusters by a reasoned blend of these four. Corroboration across
independent sources is the strongest signal; a single loud blog is not "hot".

## Output

Render the top **5** clusters into the briefing's "🔥 Hot topics" section (see the briefing template): label,
relative heat, member item links, one-line "why hot". Then select cluster **#1** as the deep-dive topic
(Tier 2), unless the user passed an explicit topic.

Keep clustering stable on a same-day re-run: the same item set should yield the same top cluster.
