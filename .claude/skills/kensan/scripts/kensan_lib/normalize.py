"""URL canonicalization, stable item ids, and the normalized item shape.

Stdlib only — safe to import anywhere. The canonical URL is the dedup key, so
the agent-native social step must canonicalize the same way (exposed via
`index_store.py canonicalize <url>`).
"""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def cutoff_dt(since_days):
    """UTC datetime `since_days` ago (floored at 1 day). Shared by collectors."""
    return datetime.now(timezone.utc) - timedelta(days=max(1, int(since_days)))


def iso_to_date(value):
    """Best-effort 'YYYY-MM-DD' from an ISO-8601 string, else ''."""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except (ValueError, AttributeError):
        return (value[:10] if isinstance(value, str) else "")

# Tracking params that never identify content and must be stripped before hashing.
_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "s", "igshid"}


def canonicalize_url(url: str) -> str:
    """Return a stable, comparable form of *url*.

    Lowercases scheme + host, drops the fragment, removes tracking query params,
    sorts remaining params, and strips a trailing slash.
    """
    if not url:
        return ""
    url = url.strip()
    # Scheme-less input ("example.com/foo") → prefix "//" so the host parses as
    # netloc instead of landing in the path.
    if "://" not in url and not url.startswith("//"):
        url = "//" + url
    parts = urlsplit(url)
    if not parts.netloc:
        return ""
    # Force https so http/https variants of the same page share one dedup id.
    scheme = "https"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    kept = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=False)
        if not k.lower().startswith(_TRACKING_PREFIXES) and k.lower() not in _TRACKING_KEYS
    ]
    kept.sort()
    query = urlencode(kept)
    path = parts.path.rstrip("/") or ""
    return urlunsplit((scheme, host, path, query, ""))


def _sha1(text: str, length: int = 16) -> str:
    return hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()[:length]


def item_id(url: str) -> str:
    """Dedup id = short SHA-1 of the canonical URL; empty for url-less items
    (which are dropped: no link, no inclusion)."""
    canon = canonicalize_url(url)
    return _sha1(canon) if canon else ""


def content_hash(title: str, summary: str = "") -> str:
    """Change-detection hash over normalized title + summary."""
    norm = re.sub(r"\s+", " ", f"{title} {summary}".strip().lower())
    return _sha1(norm)


def make_item(source_id, source, type_, title, url, author="", published="",
              summary="", lang="en", raw_score_hint=0, backend=""):
    """Build a normalized item dict. `id` is derived from the canonical URL.

    `backend` is optional metadata naming which fetch backend served the item
    (e.g. "gh" vs "api", "yt-dlp" vs "rss"); it does NOT affect `id`/`content_hash`.
    """
    return {
        "id": item_id(url),
        "source_id": source_id,
        "source": source,
        "type": type_,
        "title": (title or "").strip(),
        "url": url,
        "author": author,
        "published": published,
        "summary": (summary or "").strip(),
        "lang": lang,
        "raw_score_hint": raw_score_hint,
        "content_hash": content_hash(title or "", summary or ""),
        "backend": backend,
    }


def build_provenance(items):
    """Summarize where a collected item set came from: counts by type + per-source.

    `sources` keeps the full per-source list (name/type/count) even when a consumer
    only renders the counts — so the link-list view can be added later for free.
    """
    by_type, sources, by_backend = {}, {}, {}
    for it in items:
        t = it.get("type", "") or it.get("platform", "")
        by_type[t] = by_type.get(t, 0) + 1
        b = it.get("backend")
        if b:  # only items that recorded a serving backend
            by_backend[b] = by_backend.get(b, 0) + 1
        sid = it.get("source_id") or it.get("source") or t or "unknown"
        s = sources.setdefault(sid, {"id": sid, "name": it.get("source", sid), "type": t, "count": 0})
        s["count"] += 1
    return {"by_type": by_type,
            "by_backend": by_backend,
            "sources": sorted(sources.values(), key=lambda x: -x["count"])}


def make_discussion_item(platform, source, title, url, author="", published="",
                         excerpt="", upvotes=0, comments=0, lang="en"):
    """Build a normalized *discussion* item (a post/comment/issue worth quoting).

    Shares `id`/`content_hash` with feed items so the dedup ledger treats both
    uniformly; adds `kind`, `platform`, `excerpt`, and `engagement`.
    """
    excerpt = (excerpt or "").strip()
    return {
        "id": item_id(url),
        "kind": "discussion",
        "platform": platform,
        "source": source,
        "type": platform,
        "title": (title or "").strip(),
        "url": url,
        "author": author,
        "published": published,
        "excerpt": excerpt[:280],
        "engagement": {"upvotes": int(upvotes or 0), "comments": int(comments or 0)},
        "lang": lang,
        "content_hash": content_hash(title or "", excerpt),
    }
