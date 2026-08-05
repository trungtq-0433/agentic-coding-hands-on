"""Entity correlation heuristics for Phase D synthesis (RT2-F15).

Independent of the glossary (glossary is OUTPUT, not INPUT).
Every auto-match is [UNVERIFIED] — no confident auto-merge.

Stdlib only.
"""
from __future__ import annotations

import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Name normalisation
# ---------------------------------------------------------------------------

_SINGULARIZE_SUFFIXES = [("ies", "y"), ("ses", "s"), ("s", "")]


def _normalize_name(name: str) -> str:
    """Case-fold + strip separators + singularize for entity name matching."""
    n = unicodedata.normalize("NFC", name).casefold()
    n = n.replace("_", "").replace("-", "")
    for suffix, replacement in _SINGULARIZE_SUFFIXES:
        if n.endswith(suffix) and len(n) > len(suffix) + 2:
            n = n[: -len(suffix)] + replacement
            break
    return n


# ---------------------------------------------------------------------------
# Jaro-Winkler (stdlib — no jellyfish/rapidfuzz)
# ---------------------------------------------------------------------------

def _jaro_winkler(s1: str, s2: str) -> float:
    """Jaro-Winkler similarity in [0.0, 1.0]."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_dist = max(len1, len2) // 2 - 1
    if match_dist < 0:
        match_dist = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3
    prefix = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break
    return jaro + prefix * 0.1 * (1 - jaro)


# ---------------------------------------------------------------------------
# Type-family compatibility
# ---------------------------------------------------------------------------

_TYPE_FAMILIES: dict[str, str] = {
    "uuid": "string", "string": "string", "str": "string",
    "text": "string", "varchar": "string",
    "int": "integer", "int32": "integer", "int64": "integer",
    "integer": "integer", "long": "integer",
    "bigint": "integer", "smallint": "integer",
}
_JW_THRESHOLD = 0.92


def _type_family(id_type: str) -> str:
    return _TYPE_FAMILIES.get(str(id_type).lower().strip(), "other")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def correlate_entities(digests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Correlate entity names across services using independent heuristics (RT2-F15).

    Returns suggestion dicts with confidence="UNVERIFIED". Never auto-merges.
    Glossary is an OUTPUT of this process, not an input.
    """
    entities: list[dict[str, Any]] = []
    for d in digests:
        svc = str(d.get("service", ""))
        for ent in d.get("entity", []):
            if not isinstance(ent, dict):
                continue
            entities.append({
                "service": svc,
                "name": str(ent.get("name", "")),
                "id_field": str(ent.get("id_field", "")),
                "id_type": str(ent.get("id_type", "")),
                "visibility": str(ent.get("visibility", "internal")),
            })

    suggestions: list[dict[str, Any]] = []
    seen: set[frozenset[int]] = set()

    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            pair_key = frozenset({i, j})
            if pair_key in seen:
                continue
            a, b = entities[i], entities[j]
            if a["service"] == b["service"]:
                continue
            # Review M2: a `private` entity is service-internal — never a shared-entity candidate.
            # (public/internal still surface as [UNVERIFIED] suggestions for the consent gate.)
            if a["visibility"] == "private" or b["visibility"] == "private":
                continue

            norm_a = _normalize_name(a["name"])
            norm_b = _normalize_name(b["name"])

            matched, reason = False, ""
            if norm_a and norm_a == norm_b:
                matched = True
                reason = f"normalized-name-exact ({a['name']!r} ≈ {b['name']!r})"
            elif norm_a and norm_b:
                jw = _jaro_winkler(norm_a, norm_b)
                if jw >= _JW_THRESHOLD:
                    matched = True
                    reason = f"jaro-winkler={jw:.3f} ({a['name']!r} ≈ {b['name']!r})"

            if not matched:
                continue

            seen.add(pair_key)
            fam_a, fam_b = _type_family(a["id_type"]), _type_family(b["id_type"])
            type_note = "compatible" if fam_a == fam_b else f"mismatch:{fam_a}-vs-{fam_b}"
            suggestions.append({
                "entity_a": a, "entity_b": b,
                "confidence": "UNVERIFIED",
                "match_reason": reason,
                "type_note": type_note,
            })

    return suggestions
