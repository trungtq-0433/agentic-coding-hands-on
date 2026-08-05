"""Tests for check_translation_gate.py — translation sync completion gate.

Run via:
  python3 -m pytest claude/skills/rebuild-spec/scripts/tests/test_check_translation_gate.py -v

Coverage:
  - no secondary langs → PASS
  - auto-sync off (REBUILD_AUTO_SYNC_TRANSLATIONS=0) → PASS + warning, NOT fail
  - report missing + langs + auto-sync on → FAIL (gate.report_missing)
  - report present with wrong pass → FAIL (gate.report_stale_pass)
  - report present all synced (cursors fresh) → PASS
  - report present one lang failed (cursor stale) → FAIL (gate.lang_behind_cursor)
  - lang translated_from_sha behind primary cursor → FAIL
  - pass not in passes_translated → FAIL
  - idempotency: same inputs → same verdict
  - path safety: --plan-dir outside project root → exit 2
  - --plan-dir is a file → exit 2
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "check_translation_gate.py"
PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(plan_dir: Path, pass_name: str, project_root: Path | None = None,
         env_overrides: dict | None = None, extra_args: list[str] | None = None) -> tuple[int, dict | None, str]:
    """Run check_translation_gate.py; return (returncode, parsed_json_or_None, stderr)."""
    run_env = os.environ.copy()
    if env_overrides:
        run_env.update(env_overrides)
    pr = project_root or plan_dir.parent
    args = [PYTHON, str(SCRIPT),
            "--plan-dir", str(plan_dir),
            "--pass", pass_name,
            "--project-root", str(pr)]
    if extra_args:
        args += extra_args
    result = subprocess.run(args, capture_output=True, text=True, timeout=30, env=run_env)
    data = None
    if result.stdout.strip():
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return result.returncode, data, result.stderr


def _make_plan(tmp_path: Path, state: dict | None = None, report: dict | None = None) -> Path:
    """Create plan dir with optional state and report."""
    plan_dir = tmp_path / "my-plan"
    (plan_dir / "artifacts").mkdir(parents=True)

    if state is not None:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / ".rebuild-state.json").write_text(json.dumps(state), encoding="utf-8")

    if report is not None:
        (plan_dir / "artifacts" / "translation-sync-report.json").write_text(
            json.dumps(report), encoding="utf-8"
        )

    return plan_dir


def _state(langs: dict | None = None, sha: str = "abc123") -> dict:
    """Build a minimal .rebuild-state.json dict."""
    return {
        "primary_lang": "en",
        "last_rebuild_sha": sha,
        "translations": langs or {},
    }


def _report(pass_name: str, languages: list[dict], sha: str = "abc123") -> dict:
    """Build a minimal translation-sync-report.json dict."""
    return {
        "schema_version": 1,
        "pass": pass_name,
        "primary_cursor_sha": sha,
        "auto_sync_enabled": True,
        "languages": languages,
    }


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in data.get("issues", [])]


def _severities(data: dict) -> list[str]:
    return [i["severity"] for i in data.get("issues", [])]


# ---------------------------------------------------------------------------
# No secondary langs → PASS (short-circuit before any report check)
# ---------------------------------------------------------------------------

class TestNoSecondaryLangs:
    def test_exit_zero(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 0

    def test_status_pass(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["status"] == "PASS"

    def test_no_issues(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["issues"] == []

    def test_no_langs_no_report_needed(self, tmp_path):
        """Even without a report file, no-langs is PASS."""
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        # No report created
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 0
        assert data["status"] == "PASS"

    def test_no_state_file_treated_as_no_langs(self, tmp_path):
        """Missing state file → empty translations → PASS (legacy/greenfield project)."""
        plan_dir = _make_plan(tmp_path)  # no state
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 0


# ---------------------------------------------------------------------------
# Auto-sync disabled → PASS + warning (never FAIL)
# ---------------------------------------------------------------------------

class TestAutoSyncDisabled:
    def test_exit_zero_not_one(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        code, _, _ = _run(plan_dir, "core", tmp_path,
                          env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        assert code == 0, "auto-sync opt-out must NEVER hard-fail (resolved design decision)"

    def test_status_pass(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path,
                          env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        assert data["status"] == "PASS"

    def test_warning_issue_present(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path,
                          env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        assert "gate.auto_sync_disabled" in _rule_ids(data)

    def test_warning_not_critical(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path,
                          env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        assert all(s != "critical" for s in _severities(data))

    def test_no_report_needed_when_disabled(self, tmp_path):
        """With auto-sync off, missing report must NOT cause FAIL."""
        # No report file, but auto-sync is off
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        code, data, _ = _run(plan_dir, "core", tmp_path,
                              env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        assert code == 0
        assert data["status"] == "PASS"

    def test_message_mentions_lang(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path,
                          env_overrides={"REBUILD_AUTO_SYNC_TRANSLATIONS": "0"})
        warn_issues = [i for i in data["issues"] if i["rule_id"] == "gate.auto_sync_disabled"]
        assert any("vi" in i["message"] for i in warn_issues)


# ---------------------------------------------------------------------------
# Report missing + langs + auto-sync on → FAIL (gate.report_missing)
# ---------------------------------------------------------------------------

class TestReportMissing:
    def test_exit_one(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        code, _, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1

    def test_status_fail(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["status"] == "FAIL"

    def test_rule_id_report_missing(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert "gate.report_missing" in _rule_ids(data)

    def test_fail_message_is_actionable(self, tmp_path):
        """FAIL message must tell operator exactly how to fix."""
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        missing_issues = [i for i in data["issues"] if i["rule_id"] == "gate.report_missing"]
        assert missing_issues
        msg = missing_issues[0]["message"]
        # Must mention the pass and instruct a fix
        assert "core" in msg
        assert "Re-run" in msg or "re-run" in msg or "/tkm:rebuild-spec" in msg

    def test_multiple_langs_still_single_report_missing_issue(self, tmp_path):
        """Multiple langs + missing report → one gate.report_missing issue (not one per lang)."""
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}, "jp": {}}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        missing = [i for i in data["issues"] if i["rule_id"] == "gate.report_missing"]
        assert len(missing) == 1


# ---------------------------------------------------------------------------
# Report present with wrong pass name → FAIL (gate.report_stale_pass)
# ---------------------------------------------------------------------------

class TestReportWrongPass:
    def test_wrong_pass_exits_one(self, tmp_path):
        # Report says "flows" but we're checking "core"
        plan_dir = _make_plan(
            tmp_path,
            state=_state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["flows"]}}),
            report=_report("flows", [{"lang": "vi", "status": "synced"}]),
        )
        code, _, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1

    def test_wrong_pass_rule_id(self, tmp_path):
        plan_dir = _make_plan(
            tmp_path,
            state=_state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["flows"]}}),
            report=_report("flows", [{"lang": "vi", "status": "synced"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert "gate.report_stale_pass" in _rule_ids(data)

    def test_wrong_pass_message_mentions_both_passes(self, tmp_path):
        plan_dir = _make_plan(
            tmp_path,
            state=_state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["flows"]}}),
            report=_report("flows", [{"lang": "vi", "status": "synced"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        stale = [i for i in data["issues"] if i["rule_id"] == "gate.report_stale_pass"]
        assert stale
        assert "core" in stale[0]["message"]
        assert "flows" in stale[0]["message"]


# ---------------------------------------------------------------------------
# Report present, all synced + fresh cursors → PASS
# ---------------------------------------------------------------------------

class TestAllSynced:
    def test_exit_zero(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        code, _, _ = _run(plan_dir, "core", tmp_path)
        assert code == 0

    def test_status_pass(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["status"] == "PASS"

    def test_no_critical_issues(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["summary"]["critical"] == 0

    def test_multiple_langs_all_synced(self, tmp_path):
        state = _state(langs={
            "vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]},
            "jp": {"translated_from_sha": "abc123", "passes_translated": ["core"]},
        })
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [
                {"lang": "vi", "status": "synced"},
                {"lang": "jp", "status": "synced"},
            ]),
        )
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 0
        assert data["status"] == "PASS"


# ---------------------------------------------------------------------------
# Report present but one lang has stale cursor → FAIL (gate.lang_behind_cursor)
# ---------------------------------------------------------------------------

class TestOneLangFailed:
    def test_stale_cursor_exits_one(self, tmp_path):
        # vi: translated from old sha — NOT the current primary cursor abc123
        state = _state(langs={"vi": {"translated_from_sha": "old000", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "failed"}]),
        )
        code, _, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1

    def test_stale_cursor_rule_id(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "old000", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "failed"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert "gate.lang_behind_cursor" in _rule_ids(data)

    def test_mixed_one_synced_one_stale_is_fail(self, tmp_path):
        state = _state(langs={
            "vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]},
            "jp": {"translated_from_sha": "old000", "passes_translated": ["core"]},
        })
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [
                {"lang": "vi", "status": "synced"},
                {"lang": "jp", "status": "failed"},
            ]),
        )
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1
        assert data["status"] == "FAIL"
        # Only jp is stale
        behind = [i for i in data["issues"] if i["rule_id"] == "gate.lang_behind_cursor"]
        assert any("jp" in i["message"] for i in behind)
        # vi must not appear in behind-cursor issues
        assert not any("vi" in i["message"] for i in behind)


# ---------------------------------------------------------------------------
# translated_from_sha behind primary cursor → FAIL
# ---------------------------------------------------------------------------

class TestShaBehinCursor:
    def test_sha_mismatch_is_fail(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "deadbeef", "passes_translated": ["core"]}},
                       sha="abc123")
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        code, data, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1
        assert "gate.lang_behind_cursor" in _rule_ids(data)

    def test_message_mentions_shas(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "deadbeef", "passes_translated": ["core"]}},
                       sha="abc123")
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        _, data, _ = _run(plan_dir, "core", tmp_path)
        behind = [i for i in data["issues"] if i["rule_id"] == "gate.lang_behind_cursor"]
        assert behind
        assert "deadbeef" in behind[0]["message"] or "abc123" in behind[0]["message"]


# ---------------------------------------------------------------------------
# Pass not in passes_translated → FAIL
# ---------------------------------------------------------------------------

class TestPassNotTranslated:
    def test_pass_missing_from_passes_translated_is_fail(self, tmp_path):
        # sha matches but "feature-specs" not yet in passes_translated
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("feature-specs", [{"lang": "vi", "status": "synced"}]),
        )
        code, data, _ = _run(plan_dir, "feature-specs", tmp_path)
        assert code == 1
        assert "gate.lang_behind_cursor" in _rule_ids(data)

    def test_empty_passes_translated_is_fail(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": []}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        code, _, _ = _run(plan_dir, "core", tmp_path)
        assert code == 1


# ---------------------------------------------------------------------------
# Idempotency: running gate twice produces same verdict
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_pass_verdict_idempotent(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        code1, data1, _ = _run(plan_dir, "core", tmp_path)
        code2, data2, _ = _run(plan_dir, "core", tmp_path)
        assert code1 == code2 == 0
        assert data1["status"] == data2["status"] == "PASS"

    def test_fail_verdict_idempotent(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        code1, data1, _ = _run(plan_dir, "core", tmp_path)
        code2, data2, _ = _run(plan_dir, "core", tmp_path)
        assert code1 == code2 == 1
        assert data1["status"] == data2["status"] == "FAIL"
        assert _rule_ids(data1) == _rule_ids(data2)

    def test_summary_out_idempotent(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        summary_out = tmp_path / "validation-summary.json"
        _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        snap1 = json.loads(summary_out.read_text())
        _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        snap2 = json.loads(summary_out.read_text())
        assert snap1["validators"]["translation_gate"]["status"] == snap2["validators"]["translation_gate"]["status"]


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

class TestPathSafety:
    def test_plan_dir_is_file_exits_two(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("hi")
        result = subprocess.run(
            [PYTHON, str(SCRIPT),
             "--plan-dir", str(bogus),
             "--pass", "core",
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()

    def test_plan_dir_outside_project_root_exits_two(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        inner_root = tmp_path / "inner"
        inner_root.mkdir()
        result = subprocess.run(
            [PYTHON, str(SCRIPT),
             "--plan-dir", str(outside),
             "--pass", "core",
             "--project-root", str(inner_root)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# Output shape / required keys
# ---------------------------------------------------------------------------

class TestOutputShape:
    def test_required_keys_present(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        for key in ("validator", "timestamp", "plan_dir", "pass", "status", "summary", "issues"):
            assert key in data, f"missing key: {key}"

    def test_validator_name_is_translation_gate(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        _, data, _ = _run(plan_dir, "core", tmp_path)
        assert data["validator"] == "translation_gate"

    def test_pass_field_echoes_arg(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={}))
        _, data, _ = _run(plan_dir, "feature-specs", tmp_path)
        assert data["pass"] == "feature-specs"


# ---------------------------------------------------------------------------
# --summary-out merge
# ---------------------------------------------------------------------------

class TestSummaryOut:
    def test_summary_out_written_on_pass(self, tmp_path):
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        summary_out = tmp_path / "validation-summary.json"
        _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        assert summary_out.is_file()
        summary = json.loads(summary_out.read_text())
        assert "translation_gate" in summary["validators"]

    def test_summary_out_written_on_fail(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        summary_out = tmp_path / "validation-summary.json"
        _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        assert summary_out.is_file()
        summary = json.loads(summary_out.read_text())
        assert summary["validators"]["translation_gate"]["status"] == "FAIL"

    def test_summary_overall_status_fail_when_gate_fails(self, tmp_path):
        plan_dir = _make_plan(tmp_path, state=_state(langs={"vi": {}}))
        summary_out = tmp_path / "validation-summary.json"
        _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        summary = json.loads(summary_out.read_text())
        # translation_gate critical issue → overall FAIL
        assert summary["overall_status"] == "FAIL"

    def test_summary_totals_not_inflated_on_pass(self, tmp_path):
        """[M2] A PASS verdict must NOT add to totals.critical/warning.

        The gate manually folds its own counts onto totals after
        recalculate_totals() (which only knows feature_existence + specs slots).
        This pins the invariant so a future _summary_lib change that starts
        auto-aggregating all validators cannot silently double-count.
        """
        # all-synced + fresh cursor → PASS with zero findings
        state = _state(langs={"vi": {"translated_from_sha": "abc123", "passes_translated": ["core"]}})
        plan_dir = _make_plan(
            tmp_path,
            state=state,
            report=_report("core", [{"lang": "vi", "status": "synced"}]),
        )
        summary_out = tmp_path / "validation-summary.json"
        rc, _, _ = _run(plan_dir, "core", tmp_path, extra_args=["--summary-out", str(summary_out)])
        assert rc == 0
        summary = json.loads(summary_out.read_text())
        assert summary["validators"]["translation_gate"]["status"] == "PASS"
        assert summary["totals"]["critical"] == 0
        assert summary["totals"]["warning"] == 0
        assert summary["overall_status"] != "FAIL"
