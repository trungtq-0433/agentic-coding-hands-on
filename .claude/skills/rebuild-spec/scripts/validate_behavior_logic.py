#!/usr/bin/env python3
"""Wave 6.875 — behavior-logic deterministic validator.
Checks behavior-logic.md against 6 deterministic rules.
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
from _file_schema_lib import has_populated_file_schema, is_file_exchange  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, load_summary, recalculate_totals, derive_overall_status  # noqa: E402

VALIDATOR = "behavior_logic"

# Matches ## BL001_DoSomething, ## BL042, etc.
BL_H2_RE = re.compile(r"^## (BL\d{3}(?:_\w+)?)", re.IGNORECASE)
# Matches **Source File** label — with or without trailing colon/content.
# Anchored to the bold-label open only; closing ** may not exist when value is on the same line.
SOURCE_FILE_RE = re.compile(r"\*\*Source File", re.IGNORECASE)
# Matches **Source Symbol** label — same rationale as SOURCE_FILE_RE.
SOURCE_SYMBOL_RE = re.compile(r"\*\*Source Symbol", re.IGNORECASE)
# Matches **Type**: <value> — used to gate the file_schema_missing rule to the BL types
# that plausibly exchange files (reduces noise on e.g. middleware/observer types).
TYPE_FIELD_RE = re.compile(r"^\*\*Type\*\*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
FILE_EXCHANGE_BL_TYPES = {"queue-worker", "custom-command", "integration"}


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


def _parse_bl_sections(text: str) -> list[dict]:
    """Extract BL### sections with their body text and heading line numbers."""
    bl_sections: list[dict] = []
    lines = text.splitlines()
    current: dict | None = None

    for i, line in enumerate(lines):
        m = BL_H2_RE.match(line)
        if m:
            # Start of a new BL### section — close the previous one first
            if current is not None:
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                bl_sections.append(current)
            bl_code = m.group(1)[:5].upper()  # normalize to BL### prefix (e.g. BL001)
            current = {
                "bl_code": bl_code,
                "heading": line.strip(),
                "line_start": i + 1,
                "_lines": [],
            }
        elif current is not None:
            # Any non-BL ## heading closes the current BL section
            if line.startswith("## "):
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                bl_sections.append(current)
                current = None
            else:
                current["_lines"].append(line)

    if current is not None:
        current["body"] = "\n".join(current["_lines"])
        del current["_lines"]
        bl_sections.append(current)

    return bl_sections


def validate(
    plan_dir: Path,
    root: Path,
    single_file: Path | None = None,
    scout_bl_inventory: Path | None = None,
) -> dict:
    issues: list[dict] = []

    if single_file:
        bl_path = single_file
    else:
        bl_path = plan_dir / "artifacts" / "behavior-logic.md"

    rel_path = "behavior-logic.md"
    try:
        rel_path = str(bl_path.relative_to(root))
    except ValueError:
        rel_path = str(bl_path)

    if not bl_path.is_file():
        issues.append(_issue("warning", "BehaviorLogic.completed_missing", rel_path, 0,
                             "behavior-logic.md not found"))
        return _build_result(issues, plan_dir)

    text = bl_path.read_text(encoding="utf-8", errors="replace")
    sections = _parse_sections(text)

    # Check: required_sections — ## Behavior Logic Index must exist
    index_sections = [s for s in sections if "behavior logic index" in s["heading"].lower()]
    if not index_sections:
        issues.append(_issue("critical", "BehaviorLogic.required_sections", rel_path, 1,
                             "Required section '## Behavior Logic Index' not found"))

    # Check: single_header — exactly ONE ## Behavior Logic Index section
    if len(index_sections) > 1:
        for sec in index_sections[1:]:
            issues.append(_issue("critical", "BehaviorLogic.single_header", rel_path, sec["line_start"],
                                 "Duplicate '## Behavior Logic Index' section — possibly caused by fragment merge"))

    # Parse BL### sections
    bl_sections = _parse_bl_sections(text)

    seen_bl_codes: dict[str, int] = {}  # BL### -> first line number

    for bl_sec in bl_sections:
        bl_code = bl_sec["bl_code"]
        line_start = bl_sec["line_start"]

        # Check: no_dup_bl
        if bl_code in seen_bl_codes:
            issues.append(_issue("critical", "BehaviorLogic.no_dup_bl", rel_path, line_start,
                                 f"Duplicate BL code '{bl_code}' "
                                 f"(first seen at line {seen_bl_codes[bl_code]})"))
        else:
            seen_bl_codes[bl_code] = line_start

        # Check: source_present — body must contain **Source File** and **Source Symbol**
        body = bl_sec["body"]
        has_source_file = bool(SOURCE_FILE_RE.search(body))
        has_source_symbol = bool(SOURCE_SYMBOL_RE.search(body))

        if not has_source_file:
            issues.append(_issue("critical", "BehaviorLogic.source_present", rel_path, line_start,
                                 f"BL section '{bl_code}' missing '**Source File**' field"))
        if not has_source_symbol:
            issues.append(_issue("critical", "BehaviorLogic.source_present", rel_path, line_start,
                                 f"BL section '{bl_code}' missing '**Source Symbol**' field"))

        # Check: file_schema_missing — file-exchange BL types without a populated
        # **File Schema** table. Gate on Type to reduce noise on types that would never
        # exchange a file (e.g. middleware/observer). N/A-misuse on a vocab-matching
        # block is also treated as "not populated" by has_populated_file_schema().
        type_match = TYPE_FIELD_RE.search(body)
        bl_type = type_match.group(1).strip().lower() if type_match else ""
        heading_and_body = bl_sec["heading"] + "\n" + body
        if (bl_type in FILE_EXCHANGE_BL_TYPES
                and is_file_exchange(heading_and_body)
                and not has_populated_file_schema(body)):
            issues.append(_issue("warning", "BehaviorLogic.file_schema_missing", rel_path, line_start,
                                 f"BL section '{bl_code}' (type: {bl_type}) matches file-exchange "
                                 f"vocabulary but has no populated '**File Schema**' table"))

    # Check: cardinality — if scout inventory provided, warn on mismatch
    if scout_bl_inventory is not None and scout_bl_inventory.is_file():
        try:
            inventory_text = scout_bl_inventory.read_text(encoding="utf-8", errors="replace")
            # Count non-empty, non-header lines that look like inventory entries
            # Accept simple line-based format or CSV: one entry per line
            inventory_entries = [
                ln.strip() for ln in inventory_text.splitlines()
                if ln.strip() and not ln.startswith("#") and not ln.startswith("//")
            ]
            inventory_count = len(inventory_entries)
            doc_count = len(bl_sections)
            if inventory_count != doc_count:
                issues.append(_issue("warning", "BehaviorLogic.cardinality", rel_path, 0,
                                     f"BL count mismatch: scout inventory has {inventory_count} "
                                     f"entries but document has {doc_count} BL sections"))
        except OSError as exc:
            issues.append(_issue("warning", "BehaviorLogic.cardinality", rel_path, 0,
                                 f"Could not read scout BL inventory: {exc}"))

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
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 behavior-logic validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--behavior-logic-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    p.add_argument("--scout-bl-inventory", default=None,
                   help="Optional path to scout BL inventory file for cardinality check")
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
    else:
        single = Path(args.behavior_logic_file).resolve()
        plan_dir = single.parent.parent

    scout_inv = Path(args.scout_bl_inventory).resolve() if args.scout_bl_inventory else None

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, root, single, scout_inv)
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
