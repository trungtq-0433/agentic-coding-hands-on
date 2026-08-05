# Dedup Index & Scoring

The dedup index is the knowledge ledger that lets Kensan run day after day without re-reporting what you have
already seen. It is the reason a briefing shows *what changed* instead of the same headlines again.

## The ledger

Location: `~/.claude/kensan/index/seen-items.jsonl` — one JSON record per known item, appended/rewritten by
`scripts/index_store.py`.

```json
{"id":"<sha1 canonical-url>","url":"https://…","title":"…","topic":"ai-labs",
 "first_seen":"2026-06-20","last_updated":"2026-06-22","times_seen":3,
 "content_hash":"<sha1 of title+summary>","score":7,
 "briefings":["260620-ai-engineering-briefing","260622-ai-engineering-briefing"],
 "status":"new|update|stable","aliases":["<other-id>"]}
```

## Classification

For each collected item, `index_store.py classify` decides:

| Outcome | Condition | Briefing effect |
|---------|-----------|-----------------|
| **NEW** | no `id` match **and** no near-duplicate title | full card under "🆕 New" |
| **SKIP** | `id` match **and** `content_hash` unchanged | not re-reported; counted in footer |
| **UPDATE** | `id` match **and** `content_hash` changed | delta-only card under "🔄 Updates" |
| **MERGE** | near-duplicate of a *different* `id` (same story, new URL) | aliased to the canonical record, treated as UPDATE |

Similarity check order (dependency-light, stdlib only):

1. Exact canonical-URL `id` equality — the strong signal.
2. Else normalized-title similarity (lowercase, strip punctuation, shingle into word-set, Jaccard overlap).
   Default merge threshold `0.82`. **Bias toward NEW**: only merge when clearly the same story, because a wrong
   merge silently hides real news, while a wrong split only costs one extra card.

## Upsert

After classification + scoring, `index_store.py upsert` writes back: bump `times_seen`, set `last_updated` to
today, append the briefing id, store the latest `score`, and record any alias. NEW items are inserted fresh.

`index_store.py prune --older-than 90` drops records not seen in N days to keep the ledger bounded.

## Two-stage scoring

Score only **NEW** and **UPDATE** items (SKIP items already carry a score).

**Stage 1 — cheap pre-filter** (mechanical): drop items outside the `--since` window, obvious low-signal
(pure marketing, dead links), and off-watchlist noise.

**Stage 2 — agent evaluation**: rate each survivor 0–10 on four axes, then average:

| Axis | Question |
|------|----------|
| Impact | Does it change practice or understanding? |
| Novelty | Genuinely new, or a rehash of known material? |
| Relevance | Does it fit this watchlist's topic / your learning goal? |
| Credibility | Is the source authoritative? Corroborated elsewhere? |

Keep items at/above the **threshold (default 6)**. `--depth low|medium|high` controls how many candidates reach
Stage 2 (e.g. low = top 10 by `raw_score_hint`, high = all). Items scoring **≥8** get a cross-source
verification pass — confirm via a second independent source before inclusion. Write the final score back to the
ledger so future runs can show score movement as part of an UPDATE delta.

### Source weight (the `weight` field)

Each item carries `weight` (1–5, default 3) copied from its source — a curated priority/credibility prior
(verified high-signal R&D sources get 5; hype/explainer get 1). Apply weight as a **prior, not an override**:

- Nudge the average score: `final = avg_score + (weight - 3) * 0.5` (so a w5 source gets +1.0, a w1 gets −1.0),
  then re-apply the threshold. A weak source still earns its place on merit; a trusted one clears the bar more easily.
- Break ties by weight (higher weight first) when ordering a section.
- Treat weight as the strongest input to the **credibility** axis for sources you cannot otherwise corroborate.

Never let weight alone include a genuinely low-signal item, nor exclude a high-signal one from a low-weight source.
