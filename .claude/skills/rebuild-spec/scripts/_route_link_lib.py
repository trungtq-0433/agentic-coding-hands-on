"""Shared route-list.md parsing/resolution for feature↔API/route ID-link (v25.0.0).

Split out of validate_feature_api_link.py to keep it under the 200-LOC invariant;
also reused by nav wiring (mirrors _nav_table_parse_lib.py's split from _nav_feature_lib.py).

  - build_route_inventory()    — Code-column ROUTE### codes, unioned across ALL
                                  `### File:` sub-tables under Backend Routes
  - build_route_owner_map_with_dups() — ROUTE### -> {F### owners} (unioned) +
                                  duplicate ROUTE### set; build_route_owner_map()
                                  is the back-compat wrapper (dups discarded)
  - iter_route_owner_rows()    — (route_code, owner_cell) per row across ALL
                                  sub-tables with Code/Owner cols; None if NONE do
  - route_columns()            — locate (code_idx, owner_idx) in a header row
  - backend_routes_table()     — FIRST sub-table only (back-compat accessor)
  - cited_routes()             — ROUTE### tokens cited anywhere in a cell/text
  - artifact_ref_cited_routes() — ROUTE### codes in an Artifact References
                                  table's Codes Used column

Pure, stdlib-only, best-effort — never raises (returns set()/{}/[])."""
from __future__ import annotations

import re
from pathlib import Path

from _id_schemes_lib import segment_text, token_re
from _nav_table_parse_lib import _first_table_after, _split_row, data_rows

# Guarded (?<!...)PREFIX\d{3}(?![0-9]) patterns (C3) reuse token_re()'s overflow
# boundary (ROUTE1000 no longer truncates to ROUTE100). token_re() is
# case-sensitive; wrap IGNORECASE so mixed-case citations still match as before.
_ROUTE_PREFIX = re.compile(token_re("ROUTE", "").pattern, re.IGNORECASE)
_F_PREFIX = re.compile(token_re("F", "").pattern, re.IGNORECASE)
_PLACEHOLDER = re.compile(r"^\s*(—|-|\{.*\}|n/?a)?\s*$", re.IGNORECASE)
_BACKEND_ROUTES_HEAD = re.compile(r"#+\s*Backend Routes\b", re.IGNORECASE)

# "code" header, but not "codes used" (Artifact References table shares the word).
_CODE_HEADER = re.compile(r"\bcode\b")
_OWNER_HEADER = re.compile(r"\bowner\b")


def _prefix(code: str, pat: re.Pattern) -> str | None:
    m = pat.search(code or "")
    return m.group(0).upper() if m else None


def _all_backend_routes_tables(text: str) -> list[list[str]]:
    """Every contiguous pipe-table under `## Backend Routes`, one per `### File:`
    sub-heading (the template's normal shape — multiple tables, not one). Mirrors
    migrate-feature-api-ids.py's `_locate_backend_routes_tables` span logic. Each
    table is its own [header, sep, rows...] block.

    Fence-scoped (C1): scans only "prose" segments (`_id_schemes_lib.segment_text`)
    so a fenced example table under the heading is never mistaken for a real one.
    """
    prose = "".join(chunk for kind, chunk in segment_text(text or "") if kind == "prose")
    lines = prose.splitlines()
    start = next((i + 1 for i, ln in enumerate(lines) if _BACKEND_ROUTES_HEAD.match(ln.strip())), None)
    if start is None:
        return []
    tables: list[list[str]] = []
    i, n = start, len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith("## "):
            break
        if s.startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            tables.append(block)
        else:
            i += 1
    return tables


def backend_routes_table(text: str) -> list[str]:
    """Lines of route-list.md's FIRST Backend Routes sub-table, or [] (back-compat
    single-table accessor; multi-table callers use the functions above)."""
    tables = _all_backend_routes_tables(text)
    return tables[0] if tables else []


def route_columns(header: list[str]) -> tuple[int | None, int | None]:
    """Locate (code_idx, owner_idx) in a Backend Routes table header row."""
    code_idx = owner_idx = None
    for i, h in enumerate(header):
        hc = h.casefold()
        if code_idx is None and _CODE_HEADER.search(hc):
            code_idx = i
        elif owner_idx is None and _OWNER_HEADER.search(hc):
            owner_idx = i
    return code_idx, owner_idx


