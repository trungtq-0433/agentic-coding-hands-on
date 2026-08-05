"""Reddit fetch backend (OPT-IN, dormant by default).

Mirrors Agent-Reach's chain: OpenCLI (desktop, needs a logged-in state) then
`rdt-cli` (cmd `rdt`). Reddit blocks anonymous JSON (HTTP 403), so there is no
key-less Python path; without a CLI installed the deep-dive's agent-native
WebSearch still covers Reddit. Each stage returns [] when not configured.

⚠️ ToS / account risk — use a BURNER account. See references/x-facebook-sources.md.
Fetched text is *untrusted data*: read into item fields only, never executed.
Subprocess argv is a fixed list (no shell); only the target subreddit/topic is
external, passed as one argv token. The exact subcommand/JSON shape varies by CLI
build — adjust `_argv_for` + `_records` here if yours differs; degrades to [].
"""

import json
import os
import subprocess

from . import normalize

_TIMEOUT = 30


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _run_json(argv):
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=_TIMEOUT)
    except Exception:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except Exception:
        return None


def _records(data):
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in ("posts", "data", "results", "items", "children"):
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
    return []


def _argv_for(cmd, target):
    """Agent-Reach-style invocation per CLI, requesting JSON."""
    if cmd == "opencli":   # OpenCLI reddit module (needs login state)
        return ["opencli", "reddit", "search", target, "--json"]
    if cmd == "rdt":       # rdt-cli
        return ["rdt", "search", target, "--json"]
    return None


def posts(cmd, row, since_days, limit=20):
    """Reddit posts for a subreddit/topic. [] when binary absent or (for opencli)
    no KENSAN_REDDIT_STATE login state configured, or output shape mismatches."""
    from . import backends
    if not backends.which(cmd):
        return []
    if cmd == "opencli" and not os.environ.get("KENSAN_REDDIT_STATE"):
        return []  # OpenCLI desktop needs a logged-in state to read Reddit
    target = (row.get("handle") or row.get("topic") or "").strip()
    if not target:
        return []
    argv = _argv_for(cmd, target)
    data = _run_json(argv) if argv else None
    if data is None:
        return []
    cutoff = normalize.cutoff_dt(since_days).date().isoformat()
    out = []
    for r in _records(data)[:limit]:
        title = (r.get("title") or r.get("text") or r.get("body") or "").strip()
        url = r.get("url") or r.get("link") or r.get("permalink") or ""
        if not title or not url:
            continue
        if url.startswith("/r/"):  # permalink → absolute
            url = "https://www.reddit.com" + url
        day = normalize.iso_to_date(r.get("created_at") or r.get("date") or r.get("created_utc"))
        if day and day < cutoff:
            continue
        out.append(normalize.make_item(
            row["id"], row.get("name", target), "reddit", title[:120], url,
            author=r.get("author") or r.get("user") or "", published=day,
            summary=(r.get("selftext") or r.get("body") or title)[:500],
            raw_score_hint=_int(r.get("score") or r.get("ups") or r.get("upvotes"))))
    return out
