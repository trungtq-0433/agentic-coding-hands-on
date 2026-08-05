#!/usr/bin/env python3
"""Wave 5.5 — feature existence validator.

Checks: every declared F### has a folder under artifacts/features/{slug}/;
every folder maps to a declared slug; all 4 audience-aware files present OR
.pending marker present.

Stdlib only. Authority: ../references/canonical-fcode-schema.md.

Exit codes: 0 (no critical), 1 (critical present), 2 (internal error).
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
    is_valid_slug,
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

VALIDATOR = "feature_existence"


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
        features = canonical.get("features", [])
        return [
            {"fcode": f["fcode"], "slug": f["slug"], "name": f.get("name", "")}
            for f in features
        ]
    flist = plan_dir / "artifacts" / "feature-list.md"
    issues.append(_issue(
        "warning", "existence.canonical_missing",
        str(flist.relative_to(plan_dir)) if flist.exists() else "_canonical-fcodes.json",
        "no _canonical-fcodes.json; falling back to feature-list.md regex parse",
    ))
    return parse_feature_list_fallback(flist)


def validate(plan_dir: Path) -> dict:
    issues: list[dict] = []
    declared = _collect_declared(plan_dir, issues)
    declared_slugs = {f["slug"] for f in declared}
    features_root = plan_dir / "artifacts" / "features"

    for feat in declared:
        slug = feat["slug"]
        if not is_valid_slug(slug):
            issues.append(_issue(
                "critical", "existence.slug_format",
                f"artifacts/features/{slug}",
                f"slug {slug!r} does not match {SLUG_RE.pattern}",
            ))
            continue
        folder = features_root / slug
        if not folder.is_dir():
            issues.append(_issue(
                "critical", "existence.folder_missing",
                f"artifacts/features/{slug}",
                f"declared feature {feat['fcode']} ({slug}) has no folder",
            ))
            continue
        required = list(FEATURE_FILES)
        missing = [f for f in required if not (folder / f).is_file()]
        pending = folder / ".pending"
        if missing and not pending.is_file():
            issues.append(_issue(
                "critical", "existence.folder_incomplete",
                f"artifacts/features/{slug}",
                f"folder missing {missing!r} and no .pending marker",
            ))

    if features_root.is_dir():
        for child in sorted(features_root.iterdir()):
            if not child.is_dir():
                continue
            if not SLUG_RE.match(child.name):
                issues.append(_issue(
                    "warning", "existence.slug_format",
                    f"artifacts/features/{child.name}",
                    f"folder name {child.name!r} does not match slug regex",
                ))
                continue
            if child.name not in declared_slugs:
                issues.append(_issue(
                    "warning", "existence.orphan_folder",
                    f"artifacts/features/{child.name}",
                    "folder present but not declared in canonical/feature-list",
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
    parser = argparse.ArgumentParser(description="rebuild-spec Wave 5.5 existence validator")
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
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
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
