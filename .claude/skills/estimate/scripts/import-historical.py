#!/usr/bin/env python3
"""Import estimate data into the historical calibration store.

Usage:
    python3 scripts/import-historical.py estimate.json
    python3 scripts/import-historical.py estimate.json --type actual --actual-md 150
    python3 scripts/import-historical.py estimate.json --dry-run
    python3 scripts/import-historical.py project.xlsx --mapping mapping.yaml
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_estimate.utils.historical_data_loader import (
    check_duplicate_slug,
    normalize_estimate_json,
    validate_entry,
)
from agentic_estimate.utils.knowledge_base_loader_yaml_config import _get_project_root
from agentic_estimate.utils.schema_validator_jsonschema import validate_against_schema

HISTORICAL_DIR = "knowledge-base/historical"


def import_json(filepath: Path, args: argparse.Namespace) -> dict:
    """Import an estimate JSON file."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    valid, errors = validate_against_schema(data, "schemas/estimate-output-schema.json")
    if not valid:
        print("ERROR: Input JSON does not match estimate-output-schema.json:")
        for e in errors[:5]:
            print(f"  - {e}")
        sys.exit(1)

    project_meta = {}
    if args.domain:
        project_meta["domain"] = args.domain
    if args.tech:
        project_meta["tech_stack"] = [t.strip() for t in args.tech.split(",")]
    if args.team_size:
        project_meta["team_size"] = args.team_size
    if args.team_exp:
        project_meta["team_experience"] = args.team_exp

    entry = normalize_estimate_json(
        data,
        entry_type=args.type,
        project_meta=project_meta,
        slug=args.slug,
    )

    if args.type == "actual" and args.actual_md:
        entry["actual"] = {"total_md": args.actual_md}

    return entry


def import_excel(filepath: Path, args: argparse.Namespace) -> dict:
    """Import an Excel/CSV file using column mapping."""
    import pandas as pd

    from agentic_estimate.utils.historical_data_loader import (
        detect_column_mapping,
        normalize_excel_data,
    )

    ext = filepath.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(filepath, skiprows=args.skip_rows or 0)
    else:
        df = pd.read_excel(
            filepath,
            sheet_name=args.sheet or 0,
            skiprows=args.skip_rows or 0,
        )

    headers = list(df.columns)
    sample_rows = df.head(5).values.tolist()

    if args.mapping:
        with open(args.mapping, encoding="utf-8") as f:
            mapping = yaml.safe_load(f)
    else:
        mapping = detect_column_mapping(headers, sample_rows)
        print("Auto-detected column mapping:")
        print(yaml.dump(mapping, default_flow_style=False))
        print("Use --mapping <file> to override.\n")

    rows = df.to_dict("records")
    project_meta = {}
    if args.domain:
        project_meta["domain"] = args.domain
    if args.tech:
        project_meta["tech_stack"] = [t.strip() for t in args.tech.split(",")]
    if args.team_size:
        project_meta["team_size"] = args.team_size
    if args.team_exp:
        project_meta["team_experience"] = args.team_exp

    entry = normalize_excel_data(rows, mapping, args.type, project_meta, slug=args.slug)

    if args.type == "actual" and args.actual_md:
        entry["actual"] = {"total_md": args.actual_md}

    return entry


def save_entry(entry: dict, args: argparse.Namespace, raw_path: Path | None = None):
    """Validate and save canonical entry to YAML."""
    valid, errors = validate_entry(entry)
    if not valid:
        print("ERROR: Sanitized entry fails schema validation:")
        for e in errors[:5]:
            print(f"  - {e}")
        sys.exit(1)

    slug = entry["project"]["name"]
    subdir = "accepted" if entry["type"] == "accepted" else "actuals"

    if not args.force:
        dup = check_duplicate_slug(slug, entry["type"])
        if dup:
            print(f"ERROR: Duplicate slug '{slug}' at {dup}")
            print("Use --force to overwrite.")
            sys.exit(1)

    yaml_content = yaml.dump(entry, default_flow_style=False, sort_keys=False)

    if args.dry_run:
        print("=== DRY RUN — Sanitized canonical YAML ===\n")
        print(yaml_content)
        print("=== No file written ===")
        return

    root = _get_project_root()
    target = root / HISTORICAL_DIR / subdir / f"{slug}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml_content, encoding="utf-8")
    print(f"Saved: {target}")

    if args.keep_raw and raw_path:
        raw_dest = root / HISTORICAL_DIR / "raw" / f"{slug}{raw_path.suffix}"
        raw_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw_path, raw_dest)
        print(f"Raw copy: {raw_dest}")

    task_count = len(entry.get("estimate", {}).get("tasks", []))
    total_md = entry.get("estimate", {}).get("total_md", 0)
    print(f"\nSummary: {task_count} tasks, {total_md} total MD, type={entry['type']}")
    print("Reminder: run `python3 scripts/compile-knowledge-base.py` to update historical summary.")


def main():
    parser = argparse.ArgumentParser(
        description="Import estimate data into historical calibration store"
    )
    parser.add_argument("file", type=Path, help="Path to estimate JSON or Excel file")
    parser.add_argument(
        "--type",
        choices=["accepted", "actual"],
        default="accepted",
        help="Entry type (default: accepted)",
    )
    parser.add_argument("--domain", help="Project domain (e-commerce, saas, etc.)")
    parser.add_argument("--tech", help="Comma-separated tech stack (react,nestjs)")
    parser.add_argument("--team-size", type=int, help="Team size")
    parser.add_argument(
        "--team-exp", choices=["junior", "mid", "senior", "mixed"], help="Team experience level"
    )
    parser.add_argument("--actual-md", type=float, help="Total actual man-days (Type A)")
    parser.add_argument("--slug", help="Anonymous slug (default: auto-increment)")
    parser.add_argument("--dry-run", action="store_true", help="Print YAML without writing")
    parser.add_argument("--force", action="store_true", help="Overwrite existing slug")
    parser.add_argument(
        "--keep-raw", action="store_true", help="Copy raw file to raw/ (default: skip for privacy)"
    )

    # Excel-specific options
    parser.add_argument("--sheet", help="Sheet name for Excel files")
    parser.add_argument("--mapping", type=Path, help="Column mapping YAML file")
    parser.add_argument("--skip-rows", type=int, default=0, help="Skip N header rows")

    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    ext = args.file.suffix.lower()
    if ext == ".json":
        entry = import_json(args.file, args)
    elif ext in (".xlsx", ".xls", ".csv"):
        entry = import_excel(args.file, args)
    else:
        print(f"ERROR: Unsupported file type: {ext}")
        print("Supported: .json, .xlsx, .xls, .csv")
        sys.exit(1)

    save_entry(entry, args, raw_path=args.file)


if __name__ == "__main__":
    main()
