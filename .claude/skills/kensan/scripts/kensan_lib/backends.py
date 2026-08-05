"""Lightweight fallback-routing primitive for kensan collectors.

Pattern ported from Agent-Reach (ordered backend list → first working backend
wins → a `doctor` health check) but reimplemented idiomatically: a helper, not
a framework, and stdlib-only so it is safe to import anywhere.

Nothing here executes fetched content — `route` only dispatches collector
callables, and `doctor` only probes CLI presence + env (read-only, no network).
"""

import os
import shutil
import subprocess

_WHICH_CACHE = {}
_GH_ACTIVE_CACHE = {}  # one-slot cache keyed by True


def which(cmd):
    """Cached `shutil.which` — cheap CLI-presence check, never raises."""
    if cmd not in _WHICH_CACHE:
        try:
            _WHICH_CACHE[cmd] = shutil.which(cmd)
        except Exception:
            _WHICH_CACHE[cmd] = None
    return _WHICH_CACHE[cmd]


def route(backends, *args, **kwargs):
    """Try an ordered list of `(name, callable)` backends; first non-empty wins.

    Returns `(items, served_by_name_or_None, warnings)`. A backend that returns
    an empty result → try the next. A backend that raises → record a warning
    string and try the next. Never raises.
    """
    warnings = []
    for name, fn in backends:
        try:
            items = fn(*args, **kwargs)
        except Exception as exc:  # one backend failing must not abort the chain
            warnings.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        if items:
            return items, name, warnings
    return [], None, warnings


def tag_backend(items, name):
    """Stamp each item with the backend that served it (idempotent).

    Items already carrying a non-empty `backend` are left untouched, so a
    per-item enricher (e.g. yt-dlp) can mark its winners before a bulk tag
    stamps the remainder with the fallback name.
    """
    if not name:
        return items
    for it in items:
        if isinstance(it, dict) and not it.get("backend"):
            it["backend"] = name
    return items


def gh_active():
    """True only when `gh` is installed AND authenticated. Cached per process."""
    if True in _GH_ACTIVE_CACHE:
        return _GH_ACTIVE_CACHE[True]
    active = False
    if which("gh"):
        try:
            rc = subprocess.run(["gh", "auth", "status"], capture_output=True,
                                text=True, timeout=10).returncode
            active = rc == 0
        except Exception:
            active = False
    _GH_ACTIVE_CACHE[True] = active
    return active


def doctor():
    """Per-platform backend availability (read-only — no network, no fetch)."""
    gh_present = bool(which("gh"))
    jina_on = os.environ.get("KENSAN_JINA", "1") != "0"
    return {
        "github": {
            "gh": "active" if gh_active() else ("installed" if gh_present else "missing"),
            "api": "active",  # the requests fallback is always available
        },
        "youtube": {
            "yt-dlp": "installed" if which("yt-dlp") else "missing",
            "rss": "active",
        },
        "web": {
            "jina": "active" if jina_on else "off",
            "webfetch": "active",
        },
        "x": {
            "twitter-cli": "installed" if which("twitter") else "missing",
            "opencli": "installed" if which("opencli") else "missing",
            "twikit": "active" if os.environ.get("TWITTER_COOKIES") else "dormant",
        },
        "reddit": {
            "opencli": ("active" if which("opencli") and os.environ.get("KENSAN_REDDIT_STATE")
                        else ("installed" if which("opencli") else "missing")),
            "rdt-cli": "installed" if which("rdt") else "missing",
        },
    }


def _print_doctor(report):
    for platform, entries in report.items():
        line = ", ".join(f"{b}={s}" for b, s in entries.items())
        print(f"{platform:>8}: {line}")


if __name__ == "__main__":
    _print_doctor(doctor())
