"""Tests for translation_sync_gate.py + _translation_sync_lib.py.

Run via:
  .claude/skills/.venv/bin/python3 -m pytest \
    claude/skills/rebuild-spec/scripts/tests/test_translation_sync_gate.py -v

Coverage targets (phase-01 acceptance criteria):
  - plan mode: stale/up-to-date lang detection, first-translate, pass-missing, deferred
  - finalize: report written, cursor updated, promoted-dir verification downgrade
  - all 5 handoff-line cases byte-for-byte
  - none-registered, report-missing
  - path-traversal rejection via normalize_lang
  - idempotency of finalize
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "translation_sync_gate.py"
# Use the venv interpreter so imports resolve correctly
PYTHON = sys.executable

# Import lib directly for unit-level tests
sys.path.insert(0, str(SCRIPTS_DIR))
from _translation_sync_lib import (  # noqa: E402
    REPORT_MISSING_MSG,
    compute_finalize_result,
    compute_plan_worklist,
    discover_artifacts,
    is_stale,
    lang_docs_path,
    parse_lang_statuses,
    render_handoff,
    secondary_langs,
    summarize_from_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(argv: list[str], env: dict | None = None, project_root: Path | None = None) -> tuple[int, str, str]:
    """Run gate script; return (returncode, stdout, stderr)."""
    import os
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    pr = project_root or Path(__file__).resolve().parents[5]
    result = subprocess.run(
        [PYTHON, str(SCRIPT), "--project-root", str(pr)] + argv,
        capture_output=True, text=True, timeout=30, env=run_env,
    )
    return result.returncode, result.stdout, result.stderr


def _make_state(tmp_path: Path, **overrides) -> Path:
    """Write a minimal .rebuild-state.json and return its path."""
    state: dict = {
        "primary_lang": "en",
        "last_rebuild_sha": "abc123",
        "translations": {},
    }
    state.update(overrides)
    p = tmp_path / "docs" / ".rebuild-state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state), encoding="utf-8")
    return p


def _make_primary_docs(tmp_path: Path) -> Path:
    """Create a minimal primary docs tree and return its path."""
    root = tmp_path / "docs"
    (root / "system").mkdir(parents=True, exist_ok=True)
    (root / "system" / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (root / "generated").mkdir(exist_ok=True)
    (root / "generated" / "api-contracts.md").write_text("# API\n", encoding="utf-8")
    (root / "flows").mkdir(exist_ok=True)
    (root / "flows" / "main.md").write_text("# Flows\n", encoding="utf-8")
    (root / "screens" / "SCR001").mkdir(parents=True, exist_ok=True)
    (root / "screens" / "SCR001" / "spec.md").write_text("# Screen\n", encoding="utf-8")
    return root


# ===========================================================================
# Unit: is_stale
# ===========================================================================

class TestIsStale:
    def test_fresh_sha_and_pass_not_stale(self):
        entry = {"translated_from_sha": "abc123", "passes_translated": ["core"]}
        assert not is_stale(entry, "abc123", "core")

    def test_sha_behind_is_stale(self):
        entry = {"translated_from_sha": "old000", "passes_translated": ["core"]}
        assert is_stale(entry, "abc123", "core")

    def test_pass_missing_is_stale(self):
        entry = {"translated_from_sha": "abc123", "passes_translated": ["core"]}
        assert is_stale(entry, "abc123", "feature-specs")

    def test_empty_entry_is_stale(self):
        assert is_stale({}, "abc123", "core")


# ===========================================================================
# Unit: secondary_langs
# ===========================================================================

class TestSecondaryLangs:
    def test_excludes_primary(self):
        state = {"primary_lang": "en", "translations": {"vi": {}, "en": {}}}
        assert secondary_langs(state) == ["vi"]

    def test_empty_translations(self):
        state = {"primary_lang": "en", "translations": {}}
        assert secondary_langs(state) == []

    def test_no_translations_key(self):
        assert secondary_langs({}) == []

    def test_dedupes_alias_and_canonical(self):
        # [M1] partially-migrated state with both jp + ja → one canonical entry, not two.
        state = {"primary_lang": "en", "translations": {"jp": {}, "ja": {}}}
        result = secondary_langs(state)
        assert len(result) == 1  # only one (first-seen raw key kept)
        assert result[0] in ("jp", "ja")

    def test_excludes_aliased_primary(self):
        # primary=ja, a "jp" translation key normalizes to ja → not a secondary.
        state = {"primary_lang": "ja", "translations": {"jp": {}, "vi": {}}}
        assert secondary_langs(state) == ["vi"]


# ===========================================================================
# Unit: parse_lang_statuses — path-traversal rejection
# ===========================================================================

class TestParseLangStatuses:
    def test_normal_entry(self):
        r = parse_lang_statuses(["vi:synced"])
        assert r == {"vi": {"status": "synced"}}

    def test_with_reason(self):
        # [D1] "jp" is aliased to canonical "ja" inside parse_lang_statuses.
        r = parse_lang_statuses(["jp:failed:timeout"])
        assert r["ja"] == {"status": "failed", "reason": "timeout"}

    def test_traversal_rejected(self):
        # lang code with "/" must be rejected silently (normalize_lang raises)
        r = parse_lang_statuses(["../evil:synced"])
        assert r == {}

    def test_dot_rejected(self):
        r = parse_lang_statuses([".hidden:synced"])
        assert r == {}

    def test_malformed_entry_skipped(self):
        r = parse_lang_statuses(["nocolon"])
        assert r == {}


# ===========================================================================
# Unit: render_handoff — all 5 canonical cases byte-for-byte
# ===========================================================================

class TestRenderHandoff:
    def test_none_registered(self):
        assert render_handoff({"pass": "core", "languages": []}) == "none registered"

    def test_all_synced(self):
        report = {"pass": "core", "languages": [
            {"lang": "vi", "status": "synced"},
            {"lang": "jp", "status": "synced"},
        ]}
        assert render_handoff(report) == "synced core → vi, jp (2/2)"

    def test_all_synced_single(self):
        report = {"pass": "feature-specs", "languages": [{"lang": "vi", "status": "synced"}]}
        assert render_handoff(report) == "synced feature-specs → vi (1/1)"

    def test_mixed_failed(self):
        report = {"pass": "core", "languages": [
            {"lang": "vi", "status": "synced"},
            {"lang": "jp", "status": "failed"},
        ]}
        result = render_handoff(report)
        assert result == (
            "⚠ synced: vi | STALE (failed): jp"
            " — re-sync stale with /tkm:rebuild-spec --lang jp"
        )

    def test_mixed_deferred(self):
        report = {"pass": "core", "languages": [
            {"lang": "vi", "status": "synced"},
            {"lang": "jp", "status": "deferred"},
        ]}
        result = render_handoff(report)
        assert result == (
            "⚠ synced: vi | STALE (auto-sync off): jp"
            " — re-sync stale with /tkm:rebuild-spec --lang jp"
        )

    def test_resync_command_never_has_pass_suffix(self):
        """Regression: command must be /tkm:rebuild-spec --lang <code> only."""
        report = {"pass": "flows", "languages": [{"lang": "vi", "status": "failed"}]}
        result = render_handoff(report)
        assert "--flows" not in result
        assert "--feature-specs" not in result
        assert "/tkm:rebuild-spec --lang vi" in result

    def test_failed_and_deferred_both_in_resync(self):
        report = {"pass": "core", "languages": [
            {"lang": "vi", "status": "failed"},
            {"lang": "jp", "status": "deferred"},
        ]}
        result = render_handoff(report)
        assert "STALE (failed): vi" in result
        assert "STALE (auto-sync off): jp" in result
        assert "/tkm:rebuild-spec --lang vi" in result
        assert "/tkm:rebuild-spec --lang jp" in result


# ===========================================================================
# Unit: summarize_from_report — report-missing case
# ===========================================================================

class TestSummarizeFromReport:
    def test_missing_file_returns_report_missing_msg(self, tmp_path):
        p = tmp_path / "translation-sync-report.json"
        assert summarize_from_report(p) == REPORT_MISSING_MSG

    def test_empty_file_returns_report_missing_msg(self, tmp_path):
        p = tmp_path / "translation-sync-report.json"
        p.write_text("", encoding="utf-8")
        assert summarize_from_report(p) == REPORT_MISSING_MSG

    def test_corrupt_json_returns_report_missing_msg(self, tmp_path):
        p = tmp_path / "translation-sync-report.json"
        p.write_text("{bad json", encoding="utf-8")
        assert summarize_from_report(p) == REPORT_MISSING_MSG

    def test_valid_report_delegates_to_render_handoff(self, tmp_path):
        p = tmp_path / "translation-sync-report.json"
        report = {"pass": "core", "languages": [{"lang": "vi", "status": "synced"}]}
        p.write_text(json.dumps(report), encoding="utf-8")
        assert summarize_from_report(p) == "synced core → vi (1/1)"

    def test_report_missing_msg_exact_wording(self):
        """Byte-for-byte match against pipeline-translate.md:383-384."""
        assert REPORT_MISSING_MSG == (
            "⚠ auto-sync did NOT run (no translation-sync-report.json)"
            " — secondary mirrors may be stale. "
            "Re-run the pass, or sync manually with /tkm:rebuild-spec --lang <code>."
        )


# ===========================================================================
# Unit: discover_artifacts — includes screens/
# ===========================================================================

class TestDiscoverArtifacts:
    def test_includes_screens(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        arts = discover_artifacts(root)
        screen_arts = [a for a in arts if a.startswith("screens/")]
        assert screen_arts, "screens/ artifacts must be discovered (lang-sync-fix)"

    def test_includes_system(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        assert any(a.startswith("system/") for a in discover_artifacts(root))

    def test_includes_generated(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        assert any(a.startswith("generated/") for a in discover_artifacts(root))

    def test_includes_flows(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        assert any(a.startswith("flows/") for a in discover_artifacts(root))

    def test_includes_job_list(self, tmp_path):
        """F2 discovery test (v26.1.0 jobs pass): job-list.md lives under generated/,
        already covered by _DOC_AREAS's ("generated", "*.md") glob — no code change
        required, this asserts that fact stays true."""
        root = _make_primary_docs(tmp_path)
        (root / "generated" / "job-list.md").write_text("# Job List\n", encoding="utf-8")
        arts = discover_artifacts(root)
        assert "generated/job-list.md" in arts

    def test_includes_feature_test_cases(self, tmp_path):
        """F2 discovery test (v26.1.0 test-cases pass): test-cases.md lives under
        features/{fcode}/, already covered by _DOC_AREAS's ("features", "*/*.md")
        glob — no code change required, this asserts that fact stays true."""
        root = _make_primary_docs(tmp_path)
        feat_dir = root / "features" / "F001_Login"
        feat_dir.mkdir(parents=True, exist_ok=True)
        (feat_dir / "test-cases.md").write_text("# Test Cases\n", encoding="utf-8")
        arts = discover_artifacts(root)
        assert "features/F001_Login/test-cases.md" in arts

    def test_empty_root_returns_empty(self, tmp_path):
        assert discover_artifacts(tmp_path / "nonexistent") == []

    # --- [acsim phase-02 / A1 remaining passes] confidence-report companion glob-mirror ---
    # Verifies the finding from Decision 7 / researcher-01 Q4: confidence-report_*.md sidecars
    # landing beside flows/glossary/system-synthesis artifacts are discovered by the SAME
    # directory-scan globs as their primary artifact — zero _DOC_AREAS code change needed.

    def test_flows_companion_discovered_by_existing_glob(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        (root / "flows" / "confidence-report_main.md").write_text("# CR\n", encoding="utf-8")
        arts = discover_artifacts(root)
        assert "flows/confidence-report_main.md" in arts

    def test_glossary_companion_discovered_by_existing_glob(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        (root / "system" / "confidence-report_glossary.md").write_text("# CR\n", encoding="utf-8")
        arts = discover_artifacts(root)
        assert "system/confidence-report_glossary.md" in arts

    def test_system_synthesis_companion_discovered_by_existing_glob(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        (root / "system" / "confidence-report_overview.md").write_text("# CR\n", encoding="utf-8")
        arts = discover_artifacts(root)
        assert "system/confidence-report_overview.md" in arts


# ===========================================================================
# Unit: compute_plan_worklist
# ===========================================================================

class TestComputePlanWorklist:
    def _state_with_vi(self, sha: str = "abc123", passes: list | None = None) -> dict:
        return {
            "primary_lang": "en",
            "last_rebuild_sha": "abc123",
            "translations": {
                "vi": {
                    "translated_from_sha": sha,
                    "passes_translated": passes or ["core"],
                }
            },
        }

    def test_up_to_date_lang_empty_artifacts(self, tmp_path):
        state = self._state_with_vi("abc123", ["core"])
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert not vi["stale"]
        assert vi["artifacts_to_translate"] == []

    def test_behind_sha_is_stale(self, tmp_path):
        state = self._state_with_vi("old000", ["core"])
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["stale"]
        assert len(vi["artifacts_to_translate"]) > 0

    def test_pass_not_translated_is_stale(self, tmp_path):
        state = self._state_with_vi("abc123", ["core"])
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "feature-specs", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["stale"]

    def test_first_translate_uses_all_artifacts(self, tmp_path):
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {"vi": {}}}
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["stale"]
        assert len(vi["artifacts_to_translate"]) > 0

    def test_stale_file_used_for_incremental(self, tmp_path):
        state = self._state_with_vi("old000", ["core"])
        root = _make_primary_docs(tmp_path)
        stale_path = tmp_path / "plan" / "artifacts" / "translation-stale.json"
        stale_path.parent.mkdir(parents=True)
        stale_path.write_text(json.dumps({
            "pass": "core", "changed_artifacts": ["system/overview.md"], "primary_cursor_sha": "abc123"
        }), encoding="utf-8")
        w = compute_plan_worklist(state, "core", root, stale_path)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["artifacts_to_translate"] == ["system/overview.md"]

    def test_no_secondary_langs_empty_list(self, tmp_path):
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "core", root, None)
        assert w["languages"] == []

    def test_auto_sync_disabled_marks_deferred(self, tmp_path, monkeypatch):
        monkeypatch.setenv("REBUILD_AUTO_SYNC_TRANSLATIONS", "0")
        state = self._state_with_vi("old000", ["core"])
        root = _make_primary_docs(tmp_path)
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi.get("deferred") is True
        assert w["auto_sync_enabled"] is False

    def test_schema_version_is_1(self, tmp_path):
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        w = compute_plan_worklist(state, "core", tmp_path, None)
        assert w["schema_version"] == 1


# ===========================================================================
# Unit: compute_finalize_result
# ===========================================================================

class TestComputeFinalizeResult:
    def test_synced_with_promoted_dir_updates_cursor(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        # Create docs/vi/ to simulate promotion
        vi_dir = tmp_path / "docs" / "vi"
        vi_dir.mkdir(parents=True)
        state = {
            "primary_lang": "en",
            "last_rebuild_sha": "abc123",
            "translations": {"vi": {"translated_from_sha": "old", "passes_translated": ["core"]}},
        }
        lang_statuses = {"vi": {"status": "synced"}}
        updated, report = compute_finalize_result(state, "feature-specs", root, lang_statuses)
        assert updated["translations"]["vi"]["translated_from_sha"] == "abc123"
        assert "feature-specs" in updated["translations"]["vi"]["passes_translated"]
        assert "core" in updated["translations"]["vi"]["passes_translated"]

    def test_synced_without_promoted_dir_downgraded_to_failed(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        # docs/vi/ does NOT exist
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        _, report = compute_finalize_result(state, "core", root, {"vi": {"status": "synced"}})
        vi_result = next(r for r in report["languages"] if r["lang"] == "vi")
        assert vi_result["status"] == "failed"
        assert vi_result["reason"] == "promoted_dir_missing"

    def test_failed_status_preserved(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        _, report = compute_finalize_result(state, "core", root, {"vi": {"status": "failed", "reason": "timeout"}})
        vi = next(r for r in report["languages"] if r["lang"] == "vi")
        assert vi["status"] == "failed"
        assert vi["reason"] == "timeout"

    def test_deferred_status_preserved(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        _, report = compute_finalize_result(
            state, "core", root,
            {"vi": {"status": "deferred", "reason": "REBUILD_AUTO_SYNC_TRANSLATIONS=0"}}
        )
        vi = next(r for r in report["languages"] if r["lang"] == "vi")
        assert vi["status"] == "deferred"

    def test_passes_translated_sorted_and_deduped(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        vi_dir = tmp_path / "docs" / "vi"
        vi_dir.mkdir(parents=True)
        state = {
            "primary_lang": "en",
            "last_rebuild_sha": "abc123",
            "translations": {"vi": {"translated_from_sha": "abc123", "passes_translated": ["core", "flows"]}},
        }
        updated, _ = compute_finalize_result(state, "core", root, {"vi": {"status": "synced"}})
        passes = updated["translations"]["vi"]["passes_translated"]
        assert passes == sorted(set(passes))
        assert passes.count("core") == 1

    def test_report_schema_version_1(self, tmp_path):
        root = _make_primary_docs(tmp_path)
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        _, report = compute_finalize_result(state, "core", root, {})
        assert report["schema_version"] == 1


# ===========================================================================
# Integration: plan mode via subprocess
# ===========================================================================

class TestPlanModeIntegration:
    def test_plan_mode_emits_valid_json(self, tmp_path):
        state_path = _make_state(tmp_path)
        code, out, _ = _run([
            "--mode", "plan", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
        ], project_root=tmp_path)
        assert code == 0
        data = json.loads(out)
        assert data["schema_version"] == 1
        assert data["pass"] == "core"
        assert "languages" in data

    def test_plan_mode_no_secondary_langs(self, tmp_path):
        state_path = _make_state(tmp_path)
        code, out, _ = _run([
            "--mode", "plan", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
        ], project_root=tmp_path)
        assert code == 0
        assert json.loads(out)["languages"] == []

    def test_plan_mode_stale_lang_populated(self, tmp_path):
        _make_primary_docs(tmp_path)
        state_path = _make_state(tmp_path, translations={
            "vi": {"translated_from_sha": "old000", "passes_translated": ["core"]}
        })
        code, out, _ = _run([
            "--mode", "plan", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
        ], project_root=tmp_path)
        assert code == 0
        langs = json.loads(out)["languages"]
        vi = next(l for l in langs if l["lang"] == "vi")
        assert vi["stale"]
        assert len(vi["artifacts_to_translate"]) > 0

    def test_plan_missing_pass_exits_2(self, tmp_path):
        state_path = _make_state(tmp_path)
        code, _, err = _run([
            "--mode", "plan",
            "--state", str(state_path),
        ], project_root=tmp_path)
        assert code == 2
        assert "--pass" in err


# ===========================================================================
# Integration: finalize mode via subprocess
# ===========================================================================

class TestFinalizeModeIntegration:
    def test_finalize_writes_report_and_exits_0(self, tmp_path):
        _make_primary_docs(tmp_path)
        # Create docs/vi/ so synced claim passes
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        state_path = _make_state(tmp_path, translations={"vi": {}})
        report_out = tmp_path / "report.json"
        code, out, _ = _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
        ], project_root=tmp_path)
        assert code == 0
        assert report_out.is_file()
        report = json.loads(report_out.read_text())
        assert report["schema_version"] == 1

    def test_finalize_stdout_last_line_starts_with_secondary_languages(self, tmp_path):
        _make_primary_docs(tmp_path)
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        state_path = _make_state(tmp_path, translations={"vi": {}})
        report_out = tmp_path / "report.json"
        _, out, _ = _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
        ], project_root=tmp_path)
        last_line = out.strip().splitlines()[-1]
        assert last_line.startswith("Secondary languages:")

    def test_finalize_updates_state_cursor(self, tmp_path):
        _make_primary_docs(tmp_path)
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        state_path = _make_state(tmp_path, translations={"vi": {"translated_from_sha": "old", "passes_translated": []}})
        report_out = tmp_path / "report.json"
        _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
        ], project_root=tmp_path)
        state = json.loads(state_path.read_text())
        assert state["translations"]["vi"]["translated_from_sha"] == "abc123"
        assert "core" in state["translations"]["vi"]["passes_translated"]

    def test_finalize_idempotent(self, tmp_path):
        """Running finalize twice with same inputs yields identical state + report."""
        _make_primary_docs(tmp_path)
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        state_path = _make_state(tmp_path, translations={"vi": {}})
        report_out = tmp_path / "report.json"
        argv = [
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
        ]
        _run(argv, project_root=tmp_path)
        state1 = json.loads(state_path.read_text())
        report1 = json.loads(report_out.read_text())

        _run(argv, project_root=tmp_path)
        state2 = json.loads(state_path.read_text())
        report2 = json.loads(report_out.read_text())

        assert state1["translations"] == state2["translations"]
        assert report1["languages"] == report2["languages"]

    def test_finalize_synced_without_dir_downgraded(self, tmp_path):
        _make_primary_docs(tmp_path)
        # docs/vi/ intentionally absent
        state_path = _make_state(tmp_path, translations={"vi": {}})
        report_out = tmp_path / "report.json"
        code, out, _ = _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
        ], project_root=tmp_path)
        assert code == 0
        report = json.loads(report_out.read_text())
        vi = next(r for r in report["languages"] if r["lang"] == "vi")
        assert vi["status"] == "failed"
        assert vi["reason"] == "promoted_dir_missing"
        # Cursor must NOT have been updated
        state = json.loads(state_path.read_text())
        assert "vi" not in state.get("translations", {}) or \
               state["translations"].get("vi", {}).get("translated_from_sha") != "abc123"

    def test_finalize_multiple_lang_statuses(self, tmp_path):
        _make_primary_docs(tmp_path)
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        # ja dir absent — will be downgraded ("jp" status alias-normalizes to "ja")
        state_path = _make_state(tmp_path, translations={"vi": {}, "ja": {}})
        report_out = tmp_path / "report.json"
        code, out, _ = _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:synced",
            "--lang-status", "jp:synced",
        ], project_root=tmp_path)
        assert code == 0
        last_line = out.strip().splitlines()[-1]
        assert "STALE (failed): ja" in last_line
        assert "synced: vi" in last_line

    def test_finalize_deferred_handoff_wording(self, tmp_path):
        _make_primary_docs(tmp_path)
        state_path = _make_state(tmp_path, translations={"vi": {}})
        report_out = tmp_path / "report.json"
        _, out, _ = _run([
            "--mode", "finalize", "--pass", "core",
            "--state", str(state_path),
            "--primary-docs-root", str(tmp_path / "docs"),
            "--report-out", str(report_out),
            "--lang-status", "vi:deferred:REBUILD_AUTO_SYNC_TRANSLATIONS=0",
        ], project_root=tmp_path)
        last_line = out.strip().splitlines()[-1]
        assert "STALE (auto-sync off): vi" in last_line
        assert "/tkm:rebuild-spec --lang vi" in last_line


# ===========================================================================
# Integration: summarize mode via subprocess
# ===========================================================================

class TestSummarizeModeIntegration:
    def test_summarize_missing_report(self, tmp_path):
        code, out, _ = _run([
            "--mode", "summarize",
            "--report-out", str(tmp_path / "missing.json"),
        ], project_root=tmp_path)
        assert code == 0
        assert out.strip() == f"Secondary languages: {REPORT_MISSING_MSG}"

    def test_summarize_none_registered(self, tmp_path):
        rp = tmp_path / "report.json"
        rp.write_text(json.dumps({"pass": "core", "languages": []}), encoding="utf-8")
        _, out, _ = _run([
            "--mode", "summarize", "--report-out", str(rp),
        ], project_root=tmp_path)
        assert out.strip() == "Secondary languages: none registered"

    def test_summarize_all_synced(self, tmp_path):
        rp = tmp_path / "report.json"
        rp.write_text(json.dumps({
            "pass": "core",
            "languages": [{"lang": "vi", "status": "synced"}]
        }), encoding="utf-8")
        _, out, _ = _run([
            "--mode", "summarize", "--report-out", str(rp),
        ], project_root=tmp_path)
        assert out.strip() == "Secondary languages: synced core → vi (1/1)"


# ---------------------------------------------------------------------------
# Per-lang layout — exercises the mode-aware resolver path so a missed
# resolve_docs_root callsite surfaces as a test failure, not a user TypeError
# (Phase 06 / AssumDest-F3). primary_root is docs/<primary>/ in per-lang mode.
# ---------------------------------------------------------------------------
class TestPerLangResolution:
    def test_lang_docs_path_per_lang_root(self, tmp_path):
        # per-lang: primary docs root is docs/en; secondary vi → docs/vi (siblings)
        primary_root = tmp_path / "docs" / "en"
        primary_root.mkdir(parents=True)
        assert lang_docs_path(primary_root, "vi", "en") == (tmp_path / "docs" / "vi")

    def test_lang_docs_path_single_lang_root(self, tmp_path):
        # single-lang legacy invocation: primary docs root is docs/
        primary_root = tmp_path / "docs"
        primary_root.mkdir(parents=True)
        assert lang_docs_path(primary_root, "vi", "en") == (tmp_path / "docs" / "vi")

    def test_lang_docs_path_alias_normalized(self, tmp_path):
        primary_root = tmp_path / "docs" / "en"
        primary_root.mkdir(parents=True)
        # "jp" secondary de-aliases to "ja"
        assert lang_docs_path(primary_root, "jp", "en") == (tmp_path / "docs" / "ja")

    def test_finalize_per_lang_synced(self, tmp_path):
        # Full finalize under per-lang: primary at docs/en, secondary promoted to docs/vi.
        (tmp_path / "docs" / "en" / "system").mkdir(parents=True)
        (tmp_path / "docs" / "en" / "system" / "overview.md").write_text("# o\n", encoding="utf-8")
        (tmp_path / "docs" / "vi").mkdir(parents=True)
        state = {
            "primary_lang": "en",
            "last_rebuild_sha": "abc123",
            "translations": {"vi": {"translated_from_sha": "old", "passes_translated": ["core"]}},
        }
        primary_root = tmp_path / "docs" / "en"
        updated, report = compute_finalize_result(
            state, "core", primary_root, {"vi": {"status": "synced"}}
        )
        vi = next(r for r in report["languages"] if r["lang"] == "vi")
        assert vi["status"] == "synced"  # NOT downgraded — dir resolved correctly
        assert updated["translations"]["vi"]["translated_from_sha"] == "abc123"


# ===========================================================================
# P05 / D2 + D6 — Per-component mirror artifact discovery + auto-sync
# ===========================================================================

def _make_primary_docs_with_components(tmp_path: Path) -> Path:
    """Create a primary docs tree that includes per-component artifact dirs."""
    root = tmp_path / "docs"
    (root / "system").mkdir(parents=True, exist_ok=True)
    (root / "system" / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (root / "components" / "payments").mkdir(parents=True, exist_ok=True)
    (root / "components" / "payments" / "architecture.md").write_text(
        "# Architecture\n\nSome prose.\n", encoding="utf-8"
    )
    (root / "components" / "payments" / "business-context.md").write_text(
        "# Business Context\n\nSome prose.\n", encoding="utf-8"
    )
    (root / "components" / "orders").mkdir(parents=True, exist_ok=True)
    (root / "components" / "orders" / "architecture.md").write_text(
        "# Architecture\n\nOrders prose.\n", encoding="utf-8"
    )
    return root


class TestComponentMirrorDiscovery:
    """(a) discover_artifacts includes components/*/*.md — P05/D6."""

    def test_includes_component_artifacts(self, tmp_path):
        root = _make_primary_docs_with_components(tmp_path)
        arts = discover_artifacts(root)
        comp_arts = [a for a in arts if a.startswith("components/")]
        assert len(comp_arts) >= 3, f"expected ≥3 component artifacts, got {comp_arts}"

    def test_includes_specific_component_files(self, tmp_path):
        root = _make_primary_docs_with_components(tmp_path)
        arts = discover_artifacts(root)
        assert "components/payments/architecture.md" in arts
        assert "components/payments/business-context.md" in arts
        assert "components/orders/architecture.md" in arts

    def test_still_includes_system_artifacts(self, tmp_path):
        root = _make_primary_docs_with_components(tmp_path)
        arts = discover_artifacts(root)
        assert "system/overview.md" in arts

    def test_no_components_dir_returns_no_component_artifacts(self, tmp_path):
        """en-primary single-lang repo without components/ → no component entries."""
        root = _make_primary_docs(tmp_path)  # uses the helper from the top of this file
        arts = discover_artifacts(root)
        comp_arts = [a for a in arts if a.startswith("components/")]
        assert comp_arts == [], (
            "a docs tree with no components/ dir must not emit component artifacts"
        )


class TestComponentNestedDiscovery:
    """M2 — components/**/*.md glob discovers nested subdirs; draft shadows excluded."""

    def _make_nested_components(self, tmp_path: Path) -> Path:
        """Create a realistic nested component structure under docs/."""
        root = tmp_path / "docs"
        comp = root / "components" / "payments"
        (comp / "system").mkdir(parents=True, exist_ok=True)
        (comp / "system" / "overview.md").write_text("# Overview\n", encoding="utf-8")
        (comp / "generated").mkdir(parents=True, exist_ok=True)
        (comp / "generated" / "screen-list.md").write_text("# Screens\n", encoding="utf-8")
        (comp / "features" / "F001_checkout").mkdir(parents=True, exist_ok=True)
        (comp / "features" / "F001_checkout" / "spec.md").write_text("# Spec\n", encoding="utf-8")
        (comp / "flows").mkdir(parents=True, exist_ok=True)
        (comp / "flows" / "main.md").write_text("# Flows\n", encoding="utf-8")
        return root

    def test_nested_component_docs_are_discovered(self, tmp_path):
        """components/<name>/system/*.md, generated/*.md, features/<F>/*.md, flows/*.md
        must all appear in the worklist (M2 fix: was skipped by depth-1 glob).
        """
        root = self._make_nested_components(tmp_path)
        arts = discover_artifacts(root)
        comp_arts = [a for a in arts if a.startswith("components/")]
        assert "components/payments/system/overview.md" in comp_arts, (
            "system/overview.md (nested) must be discovered"
        )
        assert "components/payments/generated/screen-list.md" in comp_arts, (
            "generated/screen-list.md (nested) must be discovered"
        )
        assert "components/payments/features/F001_checkout/spec.md" in comp_arts, (
            "features/<F>/spec.md (nested) must be discovered"
        )
        assert "components/payments/flows/main.md" in comp_arts, (
            "flows/main.md (nested) must be discovered"
        )

    def test_draft_shadows_excluded_from_component_discovery(self, tmp_path):
        """*.draft.md files in components/ must NOT appear in the worklist."""
        root = self._make_nested_components(tmp_path)
        comp = root / "components" / "payments" / "system"
        (comp / "overview.draft.md").write_text("# DRAFT\n", encoding="utf-8")
        arts = discover_artifacts(root)
        draft_arts = [a for a in arts if a.endswith(".draft.md")]
        assert draft_arts == [], (
            f"draft shadows must be excluded from discovery, found: {draft_arts}"
        )

    def test_non_draft_md_not_excluded(self, tmp_path):
        """Normal .md files must still appear after the draft filter is in place."""
        root = self._make_nested_components(tmp_path)
        arts = discover_artifacts(root)
        assert any(a.startswith("components/") and not a.endswith(".draft.md") for a in arts), (
            "non-draft component artifacts must be present"
        )


class TestComponentWorklist:
    """(b) compute_plan_worklist enumerates component mirrors; (c) changed-only; (d) opt-out; (e) no spurious."""

    def _state_with_vi(self, sha: str = "abc123", passes: list | None = None) -> dict:
        return {
            "primary_lang": "en",
            "last_rebuild_sha": "abc123",
            "translations": {
                "vi": {
                    "translated_from_sha": sha,
                    "passes_translated": passes or ["core"],
                }
            },
        }

    def test_stale_lang_includes_component_artifacts(self, tmp_path):
        """(b) stale vi lang → worklist includes components/*/*.md entries."""
        root = _make_primary_docs_with_components(tmp_path)
        state = self._state_with_vi("old000", ["core"])
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["stale"]
        comp_arts = [a for a in vi["artifacts_to_translate"] if a.startswith("components/")]
        assert len(comp_arts) >= 1, (
            f"stale worklist must include component artifacts, got {vi['artifacts_to_translate']}"
        )

    def test_changed_only_stale_file_scoped_to_component_artifact(self, tmp_path):
        """(c) stale-file with a single component artifact → only that file in worklist."""
        root = _make_primary_docs_with_components(tmp_path)
        state = self._state_with_vi("old000", ["core"])
        stale_path = tmp_path / "plan" / "artifacts" / "translation-stale.json"
        stale_path.parent.mkdir(parents=True)
        stale_path.write_text(json.dumps({
            "pass": "core",
            "changed_artifacts": ["components/payments/architecture.md"],
            "primary_cursor_sha": "abc123",
        }), encoding="utf-8")
        w = compute_plan_worklist(state, "core", root, stale_path)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi["artifacts_to_translate"] == ["components/payments/architecture.md"], (
            "changed-only: only the listed component artifact should be scheduled"
        )

    def test_up_to_date_lang_no_component_artifacts_scheduled(self, tmp_path):
        """(c) up-to-date lang → empty worklist (no spurious component re-translation)."""
        root = _make_primary_docs_with_components(tmp_path)
        state = self._state_with_vi("abc123", ["core"])
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert not vi["stale"]
        assert vi["artifacts_to_translate"] == []

    def test_auto_sync_disabled_defers_component_artifacts(self, tmp_path, monkeypatch):
        """(d) REBUILD_AUTO_SYNC_TRANSLATIONS=0 → deferred, no component artifacts in worklist."""
        monkeypatch.setenv("REBUILD_AUTO_SYNC_TRANSLATIONS", "0")
        root = _make_primary_docs_with_components(tmp_path)
        state = self._state_with_vi("old000", ["core"])
        w = compute_plan_worklist(state, "core", root, None)
        vi = next(l for l in w["languages"] if l["lang"] == "vi")
        assert vi.get("deferred") is True
        assert vi["artifacts_to_translate"] == []
        assert w["auto_sync_enabled"] is False

    def test_no_secondary_langs_no_component_worklist(self, tmp_path):
        """(e) en-primary single-lang → empty worklist even when components/ exists."""
        root = _make_primary_docs_with_components(tmp_path)
        state = {"primary_lang": "en", "last_rebuild_sha": "abc123", "translations": {}}
        w = compute_plan_worklist(state, "core", root, None)
        assert w["languages"] == [], (
            "no secondary langs registered → no component mirrors scheduled"
        )


class TestComponentSkeletonIdentity:
    """Skeleton validator on a component mirror artifact (reuse — same as core tier)."""

    def test_identical_primary_and_mirror_passes(self, tmp_path):
        """A mirror with prose translated but skeleton identical → PASS."""
        from validate_translation_skeleton import validate

        primary = tmp_path / "architecture.md"
        mirror = tmp_path / "architecture-vi.md"
        primary.write_text(
            "# Architecture\n\n## Overview\n\nSome English prose here.\n",
            encoding="utf-8",
        )
        mirror.write_text(
            "# Architecture\n\n## Overview\n\nSome Vietnamese prose here.\n",
            encoding="utf-8",
        )
        issues = validate(primary, mirror)
        assert issues == [], f"expected PASS, got issues: {issues}"

    def test_heading_drift_in_mirror_fails(self, tmp_path):
        """A mirror with a translated heading (skeleton drift) → CRITICAL issue."""
        from validate_translation_skeleton import validate

        primary = tmp_path / "architecture.md"
        mirror = tmp_path / "architecture-vi.md"
        primary.write_text(
            "# Architecture\n\n## Overview\n\nProse.\n",
            encoding="utf-8",
        )
        mirror.write_text(
            "# Kiến trúc\n\n## Tổng quan\n\nProse dịch.\n",  # headings translated — violation
            encoding="utf-8",
        )
        issues = validate(primary, mirror)
        assert any(i["severity"] == "critical" for i in issues), (
            "translated headings must be caught as skeleton drift"
        )

    def test_primary_unchanged_after_validate(self, tmp_path):
        """(b) Skeleton validation must NOT mutate the primary file."""
        from validate_translation_skeleton import validate

        primary = tmp_path / "architecture.md"
        mirror = tmp_path / "architecture-vi.md"
        content = "# Architecture\n\nEnglish.\n"
        primary.write_text(content, encoding="utf-8")
        mirror.write_text("# Architecture\n\nVietnamese.\n", encoding="utf-8")
        validate(primary, mirror)
        assert primary.read_text(encoding="utf-8") == content, (
            "primary source must not be mutated by skeleton validation"
        )
