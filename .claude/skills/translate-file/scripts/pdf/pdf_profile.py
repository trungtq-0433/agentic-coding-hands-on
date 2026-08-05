#!/usr/bin/env python3
"""Profile a PDF file to produce config parameters for the in-place engine.

All signals are derived deterministically from PyMuPDF — no LLM calls.
Output: pdf_profile.json placed in the temp dir by convert.py.
"""
import pymupdf


def _detect_columns(page, blocks, page_w):
    """Estimate column count by clustering text-block x-center positions."""
    if not blocks or page_w <= 0:
        return 1
    x_centers = [((b["bbox"][0] + b["bbox"][2]) / 2) / page_w for b in blocks if b.get("type") == 0]
    if len(x_centers) < 4:
        return 1
    # Simple split at 0.45–0.55 midline: two clusters → 2 cols
    left = sum(1 for x in x_centers if x < 0.45)
    right = sum(1 for x in x_centers if x > 0.55)
    total = len(x_centers)
    if left > 0 and right > 0 and (left + right) / total > 0.6:
        return 2
    return 1


def _dominant_script(doc, sample_pages=5):
    """Sample text spans and guess script (latin / cjk / arabic / other)."""
    counts = {"latin": 0, "cjk": 0, "arabic": 0, "other": 0}
    sampled = 0
    for page in doc:
        if sampled >= sample_pages:
            break
        for block in page.get_textpage().extractDICT().get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for ch in span.get("text", "")[:50]:
                        cp = ord(ch)
                        if 0x0000 <= cp <= 0x024F:
                            counts["latin"] += 1
                        elif 0x4E00 <= cp <= 0x9FFF or 0x3040 <= cp <= 0x30FF:
                            counts["cjk"] += 1
                        elif 0x0600 <= cp <= 0x06FF:
                            counts["arabic"] += 1
                        else:
                            counts["other"] += 1
        sampled += 1
    return max(counts, key=counts.get)


def _has_translatable_images(doc, min_area=10000):
    """Check if any page has large raster images that might contain text."""
    for page in doc:
        for img in page.get_images(full=False):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                w = base.get("width", 0)
                h = base.get("height", 0)
                if w * h >= min_area:
                    return True
            except Exception:
                pass
    return False


def profile(pdf_path, user_overrides=None):
    """Profile a PDF and return a config dict.

    Args:
        pdf_path: path to the input PDF
        user_overrides: dict of user-supplied flags to merge over heuristics
            Supported keys: translate_img (bool), page_range (str "N-M" or None),
            font_choice (str)

    Returns dict matching pdf_profile.json schema:
        {
            "page_count": int,
            "scanned_pages": [int, ...],
            "columns_per_page": {"0": int, ...},
            "has_translatable_images": bool,
            "dominant_script": str,
            "translate_img": bool,
            "font_choice": str,
            "page_range": null | "N-M"
        }
    """
    doc = pymupdf.open(pdf_path)
    page_count = doc.page_count

    # Detect glyphless (scanned) pages
    scanned_pages = []
    for page in doc:
        for block in page.get_bboxlog():
            if block[0] == "ignore-text":
                scanned_pages.append(page.number)
                break

    # Column detection per page
    columns_per_page = {}
    for page in doc:
        page_dict = page.get_textpage().extractDICT()
        blocks = page_dict.get("blocks", [])
        columns_per_page[str(page.number)] = _detect_columns(page, blocks, page.rect.width)

    has_images = _has_translatable_images(doc)
    script = _dominant_script(doc)
    doc.close()

    result = {
        "page_count": page_count,
        "scanned_pages": scanned_pages,
        "columns_per_page": columns_per_page,
        "has_translatable_images": has_images,
        "dominant_script": script,
        "translate_img": False,
        "font_choice": "noto-sans",
        "page_range": None,
    }

    # Merge user overrides (CLI > heuristic)
    if user_overrides:
        for key in ("translate_img", "page_range", "font_choice"):
            if key in user_overrides and user_overrides[key] is not None:
                result[key] = user_overrides[key]

    return result
