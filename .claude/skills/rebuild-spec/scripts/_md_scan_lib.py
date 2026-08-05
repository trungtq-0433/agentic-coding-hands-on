#!/usr/bin/env python3
"""Shared fence/comment/escape-aware markdown scanning primitives.

Root cause (PR #176 max-review): C1, I1 (x2: fence + HTML-comment), I3 (escaped-pipe), and
2 minor findings (disclaimer spurious rows, B4 `data_rows()`) are all the same missing
primitive — a fence/comment/escape-aware scanner duplicated (or absent) across
`validate_reading_guide_db_impact.py`, `validate_job_list.py`, `validate_test_cases.py`,
`derive_confidence_report.py`, and `validate_design_intent_density.py`. This module is the
single, unit-tested primitive all five converge on. See
`plans/260708-0847-pr176-review-fixes/phase-01-md-scan-lib.md`.

Pure, stdlib-only, best-effort — never raises on malformed input.
"""
from __future__ import annotations

import re
from collections.abc import Iterator

_FENCE_RE = re.compile(r"^(```|~~~)")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_DISCLAIMER_RE = re.compile(
    r"<!--\s*disclaimer:start\s*-->.*?<!--\s*disclaimer:end\s*-->",
    re.IGNORECASE | re.DOTALL,
)
# Sentinel used to protect an escaped `\|` while splitting on bare `|`. NUL bytes never
# occur in real markdown, so this round-trips safely.
_ESCAPED_PIPE = "\x00ESC_PIPE\x00"


def iter_lines_with_fence(text: str) -> Iterator[tuple[int, str, bool]]:
    """Yield `(1-based lineno, line, in_fence)` for every line of `text`.

    Tracks BOTH ``` and ~~~ fences. A fence opened with one marker only closes on that
    SAME marker — a `~~~` block containing a stray ``` line never closes early. Both the
    opening and the closing delimiter lines are themselves reported with `in_fence=True`
    (matching the skip-the-delimiter-line convention every prior fence-aware scanner in
    this skill already used).
    """
    in_fence = False
    marker: str | None = None
    for lineno, line in enumerate(text.splitlines(), 1):
        m = _FENCE_RE.match(line.lstrip())
        if m:
            this_marker = m.group(1)
            if not in_fence:
                in_fence = True
                marker = this_marker
                yield lineno, line, True
                continue
            if this_marker == marker:
                yield lineno, line, True
                in_fence = False
                marker = None
                continue
        yield lineno, line, in_fence


def strip_comments(text: str) -> str:
    """Blank `<!-- ... -->` HTML comments (DOTALL), preserving the line count.

    A multi-line comment is replaced by its own newlines rather than the empty string,
    so line numbers computed on the stripped text still map to the original document —
    callers (`validate_job_list._parse_h2_sections`) report `line_start` diagnostics.
    """
    return _COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def strip_disclaimer_blocks(text: str) -> str:
    """Remove every `<!-- disclaimer:start -->...<!-- disclaimer:end -->` span.

    Case-insensitive on the marker tokens. An unterminated `disclaimer:start` (no matching
    `disclaimer:end`) is left untouched — best-effort, never raises.
    """
    return _DISCLAIMER_RE.sub("", text)


def mask_fenced(text: str) -> str:
    """Return `text` with every fenced line (incl. its delimiters) blanked to `""`.

    Line count is preserved 1:1 with `text.splitlines()`, so downstream line-indexed or
    line-anchored regex work (e.g. `_first_table_after`) sees the same offsets, just with
    fenced content invisible.
    """
    return "\n".join("" if in_fence else line
                     for _, line, in_fence in iter_lines_with_fence(text))


def split_table_row(row: str) -> list[str]:
    r"""Split a markdown table row into trimmed cells, unescaping `\|` -> `|`.

    Parity with `_nav_table_parse_lib._split_row` (outer-pipe/empty drop), except an
    escaped `\|` is protected before splitting and restored after, so a cell like
    `{INSERT\|UPDATE\|DELETE}` survives as ONE cell instead of being shredded into three.
    """
    protected = row.replace("\\|", _ESCAPED_PIPE)
    cells = [c.strip() for c in protected.strip().strip("|").split("|")]
    return [c.replace(_ESCAPED_PIPE, "|") for c in cells]
