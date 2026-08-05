#!/usr/bin/env python3
"""extract_docx.py - Extract DOCX to Markdown chunks via raw-XML engine.

Produces chunk*.md (with [P:id] markers) + docx_structure.json (with per-element
components needed by the mapping and rebuild phases).

Schema version 4: id-based elements, components per element, parts_used list.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_extract_engine import extract
from docx_xml_model import TranslateElement

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from manifest import create_manifest


def _group_into_chunks(items: list[tuple[str, dict]], target_size: int) -> list[list[tuple[str, dict]]]:
    chunks, current, size = [], [], 0
    for md, meta in items:
        block_size = len(md) + 2
        if size + block_size > target_size and current:
            chunks.append(current)
            current, size = [], 0
        current.append((md, meta))
        size += block_size
    if current:
        chunks.append(current)
    return chunks


def extract_docx_to_chunks(docx_path: str, temp_dir: str, chunk_size: int = 6000) -> int:
    """Extract DOCX to chunks + docx_structure.json using the raw-XML engine.

    Returns number of chunk files created, or 0 on failure.
    """
    elements, parts_used = extract(docx_path)

    structure = {
        "schema_version": 4,
        "source_docx": os.path.abspath(docx_path),
        "parts_used": parts_used,
        "elements": [e.to_dict() for e in elements],
    }
    struct_path = os.path.join(temp_dir, "docx_structure.json")
    with open(struct_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    print(f"Wrote docx_structure.json ({len(elements)} elements, {len(parts_used)} parts)")

    # Build translatable items: (chunk_line, element_dict)
    items: list[tuple[str, dict]] = []
    for elem in elements:
        text = elem.general_text.strip()
        if text:
            line = f"[P:{elem.id}] {text}"
            items.append((line, elem.to_dict()))

    if not items:
        print("No translatable content found in DOCX")
        return 0

    input_md = os.path.join(temp_dir, "input.md")
    with open(input_md, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md for md, _ in items))

    groups = _group_into_chunks(items, chunk_size)
    chunk_files = []
    for i, group in enumerate(groups, 1):
        fname = f"chunk{i:04d}.md"
        with open(os.path.join(temp_dir, fname), "w", encoding="utf-8") as f:
            f.write("\n\n".join(md for md, _ in group))
        chunk_files.append(fname)

    create_manifest(temp_dir, chunk_files, input_md)
    print(f"DOCX extracted: {len(chunk_files)} chunks, {len(elements)} elements")
    return len(chunk_files)


def main():
    parser = argparse.ArgumentParser(description="Extract DOCX to Markdown chunks (raw-XML engine)")
    parser.add_argument("docx_file", help="Input DOCX file")
    parser.add_argument("--temp-dir", required=True, help="Output temp directory")
    parser.add_argument("--chunk-size", type=int, default=6000)
    args = parser.parse_args()

    if not os.path.exists(args.docx_file):
        print(f"Error: {args.docx_file} not found")
        sys.exit(1)

    os.makedirs(args.temp_dir, exist_ok=True)
    count = extract_docx_to_chunks(args.docx_file, args.temp_dir, args.chunk_size)
    if count == 0:
        sys.exit(1)
    print(f"Done. Chunks in: {args.temp_dir}")


if __name__ == "__main__":
    main()
