"""Engine 2 — parse the promoted `user-stories.md` into structs for conformance checking.

Parses THREE structures the artifact declares itself (see `user-stories-template.md`):
  1. the **Interaction Inventory** table  — `Screen | Element | Type | Action | Endpoint`
  2. the **Screen → US Map**              — `Screen | US Codes`
  3. every **US title**                    — `## US###...: <title>` headers

Deterministic, stdlib-only. No fabrication: a row with a blank Endpoint / a missing table is
reported as absent, never guessed (the caller degrades it to UNVERIFIABLE).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_US_HEADER_RE = re.compile(r"^##\s+(US\d{3,4}[A-Za-z0-9_]*)\s*:\s*(.+?)\s*$")
_US_CODE_RE = re.compile(r"US\d{3,4}")


@dataclass
class Interaction:
    screen: str
    element: str
    itype: str        # primary-action | secondary-action | destructive-action | navigation | system-action
    action: str
    endpoint: str     # route-view: HTTP endpoint; dfm-form: event-handler proc; may be "" / "N/A"


@dataclass
class ParsedUserStories:
    interactions: list[Interaction] = field(default_factory=list)
    screen_to_us: dict[str, list[str]] = field(default_factory=dict)
    us_titles: dict[str, str] = field(default_factory=dict)
    has_inventory: bool = False
    has_screen_map: bool = False


def _is_separator(cells: list[str]) -> bool:
    return all(set(c) <= set("-: ") and c for c in cells) if cells else False


def _is_placeholder(cells: list[str]) -> bool:
    """Template rows carry {TOKEN} placeholders — skip them."""
    return any("{" in c and "}" in c for c in cells)


def _split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def _iter_table_rows(lines: list[str], start_idx: int) -> list[list[str]]:
    """Collect data rows of the first markdown table after start_idx until the section ends."""
    rows: list[list[str]] = []
    seen_table = False
    for line in lines[start_idx:]:
        s = line.strip()
        if s.startswith("## "):
            break
        if s.startswith("|"):
            seen_table = True
            cells = _split_row(line)
            if _is_separator(cells):
                continue
            rows.append(cells)
        elif seen_table and not s:
            continue
        elif seen_table and not s.startswith("|"):
            # table ended (non-blank, non-pipe line after the table)
            break
    return rows


def _find_section(lines: list[str], *titles: str) -> int | None:
    """Return the line index just after a section header matching any of `titles` (case/space/arrow tolerant)."""
    norm_targets = [re.sub(r"[\s>→-]+", "", t.lower()) for t in titles]
    for i, line in enumerate(lines):
        if line.strip().startswith("## "):
            norm = re.sub(r"[\s>→-]+", "", line.strip()[3:].lower())
            if norm in norm_targets:
                return i + 1
    return None


def parse(text: str) -> ParsedUserStories:
    lines = text.splitlines()
    result = ParsedUserStories()

    # 1) Interaction Inventory
    inv_idx = _find_section(lines, "Interaction Inventory")
    if inv_idx is not None:
        rows = _iter_table_rows(lines, inv_idx)
        for cells in rows:
            if _is_placeholder(cells) or len(cells) < 5:
                continue
            # Skip the header row (column names).
            if cells[0].lower() == "screen" and cells[1].lower() == "element":
                continue
            result.has_inventory = True
            result.interactions.append(Interaction(
                screen=cells[0], element=cells[1], itype=cells[2].lower(),
                action=cells[3], endpoint=cells[4]))

    # 2) Screen → US Map
    map_idx = _find_section(lines, "Screen → US Map", "Screen -> US Map", "Screen US Map")
    if map_idx is not None:
        rows = _iter_table_rows(lines, map_idx)
        for cells in rows:
            if _is_placeholder(cells) or len(cells) < 2:
                continue
            if cells[0].lower() == "screen" and "us" in cells[1].lower():
                continue
            us_codes = _US_CODE_RE.findall(cells[1])
            if cells[0]:
                result.has_screen_map = True
                result.screen_to_us[cells[0]] = us_codes

    # 3) US titles
    for line in lines:
        m = _US_HEADER_RE.match(line)
        if m:
            result.us_titles[m.group(1)] = m.group(2)

    return result
