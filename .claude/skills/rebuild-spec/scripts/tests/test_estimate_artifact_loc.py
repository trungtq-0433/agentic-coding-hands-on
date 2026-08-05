"""Tests for estimate_artifact_loc.py — pre-gen artifact LOC estimator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
from estimate_artifact_loc import (  # noqa: E402
    estimate,
    estimate_op,
    DESCRIPTORS,
    _count_inventory_by_type,
    _count_bl_inventory,
    _count_total_inventory,
    _extract_actors,
    MONOLITHIC_ROUTE_FLOOR,
    MONOLITHIC_LARGE_REPO_THRESHOLD,
    ROUTE_ROWS_PER_FILE,
)


def _write_scout(plan_dir, *, file_inventory="", bl_inventory=""):
    """Write a scout-report.md with the given File Inventory / BL Inventory bodies."""
    scout = plan_dir / "artifacts" / "scout-report.md"
    scout.write_text(
        "# Scout Report\n\n## Detected Language\nTypeScript\n\n"
        f"## File Inventory\n\n{file_inventory}\n\n"
        f"## Background Logic Source Inventory\n\n### TypeScript\n{bl_inventory}\n\n"
        "## Notes\n- none\n"
    )
    return scout


def _inv(entries):
    """Build TAB-separated File Inventory lines from (path, type) tuples."""
    return "\n".join(f"{p}\t{t}" for p, t in entries)


@pytest.fixture
def tmp_plan(tmp_path):
    """Create a minimal plan dir with artifacts subdir."""
    arts = tmp_path / "artifacts"
    arts.mkdir()
    return tmp_path


@pytest.fixture
def small_route_list(tmp_path):
    rl = tmp_path / "route-list.md"
    rl.write_text(
        "| Method | Path | Handler | Middleware |\n"
        "|--------|------|---------|------------|\n"
        "| GET | /api/users | UserController@index | auth |\n"
        "| POST | /api/users | UserController@store | auth |\n"
        "| GET | /api/posts | PostController@index | auth |\n"
    )
    return rl


@pytest.fixture
def large_route_list(tmp_path):
    rl = tmp_path / "route-list.md"
    lines = ["| Method | Path | Handler | Middleware |", "|--------|------|---------|------------|"]
    for i in range(260):
        lines.append(f"| GET | /api/resource{i} | Ctrl{i}@index | auth |")
    rl.write_text("\n".join(lines))
    return rl


class TestApiContracts:
    def test_small_route_list_no_shard(self, small_route_list):
        r = estimate("api-contracts", route_list=small_route_list)
        assert r["shard"] is False
        assert r["unit_count"] == 3
        assert r["est_loc"] == 48  # 3 * 16

    def test_large_route_list_shard(self, large_route_list):
        r = estimate("api-contracts", route_list=large_route_list)
        assert r["shard"] is True
        assert r["unit_count"] == 260
        assert r["est_loc"] == 4160  # 260 * 16
        assert r["slice_key"] == "resource namespace"

    def test_no_route_list_no_shard(self):
        r = estimate("api-contracts")
        assert r["shard"] is False
        assert r["unit_count"] == 0

    def test_header_sep_rows_excluded(self, tmp_path):
        rl = tmp_path / "route-list.md"
        rl.write_text(
            "| Method | Path | Handler |\n"
            "|--------|------|---------|\n"
            "| Method | Path | Handler |\n"  # repeated header
            "|:-------|:-----|:--------|\n"  # separator variant
        )
        r = estimate("api-contracts", route_list=rl)
        assert r["unit_count"] == 0


class TestDataModel:
    def test_fixed_threshold_below(self, tmp_plan):
        dm = tmp_plan / "artifacts" / "data-model.md"
        lines = []
        for i in range(30):
            lines.append(f"### MODEL{i:03d}_Entity{i}")
        dm.write_text("\n".join(lines))
        r = estimate("data-model", plan_dir=tmp_plan)
        assert r["shard"] is False
        assert r["unit_count"] == 30

    def test_fixed_threshold_above(self, tmp_plan):
        dm = tmp_plan / "artifacts" / "data-model.md"
        lines = []
        for i in range(45):
            lines.append(f"### MODEL{i:03d}_Entity{i}")
        dm.write_text("\n".join(lines))
        r = estimate("data-model", plan_dir=tmp_plan)
        assert r["shard"] is True
        assert r["unit_count"] == 45


class TestMaxLocOverride:
    def test_custom_max_loc_changes_boundary(self, large_route_list):
        r_default = estimate("api-contracts", route_list=large_route_list, max_loc=800)
        assert r_default["shard"] is True

        r_high = estimate("api-contracts", route_list=large_route_list, max_loc=5000)
        assert r_high["shard"] is False
        assert r_high["unit_count"] == 260

    def test_data_model_ignores_max_loc(self, tmp_plan):
        """data-model uses fixed threshold (>=40), not est_loc > max_loc."""
        dm = tmp_plan / "artifacts" / "data-model.md"
        lines = [f"### MODEL{i:03d}_E{i}" for i in range(45)]
        dm.write_text("\n".join(lines))
        r = estimate("data-model", plan_dir=tmp_plan, max_loc=99999)
        assert r["shard"] is True  # fixed threshold, max_loc irrelevant


class TestFeatureList:
    def test_lpu_42_boundary_below(self, tmp_plan):
        fl = tmp_plan / "artifacts" / "feature-list.md"
        lines = [f"### F{i:03d}_Feature{i}" for i in range(18)]
        fl.write_text("\n".join(lines))
        r = estimate("feature-list", plan_dir=tmp_plan)
        assert r["unit_count"] == 18
        assert r["est_loc"] == 756  # 18 * 42 = 756 < 800
        assert r["shard"] is False

    def test_lpu_42_boundary_above(self, tmp_plan):
        fl = tmp_plan / "artifacts" / "feature-list.md"
        lines = [f"### F{i:03d}_Feature{i}" for i in range(20)]
        fl.write_text("\n".join(lines))
        r = estimate("feature-list", plan_dir=tmp_plan)
        assert r["unit_count"] == 20
        assert r["est_loc"] == 840  # 20 * 42 = 840 > 800
        assert r["shard"] is True
        assert r["slice_key"] == "expand by F### batch"


class TestRouteList:
    def test_lpu_2_small(self, small_route_list):
        r = estimate("route-list", route_list=small_route_list)
        assert r["unit_count"] == 3
        assert r["est_loc"] == 6
        assert r["shard"] is False

    def test_lpu_2_large(self, tmp_path):
        rl = tmp_path / "route-list.md"
        lines = ["| Method | Path | Handler |", "|--------|------|---------|"]
        for i in range(500):
            lines.append(f"| GET | /api/r{i} | C{i}@i | auth |")
        rl.write_text("\n".join(lines))
        r = estimate("route-list", route_list=rl)
        assert r["shard"] is True
        assert r["unit_count"] == 500


class TestUnknownArtifact:
    def test_unknown_returns_no_shard(self):
        r = estimate("unknown")
        assert r["shard"] is False
        assert r["slice_key"] is None


class TestFirstGen:
    """First-generation dispatch: the artifact's own output file does NOT exist yet, so the
    estimate must come from the scout report (or an already-generated upstream artifact).
    These are the paths that previously returned unit_count=0 → shard:false → monolithic hang.
    """

    def test_behavior_logic_from_scout_bl_inventory_shards(self, tmp_plan):
        bl = "\n".join(f"- service: app/services/svc{i}.ts" for i in range(40))
        _write_scout(tmp_plan, bl_inventory=bl)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("behavior-logic", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 40  # 1 BL per inventory entry
        assert r["est_loc"] == 1000  # 40 * 25
        assert r["shard"] is True

    def test_behavior_logic_small_no_shard(self, tmp_plan):
        bl = "\n".join(f"- mail: app/mail/m{i}.ts" for i in range(5))
        _write_scout(tmp_plan, bl_inventory=bl)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("behavior-logic", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 5
        assert r["shard"] is False

    def test_behavior_logic_skips_none_found_sentinel(self, tmp_plan):
        bl = "- observer: _(none found)_\n- queue-worker: app/jobs/j1.ts"
        _write_scout(tmp_plan, bl_inventory=bl)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("behavior-logic", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 1  # sentinel excluded

    def test_screen_list_from_scout_file_inventory_shards(self, tmp_plan):
        inv = _inv([(f"src/pages/P{i}.tsx", "screen") for i in range(50)]
                   + [("src/routes.ts", "route"), ("src/models/U.ts", "model")])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("screen-list", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 50  # only screen-type counted
        assert r["est_loc"] == 950  # 50 * 19
        assert r["shard"] is True

    def test_screen_flow_shares_screen_signal(self, tmp_plan):
        inv = _inv([(f"src/pages/P{i}.tsx", "screen") for i in range(90)])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("screen-flow", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 90
        assert r["shard"] is True  # 90 * 10 = 900 > 800

    def test_screen_flow_below_threshold(self, tmp_plan):
        inv = _inv([(f"src/pages/P{i}.tsx", "screen") for i in range(10)])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("screen-flow", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 10
        assert r["shard"] is False  # 10 * 10 = 100

    def test_route_list_from_scout_route_files_shards(self, tmp_plan):
        # No route-list.md yet; 40 route files * 12 rows/file = 480 units * lpu 2 = 960 > 800.
        inv = _inv([(f"src/routes/r{i}.ts", "route") for i in range(40)])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 480  # 40 * 12
        assert r["shard"] is True

    def test_route_list_few_files_no_shard(self, tmp_plan):
        inv = _inv([("src/routes/api.ts", "route"), ("src/routes/web.ts", "route")])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 24  # 2 * 12
        assert r["shard"] is False

    def test_data_model_from_scout_typed_inventory(self, tmp_plan):
        inv = _inv([(f"src/models/M{i}.ts", "model") for i in range(45)])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("data-model", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 45
        assert r["shard"] is True  # >= 40 fixed threshold

    def test_user_stories_from_screen_list_when_us_and_fl_absent(self, tmp_plan):
        # W4 reality: user-stories.md + feature-list.md don't exist; screen-list.md does.
        sl = tmp_plan / "artifacts" / "screen-list.md"
        sl.write_text("\n".join(f"## SCR{i:03d}_Screen{i}" for i in range(30)))
        r = estimate("user-stories", plan_dir=tmp_plan)
        assert r["unit_count"] == 45  # ceil(30 * 1.5)
        assert r["est_loc"] == 1485  # 45 * 33
        assert r["shard"] is True

    def test_user_stories_prefers_own_file_on_rerun(self, tmp_plan):
        us = tmp_plan / "artifacts" / "user-stories.md"
        us.write_text("\n".join(f"## US{i:03d}" for i in range(10)))
        sl = tmp_plan / "artifacts" / "screen-list.md"
        sl.write_text("\n".join(f"## SCR{i:03d}_S{i}" for i in range(30)))
        r = estimate("user-stories", plan_dir=tmp_plan)
        assert r["unit_count"] == 10  # own file wins over screen-list fallback


class TestRouteListShardGuards:
    """Phase-03 fix: monolithic single-file + compressed-rerun guards for route-list shard sizing.

    route-list: avg_lpu=2, threshold=max_loc=800. Shard when unit_count * 2 > 800 (unit_count > 400).
    MONOLITHIC_ROUTE_FLOOR=500 → est_loc=1000 > 800 → shard:true.
    """

    def test_monolithic_route_file_large_repo_shards(self, tmp_plan):
        """(a) 1 route file + large repo (total_inventory ≥ MONOLITHIC_LARGE_REPO_THRESHOLD)
        → unit_count raised to MONOLITHIC_ROUTE_FLOOR → shard:true."""
        # 1 route file + 55 controller files → total_inventory = 56 ≥ 50 → guard fires
        inv_lines = [("src/routes/web.php", "route")]
        inv_lines += [(f"src/app/Controllers/C{i}.php", "other") for i in range(55)]
        inv = _inv(inv_lines)
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", scout_report=scout)
        assert r["unit_count"] == MONOLITHIC_ROUTE_FLOOR  # 500
        assert r["shard"] is True  # 500 * 2 = 1000 > 800

    def test_compressed_rerun_uses_scout_fallback_shards(self, tmp_plan):
        """(b) Compressed route-list (0 METHOD rows) + 40 scout route files
        → unit_count = max(0, 40 * ROUTE_ROWS_PER_FILE) = 480 → shard:true.

        Note: phase spec loosely references 30 files, but 30*12*2=720 < 800 (no shard).
        40 files yields 480*2=960 > 800, which satisfies the shard:true requirement.
        """
        compressed_rl = tmp_plan / "route-list.md"
        compressed_rl.write_text(
            "## Backend Routes\n\n"
            "| Resource | Actions |\n"
            "|----------|--------|\n"
            "| users | index, show, create, update, destroy |\n"
            "| orders | index, show |\n\n"
            "## Summary\n\n~40 resources\n"
        )
        inv = _inv([(f"src/routes/r{i}.ts", "route") for i in range(40)])
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", route_list=compressed_rl, scout_report=scout)
        # _count_route_data_rows(compressed_rl) = 0 (no METHOD rows) → max(0, 40*12) = 480
        assert r["unit_count"] == 40 * ROUTE_ROWS_PER_FILE  # 480
        assert r["shard"] is True  # 480 * 2 = 960 > 800

    def test_small_project_single_route_file_no_shard(self, tmp_plan):
        """(c) 1 route file + small repo (total_inventory < MONOLITHIC_LARGE_REPO_THRESHOLD)
        → no monolithic guard → shard:false (no regression)."""
        # 10 total files — below MONOLITHIC_LARGE_REPO_THRESHOLD=50
        inv_lines = [("src/routes/api.ts", "route")]
        inv_lines += [(f"src/components/C{i}.tsx", "screen") for i in range(9)]
        inv = _inv(inv_lines)
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", scout_report=scout)
        # total_inventory=10 < 50 → guard does not fire; unit_count = 1 * ROUTE_ROWS_PER_FILE
        assert r["unit_count"] == 1 * ROUTE_ROWS_PER_FILE  # 12
        assert r["shard"] is False  # 12 * 2 = 24 < 800

    def test_two_route_files_large_repo_monolithic_guard_fires(self, tmp_plan):
        """2 route files ≤ 2 threshold + large repo → monolithic guard fires → shard:true."""
        inv_lines = [("src/routes/api.ts", "route"), ("src/routes/web.ts", "route")]
        inv_lines += [(f"src/models/M{i}.ts", "model") for i in range(60)]
        inv = _inv(inv_lines)
        _write_scout(tmp_plan, file_inventory=inv)
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("route-list", scout_report=scout)
        # scout_route_files=2 ≤ 2, total_inventory=62 ≥ 50 → guard fires
        assert r["unit_count"] == MONOLITHIC_ROUTE_FLOOR  # 500
        assert r["shard"] is True


class TestNoSignalDefaultsSingle:
    """No usable signal anywhere → unit_count 0 → no shard (single task), never a false shard."""

    def test_feature_list_no_files(self, tmp_plan):
        r = estimate("feature-list", plan_dir=tmp_plan)
        assert r["unit_count"] == 0
        assert r["shard"] is False

    def test_behavior_logic_empty_scout(self, tmp_plan):
        _write_scout(tmp_plan, bl_inventory="- observer: _(none found)_")
        scout = tmp_plan / "artifacts" / "scout-report.md"
        r = estimate("behavior-logic", scout_report=scout, plan_dir=tmp_plan)
        assert r["unit_count"] == 0
        assert r["shard"] is False


class TestModelHeadingNoOvercount:
    def test_generic_h3_headings_not_counted(self, tmp_plan):
        dm = tmp_plan / "artifacts" / "data-model.md"
        lines = [f"### MODEL{i:03d}_E{i}" for i in range(38)]
        lines += ["### Notes", "### Overview", "### Relationships"]  # generic, must NOT count
        dm.write_text("\n".join(lines))
        r = estimate("data-model", plan_dir=tmp_plan)
        assert r["unit_count"] == 38  # generic headings excluded
        assert r["shard"] is False  # 38 < 40 fixed threshold


class TestHelpers:
    def test_count_inventory_by_type(self, tmp_plan):
        inv = _inv([("a.tsx", "screen"), ("b.ts", "route"), ("c.tsx", "screen")])
        scout = _write_scout(tmp_plan, file_inventory=inv)
        assert _count_inventory_by_type(scout, "screen") == 2
        assert _count_inventory_by_type(scout, "route") == 1
        assert _count_inventory_by_type(scout, "model") == 0

    def test_count_inventory_stops_at_next_section(self, tmp_plan):
        # A `route`-looking token in a later section must not be counted.
        inv = _inv([("a.tsx", "screen")])
        scout = _write_scout(tmp_plan, file_inventory=inv, bl_inventory="- x: y.ts route")
        assert _count_inventory_by_type(scout, "route") == 0

    def test_count_bl_inventory_skips_sentinel(self, tmp_plan):
        bl = "- a: x.ts\n- b: _(none found)_\n- c: z.ts"
        scout = _write_scout(tmp_plan, bl_inventory=bl)
        assert _count_bl_inventory(scout) == 2

    def test_extract_actors_from_permission_rules(self, tmp_plan):
        pm = tmp_plan / "artifacts" / "permissions-matrix.md"
        pm.write_text(
            "# Permissions Matrix\n\n"
            "## PERM001: View Reports\n\n### Permission Rules\n\n"
            "| Role | Allow | Conditions |\n|------|-------|------------|\n"
            "| Admin | ✓ | - |\n| Editor | ✗ | - |\n\n"
            "## PERM002: Edit Users\n\n### Permission Rules\n\n"
            "| Role | Allow | Conditions |\n|------|-------|------------|\n"
            "| Admin | ✓ | - |\n| Viewer | ✗ | - |\n"
        )
        actors = _extract_actors(pm)
        assert actors == ["Admin", "Editor", "Viewer"]  # distinct roles, sorted; no PERM codes

    def test_extract_actors_empty_when_missing(self, tmp_path):
        assert _extract_actors(tmp_path / "nope.md") == []


class TestCli:
    def test_cli_exit_0(self, small_route_list):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "estimate_artifact_loc.py"),
                "--artifact", "api-contracts",
                "--route-list", str(small_route_list),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["shard"] is False

    def test_cli_max_loc_override(self, small_route_list):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "estimate_artifact_loc.py"),
                "--artifact", "api-contracts",
                "--route-list", str(small_route_list),
                "--max-loc", "1",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["shard"] is True


class TestPhaseBDigestDescriptors:
    """Phase B (v11.1.0): crud-matrix / db-objects estimate from Wave 0.6 digests."""

    def _plan(self, tmp_path):
        plan = tmp_path / "plan"
        (plan / "artifacts").mkdir(parents=True)
        return plan

    def test_db_objects_counts_digest_objects(self, tmp_path):
        plan = self._plan(tmp_path)
        (plan / "artifacts" / "_digest_extract_sql_schema.json").write_text(json.dumps({
            "db_objects": [{"kind": "table", "name": f"T{i}"} for i in range(150)]
        }))
        r = estimate("db-objects", plan_dir=plan, max_loc=800)
        assert r["unit_count"] == 150
        assert r["shard"] is True  # 150 * 6 = 900 > 800

    def test_crud_matrix_counts_distinct_tables(self, tmp_path):
        plan = self._plan(tmp_path)
        (plan / "artifacts" / "_digest_extract_data_flow.json").write_text(json.dumps({
            "units": [
                {"db_ops": [{"table": "ORDERS", "op": "C"}, {"table": "ORDERS", "op": "R"}]},
                {"db_ops": [{"table": "ITEMS", "op": "U"}]},
            ]
        }))
        r = estimate("crud-matrix", plan_dir=plan, max_loc=800)
        assert r["unit_count"] == 2  # distinct tables: ORDERS, ITEMS
        assert r["slice_key"] == "F### range"

    def test_missing_digest_is_zero_not_crash(self, tmp_path):
        plan = self._plan(tmp_path)
        r = estimate("crud-matrix", plan_dir=plan, max_loc=800)
        assert r["unit_count"] == 0
        assert r["shard"] is False


# ---------------------------------------------------------------------------
# --op translate|rewrite  (Phase C output-guard extension)
# ---------------------------------------------------------------------------

class TestEstimateOp:
    def _write_file(self, path: Path, n_lines: int) -> Path:
        path.write_text("\n".join(f"line {i}" for i in range(n_lines)) + "\n",
                        encoding="utf-8")
        return path

    # --- translate ---

    def test_translate_small_file_chunk_false(self, tmp_path):
        f = self._write_file(tmp_path / "small.md", 50)
        r = estimate_op("translate", f, max_loc=800)
        assert r["op"] == "translate"
        assert r["chunk"] is False
        assert r["est_loc"] > 0
        assert r["max_loc"] == 800

    def test_translate_large_file_chunk_true(self, tmp_path):
        # 1000 source lines × 1.05 = 1050 > 800
        f = self._write_file(tmp_path / "large.md", 1000)
        r = estimate_op("translate", f, max_loc=800)
        assert r["chunk"] is True
        assert r["est_loc"] > 800

    def test_translate_boundary_exactly_at_threshold_false(self, tmp_path):
        # 761 lines × 1.05 = ceil(799.05) = 800 → NOT over threshold (not >800)
        f = self._write_file(tmp_path / "boundary.md", 761)
        r = estimate_op("translate", f, max_loc=800)
        assert r["chunk"] is False

    def test_translate_one_over_boundary_chunk_true(self, tmp_path):
        # 762 lines × 1.05 = ceil(800.1) = 801 → chunk
        f = self._write_file(tmp_path / "over.md", 762)
        r = estimate_op("translate", f, max_loc=800)
        assert r["chunk"] is True

    def test_translate_missing_file_no_crash(self, tmp_path):
        r = estimate_op("translate", tmp_path / "missing.md", max_loc=800)
        assert r["chunk"] is False
        assert r["est_loc"] == 0
        assert "not found" in r["reason"]

    # --- rewrite ---

    def test_rewrite_small_file_chunk_false(self, tmp_path):
        f = self._write_file(tmp_path / "small.md", 50)
        r = estimate_op("rewrite", f, max_loc=800)
        assert r["op"] == "rewrite"
        assert r["chunk"] is False

    def test_rewrite_large_file_chunk_true(self, tmp_path):
        # 800 source lines × 1.15 = 920 > 800
        f = self._write_file(tmp_path / "large.md", 800)
        r = estimate_op("rewrite", f, max_loc=800)
        assert r["chunk"] is True
        assert r["est_loc"] > 800

    def test_rewrite_has_higher_multiplier_than_translate(self, tmp_path):
        # Same input file → rewrite must produce >= translate LOC estimate
        f = self._write_file(tmp_path / "doc.md", 200)
        tr = estimate_op("translate", f, max_loc=800)
        rw = estimate_op("rewrite", f, max_loc=800)
        assert rw["est_loc"] >= tr["est_loc"]

    # --- custom max_loc ---

    def test_custom_max_loc_honoured(self, tmp_path):
        f = self._write_file(tmp_path / "doc.md", 100)
        r = estimate_op("translate", f, max_loc=50)
        assert r["chunk"] is True
        assert r["max_loc"] == 50

    # --- CLI subprocess path ---

    def test_cli_op_translate(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("\n".join(f"line {i}" for i in range(1000)), encoding="utf-8")
        script = SCRIPTS / "estimate_artifact_loc.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--op", "translate", "--file", str(f)],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["op"] == "translate"
        assert data["chunk"] is True

    def test_cli_op_requires_file(self, tmp_path):
        script = SCRIPTS / "estimate_artifact_loc.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--op", "translate"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 2

    def test_cli_no_artifact_no_op_exits_error(self):
        script = SCRIPTS / "estimate_artifact_loc.py"
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode != 0
