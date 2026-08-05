#!/usr/bin/env python3
"""Wave 6.875 — screen-list deterministic validator.
Checks screen-list.md against 5 deterministic rules.
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

VALIDATOR = "screen_list"

# Matches wildcard route patterns in table cells and Routes/URLs bullet values.
# Scoped to table rows (|…|) and Routes/URLs bullet lines (- /path) within SCR body sections.
# Patterns: /x/* or /x/**  (one or two asterisks), :splat, /... (Remix splat)
WILDCARD_RE = re.compile(r"/\*{1,2}(\s|\||/|$)|:splat|/\.\.\.")

# Matches ## SCR001_Login, ## SCR042_Dashboard, and bare ## SCR001 (suffix optional)
# so a slug-less SCR heading is still recognised as a screen section rather than
# misclassified (its child REGs would otherwise be reported as orphan_reg).
SCR_H2_RE = re.compile(r"^## (SCR\d{3}(?:_\w+)?)", re.IGNORECASE)
# Matches SCR### codes anywhere in text (for index table scanning)
SCR_CODE_RE = re.compile(r"\b(SCR\d{3}(?:_\w+)?)\b", re.IGNORECASE)
# Matches REG### codes in table rows, incl. slug-suffixed forms (REG001_LoginForm).
# `\b` fails before `_`, so the bare `\bREG\d{3}\b` form silently misses every suffixed
# code — duplicate suffixed REGs would go undetected. Mirror SCR_CODE_RE's optional suffix.
REG_CODE_RE = re.compile(r"\b(REG\d{3}(?:_\w+)?)\b", re.IGNORECASE)


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


def validate(
    plan_dir: Path,
    root: Path,
    single_file: Path | None = None,
    screen_source: str = "route-view",
) -> dict:
    # v21.0.0 — route-decoupling: the `no_wildcard_route` check is meaningful only for stacks whose
    # screens are routed views. A `dfm-form` (Delphi) / `cobol-screen` (COBOL SCREEN SECTION + CICS
    # BMS, both flow through the same _digest_extract_cobol_screen.json) / `ui-sniff` (Track D
    # accept-path) / headless screen-list carries no Routes/URLs, so the wildcard-route check is
    # skipped (nothing to expand). Structural checks (Screen Index, SCR/REG uniqueness, orphan-REG,
    # required sections) ALWAYS run — they are stack-neutral.
    routes_expected = screen_source == "route-view"
    issues: list[dict] = []

    if single_file:
        sl_path = single_file
    else:
        sl_path = plan_dir / "artifacts" / "screen-list.md"

    rel_path = "screen-list.md"
    try:
        rel_path = str(sl_path.relative_to(root))
    except ValueError:
        rel_path = str(sl_path)

    if not sl_path.is_file():
        issues.append(_issue("warning", "ScreenList.completed_missing", rel_path, 0,
                             "screen-list.md not found"))
        return _build_result(issues, plan_dir)

    text = sl_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sections = _parse_sections(text)

    # Check: required_sections — ## Screen Index must exist
    index_sections = [s for s in sections if "screen index" in s["heading"].lower()]
    if not index_sections:
        issues.append(_issue("critical", "ScreenList.required_sections", rel_path, 1,
                             "Required section '## Screen Index' not found"))

    # Check: single_header — exactly ONE ## Screen Index section
    if len(index_sections) > 1:
        for sec in index_sections[1:]:
            issues.append(_issue("critical", "ScreenList.single_header", rel_path, sec["line_start"],
                                 "Duplicate '## Screen Index' section — possibly caused by fragment merge"))

    # Collect all ## SCR### sections — these are the "parent SCR" sections
    scr_sections: list[dict] = []
    seen_scr_codes: dict[str, int] = {}  # normalized SCR### -> first line number

    for i, line in enumerate(lines, start=1):
        m = SCR_H2_RE.match(line)
        if not m:
            continue
        scr_full = m.group(1)  # e.g. SCR001_Login
        scr_code = scr_full[:6].upper()  # normalize to SCR### prefix for dup check

        # Check: no_dup_scr
        if scr_code in seen_scr_codes:
            issues.append(_issue("critical", "ScreenList.no_dup_scr", rel_path, i,
                                 f"Duplicate SCR code '{scr_code}' "
                                 f"(first seen at line {seen_scr_codes[scr_code]})"))
        else:
            seen_scr_codes[scr_code] = i
            scr_sections.append({"scr_code": scr_code, "heading_line": i})

    defined_scr_codes = set(seen_scr_codes.keys())

    # Per-SCR-section: check REG codes
    # We need to parse body per SCR section to find REG codes and check for dups within same parent
    # Build a map: line index -> SCR section
    # Re-parse to get section bodies for SCR H2 sections
    scr_body_sections: list[dict] = []
    current_scr: dict | None = None
    for i, line in enumerate(lines, start=1):
        m = SCR_H2_RE.match(line)
        if m:
            if current_scr is not None:
                current_scr["body_lines"] = current_scr["_lines"]
                del current_scr["_lines"]
                scr_body_sections.append(current_scr)
            scr_code = m.group(1)[:6].upper()
            current_scr = {"scr_code": scr_code, "line_start": i, "_lines": []}
        elif current_scr is not None:
            if line.startswith("## "):
                # Next H2 that is NOT an SCR section ends this SCR section
                current_scr["body_lines"] = current_scr["_lines"]
                del current_scr["_lines"]
                scr_body_sections.append(current_scr)
                current_scr = None
            else:
                current_scr["_lines"].append((i, line))

    if current_scr is not None:
        current_scr["body_lines"] = current_scr["_lines"]
        del current_scr["_lines"]
        scr_body_sections.append(current_scr)

    # Check: no_wildcard_route (pass 1) — scan ALL table rows in the entire file.
    # The Screen Index table's Path/Route columns can carry wildcard patterns.
    # WILDCARD_RE requires a leading `/` before `*`, so bare asterisks in prose table cells
    # (e.g. "* required") never fire; :splat and /... are unambiguous.
    # File-wide pass covers Screen Index table AND all SCR body tables in one sweep.
    # Skipped entirely when routes are not expected (non-route-view stack — see routes_expected).
    for i, line in (enumerate(lines, start=1) if routes_expected else []):
        if not line.strip().startswith("|"):
            continue
        if WILDCARD_RE.search(line):
            issues.append(_issue("critical", "ScreenList.no_wildcard_route", rel_path, i,
                                 f"Wildcard route pattern detected in table row at line {i} — "
                                 f"expand to concrete child routes per composite-screen-detection.md "
                                 f"§ Composite Hard Guard"))

    for scr_sec in scr_body_sections:
        seen_reg_in_scr: dict[str, int] = {}
        for abs_line, line in scr_sec["body_lines"]:
            stripped = line.strip()

            # Check: no_wildcard_route (pass 2) — Routes/URLs bullet lines inside SCR bodies.
            # Table rows already covered by pass 1 above; this catches bullet-list route entries.
            # Skipped when routes are not expected (non-route-view stack).
            is_route_bullet = (
                routes_expected
                and stripped.startswith("-")
                and re.search(r"^\s*-\s+/", line)
            )
            if is_route_bullet and WILDCARD_RE.search(line):
                issues.append(_issue("critical", "ScreenList.no_wildcard_route", rel_path, abs_line,
                                     f"Wildcard route pattern detected in Routes/URLs bullet in SCR section "
                                     f"'{scr_sec['scr_code']}' at line {abs_line} — "
                                     f"expand to concrete child routes per composite-screen-detection.md "
                                     f"§ Composite Hard Guard"))

            # Only check table rows (lines starting with |) for REG dup detection
            if not stripped.startswith("|"):
                continue
            for reg_m in REG_CODE_RE.finditer(line):
                reg_code = reg_m.group(1).upper()
                if reg_code in seen_reg_in_scr:
                    issues.append(_issue("critical", "ScreenList.no_dup_reg", rel_path, abs_line,
                                         f"Duplicate REG code '{reg_code}' within SCR section "
                                         f"'{scr_sec['scr_code']}' "
                                         f"(first seen at line {seen_reg_in_scr[reg_code]})"))
                else:
                    seen_reg_in_scr[reg_code] = abs_line

    # Check: orphan_reg — every REG### must appear within a SCR section body
    # Any REG### found outside all SCR sections is an orphan
    # Collect all REG occurrences with their line numbers and whether they fall inside a SCR section
    scr_section_line_ranges: list[tuple[int, int]] = []
    for scr_sec in scr_body_sections:
        if scr_sec["body_lines"]:
            start = scr_sec["body_lines"][0][0]
            end = scr_sec["body_lines"][-1][0]
            scr_section_line_ranges.append((start, end))

    def _in_scr_section(lineno: int) -> bool:
        return any(s <= lineno <= e for s, e in scr_section_line_ranges)

    for i, line in enumerate(lines, start=1):
        if not line.strip().startswith("|"):
            continue
        for reg_m in REG_CODE_RE.finditer(line):
            reg_code = reg_m.group(1).upper()
            if not _in_scr_section(i):
                issues.append(_issue("critical", "ScreenList.orphan_reg", rel_path, i,
                                     f"REG code '{reg_code}' appears outside any ## SCR### section "
                                     f"(orphaned reference)"))

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
    p = argparse.ArgumentParser(description="rebuild-spec Wave 6.875 screen-list validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--screen-list-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    p.add_argument(
        "--screen-source",
        default="route-view",
        choices=["route-view", "dfm-form", "form-module", "cobol-screen", "ui-sniff", "none"],
        help="Profile screen_source (v21.0.0; cobol-screen/ui-sniff added in Phase 04 of the "
        "cobol-stack-and-generic-fallback plan — kept in sync with "
        "_stack_profile_lib._VALID_SCREEN_SOURCES). Non-route-view skips the route-specific "
        "no_wildcard_route check; structural checks always run. Default route-view (back-compat).",
    )
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        single = None
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
    else:
        single = Path(args.screen_list_file).resolve()
        plan_dir = single.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        if single is not None:
            print(
                f"[ERROR] {exc} — when using --screen-list-file the file must live under "
                f"<plan_dir>/artifacts/ (e.g. .../my-plan/artifacts/screen-list.md)",
                file=sys.stderr,
            )
        else:
            print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, root, single, screen_source=args.screen_source)
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
