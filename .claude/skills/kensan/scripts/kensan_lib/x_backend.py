"""X/Twitter fetch backends (OPT-IN, dormant by default).

Mirrors Agent-Reach's chain: a cookie-based CLI (`twitter-cli`, cmd `twitter`),
then OpenCLI (`opencli`, browser-session reuse), then kensan's existing `twikit`
path. Each stage is dormant unless its prerequisite is present:
  - twitter-cli / opencli — only invoked when the binary is on PATH;
  - twikit — only when TWITTER_COOKIES points at a cookies file.
Every stage returns [] (not an error) when not configured, so with nothing set
up the X collector is silent — exactly as before.

⚠️ ToS / account risk: these automate X against its terms. Use a BURNER account.
See references/x-facebook-sources.md. All fetched text is *untrusted data* —
read into item fields only, never executed. Subprocess argv is a fixed list
(no shell); the handle is the only external value, passed as one argv token.

The exact subcommand/JSON shape varies by CLI build — adjust `_argv_for` +
`_records` here if yours differs; everything degrades to [] on a mismatch.
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
    """Run a CLI expected to emit JSON on stdout; return parsed value or None."""
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
    """Coerce a CLI JSON payload into a list of dict records (best-effort)."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in ("tweets", "data", "results", "items", "posts"):
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
    return []


def _argv_for(cmd, handle):
    """Agent-Reach-style invocation per CLI, requesting JSON."""
    if cmd == "twitter":   # twitter-cli
        return ["twitter", "user", handle, "--json"]
    if cmd == "opencli":   # OpenCLI twitter module
        return ["opencli", "twitter", "user", handle, "--json"]
    return None


def cli_tweets(cmd, row, since_days, limit=20):
    """Recent tweets via `twitter-cli`/`opencli`. [] when binary absent/mismatch."""
    from . import backends
    if not backends.which(cmd):
        return []
    handle = (row.get("handle") or "").lstrip("@")
    argv = _argv_for(cmd, handle)
    data = _run_json(argv) if argv else None
    if data is None:
        return []
    cutoff = normalize.cutoff_dt(since_days).date().isoformat()
    out = []
    for r in _records(data)[:limit]:
        text = (r.get("text") or r.get("full_text") or r.get("content") or "").strip()
        if not text:
            continue
        day = normalize.iso_to_date(r.get("created_at") or r.get("date") or r.get("createdAt"))
        if day and day < cutoff:
            continue
        tid = r.get("id") or r.get("id_str") or r.get("rest_id") or ""
        url = (r.get("url") or r.get("link")
               or (f"https://x.com/{handle}/status/{tid}" if tid else f"https://x.com/{handle}"))
        out.append(normalize.make_item(
            row["id"], row.get("name", handle), "twitter", text[:90], url,
            author="@" + handle, published=day, summary=text[:500],
            raw_score_hint=_int(r.get("favorite_count") or r.get("likes"))))
    return out


def twikit_tweets(row, since_days, limit=20):
    """Recent tweets via twikit (X's internal GraphQL). [] unless TWITTER_COOKIES
    points at a burner-account cookies file. Relocated from collect_twitter."""
    cookies = os.environ.get("TWITTER_COOKIES", "")
    if not cookies or not os.path.exists(os.path.expanduser(cookies)):
        return []
    import asyncio

    from twikit import Client  # lazy — only when actually used
    handle = (row.get("handle") or "").lstrip("@")
    cutoff = normalize.cutoff_dt(since_days)

    async def _fetch():
        client = Client("en-US")
        client.load_cookies(os.path.expanduser(cookies))
        user = await client.get_user_by_screen_name(handle)
        return await user.get_tweets("Tweets", count=limit)

    out = []
    for t in asyncio.run(_fetch()):
        text = (getattr(t, "text", "") or "").strip()
        if not text:
            continue
        dt = None
        try:  # twikit gives a Twitter-style date string or a datetime
            from email.utils import parsedate_to_datetime
            raw = getattr(t, "created_at", "")
            dt = raw if hasattr(raw, "year") else parsedate_to_datetime(raw)
        except Exception:
            dt = None
        if dt and dt < cutoff:
            continue
        tid = getattr(t, "id", "")
        out.append(normalize.make_item(
            row["id"], row.get("name", handle), "twitter", text[:90],
            f"https://x.com/{handle}/status/{tid}", author="@" + handle,
            published=(dt.date().isoformat() if dt else ""), summary=text[:500],
            raw_score_hint=getattr(t, "favorite_count", 0) or 0))
    return out
