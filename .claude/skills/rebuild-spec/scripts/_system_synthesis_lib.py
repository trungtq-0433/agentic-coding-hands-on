# layout-exempt: rebuild-spec synthesis helpers — docs/system is this skill's own output target
"""System-synthesis helpers for Phase D rebuild-spec.

RT2-F6:  sanitize_field — strip/escape Markdown-injection chars before render.
RT2-F7:  load_digests — field-length caps + symlink reject.
RT2-F10: snapshot_hash — sha over all component source_sha for stale guard.
RT2-F15: correlate_entities — delegated to _entity_correlation_lib.
         build_interaction_edges — sync(rpc)+async(topic); unresolvable → no phantom edge.
Stdlib only. Heavy correlation logic lives in _entity_correlation_lib.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter
from typing import Any

from _entity_correlation_lib import correlate_entities  # noqa: F401 — re-exported

# Synthesis output-format version. Folded into snapshot_hash so a format change (not
# just a source change) trips the [WARN] stale_digest guard. Tracks the skill version.
SYNTHESIS_FORMAT_VERSION = "22.0.0"

# ---------------------------------------------------------------------------
# RT2-F6 — Markdown-sanitize gate
# ---------------------------------------------------------------------------

_NEWLINE_RE = re.compile(r"[\r\n]+")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG_RE = re.compile(r"<[^>]*>")


def sanitize_field(s: object) -> str:
    """Sanitize any digest string field for safe Markdown rendering (RT2-F6).

    Strips/escapes: ``|``, newlines, backticks, ``[text](url)`` links, ``<...>`` HTML.
    EVERY string field MUST pass through this before being written to docs/system/*.
    """
    if s is None:
        return ""
    text = str(s)
    text = _LINK_RE.sub(r"\1", text)      # [text](url) → text
    text = _HTML_TAG_RE.sub("", text)     # strip <...>
    text = _NEWLINE_RE.sub(" ", text)     # newlines → space
    text = text.replace("|", r"\|")       # escape table separator
    text = text.replace("`", "'")         # escape code fence
    text = text.replace("[", r"\[").replace("]", r"\]")  # escape link/cell brackets
    return text.strip()


# ---------------------------------------------------------------------------
# Mermaid-injection gate (red-team #3 — sanitize_field is Markdown-only)
# ---------------------------------------------------------------------------

_MERMAID_ID_STRIP_RE = re.compile(r"[^A-Za-z0-9_-]+")


def mermaid_safe_id(s: object) -> str:
    """Return a Mermaid-safe node id ([A-Za-z0-9_-] only).

    Mermaid node ids are unquoted tokens: an unescaped ``"``, ``;``, ``[`` or newline in
    a raw service name can break out of the node and inject directives. Collapse every
    other character to ``_``; an all-unsafe name degrades to ``svc``. Markdown's
    ``sanitize_field`` does NOT cover this surface (red-team #3).
    """
    ident = _MERMAID_ID_STRIP_RE.sub("_", str(s or "")).strip("_")
    return ident or "svc"


def mermaid_safe_label(s: object) -> str:
    """Return a Mermaid-safe quoted-label body.

    Labels live inside ``["..."]`` node shapes and ``|"..."|`` edge delimiters. Every
    char that a Mermaid parser may treat as structural even inside quotes is mapped to
    its numeric HTML entity so it renders as text and cannot break out:
    ``"`` → ``#quot;``, ``|`` → ``#124;`` (the edge-label delimiter),
    ``]`` → ``#93;`` (could close a ``[...]`` node shape),
    `` ` `` → ``#96;`` (backtick could start a code-fence in the surrounding Markdown).
    HTML tags are stripped (``<...>`` → empty) to avoid breaking renderers.
    Newlines collapse to a space.
    """
    text = _NEWLINE_RE.sub(" ", str(s or ""))
    text = _HTML_TAG_RE.sub("", text)       # strip <...> HTML tags
    text = text.replace('"', "#quot;")
    text = text.replace("|", "#124;")
    text = text.replace("]", "#93;")
    text = text.replace("`", "#96;")
    return text.strip()


# ---------------------------------------------------------------------------
# Field-length caps (RT2-F7)
# ---------------------------------------------------------------------------

_CAPS = {"service": 128, "name": 256}
_ARRAY_MAX = 1000


def _check_caps(digest: dict[str, Any], path: str) -> None:
    svc = digest.get("service", "")
    if len(str(svc)) > _CAPS["service"]:
        raise ValueError(
            f"Digest {path!r}: 'service' exceeds {_CAPS['service']} chars "
            f"(got {len(str(svc))})"
        )
    for arr_key in ("rpc", "topic", "entity"):
        arr = digest.get(arr_key, [])
        if not isinstance(arr, list):
            continue
        if len(arr) > _ARRAY_MAX:
            raise ValueError(
                f"Digest {path!r}: '{arr_key}' array exceeds {_ARRAY_MAX} entries "
                f"(got {len(arr)})"
            )
        for item in arr:
            if isinstance(item, dict):
                n = str(item.get("name", ""))
                if len(n) > _CAPS["name"]:
                    raise ValueError(
                        f"Digest {path!r}: '{arr_key}[].name' exceeds "
                        f"{_CAPS['name']} chars (got {len(n)})"
                    )


# ---------------------------------------------------------------------------
# RT2-F7 — load_digests
# ---------------------------------------------------------------------------

def load_digests(source: str | list[str]) -> list[dict[str, Any]]:
    """Load all ``_service-digest.json`` files from a directory or explicit path list.

    Enforces field-length caps (RT2-F7), rejects symlinks, requires provenance fields.
    Returns parsed digest dicts; sanitize_field is applied at render time.
    """
    if isinstance(source, str):
        paths: list[str] = []
        for root, _dirs, files in os.walk(source):
            for fname in files:
                if fname == "_service-digest.json":
                    paths.append(os.path.join(root, fname))
        paths.sort()
    else:
        paths = list(source)

    digests: list[dict[str, Any]] = []
    for p in paths:
        # Symlink rejection: realpath != abspath means a symlink component
        if os.path.islink(p) or os.path.realpath(p) != os.path.abspath(p):
            print(f"[WARN] skipping symlink digest: {p}", file=sys.stderr)
            continue
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[WARN] cannot load digest {p}: {exc}", file=sys.stderr)
            continue
        if not isinstance(d, dict):
            print(f"[WARN] digest {p} is not a JSON object — skipping", file=sys.stderr)
            continue
        if not d.get("source_sha") or not d.get("generated_at"):
            print(
                f"[WARN] digest {p} missing 'source_sha'/'generated_at' — skipping",
                file=sys.stderr,
            )
            continue
        try:
            _check_caps(d, p)
        except ValueError as exc:
            # Skip the one offending digest (consistent with the non-dict / missing-
            # provenance guards above) rather than aborting the whole multi-component
            # synthesis on a single malformed component.
            print(f"[WARN] digest {p} exceeds field caps — skipping: {exc}", file=sys.stderr)
            continue
        digests.append(d)
    return digests


# ---------------------------------------------------------------------------
# RT2-F10 — snapshot_hash
# ---------------------------------------------------------------------------

def snapshot_hash(digests: list[dict[str, Any]], version: str = "") -> str:
    """Deterministic sha256 over all component source_sha values + format version (RT2-F10).

    The ``version`` (the synthesis output-format version) is folded in so that a
    format change alone — not just a source change — trips the stale-digest guard.
    """
    h = hashlib.sha256()
    if version:
        h.update(f"__format__:{version}\n".encode())
    for d in sorted(digests, key=lambda x: str(x.get("service", ""))):
        h.update(f"{d.get('service', '')}:{d.get('source_sha', '')}\n".encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# build_interaction_edges
# ---------------------------------------------------------------------------

def build_interaction_edges(digests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build cross-service interaction edges from rpc + topic arrays.

    Sync: outbound rpc name matched to exactly one inbound in another service.
    Async: topic producer → consumer, matched by topic name string.
    All edges: verified=False (caller renders [UNVERIFIED]).
    Unresolvable targets (0 or >1 inbound matches): NO phantom edge emitted.
    """
    edges: list[dict[str, Any]] = []

    # Index inbound rpc → services that expose it
    inbound_rpc: dict[str, list[str]] = {}
    for d in digests:
        svc = str(d.get("service", ""))
        for rpc in d.get("rpc", []):
            if isinstance(rpc, dict) and str(rpc.get("direction", "")) == "inbound":
                inbound_rpc.setdefault(str(rpc.get("name", "")), []).append(svc)

    # Index topic producers and consumers
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    for d in digests:
        svc = str(d.get("service", ""))
        for t in d.get("topic", []):
            if not isinstance(t, dict):
                continue
            tname = str(t.get("name", ""))
            if t.get("role") == "producer":
                producers.setdefault(tname, []).append(svc)
            elif t.get("role") == "consumer":
                consumers.setdefault(tname, []).append(svc)

    # Sync edges
    for d in digests:
        src = str(d.get("service", ""))
        for rpc in d.get("rpc", []):
            if not isinstance(rpc, dict) or str(rpc.get("direction", "")) != "outbound":
                continue
            name = str(rpc.get("name", ""))
            resolved = [t for t in inbound_rpc.get(name, []) if t != src]
            if len(resolved) == 1:
                edges.append({"from": src, "to": resolved[0],
                               "type": "sync", "label": name, "verified": False})

    # Async edges
    seen: set[tuple[str, str, str]] = set()
    for tname, prod_svcs in producers.items():
        for p_svc in prod_svcs:
            for c_svc in consumers.get(tname, []):
                if p_svc == c_svc:
                    continue
                key = (p_svc, c_svc, tname)
                if key not in seen:
                    seen.add(key)
                    edges.append({"from": p_svc, "to": c_svc,
                                   "type": "async", "label": tname, "verified": False})

    # Deterministic order: async edges derive from dict iteration whose insertion order
    # tracks digest array ordering. Sort so identical logical content renders identically
    # across runs (no spurious doc churn).
    edges.sort(key=lambda e: (str(e.get("from", "")), str(e.get("to", "")),
                              str(e.get("type", "")), str(e.get("label", ""))))
    return edges


# ---------------------------------------------------------------------------
# Topology summaries (interaction-graph fan-in/out + data-ownership-map)
# ---------------------------------------------------------------------------

def fan_in_out(edges: list[dict[str, Any]]) -> tuple[Counter, Counter]:
    """Return (fan_out, fan_in) Counters keyed by service over the edge list.

    fan_out[svc] = edges leaving svc; fan_in[svc] = edges arriving at svc. Replaces a
    standalone dependency-matrix (red-team #2/#6): the same dependency signal, summarised.
    """
    fan_out: Counter = Counter()
    fan_in: Counter = Counter()
    for e in edges:
        fan_out[str(e.get("from", ""))] += 1
        fan_in[str(e.get("to", ""))] += 1
    return fan_out, fan_in


def self_loop_topics(digests: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Topics a single service both produces AND consumes (red-team #15 — noted, not dropped).

    build_interaction_edges skips these (no self-edge), so they would vanish silently;
    surfaced here so the interaction-graph can render them as a note.
    """
    loops: list[tuple[str, str]] = []
    for d in digests:
        svc = str(d.get("service", ""))
        prod: set[str] = set()
        cons: set[str] = set()
        for t in d.get("topic", []):
            if not isinstance(t, dict):
                continue
            name = str(t.get("name", ""))
            if t.get("role") == "producer":
                prod.add(name)
            elif t.get("role") == "consumer":
                cons.add(name)
        for name in sorted(prod & cons):
            loops.append((svc, name))
    return loops


def event_flows(digests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-topic producer→consumer map: [{topic, producers[], consumers[]}] sorted by topic."""
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    for d in digests:
        svc = str(d.get("service", ""))
        for t in d.get("topic", []):
            if not isinstance(t, dict):
                continue
            tname = str(t.get("name", ""))
            if t.get("role") == "producer":
                producers.setdefault(tname, []).append(svc)
            elif t.get("role") == "consumer":
                consumers.setdefault(tname, []).append(svc)
    flows: list[dict[str, Any]] = []
    for tname in sorted(set(producers) | set(consumers)):
        flows.append({
            "topic": tname,
            "producers": sorted(set(producers.get(tname, []))),
            "consumers": sorted(set(consumers.get(tname, []))),
        })
    return flows


def service_dependencies(edges: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return per-service sorted unique out-neighbour names from resolved edges only.

    Derives directly from build_interaction_edges output (no phantom edges — only
    edges that passed the single-inbound-match / topic-name-match gate).
    Returns {from_svc: sorted(set(to_svc names))}.
    """
    deps: dict[str, set[str]] = {}
    for e in edges:
        src = str(e.get("from", ""))
        tgt = str(e.get("to", ""))
        if src and tgt:
            deps.setdefault(src, set()).add(tgt)
    return {svc: sorted(targets) for svc, targets in deps.items()}


# ---------------------------------------------------------------------------
# Entity-name canonicalization (Phase 01 — dirty-entity filter + dedup)
# ---------------------------------------------------------------------------

# Doc-section headings that `parse_entities` lifts from entities.md as if they were
# entity names. Matched case-insensitively against the FULL trimmed name (never a
# substring), so a real entity literally named "Summary" is the only false-positive
# surface — accepted and documented. Keep lowercased canonical forms.
_JUNK_ENTITY_NAMES = frozenset({
    "entity relationship diagram",
    "entities",
    "summary",
    "validation rules",
})

# "MODEL004 — Candidate" / "MODEL12 - Candidate" → "Candidate". Requires an em-dash, en-dash,
# or hyphen separator, so a legit name like "MODEL3 Pricing" (no separator) is untouched.
_MODEL_PREFIX_RE = re.compile(r"^MODEL\d+\s*[—–-]\s*")


# Role → reading/layer tier, shared by the layer-diagram renderer and the nav reading-order
# (L1 — single source of truth so the two never drift). gateway/entry = 0, services = 1,
# frontend = 2; unknown roles default to the services tier.
ROLE_TIER: dict[str, int] = {
    "gateway": 0, "api-gateway": 0, "api_gateway": 0,
    "domain-service": 1, "service": 1, "backend": 1, "fullstack": 1,
    "frontend": 2,
}


def role_tier(role: object) -> int:
    """Return the reading/layer tier for a digest role (unknown → services tier)."""
    return ROLE_TIER.get(str(role or "").lower().replace(" ", "-"), 1)


def _canonical_entity_name(name: str) -> str | None:
    """Canonicalize an entity name; return None when it is doc-section junk.

    Strips a leading ``MODELnnn — `` prefix and trims; returns None when the result is
    empty or (case-folded) a known doc-section heading. Shared by parse_entities (source
    filter) and entity_ownership (downstream dedup) so the denylist lives in ONE place.
    """
    canon = _MODEL_PREFIX_RE.sub("", str(name or "")).strip()
    if not canon or canon.casefold() in _JUNK_ENTITY_NAMES:
        return None
    return canon


def entity_ownership(digests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flat ownership rows: owner = the declaring service (red-team #1 — derivable signal).

    Returns [{owner, name, id_field, id_type, visibility}] sorted by (owner, name).
    Junk doc-section headings are dropped and rows are deduped by canonical (owner, name)
    — a service's entity is listed once even if it appears under both `MODELnnn — X` and
    `X` headings (Phase 01). No speculative consumer column — the data cannot support it.
    """
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for d in digests:
        svc = str(d.get("service", ""))
        for ent in d.get("entity", []):
            if not isinstance(ent, dict):
                continue
            canon = _canonical_entity_name(str(ent.get("name", "")))
            if canon is None:
                continue
            key = (svc, canon)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "owner": svc,
                "name": canon,
                "id_field": str(ent.get("id_field", "")),
                "id_type": str(ent.get("id_type", "")),
                "visibility": str(ent.get("visibility", "internal")),
            })
    return sorted(rows, key=lambda r: (r["owner"], r["name"]))
