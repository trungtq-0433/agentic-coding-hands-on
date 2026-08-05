"""JSON-API feed collectors: goodailist trending repos, HuggingFace daily papers,
GitHub trending search, and GitHub-user recent activity.

These replace the old brittle HTML scrapers with real endpoints. Third-party
`requests` is imported lazily; collectors never raise (the caller wraps them).
All are free / no key (GitHub honors an optional GITHUB_TOKEN for higher limits).
"""

from . import backends, gh_backend, normalize

_UA = {"User-Agent": "tkm-kensan/1.0 (learning-briefing)"}
_TIMEOUT = 25


def collect_goodailist(row, since_days, limit=30):
    """Trending AI repos from goodailist.com's JSON API (Huyền Chip)."""
    import requests
    params = {"limit": limit, "page": 1, "sort": "stars"}
    data = requests.get("https://goodailist.com/api/repos", headers=_UA,
                        params=params, timeout=_TIMEOUT).json()
    out = []
    for r in (data.get("repos", []) if isinstance(data, dict) else [])[:limit]:
        full = r.get("repo") or r.get("full_name") or ""
        if not full:
            continue
        stars = r.get("stars") or r.get("stargazers_count") or 0
        out.append(normalize.make_item(
            row["id"], "goodailist", "goodailist", full,
            f"https://github.com/{full}", published=normalize.iso_to_date(r.get("created") or r.get("updated")),
            summary=(r.get("description") or "")[:300], raw_score_hint=stars))
    return out


def collect_hf_papers(row, since_days, limit=30):
    """HuggingFace daily papers via the API (real titles, not scraped nav)."""
    import requests
    data = requests.get("https://huggingface.co/api/daily_papers", headers=_UA,
                        params={"limit": limit}, timeout=_TIMEOUT).json()
    cutoff, out = normalize.cutoff_dt(since_days).date().isoformat(), []
    for d in data if isinstance(data, list) else []:
        paper = d.get("paper", {}) or {}
        pid = paper.get("id", "")
        pub = normalize.iso_to_date(d.get("publishedAt") or paper.get("publishedAt"))
        if pub and pub < cutoff:
            continue
        out.append(normalize.make_item(
            row["id"], "HF Daily Papers", "hf-papers",
            d.get("title") or paper.get("title", ""), f"https://huggingface.co/papers/{pid}",
            published=pub, summary=(paper.get("summary") or "")[:300],
            raw_score_hint=paper.get("upvotes", 0)))
    return out


def collect_github_trending(row, since_days, limit=20):
    """Recently-pushed, most-starred repos matching a topic (handle = query/topic).

    Routes via `gh` (no 60/h cap) then falls back to the REST API.
    """
    topic = row.get("handle") or "AI"
    since = normalize.cutoff_dt(since_days).date().isoformat()
    q = f"{topic} pushed:>{since}"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": limit}
    data, served, _ = backends.route(gh_backend.github_backends("search/repositories", params))
    out = []
    for r in data.get("items", []) if isinstance(data, dict) else []:
        out.append(normalize.make_item(
            row["id"], "GitHub trending", "github-trending", r.get("full_name", ""),
            r.get("html_url", ""), published=normalize.iso_to_date(r.get("pushed_at")),
            summary=(r.get("description") or "")[:300], raw_score_hint=r.get("stargazers_count", 0)))
    return backends.tag_backend(out, served)


def _repo_meta(repo, cache):
    """description · topics · language for a repo (one call, cached) — the
    substance that says WHAT the activity is about and whether it's AI.

    Routes via `gh` then REST; this enrichment is where the 60/h cap hurts most
    (one call per repo), so the gh win is largest here.
    """
    if repo in cache:
        return cache[repo]
    meta = ""
    d, _served, _warn = backends.route(gh_backend.github_backends(f"repos/{repo}"))
    if isinstance(d, dict):
        topics = d.get("topics") or []
        meta = " · ".join(filter(None, [
            (d.get("description") or "").strip()[:180],
            ("topics: " + ", ".join(topics[:8])) if topics else "",
            d.get("language") or ""]))
    cache[repo] = meta
    return meta


def collect_github_user(row, since_days, limit=30, enrich_repos=6):
    """Recent public activity of a GitHub user (handle = login): what they ship,
    enriched with each repo's description + topics so the briefing can judge AI relevance.

    Routes via `gh` (no 60/h cap) then falls back to the REST API.
    """
    login = (row.get("handle") or "").lstrip("@")
    cutoff = normalize.cutoff_dt(since_days).date().isoformat()
    events, served, _ = backends.route(
        gh_backend.github_backends(f"users/{login}/events/public", {"per_page": limit}))
    keep = {"CreateEvent": "created", "ReleaseEvent": "released",
            "PublicEvent": "open-sourced", "PushEvent": "pushed to",
            "PullRequestEvent": "opened PR in", "IssuesEvent": "opened issue in"}
    pending, seen = [], set()
    for e in events if isinstance(events, list) else []:
        etype = e.get("type")
        if etype not in keep:
            continue
        day = normalize.iso_to_date(e.get("created_at"))
        if day and day < cutoff:
            continue
        repo = e.get("repo", {}).get("name", "")
        verb, payload = keep[etype], e.get("payload", {})
        if etype == "CreateEvent" and payload.get("ref_type") != "repository":
            continue  # only new repos, not branches/tags
        if etype == "PushEvent" and not repo.startswith(login + "/"):
            continue  # only pushes to their own repos signal "what they're building"
        title, url, base = f"{login} {verb} {repo}", f"https://github.com/{repo}", ""
        if etype in ("PullRequestEvent", "IssuesEvent"):
            if payload.get("action") != "opened":
                continue  # their contribution to any repo
            obj = payload.get("pull_request") or payload.get("issue") or {}
            url = obj.get("html_url") or url
            base = (obj.get("title") or "")[:90]
        elif etype == "ReleaseEvent":
            base = payload.get("release", {}).get("name", "")
        key = (login, verb, repo, url)
        if key in seen:
            continue
        seen.add(key)
        pending.append({"title": title, "url": url, "day": day, "repo": repo, "base": base})
    # enrich the most-recent distinct repos with description+topics (bounded — 1 call each)
    cache = {}
    for repo in list(dict.fromkeys(p["repo"] for p in pending))[:enrich_repos]:
        _repo_meta(repo, cache)
    out = []
    for p in pending:
        summary = " — ".join(filter(None, [p["base"], cache.get(p["repo"], "")]))
        out.append(normalize.make_item(
            row["id"], f"GitHub · {login}", "github-user", p["title"], p["url"],
            author=login, published=p["day"], summary=summary))
    return backends.tag_backend(out, served)


_DISPATCH = {
    "goodailist": collect_goodailist,
    "hf-papers": collect_hf_papers,
    "github-trending": collect_github_trending,
    "github-user": collect_github_user,
}
