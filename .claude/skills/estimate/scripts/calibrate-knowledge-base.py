#!/usr/bin/env python3
"""Analyze historical data and propose KB calibration changes.

Usage:
    python3 scripts/calibrate-knowledge-base.py
    python3 scripts/calibrate-knowledge-base.py --format markdown --output report.md
    python3 scripts/calibrate-knowledge-base.py --apply-selected
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_estimate.utils.calibration_engine import CalibrationEngine, CalibrationReport


def render_text(report: CalibrationReport) -> str:
    lines = []
    lines.append("=== KB Calibration Report ===")
    lines.append(
        f"Date: {report.generated_date} | Sources: "
        f"{report.total_accepted} accepted, {report.total_actuals} actuals"
    )
    lines.append("")

    by_cat: dict[str, list] = {}
    for d in report.diffs:
        by_cat.setdefault(d.category, []).append(d)

    for cat, diffs in by_cat.items():
        lines.append(f"--- {cat.replace('_', ' ').title()} ({len(diffs)} changes) ---")
        for d in diffs:
            sign = "+" if d.change_pct > 0 else ""
            lines.append(f"[CHANGE] {d.key}: {d.current} -> {d.proposed} ({sign}{d.change_pct}%)")
            lines.append(
                f"  Samples: {d.samples} | Median: {d.median} | "
                f"IQR: [{d.iqr[0]}, {d.iqr[1]}] | Confidence: {d.confidence}"
            )
        lines.append("")

    if report.unchanged:
        lines.append(f"--- Unchanged ({len(report.unchanged)} parameters) ---")
        lines.append(", ".join(report.unchanged[:20]))
        if len(report.unchanged) > 20:
            lines.append(f"  ... and {len(report.unchanged) - 20} more")
        lines.append("")

    if report.warnings:
        lines.append("--- Warnings ---")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


def render_markdown(report: CalibrationReport) -> str:
    lines = []
    lines.append("# KB Calibration Report\n")
    lines.append(
        f"**Date:** {report.generated_date} | "
        f"**Sources:** {report.total_accepted} accepted, {report.total_actuals} actuals\n"
    )

    by_cat: dict[str, list] = {}
    for d in report.diffs:
        by_cat.setdefault(d.category, []).append(d)

    for cat, diffs in by_cat.items():
        lines.append(f"## {cat.replace('_', ' ').title()} ({len(diffs)} changes)\n")
        lines.append("| Parameter | Current | Proposed | Change | Samples | Confidence |")
        lines.append("|-----------|---------|----------|--------|---------|------------|")
        for d in diffs:
            sign = "+" if d.change_pct > 0 else ""
            lines.append(
                f"| {d.key} | {d.current} | {d.proposed} | {sign}{d.change_pct}% "
                f"| {d.samples} | {d.confidence} |"
            )
        lines.append("")

    if report.unchanged:
        lines.append(f"## Unchanged ({len(report.unchanged)} parameters)\n")
        lines.append(", ".join(f"`{u}`" for u in report.unchanged[:20]))
        lines.append("")

    if report.warnings:
        lines.append("## Warnings\n")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


def render_json(report: CalibrationReport) -> str:
    data = {
        "generated_date": report.generated_date,
        "total_accepted": report.total_accepted,
        "total_actuals": report.total_actuals,
        "diffs": [
            {
                "category": d.category,
                "key": d.key,
                "current": d.current,
                "proposed": d.proposed,
                "change_pct": d.change_pct,
                "samples": d.samples,
                "median": d.median,
                "iqr": list(d.iqr),
                "confidence": d.confidence,
                "sources": d.sources,
            }
            for d in report.diffs
        ],
        "unchanged": report.unchanged,
        "warnings": report.warnings,
    }
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze historical data and propose KB calibration changes"
    )
    parser.add_argument(
        "--report", action="store_true", default=True, help="Generate report only (default)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply all changes (with confirmation)"
    )
    parser.add_argument(
        "--apply-selected", action="store_true", help="Interactive per-item approve/skip"
    )
    parser.add_argument(
        "--format", choices=["text", "markdown", "json"], default="text", help="Output format"
    )
    parser.add_argument("--output", "-o", type=Path, help="Save report to file")
    parser.add_argument(
        "--min-confidence",
        choices=["low", "medium", "high"],
        help="Filter diffs by minimum confidence",
    )

    args = parser.parse_args()

    engine = CalibrationEngine()
    report = engine.analyze()

    if args.min_confidence:
        levels = {"low": 0, "medium": 1, "high": 2}
        min_level = levels[args.min_confidence]
        report.diffs = [d for d in report.diffs if levels.get(d.confidence, 0) >= min_level]

    renderers = {"text": render_text, "markdown": render_markdown, "json": render_json}
    output = renderers[args.format](report)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    if not report.diffs:
        if args.format != "json":
            print("No significant deviations found.")
        return

    if args.apply:
        answer = input(f"\nApply {len(report.diffs)} changes? [y/N] ").strip().lower()
        if answer == "y":
            modified = engine.apply_changes(report.diffs)
            print(f"Applied. Modified files: {', '.join(modified)}")
        else:
            print("Cancelled.")

    elif args.apply_selected:
        approved = []
        for d in report.diffs:
            sign = "+" if d.change_pct > 0 else ""
            prompt = (
                f"[{d.category}] {d.key}: {d.current} -> {d.proposed} "
                f"({sign}{d.change_pct}%) — Apply? [y/N] "
            )
            if input(prompt).strip().lower() == "y":
                approved.append(d)
        if approved:
            modified = engine.apply_changes(approved)
            print(f"\nApplied {len(approved)} changes. Modified: {', '.join(modified)}")
        else:
            print("No changes applied.")


if __name__ == "__main__":
    main()
