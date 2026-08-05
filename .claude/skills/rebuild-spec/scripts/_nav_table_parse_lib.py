"""Tolerant markdown-table parsers for the feature/screen reading guide (A4/B).

Pure, stdlib-only, best-effort — never raise on malformed input (return [] / {}).
Split out of _nav_feature_lib to keep each module under the 200-LOC invariant.

  - parse_screen_names()  — Screen-List table of a feature's screens.md (column-aware)
  - index_screen_list()   — name → SCR### code map from generated/screen-list.md
  - norm_name()           — shared name normalization for matching
  - data_rows()           — header/separator-aware data-row slice (reviewer C5 fix)
"""
from __future__ import annotations

import re

# Matches the SCR### prefix of a code, with or without a `_NameSlug` tail. A trailing
# \b would FAIL on "SCR001_LoginForm" because "_" is a word char (no boundary after the
# digits), so we anchor only on the leading boundary.
_SCR_RE = re.compile(r"\bSCR\d{3}")

# Matches a markdown table separator row (`|---|:---:|`) — pipes/colons/dashes/space
# only. A real data row (e.g. `| GET | /x |`) never matches this shape.
_SEP_ROW = re.compile(r"^[\s|:\-]+$")


def data_rows(table: list[str]) -> list[str]:
    """Rows after the header, tolerant of a missing `|---|` separator (reviewer C5).

    `table` is `[header, ...]` as returned by `_first_table_after`/the Backend
    Routes span scanners. If row 1 has the separator's shape, it is skipped
    (`table[2:]`); otherwise row 1 is a real data row that a naive positional
    `table[2:]` slice would silently drop — keep it (`table[1:]`).
    """
    if len(table) < 2:
        return []
    return table[2:] if _SEP_ROW.match(table[1] or "") else table[1:]


def norm_name(name: str) -> str:
    """Normalize a screen name for matching: strip, collapse spaces, casefold."""
    return re.sub(r"\s+", " ", name or "").strip().casefold()


def _first_table_after(text: str, heading_re: str) -> list[str]:
    """Return the lines of the first markdown table after a heading, or []."""
    lines = text.splitlines()
    start = None
    pat = re.compile(heading_re, re.IGNORECASE)
    for i, ln in enumerate(lines):
        if pat.match(ln.strip()):
            start = i + 1
            break
    if start is None:
        return []
    table: list[str] = []
    seen_row = False
    for ln in lines[start:]:
        stripped = ln.strip()
        if stripped.startswith("|"):
            table.append(stripped)
            seen_row = True
        elif seen_row:
            break  # table ended
    return table


def _split_row(row: str) -> list[str]:
    """Split a markdown table row into trimmed cells (drops outer empties)."""
    return [c.strip() for c in row.strip().strip("|").split("|")]


def parse_screen_names(screens_md: str) -> list[dict]:
    """Parse the Screen List table of a feature's screens.md (column-aware).

    Returns a list of {"name": str, "scr": str|None}. Column-aware: if the table
    carries an SCR### column (Phase B), its value is read directly; otherwise scr
    is None and the caller resolves by name. Tolerant — a background-only feature
    ("N/A — background feature", no table) or an unparseable table yields [].
    """
    table = _first_table_after(screens_md, r"#+\s*Screen List\b")
    if len(table) < 2:
        return []
    header = [h.casefold() for h in _split_row(table[0])]
    # locate the screen-name column (prefer an explicit "screen name"/"screen" header)
    name_idx = 0
    for i, h in enumerate(header):
        if "screen" in h and "scr" not in h.replace("screen", ""):
            name_idx = i
            break
    # locate an optional SCR### column (Phase B). "scr" must be followed by a boundary,
    # "#", or a digit — so "Screen Name" (scr+"e") is never mistaken for the SCR column.
    scr_idx = None
    for i, h in enumerate(header):
        if i != name_idx and re.search(r"\bscr(\b|#|\d)", h):
            scr_idx = i
            break
    rows: list[dict] = []
    for raw in table[2:]:  # skip header + separator
        cells = _split_row(raw)
        if not cells or name_idx >= len(cells):
            continue
        name = cells[name_idx]
        if not name or name.startswith("{"):  # template placeholder row
            continue
        scr = None
        if scr_idx is not None and scr_idx < len(cells):
            scr_cell = cells[scr_idx].strip()
            scr = scr_cell if (scr_cell and scr_cell != "—") else None
        rows.append({"name": name, "scr": scr})
    return rows


def index_screen_list(screen_list_md: str) -> dict[str, str]:
    """Build {normalized name → SCR### code} from generated/screen-list.md.

    Parses the Screen Index table (Code | Name | ...). The Code column carries the
    canonical `SCR###_NameSlug`. First match wins on duplicate names. Returns {}
    when the table is absent or unparseable (best-effort).
    """
    table = _first_table_after(screen_list_md, r"#+\s*Screen Index\b")
    if len(table) < 2:
        return {}
    header = [h.casefold() for h in _split_row(table[0])]
    code_idx = next((i for i, h in enumerate(header) if "code" in h), 0)
    name_idx = next((i for i, h in enumerate(header) if "name" in h), 1)
    out: dict[str, str] = {}
    for raw in table[2:]:
        cells = _split_row(raw)
        if max(code_idx, name_idx) >= len(cells):
            continue
        code = cells[code_idx].strip()
        name = cells[name_idx].strip()
        if not code or not name or code.startswith("{") or not _SCR_RE.search(code):
            continue
        key = norm_name(name)
        if key not in out:  # first match wins
            out[key] = code
    return out
