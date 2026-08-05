#!/usr/bin/env python3
"""
extract_pptx.py — Extract translatable text from PPTX into [PPTX:S:SH:P] chunks.

Markers:
  [PPTX:S:SH:P]           — slide S, shape SH, paragraph P (text frame)
  [PPTX:S:SH:T:R:C:P]     — slide S, shape SH, table row R col C paragraph P
  [PPTX:S:notes:P]         — slide S, speaker notes paragraph P

All indices are 0-based. Masters and layouts are skipped.

Usage:
    python3 extract_pptx.py <input.pptx> <temp_dir> [--chunk-size N]
"""
import os
import sys
import json
import argparse

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PPTX_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, _PPTX_DIR)

from manifest import create_manifest
from pptx_runs import extract_run_attrs


def _para_text(para):
    return "".join(r.text for r in para.runs)


def _add_element(elements: list, marker_id: str, text: str, para) -> None:
    """Append a flat element entry with per-run components."""
    components = [extract_run_attrs(r) for r in para.runs]
    elements.append({
        "id": marker_id,
        "general_text": text,
        "components": components,
    })


def _walk_shapes(shapes, slide_idx, shape_counter, shape_list, chunk_lines, elements):
    """Recursively walk shapes, handling group shapes."""
    try:
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        MSO_SHAPE_TYPE = None

    for shape in shapes:
        # Recurse into group shapes
        if MSO_SHAPE_TYPE and shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            _walk_shapes(shape.shapes, slide_idx, shape_counter, shape_list, chunk_lines, elements)
            continue

        shape_idx = shape_counter[0]
        shape_counter[0] += 1

        shape_entry = {
            "shape_index": shape_idx,
            "shape_name": shape.name,
            "shape_type": "other",
        }

        if shape.has_text_frame:
            paras_text = []
            for p_idx, para in enumerate(shape.text_frame.paragraphs):
                text = _para_text(para).strip()
                paras_text.append(text)
                if text:
                    marker_id = f"PPTX:{slide_idx}:{shape_idx}:{p_idx}"
                    chunk_lines.append(f"[{marker_id}] {text}")
                    _add_element(elements, marker_id, text, para)
            shape_entry["shape_type"] = "text"
            shape_entry["paragraphs"] = paras_text

        if shape.has_table:
            table_data = []
            for r_idx, row in enumerate(shape.table.rows):
                row_data = []
                for c_idx, cell in enumerate(row.cells):
                    cell_paras = []
                    for p_idx, para in enumerate(cell.text_frame.paragraphs):
                        text = _para_text(para).strip()
                        cell_paras.append(text)
                        if text:
                            marker_id = f"PPTX:{slide_idx}:{shape_idx}:T:{r_idx}:{c_idx}:{p_idx}"
                            chunk_lines.append(f"[{marker_id}] {text}")
                            _add_element(elements, marker_id, text, para)
                    row_data.append({"paragraphs": cell_paras})
                table_data.append(row_data)
            shape_entry["shape_type"] = "table"
            shape_entry["table"] = table_data

        shape_list.append(shape_entry)


def extract_pptx_to_chunks(input_file, temp_dir, chunk_size=6000):
    from pptx import Presentation

    prs = Presentation(input_file)
    structure = {"schema_version": 1, "slides": [], "elements": []}
    elements = structure["elements"]

    chunk_index = 1
    current_lines = []
    chunk_files = []

    def flush():
        nonlocal chunk_index, current_lines
        if not current_lines:
            return
        fname = f"chunk{chunk_index:04d}.md"
        fpath = os.path.join(temp_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(current_lines) + "\n")
        chunk_files.append(fname)
        chunk_index += 1
        current_lines = []

    for s_idx, slide in enumerate(prs.slides):
        slide_entry = {
            "slide_index": s_idx,
            "shapes": [],
            "notes_paragraphs": [],
        }
        shape_counter = [0]
        slide_lines = []

        _walk_shapes(slide.shapes, s_idx, shape_counter, slide_entry["shapes"], slide_lines, elements)

        # Speaker notes
        if slide.has_notes_slide:
            notes_tf = slide.notes_slide.notes_text_frame
            for p_idx, para in enumerate(notes_tf.paragraphs):
                text = _para_text(para).strip()
                if text:
                    marker_id = f"PPTX:{s_idx}:notes:{p_idx}"
                    slide_lines.append(f"[{marker_id}] {text}")
                    slide_entry["notes_paragraphs"].append(text)
                    _add_element(elements, marker_id, text, para)

        current_lines.extend(slide_lines)
        structure["slides"].append(slide_entry)

        # Flush after each slide if accumulated size exceeds chunk_size
        current_size = sum(len(l) for l in current_lines)
        if current_size >= chunk_size:
            flush()

    flush()

    # Save structure sidecar
    struct_path = os.path.join(temp_dir, "pptx_structure.json")
    with open(struct_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    if chunk_files:
        create_manifest(temp_dir, chunk_files, struct_path)

    total_markers = sum(
        sum(1 for _ in open(os.path.join(temp_dir, cf)).readlines())
        for cf in chunk_files
    )
    print(
        f"PPTX: {len(prs.slides)} slide(s) → {len(chunk_files)} chunk(s), "
        f"~{total_markers} text block(s), {len(elements)} element(s)"
    )
    return len(chunk_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PPTX text into translation chunks")
    parser.add_argument("input_file")
    parser.add_argument("temp_dir")
    parser.add_argument("--chunk-size", type=int, default=6000)
    args = parser.parse_args()
    os.makedirs(args.temp_dir, exist_ok=True)
    count = extract_pptx_to_chunks(args.input_file, args.temp_dir, args.chunk_size)
    sys.exit(0 if count > 0 else 1)
