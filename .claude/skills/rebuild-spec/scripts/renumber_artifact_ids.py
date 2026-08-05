"""Renumber all ID codes in a rebuild-spec artifact to be contiguous (001..N).

Usage:
  python3 renumber_artifact_ids.py \\
      --artifact user-stories \\
      --plan-dir plans/260610-1545-my-project \\
      [--project-root /path/to/repo] \\
      [--map-out artifacts/renumber-map-user-stories.json] \\
      [--report-only]

Exit codes: 0 = success / no-op, 2 = internal error.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allow running as a standalone script or via -m
# ---------------------------------------------------------------------------
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import json  # noqa: E402 — stdlib, needed for slice-plan key rewrite (F13)

from _id_schemes_lib import (  # noqa: E402
    ARTIFACT_OWNS,
    SCHEMES,
    SIBLING_MATRIX,
    atomic_write_json,
    atomic_write_text,
    build_renumber_map,
    find_codes,
    find_codes_scoped,
    find_fence_only_codes,
    find_overflow_tokens,
    pre_flight_sentinel_check,
    resolve_artifact_files,
    rewrite_text,
)
from _slug_lib import assert_under, resolve_project_root  # noqa: E402


# ---------------------------------------------------------------------------
# F13: Slice-plan key rewrite helper
# ---------------------------------------------------------------------------

def rewrite_slice_plan_keys(
    slice_plan_path: Path,
    full_map: dict[str, dict[str, str]],
    project_root: Path,
) -> None:
    """Rewrite F### JSON keys in _slice-plan.json using the same in-memory map.

    Targeted key replacement only — values referencing US###/SCR###/etc. are
    NOT feature-list-owned and remain untouched. If the file is absent → no-op.
    Uses atomic write to prevent a partial-write leaving a corrupt slice-plan.

    Args:
        slice_plan_path: Path to _fragments/feature-list/_slice-plan.json.
        full_map: Renumber map produced during feature-list renumber (prefix → {old: new}).
        project_root: Project root for assert_under guard.
    """
    if not slice_plan_path.is_file():
        return  # absent → no-op (single-task path)

    assert_under(slice_plan_path, project_root)

    raw = slice_plan_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[WARN] slice-plan key rewrite skipped — invalid JSON in {slice_plan_path}: {exc}", file=sys.stderr)
        return

    if not isinstance(data, dict):
        print(f"[WARN] slice-plan key rewrite skipped — expected JSON object, got {type(data).__name__}", file=sys.stderr)
        return

    # Build a flat {old_key: new_key} map across all owned prefixes (F### only)
    key_map: dict[str, str] = {}
    for prefix_mapping in full_map.values():
        key_map.update(prefix_mapping)

    if not key_map:
        return  # no renaming needed

    # Rewrite top-level JSON keys only; values are untouched
    new_data: dict = {}
    for key, value in data.items():
        new_key = key_map.get(key, key)
        new_data[new_key] = value

    if new_data == data:
        return  # already up-to-date, skip write

    atomic_write_json(slice_plan_path, new_data)
    print(f"[INFO] slice-plan keys rewritten: {len(key_map)} mappings applied to {slice_plan_path.name}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Core run logic
# ---------------------------------------------------------------------------

def run(
    artifact: str,
    plan_dir: Path,
    project_root: Path,
    map_out: Path,
    report_only: bool,
) -> int:
    """Renumber owned scheme codes in *artifact* to be contiguous. Returns exit code.

    For multi-file artifacts (process-flows: artifacts/flows/*.md):
    - The FLOW### renumber map is built from ALL files concatenated in sorted-filename
      document order (first occurrence across the sequence defines the ordinal).
    - The same map is then applied to EACH file individually via atomic write.
    - Zero files → no-op exit 0 (not an error).
    """
    prefixes = ARTIFACT_OWNS.get(artifact)
    if not prefixes:
        print(f"[ERROR] Unknown artifact {artifact!r}. Known: {list(ARTIFACT_OWNS)}", file=sys.stderr)
        return 2

    # Resolve the file(s) for this artifact.  process-flows → flows/*.md (multi-file);
    # all others → single artifacts/<artifact>.md.
    artifact_files = resolve_artifact_files(plan_dir, artifact)

    if not artifact_files:
        # Zero files → vacuous no-op (not an error)
        if not report_only:
            atomic_write_json(map_out, {})
        return 0

    # Guard all resolved paths under project_root
    for af in artifact_files:
        assert_under(af, project_root)

    # F5: delete stale map at invocation START so no prior crashed run lingers
    if not report_only and map_out.is_file():
        map_out.unlink()

    # --- Multi-file path (process-flows) ---
    if len(artifact_files) > 1:
        return _run_multifile(artifact, artifact_files, project_root, map_out, report_only, prefixes)

    # --- Single-file path (all artifacts except process-flows with ≥2 files) ---
    artifact_file = artifact_files[0]

    text = artifact_file.read_text(encoding="utf-8", errors="replace")

    # F11: sentinel pre-flight check BEFORE any write
    try:
        pre_flight_sentinel_check(text, artifact_file)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    # Build renumber maps for every owned prefix.
    # Scan prose+mermaid only (same scope as rewrite_text and the validator):
    # IDs appearing exclusively inside non-mermaid code fences are excluded
    # from the map so the emitted JSON does not claim renames that never happen.
    full_map: dict[str, dict[str, str]] = {}
    for prefix in prefixes:
        sep = SCHEMES[prefix]["sep"]

        # Overflow detection — warn, leave untouched (phase-02 validator escalates)
        for ov in find_overflow_tokens(text, prefix, sep):
            print(
                f"[WARN] overflow token {ov} (4+ digits) — not renumbered; "
                "will fail contiguity gate",
                file=sys.stderr,
            )

        # Warn about IDs found only inside code fences (excluded from map)
        for fc in find_fence_only_codes(text, prefix, sep):
            print(
                f"[WARN] {fc} found only inside a code fence — excluded from "
                "renumber map; manual review recommended",
                file=sys.stderr,
            )

        mapping = build_renumber_map(find_codes_scoped(text, prefix, sep), prefix, sep)
        if mapping:
            full_map[prefix] = mapping

    if not full_map:
        # Already contiguous / no-op
        if not report_only:
            atomic_write_json(map_out, {})
        return 0

    if report_only:
        for prefix, mapping in full_map.items():
            for old, new in mapping.items():
                print(f"  {prefix}: {old} → {new}")
        return 0

    # Apply rewrites — one prefix at a time (re-read file each pass for safety)
    for prefix, mapping in full_map.items():
        sep = SCHEMES[prefix]["sep"]

        # Re-read; a prior prefix pass may have already written changes
        text = artifact_file.read_text(encoding="utf-8", errors="replace")
        try:
            pre_flight_sentinel_check(text, artifact_file)
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 2

        new_text = rewrite_text(text, mapping, prefix, sep, artifact_file)
        if new_text != text:
            assert_under(artifact_file, project_root)
            atomic_write_text(artifact_file, new_text)

        # Apply same map to siblings that exist on disk (absent = skipped, not error)
        for sib_name in SIBLING_MATRIX.get(prefix, []):
            sib_path = plan_dir / "artifacts" / sib_name
            if not sib_path.is_file():
                continue
            assert_under(sib_path, project_root)
            sib_text = sib_path.read_text(encoding="utf-8", errors="replace")
            try:
                pre_flight_sentinel_check(sib_text, sib_path)
            except RuntimeError as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                return 2
            new_sib = rewrite_text(sib_text, mapping, prefix, sep, sib_path)
            if new_sib != sib_text:
                atomic_write_text(sib_path, new_sib)

    # F13: slice-plan key rewrite — only for feature-list (shard path); no-op if file absent.
    if artifact == "feature-list":
        slice_plan_path = plan_dir / "_fragments" / "feature-list" / "_slice-plan.json"
        rewrite_slice_plan_keys(slice_plan_path, full_map, project_root)

    # F6: write per-artifact map (never a shared renumber-map.json)
    atomic_write_json(map_out, {p: m for p, m in full_map.items() if m})
    return 0


def _run_multifile(
    artifact: str,
    artifact_files: "list[Path]",
    project_root: Path,
    map_out: Path,
    report_only: bool,
    prefixes: "list[str]",
) -> int:
    """Renumber multi-file artifact (process-flows: artifacts/flows/*.md).

    Build the renumber map from ALL files concatenated in sorted-filename order
    (first occurrence defines the ordinal), then rewrite EACH file individually.
    """
    # F11: pre-flight sentinel check on all files before ANY write
    all_texts: list[str] = []
    for af in artifact_files:
        t = af.read_text(encoding="utf-8", errors="replace")
        try:
            pre_flight_sentinel_check(t, af)
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 2
        all_texts.append(t)

    # Build combined text in sorted-filename document order for map construction
    combined_text = "\n".join(all_texts)

    # Build renumber maps using prose+mermaid scope only (same as rewrite/validator).
    full_map: dict[str, dict[str, str]] = {}
    for prefix in prefixes:
        sep = SCHEMES[prefix]["sep"]

        # Overflow detection — warn, leave untouched
        for ov in find_overflow_tokens(combined_text, prefix, sep):
            print(
                f"[WARN] overflow token {ov} (4+ digits) — not renumbered; "
                "will fail contiguity gate",
                file=sys.stderr,
            )

        # Warn about IDs found only inside code fences (excluded from map)
        for fc in find_fence_only_codes(combined_text, prefix, sep):
            print(
                f"[WARN] {fc} found only inside a code fence — excluded from "
                "renumber map; manual review recommended",
                file=sys.stderr,
            )

        mapping = build_renumber_map(find_codes_scoped(combined_text, prefix, sep), prefix, sep)
        if mapping:
            full_map[prefix] = mapping

    if not full_map:
        # Already contiguous / no-op
        if not report_only:
            atomic_write_json(map_out, {})
        return 0

    if report_only:
        for prefix, mapping in full_map.items():
            for old, new in mapping.items():
                print(f"  {prefix}: {old} → {new}")
        return 0

    # Apply the SAME map to each file individually
    for prefix, mapping in full_map.items():
        sep = SCHEMES[prefix]["sep"]
        for af in artifact_files:
            # Re-read each file (a previous iteration may have written it)
            current_text = af.read_text(encoding="utf-8", errors="replace")
            try:
                pre_flight_sentinel_check(current_text, af)
            except RuntimeError as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                return 2
            new_text = rewrite_text(current_text, mapping, prefix, sep, af)
            if new_text != current_text:
                assert_under(af, project_root)
                atomic_write_text(af, new_text)

        # FLOW### has no siblings in SIBLING_MATRIX (empty list), so no sibling pass needed.
        for sib_name in SIBLING_MATRIX.get(prefix, []):
            sib_path = artifact_files[0].parent.parent / sib_name  # artifacts/<sib>
            if not sib_path.is_file():
                continue
            assert_under(sib_path, project_root)
            sib_text = sib_path.read_text(encoding="utf-8", errors="replace")
            try:
                pre_flight_sentinel_check(sib_text, sib_path)
            except RuntimeError as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                return 2
            new_sib = rewrite_text(sib_text, mapping, prefix, sep, sib_path)
            if new_sib != sib_text:
                atomic_write_text(sib_path, new_sib)

    # F6: write per-artifact map
    atomic_write_json(map_out, {p: m for p, m in full_map.items() if m})
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", required=True, help="Artifact name, e.g. user-stories")
    p.add_argument("--plan-dir", required=True, help="Path to the active plan directory")
    p.add_argument("--project-root", default=None, help="Git project root (default: auto-detect)")
    p.add_argument(
        "--map-out", default=None,
        help="Override map file path (default: artifacts/renumber-map-<artifact>.json)",
    )
    p.add_argument(
        "--report-only", action="store_true",
        help="Build map but do NOT rewrite any files and do NOT write the map file",
    )
    return p.parse_args()


def main() -> None:
    args = _build_args()
    project_root = resolve_project_root(args.project_root)
    plan_dir = Path(args.plan_dir).resolve()
    assert_under(plan_dir, project_root)
    map_out_default = plan_dir / "artifacts" / f"renumber-map-{args.artifact}.json"
    map_out = Path(args.map_out).resolve() if args.map_out else map_out_default
    assert_under(map_out, project_root)  # M1: guard --map-out against path traversal
    try:
        code = run(
            artifact=args.artifact,
            plan_dir=plan_dir,
            project_root=project_root,
            map_out=map_out,
            report_only=args.report_only,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        code = 2
    sys.exit(code)


if __name__ == "__main__":
    main()
