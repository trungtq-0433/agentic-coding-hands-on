#!/usr/bin/env python3
"""Public API for the PDF in-place translation engine.

Two pure functions with no LLM / network dependency:
  extract_elements(pdf_path, profile=None) -> (elements, structure)
  rebuild(pdf_path, translated_elements, structure, out_path, ...) -> fit_results

CLI usage (for standalone testing):
  python pdf_inplace_engine.py extract <pdf> <out_elements.json> <out_structure.json>
  python pdf_inplace_engine.py rebuild <pdf> <elements.json> <structure.json> <out.pdf>
"""
import argparse
import json
import sys

from pdf_inplace_extract import extract_elements  # noqa: F401
from pdf_inplace_build import rebuild  # noqa: F401


def _cmd_extract(args):
    elements, structure = extract_elements(args.pdf)
    with open(args.elements_out, "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    with open(args.structure_out, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(elements)} elements from {args.pdf}")
    print(f"  Glyphless pages: {structure.get('glyphless_pages', [])}")
    print(f"  Elements: {args.elements_out}")
    print(f"  Structure: {args.structure_out}")


def _cmd_rebuild(args):
    with open(args.elements, encoding="utf-8") as f:
        elements = json.load(f)
    with open(args.structure, encoding="utf-8") as f:
        structure = json.load(f)
    # Identity round-trip: use original text as translated_text
    for elem in elements:
        if "translated_text" not in elem:
            elem["translated_text"] = elem.get("text", "")
    fit_results = rebuild(args.pdf, elements, structure, args.out)
    overflow = [eid for eid, ret in fit_results.items() if ret]
    print(f"Rebuilt: {args.out}")
    print(f"  Total elements: {len(fit_results)}")
    print(f"  Overflow elements: {len(overflow)}" + (f" — {overflow[:5]}" if overflow else ""))


def main():
    parser = argparse.ArgumentParser(description="PDF in-place engine CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ext = sub.add_parser("extract", help="Extract elements + structure from a PDF")
    p_ext.add_argument("pdf", help="Input PDF path")
    p_ext.add_argument("elements_out", help="Output elements JSON path")
    p_ext.add_argument("structure_out", help="Output structure JSON path")

    p_reb = sub.add_parser("rebuild", help="Rebuild PDF from elements + structure JSON")
    p_reb.add_argument("pdf", help="Original PDF (source — never mutated)")
    p_reb.add_argument("elements", help="Elements JSON with 'translated_text' field")
    p_reb.add_argument("structure", help="Structure JSON from extract")
    p_reb.add_argument("out", help="Output PDF path")

    args = parser.parse_args()
    if args.cmd == "extract":
        _cmd_extract(args)
    elif args.cmd == "rebuild":
        _cmd_rebuild(args)


if __name__ == "__main__":
    main()
