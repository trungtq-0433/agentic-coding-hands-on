"""KOL / media feed collectors that actually return content for free:
Bluesky author feeds (the practical replacement for X) and YouTube channel feeds.

Bluesky has a free unauthenticated public API; YouTube exposes a per-channel
RSS/Atom feed. X/Twitter has no free API and stays agent-native (WebSearch).
Third-party deps are imported lazily; collectors never raise.
"""

from . import normalize

_UA = {"User-Agent": "tkm-kensan/1.0 (learning-briefing)"}
_TIMEOUT = 20


def collect_bluesky(row, since_days, limit=20):
    """Recent original posts from a KOL's Bluesky author feed (handle = actor)."""
    import requests
    actor = (row.get("handle") or "").lstrip("@")
    cutoff = normalize.cutoff_dt(since_days).date().isoformat()
    data = requests.get("https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed",
                        headers=_UA, params={"actor": actor, "limit": limit, "filter": "posts_no_replies"},
                        timeout=_TIMEOUT).json()
    out = []
    for entry in (data.get("feed", []) if isinstance(data, dict) else []):
        if entry.get("reason"):  # skip reposts — we want the KOL's own voice
            continue
        post = entry.get("post", {})
        rec = post.get("record", {})
        text = (rec.get("text") or "").strip()
        if not text:
            continue
        day = normalize.iso_to_date(rec.get("createdAt"))
        if day and day < cutoff:
            continue
        handle = post.get("author", {}).get("handle", actor)
        rkey = post.get("uri", "").rsplit("/", 1)[-1]
        url = f"https://bsky.app/profile/{handle}/post/{rkey}"
        out.append(normalize.make_item(
            row["id"], row.get("name", handle), "bluesky", text[:90], url,
            author="@" + handle, published=day, summary=text[:400],
            raw_score_hint=post.get("likeCount", 0)))
    return out


def collect_youtube(row, since_days, limit=15, enrich_n=4):
    """Recent uploads from an AI YouTube channel (handle = UC... channel_id).

    Discovery is the channel RSS feed (titles/links/dates + the author-written
    description). When `yt-dlp` is present, the most-recent `enrich_n` items also
    get the spoken-content transcript appended to their summary; those are tagged
    `backend: "yt-dlp"`, the rest `backend: "rss"`.
    """
    import feedparser

    from . import backends, youtube_backend
    channel_id = (row.get("handle") or "").strip()
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url, request_headers=_UA)
    cutoff, out = normalize.cutoff_dt(since_days), []
    from datetime import datetime, timezone
    for e in feed.entries[:limit * 2]:
        st = getattr(e, "published_parsed", None)
        dt = datetime(*st[:6], tzinfo=timezone.utc) if st else None
        if dt and dt < cutoff:
            continue
        # The feed carries the full author-written video description (often a real
        # summary + chapters) — keep it so the briefing analyses content, not the title.
        desc = (getattr(e, "summary", "") or getattr(e, "media_description", "") or "").strip()
        views = (getattr(e, "media_statistics", {}) or {}).get("views", "")
        summary = (f"[{views} views] " if views else "") + desc[:1200]
        out.append(normalize.make_item(
            row["id"], row.get("name", "YouTube"), "youtube",
            getattr(e, "title", ""), getattr(e, "link", ""),
            author=getattr(e, "author", ""), published=(dt.date().isoformat() if dt else ""),
            summary=summary, raw_score_hint=int(views) if str(views).isdigit() else 0))
        if len(out) >= limit:
            break
    # Bounded transcript enrichment: only when yt-dlp is installed, only the
    # most-recent enrich_n items (transcripts are large + network-bound).
    if backends.which("yt-dlp"):
        for it in out[:enrich_n]:
            text = youtube_backend.transcript(it["url"])
            if text:
                it["summary"] = (it["summary"] + "\n[transcript] " + text).strip()
                it["backend"] = "yt-dlp"
    backends.tag_backend(out, "rss")  # stamp the un-enriched remainder
    return out


def collect_twitter(row, since_days, limit=20):
    """Recent tweets of a KOL — OPT-IN, dormant by default.

    Chain (Agent-Reach order): twitter-cli → OpenCLI → twikit. Each stage skips
    itself when its prerequisite is absent (binary not on PATH / no
    TWITTER_COOKIES), so an unconfigured X collector returns []. Backend logic
    lives in `x_backend.py`. See references/x-facebook-sources.md (burner/ToS).
    """
    from . import backends, x_backend
    chain = [
        ("twitter-cli", lambda: x_backend.cli_tweets("twitter", row, since_days, limit)),
        ("opencli", lambda: x_backend.cli_tweets("opencli", row, since_days, limit)),
        ("twikit", lambda: x_backend.twikit_tweets(row, since_days, limit)),
    ]
    items, served, _ = backends.route(chain)
    return backends.tag_backend(items, served)


def collect_reddit(row, since_days, limit=20):
    """Reddit posts for a subreddit/topic — OPT-IN, dormant by default.

    Chain: OpenCLI (needs login state) → rdt-cli; returns [] unless a CLI is
    installed. Reddit blocks anonymous JSON, so without a CLI the deep-dive's
    agent-native WebSearch still covers Reddit. Backend logic lives in
    `reddit_backend.py`. See references/x-facebook-sources.md (burner/ToS).
    """
    from . import backends, reddit_backend
    chain = [
        ("opencli", lambda: reddit_backend.posts("opencli", row, since_days, limit)),
        ("rdt-cli", lambda: reddit_backend.posts("rdt", row, since_days, limit)),
    ]
    items, served, _ = backends.route(chain)
    return backends.tag_backend(items, served)


_DISPATCH = {
    "bluesky": collect_bluesky,
    "youtube": collect_youtube,
    "twitter": collect_twitter,
    "reddit": collect_reddit,
}
