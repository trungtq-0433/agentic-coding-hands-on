#!/usr/bin/env python3
"""Phase B CRUD-matrix validator. Stdlib only.
Checks: citation per CRUD cell, valid op tokens, table cross-ref, column safety, RT-F8 WARN.
Exit: 0 PASS/WARN, 1 critical FAIL, 2 internal error.
"""
from __future__ import annotations
import argparse, datetime as _dt, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, derive_overall_status, load_summary, recalculate_totals  # noqa: E402

VALIDATOR = "crud_matrix"
CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?[^`\n:]+:\d+", re.IGNORECASE)
VALID_OP_RE = re.compile(r"^(\s*[CRUDcrud✓✗x\-]\s*|\s*\[UNVERIFIED\]\s*|\s*)$")
TABLE_ROW_RE = re.compile(r"^\s*\|")
SEPARATOR_ROW_RE = re.compile(r"^\s*\|[\s\-|:]+\|?\s*$")
CROSS_MODULE_RE = re.compile(r"^#{1,3}\s+Cross.Module", re.IGNORECASE)
HEADER_KEYWORDS = {"table", "c", "r", "u", "d", "columns", "source"}
TABLE_NAME_RE = re.compile(r"^\|\s*([^\|]+?)\s*\|")


def _issue(sev, rid, fp, ln, msg):
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": fp, "line": ln}, "message": msg}


def _collect_names(path: Path, h3_headings: bool = False) -> set[str]:
    """Extract identifier names from first column of Markdown tables (+ optional H3 headings).

    Kind-agnostic by design: this walks every Markdown table in db-objects.md regardless of
    which `##`/`###` section (kind) it sits under, so a CRUD cell cross-references cleanly
    against `table`, `view`, ... AND `dataset` (flat-file/VSAM COBOL) objects alike — no
    per-kind allowlist to keep in sync here (Phase 06).
    """
    names: set[str] = set()
    if not path.is_file():
        return names
    in_tbl = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if h3_headings and s.startswith("### "):
            n = s[4:].strip()
            if n: names.add(n.upper())
            continue
        if not s.startswith("|"):
            in_tbl = False; continue
        if SEPARATOR_ROW_RE.match(s):
            in_tbl = True; continue
        if not in_tbl:
            in_tbl = True; continue
        m = TABLE_NAME_RE.match(s)
        if m:
            n = m.group(1).strip().lstrip("\\").strip()
            if n: names.add(n.upper())
    return names


def _load_digest(artifacts_dir: Path) -> dict | None:
    p = artifacts_dir / "_digest_extract_data_flow.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def _dynamic_zero_crud(digest: dict | None) -> set[str]:
    if not digest:
        return set()
    return {u.get("path", "") for u in digest.get("units", [])
            if u.get("parse_coverage", {}).get("dynamic_sql_detected") and not u.get("db_ops")}


def _parse_rows(lines: list[str]) -> list[dict]:
    rows: list[dict] = []
    in_cross = in_tbl = False
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if CROSS_MODULE_RE.match(s):
            in_cross = True; in_tbl = False; continue
        if s.startswith("## ") or s.startswith("### "):
            if not CROSS_MODULE_RE.match(s):
                in_cross = False; in_tbl = False
            continue
        if in_cross or not TABLE_ROW_RE.match(s):
            if s and not TABLE_ROW_RE.match(s):
                in_tbl = False
            continue
        if SEPARATOR_ROW_RE.match(s):
            in_tbl = True; continue
        if not in_tbl:
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells.pop(0)
        if cells and cells[-1] == "":
            cells.pop()
        if len(cells) < 2:
            continue
        rows.append({"ln": i, "table": cells[0], "cells": cells,
                     "src": cells[-1], "raw": line})
    return rows


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    issues: list[dict] = []
    matrix_path = single_file or (plan_dir / "artifacts" / "crud-matrix.md")
    artifacts_dir = plan_dir / "artifacts"
    try:
        rel = str(matrix_path.relative_to(root))
    except ValueError:
        rel = str(matrix_path)

    if not matrix_path.is_file():
        issues.append(_issue("warning", "CrudMatrix.completed_missing", rel, 0,
                             "crud-matrix.md not found"))
        return _build(issues, plan_dir)

    text = matrix_path.read_text(encoding="utf-8", errors="replace")
    db_objs = root / "docs" / "generated" / "db-objects.md"
    dm = root / "docs" / "generated" / "entities.md"
    known = _collect_names(db_objs) | _collect_names(dm, h3_headings=True)
    has_ref = db_objs.is_file() or dm.is_file()

    for p in _dynamic_zero_crud(_load_digest(artifacts_dir)):
        issues.append(_issue("warning", "CrudMatrix.dynamic_sql_no_crud", rel, None,
                             f"Unit '{p}' has dynamic_sql_detected:true but 0 CRUD cells "
                             "— likely false-negative; verify manually"))

    rows = _parse_rows(text.splitlines())
    # Guard against vacuous PASS: an empty file, or one whose tables omit the separator
    # row (|---|---|), parses to zero rows. Without this the validator would report PASS
    # on a malformed/empty matrix — false confidence the gate exists to prevent.
    if not rows:
        if not text.strip():
            issues.append(_issue("critical", "CrudMatrix.empty", rel, 0,
                                 "crud-matrix.md is empty — no CRUD content to validate"))
        elif any(TABLE_ROW_RE.match(ln.strip()) for ln in text.splitlines()):
            issues.append(_issue("critical", "CrudMatrix.no_rows_parsed", rel, 0,
                                 "table-like content present but no rows parsed — "
                                 "missing separator row (|---|---|)?"))

    for row in rows:
        cells, ln, tbl = row["cells"], row["ln"], row["table"]
        if len(cells) < 2:
            issues.append(_issue("warning", "CrudMatrix.column_drift", rel, ln,
                                 f"Row has fewer columns than expected: {tbl!r}")); continue
        if not CITATION_RE.search(row["src"]):
            issues.append(_issue("critical", "CrudMatrix.citation_missing", rel, ln,
                                 f"Table '{tbl}' CRUD row missing citation "
                                 f"(**Source:** `path:line`); got: {row['src']!r}"))
        if has_ref:
            norm = tbl.upper().lstrip("\\").strip()
            if norm and norm not in known:
                issues.append(_issue("warning", "CrudMatrix.table_unknown", rel, ln,
                                     f"Table '{tbl}' not in db-objects.md or entities.md"))
        for idx in range(1, min(5, len(cells))):
            v = cells[idx].strip()
            if v and not VALID_OP_RE.match(v):
                issues.append(_issue("critical", "CrudMatrix.invalid_op_token", rel, ln,
                                     f"Invalid op token {v!r} col {idx} for '{tbl}'; "
                                     "expected C/R/U/D, ✓, or empty"))
    return _build(issues, plan_dir)


def _build(issues: list[dict], plan_dir: Path) -> dict:
    c = sum(1 for i in issues if i["severity"] == "critical")
    w = sum(1 for i in issues if i["severity"] == "warning")
    return {"validator": VALIDATOR,
            "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir),
            "status": "FAIL" if c else ("WARN" if w else "PASS"),
            "summary": {"critical": c, "warning": w}, "issues": issues}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Phase B CRUD-matrix validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir"); g.add_argument("--crud-matrix-file")
    p.add_argument("--project-root", default=None); p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)
    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve(); single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir not a directory: {plan_dir}", file=sys.stderr); return 2
    else:
        single = Path(args.crud_matrix_file).resolve(); plan_dir = single.parent.parent
    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr); return 2
    try:
        result = validate(plan_dir, root, single)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr); return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    crit = result["summary"]["critical"]
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            summary["validators"][VALIDATOR] = {"status": result["status"],
                                                "summary": result["summary"],
                                                "issues": result["issues"]}
            recalculate_totals(summary); summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr); return 2
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
