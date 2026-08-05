"""Tests for incremental_planner.py — cascade engine, fallback table, planner logic."""
from __future__ import annotations  # PEP 604 `X | None` at runtime on Python 3.9

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from incremental_planner import (
    ARTIFACT_LAYERED,
    CORE_ARTIFACT_TO_WAVE_SUBJECT,
    WAVE_ORDER,
    _build_payload,
    _cascade,
    _classify_files,
    _compute_doc_shas_snapshot,
    _detect_confidence_report_missing,
    _detect_oob,
    _diff_screen_shas,
    _hash_screen_sections,
    _parse_scout_inventory,
    _parse_screen_sections,
    _resolve_fcodes,
    _resolve_screen_dirname,
)

FIXTURES_DIR = _TESTS_DIR / "fixtures"
INCREMENTAL_FIXTURES = FIXTURES_DIR / "incremental"
PLANNER_SCRIPT = _SCRIPTS_DIR / "incremental_planner.py"
PYTHON = sys.executable


def _init_git_repo(d: Path, initial_sha: str | None = None) -> str:
    """Create a git repo with one commit; return HEAD SHA."""
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"], capture_output=True, check=True)
    (d / "init.txt").write_text("init")
    subprocess.run(["git", "-C", str(d), "add", "."], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-m", "init"], capture_output=True, check=True)
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _seed_planner_env(tmp: Path) -> dict:
    """Create the full planner input environment at v4 layered paths. Returns paths dict."""
    plan_dir = tmp / "plans" / "test-plan"
    artifacts = plan_dir / "artifacts"
    docs_root = tmp / "docs"
    docs_generated = docs_root / "generated"
    docs_features = docs_root / "features" / "F001_Auth"

    artifacts.mkdir(parents=True)
    docs_generated.mkdir(parents=True)
    docs_features.mkdir(parents=True)

    # Scout report
    shutil.copy(INCREMENTAL_FIXTURES / "synthetic-scout-report.md", artifacts / "scout-report.md")
    # Canonical fcodes
    canonical = {
        "generated_at": "2026-05-19T08:00:00Z",
        "plan": "test-plan",
        "features": [
            {"fcode": "F001", "slug": "F001_Auth", "name": "Auth", "priority": "P0", "type": "ui", "related": {}},
            {"fcode": "F005", "slug": "F005_Pay", "name": "Pay", "priority": "P1", "type": "ui", "related": {}},
        ],
    }
    (artifacts / "_canonical-fcodes.json").write_text(json.dumps(canonical))
    # Also in docs_root for prereq check
    (docs_root / "_canonical-fcodes.json").write_text(json.dumps(canonical))
    # Reverse index at docs_root (no longer in docs/specs)
    shutil.copy(INCREMENTAL_FIXTURES / "synthetic-reverse-index.json", docs_root / "_source-to-fcode.json")
    # Core artifact stubs at layered paths
    (docs_generated / "route-list.md").write_text("# route-list.md\nstub content\n")
    (docs_generated / "entities.md").write_text("# data-model\nstub content\n")
    (docs_generated / "behavior-logic.md").write_text("# behavior-logic.md\nstub content\n")
    # Feature spec
    (docs_features / "spec.md").write_text("# F001 Auth spec\n")

    return {
        "plan_dir": str(plan_dir),
        "docs_root": str(docs_root),
        "scout_report": str(artifacts / "scout-report.md"),
        "out": str(artifacts / ".incremental-plan.json"),
    }


class TestParseScoutInventory:
    def test_parses_fixture(self):
        inv = _parse_scout_inventory(INCREMENTAL_FIXTURES / "synthetic-scout-report.md")
        assert inv["api/app/Http/Controllers/AuthController.php"] == "route"
        assert inv["api/app/Models/User.php"] == "model"
        assert inv["web/src/pages/Login.vue"] == "screen"
        assert inv["api/app/Jobs/SendEmail.php"] == "background"
        assert inv["api/app/Policies/SurveyPolicy.php"] == "permission"
        assert inv["api/config/app.php"] == "config"
        assert inv["api/app/Helpers/StringHelper.php"] == "other"

    def test_missing_file_returns_empty(self, tmp_path):
        assert _parse_scout_inventory(tmp_path / "nope.md") == {}


class TestClassifyFiles:
    def test_classifies_by_inventory(self):
        inv = {"src/route.php": "route", "src/model.py": "model"}
        diff = [("M", "src/route.php", None), ("M", "src/model.py", None)]
        classified, unowned = _classify_files(diff, inv)
        assert "route" in classified
        assert "model" in classified
        assert unowned == []

    def test_new_file_not_in_inventory(self):
        diff = [("A", "src/new.py", None)]
        classified, unowned = _classify_files(diff, {})
        assert "src/new.py" in unowned

    def test_rename_uses_new_path(self):
        inv = {"new/file.ts": "screen"}
        diff = [("R", "old/file.ts", "new/file.ts")]
        classified, unowned = _classify_files(diff, inv)
        assert "screen" in classified


class TestCascade:
    def test_route_triggers_full_chain(self):
        # [RT-C6] Wave6.8: process-flow and Wave6.9: glossary removed from core cascade (v5.0.0).
        # These are now standalone passes (--flows, --glossary). Route chain now has 7 waves.
        # Previous: 9 waves (included Wave6.8 + Wave6.9).
        # New: 7 waves (Wave1:route-list through Wave5:feature-list + Wave2.9:api-map).
        waves, chain = _cascade({"route"})
        assert "Wave1: route-list" in waves
        assert "Wave5: feature-list" in waves
        assert "Wave6.8: process-flow" not in waves
        assert "Wave6.9: glossary" not in waves
        assert len(waves) == 7  # Wave1:route-list, Wave2:screen+flow, Wave2:behavior, Wave2.9:api-map, Wave3:perms, Wave4:stories, Wave5:feature-list

    def test_model_triggers_full_chain(self):
        waves, _ = _cascade({"model"})
        assert "Wave1: data-model" in waves
        assert "Wave5: feature-list" in waves

    def test_screen_triggers_from_w2(self):
        waves, _ = _cascade({"screen"})
        assert "Wave2: screen-list + screen-flow" in waves
        assert "Wave1: route-list" not in waves

    def test_background_triggers_from_w2bg(self):
        waves, _ = _cascade({"background"})
        assert "Wave2: behavior-logic" in waves
        assert "Wave2: screen-list + screen-flow" not in waves

    def test_permission_triggers_from_w3(self):
        waves, _ = _cascade({"permission"})
        assert "Wave3: permissions" in waves
        assert "Wave2: behavior-logic" not in waves

    def test_config_returns_full_sentinel(self):
        waves, chain = _cascade({"config"})
        assert waves == []
        assert "FULL" in chain

    def test_other_only_returns_empty(self):
        waves, chain = _cascade({"other"})
        assert waves == []
        assert chain is None

    def test_mixed_types_union(self):
        waves, _ = _cascade({"route", "permission"})
        assert "Wave1: route-list" in waves
        assert "Wave3: permissions" in waves

    def test_order_matches_wave_order(self):
        waves, _ = _cascade({"route", "screen"})
        indices = [WAVE_ORDER.index(w) for w in waves]
        assert indices == sorted(indices)


class TestResolveFcodes:
    def test_w5_reran_returns_all_canonical(self, tmp_path):
        canonical = {
            "features": [
                {"fcode": "F001", "slug": "F001_Auth"},
                {"fcode": "F005", "slug": "F005_Pay"},
            ]
        }
        cp = tmp_path / "_canonical-fcodes.json"
        cp.write_text(json.dumps(canonical))
        result = _resolve_fcodes({}, [], True, cp)
        assert result == ["F001", "F005"]

    def test_w5_not_reran_uses_reverse_index(self, tmp_path):
        ri = {"index": {"src/auth.php": ["F001"], "src/pay.php": ["F005"]}}
        result = _resolve_fcodes(ri, ["src/auth.php"], False, tmp_path / "nope.json")
        assert result == ["F001"]

    def test_empty_paths_returns_empty(self, tmp_path):
        ri = {"index": {"src/auth.php": ["F001"]}}
        result = _resolve_fcodes(ri, [], False, tmp_path / "nope.json")
        assert result == []


class TestDetectOob:
    def test_mismatch_emits_warning(self, tmp_path):
        # route-list.md lives at generated/route-list.md in v4 layered layout
        (tmp_path / "generated").mkdir()
        (tmp_path / "generated" / "route-list.md").write_text("changed content")
        state = {"doc_shas": {"route-list.md": "0000000000000000000000000000000000000000000000000000000000000000"}}
        warnings = _detect_oob(state, tmp_path, [])
        assert any("route-list.md" in w for w in warnings)

    def test_affected_artifact_skipped(self, tmp_path):
        (tmp_path / "generated").mkdir()
        (tmp_path / "generated" / "route-list.md").write_text("changed")
        state = {"doc_shas": {"route-list.md": "0000"}}
        warnings = _detect_oob(state, tmp_path, ["Wave1: route-list"])
        assert len(warnings) == 0

    def test_no_doc_shas_returns_empty(self, tmp_path):
        assert _detect_oob({}, tmp_path, []) == []


class TestDetectConfidenceReportMissing:
    """[v25.2.0 rework] A1 advisory scan — companion-absent detection, unit level."""

    def test_core_artifact_without_companion_emits_warning(self, tmp_path):
        (tmp_path / "generated").mkdir()
        (tmp_path / "generated" / "route-list.md").write_text("content")
        warnings = _detect_confidence_report_missing(tmp_path)
        assert any("[CONFIDENCE_REPORT_MISSING]" in w and "route-list.md" in w for w in warnings)

    def test_core_artifact_with_companion_no_warning(self, tmp_path):
        (tmp_path / "generated").mkdir()
        (tmp_path / "generated" / "route-list.md").write_text("content")
        (tmp_path / "generated" / "confidence-report_route-list.md").write_text("stub")
        assert _detect_confidence_report_missing(tmp_path) == []

    def test_feature_technical_spec_missing_companion(self, tmp_path):
        fdir = tmp_path / "features" / "F001_Auth"
        fdir.mkdir(parents=True)
        (fdir / "technical-spec.md").write_text("content")
        warnings = _detect_confidence_report_missing(tmp_path)
        assert any("F001_Auth/technical-spec.md" in w for w in warnings)

    def test_screen_spec_missing_companion(self, tmp_path):
        sdir = tmp_path / "screens" / "SCR001_Login"
        sdir.mkdir(parents=True)
        (sdir / "spec.md").write_text("content")
        warnings = _detect_confidence_report_missing(tmp_path)
        assert any("SCR001_Login/spec.md" in w for w in warnings)

    def test_absent_primary_artifact_never_warns(self, tmp_path):
        # A profile-conditional artifact (e.g. route-list.md on a non-web stack) that was
        # never produced must never be treated as "missing its companion".
        (tmp_path / "generated").mkdir()
        assert _detect_confidence_report_missing(tmp_path) == []

    def test_no_artifacts_returns_empty(self, tmp_path):
        assert _detect_confidence_report_missing(tmp_path) == []


class TestConfidenceReportAdvisoryNonGating:
    """[v25.2.0 rework — reviewer finding 1] Proves the advisory is print-only: unlike
    _detect_oob (which forces mode=full on a mismatch), a missing confidence-report
    companion must NEVER change planning mode, payload, or exit code."""

    @staticmethod
    def _happy_path_env(tmp_path):
        env = _seed_planner_env(tmp_path)
        sha1 = _init_git_repo(tmp_path)
        docs_root = Path(env["docs_root"])
        # A docs/-prefixed new file is exempt from the unowned_new_source fallback (condition 8)
        # and carries no scout-inventory type, so cascade stays empty — the plain "incremental,
        # no waves affected" happy path that reaches the confidence-report advisory + OOB block.
        (docs_root / "note.md").write_text("note")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "docs note"], capture_output=True, check=True)
        state = {"last_rebuild_sha": sha1, "doc_shas": _compute_doc_shas_snapshot(docs_root)}
        (docs_root / ".rebuild-state.json").write_text(json.dumps(state))
        return env

    @staticmethod
    def _run(env, tmp_path):
        return subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )

    def test_warning_present_but_mode_and_exit_code_unaffected(self, tmp_path):
        env = self._happy_path_env(tmp_path)
        r = self._run(env, tmp_path)
        assert r.returncode == 0
        assert "[CONFIDENCE_REPORT_MISSING]" in r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "incremental"
        assert payload["fallback_to_full"] is False

    def test_no_warning_when_companions_present(self, tmp_path):
        env = self._happy_path_env(tmp_path)
        docs_root = Path(env["docs_root"])
        for rel in ARTIFACT_LAYERED.values():
            fpath = docs_root / rel
            if fpath.is_file():
                (fpath.parent / f"confidence-report_{fpath.stem}.md").write_text("stub")
        r = self._run(env, tmp_path)
        assert r.returncode == 0
        assert "[CONFIDENCE_REPORT_MISSING]" not in r.stderr
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "incremental"


