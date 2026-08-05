"""Reasoned service reading-order metadata for the aggregate nav layer (Phase 04).

Synthesis has the digests + edges; the nav layer (which renders the READMEs) runs later
and never sees them. `build_nav_metadata()` computes a deterministic, reasoned service
reading-order — which service to read first and WHY — that `synthesize_system` writes to
`docs/<lang>/system/.nav-metadata.json` for the nav renderer to consume.

Ranking (deterministic): role tier first (gateway/entry = 0, services = 1, frontend = 2),
then descending fan-in (most-depended-on first), tie-break by name. Reused components
(manifest status=="reused") are pushed last — read them after the services that consume
them. The rationale is stored as a language-neutral KEY + the fan-in count; the nav reader
formats the prose lang-aware so no English leaks into a non-en README. Stdlib only.

Fix A (v23): authoritative `reused` flag comes from manifest status=="reused" (passed in
via `reused_map`), NOT from digest `provenance`. Every digest carries provenance=
"docs-derived" (synthesized from each component's docs), so the old `_is_reused` flagged
ALL services reused. The `reused_map` is built once from `manifest_entries` by the caller
(synthesize_system.py) and passed here to avoid re-computing.
"""
from __future__ import annotations

from typing import Any

from _system_synthesis_lib import fan_in_out, role_tier  # role_tier shared with layer renderer (L1)


def build_nav_metadata(
    digests: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    reused_map: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """Return a ranked reading-order: [{service, role, rank, reused, fan_in, rationale_key}].

    Sorted by (component_reused, tier, -fan_in, service); rank assigned 1..N in that order.
    `rationale_key` is one of gateway|backend|frontend|reused — the nav reader maps it
    (plus `fan_in`) to lang-aware prose.

    Args:
        digests: list of service digest dicts (each has "service", "role", optionally "stack").
        edges: list of interaction edge dicts used to compute fan-in counts.
        reused_map: authoritative name→bool map from manifest status=="reused".
            When None (e.g. tests that predate v23), falls back to False for all services.
    """
    _fan_out, fan_in = fan_in_out(edges)
    _reused_map: dict[str, bool] = reused_map or {}
    rows: list[dict[str, Any]] = []
    for d in digests:
        svc = str(d.get("service", ""))
        # Fix A: use manifest-derived reuse flag, NOT digest provenance.
        # digest_from_docs (provenance=="docs-derived") is always True for every digest —
        # it only means the digest was synthesized from component docs, which is universal.
        component_reused = bool(_reused_map.get(svc, False))
        rows.append({
            "service": svc,
            "role": str(d.get("role", "")),
            "reused": component_reused,
            "fan_in": int(fan_in.get(svc, 0)),
            "tier": role_tier(d.get("role", "")),
            "stack": str(d.get("stack", "")),
        })
    rows.sort(key=lambda r: (r["reused"], r["tier"], -r["fan_in"], r["service"]))

    meta: list[dict[str, Any]] = []
    for rank, r in enumerate(rows, start=1):
        if r["reused"]:
            key = "reused"
        elif r["tier"] == 0:
            key = "gateway"
        elif r["tier"] == 2:
            key = "frontend"
        else:
            key = "backend"
        meta.append({
            "service": r["service"],
            "role": r["role"],
            "rank": rank,
            "reused": r["reused"],
            "fan_in": r["fan_in"],
            "rationale_key": key,
            "stack": r["stack"],
        })
    return meta
