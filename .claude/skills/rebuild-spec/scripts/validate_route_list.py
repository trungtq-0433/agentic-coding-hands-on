#!/usr/bin/env python3
"""Wave 6.875 — route-list deterministic validator.
Checks route-list.md against 4 deterministic rules.
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

VALIDATOR = "route_list"

# Tolerate any inter-pipe whitespace (incl. compact `|GET|` and padded `|  GET |`)
# so merged/reformatted rows are never silently skipped past the dup/citation checks.
ROUTE_ROW_RE = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\b")
METHOD_PATH_RE = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*([^|]+?)\s*\|")

# Completeness checks
# Matches approximation markers in table cells / body lines.
# Anchored to table cell content or plain text lines — does NOT fire on literal path params (~user).
# NOTE: `etc` detection is intentionally EXCLUDED from this pattern. It is handled separately
# in prose-only mode to avoid false positives on handler/description table cells (e.g.
# "UserController@index, etc." in the Handler column). ~N and (+...) patterns remain global
# because they are unambiguous as route-count approximations regardless of position.
APPROX_RE = re.compile(r"~\s*\d+|\(\+.*?\)|\bsee\s+routes\.[a-z]{2,4}\b|…", re.IGNORECASE)
# Matches `etc` approximation marker in prose (non-table) lines only.
# Scans all prose lines in the document (not scoped to Backend Routes section body).
ETC_PROSE_RE = re.compile(r"\betc\b\.?", re.IGNORECASE)
# Matches a table data row whose first cell is a resource macro keyword (unexpanded Rails/Phoenix macro).
MACRO_METHOD_RE = re.compile(r"^\|\s*(resources?)\s*\|", re.IGNORECASE)


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
        rl_path = single_file
    else:
        rl_path = plan_dir / "artifacts" / "route-list.md"

    rel_path = "route-list.md"
    try:
        rel_path = str(rl_path.relative_to(root))
    except ValueError:
        rel_path = str(rl_path)

    if not rl_path.is_file():
        issues.append(_issue("warning", "RouteList.completed_missing", rel_path, 0,
                             "route-list.md not found"))
        return _build_result(issues, plan_dir)

    text = rl_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sections = _parse_sections(text)

    # Check: required_sections
    backend_sections = [s for s in sections if s["heading"].strip() == "## Backend Routes"]
    summary_sections = [s for s in sections if "summary" in s["heading"].lower()]

    if not backend_sections:
        issues.append(_issue("critical", "RouteList.required_sections", rel_path, 1,
                             "Required section '## Backend Routes' not found"))
    if not summary_sections:
        issues.append(_issue("warning", "RouteList.required_sections", rel_path, 1,
                             "Required section '## Summary' not found"))

    # Check: single_header — exactly ONE ## Backend Routes section
    if len(backend_sections) > 1:
        for sec in backend_sections[1:]:
            issues.append(_issue("critical", "RouteList.single_header", rel_path, sec["line_start"],
                                 "Duplicate '## Backend Routes' section — possibly caused by fragment merge"))

    # --- Completeness checks ---
    # Build the set of body lines from all backend sections (line numbers preserved).
    # Used for resource-summary-table and unexpanded-macro checks (Backend-scoped).
    backend_body_lines: list[tuple[int, str]] = []
    for sec in backend_sections:
        start = sec["line_start"]  # 1-based line of the ## heading
        for j, body_line in enumerate(sec["body"].splitlines(), start=start + 1):
            backend_body_lines.append((j, body_line))

    # Check: no_approximation_marker — scan ALL document lines for approximation text.
    # Approximation markers anywhere in the file indicate the route list was compressed.
    # False-positive guard: skip cells that look like a URL path (start with `/`).
    # `etc` is checked ONLY on prose (non-table) lines to avoid false positives on
    # handler/description cells like "UserController@index, etc." — see ETC_PROSE_RE.
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip separator rows (---|---) and empty lines
        if not stripped or stripped.startswith("|--") or stripped.startswith("| --"):
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")]
            for cell in cells:
                # Skip cells that look like a URL path (start with /)
                if cell.startswith("/"):
                    continue
                # APPROX_RE excludes `etc` — table cells with etc. in handler/description
                # are NOT approximation markers; only prose `etc` signals compression.
                if APPROX_RE.search(cell):
                    issues.append(_issue("critical", "RouteList.no_approximation_marker",
                                         rel_path, lineno,
                                         f"Approximation marker found in table cell: {cell!r}"))
                    break  # one issue per line is sufficient
        else:
            # Prose lines: check both APPROX_RE and ETC_PROSE_RE
            if APPROX_RE.search(stripped) or ETC_PROSE_RE.search(stripped):
                issues.append(_issue("critical", "RouteList.no_approximation_marker",
                                     rel_path, lineno,
                                     f"Approximation marker found in body text: {stripped!r}"))

    # Check: no_resource_summary_table — table whose header has Resource+Actions but lacks Path/Method.
    # Scoped to Backend Routes body (compressed tables belong there, not in other sections).
    for lineno, body_line in backend_body_lines:
        stripped = body_line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip().lower() for c in stripped.split("|") if c.strip()]
        # Detect compressed resource-summary header: has "resource"+"actions", lacks "path"+"method"
        has_resource = any(c == "resource" or c == "resources" for c in cells)
        has_actions = "actions" in cells
        has_path = "path" in cells
        has_method = "method" in cells
        if has_resource and has_actions and not (has_path or has_method):
            issues.append(_issue("critical", "RouteList.no_resource_summary_table",
                                 rel_path, lineno,
                                 "Compressed resource-summary table detected "
                                 "('Resource'+'Actions' columns without 'Method'/'Path'). "
                                 "Expand to one row per leaf route."))

    # Check: no_unexpanded_macro — row whose method column is a Rails `resources`/`resource` DSL
    # macro keyword (rule_id intentionally unchanged; tests + docs reference it).
    # Scope: Rails-style resource macros only. Phoenix scope/pipe_through, Express router.use(),
    # and Laravel Route::group() are not caught statically and are out of scope for this check.
    for lineno, body_line in backend_body_lines:
        if MACRO_METHOD_RE.match(body_line.strip()):
            issues.append(_issue("warning", "RouteList.no_unexpanded_macro",
                                 rel_path, lineno,
                                 f"Unexpanded resource macro row detected: {body_line.strip()!r}. "
                                 "Expand to explicit RESTful rows (GET /x, POST /x, …)."))

    # Collect all route rows for dup + citation checks
    seen_routes: dict[str, int] = {}  # "METHOD PATH" -> first line number

    for i, line in enumerate(lines, start=1):
        if not ROUTE_ROW_RE.match(line):
            continue
        m = METHOD_PATH_RE.match(line)
        if not m:
            continue
        method = m.group(1).strip()
        path = m.group(2).strip()
        key = f"{method} {path}"

        # Check: no_dup_route
        if key in seen_routes:
            issues.append(_issue("critical", "RouteList.no_dup_route", rel_path, i,
                                 f"Duplicate route '{key}' (first seen at line {seen_routes[key]})"))
        else:
            seen_routes[key] = i

        # Check: citation_present — handler column must be non-empty
        raw_cells = [c.strip() for c in line.split("|")]
        # Keep positional: split on | gives ['', 'GET', '/path', 'Handler', ...', '']
        # Index 3 is the Handler column (0-based, after leading empty)
        if len(raw_cells) < 4 or not raw_cells[3]:
            issues.append(_issue("warning", "RouteList.citation_present", rel_path, i,
                                 f"Route '{key}' has empty or missing Handler column"))

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
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 route-list validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--route-list-file")
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
        single = Path(args.route_list_file).resolve()
        plan_dir = single.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        if single is not None:
            print(
                f"[ERROR] {exc} — when using --route-list-file the file must live under "
                f"<plan_dir>/artifacts/ (e.g. .../my-plan/artifacts/route-list.md)",
                file=sys.stderr,
            )
        else:
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
