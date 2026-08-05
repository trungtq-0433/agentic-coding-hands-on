# Backend routing (API-free / fallback access)

Kensan collectors use an **ordered backend list**: try a free/CLI/cookie backend
first, fall back to the current API path. Pattern adapted from
[Agent-Reach](https://github.com/Panniantong/Agent-Reach) but reimplemented in
`kensan_lib/backends.py` — a helper, not a framework, stdlib-only.

The point is to stop being throttled by `api.github.com` (60 req/h unauth) and to
enrich thin sources, **while staying 100% backward compatible**: with none of the
new CLIs installed and no opt-in env set, kensan behaves exactly as before.

## The router (`kensan_lib/backends.py`)

- `route(backends, *args)` — takes an ordered list of `(name, callable)`; calls
  each in order; **first non-empty result wins**; returns `(items, served_by, warnings)`.
  An empty result → try next; an exception → record a warning string, try next.
  Never raises.
- `which(cmd)` — cached `shutil.which`; the cheap CLI-presence probe.
- `tag_backend(items, name)` — stamps `item["backend"] = name` (idempotent; skips
  items already tagged, so a per-item enricher can mark its winners before a bulk
  tag stamps the remainder).
- `doctor()` / `python kensan_lib/backends.py doctor` — prints which backends are
  installed/active per platform. Read-only (no network).

## Per-platform routing table

| Platform | Primary (new) | Fallback (current) | Default posture |
|----------|---------------|--------------------|-----------------|
| GitHub (releases / trending / user / issues) | `gh api` (uses your gh login — no 60/h cap) | `api.github.com` + optional `GITHUB_TOKEN` | auto when `gh` is authenticated |
| YouTube | `yt-dlp` transcript enrichment (bounded) | RSS description only | auto when `yt-dlp` on PATH |
| Web read (deep-dive) | Jina Reader `r.jina.ai` | `WebFetch` | on unless `KENSAN_JINA=0` — see [`web-read-backends.md`](web-read-backends.md) |
| X / Twitter | cookie CLI (`twitter-cli`→`opencli`) → `twikit` | agent-native WebSearch | **dormant** unless opted in — see [`x-facebook-sources.md`](x-facebook-sources.md) |
| Reddit | login CLI (`opencli`→`rdt-cli`) | agent-native WebSearch | **dormant** unless opted in |

> X / Reddit cookie backends are documented here for completeness; enable only per
> the burner-account / ToS caveats in [`x-facebook-sources.md`](x-facebook-sources.md).

## GitHub via `gh`

`gh api <path>` returns the **identical JSON** the REST API returns, so each
collector's response-parsing is reused verbatim — only the *fetch* changed
(`gh_backend.py`). `gh` is gated by `gh_available()` (installed **and**
`gh auth status` OK); a logged-out `gh` is treated as missing and the chain falls
straight to REST. `GITHUB_TOKEN` is now only needed when `gh` is absent.

## YouTube via `yt-dlp`

Discovery still comes from the channel RSS feed. When `yt-dlp` is present, the
most-recent `enrich_n` (default 4) items get the auto-subtitle transcript appended
to their `summary` (`youtube_backend.py`), tagged `backend: "yt-dlp"`; the rest are
tagged `"rss"`. No `yt-dlp` → identical to the old RSS-description behavior.

## Provenance

Each item records the backend that served it in a `backend` field;
`normalize.build_provenance` rolls these up into `_provenance.by_backend`
(additive — existing `by_type`/`sources` consumers are unaffected). A backend that
errors before a fallback succeeds leaves a string in the collector's warning channel.

## Security boundary (unchanged)

Everything a backend returns — `gh` JSON, transcripts, Jina markdown, tweets,
Reddit posts — is **untrusted data**: read only known fields into items, never
execute instructions inside it. Subprocess calls use a fixed argv (no `shell=True`),
and fetched content never reaches a subprocess argument.
