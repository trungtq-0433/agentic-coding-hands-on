"""Reusable helpers for parsing BR/SM/ALG/INT sub-blocks in feature spec files.

Heading pattern: ### {BR|SM|ALG|INT}-NNN_NameSlug
Stdlib only. O(n) single pass.
"""
from __future__ import annotations
import re

BLOCK_HEADING_RE = re.compile(r"^### (BR|SM|ALG|INT)-(\d{3}_\w+)")
LINKED_FR_RE = re.compile(r"^\*\*Linked FR:\*\*")


def find_blocks(text: str) -> list[dict]:
    """Return a list of dicts for every BR/SM/ALG/INT block heading.

    Each dict has:
        heading_line  int   0-based line index of the heading
        heading_text  str   full heading line text
        prefix        str   BR | SM | ALG | INT
        code          str   e.g. "BR-001_OrderMinItems"
        block_end     int   line index of the next ### heading, or len(lines)

    Headings inside fenced code blocks (``` or ~~~) are skipped.
    """
    lines = text.splitlines()
    total = len(lines)
    found: list[dict] = []
    in_fence = False
    fence_char = ""

    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_char = stripped[:3]
                continue
        else:
            if stripped.startswith(fence_char):
                in_fence = False
            continue

        m = BLOCK_HEADING_RE.match(ln)
        if m:
            prefix = m.group(1)
            rest = m.group(2)          # e.g. "001_OrderMinItems"
            code = f"{prefix}-{rest}"  # e.g. "BR-001_OrderMinItems"
            found.append({
                "heading_line": i,
                "heading_text": ln,
                "prefix": prefix,
                "code": code,
                "block_end": total,    # filled in next pass
            })

    # fill block_end: each block ends where the next ### heading starts
    for k in range(len(found) - 1):
        found[k]["block_end"] = found[k + 1]["heading_line"]

    return found


def has_linked_fr(text: str, heading_line: int, block_end: int) -> bool:
    """Return True if **Linked FR:** appears between heading_line and block_end."""
    lines = text.splitlines()
    for i in range(heading_line + 1, min(block_end, len(lines))):
        if LINKED_FR_RE.match(lines[i]):
            return True
    return False


def find_blocks_missing_linked_fr(text: str) -> list[dict]:
    """Return only blocks that are missing a **Linked FR:** line."""
    blocks = find_blocks(text)
    return [b for b in blocks if not has_linked_fr(text, b["heading_line"], b["block_end"])]
