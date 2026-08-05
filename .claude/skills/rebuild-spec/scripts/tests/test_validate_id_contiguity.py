"""Tests for validate_id_contiguity.py.

Runs script as subprocess + parses stdout JSON.
Test matrix from phase-02 success criteria:
  - contiguous global → PASS, exit 0
  - global gap → critical contiguity.gap, exit 1
  - duplicate → critical contiguity.duplicate, exit 1
  - REG per-screen reset → PASS, exit 0
  - REG gap → WARNING, exit 0
  - DISC gap → WARNING, exit 0
  - overflow (US1000 or max==US999) → critical contiguity.overflow, exit 1
  - summary wiring: critical raises overall_status=FAIL, counted in totals
  - slot placement: validators["id_contiguity"], NOT inside validators["specs"]
  - empty file → PASS, exit 0
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "validate_id_contiguity.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_artifact(plan_dir: Path, artifact: str, content: str) -> Path:
    art_dir = plan_dir / "artifacts"
    art_dir.mkdir(parents=True, exist_ok=True)
    f = art_dir / f"{artifact}.md"
    f.write_text(content, encoding="utf-8")
    return f


def _run(plan_dir: Path, artifact: str, summary_out: Path | None = None,
         project_root: Path | None = None,
         report_only: bool = False) -> tuple[int, dict]:
    cmd = [
        sys.executable, str(SCRIPT),
        "--artifact", artifact,
        "--plan-dir", str(plan_dir),
        "--project-root", str(project_root or plan_dir.parent),
    ]
    if summary_out:
        cmd += ["--summary-out", str(summary_out)]
    if report_only:
        cmd += ["--report-only"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)
    return result.returncode, data


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in data.get("issues", [])]


def _severities(data: dict) -> list[str]:
    return [i["severity"] for i in data.get("issues", [])]


# ---------------------------------------------------------------------------
# Contiguous global → PASS, exit 0
# ---------------------------------------------------------------------------

class TestContiguousGlobalPass:
    def test_exit_code_zero(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 first\nUS002 second\nUS003 third\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 0

    def test_status_pass(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 first\nUS002 second\nUS003 third\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["status"] == "PASS"

    def test_no_issues(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 first\nUS002 second\nUS003 third\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["issues"] == []

    def test_output_has_required_keys(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\n")
        _, data = _run(tmp_path, "user-stories")
        for key in ("validator", "timestamp", "plan_dir", "status", "summary", "issues"):
            assert key in data


# ---------------------------------------------------------------------------
# Global gap → critical contiguity.gap, exit 1
# ---------------------------------------------------------------------------

class TestGlobalGap:
    def test_exit_code_one(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 1

    def test_status_fail(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["status"] == "FAIL"

    def test_gap_rule_id_present(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories")
        assert "contiguity.gap" in _rule_ids(data)

    def test_gap_message_names_missing_code(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories")
        gaps = [i for i in data["issues"] if i["rule_id"] == "contiguity.gap"]
        assert any("US002" in i["message"] for i in gaps)

    def test_gap_severity_critical(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories")
        gaps = [i for i in data["issues"] if i["rule_id"] == "contiguity.gap"]
        assert all(i["severity"] == "critical" for i in gaps)

    def test_critical_count_matches(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["summary"]["critical"] >= 1


# ---------------------------------------------------------------------------
# Duplicate → critical contiguity.duplicate, exit 1
# ---------------------------------------------------------------------------

class TestDuplicate:
    def test_exit_code_one(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "## US001 a\n## US002 b\n## US002 dup\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 1

    def test_duplicate_rule_id_present(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "## US001 a\n## US002 b\n## US002 dup\n")
        _, data = _run(tmp_path, "user-stories")
        assert "contiguity.duplicate" in _rule_ids(data)

    def test_duplicate_severity_critical(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "## US001 a\n## US002 b\n## US002 dup\n")
        _, data = _run(tmp_path, "user-stories")
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert all(i["severity"] == "critical" for i in dups)

    def test_status_fail(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "## US001 a\n## US002 b\n## US002 dup\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["status"] == "FAIL"


# ---------------------------------------------------------------------------
# REG per-screen reset → PASS (codes restart 001 for each SCR block)
# ---------------------------------------------------------------------------

class TestRegPerScreenReset:
    def test_exit_code_zero_when_reg_resets(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG002 | button |\n"
            "## SCR002_Dashboard\n"
            "| REG001 | header |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        code, _ = _run(tmp_path, "screen-list")
        assert code == 0

    def test_status_pass_when_reg_resets(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG002 | button |\n"
            "## SCR002_Dashboard\n"
            "| REG001 | header |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        assert data["status"] == "PASS"

    def test_no_reg_issues_when_reg_resets(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "## SCR002_Dashboard\n"
            "| REG001 | header |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        reg_issues = [i for i in data["issues"] if "REG" in i["message"]]
        assert reg_issues == []


# ---------------------------------------------------------------------------
# REG gap → WARNING, exit 0
# ---------------------------------------------------------------------------

class TestRegGap:
    def test_exit_code_zero_on_reg_gap(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG003 | extra |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        # SCR001 is the only owned scheme for screen-list; no global gap
        # But screen-list also owns SCR — we need a contiguous SCR to avoid false critical
        content_full = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG003 | extra |\n"
        )
        _write_artifact(tmp_path, "screen-list", content_full)
        code, _ = _run(tmp_path, "screen-list")
        assert code == 0

    def test_status_warn_on_reg_gap(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG003 | extra |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        assert data["status"] == "WARN"

    def test_gap_rule_id_in_reg_block(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG003 | extra |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        assert "contiguity.gap" in _rule_ids(data)

    def test_reg_gap_severity_warning(self, tmp_path):
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG003 | extra |\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        reg_gaps = [i for i in data["issues"]
                    if i["rule_id"] == "contiguity.gap" and i["severity"] == "warning"]
        assert len(reg_gaps) >= 1

    def test_reg_token_in_code_fence_ignored(self, tmp_path):
        # REG token quoted inside a non-mermaid code fence must not create a
        # false gap warning (F10 fence scoping applies to the per-screen check).
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "| REG002 | button |\n"
            "```python\n"
            "# renders REG004 region\n"
            "```\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        code, data = _run(tmp_path, "screen-list")
        assert code == 0
        assert "contiguity.gap" not in _rule_ids(data)

    def test_reg_token_in_mermaid_fence_counted(self, tmp_path):
        # Mermaid fences ARE in scope: a REG gap visible only in mermaid still warns.
        content = (
            "## SCR001_Login\n"
            "| REG001 | form |\n"
            "```mermaid\n"
            "flowchart TD\n"
            "  A[REG003 panel]\n"
            "```\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        _, data = _run(tmp_path, "screen-list")
        assert "contiguity.gap" in _rule_ids(data)


# ---------------------------------------------------------------------------
# DISC gap → WARNING, exit 0
# ---------------------------------------------------------------------------

class TestDiscGap:
    def test_disc_gap_is_warning(self, tmp_path):
        _write_artifact(tmp_path, "data-model", "DISC-001 entity\nDISC-003 other\n")
        _, data = _run(tmp_path, "data-model")
        disc_gaps = [i for i in data["issues"]
                     if i["rule_id"] == "contiguity.gap" and "DISC" in i["message"]]
        assert disc_gaps
        assert all(i["severity"] == "warning" for i in disc_gaps)

    def test_disc_gap_exit_zero(self, tmp_path):
        _write_artifact(tmp_path, "data-model", "DISC-001 entity\nDISC-003 other\n")
        code, _ = _run(tmp_path, "data-model")
        assert code == 0

    def test_disc_gap_status_warn(self, tmp_path):
        _write_artifact(tmp_path, "data-model", "DISC-001 entity\nDISC-003 other\n")
        _, data = _run(tmp_path, "data-model")
        assert data["status"] == "WARN"

    def test_disc_gap_message_names_missing_code(self, tmp_path):
        _write_artifact(tmp_path, "data-model", "DISC-001 entity\nDISC-003 other\n")
        _, data = _run(tmp_path, "data-model")
        gaps = [i for i in data["issues"] if i["rule_id"] == "contiguity.gap"]
        assert any("DISC-002" in i["message"] for i in gaps)


# ---------------------------------------------------------------------------
# Overflow: 4+-digit token (US1000) → critical, exit 1
# ---------------------------------------------------------------------------

class TestOverflowFourDigit:
    def test_overflow_four_digit_exit_one(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS1000 overflow\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 1

    def test_overflow_four_digit_rule_id(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS1000 overflow\n")
        _, data = _run(tmp_path, "user-stories")
        assert "contiguity.overflow" in _rule_ids(data)

    def test_overflow_four_digit_severity_critical(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS1000 overflow\n")
        _, data = _run(tmp_path, "user-stories")
        overflow = [i for i in data["issues"] if i["rule_id"] == "contiguity.overflow"]
        assert all(i["severity"] == "critical" for i in overflow)

    def test_overflow_four_digit_status_fail(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS1000 overflow\n")
        _, data = _run(tmp_path, "user-stories")
        assert data["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Overflow: max 3-digit == 999 → critical, exit 1
# ---------------------------------------------------------------------------

class TestOverflowMaxNine99:
    def test_overflow_at_999_ceiling_exit_one(self, tmp_path):
        # Build US001..US999 — too large to write all; just use US999 alone
        _write_artifact(tmp_path, "user-stories", "US999 ceiling\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 1

    def test_overflow_at_999_ceiling_rule_id(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US999 ceiling\n")
        _, data = _run(tmp_path, "user-stories")
        assert "contiguity.overflow" in _rule_ids(data)

    def test_overflow_at_999_ceiling_severity_critical(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US999 ceiling\n")
        _, data = _run(tmp_path, "user-stories")
        overflow = [i for i in data["issues"] if i["rule_id"] == "contiguity.overflow"]
        assert all(i["severity"] == "critical" for i in overflow)


# ---------------------------------------------------------------------------
# Empty file → PASS, exit 0
# ---------------------------------------------------------------------------

class TestEmptyFile:
    def test_empty_file_exit_zero(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 0

    def test_empty_file_status_pass(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "")
        _, data = _run(tmp_path, "user-stories")
        assert data["status"] == "PASS"

    def test_missing_artifact_file_exit_zero(self, tmp_path):
        # No artifact file at all — vacuous PASS
        (tmp_path / "artifacts").mkdir(parents=True, exist_ok=True)
        code, _ = _run(tmp_path, "user-stories")
        assert code == 0

    def test_no_codes_exit_zero(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "# Header\nSome prose with no IDs.\n")
        code, _ = _run(tmp_path, "user-stories")
        assert code == 0


# ---------------------------------------------------------------------------
# Summary wiring: slot lands at validators["id_contiguity"], NOT in specs;
# criticals raise overall_status=FAIL and are counted in totals.
# ---------------------------------------------------------------------------

class TestSummaryWiring:
    def test_slot_at_top_level_validators_not_in_specs(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        # slot must be a direct child of validators
        assert "id_contiguity" in summary["validators"]
        # must NOT be nested inside specs sub-dict
        specs = summary["validators"].get("specs", {})
        assert "id_contiguity" not in specs

    def test_critical_raises_overall_status_to_fail(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        assert summary["overall_status"] == "FAIL"

    def test_criticals_counted_in_totals(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        assert summary["totals"]["critical"] >= 1

    def test_slot_status_matches_result_status(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _, result = _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        slot = summary["validators"]["id_contiguity"]
        assert slot["status"] == result["status"]

    def test_pass_result_does_not_raise_overall_status(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS002 b\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        assert summary["overall_status"] == "PASS"

    def test_slot_issues_list_populated(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "user-stories", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        slot = summary["validators"]["id_contiguity"]
        assert len(slot["issues"]) >= 1

    def test_summary_out_creates_file(self, tmp_path):
        _write_artifact(tmp_path, "user-stories", "US001 a\n")
        summary_file = tmp_path / "validation-summary.json"
        assert not summary_file.exists()
        _run(tmp_path, "user-stories", summary_out=summary_file)
        assert summary_file.exists()

    def test_warning_slot_does_not_flip_overall_to_fail(self, tmp_path):
        # DISC gap = warning; overall should stay PASS (no criticals)
        _write_artifact(tmp_path, "data-model", "DISC-001 a\nDISC-003 c\n")
        summary_file = tmp_path / "validation-summary.json"
        _run(tmp_path, "data-model", summary_out=summary_file)
        summary = json.loads(summary_file.read_text())
        assert summary["overall_status"] in ("WARN", "PASS")
        assert summary["overall_status"] != "FAIL"


# ---------------------------------------------------------------------------
# --report-only: gap → warning severity, status never FAIL, exit always 0
# ---------------------------------------------------------------------------

class TestReportOnly:
    def test_report_only_gap_exit_zero(self, tmp_path):
        """A contiguity gap that would normally FAIL exits 0 in --report-only."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        code, _ = _run(tmp_path, "user-stories", report_only=True)
        assert code == 0

    def test_report_only_gap_status_not_fail(self, tmp_path):
        """Status must never be FAIL in --report-only, even with a critical gap."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories", report_only=True)
        assert data["status"] != "FAIL"

    def test_report_only_gap_severity_downgraded_to_warning(self, tmp_path):
        """Critical gap is downgraded to warning severity under --report-only."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories", report_only=True)
        # All issues must be warnings (no criticals)
        for issue in data["issues"]:
            assert issue["severity"] == "warning", f"Expected warning, got {issue['severity']}: {issue}"

    def test_report_only_gap_no_criticals_in_summary(self, tmp_path):
        """summary.critical must be 0 in --report-only mode."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories", report_only=True)
        assert data["summary"]["critical"] == 0

    def test_report_only_gap_warning_count_positive(self, tmp_path):
        """summary.warning must be > 0 when there is a gap."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS003 c\n")
        _, data = _run(tmp_path, "user-stories", report_only=True)
        assert data["summary"]["warning"] >= 1

    def test_report_only_pass_still_exits_zero(self, tmp_path):
        """A contiguous artifact under --report-only also exits 0 (vacuous PASS)."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS002 b\n")
        code, data = _run(tmp_path, "user-stories", report_only=True)
        assert code == 0
        assert data["status"] == "PASS"

    def test_report_only_duplicate_also_downgraded(self, tmp_path):
        """Duplicate (critical) is downgraded to warning under --report-only."""
        _write_artifact(tmp_path, "user-stories", "## US001 a\n## US002 b\n## US002 dup\n")
        code, data = _run(tmp_path, "user-stories", report_only=True)
        assert code == 0
        assert data["status"] != "FAIL"
        for issue in data["issues"]:
            assert issue["severity"] == "warning"

    def test_report_only_overflow_also_downgraded(self, tmp_path):
        """Overflow (critical) is downgraded to warning under --report-only."""
        _write_artifact(tmp_path, "user-stories", "US001 a\nUS1000 overflow\n")
        code, data = _run(tmp_path, "user-stories", report_only=True)
        assert code == 0
        assert data["status"] != "FAIL"


# ---------------------------------------------------------------------------
# Error path: plan-dir is a file → exit 2
# ---------------------------------------------------------------------------

class TestPlanDirIsFile:
    def test_exit_code_two_when_plan_dir_is_file(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("hi")
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--artifact", "user-stories",
             "--plan-dir", str(bogus),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Phase-04 edge-case regression tests
# ---------------------------------------------------------------------------

class TestW8DeletionGap:
    """W8 fix deletes a dup SCR### → post-W8 --report-only re-check surfaces WARNING (non-halting, F9).

    Simulates the scenario where W8 removes a duplicate SCR### entry from screen-list,
    leaving a gap in the sequence. The contiguity validator in --report-only mode must
    surface a WARNING (exit 0) rather than a critical failure, since the renumber gate
    has not yet run on the W8-fixed artifact.
    """

    def test_w8_deletion_gap_surfaces_warning_in_report_only(self, tmp_path):
        """After W8 removes a dup, --report-only contiguity check exits 0 with a warning."""
        # Simulate post-W8 screen-list: SCR002 was a duplicate and was deleted,
        # leaving a gap between SCR001 and SCR003.
        _write_artifact(tmp_path, "screen-list", "SCR001_Login\nSCR003_Dashboard\n")
        code, data = _run(tmp_path, "screen-list", report_only=True)
        assert code == 0, f"--report-only must exit 0 even with a gap, got {code}"

    def test_w8_deletion_gap_status_not_fail_in_report_only(self, tmp_path):
        """--report-only status must not be FAIL even when a gap exists."""
        _write_artifact(tmp_path, "screen-list", "SCR001_Login\nSCR003_Dashboard\n")
        _, data = _run(tmp_path, "screen-list", report_only=True)
        assert data["status"] != "FAIL"

    def test_w8_deletion_gap_severity_warning_not_critical(self, tmp_path):
        """Issues reported in --report-only must be warnings, not critical."""
        _write_artifact(tmp_path, "screen-list", "SCR001_Login\nSCR003_Dashboard\n")
        _, data = _run(tmp_path, "screen-list", report_only=True)
        for issue in data.get("issues", []):
            assert issue["severity"] == "warning", (
                f"Expected warning severity in report-only, got {issue['severity']}: {issue}"
            )

    def test_w8_deletion_gap_warning_count_nonzero(self, tmp_path):
        """The warning count in summary must be > 0 when a gap is present."""
        _write_artifact(tmp_path, "screen-list", "SCR001_Login\nSCR003_Dashboard\n")
        _, data = _run(tmp_path, "screen-list", report_only=True)
        assert data["summary"]["warning"] >= 1

    def test_w8_deletion_gap_full_mode_still_critical(self, tmp_path):
        """Without --report-only, the same gap IS a critical failure (exit 1)."""
        _write_artifact(tmp_path, "screen-list", "SCR001_Login\nSCR003_Dashboard\n")
        code, data = _run(tmp_path, "screen-list", report_only=False)
        assert code == 1
        assert data["status"] == "FAIL"


# ---------------------------------------------------------------------------
# FIX H1: Fence-unaware duplicate detection → false CRITICAL
# ---------------------------------------------------------------------------

class TestFenceAwareDuplication:
    """Validator must scope duplicate/gap/overflow checks to prose+mermaid only."""

    def test_token_only_in_code_fence_no_gap(self, tmp_path):
        """A token appearing ONLY inside a python fence must not create a gap/extra code."""
        # US001 in prose, US002 only in python fence — validator should see only US001 in prose
        content = (
            "US001 prose entry\n"
            "```python\n"
            "# Implements US002\n"
            "def foo():\n"
            "    pass\n"
            "```\n"
        )
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        # US001 alone is contiguous (no gap), PASS
        assert code == 0
        assert data["status"] == "PASS"
        assert data["issues"] == []

    def test_token_in_prose_and_code_fence_no_duplicate(self, tmp_path):
        """US001 in prose + US001 in python fence + US002 in prose → PASS, no duplicate."""
        content = (
            "US001 prose entry\n"
            "```python\n"
            "# Implements US001\n"
            "```\n"
            "US002 second entry\n"
        )
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        assert code == 0
        assert data["status"] == "PASS"
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert dups == [], f"No duplicate issues expected, got: {dups}"

    def test_real_duplicate_in_prose_still_critical(self, tmp_path):
        """US001 defined twice on heading lines (no fence) → still a critical duplicate."""
        content = "## US001 first\n## US001 second\n## US002 third\n"
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        assert code == 1
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert len(dups) >= 1

    def test_heading_defined_with_many_refs_not_duplicate(self, tmp_path):
        """Heading-defined code: one heading + many table/cross-ref mentions → NOT a duplicate.

        Hybrid rule: when a code appears as a heading at all, duplicate count is judged by
        HEADING occurrences only; index-table rows and cross-references are ignored.
        """
        content = (
            "| US001 | summary row |\n"
            "## US001 The definition\n"
            "Dependencies: US001, US002\n"
            "## US002 Second\n"
            "See also US001 above.\n"
        )
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert dups == [], f"No duplicate expected (US001 has one heading), got: {dups}"
        assert code == 0

    def test_table_defined_scheme_duplicate_via_fallback(self, tmp_path):
        """Table-defined scheme (no headings at all) → fall back to prose counting.

        A code never appearing as a heading is judged by total prose occurrences, so a
        genuine duplicate table row is still caught (route-list / crud-matrix style).
        """
        content = "| US001 | a |\n| US001 | dup row |\n| US002 | b |\n"
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert len(dups) >= 1, "Duplicate table row must still be caught via prose fallback"
        assert code == 1

    def test_token_in_mermaid_fence_counts(self, tmp_path):
        """US001 in mermaid fence + US002 in prose → both counted (mermaid is rewritten scope)."""
        content = (
            "```mermaid\n"
            "graph TD\n"
            "    A[US001_Login]\n"
            "```\n"
            "US002 prose\n"
        )
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        # US001 (mermaid) + US002 (prose) → contiguous 001..002 → PASS
        assert code == 0
        assert data["status"] == "PASS"

    def test_code_fence_only_token_no_overflow(self, tmp_path):
        """US999 appearing ONLY in a code fence must not trigger overflow critical."""
        content = (
            "US001 normal\n"
            "```python\n"
            "# reference: US999\n"
            "```\n"
        )
        _write_artifact(tmp_path, "user-stories", content)
        code, data = _run(tmp_path, "user-stories")
        # Only US001 visible in prose scope → contiguous → PASS
        assert code == 0
        overflow = [i for i in data["issues"] if i["rule_id"] == "contiguity.overflow"]
        assert overflow == []


# ---------------------------------------------------------------------------
# FIX A3: prose+mermaid same-ID false duplicate
# ---------------------------------------------------------------------------

class TestProseMermaidFalseDuplicate:
    """A3 repro: same ID in prose heading AND mermaid edge is ONE logical occurrence."""

    def test_scr_in_prose_and_mermaid_edge_pass(self, tmp_path):
        """A3 repro: SCR001 in prose heading + mermaid node → PASS, not duplicate."""
        content = (
            "## SCR001_Login\n"
            "Desc.\n"
            "```mermaid\n"
            "graph TD\n"
            "    A[SCR001_Login] --> B[SCR002_Dashboard]\n"
            "```\n"
            "## SCR002_Dashboard\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        code, data = _run(tmp_path, "screen-list")
        assert code == 0, f"Expected exit 0, got {code}. Issues: {data['issues']}"
        assert data["status"] == "PASS"
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert dups == [], f"False duplicate fired: {dups}"

    def test_id_repeated_only_in_mermaid_edges_not_duplicate(self, tmp_path):
        """SCR001 as source of multiple mermaid edges → NOT a duplicate (reference, not definition)."""
        content = (
            "## SCR001_Login\n"
            "Desc.\n"
            "## SCR002_Dashboard\n"
            "Desc.\n"
            "## SCR003_Settings\n"
            "Desc.\n"
            "```mermaid\n"
            "graph TD\n"
            "    SCR001 --> SCR002\n"
            "    SCR001 --> SCR003\n"
            "```\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        code, data = _run(tmp_path, "screen-list")
        assert code == 0, f"Expected exit 0, got {code}. Issues: {data['issues']}"
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert dups == [], f"Mermaid-only repeat falsely flagged as duplicate: {dups}"

    def test_two_prose_headings_same_id_still_critical(self, tmp_path):
        """Two prose headings with the same SCR### → real duplicate, CRITICAL (existing behavior preserved)."""
        content = (
            "## SCR001_Login\n"
            "First definition.\n"
            "## SCR001_AnotherPage\n"
            "Duplicate definition.\n"
            "## SCR002_Dashboard\n"
            "Other screen.\n"
        )
        _write_artifact(tmp_path, "screen-list", content)
        code, data = _run(tmp_path, "screen-list")
        assert code == 1, f"Expected exit 1 for genuine duplicate, got {code}"
        dups = [i for i in data["issues"] if i["rule_id"] == "contiguity.duplicate"]
        assert len(dups) >= 1, "Genuine prose duplicate must still fire"
        assert all(i["severity"] == "critical" for i in dups)


