#!/usr/bin/env python3
"""
build_csv.py — Reconstruct translated CSV from output_chunk*.md files.

Reads csv_structure.json + output_chunk*.md → writes output.csv
"""
import os
import sys
import csv
import json
import glob
import re
import argparse

_MARKER_RE = re.compile(r"^\[CSV:(\d+):(\d+)\]\s*(.*)")


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


def build_csv(temp_dir):
    struct_path = os.path.join(temp_dir, "csv_structure.json")
    if not os.path.exists(struct_path):
        print("Error: csv_structure.json not found")
        return False

    with open(struct_path, "r", encoding="utf-8") as f:
        structure = json.load(f)

    delimiter = structure["delimiter"]
    encoding = structure["encoding"]
    has_header = structure["has_header"]
    header = structure["header"]
    total_rows = structure["total_rows"]
    translatable_cols = set(structure["translatable_cols"])

    # Load original file to preserve untranslated columns
    config = _read_config(temp_dir)
    input_file = config.get("input_file", "")
    original_rows = []
    if input_file and os.path.exists(input_file):
        with open(input_file, "r", encoding=encoding, newline="", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                original_rows.append(list(row))

    # Parse translations from output chunks
    translations = {}
    for chunk_path in sorted(glob.glob(os.path.join(temp_dir, "output_chunk*.md"))):
        with open(chunk_path, "r", encoding="utf-8") as f:
            for line in f:
                m = _MARKER_RE.match(line.rstrip("\n"))
                if m:
                    row_idx = int(m.group(1))
                    col_idx = int(m.group(2))
                    text = m.group(3)
                    translations[(row_idx, col_idx)] = text

    # Reconstruct rows
    output_rows = []
    if has_header and header:
        output_rows.append(header)

    row_offset = 1 if has_header else 0
    for i in range(total_rows):
        row_idx = i + row_offset
        # Start from original row if available
        orig_row_index = row_idx if has_header else i
        if orig_row_index < len(original_rows):
            row = original_rows[orig_row_index].copy()
        else:
            max_col = max(translatable_cols) if translatable_cols else 0
            row = [""] * (max_col + 1)

        # Apply translations
        for col in translatable_cols:
            key = (row_idx, col)
            if key in translations:
                while len(row) <= col:
                    row.append("")
                row[col] = translations[key]

        output_rows.append(row)

    output_path = os.path.join(temp_dir, "output.csv")
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerows(output_rows)

    print(f"CSV output: {output_path} ({len(output_rows)} rows, {os.path.getsize(output_path):,} bytes)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct translated CSV")
    parser.add_argument("temp_dir")
    args = parser.parse_args()
    sys.exit(0 if build_csv(args.temp_dir) else 1)
