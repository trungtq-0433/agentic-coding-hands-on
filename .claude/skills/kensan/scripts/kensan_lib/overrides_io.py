"""Load + atomically rewrite the per-user override file (`watchlist.local.md`).

Structured, manager-owned representation: the four override sections
(add / remove / mute / disable-preset). `dump` rewrites the whole file (a short
managed header is preserved; free-form comments are not — `manage` owns this file).
Stdlib only.
"""

import os
import tempfile

from . import watchlist

_HEADER = [
    "# My Kensan overrides",
    "# Managed by `/tkm:kensan manage` — these override the shipped presets; presets are never edited.",
    "",
]
_ADD_COLS = ["id", "name", "type", "handle", "topic", "weight"]


def load(path):
    """Return {add:[row...], remove:[id...], mute:[id...], disable_preset:[stem...]}."""
    path = os.path.expanduser(path) if path else ""
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            add, remove, mute, disabled = watchlist.parse_overrides(fh.read())
    else:
        add, remove, mute, disabled = [], set(), set(), set()
    return {"add": add, "remove": sorted(remove), "mute": sorted(mute),
            "disable_preset": sorted(disabled)}


def dump(path, data):
    """Rewrite the override file atomically from the structured `data`."""
    lines = list(_HEADER)
    if data["add"]:
        lines += ["## add",
                  "| id | name | type | handle/url | topic | weight |",
                  "|----|------|------|------------|-------|--------|"]
        for r in data["add"]:
            lines.append("| " + " | ".join(str(r.get(c, "")) for c in _ADD_COLS) + " |")
        lines.append("")
    for section, key in (("remove", "remove"), ("mute", "mute"), ("disable-preset", "disable_preset")):
        if data[key]:
            lines.append("## " + section)
            lines += ["- " + x for x in data[key]]
            lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    p = os.path.expanduser(path)
    dirpath = os.path.dirname(p) or "."
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, p)  # atomic on POSIX


def toggle(data, key, value, present):
    """Add/remove `value` from a bullet-list section (idempotent, sorted, deduped)."""
    items = [x for x in data[key] if x != value]
    if present:
        items.append(value)
    data[key] = sorted(set(items))


def add_or_update(data, row):
    """Insert or replace (by id) a row in the add section."""
    data["add"] = [r for r in data["add"] if r.get("id") != row["id"]] + [row]
    # a re-added source should not stay in the remove list
    toggle(data, "remove", row["id"], False)


def remove_id(data, source_id):
    add_ids = {r.get("id") for r in data["add"]}
    if source_id in add_ids:  # dropping a user-added source = delete its add row
        data["add"] = [r for r in data["add"] if r.get("id") != source_id]
    else:  # dropping a shipped-preset source = record it under remove
        _bullet(data, "remove", source_id, True)