def cited_routes(text: str) -> set[str]:
    """ROUTE### tokens cited anywhere in text, scoped narrowly to avoid bleed from
    other rows' compound tokens (e.g. SCR###/REG###) in the same table."""
    return {m.group(0).upper() for m in _ROUTE_PREFIX.finditer(text or "")}


def artifact_ref_cited_routes(text: str) -> set[str]:
    """All ROUTE### codes cited in an Artifact References table's Codes Used column
    (technical-spec.md / behavior-logic.md share this table shape)."""
    table = _first_table_after(text, r"#+\s*Artifact References\b")
    if len(table) < 2:
        return set()
    header = [h.casefold() for h in _split_row(table[0])]
    codes_idx = next((i for i, h in enumerate(header) if "codes used" in h), None)
    if codes_idx is None:
        return set()
    cited: set[str] = set()
    for raw in data_rows(table):
        cells = _split_row(raw)
        if codes_idx < len(cells):
            cited |= cited_routes(cells[codes_idx])
    return cited


def build_route_inventory(text: str) -> set[str]:
    """ROUTE### codes named in route-list.md's Code column, unioned across every
    `### File:` sub-table. Scoped to the Code column specifically (not any
    ROUTE### substring in prose) to avoid false positives from a stray mention.
    """
    inv: set[str] = set()
    for table in _all_backend_routes_tables(text):
        if len(table) < 2:
            continue
        code_idx, _ = route_columns(_split_row(table[0]))
        if code_idx is None:
            continue
        for raw in data_rows(table):
            cells = _split_row(raw)
            if code_idx >= len(cells):
                continue
            pref = _prefix(cells[code_idx], _ROUTE_PREFIX)
            if pref:
                inv.add(pref)
    return inv


def iter_route_owner_rows(text: str) -> list[tuple[str, str]] | None:
    """(route_code_cell, owner_cell) per Backend Routes row, across every
    `### File:` sub-table with Code/Owner F### columns. None ONLY when NO
    sub-table has both (pure pre-migration); a half-migrated file yields rows
    from the migrated sub-tables only. route_code_cell is raw text — callers
    needing the bare code run it through `_prefix` themselves."""
    tables = _all_backend_routes_tables(text)
    if not tables:
        return []
    rows: list[tuple[str, str]] = []
    any_migrated = False
    for table in tables:
        if len(table) < 2:
            continue
        code_idx, owner_idx = route_columns(_split_row(table[0]))
        if code_idx is None or owner_idx is None:
            continue  # this sub-table is pre-migration; skip, don't fail the whole file
        any_migrated = True
        for raw in data_rows(table):
            cells = _split_row(raw)
            if max(code_idx, owner_idx) >= len(cells):
                continue
            rows.append((cells[code_idx], cells[owner_idx]))
    return rows if any_migrated else None


def build_route_owner_map_with_dups(root: Path) -> tuple[dict[str, set[str]], set[str]]:
    """{ROUTE### -> {F### owners}} (UNIONED, not last-wins) + the set of ROUTE###
    codes declared in >1 Backend Routes row (C4) — caller (validator) raises
    `link.route_duplicate` on the returned set. Never raises: ({}, set()) on any
    missing table/columns/file."""
    path = next((c for c in (root / "generated" / "route-list.md", root / "route-list.md")
                 if c.is_file()), None)
    if path is None:
        return {}, set()
    try:
        rows = iter_route_owner_rows(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return {}, set()
    if not rows:
        return {}, set()
    owner_map: dict[str, set[str]] = {}
    seen: set[str] = set()
    dups: set[str] = set()
    for route_cell, owner_cell in rows:
        route_code = _prefix(route_cell, _ROUTE_PREFIX)
        if route_code is None:
            continue
        (dups if route_code in seen else seen).add(route_code)
        owners = set() if _PLACEHOLDER.match(owner_cell) else {
            _prefix(tok, _F_PREFIX) for tok in re.split(r"[,/]", owner_cell) if _prefix(tok, _F_PREFIX)
        }
        owner_map.setdefault(route_code, set()).update(owners)
    return owner_map, dups


def build_route_owner_map(root: Path) -> dict[str, set[str]]:
    """Back-compat wrapper: owner map only, dups discarded (see *_with_dups)."""
    return build_route_owner_map_with_dups(root)[0]
