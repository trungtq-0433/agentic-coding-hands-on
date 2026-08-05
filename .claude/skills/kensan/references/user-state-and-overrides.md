# User State & Overrides

Kensan keeps all per-user state in your home directory, outside any repo, so it persists across sessions and is
never committed. The shipped presets stay pristine; everything you customize lives here.

```
~/.claude/kensan/
  watchlist.local.md            # your overrides (add / remove / mute)
  index/seen-items.jsonl        # cross-day dedup ledger (see dedup-index-and-scoring.md)
  briefings/                    # generated briefings, date-stamped
```

The directory is created on first run. If `watchlist.local.md` is absent, the effective watchlist is just the presets.

## Override file format

`watchlist.local.md` uses three optional sections, all keyed by source `id`:

```markdown
# My Kensan overrides

## add
| id | name | type | handle/url | topic |
|----|------|------|------------|-------|
| kol-karpathy-bsky | Andrej Karpathy | bluesky | karpathy.bsky.social | ai-eng |
| yt-coleMedin | Cole Medin | youtube | UCMwVTLZIRRUyVy1A1Ah8MMA | builder |

## remove
- kol-ylecun
- vm-runway

## mute
- td-goodailist

## disable-preset
- youtube
```

Use the bare source `id` exactly as it appears in the preset tables (e.g. `vm-runway`, `td-goodailist`) —
not a `topic:id` form. An id that matches no row is silently ignored. `## disable-preset` lists **preset file
stems** (e.g. `youtube`, `edge-ai`); a disabled preset's sources are dropped from the effective watchlist until
re-enabled — nothing is deleted.

> **Tip:** `/tkm:kensan manage` edits all of these sections for you through questions (enable/disable presets,
> mute/unmute, add/update/delete) — it owns this file, so prefer it over hand-editing. See
> [`manage-mode.md`](manage-mode.md).

## Merge semantics (presets ⊕ overrides)

The collector computes the **effective watchlist** as:

1. Start from all preset rows.
2. **add** — append rows from `## add`. If an `id` collides with a preset, the override row wins (lets you re-point a source).
3. **remove** — drop any row whose `id` is listed in `## remove`. It will not be collected and will not appear.
4. **mute** — keep the row in the listing (so `--list` shows it) but skip it during collection this run.

`id` is the join key everywhere — overrides, dedup ledger, and briefing provenance all reference it, so keep ids stable.

## How the management flags write here

- `--add-source` appends a row under `## add` (creating the section/file if needed).
- `--remove-source <id>` appends `- <id>` under `## remove`.
- `--mute <id>` appends `- <id>` under `## mute`.

These flags are the only writers of `watchlist.local.md`; presets are never modified by the skill.

## Privacy

Because state lives under `~/.claude/kensan/`, your followed handles and reading history stay local to your machine
and out of version control. If you keep sensitive sources, the takumi privacy-block hook still guards against
accidental reads of unrelated sensitive files during collection.
