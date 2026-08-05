"""Tests for validate_job_list.py (Wave J.2 gate).

Coverage: JOB### regex + file-global uniqueness, **Source** citation presence,
**BL Ref** presence/shape/resolution, secrets gate (F6 — assert_no_secrets wiring),
missing-file warning, CLI exit codes + summary merge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_job_list import validate, main  # noqa: E402

VALID_JOB_LIST = """\
# Job List

## Job Index

| Code | Name | BL Ref | Type | Schedule/Trigger |
|------|------|--------|------|-------------------|
| JOB001_NightlyInvoiceExport | Nightly Invoice Export | BL012 | scheduled-job | daily 02:00 |

---

## JOB001_NightlyInvoiceExport

**BL Ref**: BL012
**Type**: scheduled-job
**Source**: `app/jobs/scheduled/invoice_export_job.rb:8`

### Purpose

Exports paid invoices nightly.

### Schedule / Trigger

Daily at 02:00 UTC (`config/schedule.rb:14`).

### Data Touched

- Invoice — read

### Failure / Retry Behavior

Sidekiq default retry.
"""

BEHAVIOR_LOGIC_WITH_BL012 = """\
# Behavior Logic

## Behavior Logic Index

| Code | Name | Type | Trigger |
|------|------|------|---------|
| BL012_NightlyInvoiceExport | Nightly Invoice Export | scheduled-job | daily |

---

## BL012_NightlyInvoiceExport

**Type**: scheduled-job
**Source File**: app/jobs/scheduled/invoice_export_job.rb
**Source Symbol**: InvoiceExportJob::perform
"""


BEHAVIOR_LOGIC_UNCOVERED_JOB = """\
## BL099_NightlyCleanup

**Type**: scheduled-job
**Source File**: app/jobs/scheduled/cleanup_job.rb
**Source Symbol**: CleanupJob::perform
"""

BEHAVIOR_LOGIC_NON_QUALIFYING = """\
## BL050_SendWelcomeMail

**Type**: mail
**Source File**: app/mail/welcome_mail.rb
**Source Symbol**: WelcomeMail::deliver
"""

NO_INDEX_JOB_LIST = """\
# Job List

## JOB001_NightlyInvoiceExport

