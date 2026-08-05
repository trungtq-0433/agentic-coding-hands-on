#!/usr/bin/env python3
"""Wave D.2 — design-intent mode-agnostic citation-density gate (F11c).

The `--design-intent` pass (B5, v26.1.0, EXPERIMENTAL) synthesizes inferred "why built this
way" narrative — the highest-hallucination-risk artifact in the kit. Every claim must carry an
ADR / business-rules.md / architecture.md / business-context.md / file:line citation, OR be
tagged `[INFERRED]` with reasoning — never asserted as bare fact.

NEW validator, NOT a reuse of `re-output-contract.md`'s density check: that check is gated on
`profile.re_contract` (RE-mode only) and never fires for a normal `--design-intent` run. This
script is mode-agnostic — always runs, regardless of profile. Modelled on `verify_overview.py`'s
deterministic-scan PATTERN (regex classes, fence-skip, exit-code contract), flagging a different
shape: asserted-as-fact paragraphs with zero citation evidence.

Stdlib only. Exit codes: 0 (no critical), 1 (critical found), 2 (usage/IO/internal error).
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

VALIDATOR = "design_intent_density"

# A paragraph counts as "cited" if it references ANY of the researcher contract's authorized
# source classes, or carries the [INFERRED] tag. Generic, project-agnostic (mirrors
# verify_overview.py's stance: no hardcoded per-project vocabulary).
_ADR_RE = re.compile(r"\bADR-\d+\b|docs/decisions/ADR", re.IGNORECASE)
_DOC_CITATION_RE = re.compile(
    r"\b(architecture|business-rules|business-context)\.md\b", re.IGNORECASE)
_FILE_LINE_RE = re.compile(
    r"\b[\w/.-]+\.(rb|rake|erb|py|tsx|ts|jsx|js|mjs|cjs|vue|yml|yaml|"
    r"kt|kts|swift|java|scala|go|rs|m|mm|cs|php|c|cc|cpp|h|hpp|dart|ex|exs|"
    # I6: Delphi/Oracle legacy-stack extensions so legit citations there aren't read as uncited.
    r"pas|dpr|dfm|sql|pks|pkb|pls):\d+\b")
_INFERRED_RE = re.compile(r"\[INFERRED\]")
# `{...}` spans are unfilled template placeholders (scaffold drafts) -- their content is
# authoring instructions, not an asserted-as-fact claim. Parity with derive_confidence_report's
# PLACEHOLDER_RE: strip before the word-count/citation check so unfilled scaffold guidance
# text is never flagged as an uncited assertion (minor finding, PR #176 phase-01).
_PLACEHOLDER_RE = re.compile(r"\{[^{}\n]*\}")

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_DISCLAIMER_START_RE = re.compile(r"<!--\s*disclaimer:start\s*-->", re.IGNORECASE)
_DISCLAIMER_END_RE = re.compile(r"<!--\s*disclaimer:end\s*-->", re.IGNORECASE)
_HEADING_RE = re.compile(r"^\s*#")
_TABLE_ROW_RE = re.compile(r"^\s*\|")
_RULE_RE = re.compile(r"^\s*(-{3,}|\*{3,})\s*$")

# Short paragraphs (labels, transitions) are excluded — the gate targets sweeping assertions.
MIN_WORDS = 12


def _is_cited(paragraph: str) -> bool:
    return bool(
        _ADR_RE.search(paragraph)
        or _DOC_CITATION_RE.search(paragraph)
        or _FILE_LINE_RE.search(paragraph)
        or _INFERRED_RE.search(paragraph)
    )


def _iter_paragraphs(text: str):
    """Yield (start_lineno, paragraph_text) for prose blocks only.

    Skips fenced code, the disclaimer banner (F11a — deliberately citation-free), headings,
    table rows, and horizontal rules. A paragraph is a run of contiguous plain-prose lines.
    """
    in_fence = in_disclaimer = False
    buf: list[str] = []
    start = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            skip = True
        elif in_fence:
            skip = True
        elif _DISCLAIMER_START_RE.search(line):
            in_disclaimer = True
            skip = True
        elif _DISCLAIMER_END_RE.search(line):
            in_disclaimer = False
            skip = True
        elif in_disclaimer:
            skip = True
        else:
            skip = (not line.strip() or _HEADING_RE.match(line)
                    or _TABLE_ROW_RE.match(line) or _RULE_RE.match(line))
        if skip:
            if buf:
                yield (start, "\n".join(buf))
                buf = []
            continue
        if not buf:
            start = lineno
        buf.append(line)
    if buf:
        yield (start, "\n".join(buf))


def _issue(rid: str, line_num: int, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": "critical",
        "rule_id": rid,
        "location": {"file": "design-intent.md", "line": line_num},
        "message": msg,
    }


def validate(design_intent_path: Path) -> dict:
    if not design_intent_path.is_file():
        return _build_result([{
            "validator": VALIDATOR, "severity": "warning", "rule_id": "DesignIntent.file_missing",
            "location": {"file": "design-intent.md", "line": 0}, "message": "design-intent.md not found",
        }])

    issues: list[dict] = []
    text = design_intent_path.read_text(encoding="utf-8", errors="replace")
    for start_line, para in _iter_paragraphs(text):
        scan_para = _PLACEHOLDER_RE.sub("", para)
        if len(scan_para.split()) < MIN_WORDS or _is_cited(scan_para):
            continue
        snippet = para.strip().splitlines()[0][:120]
        issues.append(_issue(
            "DesignIntent.uncited_assertion", start_line,
            f"Asserted-as-fact paragraph with 0 citations and no [INFERRED] tag: {snippet!r}"
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
    p = argparse.ArgumentParser(description="rebuild-spec Wave D.2 design-intent density validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--design-intent-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
        di_path = plan_dir / "artifacts" / "design-intent.md"
    else:
        di_path = Path(args.design_intent_file).resolve()
        plan_dir = di_path.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(di_path)
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
