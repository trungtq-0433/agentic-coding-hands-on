#!/usr/bin/env python3
"""
extract_csv.py — Extract translatable text cells from CSV into [CSV:row:col] chunks.

Usage:
    python3 extract_csv.py <input.csv> <temp_dir> [--chunk-size N]
"""
import os
import sys
import csv
import json
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from manifest import create_manifest


def _detect_encoding(path):
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read(32768)
        enc = chardet.detect(raw).get("encoding") or "utf-8"
        return enc if enc else "utf-8"
    except ImportError:
        return "utf-8-sig"  # handles Excel BOM without chardet


def _looks_numeric(value):
    v = value.strip()
    if not v:
        return True
    if v.startswith("="):
        return True
    v_clean = v.replace(",", "").replace(" ", "").replace("_", "")
    try:
        float(v_clean)
        return True
    except ValueError:
        pass
    if re.match(r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$", v):
        return True
    return False


def _detect_translatable_cols(rows, threshold=0.8):
    """Return set of column indices whose values are mostly translatable text."""
    if not rows:
        return set()
    num_cols = max(len(r) for r in rows)
    translatable = set()
    for col in range(num_cols):
        values = [r[col] if col < len(r) else "" for r in rows]
        non_empty = [v for v in values if v.strip()]
        if not non_empty:
            continue
        numeric_count = sum(1 for v in non_empty if _looks_numeric(v))
        if numeric_count / len(non_empty) < threshold:
            translatable.add(col)
    return translatable


def extract_csv_to_chunks(input_file, temp_dir, chunk_size=6000):
    encoding = _detect_encoding(input_file)

    # Detect delimiter
    try:
        with open(input_file, "r", encoding=encoding, newline="", errors="replace") as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    # Read all rows
    rows = []
    with open(input_file, "r", encoding=encoding, newline="", errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    if not rows:
        print("Error: CSV is empty")
        return 0

    # Detect header
    try:
        has_header = csv.Sniffer().has_header(
            "\n".join(delimiter.join(r) for r in rows[:20])
        )
    except csv.Error:
        has_header = False

    header = rows[0] if has_header else []
    data_rows = rows[1:] if has_header else rows

    if not data_rows:
        print("Error: CSV has no data rows")
        return 0

    translatable_cols = _detect_translatable_cols(data_rows)
    if not translatable_cols:
        print("Warning: No translatable columns detected (all numeric/empty/formula)")
        return 0

    # Save structure sidecar
    structure = {
        "delimiter": delimiter,
        "encoding": encoding,
        "has_header": has_header,
        "header": header,
        "translatable_cols": sorted(translatable_cols),
        "total_rows": len(data_rows),
    }
    struct_path = os.path.join(temp_dir, "csv_structure.json")
    with open(struct_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    # row_offset: header occupies row 0, data starts at 1 (or 0 if no header)
    row_offset = 1 if has_header else 0

    chunk_index = 1
    current_lines = []
    current_size = 0
    chunk_files = []

    def flush():
        nonlocal chunk_index, current_lines, current_size
        if not current_lines:
            return
        fname = f"chunk{chunk_index:04d}.md"
        fpath = os.path.join(temp_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("\n".join(current_lines) + "\n")
        chunk_files.append(fname)
        chunk_index += 1
        current_lines = []
        current_size = 0

    for i, row in enumerate(data_rows):
        row_idx = i + row_offset
        for col in sorted(translatable_cols):
            cell_text = row[col].strip() if col < len(row) else ""
            if not cell_text:
                continue
            marker = f"[CSV:{row_idx}:{col}] {cell_text}"
            current_lines.append(marker)
            current_size += len(marker)
        if current_size >= chunk_size:
            flush()

    flush()

    if chunk_files:
        create_manifest(temp_dir, chunk_files, struct_path)

    print(
        f"CSV: extracted {len(chunk_files)} chunk(s) from {len(data_rows)} data rows, "
        f"{len(translatable_cols)} translatable column(s)"
    )
    return len(chunk_files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract CSV text cells into translation chunks")
    parser.add_argument("input_file")
    parser.add_argument("temp_dir")
    parser.add_argument("--chunk-size", type=int, default=6000)
    args = parser.parse_args()
    os.makedirs(args.temp_dir, exist_ok=True)
    count = extract_csv_to_chunks(args.input_file, args.temp_dir, args.chunk_size)
    sys.exit(0 if count > 0 else 1)