**BL Ref**: BL012
**Type**: scheduled-job
**Source**: `app/jobs/scheduled/invoice_export_job.rb:8`
"""


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestValidate:
    def test_valid_job_list_passes(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md", BEHAVIOR_LOGIC_WITH_BL012)
        result = validate(job_path, tmp_path, bl_path)
        assert result["status"] == "PASS"
        assert result["summary"]["critical"] == 0

    def test_missing_file_warns_not_crits(self, tmp_path):
        job_path = tmp_path / "plans/p1/artifacts/job-list.md"
        result = validate(job_path, tmp_path)
        assert result["summary"]["critical"] == 0
        assert any(i["rule_id"] == "JobList.completed_missing" for i in result["issues"])

    def test_missing_source_citation_is_critical(self, tmp_path):
        bad = VALID_JOB_LIST.replace(
            "**Source**: `app/jobs/scheduled/invoice_export_job.rb:8`", ""
        )
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.source_missing" for i in result["issues"])

    def test_bad_code_format_is_critical(self, tmp_path):
        # JOB_H2_RE tolerates a missing slug suffix; JOB_CODE_RE (the full-shape check) does not.
        bad = VALID_JOB_LIST.replace(
            "## JOB001_NightlyInvoiceExport", "## JOB001", 1
        )
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.code_format" for i in result["issues"])

    def test_duplicate_job_code_is_critical(self, tmp_path):
        dup = VALID_JOB_LIST + "\n---\n\n## JOB001_NightlyInvoiceExport\n\n**BL Ref**: BL013\n**Source**: `x.rb:1`\n"
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", dup)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.no_dup_job" for i in result["issues"])

    def test_missing_bl_ref_is_critical(self, tmp_path):
        bad = VALID_JOB_LIST.replace("**BL Ref**: BL012\n", "")
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.bl_ref_missing" for i in result["issues"])

    def test_bl_ref_bad_format_is_critical(self, tmp_path):
        bad = VALID_JOB_LIST.replace("**BL Ref**: BL012", "**BL Ref**: not-a-code")
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.bl_ref_format" for i in result["issues"])

    def test_bl_ref_unresolved_against_behavior_logic(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md",
                         BEHAVIOR_LOGIC_WITH_BL012.replace("BL012", "BL099"))
        result = validate(job_path, tmp_path, bl_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.bl_ref_unresolved" for i in result["issues"])

    def test_bl_ref_resolution_skipped_when_behavior_logic_absent(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        result = validate(job_path, tmp_path, tmp_path / "nope.md")
        assert result["status"] == "PASS"

    def test_secret_leak_is_critical(self, tmp_path):
        leaky = VALID_JOB_LIST + "\napi_key=sk_live_ABC123DEF456\n"
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", leaky)
        result = validate(job_path, tmp_path)
        assert result["status"] == "FAIL"
        assert any(i["rule_id"] == "JobList.secret_leak" for i in result["issues"])


class TestFenceAndCommentAwareParsing:
    """I1 regression: fenced ## JOB999 example must not be parsed as a job, and an
    HTML-comment-wrapped worked example must not be parsed at all (attack/t5_job_fence +
    job-list-template.md's appendix)."""

    def test_fenced_example_job_heading_not_counted(self, tmp_path):
        content = """\
# Job List

## JOB001_SendDailyDigest

**Source**: `src/jobs/digest.rb:10`
**BL Ref**: BL001

Sends a daily digest email. Example config shown below for reference:

```ruby
## JOB999_FakeExample
# this is just an illustrative comment, not a real job
```

Runs every day at 6am.
"""
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", content)
        result = validate(job_path, tmp_path)
        assert result["status"] == "PASS", result["issues"]
        assert not any("JOB999" in i["message"] for i in result["issues"])

    def test_fenced_example_job_does_not_prematurely_close_real_job_body(self, tmp_path):
        # The real job's **Source**/**BL Ref** sit AFTER a fenced "## " line — must still
        # be attributed to JOB001, not dropped because the fence looked like a close.
        content = """\
# Job List

## JOB001_SendDailyDigest

Example config shown below for reference:

```ruby
## an illustrative fenced heading
```

**Source**: `src/jobs/digest.rb:10`
**BL Ref**: BL001
"""
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", content)
        result = validate(job_path, tmp_path)
        assert result["status"] == "PASS", result["issues"]

    def test_html_comment_wrapped_worked_example_not_parsed_as_a_real_job(self, tmp_path):
        # Mirrors templates/job-list-template.md's appendix: an entire fabricated
        # JOB004 section wrapped in an HTML comment must vanish before section parsing.
        content = VALID_JOB_LIST + """
<!--
=============================================================================
APPENDIX — WORKED EXAMPLE (Reference Only; DELETE THIS HTML-COMMENT BLOCK
BEFORE SUBMITTING A REAL JOB LIST. Fabricated codes used here must NOT
appear in the generated output.)
=============================================================================

## JOB004_NightlyInvoiceExport

**BL Ref**: BL012_NightlyInvoiceExport
**Type**: scheduled-job
**Source**: `app/jobs/scheduled/invoice_export_job.rb:8`
=============================================================================
-->
"""
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", content)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md", BEHAVIOR_LOGIC_WITH_BL012)
        result = validate(job_path, tmp_path, bl_path)
        assert result["status"] == "PASS", result["issues"]
        assert not any("JOB004" in i["message"] for i in result["issues"])

    def test_line_start_correct_after_multiline_comment(self, tmp_path):
        # Inspection rework (v26.1.1): strip_comments used to collapse a multi-line
        # comment's newlines, shifting every later section's reported line_start.
        # The broken JOB section below sits at line 10 of the ORIGINAL document —
        # the emitted issue must cite line 10, not line 10 - (comment lines).
        content = """\
# Job List

<!--
five
line
comment
block
-->

## JOB001_BrokenNoSource

**BL Ref**: BL012_NightlyInvoiceExport
"""
        expected_line = content.splitlines().index("## JOB001_BrokenNoSource") + 1
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", content)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md", BEHAVIOR_LOGIC_WITH_BL012)
        result = validate(job_path, tmp_path, bl_path)
        missing = [i for i in result["issues"] if i["rule_id"] == "JobList.source_missing"]
        assert missing, result["issues"]
        assert missing[0]["location"]["line"] == expected_line, (missing[0], expected_line)


