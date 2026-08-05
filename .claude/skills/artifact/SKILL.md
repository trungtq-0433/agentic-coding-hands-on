---
name: tkm:artifact
description: "Upload an HTML/HTM/MD file or a whole folder to Takumi Artifacts and get a shareable URL. Use when user says 'tạo artifact', 'share HTML này', 'publish artifact', 'create artifact', 'upload file này lên', or after a generate-slide --html / preview-output --html / brainstorm HTML output — suggest /tkm:artifact upload <path> to get a public link."
category: sharing
keywords: [artifact, upload, share, html, url, publish, link]
argument-hint: "upload <file> [--title <title>] [-m <message>] [--id <uuid|url>] | download <uuid|url> [-o <dir>] [--ver <n>] [--force] | delete <uuid|url> [--ver <n>] [--yes]"
metadata:
  author: takumi-agent-kit
  version: "1.1.0"
module: specialized-output
triggers: ["artifact", "tạo artifact", "share HTML", "publish artifact", "upload artifact", "shareable link"]
---

# Artifact — Upload & Share

Upload a **file** (HTML/Markdown/mermaid/YAML/JSON/CSV/TSV…) — or a whole **folder** (HTML bundle with css/js/images, or a markdown tree) — to Takumi Artifacts and get back a permanent URL.
Artifacts are **private by default** — only you can see them until you change visibility via the Share menu on the web. Markdown, diagrams, and data files render rich in the viewer; raw bytes are served to code.

## Commands

| Command                                        | Description                                                                                                     |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `tkm artifact upload <file>`                   | Upload a single file (new or re-upload same path)                                                               |
| `tkm artifact upload <folder>`                 | Upload an entire folder as ONE artifact (sidebar file-tree on the web)                                          |
| `tkm artifact upload <path> --title "My Page"` | Upload with a display title (max 200 chars)                                                                     |
| `tkm artifact upload <path> -m "<message>"`    | Attach a short change note to this version (max 100 chars; shown in version history)                            |
| `tkm artifact upload <path> --id <uuid\|url>`  | Force-replace a specific artifact by UUID or viewer URL                                                         |
| `tkm artifact download <uuid\|url>`            | Download all files into a folder in the current dir — default `slug(title)` or uuid (UUID or full URL accepted) |
| `tkm artifact download <uuid\|url> -o <dir>`   | Save to a specific directory. Saving records the path so re-upload bumps the same artifact                      |
| `tkm artifact download <uuid\|url> --ver <n>`  | Download a specific version number. `--force` allows writing into a non-empty directory                         |
| `tkm artifact delete <uuid\|url>`              | Delete an artifact (prompts for confirmation; accepts a UUID or full URL)                                       |
| `tkm artifact delete <uuid\|url> --yes`        | Delete without prompt                                                                                           |
| `tkm artifact delete <uuid\|url> --ver <n>`    | Delete ONE version only (soft delete; other versions stay, last remaining version is protected). A URL with `?v=<n>` works too |

**Limits (single file or folder):** no file-count or total-size limit — each individual file must be ≤ 20 MB. File types from the server allowlist: `html htm md mmd yaml yml csv tsv txt css js json svg png jpg jpeg gif webp ico woff woff2` — other extensions are rejected before upload.

**Ignore files:** when uploading a folder, the CLI honors `.gitignore` and `.tkmignore` at the folder root (exact `.gitignore` syntax — globs, `dir/`, `!negation`, `/anchoring`). `.tkmignore` rules are applied AFTER `.gitignore`, so `!pattern` in `.tkmignore` can re-include something `.gitignore` excluded. `.git/` and the ignore files themselves are never uploaded. Use `.tkmignore` when the artifact should exclude files that git tracks (or vice versa).

> `upload`, `download`, and `delete` are explicit subcommands — a bare `tkm artifact <path>` is rejected.
> Listing artifacts lives in the web UI (`/app/artifacts`) — there is no `tkm artifact list` command.
> `download` works for both single-file and folder artifacts — files are always written into a directory (refuses a non-empty dir unless `--force`).

## How upload works (Transport C)

Single-file and folder uploads share the same reserve/commit flow — bytes never stream through the app server; the CLI talks to S3 directly (a single file is just a 1-entry manifest):

1. **Scan** — the CLI walks the folder, computes a `sha256` for every file, and builds a manifest `[{path, sha256, size, mime}]`.
2. **Reserve** — `POST /api/artifacts/reserve` validates the manifest (path-traversal, size/count limits, MIME allowlist) and returns a **presigned PUT URL per file** plus a **skip-list**: any file whose `sha256` already exists in this artifact is skipped (content-addressed dedup → unchanged files cost **0 bytes**).
3. **Upload** — the CLI PUTs the non-skipped files **in parallel** straight to S3.
4. **Commit** — `POST /api/artifacts/commit` HEAD-verifies every blob, then atomically flips the new version live.

