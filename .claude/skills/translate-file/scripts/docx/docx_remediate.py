#!/usr/bin/env python3
"""
docx_remediate.py - Fixed-strategy remediation for failing DOCX elements.

Consumes docx_validation.json and applies a closed set of deterministic fixes:
  - marker_leak  → strip control markers from the translation text, rebuild element
  - run_mismatch → re-build element with single-run fallback (dominant format, no split)
  - missing_pn   → element left as-is (would need a re-translation sub-call; logged)
  - residue      → element left as-is (same reason; logged)

Capped at ≤ 2 passes. Re-validates after each pass.
"""

import json
import os
import re
import sys


_MARKER_STRIP_RE = re.compile(r'\[P:\d+\]\s*|⟦s\d+⟧|⟦/s\d+⟧|\*{1,3}')


def _strip_markers(text):
    """Remove leaked control markers from a translation string."""
    return _MARKER_STRIP_RE.sub('', text).strip()


def _load_validation(temp_dir):
    path = os.path.join(temp_dir, "docx_validation.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_translations(temp_dir):
    """Return mutable {elem_idx: translated_text} from output.md."""
    output_md = os.path.join(temp_dir, "output.md")
    if not os.path.exists(output_md):
        return {}
    translations = {}
    with open(output_md, "r", encoding="utf-8") as f:
        content = f.read()
    for line in content.splitlines():
        stripped = line.strip().lstrip("|").rstrip("|")
        for seg in stripped.split("¶"):
            seg = seg.strip()
            m = re.match(r'^\[P:(\d+)\]\s*(.*)', seg)
            if m:
                translations[int(m.group(1))] = m.group(2).strip()
    return translations


def _save_translations(temp_dir, translations):
    """Write a patched output.md with corrected translations (marker-stripped)."""
    output_md = os.path.join(temp_dir, "output.md")
    if not os.path.exists(output_md):
        return
    with open(output_md, "r", encoding="utf-8") as f:
        lines = f.readlines()

    patched = []
    for line in lines:
        stripped = line.strip().lstrip("|").rstrip("|")
        changed = False
        new_segs = []
        for seg in stripped.split("¶"):
            seg_s = seg.strip()
            m = re.match(r'^(\[P:(\d+)\])\s*(.*)', seg_s)
            if m:
                idx = int(m.group(2))
                if idx in translations:
                    new_segs.append(f"{m.group(1)} {translations[idx]}")
                    changed = True
                    continue
            new_segs.append(seg_s)
        if changed:
            # Reconstruct line preserving table-cell pipe wrapping if present
            inner = " ¶ ".join(new_segs)
            if line.strip().startswith("|"):
                patched.append(f"| {inner} |\n")
            else:
                patched.append(inner + "\n")
        else:
            patched.append(line)

    with open(output_md, "w", encoding="utf-8") as f:
        f.writelines(patched)


def remediate(temp_dir, output_docx, source_docx, elem_index):
    """Apply deterministic remediations (≤2 passes). Returns final validation dict."""
    # Lazy imports to avoid circular dependencies
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from docx_validate import validate

    build_docx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_docx.py")
    try:
        import build_docx as _bd
    except ImportError:
        print("docx_remediate: build_docx not importable — skipping remediation")
        return _load_validation(temp_dir)

    for pass_num in range(1, 3):
        val = _load_validation(temp_dir)
        if val is None or val.get("ok") or val.get("skipped"):
            break

        marker_leak_ids = {r["id"] for r in val.get("marker_leak", [])}
        run_mismatch_ids = set(val.get("run_mismatch", []))
        fixable = marker_leak_ids | run_mismatch_ids

        if not fixable:
            break  # Only missing_pn / residue remain — needs re-translation, not handled here

        translations = _load_translations(temp_dir)
        patched_any = False

        # Fix 1: Strip leaked markers from translation text
        for idx in marker_leak_ids:
            if idx in translations:
                cleaned = _strip_markers(translations[idx])
                if cleaned != translations[idx]:
                    translations[idx] = cleaned
                    patched_any = True

        if patched_any:
            _save_translations(temp_dir, translations)

        # Fix 2: Rebuild elements with run_mismatch using single-run fallback
        if run_mismatch_ids:
            from docx import Document
            from docx.oxml.ns import qn
            from docx.text.paragraph import Paragraph as DocxParagraph
            from docx.table import Table as DocxTable

            doc = Document(source_docx)
            elem_idx_counter = 0

            def _apply_single_run(para_obj, idx):
                meta = elem_index.get(idx, {})
                text = translations.get(idx, "")
                if text:
                    _bd.set_para_text(para_obj, text, meta, single_run_fallback=True)

            for child in doc.element.body:
                local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if local == "p":
                    if elem_idx_counter in run_mismatch_ids:
                        _apply_single_run(DocxParagraph(child, doc), elem_idx_counter)
                    elem_idx_counter += 1
                elif local == "tbl":
                    tbl = DocxTable(child, doc)
                    seen = set()
                    for row in tbl.rows:
                        for cell in row.cells:
                            tc_id = id(cell._tc)
                            dup = tc_id in seen
                            if not dup:
                                seen.add(tc_id)
                            for p in cell.paragraphs:
                                if not dup and elem_idx_counter in run_mismatch_ids:
                                    _apply_single_run(p, elem_idx_counter)
                                elem_idx_counter += 1

            doc.save(output_docx)
            # Re-apply container write-back after rebuild
            try:
                from docx_containers import write_back_containers
                write_back_containers(output_docx, elem_index, translations)
            except ImportError:
                pass

        # Re-validate
        val = validate(temp_dir, output_docx)
        print(f"Remediation pass {pass_num}: {'OK' if val.get('ok') else 'issues remain'}")
        if val.get("ok"):
            break

    # Report unresolved elements
    val = _load_validation(temp_dir) or {}
    unresolved = (val.get("missing_pn", []) + [r["id"] for r in val.get("residue", [])])
    if unresolved:
        print(f"Unresolved after remediation (needs re-translation): {unresolved[:10]}")
    return val
