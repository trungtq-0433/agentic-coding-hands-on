#!/usr/bin/env python3
"""Wave J.2 — job-list deterministic validator.
Checks job-list.md against jobs-researcher-contract.md rules.
Regex + section parsing; stdlib only.
Exit codes: 0 (no critical), 1 (critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, strip_comments, split_table_row, mask_fenced  # noqa: E402
from _nav_table_parse_lib import data_rows  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, load_summary, recalculate_totals, derive_overall_status  # noqa: E402
from _credential_scrub_lib import assert_no_secrets  # noqa: E402

VALIDATOR = "job_list"

JOB_CODE_RE = re.compile(r"^JOB\d{3}_[A-Za-z0-9]+$")
JOB_H2_RE = re.compile(r"^## (JOB\d{3}(?:_\w+)?)")
# I7: reused to locate the `## Job Index` heading whose table is diffed against `## JOB###`
# sections below it.
JOB_INDEX_HEADING_RE = re.compile(r"^#+\s*Job Index\s*$", re.IGNORECASE)
# Captures the FULL rest of the `**BL Ref**:` line (not just the first token) so the
# multi-ref minor fix below can validate every comma/space-separated ref, not just the first.
BL_REF_LINE_RE = re.compile(r"\*\*BL Ref\*\*:\s*(.+)", re.IGNORECASE)
SOURCE_RE = re.compile(r"\*\*Source\*\*:\s*`?([^`\n]+):(\d+)", re.IGNORECASE)
BL_CODE_RE = re.compile(r"^BL\d{3}(?:_\w+)?$")
BL_H2_RE = re.compile(r"^## (BL\d{3})(?:_\w+)?\b", re.IGNORECASE | re.MULTILINE)
# C2 reverse-coverage WARN: full BL### heading (with slug) + its **Type** field.
BL_H2_FULL_RE = re.compile(r"^## (BL\d{3}(?:_\w+)?)", re.IGNORECASE)
BL_TYPE_RE = re.compile(r"\*\*Type\*\*:\s*([A-Za-z0-9_-]+)", re.IGNORECASE)
# Behavior Logic types whose canonical shape is job-like (see
# references/bl-source-patterns.md canonical 10 + templates/behavior-logic-template.md).
# "Qualifying" is deliberately narrow to the machine-readable **Type** marker — no attempt
# is made to infer job-ness from prose (see phase-03 report for the precision discussion).
QUALIFYING_BL_TYPES = {"scheduled-job", "queue-worker", "custom-command"}


def _issue(sev: str, rid: str, file_path: str, line_num: int | None, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": line_num},
        "message": msg,
    }


def _parse_h2_sections(text: str, heading_re: re.Pattern, code_key: str) -> list[dict]:
    """Generic `## <CODE>...` section splitter: fence + comment aware.

    I1 fix: `text` must be comment-stripped by the caller (kills e.g. the job-list-
    template's HTML-comment "DELETE BEFORE SUBMITTING" worked-example appendix outright),
    and BOTH the opening heading match AND the generic `## `-section-close check are gated
    on `in_fence is False` — a fenced illustrative `## JOB999_FakeExample` line (shown
    inside a real section's example config) can no longer be parsed as a new section, nor
    prematurely close the section whose body it appears in.

    Shared by `_parse_job_sections` (JOB###) and `_parse_bl_sections` (BL###, for the C2
    reverse-coverage WARN) — the two heading shapes only differ in `heading_re`/`code_key`.
    """
    sections: list[dict] = []
    current: dict | None = None
    for lineno, line, in_fence in iter_lines_with_fence(text):
        m = heading_re.match(line) if not in_fence else None
        if m:
            if current is not None:
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                sections.append(current)
            current = {
                code_key: m.group(1),
                "heading": line.strip(),
                "line_start": lineno,
                "_lines": [],
            }
        elif current is not None:
            if not in_fence and line.startswith("## "):
                current["body"] = "\n".join(current["_lines"])
                del current["_lines"]
                sections.append(current)
                current = None
            else:
                current["_lines"].append(line)
    if current is not None:
        current["body"] = "\n".join(current["_lines"])
        del current["_lines"]
        sections.append(current)
    return sections


def _parse_job_sections(text: str) -> list[dict]:
    """Extract JOB### sections with heading line + body text. See `_parse_h2_sections`."""
    return _parse_h2_sections(strip_comments(text), JOB_H2_RE, "job_code_raw")


def _parse_bl_sections(text: str) -> list[dict]:
    """Extract BL### sections with heading line + body text (C2 reverse-coverage WARN).

    See `_parse_h2_sections`.
    """
    return _parse_h2_sections(strip_comments(text), BL_H2_FULL_RE, "bl_code_raw")


def _find_index_table(text: str) -> list[str] | None:
    """Return the raw `|`-prefixed lines of the table under `## Job Index`, or None.

    Fence-aware via `mask_fenced` — a fenced illustrative Job Index table is invisible, so
    it neither triggers this heading match nor gets parsed as the real index. Absent
    heading or absent table both degrade to None (I7: skip parity check silently)."""
    lines = mask_fenced(text).splitlines()
    start = None
    for i, ln in enumerate(lines):
        if JOB_INDEX_HEADING_RE.match(ln.strip()):
            start = i + 1
            break
    if start is None:
        return None
    table: list[str] = []
    seen_row = False
    for ln in lines[start:]:
        stripped = ln.strip()
        if stripped.startswith("|"):
            table.append(stripped)
            seen_row = True
        elif seen_row:
            break
    return table or None


def _parse_index_codes(table: list[str]) -> set[str]:
    """Extract the set of `JOB###` codes from the first column of a Job Index table."""
    header = [h.casefold() for h in split_table_row(table[0])] if table else []
    code_idx = next((i for i, h in enumerate(header) if "code" in h), 0)
    codes: set[str] = set()
    for raw in data_rows(table):
        cells = split_table_row(raw)
        if code_idx >= len(cells):
            continue
        code = cells[code_idx].strip()
        if not code or code.startswith("{"):
            continue
        m = re.match(r"^(JOB\d{3})", code, re.IGNORECASE)
        if m:
            codes.add(m.group(1).upper())
    return codes


def validate(job_path: Path, root: Path, behavior_logic_path: Path | None = None) -> dict:
    issues: list[dict] = []
    try:
        rel_path = str(job_path.relative_to(root))
    except ValueError:
        rel_path = str(job_path)

    if not job_path.is_file():
        issues.append(_issue("warning", "JobList.completed_missing", rel_path, 0,
                             "job-list.md not found"))
        return _build_result(issues)

    text = job_path.read_text(encoding="utf-8", errors="replace")

    # F6 — hard CRITICAL secrets gate over the promoted job-list output.
    for warn_msg in assert_no_secrets(text):
        issues.append(_issue("critical", "JobList.secret_leak", rel_path, 0, warn_msg))

    known_bl = None
    bl_text: str | None = None
    if behavior_logic_path is not None and behavior_logic_path.is_file():
        try:
            bl_text = behavior_logic_path.read_text(encoding="utf-8", errors="replace")
            known_bl = {m.group(1).upper() for m in BL_H2_RE.finditer(bl_text)}
        except OSError:
            known_bl = None
            bl_text = None

    sections = _parse_job_sections(text)
    seen_codes: dict[str, int] = {}
    referenced_bl: set[str] = set()  # every well-formed BL### a JOB### resolves — C2 reverse WARN

    for sec in sections:
        job_code_raw = sec["job_code_raw"]
        line_start = sec["line_start"]
        body = sec["body"]

        if not JOB_CODE_RE.match(job_code_raw):  # full JOB###_NameSlug shape required
            issues.append(_issue("critical", "JobList.code_format", rel_path, line_start,
                                 f"Job heading '{job_code_raw}' does not match ^JOB\\d{{3}}_[A-Za-z0-9]+$"))

        job_num = job_code_raw[:6].upper() if len(job_code_raw) >= 6 else job_code_raw.upper()
        if job_num in seen_codes:
            issues.append(_issue("critical", "JobList.no_dup_job", rel_path, line_start,
                                 f"Duplicate job code '{job_num}' (first seen at line {seen_codes[job_num]})"))
        else:
            seen_codes[job_num] = line_start

        if not SOURCE_RE.search(body):  # anti-hallucination citation presence
            issues.append(_issue("critical", "JobList.source_missing", rel_path, line_start,
                                 f"Job '{job_code_raw}' missing '**Source**: `file:line`' citation"))

        bl_match = BL_REF_LINE_RE.search(body)  # BL Ref presence + shape + best-effort resolution
        # Minor fix: the field may list multiple comma/space-separated refs
        # (`BL001, BL002`) — validate every token, not just the first.
        tokens = (
            [t.strip().rstrip(".,;") for t in re.split(r"[,\s]+", bl_match.group(1).strip())
             if t.strip(" .,;")]
            if bl_match else []
        )
        if not tokens:
            issues.append(_issue("critical", "JobList.bl_ref_missing", rel_path, line_start,
                                 f"Job '{job_code_raw}' missing '**BL Ref**: BL###' field"))
        else:
            for bl_ref in tokens:
                if not BL_CODE_RE.match(bl_ref):
                    issues.append(_issue("critical", "JobList.bl_ref_format", rel_path, line_start,
                                         f"Job '{job_code_raw}' BL Ref '{bl_ref}' does not match ^BL\\d{{3}}(_\\w+)?$"))
                    continue
                bl_num = bl_ref[:5].upper()
                referenced_bl.add(bl_num)
                if known_bl is not None and bl_num not in known_bl:
                    issues.append(_issue("critical", "JobList.bl_ref_unresolved", rel_path, line_start,
                                         f"Job '{job_code_raw}' BL Ref '{bl_ref}' not found in behavior-logic.md"))

    # I7 — Job Index table ↔ `## JOB###` section parity. Absent index table degrades to a
    # silent skip (not every job-list.md variant carries one).
    index_table = _find_index_table(text)
    if index_table is not None:
        index_codes = _parse_index_codes(index_table)
        section_codes = set(seen_codes.keys())
        for code in sorted(index_codes - section_codes):
            issues.append(_issue("warning", "JobList.index_drift", rel_path, 0,
                                 f"Job Index lists '{code}' but no matching '## {code}' section exists"))
        for code in sorted(section_codes - index_codes):
            issues.append(_issue("warning", "JobList.index_drift", rel_path, 0,
                                 f"Job section '{code}' exists but is missing from the '## Job Index' table"))

    # C2 — reverse coverage: a qualifying (job-type) BL### with no JOB### referencing it via
    # **BL Ref** is a WARN, never a critical (an unimplemented/skipped job is a legitimate
    # authoring choice, not a corruption of job-list.md itself).
    if bl_text is not None:
        for bl_sec in _parse_bl_sections(bl_text):
            type_match = BL_TYPE_RE.search(bl_sec.get("body", ""))
            if not type_match:
                continue  # no machine-readable **Type** marker — cannot judge qualification
            bl_type = type_match.group(1).strip().lower()
            if bl_type not in QUALIFYING_BL_TYPES:
                continue
            bl_code_num = bl_sec["bl_code_raw"][:5].upper()
            if bl_code_num not in referenced_bl:
                issues.append(_issue(
                    "warning", "JobList.bl_uncovered", rel_path, 0,
                    f"behavior-logic.md '{bl_sec['bl_code_raw']}' (Type={bl_type}) has no "
                    "corresponding JOB### section referencing it via '**BL Ref**'",
                ))

    return _build_result(issues)


def _build_result(issues: list[dict]) -> dict:
    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave J.2 job-list validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--job-list-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    p.add_argument("--behavior-logic-file", default=None,
                   help="Optional docs/generated/behavior-logic.md path for BL Ref resolution")
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
        job_path = plan_dir / "artifacts" / "job-list.md"
    else:
        job_path = Path(args.job_list_file).resolve()
        plan_dir = job_path.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    bl_path = Path(args.behavior_logic_file).resolve() if args.behavior_logic_file else \
        (root / "docs" / "generated" / "behavior-logic.md")

    try:
        result = validate(job_path, root, bl_path)
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
