#!/usr/bin/env python3
"""Pre-gen artifact LOC estimator — the ONLY oversize safety mechanism.

Called at EVERY generated artifact's dispatch point, BEFORE the research
task is created.  Over threshold => chunked path; else single task.

Stdlib only.  Exit 0 always (estimate is advisory, never halts).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROUTE_METHOD_RE = re.compile(
    r"^\|\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s",
    re.IGNORECASE,
)

# MODEL### entity headings only — the earlier `[\w]+` alternative matched ANY `### Word`
# heading (### Notes, ### Overview…), inflating the count and tripping the fixed-40 gate.
MODEL_HEADING_RE = re.compile(r"^###\s+MODEL\d{3}", re.IGNORECASE)

US_HEADING_RE = re.compile(r"^##\s+US\d{3}")
FEATURE_HEADING_RE = re.compile(r"^###\s+F\d{3}")
SCR_HEADING_RE = re.compile(r"^##\s+SCR\d{3}")
BL_HEADING_RE = re.compile(r"^##\s+BL\d{3}")

# --- First-gen signal parsers (scout-report.md) ---------------------------------
# CRITICAL: at first generation the artifact's own output file does not exist yet, so
# counting its OUTPUT headings (## SCR###/## BL###/## US###) returns 0 → shard:false →
# a monolithic oversized task is dispatched and hangs. The scout report is the only
# input present at every artifact's first dispatch; these parsers read its typed
# inventories so the estimate has a real signal on the first run, not just on reruns.

# File Inventory line: `<relative/path>\t<type>` (type ∈ the fixed scout type set).
INVENTORY_TYPES = ("screen", "route", "model", "background", "permission", "config", "other")
INVENTORY_LINE_RE = re.compile(
    r"^\s*(\S.*?)\s+(" + "|".join(INVENTORY_TYPES) + r")\s*$"
)
# Background Logic Source Inventory entry: `- <category>: <path>` (skip `_(none found)_`).
BL_INVENTORY_LINE_RE = re.compile(r"^\s*-\s+[\w.\-/]+:\s+\S")

# Conservative routes-per-route-file fan-out: route-list has no endpoint-level signal at
# W1 (scout marks route *files*, not individual routes). Multiply route-file count so the
# estimate biases toward over-sharding for multi-file route structures (safe: over-shard
# wastes fan-out, never hangs). KNOWN LIMITATION: a single monolithic routes file
# (one Express routes.js / Laravel web.php holding hundreds of routes) is one inventory
# entry → may under-estimate. The incremental rerun path self-corrects once route-list.md
# exists; first-gen monolithic-file projects are the residual blind spot.
ROUTE_ROWS_PER_FILE = 12

# Monolithic route-file floor: when the scout shows ≤2 route files but the repo is clearly
# large (total File Inventory entries ≥ MONOLITHIC_LARGE_REPO_THRESHOLD), a single routes
# file is almost certainly holding hundreds of routes. Apply this floor so the estimate
# crosses the shard gate. Bias: over-shard (wasted fan-out) is safe; under-shard (monolithic
# task) causes compression and incomplete output.
# Must exceed max_loc / avg_lpu for route-list = 800 / 2 = 400 units to guarantee shard:true.
# Set to 500 (1000 est_loc) — conservative overshoot that still represents a real monolithic
# project (Laravel web.php or Express routes.js easily hold 500+ routes).
MONOLITHIC_ROUTE_FLOOR = 500
# Total File Inventory entries above which a ≤2-route-file project is treated as monolithic.
# 50 is conservative: a project with 50+ files and only 1-2 route files is almost certainly
# using a single monolithic route file (Laravel web.php, Express app.js, Django urls.py).
MONOLITHIC_LARGE_REPO_THRESHOLD = 50
# User stories track screens roughly 1.5:1 (sun-news: ~105 US / 67 SCR).
US_PER_SCREEN = 1.5

DESCRIPTORS: dict[str, dict] = {
    "api-contracts": {
        "unit": "endpoint",
        "count_source": "route-list data rows",
        "avg_lpu": 16,
        "slice_key": "resource namespace",
    },
    "data-model": {
        "unit": "model/entity",
        "count_source": "scout inventory",
        "avg_lpu": 30,
        "fixed_threshold": 40,
        "slice_key": "module/domain",
    },
    "user-stories": {
        "unit": "US###",
        "count_source": "feature-list/permissions actor split",
        "avg_lpu": 33,
        "slice_key": "actor",
    },
    "feature-list": {
        "unit": "F###",
        "count_source": "prior drafts feature signal",
        "avg_lpu": 42,
        "slice_key": "expand by F### batch",
    },
    "screen-list": {
        "unit": "SCR###",
        "count_source": "scout inventory",
        "avg_lpu": 19,
        "slice_key": "module/route group",
    },
    "behavior-logic": {
        "unit": "BL###",
        "count_source": "scout BL inventory",
        "avg_lpu": 25,
        "slice_key": "category/domain",
    },
    "route-list": {
        "unit": "route row",
        "count_source": "route-list data rows",
        "avg_lpu": 2,
        "slice_key": "resource / top-level path prefix",
    },
    "api-map": {
        "unit": "endpoint",
        "count_source": "api-map endpoint rows",
        "avg_lpu": 3,
        "slice_key": "resource namespace",
    },
    "screen-flow": {
        "unit": "SCR###",
        "count_source": "scout inventory (= screen-list)",
        "avg_lpu": 10,
        "slice_key": "module/route group",
    },
    # Phase B (v11.1.0) — both estimate from the extractor digests in plans/<active>/artifacts/.
    "crud-matrix": {
        "unit": "table×feature row",
        "count_source": "_digest_extract_data_flow.json db_ops (distinct table)",
        "avg_lpu": 4,
        "slice_key": "F### range",  # RT-DOC-b: shard by feature range, never by domain
    },
    "db-objects": {
        "unit": "db object",
        "count_source": "_digest_extract_sql_schema.json db_objects",
        "avg_lpu": 6,
        "slice_key": "object kind/schema",
    },
}


def _count_digest_units(plan_dir: Path | None, extractor: str, key: str) -> int:
    """Count digest entries (db_objects, or distinct tables across units[].db_ops) for an
    extractor shard at plans/<active>/artifacts/_digest_<extractor>.json. 0 if absent."""
    if not plan_dir:
        return 0
    digest = plan_dir / "artifacts" / f"_digest_{extractor}.json"
    if not digest.is_file():
        return 0
    try:
        data = json.loads(digest.read_text(encoding="utf-8", errors="replace"))
    except (ValueError, OSError):
        return 0
    if key == "db_objects":
        return len(data.get("db_objects", []) or [])
    if key == "tables":
        tables = set()
        for unit in data.get("units", []) or []:
            for op in unit.get("db_ops", []) or []:
                if op.get("table"):
                    tables.add(op["table"])
        return len(tables)
    return 0


def _count_route_data_rows(path: Path) -> int:
    """Count route-list.md data rows (METHOD-prefixed table rows, skip header/sep)."""
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ROUTE_METHOD_RE.match(line):
            count += 1
    return count


def _count_headings(path: Path, pattern: re.Pattern) -> int:
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if pattern.match(line):
            count += 1
    return count


def _count_models_from_scout(path: Path) -> int:
    """Count entity/model files from scout report File Inventory section."""
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    model_re = re.compile(r"model|entity|migration", re.IGNORECASE)
    count = 0
    in_inventory = False
    for line in text.splitlines():
        if "File Inventory" in line or "## Entities" in line:
            in_inventory = True
            continue
        if in_inventory and line.startswith("## ") and "File Inventory" not in line:
            break
        if in_inventory and line.strip().startswith("- ") and model_re.search(line):
            count += 1
    dm_path = path.parent / "data-model.md"
    return max(count, _count_headings(dm_path, MODEL_HEADING_RE))


def _parse_inventory_by_type_from_text(text: str, wanted: str) -> int:
    """Count scout File Inventory entries of a given type from pre-read text."""
    count = 0
    in_inventory = False
    for line in text.splitlines():
        if line.startswith("## File Inventory"):
            in_inventory = True
            continue
        if in_inventory and line.startswith("## "):
            break
        if in_inventory:
            m = INVENTORY_LINE_RE.match(line)
            if m and m.group(2) == wanted:
                count += 1
    return count


def _parse_total_inventory_from_text(text: str) -> int:
    """Count ALL File Inventory entries regardless of type from pre-read text.

    Used as a large-repo signal: a project with many files and ≤2 route files is likely
    using a single monolithic route file rather than having a genuinely tiny route surface.
    """
    count = 0
    in_inventory = False
    for line in text.splitlines():
        if line.startswith("## File Inventory"):
            in_inventory = True
            continue
        if in_inventory and line.startswith("## "):
            break
        if in_inventory and INVENTORY_LINE_RE.match(line):
            count += 1
    return count


def _count_inventory_by_type(path: Path, wanted: str) -> int:
    """Count scout File Inventory entries of a given type (screen/route/model/...)."""
    if not path.is_file():
        return 0
    return _parse_inventory_by_type_from_text(
        path.read_text(encoding="utf-8", errors="replace"), wanted
    )


def _count_total_inventory(path: Path) -> int:
    """Count ALL File Inventory entries regardless of type.

    Used as a large-repo signal: a project with many files and ≤2 route files is likely
    using a single monolithic route file rather than having a genuinely tiny route surface.
    """
    if not path.is_file():
        return 0
    return _parse_total_inventory_from_text(
        path.read_text(encoding="utf-8", errors="replace")
    )


def _count_bl_inventory(path: Path) -> int:
    """Count Background Logic Source Inventory entries (1:1 with BL items per cardinality
    contract). Skips `_(none found)_` sentinels and the `### {STACK}` subsection headings."""
    if not path.is_file():
        return 0
    count = 0
    in_section = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## Background Logic Source Inventory"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and "_(none found)_" not in line and BL_INVENTORY_LINE_RE.match(line):
            count += 1
    return count


def estimate(
    artifact: str,
    max_loc: int = 800,
    route_list: Path | None = None,
    scout_report: Path | None = None,
    plan_dir: Path | None = None,
) -> dict:
    desc = DESCRIPTORS.get(artifact)
    if not desc:
        return {
            "artifact": artifact,
            "unit_count": 0,
            "est_loc": 0,
            "threshold": max_loc,
            "shard": False,
            "slice_key": None,
            "reason": "no descriptor (always-small or unknown)",
        }

    unit_count = 0

    # Each branch tries the incremental signal (the artifact's own output file, present on
    # reruns) first, then falls back to a first-gen signal from the scout report or an
    # already-generated upstream artifact. Order matters: the most precise available signal
    # wins; a first-gen fallback only fires when the precise one yields 0.
    if artifact in ("api-contracts", "api-map"):
        # Both estimate from route-list.md, which already exists by their dispatch wave.
        if route_list:
            unit_count = _count_route_data_rows(route_list)
    elif artifact == "route-list":
        # Read scout-report text once so both inventory helpers share the same read.
        scout_text = (
            scout_report.read_text(encoding="utf-8", errors="replace")
            if scout_report and scout_report.is_file()
            else ""
        )
        # Always derive both signals so max() can pick the better one.
        scout_route_files = _parse_inventory_by_type_from_text(scout_text, "route") if scout_text else 0
        rows = _count_route_data_rows(route_list) if route_list else 0
        # max() guards the compressed-rerun path: if route-list.md was compressed to a
        # Resource|Actions table its METHOD rows = 0 → fall back to the scout-file estimate.
        unit_count = max(rows, scout_route_files * ROUTE_ROWS_PER_FILE)
        # Monolithic guard: ≤2 route files + large repo → almost certainly a single monolithic
        # file holding hundreds of routes. Apply MONOLITHIC_ROUTE_FLOOR so the estimate
        # crosses the shard gate. Only fires when the unit_count from max() is still too low
        # (i.e., the compressed/absent route-list did not already push us over the floor).
        if (
            scout_text
            and scout_route_files <= 2
            and _parse_total_inventory_from_text(scout_text) >= MONOLITHIC_LARGE_REPO_THRESHOLD
        ):
            unit_count = max(unit_count, MONOLITHIC_ROUTE_FLOOR)
    elif artifact == "data-model":
        # File-count signal: counts model FILES. Mode-A stacks (Django models.py, Rails
        # with many classes per file) may under-count entities at first-gen; the data-model.md
        # MODEL### count below corrects this on rerun, and the W1.5 gate backstops quality.
        if scout_report:
            unit_count = _count_inventory_by_type(scout_report, "model")
        if unit_count == 0 and scout_report:  # older scout reports w/o typed inventory
            unit_count = _count_models_from_scout(scout_report)
        if plan_dir:
            dm = plan_dir / "artifacts" / "data-model.md"
            if dm.is_file():
                unit_count = max(unit_count, _count_headings(dm, MODEL_HEADING_RE))
    elif artifact == "user-stories":
        if plan_dir:
            us = plan_dir / "artifacts" / "user-stories.md"
            unit_count = _count_headings(us, US_HEADING_RE)
            if unit_count == 0:  # feature-list rarely exists at W4, but prefer it if it does
                fl = plan_dir / "artifacts" / "feature-list.md"
                unit_count = _count_headings(fl, FEATURE_HEADING_RE) * 3
            if unit_count == 0:  # first-gen: screen-list IS present by W4 — screens drive US
                sl = plan_dir / "artifacts" / "screen-list.md"
                unit_count = math.ceil(_count_headings(sl, SCR_HEADING_RE) * US_PER_SCREEN)
    elif artifact == "feature-list":
        if plan_dir:
            fl = plan_dir / "artifacts" / "feature-list.md"
            unit_count = _count_headings(fl, FEATURE_HEADING_RE)
        if unit_count == 0 and plan_dir:
            us = plan_dir / "artifacts" / "user-stories.md"
            us_count = _count_headings(us, US_HEADING_RE)
            # ~1 F### per 2 US### (was //3, which under-shards mid-size 40-59 US projects).
            unit_count = max(1, math.ceil(us_count / 2)) if us_count else 0
    elif artifact in ("screen-list", "screen-flow"):
        if scout_report:  # first-gen: count screen-type files from the File Inventory
            unit_count = _count_inventory_by_type(scout_report, "screen")
        if unit_count == 0 and scout_report:  # scout reports that pre-assign SCR### headings
            unit_count = _count_headings(scout_report, SCR_HEADING_RE)
        if unit_count == 0 and plan_dir:  # incremental rerun
            sl = plan_dir / "artifacts" / "screen-list.md"
            unit_count = _count_headings(sl, SCR_HEADING_RE)
    elif artifact == "behavior-logic":
        if scout_report:  # first-gen: BL inventory is 1:1 with BL items
            unit_count = _count_bl_inventory(scout_report)
        if unit_count == 0 and scout_report:  # scout reports that pre-assign BL### headings
            unit_count = _count_headings(scout_report, BL_HEADING_RE)
        if unit_count == 0 and plan_dir:  # incremental rerun
            bl = plan_dir / "artifacts" / "behavior-logic.md"
            unit_count = _count_headings(bl, BL_HEADING_RE)
    elif artifact == "crud-matrix":
        # Distinct tables touched (× features) drive size; read the data-flow digest.
        unit_count = _count_digest_units(plan_dir, "extract_data_flow", "tables")
    elif artifact == "db-objects":
        unit_count = _count_digest_units(plan_dir, "extract_sql_schema", "db_objects")

    avg_lpu = desc["avg_lpu"]
    est_loc = unit_count * avg_lpu

    if "fixed_threshold" in desc:
        shard = unit_count >= desc["fixed_threshold"]
        threshold_desc = f">={desc['fixed_threshold']} {desc['unit']}s"
    else:
        shard = est_loc > max_loc
        threshold_desc = f"est_loc>{max_loc}"

    return {
        "artifact": artifact,
        "unit_count": unit_count,
        "est_loc": est_loc,
        "threshold": max_loc,
        "shard": shard,
        "slice_key": desc["slice_key"],
        "reason": f"{unit_count} {desc['unit']}s × lpu {avg_lpu} = {est_loc} LOC; threshold {threshold_desc}",
    }


# A Permission Rules row: `| <Role> | <✓/✗ allow marker> | <conditions> |`. The role is the
# actor; the second cell is an allow/deny marker that distinguishes data rows from the
# header (`| Role | Allow | ... |`) and separator rows, so structural rows never leak in.
PERM_RULES_ROLE_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*(✓|✗|x|y|n|yes|no|true|false|-|–|—|allow|deny)\s*\|",
    re.IGNORECASE,
)
SKIP_ACTOR_CELLS = {"role", "roles", "actor", "actors", "n/a", "-", "–", "—", ""}


def _extract_actors(permissions_matrix: Path) -> list[str]:
    """Extract distinct actors (roles) from permissions-matrix.md, stable-sorted.

    Actors are the roles in the first column of the `| Role | Allow | Conditions |`
    Permission Rules tables — NOT the `## PERM###:` headings (those are permission codes,
    not actors). Stable sort keeps US### range allocation deterministic.
    """
    if not permissions_matrix.is_file():
        return []
    text = permissions_matrix.read_text(encoding="utf-8", errors="replace")
    actors = set()
    for line in text.splitlines():
        m = PERM_RULES_ROLE_ROW_RE.match(line)
        if not m:
            continue
        role = m.group(1).strip()
        if role.lower() not in SKIP_ACTOR_CELLS and len(role) >= 2:
            actors.add(role)
    return sorted(actors)


def emit_us_ranges(
    actors: list[str],
    us_per_actor: dict[str, int] | None = None,
    headroom: float = 0.2,
) -> list[dict]:
    """Compute disjoint US### ranges per actor.

    Returns list of {actor, start, end, estimated_count} sorted by actor name.
    Ranges are contiguous between actors; intra-range tail gaps are safe (W4.5 uniqueness-only).
    """
    if not actors:
        return []
    ranges = []
    next_start = 1
    for actor in sorted(actors):
        est_count = (us_per_actor or {}).get(actor, 5)
        est_count = max(1, est_count)
        padded = max(1, math.ceil(est_count * (1 + headroom)))
        ranges.append({
            "actor": actor,
            "start": next_start,
            "end": next_start + padded - 1,
            "estimated_count": est_count,
        })
        next_start = next_start + padded
    return ranges


_TRANSLATE_LOC_PER_SOURCE_LINE = 1.05  # translate output ≈ input size (prose swap only)
_REWRITE_LOC_PER_SOURCE_LINE = 1.15   # rewrite may expand slightly (added commentary/structure)


def estimate_op(op: str, file_path: Path, max_loc: int = 800) -> dict:
    """Estimate output LOC for a translate or rewrite-whole-file operation.

    Returns {"op": op, "est_loc": int, "chunk": bool, "max_loc": int}.
    chunk=True when est_loc > max_loc — caller should split the file by heading.
    Advisory only (exit 0); never halts the pipeline.
    """
    if not file_path.is_file():
        return {"op": op, "est_loc": 0, "chunk": False, "max_loc": max_loc,
                "reason": f"file not found: {file_path}"}
    try:
        src_lines = len(file_path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return {"op": op, "est_loc": 0, "chunk": False, "max_loc": max_loc,
                "reason": "file unreadable"}
    multiplier = _TRANSLATE_LOC_PER_SOURCE_LINE if op == "translate" else _REWRITE_LOC_PER_SOURCE_LINE
    est_loc = math.ceil(src_lines * multiplier)
    chunk = est_loc > max_loc
    return {
        "op": op,
        "est_loc": est_loc,
        "chunk": chunk,
        "max_loc": max_loc,
        "reason": (
            f"{src_lines} source lines × {multiplier} = {est_loc} est LOC; "
            f"threshold {max_loc}"
        ),
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Pre-gen artifact LOC estimator")
    # --artifact and --op are mutually exclusive entry points.
    # --artifact is kept required=False so --op can be used standalone.
    p.add_argument("--artifact", default=None, choices=list(DESCRIPTORS.keys()) + ["unknown"],
                   help="Artifact name for generation/sharding estimate")
    p.add_argument("--op", default=None, choices=["translate", "rewrite"],
                   help="Operation mode: estimate output LOC for translate/rewrite of --file")
    p.add_argument("--file", default=None, help="Source file path (required for --op)")
    p.add_argument("--route-list", default=None, help="Path to route-list.md")
    p.add_argument("--scout-report", default=None, help="Path to scout-report.md")
    p.add_argument("--plan-dir", default=None, help="Path to active plan dir")
    p.add_argument("--max-loc", type=int, default=800, help="LOC threshold (default 800)")
    p.add_argument("--emit-ranges", action="store_true", help="Emit US### ranges per actor (user-stories only)")
    p.add_argument("--permissions-matrix", default=None, help="Path to permissions-matrix.md (for --emit-ranges)")
    args = p.parse_args(argv)

    if args.emit_ranges:
        pm_path = Path(args.permissions_matrix) if args.permissions_matrix else None
        if pm_path:
            actors = _extract_actors(pm_path)
        else:
            actors = []
        ranges = emit_us_ranges(actors)
        print(json.dumps({"ranges": ranges}, indent=2))
        return 0

    if args.op:
        if not args.file:
            print("error: --op requires --file", file=sys.stderr)
            return 2
        result = estimate_op(args.op, Path(args.file), max_loc=args.max_loc)
        print(json.dumps(result, indent=2))
        return 0

    if not args.artifact:
        print("error: one of --artifact or --op is required", file=sys.stderr)
        return 2

    result = estimate(
        artifact=args.artifact,
        max_loc=args.max_loc,
        route_list=Path(args.route_list) if args.route_list else None,
        scout_report=Path(args.scout_report) if args.scout_report else None,
        plan_dir=Path(args.plan_dir) if args.plan_dir else None,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
