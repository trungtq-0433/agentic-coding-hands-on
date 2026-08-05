"""Engine 1 — redundancy (thừa) detection, NARROWED to the mechanical case.

The subjective "restates another artifact with no added why" case is a reviewer judgment and is
routed to Engine 3 as WARN [Red-team F8 / user Q2]. This lib decides ONLY the unambiguous
deterministic FAIL: the SAME artifact emitted twice — two distinct artifact files whose
normalized content is byte-identical (a genuine duplicate, e.g. a copy-pasted feature spec).

A verbatim-similarity detector would need to EXEMPT spans adjacent to a `**Source:**`/ADR
citation (mandated ADR quotes are required by contract, not restatement) [Red-team FM-F4]. This
lib does not do span-similarity at all — it matches whole-artifact identity — so that trap is
avoided by construction. Trivially-small / template-stub files are exempt (a shared empty
scaffold is not a duplicate).

Stdlib only.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Below this many non-whitespace chars, an "identical" file is a stub/scaffold, not a real dup.
_MIN_MEANINGFUL_CHARS = 200

_WS_RE = re.compile(r"\s+")


def _normalized_hash(text: str) -> str:
    """Whitespace-collapsed content hash (ignores trivial reformatting)."""
    collapsed = _WS_RE.sub(" ", text).strip()
    return hashlib.sha256(collapsed.encode("utf-8")).hexdigest()


def _meaningful_len(text: str) -> int:
    return len(_WS_RE.sub("", text))


def find_duplicate_artifacts(artifacts: list[dict]) -> dict:
    """Detect literal duplicate artifacts (same content, ≥2 distinct paths).

    `artifacts` items: {"path": <abs>, "kind": ..., "present": bool}.

    Returns:
        {
          "duplicates": [ {kind: "DUP_ARTIFACT", paths: [...], evidence} ],
          "exempted": [ {path, reason} ],   # stubs/templates skipped, logged
        }
    """
    by_hash: dict[str, list[str]] = {}
    exempted: list[dict] = []

    for art in artifacts:
        if not art.get("present"):
            continue
        path = art.get("path")
        if not path:
            continue
        p = Path(path)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _meaningful_len(text) < _MIN_MEANINGFUL_CHARS:
            exempted.append({"path": str(p), "reason": "below meaningful-content threshold (stub/scaffold)"})
            continue
        by_hash.setdefault(_normalized_hash(text), []).append(str(p))

    duplicates: list[dict] = []
    for _h, paths in by_hash.items():
        distinct = sorted(set(paths))
        if len(distinct) >= 2:
            duplicates.append({
                "kind": "DUP_ARTIFACT",
                "paths": distinct,
                "evidence": f"identical artifact content emitted at {len(distinct)} paths: {', '.join(distinct)}",
            })
    return {"duplicates": duplicates, "exempted": exempted}
