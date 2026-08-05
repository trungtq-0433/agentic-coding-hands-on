#!/usr/bin/env python3
"""Scan feature technical-specs for entity-kind SM-### state machines.

Used by validate_process_flow.py (B3 — SM/FLOW DRY cross-ref enforcement).
A FLOW### that re-documents an entity state machine already captured as an
SM-### in a feature spec MUST cross-reference it instead of duplicating the
transition table. This module surfaces the candidate SMs for that check.

Note: headings are matched over the full file text without skipping fenced code
blocks. A `### SM-###` line inside a mermaid/code fence could be picked up, but it
is harmless unless that block also carries a `**kind:** entity` line (filtered out
otherwise). Kept simple deliberately — feeds a warning-only check.

Stdlib only.
"""
from __future__ import annotations

import re
from pathlib import Path

# Matches "### SM-001_Name" or "#### SM-001_Name" heading lines.
_SM_HEADING_RE = re.compile(r"^#{3,4}\s+(SM-\d{3})[^\n]*", re.MULTILINE)
_KIND_RE = re.compile(r"\*\*kind:\*\*\s*(\w+)", re.IGNORECASE)
_STATES_RE = re.compile(r"\*\*States:\*\*\s*(.+)")


def _parse_states(block: str) -> set[str]:
    m = _STATES_RE.search(block)
    if not m:
        return set()
    states: set[str] = set()
    for tok in re.split(r"[,→]", m.group(1)):
        s = tok.strip().strip("`").strip()
        if s:
            states.add(s)
    return states


def scan_entity_state_machines(features_dir: Path) -> list[dict]:
    """Return entity-kind SMs as [{code, feature, states:set[str]}].

    Only SMs with `**kind:** entity` and >=2 declared states are returned —
    UI/polling SMs are irrelevant to the FLOW### DRY boundary.
    """
    results: list[dict] = []
    if not features_dir.is_dir():
        return results
    for tspec in sorted(features_dir.glob("*/technical-spec.md")):
        text = tspec.read_text(encoding="utf-8", errors="replace")
        feature = tspec.parent.name
        headings = list(_SM_HEADING_RE.finditer(text))
        for i, h in enumerate(headings):
            block_start = h.end()
            block_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            block = text[block_start:block_end]
            kind_m = _KIND_RE.search(block)
            if not kind_m or kind_m.group(1).strip().lower() != "entity":
                continue
            states = _parse_states(block)
            if len(states) >= 2:
                results.append({"code": h.group(1), "feature": feature, "states": states})
    return results
