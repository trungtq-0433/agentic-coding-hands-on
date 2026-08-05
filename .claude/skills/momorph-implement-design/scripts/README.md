# MoMorph Implement Design Scripts

Two local helper scripts (asset download + coverage check). Every node/style query goes through MCP tools directly (`get_overview`, `query_section`, `get_node`, `get_node_context`, ...).

> **Python interpreter:** `.claude/skills/.venv/bin/python3`

## 1. `asset_downloader.py` — Parallel media download + manifest generation

Input: JSON map `{nodeId: download_url}` from MCP `get_media_files`.

Output:
- Asset files inside `--out`
- `assets.md` (Markdown table) mapping `nodeId → file path` (relative)

```bash
# Plan-only: write the manifest immediately, DO NOT download (orchestrator uses this so subagents can read right away)
python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py data/media_files.json \
  --out data/assets --plan-only --manifest data/assets.md

# Full download (run in background)
python3 .claude/skills/momorph-implement-design/scripts/asset_downloader.py data/media_files.json \
  --out data/assets --workers 8 --manifest data/assets.md
```

- Filename preference: from URL path (presigned S3). Collision → suffix `_{nodeId}`.
- Supports the `{nodeId: {url: ...}}` format (fallback keys: `url`/`downloadUrl`/`href`).
- **Recommendation:** run twice — `--plan-only` synchronously first (instant), then full download in the background.

## 2. `validate_coverage.py` — Check assets.md coverage

Scan code dir → find markers → ensure every nodeId in `assets.md` appears at least once.

```bash
python3 .claude/skills/momorph-implement-design/scripts/validate_coverage.py \
  --assets data/assets.md \
  --code src/components/screens/{slug}
```

Recognized markers (universal — comment-only, NO runtime leak):
- `// mm:1:1` (TS/JS/Vue/Svelte/Dart/Swift/Kotlin)
- `{/* mm:1:1 */}` (JSX/TSX inline)
- `/* mm:1:1 */` (CSS/JS block)
- `<!-- mm:1:1 -->` (HTML/Vue template)

Exit code: `0` ok, `2` some asset missing (prints the missing nodeIds).

## Recommended pipeline

```bash
# After MCP get_media_files returns → cp to data/media_files.json

# 1. Plan asset (instant)
python3 asset_downloader.py data/media_files.json --out data/assets --plan-only \
  --manifest data/assets.md

# 2. Background download
python3 asset_downloader.py data/media_files.json --out data/assets \
  --manifest data/assets.md &

# 3. Subagents code in parallel (use MCP query_section / get_node directly,
#    read asset paths from data/assets.md)

# 4. Validate
python3 validate_coverage.py --assets data/assets.md \
  --code src/components/screens/{slug}
```
