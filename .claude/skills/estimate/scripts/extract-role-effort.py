#!/usr/bin/env python3
"""CLI: Extract per-role effort from WBS Excel files.

Usage:
    python3 scripts/extract-role-effort.py <excel-file> [--sheet <name>] [--json] [--yaml]
    python3 scripts/extract-role-effort.py <excel-file> --update-entry <yaml-path>
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic_estimate.utils.role_effort_extractor import extract_role_effort


def main():
    parser = argparse.ArgumentParser(description="Extract per-role effort from WBS Excel")
    parser.add_argument("excel_file", help="Path to Excel file")
    parser.add_argument("--sheet", help="Specific sheet name (auto-detect if omitted)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--yaml", action="store_true", dest="yaml_out", help="Output as YAML")
    parser.add_argument(
        "--update-entry",
        metavar="YAML_PATH",
        help="Update an existing historical YAML entry with extracted effort",
    )
    parser.add_argument(
        "--scan-rows", type=int, default=15, help="Number of rows to scan for headers (default: 15)"
    )
    args = parser.parse_args()

    result = extract_role_effort(
        args.excel_file, sheet_name=args.sheet, header_scan_rows=args.scan_rows
    )

    for w in result.warnings:
        print(f"[INFO] {w}", file=sys.stderr)

    if not result.tasks:
        print("No tasks extracted. Check warnings above.", file=sys.stderr)
        sys.exit(1)

    if args.update_entry:
        _update_yaml_entry(args.update_entry, result)
        return

    output = _build_output(result)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif args.yaml_out:
        import yaml

        print(yaml.dump(output, default_flow_style=False, allow_unicode=True, sort_keys=False))
    else:
        _print_table(result)


def _build_output(result) -> dict:
    return {
        "sheet": result.sheet_name,
        "task_count": len(result.tasks),
        "total_md": round(sum(t.total_md for t in result.tasks), 1),
        "by_category": {
            cat: {"total_md": result.category_totals[cat], "effort": result.aggregated[cat]}
            for cat in sorted(result.category_totals.keys())
        },
        "tasks": [
            {
                "id": t.task_id,
                "name": t.task_name[:60],
                "type": t.task_type,
                "total_md": t.total_md,
                "effort": t.effort,
            }
            for t in result.tasks
        ],
    }


def _print_table(result):
    print(f"\nSheet: {result.sheet_name}")
    print(f"Tasks extracted: {len(result.tasks)}")
    print(f"Total MD: {sum(t.total_md for t in result.tasks):.1f}\n")

    all_roles = sorted({r for cat in result.aggregated.values() for r in cat})
    header = f"{'Category':<20} {'Total':>8}"
    for r in all_roles:
        header += f" {r:>10}"
    print(header)
    print("-" * len(header))

    for cat in sorted(result.category_totals.keys()):
        row = f"{cat:<20} {result.category_totals[cat]:>8.1f}"
        for r in all_roles:
            val = result.aggregated[cat].get(r, 0)
            row += f" {val:>10.1f}" if val else f" {'':>10}"
        print(row)

    total = sum(result.category_totals.values())
    row = f"{'TOTAL':<20} {total:>8.1f}"
    for r in all_roles:
        val = sum(result.aggregated.get(cat, {}).get(r, 0) for cat in result.category_totals)
        row += f" {val:>10.1f}" if val else f" {'':>10}"
    print("-" * len(header))
    print(row)


def _update_yaml_entry(yaml_path: str, result):
    """Update historical YAML entry tasks with extracted per-role effort."""
    import yaml

    path = Path(yaml_path)
    if not path.exists():
        print(f"File not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        entry = yaml.safe_load(f)

    existing_tasks = {t["task_type"]: t for t in entry.get("estimate", {}).get("tasks", [])}

    updated = 0
    for cat, effort in result.aggregated.items():
        if cat in existing_tasks:
            existing_tasks[cat]["effort"] = {r: round(v) for r, v in effort.items() if v > 0}
            role_sum = sum(existing_tasks[cat]["effort"].values())
            if role_sum > 0:
                existing_tasks[cat]["total_md"] = round(role_sum)
            updated += 1

    entry["estimate"]["tasks"] = list(existing_tasks.values())
    entry["estimate"]["total_md"] = sum(t["total_md"] for t in entry["estimate"]["tasks"])

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(entry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Updated {updated} task categories in {yaml_path}")
    print(f"New total_md: {entry['estimate']['total_md']}")


if __name__ == "__main__":
    main()
