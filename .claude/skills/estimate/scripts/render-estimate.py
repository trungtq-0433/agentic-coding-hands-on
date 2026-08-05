#!/usr/bin/env python3
"""Render estimate JSON to markdown, interactive Excel, and/or HTML.

Usage:
    python3 scripts/render-estimate.py estimate.json -o ./output -f md,xlsx,html
    python3 scripts/render-estimate.py estimate.json -f md
    cat estimate.json | python3 scripts/render-estimate.py - -f html
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Render estimate JSON to markdown/Excel/HTML")
    parser.add_argument("input", help="JSON file path or '-' for stdin")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: same as input)",
    )
    parser.add_argument(
        "-f",
        "--formats",
        default="md,xlsx,html",
        help="Comma-separated: md, xlsx, html, assumptions-docx, wbs, proposal (default: md,xlsx,html)",
    )
    parser.add_argument(
        "-p", "--project-name", default=None, help="Override project name for filenames"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Path to estimate-config.yaml (auto-detect if omitted)",
    )
    args = parser.parse_args()

    try:
        if args.input == "-":
            data = json.load(sys.stdin)
        else:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    formats = {f.strip().lower() for f in args.formats.split(",")}
    output_dir = args.output_dir or (Path(args.input).parent if args.input != "-" else Path("."))
    output_dir.mkdir(parents=True, exist_ok=True)

    from agentic_estimate.utils.manifest_manager import derive_slug

    name_slug = derive_slug(args.project_name or data.get("project_name", "estimate"))

    # Inherit timestamp from input filename if present (e.g. *-estimate-260425-1530.json)
    timestamp = None
    if args.input != "-":
        m = re.search(r"-(\d{6}-\d{4})\.json$", args.input)
        if m:
            timestamp = m.group(1)
    if not timestamp:
        timestamp = datetime.now().strftime("%y%m%d-%H%M")
    results = []

    if "md" in formats:
        from agentic_estimate.generators.estimate_json_to_markdown import render as render_md

        md_text = render_md(data)
        md_path = output_dir / f"{name_slug}-estimate-{timestamp}.md"
        md_path.write_text(md_text, encoding="utf-8")
        results.append({"format": "md", "path": str(md_path)})

    if "xlsx" in formats:
        try:
            from agentic_estimate.generators.estimate_json_to_interactive_excel import (
                render as render_xlsx,
            )

            xlsx_path = output_dir / f"{name_slug}-estimate-interactive-{timestamp}.xlsx"
            render_xlsx(data, xlsx_path)
            results.append({"format": "xlsx", "path": str(xlsx_path)})
        except ImportError:
            results.append({"format": "xlsx", "skipped": "openpyxl not installed"})

    if "html" in formats:
        from agentic_estimate.generators.estimate_json_to_html import render as render_html

        html_text = render_html(data)
        html_path = output_dir / f"{name_slug}-estimate-{timestamp}.html"
        html_path.write_text(html_text, encoding="utf-8")
        results.append({"format": "html", "path": str(html_path)})

    if "assumptions-docx" in formats:
        try:
            from agentic_estimate.generators.assumptions_json_to_docx import (
                render as render_assumptions,
            )

            docx_path = output_dir / f"{name_slug}-assumptions-{timestamp}.docx"
            render_assumptions(data, docx_path)
            results.append({"format": "assumptions-docx", "path": str(docx_path)})
        except ImportError:
            results.append({"format": "assumptions-docx", "skipped": "python-docx not installed"})

    if "wbs" in formats:
        try:
            from agentic_estimate.generators.wbs_json_to_standalone_xlsx import render as render_wbs

            wbs_path = output_dir / f"{name_slug}-wbs-{timestamp}.xlsx"
            render_wbs(data, wbs_path)
            results.append({"format": "wbs", "path": str(wbs_path)})
        except ImportError:
            results.append({"format": "wbs", "skipped": "openpyxl not installed"})

    if "proposal" in formats:
        try:
            from agentic_estimate.generators.proposal_json_to_docx import render as render_proposal

            proposal_path = output_dir / f"{name_slug}-proposal-{timestamp}.docx"
            render_proposal(data, proposal_path)
            results.append({"format": "proposal", "path": str(proposal_path)})
        except ImportError:
            results.append({"format": "proposal", "skipped": "python-docx not installed"})

    print(json.dumps({"generated": results}, indent=2))

    if args.input != "-":
        from agentic_estimate.utils import manifest_manager as mm

        manifest = mm.load_manifest(output_dir)
        json_filename = Path(args.input).name
        entry = mm.find_or_create_estimate(manifest, json_filename, data, timestamp)
        for r in results:
            if "path" in r:
                mm.mark_output(entry, r["format"], Path(r["path"]).name)
        mm.save_manifest(output_dir, manifest)


if __name__ == "__main__":
    main()
