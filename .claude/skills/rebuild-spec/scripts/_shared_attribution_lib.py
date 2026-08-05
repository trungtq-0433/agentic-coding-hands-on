"""Shared-layer attribution (Phase 05).

A multi-executable repo (Ishindenshin shape) keeps each `PG/<MODULE>/` component's DB objects in a
SIBLING tree `DB/{TABLE,SP,VIEW}/<MODULE>/`. The shared DB scan runs ONCE (`extract_sql_schema
--root DB/`) and attribution to a component is by the `<MODULE>` segment present in every object's
citation path — a DETERMINISTIC rule, never LLM prose (RT Finding 5).

The module label of a `PG/<MODULE>/` component is its executable basename (= `<MODULE>`), declared by
the convention `PG/<MODULE>` ⇔ `DB/<TYPE>/<MODULE>`. Full-segment equality is what kills the
`POS ⊂ POSDEN` substring bug.

Stdlib only.
"""
from __future__ import annotations

from typing import Any


def matches_module_label(citation: str, label: str) -> bool:
    """True iff `label` is a FULL path segment of `citation` (not a substring).

    `"POS"` matches `"DB/TABLE/POS/M_POS_HEAD.sql:5"` (segment `POS`) but NOT
    `"DB/TABLE/POSDEN/x.sql"` (segment `POSDEN`) nor the filename `M_POS_HEAD.sql` (substring only).
    A trailing `:line` locator is stripped before splitting on `/`.
    """
    if not label:
        return False
    path = citation.split(":", 1)[0].replace("\\", "/")
    return label in path.split("/")


def filter_shared_digest_by_label(digest: dict[str, Any], label: str) -> dict[str, Any]:
    """Per-component FILTERED view of a shared-DB digest.

    Returns a shallow copy keeping only `db_objects` whose `citation` carries the `<label>` segment
    (`matches_module_label`). The authoring step consumes this view directly — it is already
    attributed and MUST NOT be re-filtered. `filtered_for_label` records which module it was cut for.
    """
    kept = [
        obj for obj in digest.get("db_objects", [])
        if matches_module_label(obj.get("citation", ""), label)
    ]
    out = dict(digest)
    out["db_objects"] = kept
    out["filtered_for_label"] = label
    return out