class TestFallbackConditions:
    """E2E tests via subprocess — one per fallback condition."""

    def test_cond1_scout_missing(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        os.remove(env["scout_report"])
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--scout-report", str(tmp_path / "nope.md"),
             "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 1

    def test_cond2_canonical_missing(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        os.remove(str(Path(env["docs_root"]) / "_canonical-fcodes.json"))
        os.remove(str(Path(env["plan_dir"]) / "artifacts" / "_canonical-fcodes.json"))
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 1

    def test_cond3_reverse_index_missing(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        os.remove(str(Path(env["docs_root"]) / "_source-to-fcode.json"))
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 1

    def test_cond4_state_missing_fallback_full(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        sha = _init_git_repo(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert payload["fallback_reason"] == "state_missing"

    def test_cond5_sha_unreachable(self, tmp_path):
        """Cond5 — state references a SHA that doesn't exist in git history → mode=full, fallback=sha_unreachable."""
        env = _seed_planner_env(tmp_path)
        _init_git_repo(tmp_path)
        bad_sha = "0000000000000000000000000000000000000000"
        state = {"last_rebuild_sha": bad_sha, "mode": "full", "rebuilt_at": "2026-05-20T08:00:00Z"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert payload["fallback_reason"] == "sha_unreachable"

    def test_cond6_threshold_exceeded(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        sha = _init_git_repo(tmp_path)
        state = {"last_rebuild_sha": sha, "mode": "full", "rebuilt_at": "2026-05-19T08:00:00Z", "fcode_index_sha": "x"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))
        for i in range(20):
            (tmp_path / f"file{i}.txt").write_text(f"content{i}")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "bulk"], capture_output=True, check=True)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"],
             "--threshold", "0.01"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert "threshold" in payload["fallback_reason"]

    def test_cond7_manifest_changed(self, tmp_path):
        """Cond7 — diff includes a manifest file (package.json) → mode=full, fallback=manifest_changed."""
        env = _seed_planner_env(tmp_path)
        sha = _init_git_repo(tmp_path)
        state = {"last_rebuild_sha": sha, "mode": "full", "rebuilt_at": "2026-05-20T08:00:00Z"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))
        (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "add manifest"], capture_output=True, check=True)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert payload["fallback_reason"] == "manifest_changed"

    def test_cond8_unowned_new_source(self, tmp_path):
        """Cond8 — diff includes a new file (status A) not in scout-report inventory → mode=full, fallback=unowned_new_source."""
        env = _seed_planner_env(tmp_path)
        sha = _init_git_repo(tmp_path)
        state = {"last_rebuild_sha": sha, "mode": "full", "rebuilt_at": "2026-05-20T08:00:00Z"}
        (Path(env["docs_root"]) / ".rebuild-state.json").write_text(json.dumps(state))
        new_src = tmp_path / "api" / "app" / "Http" / "Controllers" / "NewController.php"
        new_src.parent.mkdir(parents=True, exist_ok=True)
        new_src.write_text("<?php class NewController {}")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "add new controller"], capture_output=True, check=True)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"]],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert "unowned_new_source" in payload["fallback_reason"]

    def test_cond9_full_flag(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        _init_git_repo(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"], "--full"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "full"
        assert "explicit" in payload["fallback_reason"]


class TestMutuallyExclusiveFlags:
    def test_full_and_since_exit_2(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--full", "--since", "abc123"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 2


class TestFeaturesPassthrough:
    def test_features_flag_minimal_payload(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        _init_git_repo(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"],
             "--features", "F001,F005"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        payload = json.loads(Path(env["out"]).read_text())
        assert payload["mode"] == "incremental"
        assert payload["affected_waves"] == []
        assert payload["affected_fcodes"] == ["F001", "F005"]
        assert payload["w5_reran"] is False


class TestDryRun:
    def test_dry_run_no_file_write(self, tmp_path):
        env = _seed_planner_env(tmp_path)
        _init_git_repo(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-root", env["docs_root"], "--out", env["out"],
             "--features", "F001", "--dry-run"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0
        assert not Path(env["out"]).exists()
        stdout_lines = r.stdout.strip().split("\n")
        json_end = next(i for i, l in enumerate(stdout_lines) if l.startswith("[INFO]"))
        parsed = json.loads("\n".join(stdout_lines[:json_end]))
        assert parsed["mode"] == "incremental"


class TestBackwardCompatDocsSpecs:
    def test_docs_specs_alias_accepted(self, tmp_path):
        """--docs-specs is accepted as alias for --docs-root for backward compat."""
        env = _seed_planner_env(tmp_path)
        _init_git_repo(tmp_path)
        r = subprocess.run(
            [PYTHON, str(PLANNER_SCRIPT), "--plan-dir", env["plan_dir"],
             "--docs-specs", env["docs_root"], "--out", env["out"],
             "--features", "F001"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert r.returncode == 0


class TestBuildPayload:
    def test_payload_has_all_fields(self):
        p = _build_payload(
            mode="incremental", affected_waves=["Wave1: route-list"],
            affected_fcodes=["F001"], w5_reran=True, cascade_chain="route → W1",
            fallback_reason=None, fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
        )
        assert set(p.keys()) == {
            "mode", "affected_waves", "affected_fcodes", "w5_reran",
            "cascade_chain", "fallback_reason", "fallback_to_full",
            "deleted_files", "doc_shas_snapshot", "generated_at",
            "since_sha", "head_sha",
        }

    def test_affected_screens_emitted_in_incremental(self):
        p = _build_payload(
            mode="incremental", affected_waves=[], affected_fcodes=[],
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
            affected_screens=["SCR001", "SCR003"],
        )
        assert p["affected_screens"] == ["SCR001", "SCR003"]

    def test_affected_screens_omitted_in_full(self):
        p = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER), affected_fcodes=[],
            w5_reran=True, cascade_chain=None, fallback_reason="explicit --full flag",
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="", head_sha="def",
            affected_screens=["SCR001"],
        )
        assert "affected_screens" not in p

    def test_screen_spec_shas_snapshot_included_when_nonempty(self):
        shas = {"SCR001": "abc123", "SCR002": "def456"}
        p = _build_payload(
            mode="incremental", affected_waves=[], affected_fcodes=[],
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
            screen_spec_shas_snapshot=shas,
        )
        assert p["screen_spec_shas_snapshot"] == shas

    def test_screen_spec_shas_snapshot_included_when_empty_dict(self):
        p = _build_payload(
            mode="incremental", affected_waves=[], affected_fcodes=[],
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
            screen_spec_shas_snapshot={},
        )
        assert "screen_spec_shas_snapshot" in p
        assert p["screen_spec_shas_snapshot"] == {}

    def test_screen_spec_shas_snapshot_omitted_when_none(self):
        p = _build_payload(
            mode="incremental", affected_waves=[], affected_fcodes=[],
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
            screen_spec_shas_snapshot=None,
        )
        assert "screen_spec_shas_snapshot" not in p

    def test_affected_holistic_docs_emitted_in_incremental(self):
        p = _build_payload(
            mode="incremental", affected_waves=["Wave1: route-list"], affected_fcodes=[],
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="abc", head_sha="def",
            affected_holistic_docs=["system-overview.md", "business-rules.md"],
            affected_flows=["flow-auth.md"],
        )
        assert p["affected_holistic_docs"] == ["system-overview.md", "business-rules.md"]
        assert p["affected_flows"] == ["flow-auth.md"]

    def test_affected_holistic_docs_omitted_in_full(self):
        p = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER), affected_fcodes=[],
            w5_reran=True, cascade_chain=None, fallback_reason="explicit --full flag",
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot={}, since_sha="", head_sha="def",
            affected_holistic_docs=["system-overview.md"],
        )
        assert "affected_holistic_docs" not in p


class TestParseScreenSections:
    _SAMPLE = """\
# Screen List

## SCR001_Login
Login screen body line 1.
Login screen body line 2.

## SCR002_Dashboard
Dashboard body.

## SCR003
No slug screen.
"""

    def test_parses_slug_and_body(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(self._SAMPLE)
        parsed = _parse_screen_sections(f)
        assert set(parsed.keys()) == {"SCR001", "SCR002", "SCR003"}
        assert parsed["SCR001"][0] == "Login"
        assert "Login screen body line 1" in parsed["SCR001"][1]
        assert parsed["SCR002"][0] == "Dashboard"
        assert "Dashboard body" in parsed["SCR002"][1]

    def test_no_slug_returns_empty_string(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text(self._SAMPLE)
        parsed = _parse_screen_sections(f)
        assert parsed["SCR003"][0] == ""

    def test_absent_file_returns_empty(self, tmp_path):
        result = _parse_screen_sections(tmp_path / "missing.md")
        assert result == {}

    def test_body_excludes_heading_line(self, tmp_path):
        f = tmp_path / "screen-list.md"
        f.write_text("## SCR001_Login\nbody text\n")
        parsed = _parse_screen_sections(f)
        assert "SCR001_Login" not in parsed["SCR001"][1]
        assert "body text" in parsed["SCR001"][1]


class TestHashScreenSections:
    def test_produces_hex_sha(self):
        import hashlib
        parsed = {"SCR001": ("Login", "some body")}
        result = _hash_screen_sections(parsed)
        expected = hashlib.sha256("some body".encode()).hexdigest()
        assert result == {"SCR001": expected}

    def test_empty_parsed_returns_empty(self):
        assert _hash_screen_sections({}) == {}

    def test_body_change_changes_sha(self):
        p1 = {"SCR001": ("Login", "body v1")}
        p2 = {"SCR001": ("Login", "body v2")}
        assert _hash_screen_sections(p1)["SCR001"] != _hash_screen_sections(p2)["SCR001"]


class TestResolveScreenDirname:
    def test_with_slug(self):
        parsed = {"SCR001": ("Login", "body")}
        assert _resolve_screen_dirname(parsed, "SCR001") == "SCR001_Login"

    def test_without_slug(self):
        parsed = {"SCR002": ("", "body")}
        assert _resolve_screen_dirname(parsed, "SCR002") == "SCR002"

    def test_missing_code_returns_bare_code(self):
        assert _resolve_screen_dirname({}, "SCR099") == "SCR099"


class TestDiffScreenShas:
    def test_new_code_is_affected(self, tmp_path):
        prior: dict[str, str] = {}
        current = {"SCR001": "abc123"}
        parsed = {"SCR001": ("Login", "body")}
        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert result == ["SCR001"]

    def test_changed_sha_is_affected(self, tmp_path):
        prior = {"SCR001": "old_sha"}
        current = {"SCR001": "new_sha"}
        parsed = {"SCR001": ("Login", "body")}
        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert result == ["SCR001"]

    def test_unchanged_sha_but_missing_spec_is_affected(self, tmp_path):
        sha = "abc123"
        prior = {"SCR001": sha}
        current = {"SCR001": sha}
        parsed = {"SCR001": ("Login", "body")}
        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert result == ["SCR001"]

    def test_unchanged_sha_with_spec_present_not_affected(self, tmp_path):
        sha = "abc123"
        prior = {"SCR001": sha}
        current = {"SCR001": sha}
        parsed = {"SCR001": ("Login", "body")}
        spec = tmp_path / "screens" / "SCR001_Login" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# spec")
        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert result == []

    def test_returns_sorted(self, tmp_path):
        prior: dict[str, str] = {}
        current = {"SCR003": "c", "SCR001": "a", "SCR002": "b"}
        parsed = {k: ("", "") for k in current}
        result = _diff_screen_shas(prior, current, tmp_path / "screens", parsed)
        assert result == ["SCR001", "SCR002", "SCR003"]
