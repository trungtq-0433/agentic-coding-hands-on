#!/usr/bin/env python3
"""Render breakdown JSON into overview + per-team markdown files.

Usage:
    python3 scripts/render-breakdown.py breakdown.json -o ./output/project/breakdown/
    python3 scripts/render-breakdown.py breakdown.json
    cat breakdown.json | python3 scripts/render-breakdown.py - -o ./output/
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MAX_LINES = 200


def _split_by_sections(content: str, max_lines: int = MAX_LINES) -> list[str]:
    """Split markdown at section boundaries so each part stays under *max_lines*.

    Tries ``## `` (epic) boundaries first; falls back to ``### `` (story)
    boundaries when a single epic still exceeds *max_lines*.
    """
    lines = content.split("\n")
    if len(lines) <= max_lines:
        return [content]

    parts = _split_at_prefix(lines, "## ", max_lines)
    refined: list[str] = []
    for part in parts:
        part_lines = part.split("\n")
        if len(part_lines) > max_lines:
            refined.extend(_split_at_prefix(part_lines, "### ", max_lines))
        else:
            refined.append(part)
    return refined


def _split_at_prefix(lines: list[str], prefix: str, max_lines: int) -> list[str]:
    """Split *lines* at headings matching *prefix*, keeping parts under *max_lines*."""
    header: list[str] = []
    sections: list[list[str]] = []
    current_start: int | None = None

    for i, line in enumerate(lines):
        if line.startswith(prefix):
            if current_start is not None:
                sections.append(lines[current_start:i])
            else:
                header = lines[:i]
            current_start = i

    if current_start is not None:
        sections.append(lines[current_start:])

    if not sections:
        return ["\n".join(lines) + "\n"]

    parts: list[str] = []
    buf = list(header)

    for section in sections:
        if len(buf) + len(section) > max_lines and len(buf) > len(header):
            parts.append("\n".join(buf) + "\n")
            buf = list(header)
        buf.extend(section)

    if buf:
        parts.append("\n".join(buf) + "\n")

    return parts


def _write_parts(parts: list[str], output_dir: Path, base_name: str) -> list[dict]:
    """Write one file when no split is needed, numbered parts otherwise."""
    generated: list[dict] = []
    if len(parts) == 1:
        filename = f"{base_name}.md"
        fp = output_dir / filename
        fp.write_text(parts[0], encoding="utf-8")
        generated.append({"format": "md", "file": filename, "path": str(fp)})
    else:
        for idx, part in enumerate(parts, 1):
            filename = f"{base_name}-part{idx}.md"
            fp = output_dir / filename
            fp.write_text(part, encoding="utf-8")
            generated.append({"format": "md", "file": filename, "path": str(fp)})
    return generated


def _count_tasks_for_role(data: dict, role: str) -> int:
    count = 0
    for epic in data.get("epics", []):
        for story in epic.get("stories", []):
            count += sum(1 for t in story.get("tasks", []) if t.get("role") == role)
    return count


def _render_index(data: dict, generated: list[dict]) -> str:
    """Build an index page linking to overview and per-team files."""
    project = data["project_name"]
    level = data.get("breakdown_level", 2)
    source = data.get("source", "pre-estimate")
    date = data.get("generated_date", "—")
    role_names = data.get("role_names", {})

    overview_files = [g for g in generated if "breakdown-overview" in g["file"]]
    team_groups: dict[str, list[dict]] = {}
    for g in generated:
        if g["file"].endswith("-tasks.md") or "-tasks-part" in g["file"]:
            slug = g["file"].split("-tasks")[0]
            team_groups.setdefault(slug, []).append(g)

    lines = [
        f"# {project} — Task Breakdown",
        "",
        f"**Date**: {date} | **Level**: L{level} | **Source**: {source}",
        "",
        "---",
        "",
        "## Tổng quan",
        "",
    ]

    if len(overview_files) == 1:
        lines.append(f"- [{overview_files[0]['file']}]({overview_files[0]['file']})")
    else:
        links = [f"[{f['file']}]({f['file']})" for f in overview_files]
        lines.append(f"- Breakdown Overview: {' · '.join(links)}")

    if not team_groups:
        return "\n".join(lines) + "\n"

    lines.extend(["", "## Tasks theo team", ""])
    lines.append("| Team | Tasks | Files |")
    lines.append("|------|-------|-------|")

    for slug in data.get("active_roles", []):
        if slug not in team_groups:
            continue
        display = role_names.get(slug, slug.upper())
        task_count = _count_tasks_for_role(data, slug)
        files = team_groups[slug]
        if len(files) == 1:
            link_str = f"[{files[0]['file']}]({files[0]['file']})"
        else:
            link_str = " · ".join(f"[Part {i}]({f['file']})" for i, f in enumerate(files, 1))
        lines.append(f"| **{display}** | {task_count} | {link_str} |")

    total = sum(_count_tasks_for_role(data, r) for r in data.get("active_roles", []))
    lines.extend(["", f"**Tổng cộng: {total} tasks**", ""])

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Render task breakdown from JSON")
    parser.add_argument("input", help="breakdown.json path or '-' for stdin")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: same as input)",
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

    output_dir = args.output_dir or (Path(args.input).parent if args.input != "-" else Path("."))
    output_dir.mkdir(parents=True, exist_ok=True)

    from agentic_estimate.generators.breakdown_json_to_overview_markdown import (
        render as render_overview,
    )
    from agentic_estimate.generators.breakdown_json_to_per_team_markdown import (
        render as render_per_team,
    )

    generated: list[dict] = []

    overview_content = render_overview(data)
    overview_parts = _split_by_sections(overview_content)
    generated.extend(_write_parts(overview_parts, output_dir, "breakdown-overview"))

    if data.get("breakdown_level", 1) >= 2:
        team_files = render_per_team(data)
        for role_slug, content in team_files.items():
            parts = _split_by_sections(content)
            generated.extend(_write_parts(parts, output_dir, f"{role_slug}-tasks"))

    index_content = _render_index(data, generated)
    index_path = output_dir / "breakdown-index.md"
    index_path.write_text(index_content, encoding="utf-8")
    generated.insert(0, {"format": "md", "file": "breakdown-index.md", "path": str(index_path)})

    print(json.dumps({"generated": generated}, indent=2))

    manifest_dir = output_dir.parent
    manifest_path = manifest_dir / "manifest.json"
    if manifest_path.exists():
        from agentic_estimate.utils import manifest_manager as mm

        manifest = mm.load_manifest(manifest_dir)
        bd_dirname = output_dir.name + "/"
        project_name = data.get("project_name", "").lower()
        for est in manifest.get("estimates", []):
            if project_name and project_name in est.get("name", "").lower():
                mm.mark_breakdown(est, bd_dirname)
                mm.save_manifest(manifest_dir, manifest)
                break


if __name__ == "__main__":
    main()
