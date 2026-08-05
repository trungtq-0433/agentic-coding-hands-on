# Kensan Source Presets

Curated default watchlists. The skill loads **all** files here and merges your personal overrides from
`~/.claude/kensan/watchlist.local.md` on top (see `../../references/user-state-and-overrides.md`).

**Do not edit these files to customize your sources** — your edits would be overwritten on kit update and lost.
Add/remove/mute via the skill flags (`--add-source`, `--remove-source`, `--mute`), which write to your local file.

| File | Topic | Seeded from |
|------|-------|-------------|
| `ai-labs.md` | Frontier labs & their releases | MorningAI ai-labs |
| `ai-apps.md` | AI products & apps | MorningAI ai-apps |
| `coding-agents.md` | Coding agents & dev tools | MorningAI coding-agent |
| `model-infra.md` | Models, serving, infra | MorningAI model-infra |
| `benchmarks.md` | Papers & benchmarks | MorningAI benchmarks-academic |
| `kol.md` | Key opinion leaders (RSS + Bluesky + X) | MorningAI kol + verified feeds |
| `vision-media.md` | Vision, video, media gen | MorningAI vision-media |
| `trending-discovery.md` | What's trending right now | goodailist API + GitHub trending + HN + HF papers |
| `youtube.md` | AI YouTube channels (research + builder) | channel RSS (verified channel_ids) |
| `top-github-users.md` | Top OSS builders + what they ship | gayanvoice/top-github-users |
| `ai-engineering.md` | Practitioner newsletters/blogs (agents, coding) | curated watchlist (weighted) |
| `llmops.md` | Evals, observability, serving, deployment | curated watchlist (weighted) |
| `news-digest.md` | Daily/weekly AI news roundups | curated watchlist (weighted) |
| `edge-ai.md` | On-device / Jetson / YOLO / CV | curated watchlist (weighted) |
| `vietnamese-ai.md` | Active Vietnamese AI sources | curated watchlist (weighted) |
| `vietnamese-ai-github.md` | 77 VN AI/ML builders — recent activity | gayanvoice vietnam, AI-filtered |
| `china-ai-github.md` / `japan-ai-github.md` / `singapore-ai-github.md` | CN/JP/SG AI builders (topics `cn/jp/sg-ai-github`) | gayanvoice per-country, AI-filtered (top-400 scan, capped 60) |

> The `*-ai-github.md` presets are large `github-user` sets — one GitHub API call per user. Set `GITHUB_TOKEN`
> (5000/h vs 60/h unauth) before a full run, or scope to one country with `/tkm:kensan <cc>-ai-github`.

YouTube channels for every topic live together in `youtube.md` (each tagged with its `topic`), so
`/tkm:kensan <topic>` still picks them up. channel_ids are resolved + title-verified.

Rows carry a **`weight` 1–5** (R&D priority) + `freshness` (green/yellow/white). Weight boosts scoring +
hot-topic heat — see `../../references/dedup-index-and-scoring.md`.

Edit scope for maintainers: keep one row per `(source, type)`, give every row a stable `id`, and prefer
key-less feed URLs. See `../../references/watchlist-format.md` for the column spec.
