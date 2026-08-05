#!/usr/bin/env python3
"""Translation sync completion gate — blocks pass completion when secondary langs are stale.

Sibling to check_promotion_gate.py. Different inputs: per-pass lang-cursor state vs feature files.
Exit codes: 0 (pass), 1 (fail — stale/missing), 2 (internal error).
Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write,
    derive_overall_status,
    load_summary,
    recalculate_totals,
)
from _translation_sync_lib import is_stale, secondary_langs  # noqa: E402

VALIDATOR = "translation_gate"

_FIX_MSG = (
    "Re-run the pass to trigger auto-sync, "
    "or sync each stale lang manually with /tkm:rebuild-spec --lang <code>."
)


def _issue(severity: str, rule_id: str, file_: str, message: str) -> dict:
    return {
        "severity": severity,
        "rule_id": rule_id,
        "location": {"file": file_, "line": None},
        "message": message,
    }


def _load_state(plan_dir: Path) -> dict:
    """Walk up from plan_dir to find docs/.rebuild-state.json (up to 5 levels)."""
    node = plan_dir
    for _ in range(5):
        p = node / "docs" / ".rebuild-state.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise ValueError(f"cannot read state file {p}: {exc}") from exc
        node = node.parent
    return {}


def _load_report(plan_dir: Path) -> dict | None:
    """Return parsed translation-sync-report.json or None if absent/unreadable."""
    p = plan_dir / "artifacts" / "translation-sync-report.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def validate(plan_dir: Path, pass_name: str) -> dict:
    issues: list[dict] = []

    # Load state — if unreadable, still check report
    try:
        state = _load_state(plan_dir)
    except ValueError as exc:
        issues.append(_issue("critical", "gate.state_unreadable", "docs/.rebuild-state.json", str(exc)))
        state = {}

    langs = secondary_langs(state)

    # Short-circuit: no secondary langs → PASS (nothing to enforce)
    if not langs:
        status = "PASS"
        return _result(plan_dir, pass_name, status, issues)

    # Auto-sync opt-out: REBUILD_AUTO_SYNC_TRANSLATIONS=0 → PASS + warning (deliberate deferral)
    if os.environ.get("REBUILD_AUTO_SYNC_TRANSLATIONS", "1") == "0":
        issues.append(_issue(
            "warning", "gate.auto_sync_disabled",
            "docs/.rebuild-state.json",
            f"REBUILD_AUTO_SYNC_TRANSLATIONS=0 — secondary langs ({', '.join(langs)}) "
            f"left stale for pass '{pass_name}'. "
            "Set REBUILD_AUTO_SYNC_TRANSLATIONS=1 or sync manually with "
            "/tkm:rebuild-spec --lang <code>.",
        ))
        return _result(plan_dir, pass_name, "PASS", issues)

    # Auto-sync enabled: report MUST exist
    report = _load_report(plan_dir)
    if report is None:
        issues.append(_issue(
            "critical", "gate.report_missing",
            f"plans/<active-plan>/artifacts/translation-sync-report.json",
            f"translation-sync-report.json is MISSING for pass '{pass_name}' "
            f"but secondary langs are registered ({', '.join(langs)}). "
            "This is the exact silent-skip bug (lang-sync-fix). "
            + _FIX_MSG,
        ))
        return _result(plan_dir, pass_name, "FAIL", issues)

    # Report exists but was written for a different pass (stale report from prior pass)
    report_pass = report.get("pass", "")
    if report_pass != pass_name:
        issues.append(_issue(
            "critical", "gate.report_stale_pass",
            "artifacts/translation-sync-report.json",
            f"translation-sync-report.json has pass='{report_pass}' "
            f"but expected pass='{pass_name}'. "
            "Re-run the pass to produce a fresh report. " + _FIX_MSG,
        ))
        return _result(plan_dir, pass_name, "FAIL", issues)

    # Check per-lang staleness against state cursors
    primary_cursor_sha = state.get("last_rebuild_sha") or ""
    translations = state.get("translations") or {}

    for lang in langs:
        entry = translations.get(lang) or {}
        if is_stale(entry, primary_cursor_sha, pass_name):
            issues.append(_issue(
                "critical", "gate.lang_behind_cursor",
                "docs/.rebuild-state.json",
                f"lang '{lang}' is still stale for pass '{pass_name}': "
                f"translated_from_sha={entry.get('translated_from_sha', '(none)')!r} "
                f"(primary cursor: {primary_cursor_sha!r}), "
                f"passes_translated={entry.get('passes_translated', [])!r}. "
                + _FIX_MSG,
            ))

    status = "FAIL" if any(i["severity"] == "critical" for i in issues) else "PASS"
    return _result(plan_dir, pass_name, status, issues)


def _result(plan_dir: Path, pass_name: str, status: str, issues: list[dict]) -> dict:
    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_dir": str(plan_dir),
        "pass": pass_name,
        "status": status,
        "summary": {"critical": critical, "warning": warning},
        "issues": sorted(issues, key=lambda i: (i["severity"], i["rule_id"], i["location"]["file"])),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="rebuild-spec translation sync completion gate")
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--pass", dest="pass_name", required=True,
                        help="pass name (core|feature-specs|flows|glossary|screen-specs|api-contracts)")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--summary-out", default=None)
    args = parser.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    plan_dir = Path(args.plan_dir).resolve()
    if not plan_dir.is_dir():
        print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
        return 2
    try:
        assert_under(plan_dir, project_root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(plan_dir, args.pass_name)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] translation gate crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))

    if args.summary_out:
        summary_path = Path(args.summary_out).resolve()
        try:
            assert_under(summary_path.parent, project_root)
            summary = load_summary(summary_path, plan_dir.name)
            # translation_gate has a flat issues list (not per-fcode specs), so store directly
            summary["validators"][VALIDATOR] = {
                "status": result["status"],
                "pass": result["pass"],
                "summary": result["summary"],
                "issues": result["issues"],
            }
            # recalculate_totals only aggregates feature_existence + specs slots;
            # add our own critical/warning counts on top so derive_overall_status sees them.
            recalculate_totals(summary)
            t = summary["totals"]
            t["critical"] = t.get("critical", 0) + result["summary"]["critical"]
            t["warning"] = t.get("warning", 0) + result["summary"]["warning"]
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(summary_path, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
