#!/usr/bin/env python3
"""
docx_validate.py - Structural validation for a translated DOCX.

Checks (no LibreOffice required):
  1. Coverage   — every source [P:N] with non-empty text has a translation.
  2. Residue    — translated text identical to source (untranslated element).
  3. Marker leak — literal ** / * / [P:N] / ⟦sN⟧ surviving into translations.
  4. Run sanity — multi-format paragraphs still have segment markers (if expected).

Produces docx_validation.json and prints a one-line summary.
"""

import json
import os
import re

_LEAKED_MARKERS = [
    (re.compile(r'\[P:\d+\]'), '[P:N]'),
    (re.compile(r'⟦s\d+⟧|⟦/s\d+⟧'), '⟦sN⟧'),
    (re.compile(r'\*\*\*|\*\*(?!\*)\*\*|\*(?!\*)'), '**'),
]


def _source_text_from_meta(meta):
    """Reconstruct plain source text from runs metadata."""
    return "".join(r.get("text", "") for r in meta.get("runs", []))


def validate(temp_dir, output_docx=None):
    """Validate the translated DOCX output.

    Reads docx_structure.json + output.md from temp_dir.
    Writes docx_validation.json and returns the validation dict.
    """
    struct_path = os.path.join(temp_dir, "docx_structure.json")
    output_md_path = os.path.join(temp_dir, "output.md")

    if not os.path.exists(struct_path) or not os.path.exists(output_md_path):
        return {"ok": True, "skipped": True}

    with open(struct_path, "r", encoding="utf-8") as f:
        structure = json.load(f)
    with open(output_md_path, "r", encoding="utf-8") as f:
        output_text = f.read()

    # Build flat element index: elem_idx -> meta
    elem_index = {}
    for elem in structure.get("elements", []):
        etype = elem.get("type")
        if etype in ("paragraph", "cell_paragraph", "hf_paragraph",
                     "footnote_paragraph", "endnote_paragraph",
                     "textbox_paragraph", "comment_paragraph"):
            elem_index[elem["elem_idx"]] = elem
        elif etype == "table":
            for cell in elem.get("cells", []):
                for para in cell.get("paragraphs", []):
                    elem_index[para["elem_idx"]] = para

    # Parse translations from output.md
    translations = {}
    for line in output_text.splitlines():
        stripped = line.strip().lstrip("|").rstrip("|")
        for seg in stripped.split("¶"):
            seg = seg.strip()
            m = re.match(r'^\[P:(\d+)\]\s*(.*)', seg)
            if m:
                translations[int(m.group(1))] = m.group(2).strip()

    result = {
        "missing_pn": [],
        "residue": [],
        "marker_leak": [],
        "run_mismatch": [],
        "ok": True,
    }

    for idx, meta in elem_index.items():
        source_text = _source_text_from_meta(meta).strip()
        if not source_text:
            continue  # skip empty source elements

        translated = translations.get(idx)

        # 1. Coverage
        if translated is None or not translated.strip():
            result["missing_pn"].append(idx)
            result["ok"] = False
            continue

        # 2. Residue — translated == source (byte-identical, strong signal)
        if translated.strip() == source_text:
            result["residue"].append({"id": idx, "sample": source_text[:80]})
            result["ok"] = False

        # 3. Marker leak
        for pattern, marker_name in _LEAKED_MARKERS:
            if pattern.search(translated):
                result["marker_leak"].append({"id": idx, "marker": marker_name})
                result["ok"] = False
                break

        # 4. Run sanity — expected segment markers missing
        if meta.get("segment_metas"):
            if not re.search(r'⟦s\d+⟧', translated):
                result["run_mismatch"].append(idx)
                # Not a hard failure — remediation will apply single-run fallback

    total = len(elem_index)
    n_miss = len(result["missing_pn"])
    n_res = len(result["residue"])
    n_leak = len(result["marker_leak"])
    n_mis = len(result["run_mismatch"])

    # Summarise
    parts = []
    if n_miss:
        parts.append(f"missing:{','.join(str(i) for i in result['missing_pn'][:5])}")
    if n_res:
        parts.append(f"residue:{','.join(str(r['id']) for r in result['residue'][:5])}")
    if n_leak:
        parts.append(f"marker-leak:{','.join(str(r['id']) for r in result['marker_leak'][:5])}")
    if n_mis:
        parts.append(f"run-mismatch:{','.join(str(i) for i in result['run_mismatch'][:5])}")
    summary = f"Validation: {total} elements • " + (" • ".join(parts) if parts else "OK")
    print(summary)

    val_path = os.path.join(temp_dir, "docx_validation.json")
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
