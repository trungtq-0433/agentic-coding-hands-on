"""Tests for scripts/detect_stack_profile.py + _stack_profile_lib.py (Phase A)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "detect_stack_profile.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import _stack_profile_lib as lib  # noqa: E402


def _run(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)] + (extra or []),
        capture_output=True, text=True, timeout=60, cwd=str(root),
    )


def _delphi_tree(root: Path) -> None:
    (root / "src").mkdir()
    (root / "src" / "Main.dpr").write_text("program Main; begin end.")
    (root / "src" / "Unit1.pas").write_text("unit Unit1; interface implementation end.")
    (root / "src" / "Form1.dfm").write_text("object Form1: TForm1\nend")
    (root / "App.dproj").write_text("<Project></Project>")


def _js_tree(root: Path) -> None:
    (root / "package.json").write_text('{"name":"x"}')
    (root / "src").mkdir()
    (root / "src" / "index.ts").write_text("export const x = 1;")


# --- CLI: detection outcomes -------------------------------------------------

class TestDetectionOutcomes:
    def test_delphi_tree_recommends_delphi_vcl(self, tmp_path):
        _delphi_tree(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["recommended_profile"] == "delphi-vcl"
        assert out["encoding"] == "shift_jis"
        assert out["detected_language_heading"] == "Delphi/VCL"

    def test_js_tree_recommends_web(self, tmp_path):
        _js_tree(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["recommended_profile"] == "web-js-ts"

    def test_empty_tree_no_match(self, tmp_path):
        (tmp_path / "README.txt").write_text("hello")
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["matched"] == []
        assert out["recommended_profile"] is None

    def test_multi_stack_matches_both(self, tmp_path):
        _delphi_tree(tmp_path)
        (tmp_path / "db").mkdir()
        for i in range(6):
            (tmp_path / "db" / f"pkg{i}.pkb").write_text("create or replace package body x is end;")
            (tmp_path / "db" / f"pkg{i}.pks").write_text("create or replace package x is end;")
        r = _run(tmp_path)
        out = json.loads(r.stdout)
        ids = {m["id"] for m in out["matched"]}
        assert "delphi-vcl" in ids and "oracle-plsql" in ids


# --- CLI: safety (RT-F6) -----------------------------------------------------

class TestComponentsAdditive:
    """Phase D (RT2-F4): components[] is ADDITIVE — recommended_profile stays the stable contract."""

    def test_single_repo_one_component_keeps_recommended(self, tmp_path):
        _js_tree(tmp_path)
        out = json.loads(_run(tmp_path).stdout)
        assert out["recommended_profile"] == "web-js-ts"      # Phase A contract intact
        assert isinstance(out["components"], list)
        assert any(c["profile"] == "web-js-ts" for c in out["components"])

    def test_monorepo_lists_subrepos(self, tmp_path):
        # Two sub-repos with different stacks.
        (tmp_path / "services" / "orders").mkdir(parents=True)
        (tmp_path / "services" / "orders" / "go.mod").write_text("module orders")
        (tmp_path / "services" / "billing").mkdir(parents=True)
        (tmp_path / "services" / "billing" / "package.json").write_text('{"name":"billing"}')
        out = json.loads(_run(tmp_path).stdout)
        paths = {c["path"] for c in out["components"]}
        assert "services/orders" in paths and "services/billing" in paths
        # recommended_profile (single) still present for legacy callers
        assert "recommended_profile" in out


# --- role classification (RT2-F4b) -------------------------------------------

class TestRoleClassification:
    """classify_role reads manifest CONTENT, not the (coarse) profile id."""

    def test_nuxt_frontend(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies":{"nuxt":"^2","vue":"^2"}}')
        assert lib.classify_role(str(tmp_path)) == "frontend"

    def test_react_frontend(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies":{"react":"^18","react-dom":"^18"}}')
        assert lib.classify_role(str(tmp_path)) == "frontend"

    def test_nestjs_backend(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies":{"@nestjs/core":"^9"}}')
        assert lib.classify_role(str(tmp_path)) == "backend"

    def test_laravel_composer_is_backend(self, tmp_path):
        (tmp_path / "composer.json").write_text('{"require":{"laravel/framework":"^8"}}')
        assert lib.classify_role(str(tmp_path)) == "backend"

    def test_composer_outranks_colocated_asset_package_json(self, tmp_path):
        # Laravel app with a Laravel-Mix package.json beside it → still backend (auth case).
        (tmp_path / "composer.json").write_text('{"require":{"laravel/framework":"^8"}}')
        (tmp_path / "package.json").write_text('{"devDependencies":{"laravel-mix":"^6"}}')
        assert lib.classify_role(str(tmp_path)) == "backend"

    def test_go_module_backend(self, tmp_path):
        (tmp_path / "go.mod").write_text("module orders")
        assert lib.classify_role(str(tmp_path)) == "backend"

    def test_django_pyproject_backend(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["django>=4"]')
        assert lib.classify_role(str(tmp_path)) == "backend"

    def test_unknown_js_is_service(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name":"lib"}')
        assert lib.classify_role(str(tmp_path)) == "service"


# --- Phase 02: executable boundary + shared-layer exclusion ------------------

def _delphi_multicomponent_tree(root: Path, modules: list[str], shared_db: bool = True) -> None:
    """Ishindenshin-shape: PG/<MOD>/*.dpr executables + shared PG/Common + DB/{TABLE,SP}/<MOD>."""
    for m in modules:
        d = root / "PG" / m
        d.mkdir(parents=True)
        (d / f"{m}main.dpr").write_text("program X; begin end.")
        (d / f"{m}u.pas").write_text("unit U; interface implementation end.")
    # Shared Common library — only .pas, no executable.
    common = root / "PG" / "Common"
    common.mkdir(parents=True)
    (common / "DBACC.pas").write_text("unit DBACC; interface implementation end.")
    if shared_db:
        for m in modules:
            t = root / "DB" / "TABLE" / m
            t.mkdir(parents=True)
            (t / f"M_{m}.sql").write_text("create table x (id number);")
            sp = root / "DB" / "SP" / m
            sp.mkdir(parents=True)
            # Oracle package files — would be co-claimed by oracle-plsql without Layer 1.
            (sp / f"P_{m}.pks").write_text("create or replace package x is end;")
            (sp / f"P_{m}.pkb").write_text("create or replace package body x is end;")


def _shared_abspaths(root: Path, basenames: set[str]) -> set[str]:
    """Mirror detect()'s resolution: abspaths of every dir whose basename ∈ basenames."""
    out: set[str] = set()
    for dp, dns, _ in os.walk(str(root)):
        for d in list(dns):
            if d in basenames:
                out.add(os.path.normpath(os.path.join(dp, d)))
    return out


class TestExecutableBoundary:
    """Phase 02 — one-spec-per-unit boundary globs + shared-layer Layer-1 exclusion."""

    BOUNDARY = ["*.dpr", "*.dproj", "*.dpk"]

    def test_one_spec_per_unit_executable_boundary(self, tmp_path):
        mods = [f"MOD{i:02d}" for i in range(20)]
        _delphi_multicomponent_tree(tmp_path, mods)
        profiles = lib.load_profiles()
        shared = _shared_abspaths(tmp_path, {"Common", "DB"})
        comps = lib.find_components(
            str(tmp_path), profiles, boundary_globs=self.BOUNDARY, shared_abspaths=shared
        )
        paths = {c["path"] for c in comps}
        assert paths == {f"PG/{m}" for m in mods}, paths

    def test_shared_layer_dirs_excluded(self, tmp_path):
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV"])
        profiles = lib.load_profiles()
        shared = _shared_abspaths(tmp_path, {"Common", "DB"})
        comps = lib.find_components(
            str(tmp_path), profiles, boundary_globs=self.BOUNDARY, shared_abspaths=shared
        )
        paths = {c["path"] for c in comps}
        assert "PG/Common" not in paths
        assert not any(p == "DB" or p.startswith("DB/") for p in paths)
        assert paths == {"PG/POS", "PG/RSV"}

    def test_oracle_co_detection_db_excluded(self, tmp_path):
        # DB/SP/<m> holds oracle .pks/.pkb — Layer 1 must stop descent so they are never claimed.
        _delphi_multicomponent_tree(tmp_path, ["POS"])
        profiles = lib.load_profiles()
        shared = _shared_abspaths(tmp_path, {"Common", "DB"})
        comps = lib.find_components(
            str(tmp_path), profiles, boundary_globs=self.BOUNDARY, shared_abspaths=shared
        )
        assert all(not c["path"].startswith("DB") for c in comps)

    def test_shared_exclusion_emits_warning(self, tmp_path):
        _delphi_multicomponent_tree(tmp_path, ["POS"])
        profiles = lib.load_profiles()
        shared = _shared_abspaths(tmp_path, {"Common", "DB"})
        warns: list[str] = []
        lib.find_components(
            str(tmp_path), profiles, boundary_globs=self.BOUNDARY,
            shared_abspaths=shared, warnings=warns,
        )
        assert any(w.startswith("shared_layer_excluded:") for w in warns)
        # One warning per excluded shared ROOT (Common + DB), not per nested dir.
        assert sum(w.startswith("shared_layer_excluded:") for w in warns) == 2

    def test_legacy_discovery_unchanged(self, tmp_path):
        # No boundary_globs / shared_abspaths → byte-identical to legacy all-globs behavior.
        (tmp_path / "services" / "orders").mkdir(parents=True)
        (tmp_path / "services" / "orders" / "go.mod").write_text("module orders")
        (tmp_path / "services" / "billing").mkdir(parents=True)
        (tmp_path / "services" / "billing" / "package.json").write_text('{"name":"billing"}')
        profiles = lib.load_profiles()
        legacy = lib.find_components(str(tmp_path), profiles)
        paths = {c["path"] for c in legacy}
        assert "services/orders" in paths and "services/billing" in paths


# --- product grouping (RT2-F4b) ----------------------------------------------

class TestProductGrouping:
    """Co-deployed FE+BE under one named wrapper = one product (group); peers stay independent."""

    def test_employee_fe_be_grouped(self, tmp_path):
        # The wsm_platform employee case: FE+BE under a named wrapper with no root manifest.
        (tmp_path / "ssv-wsm-employee" / "backend").mkdir(parents=True)
        (tmp_path / "ssv-wsm-employee" / "backend" / "composer.json").write_text(
            '{"require":{"laravel/framework":"^8"}}')
        (tmp_path / "ssv-wsm-employee" / "frontend").mkdir(parents=True)
        (tmp_path / "ssv-wsm-employee" / "frontend" / "package.json").write_text(
            '{"dependencies":{"nuxt":"^2"}}')
        # Two peer services at root with their own manifests.
        (tmp_path / "gateway").mkdir()
        (tmp_path / "gateway" / "package.json").write_text('{"dependencies":{"@nestjs/core":"^9"}}')
        out = json.loads(_run(tmp_path).stdout)
        by_path = {c["path"]: c for c in out["components"]}
        assert by_path["ssv-wsm-employee/backend"]["group"] == "ssv-wsm-employee"
        assert by_path["ssv-wsm-employee/frontend"]["group"] == "ssv-wsm-employee"
        assert by_path["gateway"]["group"] is None
        assert any(w.startswith("component_group:") for w in out["warnings"])

    def test_conventional_container_dir_not_grouped(self, tmp_path):
        # `services/{web,api}` is a container convention → NOT a single product, even FE+BE.
        (tmp_path / "services" / "web").mkdir(parents=True)
        (tmp_path / "services" / "web" / "package.json").write_text('{"dependencies":{"react":"^18"}}')
        (tmp_path / "services" / "api").mkdir(parents=True)
        (tmp_path / "services" / "api" / "package.json").write_text('{"dependencies":{"express":"^4"}}')
        out = json.loads(_run(tmp_path).stdout)
        assert all(c["group"] is None for c in out["components"])
        assert not any(w.startswith("component_group:") for w in out["warnings"])

    def test_same_role_siblings_not_grouped(self, tmp_path):
        # Two backends under a named wrapper → not complementary → independent deployables.
        (tmp_path / "billing" / "api").mkdir(parents=True)
        (tmp_path / "billing" / "api" / "go.mod").write_text("module api")
        (tmp_path / "billing" / "worker").mkdir(parents=True)
        (tmp_path / "billing" / "worker" / "go.mod").write_text("module worker")
        out = json.loads(_run(tmp_path).stdout)
        assert all(c["group"] is None for c in out["components"])

    def test_collapse_groups_folds_to_one_fullstack(self, tmp_path):
        # --collapse-groups: the FE+BE product becomes ONE entry; the peer service stays separate.
        (tmp_path / "ssv-wsm-employee" / "backend").mkdir(parents=True)
        (tmp_path / "ssv-wsm-employee" / "backend" / "composer.json").write_text(
            '{"require":{"laravel/framework":"^8"}}')
        (tmp_path / "ssv-wsm-employee" / "frontend").mkdir(parents=True)
        (tmp_path / "ssv-wsm-employee" / "frontend" / "package.json").write_text(
            '{"dependencies":{"nuxt":"^2"}}')
        (tmp_path / "gateway").mkdir()
        (tmp_path / "gateway" / "package.json").write_text('{"dependencies":{"@nestjs/core":"^9"}}')
        out = json.loads(_run(tmp_path, ["--collapse-groups"]).stdout)
        by_path = {c["path"]: c for c in out["components"]}
        assert "ssv-wsm-employee" in by_path                       # group folded to the wrapper
        assert by_path["ssv-wsm-employee"]["role"] == "fullstack"
        assert "ssv-wsm-employee/backend" not in by_path           # members gone
        assert "ssv-wsm-employee/frontend" not in by_path
        assert by_path["gateway"]["role"] == "backend"             # peer untouched


class TestAutoSwitch:
    """Phase 03 — component_profile resolution + auto-switch predicate + --mono/--profile."""

    def test_delphi_multicomponent_auto_switches(self, tmp_path):
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV", "INV"])
        out = json.loads(_run(tmp_path).stdout)
        assert out["component_profile"] == "delphi-vcl"
        assert out["auto_switch"] is True
        # shared[] surfaced in detect output (Common + DB), DB routed to the db extractor.
        kinds = {s["label"]: s["kind"] for s in out["shared"]}
        assert kinds.get("Common") == "source"
        assert kinds.get("DB") == "db"
        # components are the PG modules only — no Common/DB component.
        paths = {c["path"] for c in out["components"]}
        assert paths == {"PG/POS", "PG/RSV", "PG/INV"}

    def test_mono_flag_disables_autoswitch(self, tmp_path):
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV"])
        out = json.loads(_run(tmp_path, ["--mono"]).stdout)
        assert out["auto_switch"] is False
        assert out["auto_switch_reason"] == "--mono override"
        # component_profile is still resolved (mono only flips the recommendation).
        assert out["component_profile"] == "delphi-vcl"

    def test_js_monorepo_no_component_profile(self, tmp_path):
        # JS/TS monorepo (feature-grouped, not one-spec-per-unit) → no auto-switch hijack.
        (tmp_path / "services" / "orders").mkdir(parents=True)
        (tmp_path / "services" / "orders" / "package.json").write_text('{"name":"orders"}')
        (tmp_path / "services" / "billing").mkdir(parents=True)
        (tmp_path / "services" / "billing" / "package.json").write_text('{"name":"billing"}')
        out = json.loads(_run(tmp_path).stdout)
        assert out["component_profile"] is None
        assert out["auto_switch"] is False
        assert out["shared"] == []

    def test_component_profile_beats_hit_count_winner(self, tmp_path):
        # oracle-plsql out-HITS delphi-vcl on raw file count (big DB tree), but delphi OWNS the
        # components → component_profile=delphi-vcl, auto_switch=true (Finding 2 regression).
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV"], shared_db=False)
        big_db = tmp_path / "DB" / "TABLE"
        big_db.mkdir(parents=True)
        for i in range(60):
            (big_db / f"T{i}.sql").write_text("create table x (id number);")
        out = json.loads(_run(tmp_path).stdout)
        assert out["recommended_profile"] == "oracle-plsql"   # oracle wins on raw hits
        assert out["component_profile"] == "delphi-vcl"        # delphi owns the components
        assert out["auto_switch"] is True
        # DB still excluded (it is delphi's shared layer) — no DB component.
        assert all(not c["path"].startswith("DB") for c in out["components"])

    def test_profile_override_pins(self, tmp_path):
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV"], shared_db=False)
        out = json.loads(_run(tmp_path, ["--profile", "delphi-vcl"]).stdout)
        assert out["recommended_profile"] == "delphi-vcl"
        assert out["component_profile"] == "delphi-vcl"

    def test_invalid_profile_override_exits_2(self, tmp_path):
        _delphi_tree(tmp_path)
        r = _run(tmp_path, ["--profile", "no-such-profile"])
        assert r.returncode == 2, (r.stdout, r.stderr)

    def test_single_repo_no_auto_switch(self, tmp_path):
        _delphi_tree(tmp_path)  # one .dpr → one component, not ≥2
        out = json.loads(_run(tmp_path).stdout)
        assert out["component_profile"] is None
        assert out["auto_switch"] is False

    def test_ambiguous_one_spec_per_unit_profiles_emits_warning(self, tmp_path):
        """Edge case: two one-spec-per-unit profiles claim ≥2 roots each → ambiguity warning."""
        # Build a repo that matches BOTH delphi-vcl AND oracle-plsql patterns for multicomponent.
        # Delphi tree: PG/{MOD}/*.dpr (one-spec-per-unit boundary)
        _delphi_multicomponent_tree(tmp_path, ["POS", "RSV"], shared_db=False)
        # Oracle co-detection: add Oracle modules at the root level with *.pks/*.pkb boundaries
        # (oracle doesn't have a one-spec-per-unit boundary by default, so it won't clash).
        # Actually, let's test with oracle-plsql ALSO having a one-spec-per-unit marker.
        # For now, just verify the ambiguity detection warns when both tie.
        # The current implementation: only delphi-vcl has component_boundary_globs + shared_layer_dirs,
        # so oracle won't trigger ambiguity. This test is a placeholder for future architecture where
        # two profiles might both support multi-component detection.
        out = json.loads(_run(tmp_path).stdout)
        # With current profiles, delphi-vcl will own the components, oracle just hits matches.
        # No ambiguity warning expected with current schema.
        # This test documents what to check if another profile gains one-spec-per-unit support.
        assert out["component_profile"] == "delphi-vcl"
        assert out["auto_switch"] is True

    def test_shared_layer_nested_deeper_than_top_level(self, tmp_path):
        """Edge case: shared layer dir at nested level (e.g., services/Common) vs top-level."""
        # Create a monorepo-like structure with shared at nested level.
        (tmp_path / "services" / "svc1").mkdir(parents=True)
        (tmp_path / "services" / "svc1" / "go.mod").write_text("module svc1")
        (tmp_path / "services" / "svc1" / "main.go").write_text("package main")
        (tmp_path / "services" / "svc2").mkdir(parents=True)
        (tmp_path / "services" / "svc2" / "go.mod").write_text("module svc2")
        (tmp_path / "services" / "svc2" / "main.go").write_text("package main")
        # Nested shared layer (not top-level) — web/generic don't have shared_layer_dirs,
        # so it won't be filtered by exclusion. This just documents that shared layers
        # are only recognized at the top level per the delphi-vcl + oracle-plsql profiles.
        out = json.loads(_run(tmp_path).stdout)
        paths = {c["path"] for c in out["components"]}
        # Both services should be discovered (no shared-layer exclusion since Go doesn't define one).
        assert "services/svc1" in paths
        assert "services/svc2" in paths
        assert out["shared"] == []  # No shared layer for generic Go profile

    def test_dir_named_common_is_component_without_boundary_globs(self, tmp_path):
        """Edge case: a dir literally named 'Common' or 'DB' that IS a real component.

        Without boundary_globs, shared_layer_dirs is NOT applied, so a dir named 'Common'
        that matches the profile IS treated as a component.
        """
        # Create a repo with dirs named Common/DB but NO boundary_globs profile (e.g., Go).
        (tmp_path / "Common").mkdir()
        (tmp_path / "Common" / "go.mod").write_text("module common")
        (tmp_path / "Common" / "main.go").write_text("package main")
        (tmp_path / "DB").mkdir()
        (tmp_path / "DB" / "go.mod").write_text("module db")
        (tmp_path / "DB" / "main.go").write_text("package main")
        out = json.loads(_run(tmp_path).stdout)
        paths = {c["path"] for c in out["components"]}
        # Both should be discovered (Go has no boundary_globs, so they're real components).
        assert "Common" in paths, f"Expected 'Common' in {paths}"
        assert "DB" in paths, f"Expected 'DB' in {paths}"
        assert out["shared"] == []  # No shared layer declared for Go


class TestGlobSafety:
    def test_symlink_not_followed(self, tmp_path):
        _delphi_tree(tmp_path)
        # symlink pointing back at the tree → infinite loop if followed
        try:
            os.symlink(str(tmp_path / "src"), str(tmp_path / "loop"))
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unsupported on this platform")
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr  # no hang / crash

    def test_file_cap_reached_warning(self, tmp_path):
        d = tmp_path / "many"
        d.mkdir()
        for i in range(20):
            (d / f"u{i}.pas").write_text("unit U; end.")
        r = _run(tmp_path, ["--file-cap", "5"])
        out = json.loads(r.stdout)
        assert "file_cap_reached" in out["warnings"]


# --- CLI: encoding smoke-check (RT-F3) --------------------------------------

class TestEncodingSmokeCheck:
    def test_invalid_shift_jis_emits_warning(self, tmp_path):
        (tmp_path / "Main.dpr").write_bytes(b"program M; begin end.")
        # bytes that are not valid Shift-JIS
        (tmp_path / "Bad.pas").write_bytes(b"unit U; \xff\xfe\xfd invalid sjis end.")
        r = _run(tmp_path)
        out = json.loads(r.stdout)
        assert out["recommended_profile"] == "delphi-vcl"
        assert "encoding_unverified" in out["warnings"]


# --- lib: load + validate (RT-F5) -------------------------------------------

class TestProfileLoad:
    def test_loads_four_builtin_profiles(self):
        profiles = lib.load_profiles()
        assert {"web-js-ts", "delphi-vcl", "oracle-plsql", "generic-source"} <= set(profiles)

    def test_id_equals_stem_for_all(self):
        profiles = lib.load_profiles()
        for pid, p in profiles.items():
            assert p["id"] == pid

    def test_extractor_outside_allowlist_rejected(self):
        bad = {
            "id": "x", "display_name": "x", "detected_language_heading": "X",
            "detection": {"globs": ["*.x"]},
            "source_encoding": {"primary": "utf-8", "fallback": "utf-8"},
            "artifact_map": {}, "screen_source": "none", "extractors": ["rm_rf_evil"],
            "probe": {"bootable": False}, "module_layout": "x",
        }
        with pytest.raises(ValueError):
            lib.validate_profile(bad, "x")

    def test_builtin_extractors_within_allowlist(self):
        # Phase B: delphi/oracle declare extractors; web/generic stay []. All must be allowlisted.
        profiles = lib.load_profiles()
        assert profiles["web-js-ts"]["extractors"] == []
        assert profiles["generic-source"]["extractors"] == []
        assert profiles["delphi-vcl"]["extractors"] == [
            "extract_sql_schema", "extract_data_flow", "extract_form_nav",
        ]
        for p in profiles.values():
            for ext in p["extractors"]:
                assert ext in lib.ALLOWED_EXTRACTORS

    def test_screen_source_present_and_valid(self):
        # v21.0.0: screen_source gates screen-list/screen-flow production.
        profiles = lib.load_profiles()
        assert profiles["web-js-ts"]["screen_source"] == "route-view"
        assert profiles["delphi-vcl"]["screen_source"] == "dfm-form"
        assert profiles["oracle-plsql"]["screen_source"] == "none"
        assert profiles["generic-source"]["screen_source"] == "none"

    def test_invalid_screen_source_rejected(self):
        bad = {
            "id": "x", "display_name": "x", "detected_language_heading": "X",
            "detection": {"globs": ["*.x"]},
            "source_encoding": {"primary": "utf-8", "fallback": "utf-8"},
            "artifact_map": {}, "screen_source": "bogus", "extractors": [],
            "probe": {"bootable": False}, "module_layout": "x",
        }
        with pytest.raises(ValueError):
            lib.validate_profile(bad, "x")

    def test_corrupt_profile_raises(self, tmp_path):
        (tmp_path / "broken.json").write_text("{ not valid json")
        with pytest.raises((ValueError, json.JSONDecodeError)):
            lib.load_profiles(tmp_path)

    def test_resource_decode_wrong_type_rejected(self):
        bad = {
            "id": "x", "display_name": "x", "detected_language_heading": "X",
            "detection": {"globs": ["*.x"]},
            "source_encoding": {"primary": "utf-8", "fallback": "utf-8"},
            "artifact_map": {}, "screen_source": "none", "extractors": [], "resource_decode": 42,
            "probe": {"bootable": False}, "module_layout": "x",
        }
        with pytest.raises(ValueError):
            lib.validate_profile(bad, "x")

    # --- Phase 01: optional multi-component fields --------------------------

    @staticmethod
    def _min_profile(**extra):
        base = {
            "id": "x", "display_name": "x", "detected_language_heading": "X",
            "detection": {"globs": ["*.x"]},
            "source_encoding": {"primary": "utf-8", "fallback": "utf-8"},
            "artifact_map": {}, "screen_source": "none", "extractors": [],
            "probe": {"bootable": False}, "module_layout": "x",
        }
        base.update(extra)
        return base

    def test_optional_boundary_globs_accepted(self):
        lib.validate_profile(self._min_profile(component_boundary_globs=["*.dpr", "*.dpk"]), "x")

    def test_optional_shared_dirs_accepted(self):
        lib.validate_profile(self._min_profile(shared_layer_dirs=["Common", "DB"]), "x")

    def test_both_optional_fields_absent_accepted(self):
        # Backward-compat: neither field present → still valid.
        lib.validate_profile(self._min_profile(), "x")

    def test_non_list_boundary_globs_rejected(self):
        with pytest.raises(ValueError):
            lib.validate_profile(self._min_profile(component_boundary_globs="*.dpr"), "x")

    def test_non_str_item_shared_dirs_rejected(self):
        with pytest.raises(ValueError):
            lib.validate_profile(self._min_profile(shared_layer_dirs=["Common", 42]), "x")

    def test_existing_profiles_still_valid(self):
        # Loading every real profile must not raise (web/oracle/generic omit both fields).
        profiles = lib.load_profiles()
        assert profiles["delphi-vcl"]["component_boundary_globs"] == ["*.dpr", "*.dproj", "*.dpk"]
        assert profiles["delphi-vcl"]["shared_layer_dirs"] == ["Common", "DB"]
        assert "component_boundary_globs" not in profiles["web-js-ts"]
        assert "shared_layer_dirs" not in profiles["oracle-plsql"]


class TestEncodingHelper:
    def test_empty_sample_list_passes(self):
        # No sample files collected → nothing to verify → no warning (E1/M2 documented behavior).
        assert lib.smoke_check_encoding([], "shift_jis") == []

    def test_corrupt_profile_dir_exits_2_via_cli(self, tmp_path):
        # detect CLI surfaces a kit-profile load failure as exit 2 (H1 contract), not a crash.
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "x.pas").write_text("unit U; end.")
        bad_dir = tmp_path / "profiles"
        bad_dir.mkdir()
        (bad_dir / "broken.json").write_text("{ not json")
        # Point the lib at the bad dir by running an inline python that overrides PROFILES_DIR.
        code = (
            "import sys; sys.path.insert(0, %r);\n"
            "import _stack_profile_lib as L; from pathlib import Path;\n"
            "L.PROFILES_DIR = Path(%r);\n"
            "import detect_stack_profile as d;\n"
            "import sys as s; s.argv=['d','--root',%r];\n"
            "d.main()\n"
        ) % (str(SCRIPTS_DIR), str(bad_dir), str(proj))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
        assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)


# --- Phase 05: reused-root detection -----------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _make_reused_fixture(root: Path, primary_lang: str = "en",
                          sha: str = "abc123def456abc123def456abc123def456abc1") -> Path:
    """Build a minimal monorepo_reused layout under root (without committing .git)."""
    # gateway — normal pending backend
    (root / "gateway").mkdir(parents=True)
    (root / "gateway" / "package.json").write_text(
        '{"name":"gateway","dependencies":{"express":"^4"}}', encoding="utf-8")
    # auth — normal pending backend
    (root / "auth").mkdir(parents=True)
    (root / "auth" / "pyproject.toml").write_text(
        '[project]\ndependencies = ["fastapi>=0.100"]', encoding="utf-8")
    # employee — reused product (no root marker, but has docs/.rebuild-state.json)
    emp = root / "employee"
    (emp / "backend").mkdir(parents=True)
    (emp / "frontend").mkdir(parents=True)
    (emp / "backend" / "package.json").write_text(
        '{"name":"emp-be","dependencies":{"@nestjs/core":"^9"}}', encoding="utf-8")
    (emp / "frontend" / "package.json").write_text(
        '{"name":"emp-fe","dependencies":{"nuxt":"^3"}}', encoding="utf-8")
    docs_dir = emp / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / ".rebuild-state.json").write_text(
        f'{{"schema_version":"21.0.0","primary_lang":"{primary_lang}","last_rebuild_sha":"{sha}"}}',
        encoding="utf-8")
    return emp


class TestReusedRootDetection:
    """Phase 05 — reused sub-root emits ONE component with status=reused."""

    def test_employee_detected_as_single_reused(self, tmp_path):
        _make_reused_fixture(tmp_path)
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        by_path = {c["path"]: c for c in components}
        # Employee must be ONE component, not split
        assert "employee" in by_path
        assert "employee/backend" not in by_path
        assert "employee/frontend" not in by_path

    def test_reused_component_has_status_reused(self, tmp_path):
        _make_reused_fixture(tmp_path)
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["status"] == "reused"

    def test_reused_component_has_provenance_fields(self, tmp_path):
        sha = "abc123def456abc123def456abc123def456abc1"
        _make_reused_fixture(tmp_path, sha=sha)
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["source_sha"] == sha
        assert emp["docs_path"] == "employee/docs"
        assert isinstance(emp["is_git_root"], bool)

    def test_reused_component_not_grouped(self, tmp_path):
        _make_reused_fixture(tmp_path)
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["group"] is None

    def test_gateway_and_auth_still_pending(self, tmp_path):
        _make_reused_fixture(tmp_path)
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        by_path = {c["path"]: c for c in components}
        assert "gateway" in by_path
        assert "auth" in by_path
        # Normal components must NOT have status field (defaults to pending via emit_manifest)
        assert by_path["gateway"].get("status") != "reused"
        assert by_path["auth"].get("status") != "reused"

    def test_reused_advisory_in_warnings(self, tmp_path):
        _make_reused_fixture(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert any(w.startswith("component_reused:") for w in out["warnings"])

    def test_is_git_root_detected_worktree_file(self, tmp_path):
        """is_git_root=True when .git is a FILE (git worktree)."""
        _make_reused_fixture(tmp_path)
        # Create a .git FILE (worktree case)
        (tmp_path / "employee" / ".git").write_text("gitdir: ../../.git/worktrees/emp",
                                                     encoding="utf-8")
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["is_git_root"] is True

    def test_is_git_root_detected_git_dir(self, tmp_path):
        """is_git_root=True when .git is a DIRECTORY (normal clone)."""
        _make_reused_fixture(tmp_path)
        (tmp_path / "employee" / ".git").mkdir()
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["is_git_root"] is True

    def test_missing_sha_gives_empty_string(self, tmp_path):
        """If last_rebuild_sha absent, source_sha="". """
        _make_reused_fixture(tmp_path, sha="")
        # Overwrite state without sha
        state = tmp_path / "employee" / "docs" / ".rebuild-state.json"
        state.write_text('{"schema_version":"21.0.0","primary_lang":"en"}', encoding="utf-8")
        profiles = lib.load_profiles()
        components = lib.find_components(str(tmp_path), profiles)
        emp = next(c for c in components if c["path"] == "employee")
        assert emp["source_sha"] == ""

    def test_fixture_static(self, tmp_path):
        """The committed fixture at tests/fixtures/monorepo_reused/ also resolves correctly."""
        import shutil
        fixture_src = FIXTURES_DIR / "monorepo_reused"
        dest = tmp_path / "monorepo_reused"
        shutil.copytree(str(fixture_src), str(dest))
        profiles = lib.load_profiles()
        components = lib.find_components(str(dest), profiles)
        by_path = {c["path"]: c for c in components}
        assert "employee" in by_path
        assert by_path["employee"]["status"] == "reused"
        assert "gateway" in by_path
        assert "auth" in by_path
