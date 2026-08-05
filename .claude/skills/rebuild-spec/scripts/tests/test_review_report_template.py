"""Snapshot test: review-report-template.md ## Passed Checks block format.

Also contains H1 regression tests for _review_report_lib.mutate_review_report.
"""
import sys
import tempfile
import os
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
TEMPLATE = TEMPLATES_DIR / "review-report-template.md"

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _review_report_lib import mutate_review_report  # noqa: E402


class TestPassedChecksFormat:
    def _content(self) -> str:
        return TEMPLATE.read_text(encoding="utf-8")

    def test_template_file_exists(self):
        assert TEMPLATE.is_file(), f"template not found: {TEMPLATE}"

    def test_passed_checks_section_present(self):
        content = self._content()
        assert "## Passed Checks" in content

    def test_one_liner_instruction_present(self):
        content = self._content()
        assert "ONE LINE per passed rule" in content

    def test_no_evidence_prose_instruction(self):
        content = self._content()
        assert "NO evidence prose" in content

    def test_pattern_line_present(self):
        """Template must show the ✓ <rule_id> @ <fcode> pattern."""
        content = self._content()
        assert "✓" in content
        assert "<rule_id>" in content
        assert "<fcode>" in content

    def test_no_multi_line_entries_instruction(self):
        content = self._content()
        assert "NO multi-line" in content


class TestMutateReviewReportPassGuard:
    """H1 regression — PASS must NOT be set when missing > 0, even if failed reaches 0."""

    def _atomic_write(self, path: Path, text: str) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            os.replace(tmp, str(path))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _make_report(self, tmp_path: Path, failed: int, missing: int, result: str) -> Path:
        content = (
            f"---\n"
            f"failed: {failed}\n"
            f"missing: {missing}\n"
            f"result: {result}\n"
            f"---\n"
            f"\n"
            f"## Critical Issues\n"
            f"\n"
            f"### Missing Linked FR in BR-001\n"
            f"- Description: block missing Linked FR line.\n"
        )
        path = tmp_path / "review-report.md"
        path.write_text(content, encoding="utf-8")
        return path

    def test_pass_not_set_when_missing_nonzero(self, tmp_path):
        """failed decrements to 0 but missing=3 — result must NOT become PASS."""
        import re
        report_path = self._make_report(tmp_path, failed=1, missing=3, result="NEEDS_FIX")

        mutate_review_report(report_path, blocks_fixed=1, atomic_write_fn=self._atomic_write)

        content = report_path.read_text(encoding="utf-8")

        # failed: must have been decremented (the decrement still works)
        fm = re.search(r"^failed:\s*(\d+)", content, re.MULTILINE)
        assert fm is not None
        assert int(fm.group(1)) == 0, "failed should have been decremented to 0"

        # result: must NOT be PASS because missing > 0
        res = re.search(r"^result:\s*(\S+)", content, re.MULTILINE)
        assert res is not None
        assert res.group(1) != "PASS", (
            "result must not be set to PASS when missing > 0"
        )

    def test_pass_set_when_both_zero(self, tmp_path):
        """Confirm PASS IS set when both failed and missing reach 0 (guard against over-correction)."""
        import re
        report_path = self._make_report(tmp_path, failed=1, missing=0, result="NEEDS_FIX")

        mutate_review_report(report_path, blocks_fixed=1, atomic_write_fn=self._atomic_write)

        content = report_path.read_text(encoding="utf-8")

        res = re.search(r"^result:\s*(\S+)", content, re.MULTILINE)
        assert res is not None
        assert res.group(1) == "PASS", "result should be PASS when both failed and missing are 0"
