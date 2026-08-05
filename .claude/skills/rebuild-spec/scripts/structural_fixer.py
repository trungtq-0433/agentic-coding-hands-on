#!/usr/bin/env python3
"""Wave 7.5 — structural fixer for feature spec files.

Inserts placeholder `**Linked FR:** FR-???` into BR/SM/ALG/INT blocks that
are missing the line, then decrements `failed` in review-report.md by the
number of resolved structural issues. Stdlib only.

Exit codes: 0 = success, 2 = arg/IO error. Never exits 1.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import assert_under  # noqa: E402
from _spec_block_lib import find_blocks_missing_linked_fr, has_linked_fr  # noqa: E402
from _review_report_lib import mutate_review_report  # noqa: E402


# ---------------------------------------------------------------------------
# Atomic write helpers
# ---------------------------------------------------------------------------

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, data: dict) -> None:
    _atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Feature spec file resolution
# ---------------------------------------------------------------------------

# v4 split the single feature spec into 4 files; BR/SM/ALG/INT blocks (which carry
# **Linked FR:**) live in technical-spec.md. Legacy plans used spec.md. Prefer the v4
# name, fall back to the legacy name per-dir so resume/legacy plans still get fixed.
FEATURE_SPEC_NAMES = ("technical-spec.md", "spec.md")


def _resolve_feature_spec(feature_dir: Path) -> Path | None:
    """Return the feature spec file inside feature_dir (v4 name first), or None."""
    for name in FEATURE_SPEC_NAMES:
        candidate = feature_dir / name
        if candidate.is_file():
            return candidate
    return None


# ---------------------------------------------------------------------------
# Per-spec fix logic
# ---------------------------------------------------------------------------

def _fix_spec(spec_path: Path, backup_root: Path) -> int:
    """Insert **Linked FR:** FR-??? into blocks missing it. Return count fixed."""
    text = spec_path.read_text(encoding="utf-8")
    missing = find_blocks_missing_linked_fr(text)
    if not missing:
        return 0

    lines = text.splitlines(keepends=True)
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    fixed = 0
    for block in reversed(missing):
        hl = block["heading_line"]
        be = block["block_end"]
        current_text = "".join(lines)
        if has_linked_fr(current_text, hl, be):
            continue
        lines.insert(hl + 1, f"**Linked FR:** FR-???{eol}")
        fixed += 1

    if fixed == 0:
        return 0

    fcode = spec_path.parent.name
    backup_path = backup_root / fcode / f"{spec_path.name}.orig"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(spec_path, backup_path)

    _atomic_write_text(spec_path, "".join(lines))
    return fixed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Wave 7.5 — insert **Linked FR:** placeholder into BR/SM/ALG/INT blocks missing it."
    )
    parser.add_argument("--plan-dir", required=True, help="Path to the plan directory")
    parser.add_argument(
        "--review-report", default=None,
        help="Path to review-report.md (default: <plan-dir>/artifacts/review-report.md)",
    )
    parser.add_argument(
        "--no-decrement", action="store_true",
        help="Skip mutating review-report.md (useful for dry runs / testing)",
    )
    parser.add_argument(
        "--incremental-plan-json", default=None,
        help="Path to .incremental-plan.json; when present + mode=incremental, restrict walk to affected_fcodes",
    )
    args = parser.parse_args(argv)

    cwd = Path.cwd().resolve()
    try:
        plan_dir = Path(args.plan_dir).resolve()
        assert_under(plan_dir, cwd)
    except ValueError as exc:
        print(f"[ERROR] --plan-dir path traversal: {exc}", file=sys.stderr)
        return 2

    if not plan_dir.is_dir():
        print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
        return 2

    features_root = plan_dir / "artifacts" / "features"
    if not features_root.is_dir():
        print(f"[ERROR] features directory not found: {features_root}", file=sys.stderr)
        return 2

    review_report = (
        Path(args.review_report).resolve() if args.review_report
        else plan_dir / "artifacts" / "review-report.md"
    )
    if args.review_report:
        try:
            assert_under(review_report, cwd)
        except ValueError as exc:
            print(f"[ERROR] --review-report path traversal: {exc}", file=sys.stderr)
            return 2
    backup_root = plan_dir / "artifacts" / "validation" / "structural-fix-backup"
    validation_dir = plan_dir / "artifacts" / "validation"

    scope_mode = "full"
    scoped_fcodes: list[str] = []

    if args.incremental_plan_json:
        plan_json_path = Path(args.incremental_plan_json).resolve()
        try:
            assert_under(plan_json_path, cwd)
        except ValueError as exc:
            print(f"[ERROR] --incremental-plan-json path traversal: {exc}", file=sys.stderr)
            return 2
        if plan_json_path.is_file():
            try:
                plan_json = json.loads(plan_json_path.read_text(encoding="utf-8"))
                if plan_json.get("mode") == "incremental":
                    scope_mode = "incremental"
                    raw_fcodes = list(plan_json.get("affected_fcodes") or [])
                    scoped_fcodes = [fc for fc in raw_fcodes if re.fullmatch(r"F\d{3}(?:_\w+)?", fc)]
                    dropped = [fc for fc in raw_fcodes if fc not in set(scoped_fcodes)]
                    if dropped:
                        print(f"[WARN] {len(dropped)} fcode(s) failed validation and were skipped: {dropped}", file=sys.stderr)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"[INFO] could not read {plan_json_path}: {exc}; walking all features", file=sys.stderr)
        else:
            print(f"[INFO] incremental plan not found at {plan_json_path}; walking all features", file=sys.stderr)

    if scope_mode == "incremental":
        resolved_dirs: list[Path] = []
        for fc in scoped_fcodes:
            exact = features_root / fc
            if exact.is_dir():
                resolved_dirs.append(exact)
            else:
                matches = [d for d in features_root.iterdir() if d.is_dir() and d.name.startswith(fc + "_")]
                if len(matches) == 1:
                    resolved_dirs.append(matches[0])
                elif matches:
                    print(f"[WARN] ambiguous fcode {fc!r}: {[m.name for m in matches]}", file=sys.stderr)
        spec_paths = sorted(
            p for p in (_resolve_feature_spec(d) for d in resolved_dirs) if p is not None
        )
    else:
        spec_paths = sorted(
            p for p in (
                _resolve_feature_spec(child)
                for child in features_root.iterdir()
                if child.is_dir()
            ) if p is not None
        )

    files_modified: list[str] = []
    by_file: dict[str, int] = {}
    total_fixed = 0

    for spec_path in spec_paths:
        fcode = spec_path.parent.name
        try:
            count = _fix_spec(spec_path, backup_root)
        except OSError as exc:
            print(f"[ERROR] could not process {spec_path}: {exc}", file=sys.stderr)
            return 2
        if count > 0:
            total_fixed += count
            by_file[fcode] = count
            try:
                files_modified.append(str(spec_path.relative_to(cwd)))
            except ValueError:
                files_modified.append(str(spec_path))

    fix_report_path = validation_dir / "structural-fix-report.json"
    try:
        _atomic_write_json(fix_report_path, {
            "schema_version": 1,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "files_modified": files_modified,
            "blocks_fixed": total_fixed,
            "placeholders_remaining": total_fixed,
            "by_file": by_file,
            "scope_mode": scope_mode,
            "scoped_fcodes": scoped_fcodes,
        })
    except OSError as exc:
        print(f"[ERROR] could not write fix report: {exc}", file=sys.stderr)
        return 2

    print(f"[W7.5] blocks_fixed={total_fixed} files_modified={len(files_modified)}")
    print(f"[W7.5] fix report → {fix_report_path}")

    if not args.no_decrement and total_fixed > 0:
        if review_report.is_file():
            try:
                mutate_review_report(review_report, total_fixed, _atomic_write_text)
                print(f"[W7.5] review-report updated → {review_report}")
            except OSError as exc:
                print(f"[ERROR] could not update review-report: {exc}", file=sys.stderr)
                return 2
        else:
            print(f"[W7.5] review-report not found, skipping decrement: {review_report}",
                  file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
