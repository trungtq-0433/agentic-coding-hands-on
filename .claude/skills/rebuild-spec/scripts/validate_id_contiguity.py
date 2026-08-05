#!/usr/bin/env python3
"""Contiguity validator for rebuild-spec ID schemes.

Checks that owned scheme codes in a given artifact are exactly {001..N} with no
gaps or duplicates. Also checks REG### per-screen (screen-list) and DISC-###
globally (data-model) as warnings.

Exit codes: 0 (PASS/WARN), 1 (FAIL — any critical), 2 (internal error).
--report-only: every issue forced to severity "warning"; status never FAIL; exit always 0.
Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _id_schemes_lib import (  # noqa: E402
    ARTIFACT_OWNS,
    SCHEMES,
    find_codes,
    find_overflow_tokens,
    resolve_artifact_files,
    segment_text,
)
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, derive_overall_status, load_summary, recalculate_totals  # noqa: E402

VALIDATOR = "id_contiguity"

# Matches ## SCR### or ## SCR###_Slug headings (for REG per-screen split)
_SCR_HDR_RE = re.compile(r"^## (SCR\d{3}(?:_\S+)?)", re.MULTILINE | re.IGNORECASE)


# ---------------------------------------------------------------------------
# Issue helper
# ---------------------------------------------------------------------------

def _issue(sev: str, rid: str, file_path: str, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": None},
        "message": msg,
    }


# ---------------------------------------------------------------------------
# Per-scheme contiguity checks
# ---------------------------------------------------------------------------

def _prose_mermaid_text(text: str) -> str:
    """Return a single string containing only the prose and mermaid regions of *text*.

    Code fences (non-mermaid) are excluded so that token IDs appearing only inside
    a code fence do not create false duplicates, gaps, or overflow detections.
    """
    parts: list[str] = []
    for kind, chunk in segment_text(text):
        if kind in ("prose", "mermaid"):
            parts.append(chunk)
    return "".join(parts)


def _prose_only_text(text: str) -> str:
    """Return a single string containing only the prose regions of *text*.

    Mermaid and other code fences are excluded.  Used for duplicate detection:
    prose headings/tables are the canonical definition site; a code appearing in
    mermaid edges is a reference and must never trigger a duplicate critical.
    """
    parts: list[str] = []
    for kind, chunk in segment_text(text):
        if kind == "prose":
            parts.append(chunk)
    return "".join(parts)


def _check_global_contiguity(
    text: str,
    prefix: str,
    sep: str,
    rel_path: str,
    severity: str,
) -> list[dict]:
    """Return issues for a globally-scoped scheme (critical or warning per caller).

    All token scanning is scoped to prose + mermaid regions only (F10 mirror).
    Tokens that appear exclusively inside non-mermaid code fences are ignored
    to prevent false duplicate/gap criticals from e.g. ``# Implements US001``
    comments inside python fences.

    Duplicate detection uses PROSE regions only: mermaid occurrences are
    references (e.g. graph edges ``SCR001 --> SCR002``), not definitions.
    A code referenced multiple times in mermaid edges is normal and must NOT
    be flagged as a duplicate.  The canonical duplicate rule is:
      same code appears ≥2 times in prose regions → critical.
    """
    issues: list[dict] = []

    # Scope scanning to prose + mermaid only (H1: fence-unaware false positives)
    scoped_text = _prose_mermaid_text(text)

    # Overflow guard: 4+-digit tokens OR highest 3-digit code == 999
    overflows = find_overflow_tokens(scoped_text, prefix, sep)
    if overflows:
        issues.append(_issue(
            "critical", "contiguity.overflow", rel_path,
            f"{prefix}{sep}### scheme exceeds 3-digit ID space; "
            "renumber cannot compact — manual intervention",
        ))

    codes = find_codes(scoped_text, prefix, sep)
    if not codes:
        return issues  # vacuous — nothing to check

    nums = sorted(int(c[len(prefix) + len(sep):]) for c in codes)

    # Also flag overflow when max is exactly 999 (ceiling)
    if not overflows and nums and nums[-1] == 999:
        issues.append(_issue(
            "critical", "contiguity.overflow", rel_path,
            f"{prefix}{sep}### scheme exceeds 3-digit ID space; "
            "renumber cannot compact — manual intervention",
        ))
        return issues  # no point continuing contiguity check at ceiling

    # Duplicate detection: scan PROSE regions only.
    # Mermaid occurrences are references (graph edges etc.), never definitions.
    #
    # Reference-vs-definition rule (count headings only when heading-defined):
    # A code's canonical DEFINITION site is its markdown heading (``## SCR001``).
    # Index-table rows and cross-references (``Related Screens: SCR042``) are
    # REFERENCES, not definitions — a screen-list legitimately lists every code in
    # its Screen Index AND defines it once as a heading. Counting every prose
    # occurrence falsely flags every code as a duplicate. So: if a code appears as
    # a heading at all, its duplicate count = heading occurrences (table/bullet refs
    # ignored). If it never appears as a heading (table-defined schemes like
    # route-list / crud-matrix), fall back to all-prose counting so genuine
    # duplicate rows are still caught.
    pat = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(prefix)}{re.escape(sep)}(\d{{3}})(?![0-9])"
    )
    heading_pat = re.compile(
        rf"^#{{1,6}}\s+.*?{re.escape(prefix)}{re.escape(sep)}(\d{{3}})(?![0-9])",
        re.IGNORECASE,
    )
    prose_counts: dict[int, int] = {}
    prose_lines: dict[int, list[int]] = {}  # code_num → list of line numbers in prose
    heading_counts: dict[int, int] = {}
    heading_lines: dict[int, list[int]] = {}
    prose_line_offset = 0
    for kind, chunk in segment_text(text):
        if kind == "prose":
            for m in pat.finditer(chunk):
                n = int(m.group(1))
                prose_counts[n] = prose_counts.get(n, 0) + 1
                # Track line number of each prose occurrence (1-based from file start)
                line_in_chunk = chunk[: m.start()].count("\n")
                abs_line = prose_line_offset + line_in_chunk + 1
                prose_lines.setdefault(n, []).append(abs_line)
            for li, ln in enumerate(chunk.split("\n")):
                hm = heading_pat.match(ln)
                if hm:
                    n = int(hm.group(1))
                    heading_counts[n] = heading_counts.get(n, 0) + 1
                    heading_lines.setdefault(n, []).append(prose_line_offset + li + 1)
            prose_line_offset += chunk.count("\n")
        else:
            prose_line_offset += chunk.count("\n")

    for n, prose_count in prose_counts.items():
        hcount = heading_counts.get(n, 0)
        # Heading-defined → judge by heading count; else fall back to prose count.
        count = hcount if hcount >= 1 else prose_count
        report_lines = heading_lines.get(n) if hcount >= 1 else prose_lines.get(n)
        if count > 1:
            # Report the line of the second definition occurrence (cheaply derivable)
            second_line = report_lines[1] if report_lines and len(report_lines) >= 2 else None
            iss = _issue(
                "critical", "contiguity.duplicate", rel_path,
                f"{prefix}{sep}{n:03d} appears {count} times",
            )
            iss["location"]["line"] = second_line
            issues.append(iss)

    # Gap detection: expected 1..N
    actual = set(nums)
    expected = set(range(1, len(actual) + 1))
    for missing in sorted(expected - actual):
        issues.append(_issue(
            severity, "contiguity.gap", rel_path,
            f"{prefix}{sep}{missing:03d} missing",
        ))

    return issues


def _check_reg_per_screen(text: str, rel_path: str) -> list[dict]:
    """REG### must be contiguous 001..M within each SCR### block (warning on gap)."""
    issues: list[dict] = []

    # Fence-scope FIRST (same F10 scoping as global checks): REG tokens quoted
    # inside non-mermaid code fences must not create false gap warnings.
    text = _prose_mermaid_text(text)

    # Split text into screen blocks by ## SCR### headings
    boundaries = [(m.start(), m.group(1)) for m in _SCR_HDR_RE.finditer(text)]
    if not boundaries:
        return issues

    # Build blocks: (scr_label, block_text)
    blocks: list[tuple[str, str]] = []
    for i, (start, scr_label) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        blocks.append((scr_label, text[start:end]))

    reg_prefix, reg_sep = "REG", SCHEMES["REG"]["sep"]  # sep=""
    reg_pat = re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(reg_prefix)}{re.escape(reg_sep)}(\d{{3}})(?![0-9])"
    )

    for scr_label, block in blocks:
        nums: list[int] = [int(m.group(1)) for m in reg_pat.finditer(block)]
        if not nums:
            continue
        actual = sorted(set(nums))
        expected = list(range(1, len(actual) + 1))
        for missing in sorted(set(expected) - set(actual)):
            issues.append(_issue(
                "warning", "contiguity.gap", rel_path,
                f"REG{reg_sep}{missing:03d} missing in {scr_label} block",
            ))

    return issues


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

