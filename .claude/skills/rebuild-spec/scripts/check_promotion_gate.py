#!/usr/bin/env python3
"""Wave 9 — promotion gate: verify all 4 feature files exist before doc promotion.
Stdlib only. Exit codes: 0 (pass), 1 (fail), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _slug_lib import (  # noqa: E402
    FEATURE_FILES,
    SLUG_RE,
    assert_under,
    load_canonical,
    parse_feature_list_fallback,
    resolve_project_root,
)
from _summary_lib import (  # noqa: E402
    atomic_write,
    derive_overall_status,
    load_summary,
    merge_validator_result,
    recalculate_totals,
)

VALIDATOR = "promotion_gate"


def _issue(severity: str, rule_id: str, file_: str, message: str) -> dict:
    return {
        "severity": severity,
        "rule_id": rule_id,
        "location": {"file": file_, "line": None},
        "message": message,
    }


def _collect_declared(plan_dir: Path, issues: list[dict]) -> list[dict]:
    canonical = load_canonical(plan_dir)
    if canonical:
        return [
            {"fcode": f["fcode"], "slug": f["slug"]}
            for f in canonical.get("features", [])
        ]
    flist = plan_dir / "artifacts" / "feature-list.md"
    issues.append(_issue(
        "warning", "gate.canonical_missing",
        str(flist.relative_to(plan_dir)) if flist.exists() else "_canonical-fcodes.json",
        "no _canonical-fcodes.json; falling back to feature-list.md regex parse",
    ))
    return parse_feature_list_fallback(flist)


def _check_validation_summary(plan_dir: Path) -> str | None:
    """Return None if OK or absent, else an error message if status=FAIL."""
    summary_path = plan_dir / "artifacts" / "validation-summary.json"
    if not summary_path.is_file():
        return None  # absent is acceptable — gate only checks if present
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"validation-summary.json unreadable: {exc}"
    status = data.get("overall_status", "")
    if status == "FAIL":
        return "validation-summary.json reports overall_status=FAIL"
    return None


def _check_review_report(plan_dir: Path, slug: str) -> str | None:
    """Return None if gate:pass found in review-report frontmatter, else error."""
    # Check common review report paths
    candidates = [
        plan_dir / "artifacts" / "features" / slug / "review-report.md",
        plan_dir / "review-report.md",
    ]
    for rp in candidates:
        if rp.is_file():
            # Read first 10 lines for frontmatter gate: field
            lines = []
            try:
                with rp.open(encoding="utf-8", errors="replace") as f:
                    for _ in range(10):
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
            except OSError:
                continue
            for line in lines:
                stripped = line.strip().lower()
                if stripped.startswith("gate:") and "pass" in stripped:
                    return None
            return f"review-report frontmatter missing 'gate: pass' in {rp.name}"
    # No review report found — not a hard gate failure (may not exist yet)
    return None


def validate(plan_dir: Path) -> dict:
    issues: list[dict] = []
    declared = _collect_declared(plan_dir, issues)
    features_root = plan_dir / "artifacts" / "features"

    # Plan-level checks (run once, not per feature)
    summary_err = _check_validation_summary(plan_dir)
    if summary_err:
        issues.append(_issue(
            "warning", "gate.validation_summary",
            "artifacts/validation-summary.json",
            summary_err,
        ))

    for feat in declared:
        slug = feat["slug"]
        if not SLUG_RE.match(slug):
            issues.append(_issue(
                "critical", "gate.slug_format",
                f"artifacts/features/{slug}",
                f"slug {slug!r} does not match expected pattern",
            ))
            continue

        folder = features_root / slug
        if not folder.is_dir():
            issues.append(_issue(
                "critical", "gate.folder_missing",
                f"artifacts/features/{slug}",
                f"feature folder not found: artifacts/features/{slug}",
            ))
            continue

        # All 4 files must exist
        missing = [f for f in FEATURE_FILES if not (folder / f).is_file()]
        if missing:
            issues.append(_issue(
                "critical", "gate.files_incomplete",
                f"artifacts/features/{slug}",
                f"missing files before promotion: {missing!r}",
            ))

        # .pending marker must be absent
        pending = folder / ".pending"
        if pending.is_file():
            issues.append(_issue(
                "critical", "gate.pending_marker",
                f"artifacts/features/{slug}/.pending",
                ".pending marker still present — W6 write not completed",
            ))

        # Review report gate check (per-feature: slug/review-report.md or global fallback)
        review_err = _check_review_report(plan_dir, slug)
        if review_err:
            issues.append(_issue(
                "warning", "gate.review_report",
                f"artifacts/features/{slug}/review-report.md",
                review_err,
            ))

    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    status = "FAIL" if critical else ("WARN" if warning else "PASS")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_dir": str(plan_dir),
        "status": status,
        "summary": {"critical": critical, "warning": warning},
        "issues": sorted(issues, key=lambda i: (i["severity"], i["rule_id"], i["location"]["file"])),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="rebuild-spec Wave 9 promotion gate")
    parser.add_argument("--plan-dir", required=True)
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
        result = validate(plan_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] promotion gate crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))

    if args.summary_out:
        summary_path = Path(args.summary_out).resolve()
        try:
            assert_under(summary_path.parent, project_root)
            summary = load_summary(summary_path, plan_dir.name)
            merge_validator_result(summary, VALIDATOR, result)
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(summary_path, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
