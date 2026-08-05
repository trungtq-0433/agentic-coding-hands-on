"""docx_cross_check.py - Structural cross-check of source vs translated DOCX.

Checks (no LibreOffice required):
  1. Part parity  — same zip entries in source and output.
  2. Opens OK     — output zip is valid and document XML parses.
  3. Coverage     — every extracted element id has a mapping in docx_mapped.json.
  4. Residue      — output element text identical to source (untranslated leftover).
  5. Concat       — concat(mapped_components.text) == translated_general_text.

Writes docx_crosscheck.json and returns the report dict.
"""
from __future__ import annotations

import json
import os
import re
import zipfile

# Unicode ranges for CJK / Japanese scripts (source-language residue detection)
_CJK_RE = re.compile(
    r"[　-鿿豈-﫿＀-￯぀-ヿㇰ-ㇿ]"
)
_MIN_RESIDUE_LEN = 3  # ignore single-char CJK (may be legit in target)


def _has_cjk(text: str) -> bool:
    matches = _CJK_RE.findall(text)
    return len("".join(matches)) >= _MIN_RESIDUE_LEN


def _zip_opens(path: str) -> bool:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.read("word/document.xml")
        return True
    except Exception:
        return False


def _extract_texts(docx_path: str) -> dict[str, str]:
    """Re-extract general_text per element id from a DOCX (for residue check).

    Uses the same engine as extraction so text is comparable.
    """
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from docx_extract_engine import extract
        elements, _ = extract(docx_path)
        return {e.id: e.general_text for e in elements}
    except Exception as e:
        print(f"Warning: could not re-extract {docx_path}: {e}")
        return {}


def check(temp_dir: str, source_docx: str, output_docx: str) -> dict:
    """Run cross-check. Returns report dict and writes docx_crosscheck.json."""

    struct_path = os.path.join(temp_dir, "docx_structure.json")
    mapped_path = os.path.join(temp_dir, "docx_mapped.json")

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

    # 1. Part parity
    part_parity_ok = True
    try:
        with zipfile.ZipFile(source_docx, "r") as src_zip:
            src_parts = set(src_zip.namelist())
        with zipfile.ZipFile(output_docx, "r") as out_zip:
            out_parts = set(out_zip.namelist())
        part_parity_ok = src_parts == out_parts
    except Exception:
        part_parity_ok = False

    # 2. Opens OK
    opens_ok = _zip_opens(output_docx)

    # 3. Coverage — every element id has a mapping
    all_ids = {e["id"] for e in elements}
    missing_map = sorted(all_ids - set(mapped_by_id.keys()))

    # 4. Residue — re-extract output and compare per element
    source_texts = {e["id"]: e.get("general_text", "") for e in elements}
    output_texts = _extract_texts(output_docx)

    residue = []
    for eid, src_text in source_texts.items():
        if not src_text.strip():
            continue
        out_text = output_texts.get(eid, "")
        # Mark as residue if output == source AND source has CJK content
        if out_text == src_text and _has_cjk(src_text):
            residue.append({"id": eid, "src": src_text[:120], "out": out_text[:120]})

    # 5. Concat integrity — mapped_components concat == translated_general_text
    concat_broken = []
    for eid, comps in mapped_by_id.items():
        if not isinstance(comps, list):
            continue
        concat = "".join(c.get("text", "") for c in comps)
        # Get expected translated text from output_texts (best proxy we have)
        out_text = output_texts.get(eid, "")
        if out_text and concat != out_text and concat.strip() != out_text.strip():
            concat_broken.append(eid)

    ok = (
        part_parity_ok
        and opens_ok
        and len(missing_map) == 0
        and len(residue) == 0
        and len(concat_broken) == 0
    )

    report = {
        "elements": n_elements,
        "missing_map": missing_map,
        "residue": residue,
        "concat_broken": concat_broken,
        "part_parity_ok": part_parity_ok,
        "opens_ok": opens_ok,
        "ok": ok,
    }

    crosscheck_path = os.path.join(temp_dir, "docx_crosscheck.json")
    with open(crosscheck_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report
