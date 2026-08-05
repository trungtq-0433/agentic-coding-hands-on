#!/usr/bin/env python3
"""COBOL screen-router dispatch helpers (Phase 01 foundation).

Macro-shaped anchored-regex sniffing used by `extract_cobol_screen.py` to route a source
file to the BMS lib, the SCREEN SECTION lib, both, or neither — NEVER a naive substring
check (a SCREEN-SECTION file with `DFHMDI` only in a comment must not misroute to BMS).

Also carries the post-decode EBCDIC/binary sanity guard: [Red-team fix 4] a mis-decoded or
binary file must warn, never silently report zero screens.

Stdlib only.
"""
from __future__ import annotations

import re

_SANITY_SCAN_LINES = 200

# Anchored macro-shaped dispatch: a label column (possibly empty) then whitespace then the
# macro name — the operand-column shape real BMS source uses. Comment lines are excluded
# BEFORE this check runs (see is_comment_line).
_BMS_MACRO_RE = re.compile(r"^\s*\S*\s+(DFHMSD|DFHMDI|DFHMDF)(?=\s|,|$)")
_SCREEN_SECTION_RE = re.compile(r"\bSCREEN\s+SECTION\b", re.IGNORECASE)
_EXEC_CICS_MAP_RE = re.compile(r"EXEC\s+CICS\s+(SEND|RECEIVE)\s+MAP\b", re.IGNORECASE)
# [H3 fix] Fixed-format COBOL: cols 1-6 are the sequence-number area (blank or a
# 4-6 digit sequence number, right-padded with spaces), col 7 is the indicator
# (`*`/`/` = comment). Anchoring on any 6 leading characters -- not `^\s*` -- so a
# seq-numbered comment like `000300*  ...` is still recognized; `^\s*\*` missed it
# because digits are not `\s`, letting the comment bleed into live parsing.
_COMMENT_LINE_RE = re.compile(r"^.{6}[*/]")
_SANITY_TOKENS = ("IDENTIFICATION DIVISION", "PROCEDURE DIVISION", "DFHMSD")


def is_comment_line(line: str) -> bool:
    """COBOL comment convention: col-7 indicator is `*` or `/` (tolerates a leading
    4-6 digit sequence-number prefix in cols 1-6, blank or digits)."""
    return bool(_COMMENT_LINE_RE.match(line))


def matches_bms_macro(lines: list[str]) -> bool:
    """True if any non-comment line is an anchored DFHMSD/DFHMDI/DFHMDF macro line."""
    return any(_BMS_MACRO_RE.match(line) for line in lines if not is_comment_line(line))


def matches_screen_section(lines: list[str]) -> bool:
    """True if any non-comment line declares `SCREEN SECTION`."""
    return any(_SCREEN_SECTION_RE.search(line) for line in lines if not is_comment_line(line))


def matches_exec_cics_map(lines: list[str]) -> bool:
    """True if any non-comment line issues `EXEC CICS SEND/RECEIVE MAP` -- a calling program
    that references a BMS map without containing its own macro definitions (the normal
    real-world split between a map deck and the programs that use it) must still reach
    `BmsLib` so its EXEC CICS citation joins against the map at `finalize()`; without this,
    such a file matches neither `matches_bms_macro` nor `matches_screen_section` and the
    router would skip it, silently starving the reachability join of its only evidence."""
    return any(_EXEC_CICS_MAP_RE.search(line) for line in lines if not is_comment_line(line))


def looks_like_cobol(lines: list[str]) -> bool:
    """Post-decode EBCDIC/binary sanity guard: any mandatory token in the first N lines."""
    sample = "\n".join(lines[:_SANITY_SCAN_LINES]).upper()
    return any(tok in sample for tok in _SANITY_TOKENS)
