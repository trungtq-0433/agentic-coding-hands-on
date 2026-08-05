"""Source collectors. Third-party deps (requests, feedparser) are imported lazily
inside each collector so importing this module never fails when deps are absent.
Every collector returns a list of normalized items and never raises — failures
surface as a warning string via `collect_source`. API-based and social/media
collectors live in `api_collectors.py` / `social_collectors.py` and are merged
into the dispatch table below.
"""

from datetime import datetime, timedelta, timezone

from . import backends, gh_backend, normalize

_UA = {"User-Agent": "tkm-kensan/1.0 (+learning-briefing)"}
_TIMEOUT = 20


def _cutoff(since_days):
    return datetime.now(timezone.utc) - timedelta(days=max(1, int(since_days)))


def _struct_to_dt(st):
    try:
        return datetime(*st[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def _iso(dt):
    return dt.date().isoformat() if dt else ""


def collect_rss(row, since_days):
    import feedparser  # lazy
    cutoff, out = _cutoff(since_days), []
    feed = feedparser.parse(row["handle"], request_headers=_UA)
    for e in feed.entries:
        dt = _struct_to_dt(getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None))
        if dt and dt < cutoff:
            continue
        out.append(normalize.make_item(
            row["id"], row.get("name", row["id"]), "rss",
            getattr(e, "title", ""), getattr(e, "link", ""),
            author=getattr(e, "author", ""), published=_iso(dt),
            summary=getattr(e, "summary", "")[:500], lang=row.get("lang", "en")))
    return out


def collect_arxiv(row, since_days):
    import feedparser
    import requests
    q = row["handle"]
    cat = q if "." in q and " " not in q else None
    search = f"cat:{cat}" if cat else f"all:{q}"
    url = ("http://export.arxiv.org/api/query?search_query=" + search +
           "&sortBy=submittedDate&sortOrder=descending&max_results=40")
    resp = requests.get(url, headers=_UA, timeout=_TIMEOUT)
    cutoff, out = _cutoff(since_days), []
    for e in feedparser.parse(resp.text).entries:
        dt = _struct_to_dt(getattr(e, "published_parsed", None))
        if dt and dt < cutoff:
            continue
        out.append(normalize.make_item(
            row["id"], row.get("name", row["id"]), "arxiv",
            getattr(e, "title", "").replace("\n", " "), getattr(e, "link", ""),
            author=", ".join(a.name for a in getattr(e, "authors", [])[:3]),
            published=_iso(dt), summary=getattr(e, "summary", "")[:500]))
    return out


def collect_github_releases(row, since_days):
    repo = row["handle"]
    data, served, _ = backends.route(
        gh_backend.github_backends(f"repos/{repo}/releases", {"per_page": 10}))
    cutoff, out = _cutoff(since_days), []
    for r in data if isinstance(data, list) else []:
        pub = r.get("published_at") or r.get("created_at") or ""
        dt = None
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None
        except Exception:
            dt = None
        if dt and dt < cutoff:
            continue
        out.append(normalize.make_item(
            row["id"], row.get("name", repo), "github-releases",
            f"{repo} {r.get('tag_name', '')} {r.get('name', '')}".strip(),
            r.get("html_url", ""), published=_iso(dt),
            summary=(r.get("body") or "")[:500]))
    return backends.tag_backend(out, served)


def collect_hn(row, since_days):
    import requests
    kw = row["handle"]
    since = int(_cutoff(since_days).timestamp())
    url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story"
           f"&query={requests.utils.quote(kw)}&numericFilters=created_at_i>{since}&hitsPerPage=30")
    hits = requests.get(url, headers=_UA, timeout=_TIMEOUT).json().get("hits", [])
    out = []
    for h in hits:
        link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append(normalize.make_item(
            row["id"], row.get("name", "Hacker News"), "hn",
            h.get("title", ""), link, author=h.get("author", ""),
            published=(h.get("created_at", "")[:10]),
            summary=f"{h.get('points', 0)} points · {h.get('num_comments', 0)} comments",
            raw_score_hint=h.get("points", 0)))
    return out


# API-based + social/media collectors live in sibling modules; merge their
# dispatch tables so collect_source handles every type from one entry point.
from . import api_collectors, social_collectors  # noqa: E402

_DISPATCH = {
    "rss": collect_rss,
    "arxiv": collect_arxiv,
    "github-releases": collect_github_releases,
    "hn": collect_hn,
    **api_collectors._DISPATCH,     # goodailist, hf-papers, github-trending, github-user
    **social_collectors._DISPATCH,  # bluesky, youtube
}


def collect_source(row, since_days):
    """Dispatch one source. Returns (items, warning_or_None).

    `social` rows are not collected here — the caller handles them agent-natively.
    """
    type_ = row.get("type")
    if type_ == "social":
        return [], None
    fn = _DISPATCH.get(type_)
    if not fn:
        return [], f"{row['id']}: unknown type '{type_}'"
    try:
        return fn(row, since_days), None
    except Exception as exc:  # never let one source break the run
        return [], f"{row['id']} ({type_}): {type(exc).__name__}: {exc}"