**Versions are immutable, full snapshots.** Re-uploading the same folder (add/edit/delete files) creates a brand-new version from the folder's _current_ state — it is **not** a delta. A deleted file simply is absent from the new version; older versions still show it. The share URL never changes between versions.

The web viewer renders a folder artifact with a **sidebar file-tree**; the entry file is resolved automatically (`index.html` → `index.md` → `README.md` → first file). Relative links inside an HTML bundle navigate natively inside the sandboxed iframe.

**Data files render rich in the viewer, raw for code.** Opening a file in the viewer previews it per type: `.md` (GitHub theme + table of contents), `.mmd` and ` ```mermaid ` fences (interactive diagram — zoom/pan), `.yaml`/`.yml`/`.json` containing an OpenAPI spec (Swagger UI), plain `.json`/`.yaml` (collapsible data tree with a Raw | Parsed switcher), `.csv`/`.tsv` (interactive table). But when an HTML artifact `fetch()`es a sibling data file — or any tool requests it without the viewer — it always receives the **raw bytes with the exact MIME type**, so HTML-app artifacts can read their own bundled data.

## Flow

### Step 1 — Resolve the file path

If the user typed `/tkm:artifact upload <path>` (or just `/tkm:artifact <path>`), use that path directly.

If invoked without a path (e.g., just `/tkm:artifact` after a `generate-slide` or `preview-output` run), look for the most recently generated HTML file mentioned in the current session and ask the user to confirm before uploading:

> "Found `./slides/output.html` from this session. Upload this file as an artifact?"

### Step 2 — Upload

```bash
tkm artifact upload <file>
```

On success the CLI prints an upload summary, then the artifact URL as the last line. Capture and display it:

```
Artifact URL: https://takumi.sun-asterisk.ai/app/artifacts/<uuid>
```

### Step 3 — Inform about visibility

Artifacts are **private by default**. Tell the user:

> Artifact đã được upload. Mặc định chỉ bạn thấy được.
> Để chia sẻ, mở link trên và dùng menu **Share** để:
>
> - Chuyển sang **Public** (ai có link đều xem được), hoặc
> - Chia sẻ riêng với người trong Sun\* bằng email.

### Step 4 — Handle errors

| Error                     | Action                                                      |
| ------------------------- | ----------------------------------------------------------- |
| Not logged in             | Tell user to run `tkm auth login` first                     |
| File not found            | Show the resolved path, ask user to check                   |
| File over 20 MB           | Name the offending file, suggest compressing or removing it |
| Unsupported extension     | Show the server allowlist (see **Limits** above)            |
| Upload failed (API error) | Surface the error message from the CLI, suggest retry       |

## Integration Suggestion

After other skills generate HTML output, append this suggestion (one line, not a banner):

```
Tạo artifact để chia sẻ link? → /tkm:artifact upload <path>
```

Skills that produce HTML output where this applies:

- `tkm:generate-slide --html` — slide deck HTML
- `tkm:preview-output --html` — explain / diagram / slides HTML
- `tkm:brainstorm` — if an HTML summary was generated

This suggestion is **optional** — never block or repeat it if the user ignores it.

## Examples

```bash
# Create — single file / folder (re-upload same path bumps the same artifact)
tkm artifact upload ./slides/deck.html --title "AI Governance Deck"
tkm artifact upload ./rebuild-spec-output/ --title "Rebuild Spec"

# Update after edits — same path, new version, -m = change note
tkm artifact upload ./slides/deck.html -m "Tweak intro copy"
tkm artifact upload ./rebuild-spec-output/ -m "Add api guide"   # folder: unchanged files deduped
tkm artifact upload ./deck.html -m "fix layout" --id 7f3a1c2d-...   # path not tracked → pin by UUID

# Delete an artifact (UUID or full URL; --yes skips confirm)
tkm artifact delete 7f3a1c2d-... --yes
# Delete specific artifact version (UUID + version number)
tkm artifact delete 7f3a1c2d-... --ver 2 --yes
# or delete by full URL (version optional)
tkm artifact delete https://takumi.sun-asterisk.ai/app/artifacts/7f3a1c2d-...?v=2 --yes

# Edit loop — download (-o records path) → edit → re-upload, same artifact
tkm artifact download https://takumi.sun-asterisk.ai/app/artifacts/7f3a1c2d-... -o ./my-artifact
tkm artifact upload ./my-artifact -m "Fix layout bug" --id 7f3a1c2d-...
```
