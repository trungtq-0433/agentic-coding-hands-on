#!/usr/bin/env python3
# layout-exempt: rebuild-spec validator — docs/features|screens|generated paths are managed targets
"""v26.0.0 — A3 Source Walkthrough + B4 DB Impact per Event deterministic validator.

Covers BOTH families from one validator (Decision 2): A3 `## Source Walkthrough` in
technical-spec.md AND screen-spec spec.md; B4 `## DB Impact per Event` in technical-spec.md
ONLY (screen-spec stays UI-scoped). Degradation contract (mirrors validate_feature_screen_link.py's
v24 WARN-first shape — never break un-migrated repos): (1) absent -> WARN `*.pre_migration`;
(2) present, empty body -> CRITICAL `*.malformed`; (3) present, unfilled scaffold placeholder
-> WARN `*.unmapped`; (4) B4 real row with a blank, non-`[INFERRED]` Source cell -> WARN
`db_impact.uncited`. B4 also accepts a literal `N/A — ...` body (no DB writes) as well-formed,
no table required. Neither heading is ever added to `_spec_constants.REQUIRED_H2_TECH`
(Decision 2 — no degradation window there); this validator is the ONLY gate for these sections.

Stdlib only. Exit codes: 0 (PASS/WARN), 1 (FAIL critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, mask_fenced, split_table_row  # noqa: E402
from _md_scan_lib import strip_comments as _strip_comments  # noqa: E402
from _nav_table_parse_lib import _first_table_after, data_rows  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _spec_constants import A3_HEADING, B4_HEADING  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, recalculate_totals,
)

VALIDATOR = "reading_guide_db_impact"

_BRACE_RE = re.compile(r"\{[^{}]*\}")
_NA_RE = re.compile(r"^\s*N/A\b", re.IGNORECASE)
_CITED_RE = re.compile(r"`[^`\n:]+:\d+")
_INFERRED_RE = re.compile(r"\[INFERRED\]")


def _issue(sev: str, rid: str, file_path: str, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": file_path}, "message": msg}

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def _section_body(text: str, heading: str) -> str | None:
    """Body of `heading`'s section, bounded by the next H1/H2 heading or EOF. None if
    absent. C1 fix: walks `iter_lines_with_fence` so the closing boundary is recognized
    ONLY when `in_fence` is False — a fenced `# Note:`/`## X`-shaped line inside the
    section (e.g. a code sample) can no longer truncate the body early and hide a
    trailing unfilled `{placeholder}` scaffold."""
    heading_pat = re.compile(r"^" + re.escape(heading) + r"[ \t]*$")
    boundary_pat = re.compile(r"^#{1,2}[ \t]")
    body_lines: list[str] | None = None
    for _, line, in_fence in iter_lines_with_fence(text):
        if body_lines is None:
            if not in_fence and heading_pat.match(line):
                body_lines = []
            continue
        if not in_fence and boundary_pat.match(line):
            break
        body_lines.append(line)
    return "\n".join(body_lines) if body_lines is not None else None


def check_source_walkthrough(text: str, file_path: str) -> list[dict]:
    """A3 — shared check for technical-spec.md and screen-spec spec.md."""
    body = _section_body(text, A3_HEADING)
    if body is None:
        return [_issue("warning", "reading_guide.pre_migration", file_path,
                        f"{A3_HEADING!r} section missing (pre-migration); run "
                        "migrate-reading-guide-db-impact.py")]
    stripped = _strip_comments(body)
    if not stripped.strip():
        return [_issue("critical", "reading_guide.malformed", file_path,
                        f"{A3_HEADING!r} present but body is empty")]
    if _BRACE_RE.search(stripped):
        return [_issue("warning", "reading_guide.unmapped", file_path,
                        f"{A3_HEADING!r} still carries an unfilled `{{...}}` template "
                        "placeholder")]
    return []


def check_db_impact(text: str, file_path: str) -> list[dict]:
    """B4 — technical-spec.md only."""
    body = _section_body(text, B4_HEADING)
    if body is None:
        return [_issue("warning", "db_impact.pre_migration", file_path,
                        f"{B4_HEADING!r} section missing (pre-migration); run "
                        "migrate-reading-guide-db-impact.py")]
    stripped = _strip_comments(body)
    content = stripped.strip()
    if not content:
        return [_issue("critical", "db_impact.malformed", file_path,
                        f"{B4_HEADING!r} present but body is empty")]
    if _NA_RE.match(content):
        return []  # valid escape: feature performs no DB writes
    # R2 fix: extract the table from the fence-masked text, not raw text — a fenced
    # EXAMPLE table inside the B4 section (e.g. authoring guidance) must never be
    # mistaken for the real one.
    table = _first_table_after(mask_fenced(text), re.escape(B4_HEADING) + r"\b")
    if len(table) < 2:
        return [_issue("critical", "db_impact.malformed", file_path,
                        f"{B4_HEADING!r} present but no parseable table found (and not N/A)")]
    header = split_table_row(table[0])
    rows = data_rows(table)  # tolerant of a missing/malformed separator row
    real_rows = [r for r in rows if split_table_row(r) and not split_table_row(r)[0].startswith("{")]
    if rows and not real_rows:
        return [_issue("warning", "db_impact.unmapped", file_path,
                        f"{B4_HEADING!r} table has only placeholder rows (still being filled in)")]
    src_idx = next((i for i, h in enumerate(header) if "source" in h.casefold()), len(header) - 1)
    issues: list[dict] = []
    for raw in real_rows:
        cells = split_table_row(raw)
        src_cell = cells[src_idx] if src_idx < len(cells) else ""
        if not _INFERRED_RE.search(src_cell) and not _CITED_RE.search(src_cell):
            label = cells[0] if cells else "?"
            issues.append(_issue("warning", "db_impact.uncited", file_path,
                                  f"{B4_HEADING!r} row {label!r} has no `file:line` citation "
                                  "and no `[INFERRED]` tag in its Source cell"))
    return issues


def validate(root: Path) -> dict:
    """Walk a docs/ or artifacts/ root and aggregate A3 + B4 issues for both families."""
    issues: list[dict] = []
    for spec in sorted((root / "features").glob("*/technical-spec.md")):
        text = _read(spec)
        issues += check_source_walkthrough(text, str(spec))
        issues += check_db_impact(text, str(spec))
    for spec in sorted((root / "screens").glob("*/spec.md")):
        text = _read(spec)
        issues += check_source_walkthrough(text, str(spec))

    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="rebuild-spec v26 A3 Source Walkthrough + B4 DB Impact per Event validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--docs-root", help="docs/ (or docs/<lang>/) root to validate")
    g.add_argument("--plan-dir", help="plan dir; validates <plan>/artifacts/")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    proj = resolve_project_root(args.project_root)

    root = (Path(args.docs_root) if args.docs_root
            else Path(args.plan_dir) / "artifacts").resolve()
    if not root.is_dir():
        print(f"[ERROR] root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        assert_under(root, proj)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    try:
        result = validate(root)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, proj)
            summary = load_summary(sp, root.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"], "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2
    return 1 if result["summary"]["critical"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
