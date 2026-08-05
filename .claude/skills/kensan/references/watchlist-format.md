# Watchlist Format

A watchlist is a markdown file of source tables. Presets live in `watchlists/presets/`; your overrides live in
`~/.claude/kensan/watchlist.local.md`. The collector parses every markdown table it finds.

## Table columns

Each table row is one source. The parser keys off column **headers** (case-insensitive), so column order is flexible.
Recognized headers:

| Header | Required | Meaning |
|--------|----------|---------|
| `id` | yes | Stable unique id. Drives overrides + dedup. Use `kebab-case`, e.g. `kol-simonw`. |
| `name` | yes | Human label shown in the briefing. |
| `type` | yes | Collector type (see below). |
| `handle` / `url` | yes* | Platform handle or feed URL/identifier. At least one must be present. |
| `topic` | no | Topic/section label; defaults to the file's H1 or filename. |
| `weight` | no | Priority/credibility prior **1–5** (5 = highest-signal, default 3). Boosts scoring + hot-topic heat — see `dedup-index-and-scoring.md`. |
| `freshness` | no | `green` (posts new knowledge often) / `yellow` (sparse but fresh) / `white` (evergreen). Advisory only. |
| `note` | no | Free text, ignored by collectors. |

Extra platform columns (`X`, `GitHub`, `RSS`, `HF`, …) are allowed for human readability; the collector reads the
single authoritative `handle`/`url` for the row's `type`. Keep one row per `(source, type)` so each has its own `id`.

## Source `type` values

| `type` | Collector | `handle`/`url` holds | Free / no key |
|--------|-----------|----------------------|---------------|
| `rss` | feedparser | full feed URL | yes |
| `arxiv` | arXiv Atom API | category (e.g. `cs.AI`) or query | yes |
| `github-releases` | GitHub releases API | `owner/repo` | yes (optional `GITHUB_TOKEN`) |
| `github-trending` | GitHub repo search (recent + stars) | topic/query (e.g. `LLM agent`) | yes (optional `GITHUB_TOKEN`) |
| `github-user` | GitHub user events | login (e.g. `simonw`) | yes (optional `GITHUB_TOKEN`) |
| `hn` | Algolia HN API | comma-separated keywords | yes |
| `hf-papers` | HuggingFace daily-papers API | (empty = daily) | yes |
| `goodailist` | goodailist.com JSON API | (empty = trending) | yes |
| `bluesky` | Bluesky public API (`getAuthorFeed`) | actor handle (e.g. `simonwillison.net`) | yes |
| `youtube` | YouTube channel RSS | `UC...` channel_id | yes |
| `twitter` | twikit (X internal API) — **opt-in** | `@handle` | needs burner account + `TWITTER_COOKIES` |
| `social` | agent-native (WebSearch/WebFetch) | `@handle` or profile URL | n/a (agent; X has no free API) |

> `twitter` is **opt-in and never shipped in a preset** — it needs `pip install twikit` + a burner-account
> cookies file. Facebook + a sturdier X path go through self-hosted RSSHub feeding the `rss` type. Setup +
> ToS/security caveats: [`x-facebook-sources.md`](x-facebook-sources.md). Prefer `bluesky`/`rss` (zero risk) first.

> Removed in the source overhaul: `aiexperthub` (site blocks requests) and the old HTML-scraping `hf-papers`/
> `goodailist` collectors (replaced by their JSON APIs above).

## Example

```markdown
# Watchlist: AI Engineering

## Feeds
| id | name | type | handle/url | topic | note |
|----|------|------|------------|-------|------|
| feed-latentspace | Latent Space | rss | https://www.latent.space/feed | ai-eng | swyx podcast |
| arxiv-cs-cl | arXiv cs.CL | arxiv | cs.CL | research | NLP papers |
| rel-langchain | LangChain | github-releases | langchain-ai/langchain | tooling | |
| hn-llm | Hacker News (LLM) | hn | llm,gpt,anthropic | community | keyword filter |

## KOLs
| id | name | type | handle/url | topic |
|----|------|------|------------|-------|
| kol-simonw | Simon Willison | social | @simonw | ai-eng |
```

Rows whose `id` appears in your `## remove` override are dropped; rows in `## mute` stay listed but are skipped
during collection.
