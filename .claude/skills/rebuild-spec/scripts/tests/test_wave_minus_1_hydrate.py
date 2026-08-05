"""Tests for incremental_planner.py --hydrate mode (Wave -1)."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from incremental_planner import ARTIFACT_LAYERED, CORE_ARTIFACT_TO_WAVE_SUBJECT, _hydrate

CORE_ARTIFACTS = [
    "route-list.md", "data-model.md", "screen-list.md", "screen-flow.md",
    "behavior-logic.md", "api-map.md", "permissions.md", "permissions-matrix.md",
    "user-stories.md", "feature-list.md", "glossary.md",
]


def _layered_src(docs_root: Path, artifact_name: str) -> Path:
    """Return canonical layered path for artifact_name under docs_root."""
    return docs_root / ARTIFACT_LAYERED[artifact_name]


def _seed_hydrate_env(tmp: Path, affected_waves: list[str], affected_fcodes: list[str]) -> tuple[Path, Path]:
    """Create plan + docs dirs at v4 layered paths, write .incremental-plan.json.

    Returns (plan_dir, docs_root).
    """
    plan_dir = tmp / "plans" / "test"
    artifacts = plan_dir / "artifacts"
    docs_root = tmp / "docs"

    artifacts.mkdir(parents=True)

    # Core artifacts at layered paths
    for name in CORE_ARTIFACTS:
        fpath = _layered_src(docs_root, name)
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(f"# {name}\ncanonical content\n")
    # system-overview at layered path
    sov_path = _layered_src(docs_root, "system-overview.md")
    sov_path.parent.mkdir(parents=True, exist_ok=True)
    sov_path.write_text("# System Overview\nstub\n")
    # architecture at layered path (always-copy holistic doc, like system-overview)
    arch_path = _layered_src(docs_root, "architecture.md")
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text("# Architecture\nstub\n")

    # Canonical fcodes at docs_root (not docs/specs)
    canonical = {
        "generated_at": "2026-05-19T08:00:00Z",
        "features": [
            {"fcode": "F001", "slug": "F001_Auth"},
            {"fcode": "F005", "slug": "F005_Pay"},
        ],
    }
    (docs_root / "_canonical-fcodes.json").write_text(json.dumps(canonical))

    # Feature specs at docs_root/features/
    for slug in ["F001_Auth", "F005_Pay"]:
        d = docs_root / "features" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.md").write_text(f"# {slug} spec\n")

    # .incremental-plan.json
    plan_data = {
        "mode": "incremental",
        "affected_waves": affected_waves,
        "affected_fcodes": affected_fcodes,
        "w5_reran": "Wave5: feature-list" in affected_waves,
        "doc_shas_snapshot": {},
    }
    (artifacts / ".incremental-plan.json").write_text(json.dumps(plan_data))

    return plan_dir, docs_root


class TestHydrateSkipsAffectedWaves:
    def test_skips_route_list_when_affected(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(
            tmp_path, ["Wave1: route-list"], [])
        _hydrate(plan_dir, docs_root)
        artifacts = plan_dir / "artifacts"
        # route-list should NOT be copied (wave will regenerate it)
        assert not (artifacts / "route-list.md").exists()
        # data-model should BE copied (not in affected_waves)
        assert (artifacts / "data-model.md").exists()
        assert (artifacts / "data-model.md").read_text() == _layered_src(docs_root, "data-model.md").read_text()


class TestHydrateCopiesNonAffected:
    def test_copies_all_when_no_affected(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        _hydrate(plan_dir, docs_root)
        artifacts = plan_dir / "artifacts"
        for name in CORE_ARTIFACTS:
            assert (artifacts / name).exists(), f"{name} should be hydrated"
            assert (artifacts / name).read_text() == _layered_src(docs_root, name).read_text()

    def test_system_overview_always_copied(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(
            tmp_path, list(CORE_ARTIFACT_TO_WAVE_SUBJECT.values()), [])
        _hydrate(plan_dir, docs_root)
        assert (plan_dir / "artifacts" / "system-overview.md").exists()


class TestHydrateIdempotent:
    def test_rerun_produces_same_bytes(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], ["F001"])
        _hydrate(plan_dir, docs_root)
        first_shas = {}
        for f in (plan_dir / "artifacts").glob("*.md"):
            first_shas[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()

        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        plan_data["mode"] = "incremental"
        (plan_dir / "artifacts" / ".incremental-plan.json").write_text(json.dumps(plan_data))

        _hydrate(plan_dir, docs_root)
        for f in (plan_dir / "artifacts").glob("*.md"):
            assert first_shas.get(f.name) == hashlib.sha256(f.read_bytes()).hexdigest()


class TestDocShasSnapshotUpdated:
    def test_snapshot_written_after_hydrate(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        _hydrate(plan_dir, docs_root)
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        assert "doc_shas_snapshot" in plan_data
        assert len(plan_data["doc_shas_snapshot"]) > 0


class TestFeatureSpecHydrate:
    def test_copies_non_affected_feature_specs(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], ["F001"])
        _hydrate(plan_dir, docs_root)
        features_dst = plan_dir / "artifacts" / "features"
        # F005 not affected → should be copied
        assert (features_dst / "F005_Pay" / "spec.md").exists()
        # F001 affected → should NOT be copied
        assert not (features_dst / "F001_Auth" / "spec.md").exists()


class TestFirstRunGuard:
    def test_missing_source_auto_fallback_full(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(
            tmp_path, ["Wave1: route-list"], [])
        # Remove a source artifact that should be hydrated (data-model not in affected)
        _layered_src(docs_root, "data-model.md").unlink()
        result = _hydrate(plan_dir, docs_root)
        assert result == 0
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        assert plan_data["mode"] == "full"
        assert "baseline missing" in plan_data["fallback_reason"]

    def test_all_sources_present_stays_incremental(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        result = _hydrate(plan_dir, docs_root)
        assert result == 0
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        assert plan_data["mode"] == "incremental"


class TestFullModeNoOp:
    def test_full_mode_skips_hydrate(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        plan_data["mode"] = "full"
        (plan_dir / "artifacts" / ".incremental-plan.json").write_text(json.dumps(plan_data))
        result = _hydrate(plan_dir, docs_root)
        assert result == 0
        md_files = list((plan_dir / "artifacts").glob("*.md"))
        assert len(md_files) == 0


def _seed_screen_dirs(docs_root: Path) -> None:
    """Seed docs_root/screens/ with two SCR### subdirectories containing spec.md."""
    for name in ["SCR001_Login", "SCR002_Dashboard"]:
        d = docs_root / "screens" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.md").write_text(f"# {name} spec\n")


