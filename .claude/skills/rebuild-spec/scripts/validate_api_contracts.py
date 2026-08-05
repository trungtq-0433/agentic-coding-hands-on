#!/usr/bin/env python3
"""Wave 6.875 — api-contracts deterministic validator.
Checks api-contracts.md against the 7 deterministic rules from
verification-checklist-core-artifacts.md § ApiContracts.
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

VALIDATOR = "api_contracts"

VALID_KINDS = {"rest", "graphql", "grpc"}
CITATION_RE = re.compile(r"`[^`]+:\d+")
KIND_TAG_RE = re.compile(r"^kind:\s*(\S+)", re.MULTILINE)
CONFIDENCE_RE = re.compile(r"\[(?:EXTRACTED|INFERRED|INFERRED-from-stub)\]")


def _issue(sev: str, rid: str, file_path: str, line_num: int | None, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": line_num},
        "message": msg,
    }


def _parse_sections(text: str) -> list[dict]:
    """Split on ## H2 headings. Returns list of {heading, body, kind, line_start}."""
    sections: list[dict] = []
    lines = text.splitlines()
    current: dict | None = None

    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current is not None:
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                sections.append(current)
            current = {"heading": line.strip(), "line_start": i + 1, "kind": None, "_lines": []}
        elif current is not None:
            current["_lines"].append(line)

    if current is not None:
        current["body"] = "\n".join(current["_lines"])
        del current["_lines"]
        sections.append(current)

    for sec in sections:
        m = KIND_TAG_RE.search(sec["body"])
        if m:
            sec["kind"] = m.group(1).strip().lower()

    return sections


def _extract_entry_keys(body: str) -> list[tuple[str, int]]:
    """Extract entry Keys from ### H3 headings within a kind section."""
    keys: list[tuple[str, int]] = []
    for i, line in enumerate(body.splitlines()):
        if line.startswith("### "):
            raw = line.lstrip("# ").strip()
            keys.append((raw, i + 1))
    return keys


def _extract_shared_type_names(sections: list[dict]) -> set[str]:
    """Extract type names from the Conventions > Shared Messages / Types table."""
    names: set[str] = set()
    for sec in sections:
        if "conventions" in sec["heading"].lower():
            for line in sec["body"].splitlines():
                if line.startswith("|") and not line.startswith("|---") and not line.startswith("| Type name"):
                    cells = [c.strip() for c in line.split("|")]
                    cells = [c for c in cells if c]
                    if cells and cells[0] and not cells[0].startswith("{"):
                        names.add(cells[0])
    return names


def _check_shared_type_redefined(entry_body: str, shared_names: set[str]) -> bool:
    """Check if an entry re-defines a shared type by listing its fields in a table.

    Only flags when a shared type name appears as the SUBJECT of a definition
    (e.g., heading or bold label) immediately followed by a field-listing table.
    Bare references like "Backed by SharedType" or "see SharedType" are NOT flagged.
    """
    if not shared_names:
        return False
    lines = entry_body.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        for name in shared_names:
            is_definition_line = (
                (stripped.startswith(f"**{name}") or stripped.startswith(f"### {name}"))
                and "backed by" not in stripped.lower()
                and "see " not in stripped.lower()
                and "reference" not in stripped.lower()
            )
            if not is_definition_line:
                continue
            for subsequent in lines[i + 1:]:
                sub = subsequent.strip()
                if not sub:
                    continue
                if sub.startswith("|") and "---" not in sub:
                    cells = [c.strip() for c in sub.split("|") if c.strip()]
                    if len(cells) >= 2:
                        return True
                break
    return False


def _extract_entry_body(section_body: str, start_line: int) -> str:
    """Body text of one entry: lines after its ### heading until the next ###.

    `start_line` is the 1-indexed line of the entry's ### heading within
    section_body (as returned by _extract_entry_keys). Slicing by index avoids
    substring-collision between prefix-sharing keys (e.g. `GET /a` vs `GET /abc`).
    """
    lines = section_body.splitlines()
    entry_body_lines: list[str] = []
    for bline in lines[start_line:]:  # start_line is 1-indexed heading → slice begins after it
        if bline.startswith("### "):
            break
        entry_body_lines.append(bline)
    return "\n".join(entry_body_lines)


def _is_empty_surface(text: str) -> bool:
    return "no synchronous api surface detected" in text.lower()


