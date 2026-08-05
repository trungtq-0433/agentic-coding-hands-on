"""Markdown spec parsing helpers — heading/fence detection + HTML comment scrubber.

Used by Wave 6.5 validators. Stdlib only.
Single pass per line, O(n) over total characters.
"""
from __future__ import annotations


def parse_headings_and_blocks(lines: list[str]):
    """Return (headings, blocks).

    headings: list of (line_index, full_line) for lines starting with `#` outside fences.
    blocks: list of (start_line, end_line, lang) for ``` fenced regions.
    """
    in_fence = False
    fs = -1
    flang = ""
    headings: list[tuple[int, str]] = []
    blocks: list[tuple[int, int, str]] = []
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            if not in_fence:
                in_fence, fs, flang = True, i, ln[3:].strip()
            else:
                blocks.append((fs, i, flang))
                in_fence = False
            continue
        if not in_fence and ln.startswith("#"):
            headings.append((i, ln.rstrip()))
    return headings, blocks


def strip_html_comments(lines: list[str]) -> list[str]:
    """Return lines with HTML comment content removed, preserving line count.

    Walks each line char-by-char tracking multi-line `in_comment` state.
    Content between `-->` and the next `<!--` on the same line is preserved,
    closing the placeholder-evasion gap of net-depth line-level masks.
    """
    out: list[str] = []
    in_comment = False
    for ln in lines:
        parts: list[str] = []
        i = 0
        while i < len(ln):
            if in_comment:
                end = ln.find("-->", i)
                if end < 0:
                    i = len(ln)
                else:
                    i = end + 3
                    in_comment = False
            else:
                start = ln.find("<!--", i)
                if start < 0:
                    parts.append(ln[i:])
                    break
                parts.append(ln[i:start])
                i = start + 4
                in_comment = True
        out.append("".join(parts))
    return out