# ---------------------------------------------------------------------------
# FIX C1: process-flows multi-file validator
# ---------------------------------------------------------------------------

class TestProcessFlowsMultiFileValidator:
    """validate_id_contiguity with --artifact process-flows reads flows/*.md."""

    def _write_flows(self, plan_dir: Path, files: dict[str, str]) -> None:
        flows_dir = plan_dir / "artifacts" / "flows"
        flows_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (flows_dir / name).write_text(content, encoding="utf-8")

    def test_cross_file_gap_surfaces_critical(self, tmp_path):
        """FLOW001,FLOW003 in a.md + FLOW005 in b.md → gap → FAIL, exit 1."""
        (tmp_path / "artifacts").mkdir(parents=True, exist_ok=True)
        self._write_flows(tmp_path, {
            "a.md": "FLOW001 first\nFLOW003 second\n",
            "b.md": "FLOW005 third\n",
        })
        code, data = _run(tmp_path, "process-flows")
        assert code == 1
        assert data["status"] == "FAIL"
        gaps = [i for i in data["issues"] if i["rule_id"] == "contiguity.gap"]
        assert len(gaps) >= 1

    def test_contiguous_across_files_pass(self, tmp_path):
        """FLOW001 in a.md + FLOW002 in b.md → contiguous → PASS."""
        (tmp_path / "artifacts").mkdir(parents=True, exist_ok=True)
        self._write_flows(tmp_path, {
            "a.md": "FLOW001 first\n",
            "b.md": "FLOW002 second\n",
        })
        code, data = _run(tmp_path, "process-flows")
        assert code == 0
        assert data["status"] == "PASS"

    def test_empty_flows_dir_vacuous_pass(self, tmp_path):
        """Empty artifacts/flows/ → vacuous PASS, exit 0."""
        (tmp_path / "artifacts" / "flows").mkdir(parents=True)
        code, data = _run(tmp_path, "process-flows")
        assert code == 0
        assert data["status"] == "PASS"

    def test_missing_flows_dir_vacuous_pass(self, tmp_path):
        """Missing artifacts/flows/ entirely → vacuous PASS, exit 0."""
        (tmp_path / "artifacts").mkdir(parents=True, exist_ok=True)
        code, data = _run(tmp_path, "process-flows")
        assert code == 0
        assert data["status"] == "PASS"

