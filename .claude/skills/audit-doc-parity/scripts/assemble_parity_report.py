#!/usr/bin/env python3
"""Step 5 — Assemble the parity report from post-adjudication verdict JSON.

Reads verdicts.json (pipeline.md § Verdict JSON contract), computes counts +
parity_score + result, and renders templates/parity-report.md.

Pure assembly — no verdicts of its own. Stdlib only.
Iron Law #3: DRIFT/FABRICATED without adjudicated=true → stderr warning (but
still rendered; the assembler never silently drops findings).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_project_root  # noqa: E402

# Verdict constants
_MATCH = "MATCH"
_DRIFT = "DRIFT"
_FABRICATED = "FABRICATED"
_MISSING = "MISSING"
_UNVERIFIABLE = "UNVERIFIABLE"

_CRITICAL_VERDICTS = {_DRIFT, _FABRICATED}
_WARNING_VERDICTS = {_MISSING, _UNVERIFIABLE}


def _atomic_write(path: Path, text: str) -> None:
    """Write text atomically via .tmp + os.replace (pattern from rebuild-spec)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _count_by_verdict(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {
        _MATCH: 0, _DRIFT: 0, _FABRICATED: 0, _MISSING: 0, _UNVERIFIABLE: 0,
    }
    for f in findings:
        v = f.get("verdict", "")
        if v in counts:
            counts[v] += 1
    return counts


def _parity_score(counts: dict[str, int]) -> float:
    """match / (match + drift + fabricated); 0.0 when denominator is 0.

    UNVERIFIABLE and MISSING are excluded from the denominator so the score
    stays honest (an undocumented behavior is not a doc lie).
    """
    denom = counts[_MATCH] + counts[_DRIFT] + counts[_FABRICATED]
    return counts[_MATCH] / denom if denom else 0.0


def _result(counts: dict[str, int]) -> str:
    """PASS iff drift == 0 and fabricated == 0, else FAIL."""
    return "PASS" if counts[_DRIFT] == 0 and counts[_FABRICATED] == 0 else "FAIL"


def _render_critical_section(criticals: list[dict]) -> str:
    if not criticals:
        return "_(none)_\n"
    lines: list[str] = []
    for i, f in enumerate(criticals, 1):
        unit = f.get("unit", "")
        field = f.get("field", "")
        verdict = f.get("verdict", "")
        doc_loc = f.get("doc_location", "")
        doc_says = f.get("doc_says", "")
        code_reality = f.get("code_reality", "")
        evidence = f.get("evidence_line", "")
        severity = f.get("severity", "critical")
        confidence = f.get("confidence", "")
        adjudicated = f.get("adjudicated", False)
        adj_str = "yes" if adjudicated else "no"

        lines.append(f"### C{i}: {unit}.{field} — {verdict}")
        lines.append(f"- **Doc**: `{doc_loc}`")
        lines.append(f'- **Doc says**: "{doc_says}"')
        lines.append(f"- **Code reality**: `{evidence}` — {code_reality}")
        lines.append(
            f"- **Verdict**: {verdict} · **Severity**: {severity} · "
            f"**Confidence**: {confidence} · **Adjudicated**: {adj_str}"
        )
        lines.append("")
    return "\n".join(lines)


def _render_warning_section(warnings: list[dict]) -> str:
    if not warnings:
        return "_(none)_\n"
    lines: list[str] = []
    for i, f in enumerate(warnings, 1):
        unit = f.get("unit", "")
        field = f.get("field", "")
        verdict = f.get("verdict", "")

        if verdict == _MISSING:
            code_reality = f.get("code_reality", "")
            evidence = f.get("evidence_line", "")
            confidence = f.get("confidence", "")
            lines.append(f"### W{i}: {unit}.{field} — MISSING")
            lines.append(f"- **Code**: `{evidence}` — {code_reality}")
            lines.append(f"- **Materiality**: (see regen finding)")
            lines.append(
                f"- **Verdict**: MISSING · **Severity**: warning · **Confidence**: {confidence}"
            )
        else:  # UNVERIFIABLE
            doc_loc = f.get("doc_location", "")
            code_reality = f.get("code_reality", "")
            lines.append(f"### W{i}: {unit}.{field} — UNVERIFIABLE")
            lines.append(f"- **Doc**: `{doc_loc}`")
            lines.append(f"- **Reason**: {code_reality}")
            lines.append(f"- **Verdict**: UNVERIFIABLE · **Severity**: warning")
        lines.append("")
    return "\n".join(lines)


def _render_match_section(matches: list[dict]) -> str:
    if not matches:
        return "_(none)_\n"
    lines: list[str] = []
    for f in matches:
        unit = f.get("unit", "")
        field = f.get("field", "")
        lines.append(f"✓ {unit}.{field}")
    return "\n".join(lines) + "\n"


def assemble(verdicts_data: dict, project_root: Path) -> str:
    """Render the parity report markdown string from verdicts data."""
    findings: list[dict] = verdicts_data.get("findings", [])
    scope: dict = verdicts_data.get("scope", {})
    project_name: str = verdicts_data.get("project", str(project_root.name))

    # Iron Law #3: warn on DRIFT/FABRICATED without adjudicated=true
    for f in findings:
        if f.get("verdict") in _CRITICAL_VERDICTS and not f.get("adjudicated", False):
            unit = f.get("unit", "?")
            field = f.get("field", "?")
            print(
                f"[WARN] {f['verdict']} finding {unit}.{field} has adjudicated!=true "
                f"(Iron Law #3 violation — rendering anyway)",
                file=sys.stderr,
            )

    counts = _count_by_verdict(findings)
    score = _parity_score(counts)
    result_str = _result(counts)

    n_features = scope.get("features", "?")
    n_claims = scope.get("claims", len(findings))
    mode = scope.get("mode", "sweep")
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    criticals = [f for f in findings if f.get("verdict") in _CRITICAL_VERDICTS]
    warnings_list = [f for f in findings if f.get("verdict") in _WARNING_VERDICTS]
    matches = [f for f in findings if f.get("verdict") == _MATCH]

    total_critical = counts[_DRIFT] + counts[_FABRICATED]
    total_warning = counts[_MISSING] + counts[_UNVERIFIABLE]

    # Frontmatter
    fm_lines = [
        "---",
        f"match: {counts[_MATCH]}",
        f"drift: {counts[_DRIFT]}          # doc claim ≠ code → CRITICAL",
        f"fabricated: {counts[_FABRICATED]}     # doc claim has no code basis → CRITICAL",
        f"missing: {counts[_MISSING]}        # documentation-worthy code absent from doc → warning",
        f"unverifiable: {counts[_UNVERIFIABLE]}   # no citation / unreadable / stale anchor / dead code → warning",
        f"parity_score: {score:.4f}",
        f"result: {result_str}",
        "---",
    ]

    # Body sections
    summary_rows = [
        "| Verdict | Count |",
        "|---------|-------|",
        f"| MATCH | {counts[_MATCH]} |",
        f"| DRIFT | {counts[_DRIFT]} |",
        f"| FABRICATED | {counts[_FABRICATED]} |",
        f"| MISSING | {counts[_MISSING]} |",
        f"| UNVERIFIABLE | {counts[_UNVERIFIABLE]} |",
        f"| **Result** | **{result_str}** |",
    ]

    metrics_rows = [
        "| Metric | Value |",
        "|--------|-------|",
        f"| Features audited | {n_features} |",
        f"| Claims checked | {n_claims} |",
        f"| Parity score | {score:.1%} |",
        f"| Critical (DRIFT+FABRICATED) | {total_critical} |",
        f"| Warnings (MISSING+UNVERIFIABLE) | {total_warning} |",
    ]

    parts = [
        "\n".join(fm_lines),
        "",
        f"# Parity Report — {project_name} docs ↔ code",
        "",
        f"**Date**: {date_str} · **Scope**: {n_features} features, {n_claims} claims checked"
        f" · **Mode**: {mode}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "\n".join(summary_rows),
        "",
        "---",
        "",
        "## Critical — Doc lies (DRIFT / FABRICATED)",
        "",
        _render_critical_section(criticals),
        "---",
        "",
        "## Warning — Coverage gaps (MISSING) / UNVERIFIABLE",
        "",
        _render_warning_section(warnings_list),
        "---",
        "",
        "## Verified (MATCH)",
        "",
        _render_match_section(matches),
        "---",
        "",
        "## Metrics",
        "",
        "\n".join(metrics_rows),
        "",
    ]

    return "\n".join(parts)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Assemble parity-report.md from post-adjudication verdict JSON"
    )
    p.add_argument("--verdicts", required=True, metavar="FILE",
                   help="Path to verdicts.json (pipeline.md § Verdict JSON contract)")
    p.add_argument("--out", required=True, metavar="FILE",
                   help="Output path for parity-report.md")
    p.add_argument("--project-root", default=None)
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)

    verdicts_path = Path(args.verdicts).resolve()
    if not verdicts_path.is_file():
        print(f"[ERROR] --verdicts file not found: {verdicts_path}", file=sys.stderr)
        return 2

    try:
        verdicts_data = json.loads(verdicts_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[ERROR] cannot load {verdicts_path}: {exc}", file=sys.stderr)
        return 2

    report_text = assemble(verdicts_data, project_root)

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(out_path, report_text)
    print(f"[assemble_parity_report] wrote → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
