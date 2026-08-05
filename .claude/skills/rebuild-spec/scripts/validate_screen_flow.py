#!/usr/bin/env python3
"""Wave 6.875 — screen-flow deterministic validator.
Checks screen-flow.md against 3 deterministic rules.
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

VALIDATOR = "screen_flow"

# Matches ### SCR001, ### SCR042_Login, etc.
SCR_HEADING_RE = re.compile(r"^### (SCR\d{3})", re.IGNORECASE)


def _issue(sev: str, rid: str, file_path: str, line_num: int | None, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": line_num},
        "message": msg,
    }


def _parse_sections(text: str) -> list[dict]:
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


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    issues: list[dict] = []

    if single_file:
        sf_path = single_file
    else:
        sf_path = plan_dir / "artifacts" / "screen-flow.md"

    rel_path = "screen-flow.md"
    try:
        rel_path = str(sf_path.relative_to(root))
    except ValueError:
        rel_path = str(sf_path)

    if not sf_path.is_file():
        issues.append(_issue("warning", "ScreenFlow.completed_missing", rel_path, 0,
                             "screen-flow.md not found"))
        return _build_result(issues, plan_dir)

    text = sf_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sections = _parse_sections(text)

    # Check: required_sections
    nav_map_sections = [s for s in sections if s["heading"].strip() == "## Navigation Map"]
    access_sections = [s for s in sections if "screen access paths" in s["heading"].lower()]
    transitions_sections = [s for s in sections if "screen transitions" in s["heading"].lower()]

    if not nav_map_sections:
        issues.append(_issue("critical", "ScreenFlow.required_sections", rel_path, 1,
                             "Required section '## Navigation Map' not found"))
    if not access_sections:
        issues.append(_issue("critical", "ScreenFlow.required_sections", rel_path, 1,
                             "Required section '## Screen Access Paths' not found"))
    if not transitions_sections:
        issues.append(_issue("critical", "ScreenFlow.required_sections", rel_path, 1,
                             "Required section '## Screen Transitions' not found"))

    # Check: single_header — exactly ONE of each shared section.
    # A fragment merge can duplicate ANY of the three shared sections; when the two copies
    # hold disjoint SCR codes the no_dup_scr_flow check below cannot see it, so each shared
    # section needs its own single-header guard (not just Navigation Map).
    for dup_sections, label in (
        (nav_map_sections, "## Navigation Map"),
        (transitions_sections, "## Screen Transitions"),
        (access_sections, "## Screen Access Paths"),
    ):
        if len(dup_sections) > 1:
            for sec in dup_sections[1:]:
                issues.append(_issue("critical", "ScreenFlow.single_header", rel_path, sec["line_start"],
                                     f"Duplicate '{label}' section — possibly caused by fragment merge"))

    # Check: no_dup_scr_flow — no duplicate SCR### codes in ### SCR### headings
    # within ## Screen Transitions subsections
    seen_scr: dict[str, int] = {}  # SCR code -> first line number

    for sec in transitions_sections:
        body_lines = sec["body"].splitlines()
        for j, line in enumerate(body_lines):
            abs_line = sec["line_start"] + j + 1
            m = SCR_HEADING_RE.match(line)
            if not m:
                continue
            scr_code = m.group(1).upper()
            if scr_code in seen_scr:
                issues.append(_issue("critical", "ScreenFlow.no_dup_scr_flow", rel_path, abs_line,
                                     f"Duplicate SCR code '{scr_code}' in Screen Transitions "
                                     f"(first seen at line {seen_scr[scr_code]})"))
            else:
                seen_scr[scr_code] = abs_line

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
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 screen-flow validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--screen-flow-file")
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
        single = Path(args.screen_flow_file).resolve()
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