def validate(plan_dir: Path, root: Path, single_file: Path | None = None) -> dict:
    issues: list[dict] = []

    if single_file:
        ac_path = single_file
    else:
        ac_path = plan_dir / "artifacts" / "api-contracts.md"

    rel_path = "api-contracts.md"
    try:
        rel_path = str(ac_path.relative_to(root))
    except ValueError:
        rel_path = str(ac_path)

    if not ac_path.is_file():
        issues.append(_issue("warning", "ApiContracts.completed_missing", rel_path, 0,
                             "api-contracts.md not found"))
        return _build_result(issues, plan_dir)

    text = ac_path.read_text(encoding="utf-8", errors="replace")
    sections = _parse_sections(text)

    conventions_found = False
    kind_sections: list[dict] = []
    total_entries = 0
    extracted_entries = 0

    for sec in sections:
        if "conventions" in sec["heading"].lower():
            conventions_found = True
        if sec["kind"] in VALID_KINDS:
            kind_sections.append(sec)

    # Check 1: section_present
    if not conventions_found and not _is_empty_surface(text):
        issues.append(_issue("critical", "ApiContracts.section_present", rel_path, 1,
                             "Conventions section missing from non-empty api-contracts.md"))

    if not kind_sections and not _is_empty_surface(text):
        issues.append(_issue("critical", "ApiContracts.section_present", rel_path, 1,
                             "No kind section (kind: rest/graphql/grpc) found in non-empty api-contracts.md"))

    # Check 2: kind_tag_valid
    for sec in sections:
        if sec["kind"] is not None and sec["kind"] not in VALID_KINDS:
            issues.append(_issue("critical", "ApiContracts.kind_tag_valid", rel_path, sec["line_start"],
                                 f"Invalid kind tag '{sec['kind']}'; valid values: rest, graphql, grpc"))

    # Check 3-5: per-kind section checks
    shared_names = _extract_shared_type_names(sections)
    all_keys_by_kind: dict[str, list[str]] = {}

    for sec in kind_sections:
        kind = sec["kind"]
        entries = _extract_entry_keys(sec["body"])
        entry_keys = all_keys_by_kind.setdefault(kind, [])

        for key_text, rel_line in entries:
            total_entries += 1
            abs_line = sec["line_start"] + rel_line

            entry_body = _extract_entry_body(sec["body"], rel_line)

            # Check 3: citation_missing — require actual `file:line` pattern
            has_citation = bool(CITATION_RE.search(entry_body))
            if not has_citation:
                issues.append(_issue("critical", "ApiContracts.citation_missing", rel_path, abs_line,
                                     f"Entry '{key_text}' has no Source: file:line citation"))

            # Track confidence for %EXTRACTED metric
            if "[EXTRACTED]" in key_text:
                extracted_entries += 1
            elif CONFIDENCE_RE.search(entry_body):
                if "EXTRACTED" in (CONFIDENCE_RE.search(entry_body).group()):
                    extracted_entries += 1

            # Check 4: duplicate_key
            normalized_key = key_text.split("---")[0].strip() if "---" in key_text else key_text
            if normalized_key in entry_keys:
                issues.append(_issue("critical", "ApiContracts.duplicate_key", rel_path, abs_line,
                                     f"Duplicate entry key '{normalized_key}' within kind:{kind}"))
            entry_keys.append(normalized_key)

            # Check 5: shared_type_redefined
            if _check_shared_type_redefined(entry_body, shared_names):
                issues.append(_issue("warning", "ApiContracts.shared_type_redefined", rel_path, abs_line,
                                     f"Entry '{key_text}' re-defines fields of a shared type from Conventions (DRY violation)"))

    # Check 6: completed_missing
    if not single_file:
        completed_marker = plan_dir / "artifacts" / ".api-contracts.completed"
        if not completed_marker.exists():
            issues.append(_issue("warning", "ApiContracts.completed_missing", rel_path, 0,
                                 ".api-contracts.completed marker not found"))

    # Check 7: empty_surface
    if _is_empty_surface(text) and total_entries == 0:
        issues.append(_issue("warning", "ApiContracts.empty_surface", rel_path, 1,
                             "Empty API surface detected (no entries); expected for library/CLI projects"))
    elif total_entries == 0 and kind_sections and not _is_empty_surface(text):
        issues.append(_issue("critical", "ApiContracts.section_present", rel_path, 1,
                             "Kind sections present but contain zero entries — malformed"))

    pct = round(extracted_entries / total_entries * 100, 1) if total_entries > 0 else 0.0
    return _build_result(issues, plan_dir, total_entries, extracted_entries, pct)


def _build_result(
    issues: list[dict],
    plan_dir: Path,
    total: int = 0,
    extracted: int = 0,
    pct: float = 0.0,
) -> dict:
    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_dir": str(plan_dir),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
        "metrics": {"total": total, "extracted": extracted, "pct_extracted": pct},
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 api-contracts validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--api-contracts-file")
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
        single = Path(args.api_contracts_file).resolve()
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
    metrics = result.get("metrics", {})
    print(f"[METRIC] %EXTRACTED = {metrics.get('extracted', 0)}/{metrics.get('total', 0)} ({metrics.get('pct_extracted', 0)}%)")
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
                "metrics": result["metrics"],
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
