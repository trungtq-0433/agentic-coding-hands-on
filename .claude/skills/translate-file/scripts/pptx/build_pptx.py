#!/usr/bin/env python3
"""
build_pptx.py — Reconstruct translated PPTX from pptx_mapped.json.

Strategy: re-walk slides in the same order as extract_pptx.py; for each
paragraph that has a mapping, clear existing runs and reconstruct from
mapped_components (preserving per-run bold/italic/color/size/font).
Paragraphs without a mapping are left untouched.

Usage:
    python3 build_pptx.py <temp_dir>
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_runs import apply_components_to_paragraph


def _read_config(temp_dir):
    config = {}
    config_path = os.path.join(temp_dir, "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, _, v = line.partition("=")
                    config[k.strip()] = v.strip()
    return config


def _walk_and_replace(shapes, slide_idx, shape_counter, mapped):
    """Recursively walk shapes, replacing paragraph runs where mapped."""
    try:
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        MSO_SHAPE_TYPE = None

    for shape in shapes:
        if MSO_SHAPE_TYPE and shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            _walk_and_replace(shape.shapes, slide_idx, shape_counter, mapped)
            continue

        shape_idx = shape_counter[0]
        shape_counter[0] += 1

        if shape.has_text_frame:
            for p_idx, para in enumerate(shape.text_frame.paragraphs):
                eid = f"PPTX:{slide_idx}:{shape_idx}:{p_idx}"
                if eid in mapped:
                    apply_components_to_paragraph(para, mapped[eid])

        if shape.has_table:
            for r_idx, row in enumerate(shape.table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for p_idx, para in enumerate(cell.text_frame.paragraphs):
                        eid = f"PPTX:{slide_idx}:{shape_idx}:T:{r_idx}:{c_idx}:{p_idx}"
                        if eid in mapped:
                            apply_components_to_paragraph(para, mapped[eid])


def build_pptx(temp_dir):
    from pptx import Presentation

    config = _read_config(temp_dir)
    input_file = config.get("input_file", "")
    if not input_file or not os.path.exists(input_file):
        print(f"Error: original PPTX not found (config says: '{input_file}')")
        return False

    mapped_path = os.path.join(temp_dir, "pptx_mapped.json")
    if not os.path.exists(mapped_path):
        print(f"Error: pptx_mapped.json not found in {temp_dir} — run pptx_mapping.py finalize first")
        return False

    with open(mapped_path, encoding="utf-8") as f:
        mapped_data = json.load(f)
    mapped: dict = mapped_data.get("mapped", {})

    if not mapped:
        print("Warning: no mapped elements found in pptx_mapped.json")

    prs = Presentation(input_file)
    for s_idx, slide in enumerate(prs.slides):
        shape_counter = [0]
        _walk_and_replace(slide.shapes, s_idx, shape_counter, mapped)

        # Speaker notes
        if slide.has_notes_slide:
            notes_tf = slide.notes_slide.notes_text_frame
            for p_idx, para in enumerate(notes_tf.paragraphs):
                eid = f"PPTX:{s_idx}:notes:{p_idx}"
                if eid in mapped:
                    apply_components_to_paragraph(para, mapped[eid])

    output_path = os.path.join(temp_dir, "output.pptx")
    prs.save(output_path)
    flagged = mapped_data.get("flagged_fallback", [])
    print(
        f"PPTX output: {output_path} ({os.path.getsize(output_path):,} bytes)"
        + (f" — {len(flagged)} fallback run(s)" if flagged else "")
    )
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct translated PPTX from pptx_mapped.json")
    parser.add_argument("temp_dir")
    args = parser.parse_args()
    sys.exit(0 if build_pptx(args.temp_dir) else 1)
