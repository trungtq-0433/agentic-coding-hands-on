"""GitHub fetch backends: the `gh` CLI (primary) and direct REST (fallback).

`gh api` reuses the user's existing gh login, so it is NOT bound by the 60 req/h
unauthenticated cap that throttles `api.github.com` — that is the whole point of
this backend. `gh api` returns the *identical* JSON the REST API returns, so the
response-parsing in every GitHub collector is reused verbatim; only the fetch
changes here.

All returned JSON is GitHub-authored *untrusted data* — collectors read only
known fields into normalized items; nothing here executes it. Subprocess args are
a fixed list (no shell), and only kit-controlled path/params reach argv.
"""

import json
import os
import subprocess
from urllib.parse import urlencode

from . import backends

_UA = {"User-Agent": "tkm-kensan/1.0 (learning-briefing)"}
_TIMEOUT = 25
_GH_TIMEOUT = 30


def gh_headers():
    """REST headers for the fallback path (honors an optional GITHUB_TOKEN)."""
    h = dict(_UA)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def gh_available():
    """True only when gh is installed AND authenticated (cached via backends)."""
    return backends.gh_active()


def gh_get_json(path, params=None):
    """Run `gh api -X GET "<path>?<query>"` and return parsed JSON.

    `path` is a REST path without host (e.g. "search/repositories"). Raises
    RuntimeError on non-zero exit so `backends.route` falls back to REST.
    """
    full = path.lstrip("/")
    if params:
        full = f"{full}?{urlencode(params)}"
    proc = subprocess.run(["gh", "api", "-X", "GET", full],
                          capture_output=True, text=True, timeout=_GH_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {full!r} exit {proc.returncode}: {proc.stderr.strip()[:200]}")
    return json.loads(proc.stdout)


def api_get_json(url, params=None, headers=None):
    """Direct REST fetch via requests (the fallback path)."""
    import requests  # lazy: only the fallback needs the third-party dep
    return requests.get(url, headers=headers or gh_headers(), params=params,
                        timeout=_TIMEOUT).json()


def github_backends(path, params=None, api_url=None):
    """Ordered `(name, thunk)` list for one GitHub endpoint: gh first (when
    authenticated), then the REST fallback. Pass to `backends.route(...)`."""
    api_url = api_url or f"https://api.github.com/{path.lstrip('/')}"
    chain = []
    if gh_available():
        chain.append(("gh", lambda: gh_get_json(path, params)))
    chain.append(("api", lambda: api_get_json(api_url, params, gh_headers())))
    return chain
