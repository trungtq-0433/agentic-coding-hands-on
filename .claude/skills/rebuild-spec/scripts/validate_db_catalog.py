#!/usr/bin/env python3
"""Phase B DB-object catalog validator. Stdlib only.
Checks: unique name per kind, valid kind, every object cited, identifiers Markdown-safe (RT-F10).
Exit: 0 PASS/WARN, 1 critical FAIL, 2 internal error.
"""
from __future__ import annotations
import argparse, datetime as _dt, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, derive_overall_status, load_summary, recalculate_totals  # noqa: E402

VALIDATOR = "db_catalog"
VALID_KINDS = {"table", "view", "sequence", "trigger", "procedure", "package", "function", "dataset"}
SECTION_KIND_MAP = {
    "tables": "table", "views": "view",
    "stored procedures": "procedure", "procedures": "procedure",
    "sequences": "sequence", "triggers": "trigger",
    "packages": "package", "functions": "function",
    # "dataset" = flat-file/VSAM COBOL data store (Phase 06). Adding to VALID_KINDS alone
    # is not enough: a heading absent from this map maps to cur_kind=None and its rows are
    # silently dropped in _parse_catalog() below — this entry is the load-bearing half.
    "datasets": "dataset",
}
CITATION_RE = re.compile(r"\*\*Source:\*\*\s+`?[^`\n:]+:\d+", re.IGNORECASE)
TABLE_ROW_RE = re.compile(r"^\s*\|")
SEPARATOR_ROW_RE = re.compile(r"^\s*\|[\s\-|:]+\|?\s*$")


def _issue(sev, rid, fp, ln, msg):
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": fp, "line": ln}, "message": msg}


def _kind(heading: str) -> str | None:
    low = heading.lstrip("#").strip().lower()
    for key, kind in SECTION_KIND_MAP.items():
        if key in low:
            return kind
    return None


def _pipe_count(line: str) -> int:
    return sum(1 for j, ch in enumerate(line) if ch == "|" and (j == 0 or line[j - 1] != "\\"))


def _parse_catalog(lines: list[str], rel: str) -> tuple[list[dict], list[dict]]:
    """Parse section tables; detect column drift (unescaped | in identifier) via pipe-count."""
    objects: list[dict] = []
    issues: list[dict] = []
    cur_kind: str | None = None
    in_tbl = False
    hdr_pipes = 0

    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if s.startswith("## ") or s.startswith("### "):
            cur_kind = _kind(s); in_tbl = False; hdr_pipes = 0; continue
        if cur_kind is None or not TABLE_ROW_RE.match(s):
            continue
        if SEPARATOR_ROW_RE.match(s):
            in_tbl = True; continue
        if not in_tbl:
            hdr_pipes = _pipe_count(s); continue  # header row — record expected width

        # Data row: check for column drift before splitting
        row_pipes = _pipe_count(s)
        if hdr_pipes > 0 and row_pipes > hdr_pipes:
            issues.append(_issue("critical", "DbCatalog.unsafe_identifier", rel, i,
                                 f"Row has {row_pipes} '|' separators vs header {hdr_pipes} "
                                 "— unescaped '|' in identifier; escape as '\\|'"))

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells.pop(0)
        if cells and cells[-1] == "":
            cells.pop()
        if not cells:
            continue

        objects.append({"ln": i, "name": cells[0], "kind": cur_kind,
                        "src": cells[-1], "raw": line})
    return objects, issues


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    issues: list[dict] = []
    cat_path = single_file or (plan_dir / "artifacts" / "db-objects.md")
    try:
        rel = str(cat_path.relative_to(root))
    except ValueError:
        rel = str(cat_path)

    if not cat_path.is_file():
        issues.append(_issue("warning", "DbCatalog.completed_missing", rel, 0,
                             "db-objects.md not found"))
        return _build(issues, plan_dir)

    lines = cat_path.read_text(encoding="utf-8", errors="replace").splitlines()
    objects, parse_issues = _parse_catalog(lines, rel)
    issues.extend(parse_issues)

    # Guard against vacuous PASS: an empty file, or section tables missing the separator
    # row, parses to zero objects. Fail rather than silently report PASS (false confidence).
    if not objects:
        if not "\n".join(lines).strip():
            issues.append(_issue("critical", "DbCatalog.empty", rel, 0,
                                 "db-objects.md is empty — no catalog content to validate"))
        elif any(TABLE_ROW_RE.match(ln.strip()) for ln in lines):
            issues.append(_issue("critical", "DbCatalog.no_rows_parsed", rel, 0,
                                 "table-like content present but no objects parsed — "
                                 "missing separator row (|---|---|)?"))

    # (a) kind validity
    for obj in objects:
        if obj["kind"] not in VALID_KINDS:
            issues.append(_issue("critical", "DbCatalog.invalid_kind", rel, obj["ln"],
                                 f"'{obj['name']}' has invalid kind '{obj['kind']}'; "
                                 f"must be one of {sorted(VALID_KINDS)}"))

    # (b) citation present
    for obj in objects:
        if not CITATION_RE.search(obj["src"]):
            issues.append(_issue("critical", "DbCatalog.citation_missing", rel, obj["ln"],
                                 f"'{obj['name']}' (kind={obj['kind']}) missing citation "
                                 f"(**Source:** `path:line`); got: {obj['src']!r}"))

    # (c) unique per kind
    seen: dict[tuple[str, str], int] = {}
    for obj in objects:
        key = (obj["name"].upper().lstrip("\\").strip(), obj["kind"])
        if key in seen:
            issues.append(_issue("critical", "DbCatalog.duplicate_name", rel, obj["ln"],
                                 f"Duplicate '{obj['name']}' for kind '{obj['kind']}' "
                                 f"(first at line {seen[key]})"))
        else:
            seen[key] = obj["ln"]

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
    p = argparse.ArgumentParser(description="rebuild-spec Phase B DB-object catalog validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir"); g.add_argument("--db-objects-file")
    p.add_argument("--project-root", default=None); p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)
    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve(); single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir not a directory: {plan_dir}", file=sys.stderr); return 2
    else:
        single = Path(args.db_objects_file).resolve(); plan_dir = single.parent.parent
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
