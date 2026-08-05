#!/usr/bin/env python3
"""docx_mapping.py - Two-phase MAP pass for DOCX raw-XML engine.

Usage:
  python3 docx_mapping.py prepare <temp_dir>   -- reads output.md + structure,
                                                   writes docx_map_chunk*.json
  python3 docx_mapping.py finalize <temp_dir>  -- reads output_docx_map_chunk*.json,
                                                   writes docx_mapped.json

prepare stdout: single integer — number of map chunks written (0 = all single-format).
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

_MARKER_RE = re.compile(r"^\[P:([^\]]+)\]\s*")

# ---------------------------------------------------------------------------
# Import shared format-agnostic helpers from run_mapping
# ---------------------------------------------------------------------------

_TRANSLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "translate")
if _TRANSLATE_DIR not in sys.path:
    sys.path.insert(0, _TRANSLATE_DIR)

from run_mapping import (  # noqa: E402
    are_all_equal as _are_all_equal,
    handle_empty_text as _handle_empty_text,
    synthesize_single_run as _synthesize_single_run,
    validate_concat as _validate_concat_shared,
    batch_items as _batch_items,
    normalize_component,
)

_MAP_CHUNK_BATCH = 4000  # kept for backward compat; run_mapping uses same default


# ---------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------

def _parse_output_md(temp_dir: str) -> dict[str, str]:
    """Parse output.md → {id: translated_general_text}."""
    path = os.path.join(temp_dir, "output.md")
    if not os.path.exists(path):
        sys.exit(f"Error: output.md not found in {temp_dir}")
    result: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for line in content.splitlines():
        stripped = line.strip()
        # Strip table borders
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        for seg in stripped.split("¶"):
            seg = seg.strip()
            m = _MARKER_RE.match(seg)
            if not m:
                continue
            eid = m.group(1)
            text = seg[m.end():].strip()
            text = re.sub(r"^#{1,6}\s+", "", text)
            result[eid] = text
    return result


def _prepare(temp_dir: str) -> int:
    struct_path = os.path.join(temp_dir, "docx_structure.json")
    if not os.path.exists(struct_path):
        sys.exit(f"Error: docx_structure.json not found in {temp_dir}")
    with open(struct_path, encoding="utf-8") as f:
        structure = json.load(f)

    if structure.get("schema_version", 0) < 4:
        sys.exit("Error: docx_structure.json is old schema (<v4). Re-run extract.")

    translated_map = _parse_output_md(temp_dir)

    # Build {id: {translated_text, components}} for all mapped elements
    elem_by_id = {e["id"]: e for e in structure.get("elements", [])}

    skip_map: dict[str, list[dict]] = {}   # id -> mapped_components (single-format)
    multi_format: list[dict] = []           # elements needing MAP sub-agent

    for eid, translated_text in translated_map.items():
        elem = elem_by_id.get(eid)
        if elem is None:
            continue
        components = _handle_empty_text(list(elem.get("components", [])))
        if not components:
            skip_map[eid] = [{"text": translated_text}]
            continue
        if _are_all_equal(components):
            skip_map[eid] = _synthesize_single_run(translated_text, components)
        else:
            multi_format.append({
                "id": eid,
                "translated_general_text": translated_text,
                "components": components,
            })

    # Write skip.json
    skip_path = os.path.join(temp_dir, "docx_map_skip.json")
    with open(skip_path, "w", encoding="utf-8") as f:
        json.dump(skip_map, f, ensure_ascii=False, indent=2)

    if not multi_format:
        return 0

    # Remove old map chunk files before writing new ones
    for old in glob.glob(os.path.join(temp_dir, "docx_map_chunk*.json")):
        os.remove(old)

    chunks = _batch_items(multi_format)

    for i, batch in enumerate(chunks, 1):
        chunk_path = os.path.join(temp_dir, f"docx_map_chunk{i:04d}.json")
        with open(chunk_path, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)

    return len(chunks)


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------

def _finalize(temp_dir: str) -> None:
    # Load skip mappings (single-format, no LLM needed)
    skip_path = os.path.join(temp_dir, "docx_map_skip.json")
    if not os.path.exists(skip_path):
        sys.exit(f"Error: docx_map_skip.json not found — run prepare first")
    with open(skip_path, encoding="utf-8") as f:
        skip_map: dict[str, list] = json.load(f)

    # Load struct for fallback
    struct_path = os.path.join(temp_dir, "docx_structure.json")
    with open(struct_path, encoding="utf-8") as f:
        structure = json.load(f)
    elem_by_id = {e["id"]: e for e in structure.get("elements", [])}

    mapped: dict[str, list[dict]] = dict(skip_map)
    flagged: list[str] = []

    # Read MAP sub-agent outputs
    output_chunks = sorted(glob.glob(os.path.join(temp_dir, "output_docx_map_chunk*.json")))
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
            # Normalize attribute types
            mc = [normalize_component(c) for c in mc]
            # Validate concat equality
            elem = elem_by_id.get(eid, {})
            translated_text = item.get("translated_general_text", "")
            if mc and translated_text and not _validate_concat_shared(eid, translated_text, mc):
                # Fallback: single run with first component attrs + full translated text
                components = elem.get("components", [])
                base = dict(components[0]) if components else {}
                base["text"] = translated_text
                mc = [base]
                flagged.append(eid)
            mapped[eid] = mc

    # Write docx_mapped.json
    out = {
        "schema_version": 1,
        "mapped": mapped,
        "flagged_fallback": flagged,
    }
    out_path = os.path.join(temp_dir, "docx_mapped.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    skip_count = len(skip_map)
    llm_count = sum(1 for chunk in output_chunks)
    mapped_count = len(mapped)
    print(f"MAP finalized: {mapped_count} elements "
          f"(skip={skip_count}, llm={mapped_count - skip_count}, flagged={len(flagged)})")
    if flagged:
        print(f"Fallback single-run applied to ids: {flagged[:10]}"
              f"{'...' if len(flagged) > 10 else ''}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("prepare", "finalize"):
        print("Usage: docx_mapping.py (prepare|finalize) <temp_dir>")
        sys.exit(1)

    command = sys.argv[1]
    temp_dir = sys.argv[2]

    if not os.path.isdir(temp_dir):
        sys.exit(f"Error: {temp_dir} is not a directory")

    if command == "prepare":
        count = _prepare(temp_dir)
        print(count)  # stdout: number of map chunks (0 = all single-format)
    else:
        _finalize(temp_dir)


if __name__ == "__main__":
    main()
