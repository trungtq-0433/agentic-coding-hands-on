"""Stateless markdown content primitives shared by `profile_parser.py` and
`extra_slide_classifier.py`.

Kept dependency-free (no imports from either module) so both can import from
here without a circular import.
"""
from __future__ import annotations

import re


def split_subsections(content: str) -> dict[str, str]:
    """Split section content by `^### ` headings. Returns {heading_text: content}."""
    parts: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in content.splitlines():
        m = re.match(r'^###\s+(.+?)\s*$', line)
        if m:
            if current is not None:
                parts[current] = '\n'.join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None:
        parts[current] = '\n'.join(buf).strip()
    return parts


def parse_table(content: str) -> list[dict]:
    """Parse a markdown pipe table into a list of dicts (keys = header row)."""
    lines = [l.strip() for l in content.splitlines() if l.strip().startswith('|')]
    if len(lines) < 2:
        return []

    def split_row(line: str) -> list[str]:
        cells = [c.strip() for c in line.split('|')]
        # Strip empty leading/trailing cells from outer pipes
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]
        return cells

    header = split_row(lines[0])
    rows = []
    for line in lines[1:]:
        # Skip separator |---|---|
        if all(c in '|-: \t' for c in line):
            continue
        cells = split_row(line)
        if not cells:
            continue
        row = {header[i] if i < len(header) else f'col{i}': cells[i] for i in range(len(cells))}
        rows.append(row)
    return rows


def parse_list(content: str) -> list[str]:
    """Parse bulleted (`- item`) or numbered (`1. item`) list. Other lines ignored."""
    items: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        m = re.match(r'^(?:-|\*|\d+\.)\s+(.+)$', s)
        if m:
            items.append(m.group(1).strip())
    return items


def parse_image_ref(content: str) -> str:
    """Extract path from `Image: path` line. Returns empty string if not found."""
    m = re.search(r'^Image:\s*(.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else ''


def parse_text(content: str) -> str:
    """Strip and return text content (multi-line preserved)."""
    return content.strip()
