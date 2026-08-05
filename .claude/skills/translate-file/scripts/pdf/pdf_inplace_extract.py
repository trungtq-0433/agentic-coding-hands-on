#!/usr/bin/env python3
"""Extract text elements and structure from a PDF for in-place translation."""
import pymupdf


def _glyphless_pages(doc):
    """Return page indices that contain glyphless (scanned/image-only) text."""
    pages = []
    for page in doc:
        for block in page.get_bboxlog():
            if block[0] == "ignore-text":
                pages.append(page.number)
                break
    return pages


def _span_from_dict(span_dict):
    """Parse a raw span dict from extractDICT into a portable dict.

    Exact field derivation from PDFSpan.from_dict in the reference POC.
    """
    return {
        "text": span_dict["text"],
        "font_size": int(span_dict["size"] - 1),
        "bold": bool(span_dict["flags"] & 2**4),
        "italic": bool(span_dict["flags"] & 2**1),
        "font_color": span_dict["color"],
    }


def extract_elements(pdf_path, profile=None):
    """Extract text elements and per-element structure from a PDF.

    Args:
        pdf_path: path to the input PDF
        profile: optional pdf_profile.json dict for column-aware ordering

    Returns:
        elements: ordered list of {id, text, spans}
            - id is "{page_idx}_{line_idx}" (0-based)
            - text is the concatenated line text
            - spans carry font_size/bold/italic/font_color for re-insertion
        structure: dict with:
            - per-element "{id}": {bbox, dir, spans}
            - "page_sizes": [[w, h], ...] per page
            - "glyphless_pages": [page_idx, ...] for scanned pages
    """
    doc = pymupdf.open(pdf_path)
    glyphless = _glyphless_pages(doc)
    page_sizes = [[page.rect.width, page.rect.height] for page in doc]

    elements = []
    structure = {"glyphless_pages": glyphless, "page_sizes": page_sizes}

    columns_per_page = {}
    if profile:
        for k, v in profile.get("columns_per_page", {}).items():
            columns_per_page[int(k)] = v

    for page_id, page in enumerate(doc):
        if page_id in glyphless:
            continue

        page_dict = page.get_textpage().extractDICT()
        blocks = [b for b in page_dict.get("blocks", []) if b.get("type") == 0]

        # Column-aware ordering: sort text blocks by column then y position
        num_cols = columns_per_page.get(page_id, 1)
        if num_cols >= 2 and blocks:
            page_w = page.rect.width or 1.0
            col_w = page_w / num_cols
            blocks = sorted(
                blocks,
                key=lambda b: (int(((b["bbox"][0] + b["bbox"][2]) / 2) / col_w), b["bbox"][1]),
            )

        line_id = 0
        for block in blocks:
            for line in block.get("lines", []):
                raw_spans = line.get("spans", [])
                spans = [_span_from_dict(s) for s in raw_spans if s.get("text", "").strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans)
                if not text.strip():
                    continue
                elem_id = f"{page_id}_{line_id}"
                elements.append({"id": elem_id, "text": text, "spans": spans})
                structure[elem_id] = {
                    "bbox": list(line["bbox"]),
                    "dir": list(line["dir"]),
                    "spans": spans,
                }
                line_id += 1

    doc.close()
    return elements, structure
