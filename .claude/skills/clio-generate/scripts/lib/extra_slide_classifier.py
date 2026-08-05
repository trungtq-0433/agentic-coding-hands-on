"""Heuristic classifier for markdown sections that don't match the known
ProjectProfile schema (`profile_parser._SECTION_MAP`).

Hand-written project_content_{id}.md files won't always use the ~13
canonical `## heading` names gen-md.py emits. Rather than silently dropping
unrecognized sections, `build_extra_slide_entry` shapes their content into
one of the generate-slide-style layouts in `extra_slide_layouts.py` so every
section lands somewhere in the deck.

Deliberately conservative: `comparison_2` and `numbered_points` are only
chosen when the content's natural shape already fits their hard render-time
caps (2 columns / 5 points — see `extra_slide_layouts.py`). Everything else
falls back to `bullets`, the one layout with no cap, so this classifier can
never re-introduce the silent-truncation problem it exists to avoid.

Pure/stateless: takes already-parsed pieces (subsections/table_rows/list_items
from `markdown_primitives`) rather than re-parsing raw markdown itself, so it
has no dependency on `profile_parser.py` (avoids a circular import).
"""
from __future__ import annotations

import re
from typing import Optional


def build_extra_slide_entry(
    heading: str,
    *,
    subsections: Optional[dict] = None,
    table_rows: Optional[list] = None,
    list_items: Optional[list] = None,
    raw_text: str = '',
) -> dict:
    """Pick a layout + shape content for one unrecognized `## heading` block.

    Returns a dict matching the extra-slide entry contract consumed by
    `renderer._render_extra_slides` (same shape as --extra-slides JSON):
    `layout`, `title`, layout-specific content key, `anchor_section`
    (filled in by the caller).
    """
    title = heading.strip()
    subsections = subsections or {}

    if len(subsections) == 2:
        return {
            'layout': 'comparison_2',
            'title': title,
            'columns': [
                {'title': sub_title, 'items': _to_bullet_lines(body)}
                for sub_title, body in subsections.items()
            ],
        }

    if 3 <= len(subsections) <= 5:
        return {
            'layout': 'numbered_points',
            'title': title,
            'points': [
                {'header': sub_title, 'body': _flatten(body)}
                for sub_title, body in subsections.items()
            ],
        }

    if table_rows:
        bullets = [' — '.join(str(v) for v in row.values() if v) for row in table_rows]
        return {'layout': 'bullets', 'title': title, 'bullets': bullets}

    if list_items:
        return {'layout': 'bullets', 'title': title, 'bullets': list_items}

    if subsections:
        # n == 1 or n >= 6: outside comparison_2/numbered_points' safe caps —
        # bullets never truncates, so flatten every subsection into one line
        # each instead of picking a capped layout that would drop the rest.
        bullets = [
            f'{sub_title}: {_flatten(body)}' if body.strip() else sub_title
            for sub_title, body in subsections.items()
        ]
        return {'layout': 'bullets', 'title': title, 'bullets': bullets}

    text = raw_text.strip()
    if text and len(text) <= 280 and '\n\n' not in text:
        return {'layout': 'hero', 'title': title, 'message': text}

    return {'layout': 'bullets', 'title': title, 'bullets': _to_bullet_lines(text) or [title]}


def _flatten(text: str) -> str:
    """Collapse a multi-line block to one line (safe for a single-run field)."""
    return ' '.join((text or '').split())


def _to_bullet_lines(text: str) -> list:
    """Split free text into separate items for bullet/column-item layouts."""
    if not text:
        return []
    items = [
        m.group(1).strip()
        for line in text.splitlines()
        if (m := re.match(r'^\s*(?:-|\*|\d+\.)\s+(.+)$', line))
    ]
    if items:
        return items
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) > 1:
        return [_flatten(p) for p in paragraphs]
    flat = _flatten(text)
    return [flat] if flat else []