class TestReverseBLCoverage:
    """C2 reverse-direction WARN (`JobList.bl_uncovered`): a qualifying (job-type)
    behavior-logic.md BL### with no JOB### referencing it via **BL Ref** — informational,
    never a critical (see references/pipeline-jobs.md J.2 [INFO] note)."""

    def test_qualifying_bl_with_no_job_warns(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md",
                         BEHAVIOR_LOGIC_WITH_BL012 + "\n---\n\n" + BEHAVIOR_LOGIC_UNCOVERED_JOB)
        result = validate(job_path, tmp_path, bl_path)
        assert result["status"] != "FAIL", result["issues"]
        warns = [i for i in result["issues"] if i["rule_id"] == "JobList.bl_uncovered"]
        assert len(warns) == 1
        assert warns[0]["severity"] == "warning"
        assert "BL099" in warns[0]["message"]

    def test_covered_bl_is_not_flagged(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md", BEHAVIOR_LOGIC_WITH_BL012)
        result = validate(job_path, tmp_path, bl_path)
        assert not any(i["rule_id"] == "JobList.bl_uncovered" for i in result["issues"])

    def test_non_qualifying_type_is_never_flagged(self, tmp_path):
        # Type=mail is not in the qualifying set (scheduled-job/queue-worker/custom-command)
        # even though it also has no JOB### referencing it.
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        bl_path = _write(tmp_path, "docs/generated/behavior-logic.md",
                         BEHAVIOR_LOGIC_WITH_BL012 + "\n---\n\n" + BEHAVIOR_LOGIC_NON_QUALIFYING)
        result = validate(job_path, tmp_path, bl_path)
        assert not any("BL050" in i["message"] for i in result["issues"])

    def test_behavior_logic_absent_skips_reverse_check(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        result = validate(job_path, tmp_path, tmp_path / "nope.md")
        assert not any(i["rule_id"] == "JobList.bl_uncovered" for i in result["issues"])


class TestIndexParity:
    """I7 (`JobList.index_drift`): `## Job Index` table rows must match `## JOB###`
    sections 1:1 in both directions. Absent index table degrades to a silent skip."""

    def test_index_entry_with_no_section_warns(self, tmp_path):
        bad = VALID_JOB_LIST.replace(
            "| JOB001_NightlyInvoiceExport | Nightly Invoice Export | BL012 | scheduled-job | daily 02:00 |",
            "| JOB001_NightlyInvoiceExport | Nightly Invoice Export | BL012 | scheduled-job | daily 02:00 |\n"
            "| JOB002_Phantom | Phantom Job | BL013 | scheduled-job | daily |",
        )
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        result = validate(job_path, tmp_path)
        assert result["status"] != "FAIL", result["issues"]
        assert any(i["rule_id"] == "JobList.index_drift" and "JOB002" in i["message"]
                   for i in result["issues"])

    def test_section_with_no_index_entry_warns(self, tmp_path):
        extra_section = VALID_JOB_LIST + (
            "\n---\n\n## JOB002_ExtraJob\n\n**BL Ref**: BL013\n"
            "**Source**: `app/jobs/extra_job.rb:1`\n"
        )
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", extra_section)
        result = validate(job_path, tmp_path)
        assert any(i["rule_id"] == "JobList.index_drift" and "JOB002" in i["message"]
                   for i in result["issues"])

    def test_matching_index_and_sections_no_drift_warning(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        result = validate(job_path, tmp_path)
        assert not any(i["rule_id"] == "JobList.index_drift" for i in result["issues"])

    def test_absent_index_table_skips_silently(self, tmp_path):
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", NO_INDEX_JOB_LIST)
        result = validate(job_path, tmp_path)
        assert not any(i["rule_id"] == "JobList.index_drift" for i in result["issues"])
        assert result["status"] != "FAIL"


class TestMultiBLRef:
    """Minor fix: a comma/space-separated **BL Ref** field must validate EVERY token."""

    def test_second_bad_token_is_flagged(self, tmp_path):
        multi = VALID_JOB_LIST.replace("**BL Ref**: BL012", "**BL Ref**: BL012, BLxyz")
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", multi)
        result = validate(job_path, tmp_path)
        format_issues = [i for i in result["issues"] if i["rule_id"] == "JobList.bl_ref_format"]
        assert len(format_issues) == 1
        assert "BLxyz" in format_issues[0]["message"]
        assert "BL012" not in format_issues[0]["message"]

    def test_all_valid_multi_refs_pass(self, tmp_path):
        multi = VALID_JOB_LIST.replace("**BL Ref**: BL012", "**BL Ref**: BL012, BL013")
        job_path = _write(tmp_path, "plans/p1/artifacts/job-list.md", multi)
        result = validate(job_path, tmp_path)
        assert not any(i["rule_id"] == "JobList.bl_ref_format" for i in result["issues"])


class TestMain:
    def test_cli_pass_exit_zero(self, tmp_path, capsys):
        _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
        ])
        assert rc == 0

    def test_cli_fail_exit_one(self, tmp_path):
        bad = VALID_JOB_LIST.replace("**BL Ref**: BL012\n", "")
        _write(tmp_path, "plans/p1/artifacts/job-list.md", bad)
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
        ])
        assert rc == 1

    def test_cli_summary_out_written(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/job-list.md", VALID_JOB_LIST)
        summary_out = tmp_path / "plans" / "p1" / "artifacts" / "validation" / "job-list-validation-summary.json"
        rc = main([
            "--plan-dir", str(tmp_path / "plans" / "p1"),
            "--project-root", str(tmp_path),
            "--summary-out", str(summary_out),
        ])
        assert rc == 0
        data = json.loads(summary_out.read_text(encoding="utf-8"))
        assert data["validators"]["job_list"]["status"] == "PASS"

    def test_cli_non_directory_plan_dir_errors(self, tmp_path):
        rc = main(["--plan-dir", str(tmp_path / "nope"), "--project-root", str(tmp_path)])
        assert rc == 2