def validate(plan_dir: Path, artifact: str) -> dict:
    """Run contiguity checks for *artifact* and return a result dict.

    For multi-file artifacts (process-flows: artifacts/flows/*.md), codes are
    collected across ALL files in sorted-filename document order.  Zero files
    → vacuous PASS (no-op exit 0).
    """
    issues: list[dict] = []

    # Resolve artifact file(s).  process-flows → flows/*.md (multi-file);
    # all others → single artifacts/<artifact>.md.
    artifact_files = resolve_artifact_files(plan_dir, artifact)

    if not artifact_files:
        # Missing/empty → vacuous PASS
        return _build_result(issues, plan_dir)

    if artifact == "process-flows":
        # Multi-file: concatenate texts in sorted-filename order for contiguity checks.
        # rel_path covers the directory to give a useful location in issue messages.
        flows_dir = plan_dir / "artifacts" / "flows"
        rel_path = str(flows_dir)
        combined_text = "\n".join(
            f.read_text(encoding="utf-8", errors="replace") for f in artifact_files
        )
        if not combined_text.strip():
            return _build_result(issues, plan_dir)

        owned = ARTIFACT_OWNS.get(artifact, [])
        for prefix in owned:
            sep = SCHEMES[prefix]["sep"]
            issues.extend(_check_global_contiguity(combined_text, prefix, sep, rel_path, "critical"))
        return _build_result(issues, plan_dir)

    # Single-file path (all artifacts except process-flows)
    artifact_file = artifact_files[0]
    rel_path = str(artifact_file)

    text = artifact_file.read_text(encoding="utf-8", errors="replace")

    if not text.strip():
        # Empty file → vacuous PASS
        return _build_result(issues, plan_dir)

    # 1. Global schemes owned by this artifact (critical on gap/dup)
    owned = ARTIFACT_OWNS.get(artifact, [])
    for prefix in owned:
        sep = SCHEMES[prefix]["sep"]
        issues.extend(_check_global_contiguity(text, prefix, sep, rel_path, "critical"))

    # 2. REG### per-screen (only for screen-list)
    if artifact == "screen-list":
        issues.extend(_check_reg_per_screen(text, rel_path))

    # 3. DISC-### global (only for data-model) — warning
    if artifact == "data-model":
        disc_sep = SCHEMES["DISC"]["sep"]  # "-"
        issues.extend(_check_global_contiguity(text, "DISC", disc_sep, rel_path, "warning"))

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec contiguity validator")
    p.add_argument("--artifact", required=True, help="artifact name (e.g. user-stories)")
    p.add_argument("--plan-dir", required=True, help="path to plan directory")
    p.add_argument("--summary-out", default=None, help="path to validation-summary.json")
    p.add_argument("--project-root", default=None)
    p.add_argument(
        "--report-only", action="store_true",
        help="Downgrade every issue to warning; status never FAIL; exit always 0",
    )
    args = p.parse_args(argv)

    root = resolve_project_root(args.project_root)
    plan_dir = Path(args.plan_dir).resolve()

    if not plan_dir.is_dir():
        print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
        return 2

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, args.artifact)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    if args.report_only:
        # F4/incremental: downgrade every critical issue to warning; status never FAIL; exit always 0.
        for issue in result["issues"]:
            if issue["severity"] == "critical":
                issue["severity"] = "warning"
        crit_count = sum(1 for i in result["issues"] if i["severity"] == "critical")
        warn_count = sum(1 for i in result["issues"] if i["severity"] == "warning")
        result["summary"] = {"critical": crit_count, "warning": warn_count}
        result["status"] = "WARN" if warn_count else "PASS"

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

    # report-only: crit is always 0 after downgrade above → exit naturally 0.
    # Full mode: exit 1 if any criticals remain (halts pipeline).
    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
