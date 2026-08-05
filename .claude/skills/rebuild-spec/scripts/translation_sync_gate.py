#!/usr/bin/env python3
"""translation_sync_gate.py — Two-mode gate for translation auto-sync.

--mode plan      : read .rebuild-state.json, emit worklist JSON to stdout
--mode finalize  : verify promoted dirs, write cursors + report, print handoff line
--mode summarize : read existing report, print canonical "Secondary languages:" line

Exit codes: 0 (ok), 2 (internal error).  finalize always exits 0 (records reality).
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write  # noqa: E402
from _translation_sync_lib import (  # noqa: E402
    compute_finalize_result,
    compute_plan_worklist,
    load_state,
    parse_lang_statuses,
    render_handoff,
    summarize_from_report,
)


def _guard_state(path: Path, project_root: Path) -> dict | None:
    """Load + path-guard state file; print error and return None on failure."""
    try:
        assert_under(path.parent, project_root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return None
    try:
        return load_state(path)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return None


def _run_plan(args: argparse.Namespace, project_root: Path) -> int:
    state_path = Path(args.state).resolve()
    state = _guard_state(state_path, project_root)
    if state is None:
        return 2

    stale_file = (Path(args.plan_dir) / "artifacts" / "translation-stale.json") if args.plan_dir else None
    primary_root = Path(args.primary_docs_root).resolve()

    worklist = compute_plan_worklist(state, args.pass_name, primary_root, stale_file)
    print(json.dumps(worklist, indent=2, sort_keys=True))
    return 0


def _run_finalize(args: argparse.Namespace, project_root: Path) -> int:
    state_path = Path(args.state).resolve()
    state = _guard_state(state_path, project_root)
    if state is None:
        return 2

    if args.report_out:
        report_path = Path(args.report_out).resolve()
    elif args.plan_dir:
        report_path = (Path(args.plan_dir) / "artifacts" / "translation-sync-report.json").resolve()
    else:
        print("[ERROR] --report-out or --plan-dir required for finalize", file=sys.stderr)
        return 2

    try:
        assert_under(report_path.parent, project_root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    primary_root = Path(args.primary_docs_root).resolve()
    lang_statuses = parse_lang_statuses(args.lang_status or [])

    updated_state, report = compute_finalize_result(
        state, args.pass_name, primary_root, lang_statuses
    )

    # (b+c) Atomic writes — state cursor then report
    atomic_write(state_path, updated_state)
    atomic_write(report_path, report)

    # (d) Canonical handoff line LAST — LLM echoes verbatim
    print(f"Secondary languages: {render_handoff(report)}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Translation sync gate (plan / finalize / summarize)")
    p.add_argument("--mode", required=True, choices=["plan", "finalize", "summarize"])
    p.add_argument("--pass", dest="pass_name", default=None, metavar="PASS",
                   help="Pass name, required for plan/finalize")
    p.add_argument("--plan-dir", default=None,
                   help="Active plan dir (stale file source + default report output)")
    p.add_argument("--state", default="docs/.rebuild-state.json")
    p.add_argument("--primary-docs-root", default="docs")
    p.add_argument("--report-out", default=None,
                   help="Explicit report output path (overrides --plan-dir default)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--lang-status", action="append", default=[],
                   metavar="LANG:STATUS[:REASON]",
                   help="Per-lang outcome, repeatable. finalize mode only.")
    return p


def main(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)

    if args.mode in ("plan", "finalize") and not args.pass_name:
        print(f"[ERROR] --pass is required for --mode {args.mode}", file=sys.stderr)
        return 2

    project_root = resolve_project_root(args.project_root)

    try:
        if args.mode == "plan":
            return _run_plan(args, project_root)
        if args.mode == "finalize":
            return _run_finalize(args, project_root)
        # summarize — read existing report, print handoff
        rp = (Path(args.report_out).resolve() if args.report_out
              else (Path(args.plan_dir) / "artifacts" / "translation-sync-report.json").resolve()
              if args.plan_dir else None)
        if rp is None:
            print("[ERROR] --report-out or --plan-dir required for summarize", file=sys.stderr)
            return 2
        print(f"Secondary languages: {summarize_from_report(rp)}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] translation_sync_gate crashed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
