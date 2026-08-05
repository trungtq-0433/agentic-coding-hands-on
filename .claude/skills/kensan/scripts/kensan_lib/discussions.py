"""Topic-scoped community-discussion collectors (Hacker News comments, GitHub issues).

Free / no-key APIs only. Reddit and X are NOT here: Reddit fully blocks anonymous
JSON (HTTP 403, OAuth-only) and X has no free API, so both are gathered
agent-natively via WebSearch in the deep-dive step (see references/discussion-mining.md).

Third-party deps (requests) are imported lazily so importing this module never fails
when deps are absent. Collectors never raise — failures surface via
`collect_discussion_source` as a warning string.
"""

import html
import re
from datetime import datetime, timedelta, timezone

from . import backends, gh_backend, normalize

_UA = {"User-Agent": "tkm-kensan/1.0 (learning-briefing; +https://github.com/sun-asterisk-internal/takumi)"}
_TIMEOUT = 20


def _cutoff_ts(since_days):
    dt = datetime.now(timezone.utc) - timedelta(days=max(1, int(since_days)))
    return int(dt.timestamp())


def _strip_html(text):
    """Drop tags + collapse whitespace so excerpts quote clean prose."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def collect_hn_comments(topic, since_days, limit=20):
    """Hacker News *comments* matching a topic — the substance of HN debate."""
    import requests
    url = "https://hn.algolia.com/api/v1/search"
    params = {"tags": "comment", "query": topic,
              "numericFilters": f"created_at_i>{_cutoff_ts(since_days)}", "hitsPerPage": limit}
    hits = requests.get(url, headers=_UA, params=params, timeout=_TIMEOUT).json().get("hits", [])
    out = []
    for h in hits:
        text = _strip_html(h.get("comment_text", ""))
        if not text:
            continue
        out.append(normalize.make_discussion_item(
            "hn", "HN · " + (h.get("story_title") or "thread"),
            "↳ " + (h.get("story_title") or "comment"),
            f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            author=h.get("author", ""), published=(h.get("created_at", "")[:10]),
            excerpt=text, upvotes=h.get("points") or 0))
    return out


def collect_github_issues(topic, since_days, limit=15):
    """GitHub issues/discussions matching a topic — close-to-code technical debate.

    Quotes the topic phrase for precision and skips bot/dependabot noise.
    Routes via `gh` (no 60/h cap) then falls back to the REST API.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=max(1, int(since_days)))).date().isoformat()
    params = {"q": f'"{topic}" in:title,body updated:>{since}',
              "sort": "updated", "order": "desc", "per_page": limit}
    data, served, _ = backends.route(gh_backend.github_backends("search/issues", params))
    out = []
    for it in data.get("items", []) if isinstance(data, dict) else []:
        author = it.get("user", {}).get("login", "")
        if author.endswith("[bot]"):  # dependabot etc. — pure noise for learning
            continue
        repo = re.sub(r"^https://api.github.com/repos/", "", it.get("repository_url", ""))
        out.append(normalize.make_discussion_item(
            "github", f"{repo}#{it.get('number', '')}", it.get("title", ""),
            it.get("html_url", ""), author=author,
            published=(it.get("created_at", "")[:10]), excerpt=_strip_html(it.get("body", "") or ""),
            upvotes=(it.get("reactions", {}) or {}).get("total_count", 0),
            comments=it.get("comments", 0)))
    return backends.tag_backend(out, served)


_DISPATCH = {
    "hn-comments": collect_hn_comments,
    "github-issues": collect_github_issues,
}

SOURCES = list(_DISPATCH)


def collect_discussion_source(source, topic, since_days):
    """Dispatch one discussion source. Returns (items, warning_or_None)."""
    fn = _DISPATCH.get(source)
    if not fn:
        return [], f"{source}: unknown discussion source"
    try:
        return fn(topic, since_days), None
    except Exception as exc:
        return [], f"{source} (topic='{topic}'): {type(exc).__name__}: {exc}"
