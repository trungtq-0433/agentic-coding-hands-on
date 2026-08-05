#!/usr/bin/env python3
"""Guard-railed escape hatch: re-run rebuild for overflow pages with fixed strategies.

Strategies (closed set — no arbitrary scripting):
  1. autofit  — shrink font-size step-wise (handled in pdf_inplace_build via autofit=True)
  2. bbox_grow — expand bbox into adjacent whitespace before re-inserting

Capped at MAX_PASSES remediation rounds. If still failing, page is kept as-is.
"""
import json
import os

MAX_PASSES = 2
_GROW_PX = 8  # pixels to expand bbox on each side for bbox_grow strategy


def _grow_bbox(bbox, page_w, page_h, grow_px=_GROW_PX):
    """Expand bbox into surrounding whitespace, clamped to page dimensions."""
    x0, y0, x1, y1 = bbox
    return [
        max(0.0, x0 - grow_px),
        max(0.0, y0 - grow_px),
        min(page_w, x1 + grow_px),
        min(page_h, y1 + grow_px),
    ]


def remediate(orig_pdf, translated_elements, structure, out_path, val_json_path, profile=None):
    """Attempt to fix overflow pages via a fixed strategy menu.

    Modifies out_path in-place (rebuilds overflow pages only).
    Updates val_json_path with post-remediation fit results.

    Args:
        orig_pdf: original source PDF path
        translated_elements: list of {id, translated_text}
        structure: structure dict from extract_elements
        out_path: current output.pdf (will be overwritten with fixes)
        val_json_path: path to pdf_validation.json (read + updated)
        profile: optional pdf_profile.json dict for page dimensions
    """
    try:
        from pdf_inplace_build import rebuild, FONTS_DIR, CSS_TEMPLATE
    except ImportError as e:
        print(f"pdf_remediate: build module unavailable: {e}")
        return

    with open(val_json_path, encoding="utf-8") as f:
        val_data = json.load(f)

    page_sizes = structure.get("page_sizes", [])

    for pass_num in range(1, MAX_PASSES + 1):
        overflow_pages = {
            int(p) for p, v in val_data.items()
            if isinstance(v.get("overflow_ids"), list) and len(v["overflow_ids"]) > 0
        }
        if not overflow_pages:
            print(f"pdf_remediate: no overflow pages — done after pass {pass_num - 1}")
            break

        print(f"pdf_remediate: pass {pass_num}/{MAX_PASSES} — {len(overflow_pages)} overflow pages")

        # Build a patched structure with grown bboxes for overflow elements
        patched_structure = dict(structure)
        for elem in translated_elements:
            elem_id = elem["id"]
            parts = elem_id.split("_")
            page_id = int(parts[1]) if parts[0] == "ocr" else int(parts[0])
            if page_id not in overflow_pages:
                continue
            info = structure.get(elem_id)
            if info is None:
                continue
            bbox = info.get("bbox")
            if bbox is None:
                continue
            pw = page_sizes[page_id][0] if page_id < len(page_sizes) else 9999
            ph = page_sizes[page_id][1] if page_id < len(page_sizes) else 9999
            patched_entry = dict(info)
            patched_entry["bbox"] = _grow_bbox(bbox, pw, ph)
            patched_structure[elem_id] = patched_entry

        # Re-run rebuild for the whole document with autofit + grown bboxes
        # (autofit=True enables the font-size shrink loop in _process_page)
        try:
            fit_results = rebuild(
                orig_pdf, translated_elements, patched_structure, out_path,
                autofit=True,
            )
        except Exception as e:
            print(f"pdf_remediate: rebuild failed on pass {pass_num}: {e}")
            break

        # Update validation data
        from merge_and_build import _build_pdf_validation
        new_val = _build_pdf_validation(fit_results, patched_structure)
        for page_str, data in new_val.items():
            val_data[page_str] = data
        with open(val_json_path, "w", encoding="utf-8") as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)

        remaining = sum(1 for v in val_data.values() if v.get("overflow_ids"))
        print(f"  After pass {pass_num}: {remaining} overflow pages remaining")
        if remaining == 0:
            break

    print("pdf_remediate: remediation complete")