class TestHydrateScreenSpecs:
    def test_copies_non_affected_screen_specs(self, tmp_path):
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        _seed_screen_dirs(docs_root)
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        plan_data["affected_screens"] = ["SCR001"]
        (plan_dir / "artifacts" / ".incremental-plan.json").write_text(json.dumps(plan_data))

        _hydrate(plan_dir, docs_root)

        screens_dst = plan_dir / "artifacts" / "screens"
        # SCR002 not affected → should be copied
        assert (screens_dst / "SCR002_Dashboard" / "spec.md").exists()
        # SCR001 affected → should NOT be copied
        assert not (screens_dst / "SCR001_Login" / "spec.md").exists()

    def test_no_copy_when_affected_screens_absent(self, tmp_path):
        """When affected_screens key is absent (full mode payload), no screen specs are copied."""
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        _seed_screen_dirs(docs_root)
        _hydrate(plan_dir, docs_root)

        screens_dst = plan_dir / "artifacts" / "screens"
        assert not screens_dst.exists() or not list(screens_dst.rglob("spec.md"))

    def test_all_screens_copied_when_affected_screens_empty(self, tmp_path):
        """affected_screens present but empty → all screen specs are hydrated."""
        plan_dir, docs_root = _seed_hydrate_env(tmp_path, [], [])
        _seed_screen_dirs(docs_root)
        plan_data = json.loads((plan_dir / "artifacts" / ".incremental-plan.json").read_text())
        plan_data["affected_screens"] = []
        (plan_dir / "artifacts" / ".incremental-plan.json").write_text(json.dumps(plan_data))

        _hydrate(plan_dir, docs_root)

        screens_dst = plan_dir / "artifacts" / "screens"
        assert (screens_dst / "SCR001_Login" / "spec.md").exists()
        assert (screens_dst / "SCR002_Dashboard" / "spec.md").exists()
