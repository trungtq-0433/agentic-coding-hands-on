"""Causal why-read-here clause helpers for the aggregate reading-order table.

C-cheap:  static clauses authored once per locale in strings["aggregate_why"].
C-faithful: researcher-authored 1-line overrides written to .nav-why.json in the
            system/ directory.  Renderer prefers the grounded line; falls back to
            the static clause; omits the entry when neither is present.

Stdlib only.
"""
from __future__ import annotations

import json
import os

from _nav_strings import AGGREGATE_SYSTEM_ORDER, AGGREGATE_WHY_KEYS
from _system_synthesis_lib import sanitize_field


def load_json_file(path: str) -> object:
    """Load a JSON file; return None on any error (missing file, bad JSON, OS error)."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def build_why_clauses(system_dir: str, strings: dict) -> dict[str, str]:
    """Build filename→clause map for the reading-order table (C-cheap + C-faithful).

    Preference: if .nav-why.json carries why_read[fname], use that (researcher-authored,
    C-faithful).  Otherwise fall back to strings["aggregate_why"][why_key] (static).
    Researcher-authored lines are sanitized via sanitize_field at load time.
    Absent key in either source → entry omitted (graceful degradation).

    .nav-why.json schema: a flat JSON object mapping filename to a 1-line string:
        {"overview.md": "...", "architecture.md": "..."}
    Back-compat: absent file, non-dict content, or empty value → silent skip.
    """
    ag_why = strings.get("aggregate_why", {})
    # C-faithful: researcher-authored .nav-why.json side-channel.
    why_json = load_json_file(os.path.join(system_dir, ".nav-why.json"))
    grounded: dict[str, str] = {}
    if isinstance(why_json, dict):
        for fname, line in why_json.items():
            if isinstance(line, str) and line.strip():
                grounded[fname] = sanitize_field(line.strip())
    clauses: dict[str, str] = {}
    for fname in AGGREGATE_SYSTEM_ORDER:
        if fname in grounded:
            clauses[fname] = grounded[fname]
        else:
            why_key = AGGREGATE_WHY_KEYS.get(fname)
            if why_key and why_key in ag_why:
                clauses[fname] = ag_why[why_key]
    return clauses
