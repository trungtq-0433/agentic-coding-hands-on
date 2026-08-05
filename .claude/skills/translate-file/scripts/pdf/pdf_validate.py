#!/usr/bin/env python3
"""Image-region integrity check for the PDF in-place rebuild.

Renders original vs translated pages at low DPI and compares image-region
bboxes to confirm images were not accidentally redacted or moved.
Augments pdf_validation.json with image_integrity findings.
"""
import json
import os

import pymupdf

_RENDER_DPI = 100
_CHANGE_THRESHOLD = 15.0  # mean absolute pixel difference to flag as changed


def _render_page(doc, page_idx, dpi=_RENDER_DPI):
    """Render a page to a numpy array (RGB)."""
    import numpy as np
    page = doc[page_idx]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return arr, mat


def _scale_bbox(bbox, mat):
    """Scale a PDF bbox to pixel coordinates using the render matrix."""
    x0, y0, x1, y1 = bbox
    r = pymupdf.Rect(x0, y0, x1, y1) * mat
    return (int(r.x0), int(r.y0), int(r.x1), int(r.y1))


def validate_image_regions(orig_path, out_path, structure, val_json_path):
    """Compare image-region bboxes between original and rebuilt PDF pages.

    Only checks pages reported in pdf_validation.json plus a random sample.
    Augments pdf_validation.json with an `image_integrity` field.

    Returns True if all checked image regions are unchanged; False otherwise.
    """
    try:
        import numpy as np
    except ImportError:
        print("numpy not available — skipping image-region diff")
        return True

    orig_doc = pymupdf.open(orig_path)
    out_doc = pymupdf.open(out_path)
    num_pages = min(orig_doc.page_count, out_doc.page_count)

    with open(val_json_path, encoding="utf-8") as f:
        val_data = json.load(f)

    # Determine pages to check: overflow pages + up to 3 sample pages
    overflow_pages = {int(p) for p, v in val_data.items() if v.get("overflow_ids")}
    sample_stride = max(1, num_pages // 3)
    sample_pages = {i for i in range(0, num_pages, sample_stride)}
    check_pages = overflow_pages | sample_pages

    # Collect image-bbox info from structure
    page_image_bboxes = {}
    for page in orig_doc:
        imgs = []
        for img_info in page.get_images(full=True):
            rects = page.get_image_rects(img_info[0])
            for rect in rects:
                imgs.append(list(rect))
        if imgs:
            page_image_bboxes[page.number] = imgs

    all_ok = True
    integrity_report = {}

    for page_idx in sorted(check_pages):
        if page_idx >= num_pages:
            continue
        if page_idx not in page_image_bboxes:
            integrity_report[str(page_idx)] = "no_images"
            continue

        orig_arr, mat = _render_page(orig_doc, page_idx)
        out_arr, _ = _render_page(out_doc, page_idx)

        if orig_arr.shape != out_arr.shape:
            integrity_report[str(page_idx)] = "shape_mismatch"
            all_ok = False
            continue

        page_ok = True
        for bbox in page_image_bboxes[page_idx]:
            px0, py0, px1, py1 = _scale_bbox(bbox, mat)
            px0, py0 = max(0, px0), max(0, py0)
            px1, py1 = min(orig_arr.shape[1], px1), min(orig_arr.shape[0], py1)
            if px1 <= px0 or py1 <= py0:
                continue
            orig_crop = orig_arr[py0:py1, px0:px1].astype(float)
            out_crop = out_arr[py0:py1, px0:px1].astype(float)
            mad = float(np.mean(np.abs(orig_crop - out_crop)))
            if mad > _CHANGE_THRESHOLD:
                page_ok = False
                all_ok = False
                break

        integrity_report[str(page_idx)] = "ok" if page_ok else "changed"

    orig_doc.close()
    out_doc.close()

    # Augment val_data
    for page_str, status in integrity_report.items():
        if page_str in val_data:
            val_data[page_str]["image_integrity"] = status
        else:
            val_data[page_str] = {"image_integrity": status}

    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)

    return all_ok
