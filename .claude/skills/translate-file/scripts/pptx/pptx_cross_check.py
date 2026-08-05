#!/usr/bin/env python3
"""pptx_cross_check.py - Structural cross-check of source vs translated PPTX.

Checks (no LibreOffice required):
  1. Opens OK      — output.pptx is a valid zip and opens in python-pptx.
  2. Slide parity  — same slide count in source and output.
  3. Coverage      — every extracted element id has a mapping in pptx_mapped.json.
  4. Residue       — output paragraph text identical to source and contains CJK
                     (untranslated leftover).
  5. Concat        — concat(mapped_components.text) == translated_general_text.

Writes pptx_crosscheck.json and returns the report dict.
"""
from __future__ import annotations

import json
import os
import re
import zipfile

_CJK_RE = re.compile(r"[　-鿿豈-﫿＀-￯぀-ヿㇰ-ㇿ]")
_MIN_RESIDUE_LEN = 3


def _has_cjk(text: str) -> bool:
    matches = _CJK_RE.findall(text)
    return len("".join(matches)) >= _MIN_RESIDUE_LEN


def _zip_opens(path: str) -> bool:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            # A valid PPTX must have ppt/presentation.xml
            zf.read("ppt/presentation.xml")
        return True
    except Exception:
        return False


def _slide_count(pptx_path: str) -> int | None:
    """Return slide count or None on error."""
    try:
        from pptx import Presentation
        return len(Presentation(pptx_path).slides)
    except Exception:
        return None


def _extract_para_texts(pptx_path: str) -> dict[str, str]:
    """Re-extract paragraph texts keyed by element id (same order as extract_pptx)."""
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        return {}

    result: dict[str, str] = {}

    def _para_text(para):
        return "".join(r.text for r in para.runs)

    def _walk(shapes, s_idx, counter):
        for shape in shapes:
            try:
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    _walk(shape.shapes, s_idx, counter)
                    continue
            except Exception:
                pass
            sh_idx = counter[0]
            counter[0] += 1
            if shape.has_text_frame:
                for p_idx, para in enumerate(shape.text_frame.paragraphs):
                    text = _para_text(para).strip()
                    if text:
                        result[f"PPTX:{s_idx}:{sh_idx}:{p_idx}"] = text
            if shape.has_table:
                for r_idx, row in enumerate(shape.table.rows):
                    for c_idx, cell in enumerate(row.cells):
                        for p_idx, para in enumerate(cell.text_frame.paragraphs):
                            text = _para_text(para).strip()
                            if text:
                                result[f"PPTX:{s_idx}:{sh_idx}:T:{r_idx}:{c_idx}:{p_idx}"] = text

    try:
        prs = Presentation(pptx_path)
        for s_idx, slide in enumerate(prs.slides):
            counter = [0]
            _walk(slide.shapes, s_idx, counter)
            if slide.has_notes_slide:
                notes_tf = slide.notes_slide.notes_text_frame
                for p_idx, para in enumerate(notes_tf.paragraphs):
                    text = "".join(r.text for r in para.runs).strip()
                    if text:
                        result[f"PPTX:{s_idx}:notes:{p_idx}"] = text
    except Exception as e:
        print(f"Warning: could not re-extract {pptx_path}: {e}")

    return result


def check(temp_dir: str, source_pptx: str, output_pptx: str) -> dict:
    """Run cross-check. Returns report dict and writes pptx_crosscheck.json."""

    struct_path = os.path.join(temp_dir, "pptx_structure.json")
    mapped_path = os.path.join(temp_dir, "pptx_mapped.json")

    structure: dict = {}
    mapped_data: dict = {}

    if os.path.exists(struct_path):
        with open(struct_path, encoding="utf-8") as f:
            structure = json.load(f)
    if os.path.exists(mapped_path):
        with open(mapped_path, encoding="utf-8") as f:
            mapped_data = json.load(f)

    elements = structure.get("elements", [])
    mapped_by_id: dict = mapped_data.get("mapped", {})
    n_elements = len(elements)

    # 1. Opens OK
    opens_ok = _zip_opens(output_pptx)

    # 2. Slide parity
    src_slides = _slide_count(source_pptx)
    out_slides = _slide_count(output_pptx) if opens_ok else None
    slide_parity_ok = src_slides is not None and src_slides == out_slides

    # 3. Coverage
    all_ids = {e["id"] for e in elements}
    missing_map = sorted(all_ids - set(mapped_by_id.keys()))

    # 4. Residue — re-extract output and compare
    source_texts = {e["id"]: e.get("general_text", "") for e in elements}
    output_texts = _extract_para_texts(output_pptx) if opens_ok else {}

    residue = []
    for eid, src_text in source_texts.items():
        if not src_text.strip():
            continue
        out_text = output_texts.get(eid, "")
        if out_text == src_text and _has_cjk(src_text):
            residue.append({"id": eid, "src": src_text[:120], "out": out_text[:120]})

    # 5. Concat integrity
    concat_broken = []
    for eid, comps in mapped_by_id.items():
        if not isinstance(comps, list):
            continue
        concat = "".join(c.get("text", "") for c in comps)
        out_text = output_texts.get(eid, "")
        if out_text and concat != out_text and concat.strip() != out_text.strip():
            concat_broken.append(eid)

    ok = (
        opens_ok
        and slide_parity_ok
        and len(missing_map) == 0
        and len(residue) == 0
        and len(concat_broken) == 0
    )

    report = {
        "elements": n_elements,
        "missing_map": missing_map,
        "residue": residue,
        "concat_broken": concat_broken,
        "slide_parity_ok": slide_parity_ok,
        "opens_ok": opens_ok,
        "ok": ok,
    }

    crosscheck_path = os.path.join(temp_dir, "pptx_crosscheck.json")
    with open(crosscheck_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report
