#!/usr/bin/env python3
"""Wave 6.875 — api-map deterministic validator.
Checks api-map.md against 4 deterministic rules.
Regex + section parsing; stdlib only.
Exit codes: 0 (PASS/WARN), 1 (FAIL critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, load_summary, recalculate_totals, derive_overall_status  # noqa: E402

VALIDATOR = "api_map"

# Tolerate any inter-pipe whitespace (incl. compact `|GET|` and padded `|  GET |`)
# so merged/reformatted rows are never silently skipped past the dup/handler checks.
ENDPOINT_ROW_RE = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\b")
METHOD_PATH_RE = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*([^|]+?)\s*\|")


def _issue(sev: str, rid: str, file_path: str, line_num: int | None, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": line_num},
        "message": msg,
    }


def _parse_h2_sections(text: str) -> list[dict]:
    """Split on ## H2 headings. Returns list of {heading, body, line_start}."""
    sections: list[dict] = []
    lines = text.splitlines()
    current: dict | None = None

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current is not None:
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                sections.append(current)
            current = {"heading": line.strip(), "line_start": i + 1, "_lines": []}
        elif current is not None:
            current["_lines"].append(line)

    if current is not None:
        current["body"] = "\n".join(current["_lines"])
        del current["_lines"]
        sections.append(current)

    return sections


def _parse_h3_domains(body: str, section_line_start: int) -> list[dict]:
    """Split section body on ### H3 headings for domain sub-sections."""
    domains: list[dict] = []
    lines = body.splitlines()
    current: dict | None = None

    for i, line in enumerate(lines):
        if line.startswith("### "):
            if current is not None:
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                domains.append(current)
            current = {
                "heading": line.strip(),
                "line_start": section_line_start + i + 1,
                "_lines": [],
            }
        elif current is not None:
            current["_lines"].append(line)

    if current is not None:
        current["body"] = "\n".join(current["_lines"])
        del current["_lines"]
        domains.append(current)

    return domains


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    issues: list[dict] = []

    if single_file:
        am_path = single_file
    else:
        am_path = plan_dir / "artifacts" / "api-map.md"

    rel_path = "api-map.md"
    try:
        rel_path = str(am_path.relative_to(root))
    except ValueError:
        rel_path = str(am_path)

    if not am_path.is_file():
        issues.append(_issue("warning", "ApiMap.completed_missing", rel_path, 0,
                             "api-map.md not found"))
        return _build_result(issues, plan_dir)

    text = am_path.read_text(encoding="utf-8", errors="replace")
    sections = _parse_h2_sections(text)

    # Check: required_sections — ## Endpoints by Domain must exist
    endpoints_sections = [s for s in sections
                          if "endpoints by domain" in s["heading"].lower()]

    if not endpoints_sections:
        issues.append(_issue("critical", "ApiMap.required_sections", rel_path, 1,
                             "Required section '## Endpoints by Domain' not found"))
        return _build_result(issues, plan_dir)

    # Check: single_header — exactly ONE ## Endpoints by Domain section
    if len(endpoints_sections) > 1:
        for sec in endpoints_sections[1:]:
            issues.append(_issue("critical", "ApiMap.single_header", rel_path, sec["line_start"],
                                 "Duplicate '## Endpoints by Domain' section — possibly caused by fragment merge"))

    # Use the first (canonical) section for further checks
    ep_section = endpoints_sections[0]
    domains = _parse_h3_domains(ep_section["body"], ep_section["line_start"])

    seen_endpoints: dict[str, int] = {}  # "METHOD PATH" -> first absolute line number

    for domain in domains:
        domain_lines = domain["body"].splitlines()
        for j, line in enumerate(domain_lines):
            abs_line = domain["line_start"] + j + 1
            if not ENDPOINT_ROW_RE.match(line):
                continue
            m = METHOD_PATH_RE.match(line)
            if not m:
                continue
            method = m.group(1).strip()
            # Normalize backtick-wrapped paths (the api-map template emits
            # `/api/users`) so they dedup against bare paths after fragment merge.
            path = m.group(2).strip().strip("`").strip()
            key = f"{method} {path}"

            # Check: no_dup_endpoint
            if key in seen_endpoints:
                issues.append(_issue("critical", "ApiMap.no_dup_endpoint", rel_path, abs_line,
                                     f"Duplicate endpoint '{key}' (first seen at line {seen_endpoints[key]})"))
            else:
                seen_endpoints[key] = abs_line

            # Check: handler_present — handler column (3rd cell) must be non-empty
            raw_cells = [c.strip() for c in line.split("|")]
            # Positional: split on | gives ['', 'Method', 'Path', 'Handler', ...]
            if len(raw_cells) < 4 or not raw_cells[3]:
                issues.append(_issue("warning", "ApiMap.handler_present", rel_path, abs_line,
                                     f"Endpoint '{key}' has empty or missing Handler column"))

    return _build_result(issues, plan_dir)


def _build_result(issues: list[dict], plan_dir: Path) -> dict:
    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_dir": str(plan_dir),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 api-map validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--api-map-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
    else:
        single = Path(args.api_map_file).resolve()
        plan_dir = single.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, root, single)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    crit = result["summary"]["critical"]

    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"],
                "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
