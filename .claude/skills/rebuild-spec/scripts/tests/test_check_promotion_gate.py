"""Tests for check_promotion_gate.py — W9 promotion gate.
Runs script as subprocess with --plan-dir, parses stdout JSON,
asserts gate pass/fail per fixture and tmp_path scenarios.
"""
import json
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "check_promotion_gate.py"


def _run(plan_dir: Path, project_root: Path = REPO_ROOT) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--plan-dir", str(plan_dir),
         "--project-root", str(project_root)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in data.get("issues", [])]


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in data.get("issues", []) if i["severity"] == "critical"]


def _make_complete_plan(tmp_path: Path) -> Path:
    """Create a valid 4-file plan dir under tmp_path."""
    plan_dir = tmp_path / "my-plan"
    feat_dir = plan_dir / "artifacts" / "features" / "F001_Auth"
    feat_dir.mkdir(parents=True)

    (plan_dir / "artifacts" / "_canonical-fcodes.json").write_text(json.dumps({
        "features": [{"fcode": "F001", "slug": "F001_Auth", "name": "Auth", "priority": "P0", "type": "ui"}]
    }), encoding="utf-8")

    (feat_dir / "technical-spec.md").write_text("# F001_Auth\n\n## Overview\nAuth.\n", encoding="utf-8")
    (feat_dir / "business-context.md").write_text(
        "## Why It Matters\nCore feature.\n\n## Who Uses It\nUsers.\n\n## What They Do\nSign in.\n",
        encoding="utf-8",
    )
    (feat_dir / "screens.md").write_text(
        "## Screen List\n| Screen | Route | Purpose |\n|--------|-------|------|\n| Login | /login | Sign in |\n\n"
        "## User Journey\nNavigate to login.\n",
        encoding="utf-8",
    )
    (feat_dir / "edge-cases.md").write_text(
        "## Edge Cases\n| Scenario | Expected Behavior |\n|----------|-------------------|\n| Empty input | Show error |\n",
        encoding="utf-8",
    )
    return plan_dir


# ---------------------------------------------------------------------------
# Complete 4-file plan: all files present, no .pending → gate PASS
# ---------------------------------------------------------------------------

class TestGatePass:
    def test_exit_code_zero(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        code, _ = _run(plan_dir, tmp_path)
        assert code == 0

    def test_status_pass(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        _, data = _run(plan_dir, tmp_path)
        assert data["status"] == "PASS"

    def test_no_critical_issues(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        _, data = _run(plan_dir, tmp_path)
        assert data["summary"]["critical"] == 0

    def test_output_has_required_keys(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        _, data = _run(plan_dir, tmp_path)
        for key in ("validator", "timestamp", "plan_dir", "status", "summary", "issues"):
            assert key in data

    def test_validator_name(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        _, data = _run(plan_dir, tmp_path)
        assert data["validator"] == "promotion_gate"


# ---------------------------------------------------------------------------
# F1/F15 regression: test-cases.md (v26.1.0 B6 sidecar) is NEVER gated
# ---------------------------------------------------------------------------

class TestTestCasesSidecarNotGated:
    """test-cases.md is a 5th, optional file — its presence/absence must never
    change the promotion gate's PASS/FAIL verdict (it is not in FEATURE_FILES)."""

    def test_gate_passes_with_test_cases_present(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / "test-cases.md").write_text(
            "# Test Cases\n", encoding="utf-8"
        )
        code, data = _run(plan_dir, tmp_path)
        assert code == 0
        assert data["status"] == "PASS"
        assert data["summary"]["critical"] == 0

    def test_gate_passes_with_test_cases_absent(self, tmp_path):
        """Same 4-file plan, no test-cases.md at all — still PASS (sidecar, not mandatory)."""
        plan_dir = _make_complete_plan(tmp_path)
        assert not (plan_dir / "artifacts" / "features" / "F001_Auth" / "test-cases.md").exists()
        code, data = _run(plan_dir, tmp_path)
        assert code == 0
        assert data["status"] == "PASS"

    def test_no_files_incomplete_rule_fires_for_test_cases(self, tmp_path):
        """Removing test-cases.md (when never present) must not trigger gate.files_incomplete —
        that rule is scoped to FEATURE_FILES only, which test-cases.md is not part of."""
        plan_dir = _make_complete_plan(tmp_path)
        _, data = _run(plan_dir, tmp_path)
        assert "gate.files_incomplete" not in _rule_ids(data)


# ---------------------------------------------------------------------------
# 3-of-4 files: edge-cases.md missing → gate FAIL (gate.files_incomplete)
# ---------------------------------------------------------------------------

class TestGateFilesIncomplete:
    def test_exit_code_one(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / "edge-cases.md").unlink()
        code, _ = _run(plan_dir, tmp_path)
        assert code == 1

    def test_status_fail(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / "edge-cases.md").unlink()
        _, data = _run(plan_dir, tmp_path)
        assert data["status"] == "FAIL"

    def test_files_incomplete_rule_id(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / "edge-cases.md").unlink()
        _, data = _run(plan_dir, tmp_path)
        assert "gate.files_incomplete" in _critical_rule_ids(data)

    def test_message_mentions_missing_file(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / "edge-cases.md").unlink()
        _, data = _run(plan_dir, tmp_path)
        incomplete = [i for i in data["issues"] if i["rule_id"] == "gate.files_incomplete"]
        assert any("edge-cases.md" in i["message"] for i in incomplete)


# ---------------------------------------------------------------------------
# .pending marker present → gate FAIL (gate.pending_marker)
# ---------------------------------------------------------------------------

class TestGatePendingMarker:
    def test_pending_marker_causes_fail(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        (plan_dir / "artifacts" / "features" / "F001_Auth" / ".pending").write_text("")
        code, data = _run(plan_dir, tmp_path)
        assert code == 1
        assert "gate.pending_marker" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# validation-summary.json with overall_status=FAIL → gate WARN
# ---------------------------------------------------------------------------

class TestGateValidationSummaryFail:
    def test_fail_summary_produces_warning(self, tmp_path):
        plan_dir = _make_complete_plan(tmp_path)
        summary = {"overall_status": "FAIL", "validators": {}}
        (plan_dir / "artifacts" / "validation-summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
        _, data = _run(plan_dir, tmp_path)
        assert "gate.validation_summary" in _rule_ids(data)


# ---------------------------------------------------------------------------
# --plan-dir is a file → exit 2
# ---------------------------------------------------------------------------

class TestGateInputGuard:
    def test_plan_dir_is_file_exits_two(self, tmp_path):
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
