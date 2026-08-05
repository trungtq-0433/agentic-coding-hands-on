"""Integration tests for validate_feature_existence.py.
Runs script as subprocess, parses stdout JSON, asserts structure + rule_ids.
Coverage per phase-05 test matrix: plan-good, plan-missing-folder,
plan-orphan-folder, plan-legacy-no-canonical.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "validate_feature_existence.py"


def _run(plan_dir: Path) -> tuple[int, dict]:
    """Run the validator and return (exit_code, parsed_json_output)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--plan-dir", str(plan_dir),
         "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in data.get("issues", [])]


# ---------------------------------------------------------------------------
# plan-good: all folders present, no orphans, canonical JSON present
# ---------------------------------------------------------------------------

class TestPlanGood:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "plan-good")
        assert code == 0

    def test_status_pass(self):
        _, data = _run(FIXTURES / "plan-good")
        assert data["status"] == "PASS"

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "plan-good")
        assert data["summary"]["critical"] == 0

    def test_no_warning_issues(self):
        _, data = _run(FIXTURES / "plan-good")
        assert data["summary"]["warning"] == 0

    def test_output_has_required_keys(self):
        _, data = _run(FIXTURES / "plan-good")
        for key in ("validator", "timestamp", "plan_dir", "status", "summary", "issues"):
            assert key in data


# ---------------------------------------------------------------------------
# plan-missing-folder: F002_Search declared but folder absent
# ---------------------------------------------------------------------------

class TestPlanMissingFolder:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "plan-missing-folder")
        assert code == 1

    def test_status_fail(self):
        _, data = _run(FIXTURES / "plan-missing-folder")
        assert data["status"] == "FAIL"

    def test_has_folder_missing_issue(self):
        _, data = _run(FIXTURES / "plan-missing-folder")
        assert "existence.folder_missing" in _rule_ids(data)

    def test_critical_count_at_least_one(self):
        _, data = _run(FIXTURES / "plan-missing-folder")
        assert data["summary"]["critical"] >= 1

    def test_missing_folder_message_mentions_f002(self):
        _, data = _run(FIXTURES / "plan-missing-folder")
        folder_missing = [i for i in data["issues"] if i["rule_id"] == "existence.folder_missing"]
        assert any("F002" in i["message"] for i in folder_missing)


# ---------------------------------------------------------------------------
# plan-orphan-folder: F001 declared+present, F999 folder has no canonical entry
# ---------------------------------------------------------------------------

class TestPlanOrphanFolder:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "plan-orphan-folder")
        assert code == 0

    def test_status_warn(self):
        _, data = _run(FIXTURES / "plan-orphan-folder")
        assert data["status"] == "WARN"

    def test_has_orphan_folder_warning(self):
        _, data = _run(FIXTURES / "plan-orphan-folder")
        assert "existence.orphan_folder" in _rule_ids(data)

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "plan-orphan-folder")
        assert data["summary"]["critical"] == 0

    def test_warning_count_at_least_one(self):
        _, data = _run(FIXTURES / "plan-orphan-folder")
        assert data["summary"]["warning"] >= 1

    def test_orphan_message_mentions_f999(self):
        _, data = _run(FIXTURES / "plan-orphan-folder")
        orphans = [i for i in data["issues"] if i["rule_id"] == "existence.orphan_folder"]
        assert any("F999" in i["location"]["file"] for i in orphans)


# ---------------------------------------------------------------------------
# plan-legacy-no-canonical: no _canonical-fcodes.json, falls back to feature-list
# ---------------------------------------------------------------------------

class TestPlanLegacyNoCanonical:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "plan-legacy-no-canonical")
        assert code == 0

    def test_status_warn(self):
        _, data = _run(FIXTURES / "plan-legacy-no-canonical")
        assert data["status"] == "WARN"

    def test_has_canonical_missing_warning(self):
        _, data = _run(FIXTURES / "plan-legacy-no-canonical")
        assert "existence.canonical_missing" in _rule_ids(data)

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "plan-legacy-no-canonical")
        assert data["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Regression for stage-3 finding F2: --plan-dir pointing at a file
# previously slipped through assert_under and returned exit 0 / status WARN
# with empty features; orchestrator misread that as PASS. Must return exit 2.
# ---------------------------------------------------------------------------

class TestPlanDirIsFile:
    def test_exit_code_two_when_plan_dir_is_file(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("hi")
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--plan-dir", str(bogus),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()


# ---------------------------------------------------------------------------
# plan-incomplete: F001_Auth folder has only 3 of 4 files (no edge-cases.md)
# and no .pending marker → must report existence.folder_incomplete CRITICAL.
# ---------------------------------------------------------------------------

class TestPlanIncomplete:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "plan-incomplete")
        assert code == 1

    def test_status_fail(self):
        _, data = _run(FIXTURES / "plan-incomplete")
        assert data["status"] == "FAIL"

    def test_has_folder_incomplete_issue(self):
        _, data = _run(FIXTURES / "plan-incomplete")
        assert "existence.folder_incomplete" in _rule_ids(data)

    def test_incomplete_message_mentions_missing_file(self):
        _, data = _run(FIXTURES / "plan-incomplete")
        incomplete = [i for i in data["issues"] if i["rule_id"] == "existence.folder_incomplete"]
        assert any("edge-cases.md" in i["message"] for i in incomplete)
