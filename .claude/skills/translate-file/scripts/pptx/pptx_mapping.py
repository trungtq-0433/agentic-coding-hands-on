#!/usr/bin/env python3
"""pptx_mapping.py - Two-phase MAP pass for PPTX native engine.

Usage:
  python3 pptx_mapping.py prepare <temp_dir>   -- reads output_chunk*.md + structure,
                                                   writes pptx_map_chunk*.json
  python3 pptx_mapping.py finalize <temp_dir>  -- reads output_pptx_map_chunk*.json,
                                                   writes pptx_mapped.json

prepare stdout: single integer — number of map chunks written (0 = all single-format).
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PPTX_DIR = os.path.dirname(os.path.abspath(__file__))
_TRANSLATE_DIR = os.path.join(_SCRIPTS_DIR, "translate")
_DOCX_DIR = os.path.join(_SCRIPTS_DIR, "docx")
for _d in (_PPTX_DIR, _TRANSLATE_DIR, _DOCX_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from run_mapping import (  # noqa: E402
    are_all_equal,
    handle_empty_text,
    synthesize_single_run,
    validate_concat,
    batch_items,
    normalize_component,
)

# Matches [PPTX:...] marker at start of line; captures id and text.
_PPTX_MARKER_RE = re.compile(r"^\[PPTX:([^\]]+)\]\s*(.*)")


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def _parse_output_chunks(temp_dir: str) -> dict[str, str]:
    """Parse all output_chunk*.md → {element_id: translated_text}."""
    result: dict[str, str] = {}
    for chunk_path in sorted(glob.glob(os.path.join(temp_dir, "output_chunk*.md"))):
        with open(chunk_path, encoding="utf-8") as f:
            for line in f:
                m = _PPTX_MARKER_RE.match(line.rstrip("\n"))
                if not m:
                    continue
                eid = "PPTX:" + m.group(1)
                text = m.group(2).strip()
                result[eid] = text
    return result


def _prepare(temp_dir: str) -> int:
    struct_path = os.path.join(temp_dir, "pptx_structure.json")
    if not os.path.exists(struct_path):
        sys.exit(f"Error: pptx_structure.json not found in {temp_dir}")
    with open(struct_path, encoding="utf-8") as f:
        structure = json.load(f)

    translated_map = _parse_output_chunks(temp_dir)
    elem_by_id = {e["id"]: e for e in structure.get("elements", [])}

    skip_map: dict[str, list[dict]] = {}
    multi_format: list[dict] = []

    for eid, translated_text in translated_map.items():
        elem = elem_by_id.get(eid)
        if elem is None:
            continue
        components = handle_empty_text(list(elem.get("components", [])))
        if not components:
            skip_map[eid] = [{"text": translated_text}]
            continue
        if are_all_equal(components):
            skip_map[eid] = synthesize_single_run(translated_text, components)
        else:
            multi_format.append({
                "id": eid,
                "translated_general_text": translated_text,
                "components": components,
            })

    skip_path = os.path.join(temp_dir, "pptx_map_skip.json")
    with open(skip_path, "w", encoding="utf-8") as f:
        json.dump(skip_map, f, ensure_ascii=False, indent=2)

    if not multi_format:
        return 0

    # Remove stale map chunks
    for old in glob.glob(os.path.join(temp_dir, "pptx_map_chunk*.json")):
        os.remove(old)

    chunks = batch_items(multi_format)
    for i, batch in enumerate(chunks, 1):
        chunk_path = os.path.join(temp_dir, f"pptx_map_chunk{i:04d}.json")
        with open(chunk_path, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)

    return len(chunks)


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------

def _finalize(temp_dir: str) -> None:
    skip_path = os.path.join(temp_dir, "pptx_map_skip.json")
    if not os.path.exists(skip_path):
        sys.exit("Error: pptx_map_skip.json not found — run prepare first")
    with open(skip_path, encoding="utf-8") as f:
        skip_map: dict[str, list] = json.load(f)

    struct_path = os.path.join(temp_dir, "pptx_structure.json")
    with open(struct_path, encoding="utf-8") as f:
        structure = json.load(f)
    elem_by_id = {e["id"]: e for e in structure.get("elements", [])}

    mapped: dict[str, list[dict]] = dict(skip_map)
    flagged: list[str] = []

    output_chunks = sorted(glob.glob(os.path.join(temp_dir, "output_pptx_map_chunk*.json")))
    for chunk_file in output_chunks:
        with open(chunk_file, encoding="utf-8") as f:
            results = json.load(f)
        if not isinstance(results, list):
            print(f"Warning: {os.path.basename(chunk_file)} is not a list, skipping")
            continue
        for item in results:
            eid = str(item.get("id", ""))
            mc = item.get("mapped_components", [])
            if not eid or not isinstance(mc, list):
                continue
            mc = [normalize_component(c) for c in mc]
            translated_text = item.get("translated_general_text", "")
            if mc and translated_text and not validate_concat(eid, translated_text, mc):
                # Fallback: single run with first original component attrs
                components = elem_by_id.get(eid, {}).get("components", [])
                base = dict(components[0]) if components else {}
                base["text"] = translated_text
                mc = [base]
                flagged.append(eid)
            mapped[eid] = mc

    out = {
        "schema_version": 1,
        "mapped": mapped,
        "flagged_fallback": flagged,
    }
    out_path = os.path.join(temp_dir, "pptx_mapped.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    skip_count = len(skip_map)
    mapped_count = len(mapped)
    print(
        f"PPTX MAP finalized: {mapped_count} elements "
        f"(skip={skip_count}, llm={mapped_count - skip_count}, flagged={len(flagged)})"
    )
    if flagged:
        print(f"Fallback single-run: {flagged[:10]}{'...' if len(flagged) > 10 else ''}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("prepare", "finalize"):
        print("Usage: pptx_mapping.py (prepare|finalize) <temp_dir>")
        sys.exit(1)

    command, temp_dir = sys.argv[1], sys.argv[2]
    if not os.path.isdir(temp_dir):
        sys.exit(f"Error: {temp_dir} is not a directory")

    if command == "prepare":
        count = _prepare(temp_dir)
        print(count)
    else:
        _finalize(temp_dir)


if __name__ == "__main__":
    main()
