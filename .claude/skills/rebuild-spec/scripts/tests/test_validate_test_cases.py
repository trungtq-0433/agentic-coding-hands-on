"""Tests for validate_test_cases.py (Wave TC.2 gate).

Coverage: TC### regex + per-feature uniqueness, Type in {UT,IT,UAT}, Traces-to
presence + citation-source-family match (UT/IT vs UAT split), coverage-gap WARN
cross-ref against technical-spec.md, missing-file (sidecar) warning, CLI exit
codes + summary merge. Also: sidecar-not-gated regression (test-cases.md must
NOT be part of FEATURE_FILES / the promotion gate) — F1/F15 guardrail.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_test_cases import validate, main  # noqa: E402
from _slug_lib import FEATURE_FILES  # noqa: E402

VALID_TEST_CASES = """\
# Test Cases — F001_Login

## Test Cases

| Test-ID | Type (UT|IT|UAT) | Given | When | Then | Traces-to |
|---------|---------------------|-------|------|------|-----------|
| TC001 | UT | invalid password | user submits login form | error shown | `BR-001` |
| TC002 | IT | valid credentials | user submits login form | session created | `app/auth/session.rb:22` |
| TC003 | UAT | user on login page | user enters valid credentials and submits | dashboard is shown | screens.md § User Journey step 2 |

## Coverage Notes

- `SM-001` — [NO_TEST_CASE] pure internal state, nothing user-observable to assert.
"""

TECH_SPEC_WITH_CODES = """\
# F001_Login

## Cross-Cutting Logic

### Business Rules

### BR-001_PasswordRequired

Password is required.

### SM-001_SessionState

State machine.
"""


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestValidate:
    def test_valid_test_cases_passes(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["severity"] == "critical" for i in issues), issues
        assert not any(i["rule_id"] == "TestCases.coverage_gap" for i in issues)

    def test_missing_file_is_warning_not_critical(self, tmp_path):
        (tmp_path / "plans/p1/artifacts/features/F002_Empty").mkdir(parents=True)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F002_Empty"]["issues"]
        assert issues[0]["rule_id"] == "TestCases.file_missing"
        assert issues[0]["severity"] == "warning"

    def test_bad_code_format_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("TC001", "TC1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.code_format" and i["severity"] == "critical" for i in issues)

    def test_duplicate_tc_id_is_critical(self, tmp_path):
        dup = VALID_TEST_CASES.replace("TC002", "TC001")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", dup)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.no_dup_tc" for i in issues)

    def test_invalid_type_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("| UT |", "| E2E |")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.type_invalid" for i in issues)

    def test_uat_row_citing_bare_code_is_mismatch(self, tmp_path):
        bad = VALID_TEST_CASES.replace(
            "screens.md § User Journey step 2", "`BR-002`"
        )
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_ut_row_citing_screens_only_is_mismatch(self, tmp_path):
        bad = VALID_TEST_CASES.replace("`BR-001`", "screens.md § something")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_empty_traces_to_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("`BR-001`", "")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.traces_missing" for i in issues)

    def test_coverage_gap_warns_on_untraced_code(self, tmp_path):
        # Remove the [NO_TEST_CASE] note for SM-001 → SM-001 becomes an uncovered gap.
        no_note = VALID_TEST_CASES.split("## Coverage Notes")[0]
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", no_note)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        gap = next(i for i in issues if i["rule_id"] == "TestCases.coverage_gap")
        assert gap["severity"] == "warning"
        assert "SM-001" in gap["message"]

    def test_scoped_fcodes_filter(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        (tmp_path / "plans/p1/artifacts/features/F002_Other").mkdir(parents=True)
        result = validate(tmp_path / "plans/p1", tmp_path, ["F001_Login"])
        assert list(result["specs"].keys()) == ["F001_Login"]


class TestFileLinePathShape:
    """Minor fix: FILE_LINE_RE must require an actual path shape (`/` or `.<ext>:`), not
    accept bare `Note:1`-style tokens as a file:line citation."""

    def test_bare_note_reference_is_still_flagged(self, tmp_path):
        bad = VALID_TEST_CASES.replace("`app/auth/session.rb:22`", "Note:1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" and "TC002" in i["message"]
                   for i in issues), issues

    def test_real_file_line_citation_still_passes(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_edge_cases_reference_still_passes(self, tmp_path):
        via_edge = VALID_TEST_CASES.replace("`app/auth/session.rb:22`", "edge-cases.md § EC-1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", via_edge)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)


class TestFencedRowIgnored:
    """I1 regression: a fenced illustrative malformed row must not be parsed as a live
    test-case row (attack/t7_testcases_fence)."""

    def test_fenced_malformed_row_no_false_criticals(self, tmp_path):
        content = """\
# Test Cases

| Test-ID | Type | Given | When | Then | Traces-to |
|---------|------|-------|------|------|-----------|
| TC001 | UT | valid input | called | returns 200 | BR-001 |

Example of a malformed row we want authors to avoid (illustrative only, from a code review
comment found in the scanned repo):

```markdown
| bad-id | XX | x | y | z | nowhere |
```
"""
        tech_spec = "# Technical Spec\n\n### BR-001_Something\n\nBusiness rule text.\n"
        _write(tmp_path, "plans/p1/artifacts/features/F001_Test/test-cases.md", content)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Test/technical-spec.md", tech_spec)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Test"]["issues"]
        assert not any(i["severity"] == "critical" for i in issues), issues
        assert not any("bad-id" in i["message"] for i in issues)


class TestMainCli:
    def test_exit_0_on_valid(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        rc = main(["--plan-dir", str(tmp_path / "plans/p1"), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_exit_1_on_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("TC001", "TC1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        rc = main(["--plan-dir", str(tmp_path / "plans/p1"), "--project-root", str(tmp_path)])
        assert rc == 1

    def test_summary_out_merges(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        summary_out = tmp_path / "plans/p1/artifacts/validation/tc-validation-summary.json"
        rc = main([
            "--plan-dir", str(tmp_path / "plans/p1"),
            "--project-root", str(tmp_path),
            "--summary-out", str(summary_out),
        ])
        assert rc == 0
        data = json.loads(summary_out.read_text())
        assert "specs" in data["validators"]
        assert data["overall_status"] in ("PASS", "WARN")


class TestSidecarNotGated:
    """F1/F15 regression: test-cases.md must NEVER join the mandatory 4-tuple."""

    def test_not_in_feature_files(self):
        assert "test-cases.md" not in FEATURE_FILES
        assert FEATURE_FILES == (
            "technical-spec.md", "business-context.md", "screens.md", "edge-cases.md",
        )
