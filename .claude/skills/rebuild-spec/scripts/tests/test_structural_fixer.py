"""Tests for scripts/structural_fixer.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS_DIR / "structural_fixer.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "structural_fixer"

# v4 feature spec filename (BR/SM/ALG/INT blocks live here). Legacy plans used "spec.md".
SPEC_FILENAME = "technical-spec.md"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


def _make_plan_dir(
    tmp_path: Path, spec_content: str, fcode: str = "F001_Auth",
    spec_filename: str = SPEC_FILENAME,
) -> Path:
    """Set up a minimal plan dir with one feature spec."""
    plan_dir = tmp_path / "plan"
    feat_dir = plan_dir / "artifacts" / "features" / fcode
    feat_dir.mkdir(parents=True)
    (feat_dir / spec_filename).write_text(spec_content, encoding="utf-8")
    return plan_dir


class TestInsertsLinkedFr:
    def test_exit_code_zero(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src)
        result = _run(
            ["--plan-dir", str(plan_dir), "--no-decrement"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr

    def test_inserts_linked_fr_placeholder(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "features" / "F001_Auth" / SPEC_FILENAME).read_text()
        assert "**Linked FR:** FR-???" in content

    def test_fix_report_records_blocks_fixed(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["blocks_fixed"] >= 1

    def test_backup_created(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        backup = (
            plan_dir / "artifacts" / "validation" / "structural-fix-backup"
            / "F001_Auth" / f"{SPEC_FILENAME}.orig"
        )
        assert backup.is_file()


class TestIdempotent:
    def test_running_twice_does_not_double_insert(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "features" / "F001_Auth" / SPEC_FILENAME).read_text()
        # Count occurrences — idempotent means exactly one insertion per block
        assert content.count("**Linked FR:** FR-???") == content.count("### BR-")

    def test_spec_with_existing_linked_fr_unchanged(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-existing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src, fcode="F002_Profile")
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["blocks_fixed"] == 0


class TestIncrementalScope:
    """Tests for --incremental-plan-json scoping."""

    def _make_multi_feature_plan(self, tmp_path: Path, fcodes: list[str]) -> Path:
        """Set up a plan dir with N feature specs, all missing Linked FR."""
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = tmp_path / "plan"
        for fc in fcodes:
            feat_dir = plan_dir / "artifacts" / "features" / fc
            feat_dir.mkdir(parents=True)
            (feat_dir / SPEC_FILENAME).write_text(
                spec_src.replace("F001_Auth", fc), encoding="utf-8"
            )
        return plan_dir

    def test_scope_full_mode_walks_all(self, tmp_path):
        fcodes = [f"F{i:03d}_Feat{i}" for i in range(1, 9)]
        plan_dir = self._make_multi_feature_plan(tmp_path, fcodes)
        inc_plan = plan_dir / "artifacts" / ".incremental-plan.json"
        inc_plan.parent.mkdir(parents=True, exist_ok=True)
        inc_plan.write_text(json.dumps({
            "mode": "full",
            "affected_fcodes": ["F001_Feat1"],
        }), encoding="utf-8")
        result = _run([
            "--plan-dir", str(plan_dir),
            "--no-decrement",
            "--incremental-plan-json", str(inc_plan),
        ], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["scope_mode"] == "full"
        assert len(report["by_file"]) == 8

    def test_scope_incremental_walks_only_affected(self, tmp_path):
        fcodes = ["F001_Auth", "F002_Profile", "F003_Payments"]
        plan_dir = self._make_multi_feature_plan(tmp_path, fcodes)
        inc_plan = plan_dir / "artifacts" / ".incremental-plan.json"
        inc_plan.parent.mkdir(parents=True, exist_ok=True)
        inc_plan.write_text(json.dumps({
            "mode": "incremental",
            "affected_fcodes": ["F001_Auth"],
        }), encoding="utf-8")
        result = _run([
            "--plan-dir", str(plan_dir),
            "--no-decrement",
            "--incremental-plan-json", str(inc_plan),
        ], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["scope_mode"] == "incremental"
        assert report["scoped_fcodes"] == ["F001_Auth"]
        assert "F001_Auth" in report["by_file"]
        assert "F002_Profile" not in report["by_file"]
        assert "F003_Payments" not in report["by_file"]
        # Verify F002 and F003 spec files were NOT modified
        f2_content = (plan_dir / "artifacts" / "features" / "F002_Profile" / SPEC_FILENAME).read_text()
        assert "**Linked FR:** FR-???" not in f2_content

    def test_scope_missing_plan_file_falls_through(self, tmp_path):
        fcodes = ["F001_Auth", "F002_Profile"]
        plan_dir = self._make_multi_feature_plan(tmp_path, fcodes)
        result = _run([
            "--plan-dir", str(plan_dir),
            "--no-decrement",
            "--incremental-plan-json", str(tmp_path / "nonexistent.json"),
        ], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert "walking all features" in result.stderr
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["scope_mode"] == "full"
        assert len(report["by_file"]) == 2


class TestMultiBlockAllMissingLinkedFr:
    """C2 regression — all blocks in a multi-block spec must receive Linked FR."""

    def test_three_blocks_all_missing_linked_fr_all_fixed(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-three-missing-linked-fr.md").read_text()
        plan_dir = tmp_path / "plan"
        feat_dir = plan_dir / "artifacts" / "features" / "F099_MultiBlock"
        feat_dir.mkdir(parents=True)
        (feat_dir / SPEC_FILENAME).write_text(spec_src, encoding="utf-8")

        result = _run(
            ["--plan-dir", str(plan_dir), "--no-decrement"],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr

        content = (feat_dir / SPEC_FILENAME).read_text(encoding="utf-8")

        # All 3 blocks (BR-001, BR-002, SM-001) must have Linked FR inserted
        assert content.count("**Linked FR:** FR-???") == 3

        # Verify via _spec_block_lib that zero missing blocks remain
        import sys
        sys.path.insert(0, str(SCRIPTS_DIR))
        from _spec_block_lib import find_blocks_missing_linked_fr
        assert find_blocks_missing_linked_fr(content) == []


class TestIncrementalBareFcodeAccepted:
    """C3 regression — bare F### fcode (no slug suffix) must be accepted by structural_fixer."""

    def test_incremental_bare_fcode_accepted(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src, fcode="F001_Auth")

        inc_plan = plan_dir / "artifacts" / ".incremental-plan.json"
        inc_plan.parent.mkdir(parents=True, exist_ok=True)
        # Bare F### format — the planner's actual output (no _Slug suffix)
        inc_plan.write_text(
            json.dumps({"mode": "incremental", "affected_fcodes": ["F001"]}),
            encoding="utf-8",
        )

        result = _run(
            [
                "--plan-dir", str(plan_dir),
                "--no-decrement",
                "--incremental-plan-json", str(inc_plan),
            ],
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr

        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        # The fixer must have walked F001_Auth (prefix-resolution logic)
        assert len(report["by_file"]) >= 1, (
            "Expected at least one spec processed — bare fcode F001 should resolve to F001_Auth"
        )
        assert "F001_Auth" in report["by_file"]


class TestReviewReportDecrement:
    def _make_plan_with_review(
        self, tmp_path: Path, spec_src: str, review_src: str, fcode: str = "F001_Auth"
    ) -> Path:
        plan_dir = _make_plan_dir(tmp_path, spec_src, fcode)
        (plan_dir / "artifacts" / "review-report.md").write_text(review_src, encoding="utf-8")
        return plan_dir

    def test_failed_count_decremented(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        review_src = (FIXTURES / "review-report.25-linked-fr-critical.md").read_text()
        plan_dir = self._make_plan_with_review(tmp_path, spec_src, review_src)
        _run(["--plan-dir", str(plan_dir)], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "review-report.md").read_text()
        # failed: 25 should have been decremented
        import re
        m = re.search(r"^failed:\s*(\d+)", content, re.MULTILINE)
        assert m is not None
        assert int(m.group(1)) < 25

    def test_no_decrement_skips_review_report_mutation(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        review_src = (FIXTURES / "review-report.25-linked-fr-critical.md").read_text()
        plan_dir = self._make_plan_with_review(tmp_path, spec_src, review_src)
        _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        content = (plan_dir / "artifacts" / "review-report.md").read_text()
        import re
        m = re.search(r"^failed:\s*(\d+)", content, re.MULTILINE)
        assert m is not None
        assert int(m.group(1)) == 25  # unchanged


class TestFeatureSpecFilenameResolution:
    """v4 split feature specs into 4 files; BR/SM/ALG/INT blocks live in technical-spec.md.
    The fixer must target technical-spec.md (v4) and still fall back to spec.md (legacy)."""

    def test_v4_technical_spec_is_fixed(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src, spec_filename="technical-spec.md")
        result = _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        content = (plan_dir / "artifacts" / "features" / "F001_Auth" / "technical-spec.md").read_text()
        assert "**Linked FR:** FR-???" in content
        report = json.loads(
            (plan_dir / "artifacts" / "validation" / "structural-fix-report.json").read_text()
        )
        assert report["blocks_fixed"] >= 1

    def test_legacy_spec_md_still_fixed(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src, spec_filename="spec.md")
        result = _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        content = (plan_dir / "artifacts" / "features" / "F001_Auth" / "spec.md").read_text()
        assert "**Linked FR:** FR-???" in content
        # Backup name follows the resolved file.
        backup = (
            plan_dir / "artifacts" / "validation" / "structural-fix-backup"
            / "F001_Auth" / "spec.md.orig"
        )
        assert backup.is_file()

    def test_technical_spec_preferred_over_legacy_when_both_present(self, tmp_path):
        spec_src = (FIXTURES / "spec.with-missing-linked-fr.md").read_text()
        plan_dir = _make_plan_dir(tmp_path, spec_src, spec_filename="technical-spec.md")
        # Legacy file present but already complete — must be left untouched.
        legacy = (FIXTURES / "spec.with-existing-linked-fr.md").read_text()
        feat_dir = plan_dir / "artifacts" / "features" / "F001_Auth"
        (feat_dir / "spec.md").write_text(legacy, encoding="utf-8")
        result = _run(["--plan-dir", str(plan_dir), "--no-decrement"], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        # v4 file fixed, legacy file untouched.
        assert "**Linked FR:** FR-???" in (feat_dir / "technical-spec.md").read_text()
        assert "FR-???" not in (feat_dir / "spec.md").read_text()
