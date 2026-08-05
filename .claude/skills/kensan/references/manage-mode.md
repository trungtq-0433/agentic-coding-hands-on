# Manage mode — interactive watchlist editor

`/tkm:kensan manage` edits the user's watchlist by asking questions, never by collecting. Every change goes
through `scripts/manage_watchlist.py`, which writes **only** `~/.claude/kensan/watchlist.local.md` — shipped
presets are never touched. Run scripts with the venv python (fallback `python3`).

`OV=~/.claude/kensan/watchlist.local.md` · `PRESETS=<skill>/watchlists/presets`

## Loop

1. **Show state.** `manage_watchlist.py list --presets $PRESETS --overrides $OV` → JSON. Render a compact view:
   presets with `on/off` + source count; and any source that is `muted` / `removed` / `overridden` / `added`.
   (Don't dump all ~300 enabled sources — show the presets table + only the non-default sources.)
2. **Ask the operation** — `AskUserQuestion` (header "Watchlist"):
   - Enable/disable presets · Mute/unmute sources · Add source · Update source · Delete source · Done.
3. **Run the chosen branch (below), then re-show the affected slice and return to step 2 until "Done".**

## Branches → helper calls

| Operation | Question(s) | Helper call(s) |
|---|---|---|
| **Enable/disable presets** | multiSelect of presets (show current on/off) | per toggle: `set-preset --overrides $OV --stem <stem> --state on\|off` |
| **Mute / unmute source** | pick a preset/topic to scope → multiSelect its sources | per source: `mute`/`unmute --overrides $OV --id <id>` |
| **Add source** | one batched question: name · type · handle · topic · weight (1-5) | `add --overrides $OV --id <kebab-id> --name .. --type .. --handle .. --topic .. --weight ..` |
| **Update source** | pick id → batched question with only the fields to change | `update --overrides $OV --id <id> [--field val ...]` |
| **Delete source** | pick id (incl. a shipped default) → confirm | `remove --overrides $OV --id <id>` |

## Rules
- `type` must be one of the known collector types (the helper rejects unknown ones): `rss`, `arxiv`,
  `github-releases`, `github-trending`, `github-user`, `hn`, `hf-papers`, `goodailist`, `bluesky`, `youtube`,
  `twitter`, `social`.
- `add`/`update` write to the override `## add` table (update merges onto any existing row by id; a re-added id
  is dropped from `## remove`). `delete` of a shipped-preset source records it under `## remove`; deleting a
  user-added source drops its add row. All ops are **idempotent**.
- Disabling a preset (`set-preset off`) drops all its sources from the effective watchlist until re-enabled;
  it does not delete anything.
- Cancelling/skipping a question makes no change. Confirm before any **delete**.
- The override file is **manager-owned**: free-form comments you add by hand may be rewritten. Use the questions.
