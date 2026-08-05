#!/usr/bin/env python3
"""build_docx.py - Rebuild DOCX from docx_mapped.json via raw-XML engine.

Reads docx_mapped.json + docx_structure.json from temp_dir, calls
docx_rebuild_engine.rebuild(), then runs docx_cross_check.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_rebuild_engine import rebuild
from docx_cross_check import check as cross_check


def _load_mapped(temp_dir: str) -> tuple[dict, str, list]:
    """Load docx_mapped.json and docx_structure.json.

    Returns (mapped_by_id, source_docx, parts_used).
    Exits on missing/incompatible files.
    """
    mapped_path = os.path.join(temp_dir, "docx_mapped.json")
    struct_path = os.path.join(temp_dir, "docx_structure.json")

    if not os.path.exists(mapped_path):
        print("Error: docx_mapped.json not found — run the MAP pass (step 6.5) before building.")
        sys.exit(1)
    if not os.path.exists(struct_path):
        print("Error: docx_structure.json not found in temp dir.")
        sys.exit(1)

    with open(mapped_path, encoding="utf-8") as f:
        mapped_data = json.load(f)
    with open(struct_path, encoding="utf-8") as f:
        structure = json.load(f)

    if structure.get("schema_version", 0) < 4:
        print("Error: docx_structure.json is old schema (v<4). Re-extract the DOCX.")
        sys.exit(1)

    mapped_by_id: dict = mapped_data.get("mapped", {})
    source_docx: str = structure.get("source_docx", "")
    parts_used: list = structure.get("parts_used", [])
    return mapped_by_id, source_docx, parts_used


def build_docx_native(temp_dir: str, output_docx: str) -> bool:
    """Rebuild output_docx from mapped components. Returns True on success."""
    mapped_by_id, source_docx, parts_used = _load_mapped(temp_dir)

    if not source_docx or not os.path.exists(source_docx):
        print(f"Error: source DOCX not found: {source_docx}")
        return False

    try:
        rebuild(source_docx, mapped_by_id, parts_used, output_docx)
    except Exception as e:
        print(f"Error during rebuild: {e}")
        return False

    if not os.path.exists(output_docx):
        print("Error: rebuild produced no output file.")
        return False

    size = os.path.getsize(output_docx)
    print(f"Native DOCX rebuilt: {output_docx} ({size:,} bytes)")

    # Cross-check
    report = cross_check(temp_dir, source_docx, output_docx)
    _print_crosscheck_summary(report)

    return True


def _print_crosscheck_summary(report: dict) -> None:
    n = report.get("elements", 0)
    missing = len(report.get("missing_map", []))
    residue = len(report.get("residue", []))
    concat_broken = len(report.get("concat_broken", []))
    parts_ok = "OK" if report.get("part_parity_ok") else "MISMATCH"
    opens_ok = "OK" if report.get("opens_ok") else "FAIL"
    ok = report.get("ok", False)
    print(
        f"Cross-check: {n} elements • missing-map: {missing} • "
        f"residue: {residue} • concat-broken: {concat_broken} • "
        f"parts: {parts_ok} • opens: {opens_ok} • {'OK' if ok else 'ISSUES'}"
    )


def main():
    parser = argparse.ArgumentParser(description="Rebuild DOCX from mapped components (raw-XML engine)")
    parser.add_argument("--temp-dir", required=True, help="Temp directory with docx_mapped.json + docx_structure.json")
    parser.add_argument("--output", required=True, help="Output DOCX path")
    args = parser.parse_args()

    if not os.path.isdir(args.temp_dir):
        print(f"Error: temp dir not found: {args.temp_dir}")
        sys.exit(1)

    if not build_docx_native(args.temp_dir, args.output):
        sys.exit(1)


if __name__ == "__main__":
    main()
