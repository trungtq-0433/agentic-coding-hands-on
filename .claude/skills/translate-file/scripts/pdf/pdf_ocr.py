#!/usr/bin/env python3
"""OCR for scanned PDF pages using a Claude vision sub-agent.

Only triggered for pages listed in pdf_profile.json["scanned_pages"] or
when translate_img=True. Digital PDFs skip this entirely.

Flow per scanned page:
  render page → vision sub-agent returns [{text, bbox}] lines
  → convert polygon bbox → rect bbox
  → get background/text color
  → build ocr_elements (disjoint id namespace: "ocr_{page}_{line}")
  → route through the normal translate → rebuild path with type='ocr'
"""
import os
import json
import base64
import tempfile

import pymupdf

_OCR_RENDER_DPI = 150
_OCR_ID_PREFIX = "ocr"


def _get_rect_bbox(polygon_bbox):
    """Convert 4-corner polygon bbox to (x0, y0, x1, y1) rect."""
    xs = [pt[0] for pt in polygon_bbox]
    ys = [pt[1] for pt in polygon_bbox]
    return (min(xs), min(ys), max(xs), max(ys))


def _get_background_and_text_color(image_bytes, bbox_px, page_w_px, page_h_px):
    """Sample background and foreground color from a cropped image region."""
    try:
        from PIL import Image
        import io
        import numpy as np
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        x0, y0, x1, y1 = bbox_px
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(img.width, int(x1)), min(img.height, int(y1))
        if x1 <= x0 or y1 <= y0:
            return (255, 255, 255), (0, 0, 0)
        crop = np.array(img.crop((x0, y0, x1, y1)), dtype=float)
        # Dominant color = background (KMeans if available, else mean)
        try:
            from sklearn.cluster import KMeans
            flat = crop.reshape(-1, 3)
            km = KMeans(n_clusters=2, n_init=3, random_state=0).fit(flat)
            centers = km.cluster_centers_
            labels = km.labels_
            counts = [sum(1 for l in labels if l == i) for i in range(2)]
            bg_idx = counts.index(max(counts))
            fg_idx = 1 - bg_idx
            bg = tuple(int(v) for v in centers[bg_idx])
            fg = tuple(int(v) for v in centers[fg_idx])
        except ImportError:
            mean = crop.mean(axis=(0, 1))
            bg = tuple(int(v) for v in mean)
            # Invert for text color approximation
            fg = tuple(255 - v for v in bg)
        return bg, fg
    except Exception:
        return (255, 255, 255), (0, 0, 0)


def _render_page_to_bytes(doc, page_idx, dpi=_OCR_RENDER_DPI):
    """Render a page and return PNG bytes + pixel dimensions."""
    page = doc[page_idx]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    return pix.tobytes("png"), pix.width, pix.height, mat


def _call_vision_ocr(png_bytes, source_lang="auto"):
    """Call a Claude vision sub-agent to OCR a page image.

    Returns list of {text, bbox} where bbox is [[x,y], [x,y], [x,y], [x,y]].
    Uses the Anthropic API directly since this runs in the skill's subprocess context.
    """
    import anthropic
    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(png_bytes).decode()
    lang_hint = f"Source language: {source_lang}. " if source_lang and source_lang != "auto" else ""
    prompt = (
        f"{lang_hint}Extract all text from this PDF page image. "
        "Return a JSON array where each element is: "
        '{"text": "...", "bbox": [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]}. '
        "bbox is a 4-corner polygon in pixel coordinates (origin top-left). "
        "One entry per text line. Return ONLY the JSON array, no explanation."
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    raw = msg.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def extract_ocr_elements(pdf_path, scanned_pages, source_lang="auto"):
    """Extract text elements from scanned pages via vision sub-agent OCR.

    Args:
        pdf_path: path to the original PDF
        scanned_pages: list of page indices to OCR
        source_lang: source language hint for the OCR prompt

    Returns:
        elements: list of {id, text, spans} with "ocr_{page}_{line}" ids
        structure: {elem_id: {bbox, dir, spans, ocr_attrs}} for rebuild
    """
    doc = pymupdf.open(pdf_path)
    elements = []
    structure = {}

    for page_idx in scanned_pages:
        if page_idx >= doc.page_count:
            continue
        try:
            png_bytes, pw_px, ph_px, mat = _render_page_to_bytes(doc, page_idx)
            ocr_lines = _call_vision_ocr(png_bytes, source_lang)
        except Exception as e:
            print(f"OCR failed for page {page_idx}: {e}")
            continue

        # Scale factor from pixel to PDF points
        scale_x = doc[page_idx].rect.width / pw_px if pw_px else 1.0
        scale_y = doc[page_idx].rect.height / ph_px if ph_px else 1.0

        for line_idx, line_info in enumerate(ocr_lines):
            text = line_info.get("text", "").strip()
            if not text:
                continue
            poly_bbox = line_info.get("bbox", [])
            if not poly_bbox:
                continue
            rect_bbox_px = _get_rect_bbox(poly_bbox)
            # Convert pixel bbox to PDF points
            bbox = [
                rect_bbox_px[0] * scale_x,
                rect_bbox_px[1] * scale_y,
                rect_bbox_px[2] * scale_x,
                rect_bbox_px[3] * scale_y,
            ]
            # Sample background/text color
            bg, fg = _get_background_and_text_color(png_bytes, rect_bbox_px, pw_px, ph_px)
            elem_id = f"{_OCR_ID_PREFIX}_{page_idx}_{line_idx}"
            spans = [{"text": text, "font_size": 10, "bold": False, "italic": False, "font_color": 0}]
            elements.append({"id": elem_id, "text": text, "spans": spans})
            structure[elem_id] = {
                "bbox": bbox,
                "dir": [1.0, 0.0],
                "spans": spans,
                "ocr_attrs": {"background_color": bg, "text_color": fg},
            }

    doc.close()
    return elements, structure
