"""Parse watchlist markdown tables and merge user overrides.

Stdlib only. A watchlist file is any markdown with pipe tables; each row is one
source. Headers are matched case-insensitively, so column order is flexible.
The effective watchlist = presets (+) overrides (add / remove / mute).
"""

import glob
import os
import re

# Map flexible header spellings to canonical row keys.
_HEADER_ALIASES = {
    "id": "id",
    "name": "name",
    "type": "type",
    "handle": "handle",
    "url": "handle",
    "handle/url": "handle",
    "topic": "topic",
    "note": "note",
    "weight": "weight",       # 1-5 priority/credibility prior (default 3)
    "freshness": "freshness",  # green|yellow|white — how often it posts new knowledge
}

DEFAULT_WEIGHT = 3


def source_weight(row):
    """Parse a row's weight to an int in 1..5, defaulting to DEFAULT_WEIGHT."""
    try:
        return max(1, min(5, int(str(row.get("weight", DEFAULT_WEIGHT)).strip())))
    except (ValueError, TypeError):
        return DEFAULT_WEIGHT


def _split_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def _is_separator(line):
    return bool(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line)) and "-" in line


def parse_markdown_tables(text):
    """Yield row dicts (keyed by canonical headers) for every pipe table found."""
    rows = []
    headers = None
    for line in text.splitlines():
        if "|" not in line:
            headers = None
            continue
        if _is_separator(line):
            continue
        cells = _split_row(line)
        if headers is None:
            headers = [_HEADER_ALIASES.get(h.strip().lower()) for h in cells]
            continue
        row = {}
        for key, val in zip(headers, cells):
            if key and val:
                row[key] = val
        if row.get("id") and row.get("type"):
            rows.append(row)
    return rows


def load_presets(presets_dir):
    """Load every `*.md` preset (skipping README) into a list of source rows."""
    rows = []
    for path in sorted(glob.glob(os.path.join(presets_dir, "*.md"))):
        if os.path.basename(path).lower() == "readme.md":
            continue
        with open(path, encoding="utf-8") as fh:
            file_rows = parse_markdown_tables(fh.read())
        preset_stem = os.path.splitext(os.path.basename(path))[0]
        for row in file_rows:
            row.setdefault("topic", preset_stem)
            row["_preset"] = preset_stem  # source file stem, for --only matching
            rows.append(row)
    return rows


def _parse_bullet_ids(section_text):
    ids = set()
    for line in section_text.splitlines():
        m = re.match(r"^\s*[-*]\s+(\S+)", line)
        if m:
            ids.add(m.group(1).strip())
    return ids


def parse_overrides(text):
    """Return (add_rows, remove_ids, mute_ids, disabled_presets) from a
    watchlist.local.md body. Sections: add | remove | mute | disable-preset."""
    sections = {"add": "", "remove": "", "mute": "", "disable-preset": ""}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(add|remove|mute|disable-preset)\s*$", line.strip(), re.IGNORECASE)
        if m:
            current = m.group(1).lower()
            continue
        if line.startswith("## ") or line.startswith("# "):
            current = None
        if current:
            sections[current] += line + "\n"
    add_rows = parse_markdown_tables(sections["add"])
    return (add_rows, _parse_bullet_ids(sections["remove"]), _parse_bullet_ids(sections["mute"]),
            _parse_bullet_ids(sections["disable-preset"]))


def effective_watchlist(presets_dir, overrides_path=None, only_topic=None):
    """Compute the merged watchlist.

    Returns (rows, muted_ids). `rows` excludes removed sources and sources from
    disabled presets; muted sources stay in `rows` but their ids are in
    `muted_ids` so the caller skips collecting them.
    """
    by_id = {r["id"]: r for r in load_presets(presets_dir)}
    removed, muted, disabled = set(), set(), set()
    if overrides_path and os.path.exists(overrides_path):
        with open(overrides_path, encoding="utf-8") as fh:
            add_rows, removed, muted, disabled = parse_overrides(fh.read())
        for row in add_rows:
            row.setdefault("topic", "custom")
            by_id[row["id"]] = row  # override wins on id collision
    rows = [r for rid, r in by_id.items()
            if rid not in removed and r.get("_preset") not in disabled]
    if only_topic:
        rows = [r for r in rows
                if only_topic in (r.get("topic", ""), r.get("_preset", ""))]
    return rows, muted
