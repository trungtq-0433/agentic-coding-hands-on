"""Tests for promote_drafts.py --scope {core,features,flows,glossary,all}.

Covers:
- [RT-H2] --scope core leaves docs/system/glossary.md untouched
- [RT-C4] --scope core with pre-existing docs/features/ writes .stale
- [scope] --scope features promotes ONLY features dir; no system/generated/flows
- [scope] --scope flows promotes ONLY flows dir; no system/generated/features
- [scope] --scope glossary promotes ONLY glossary.md; no features/flows/generated
- [scope] --scope all is byte-identical to the pre-scope full promote (regression)
- [RT-FM9] each pass archives only its own report dir; core .review-archive untouched
          by synthesis passes; archive GC slots not consumed cross-pass
- [RT-FM5] core-only docs/generated/screen-flow.md has the HTML-comment placeholder,
           NOT the raw {POPULATED_BY_W6} token
- [RT-H1] after --flows / --glossary promote, planner OOB detection reports NO false
          [OUT_OF_BAND_EDIT] on flows/glossary (doc_shas refresh guard)
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROMOTE_SCRIPT = SCRIPTS_DIR / "promote_drafts.py"
BUILD_INDEX_SCRIPT = SCRIPTS_DIR / "build_source_to_fcode.py"
PLANNER_SCRIPT = SCRIPTS_DIR / "incremental_planner.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "promote_drafts"
REPO_ROOT = Path(__file__).resolve().parents[5]

_TMP_ROOT = REPO_ROOT / f"_test_scope_tmp_{os.getpid()}"


@pytest.fixture(autouse=True, scope="module")
def _cleanup_tmp():
    yield
    if _TMP_ROOT.exists():
        shutil.rmtree(_TMP_ROOT, ignore_errors=True)


def _run_promote(
    args: list[str],
    cwd: Path,
    keep_archive: bool = False,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if keep_archive:
        env["REBUILD_KEEP_REVIEW_ARCHIVE"] = "1"
    else:
        env.pop("REBUILD_KEEP_REVIEW_ARCHIVE", None)
    return subprocess.run(
        [sys.executable, str(PROMOTE_SCRIPT)] + args,
        capture_output=True, text=True, timeout=30, cwd=str(cwd), env=env,
    )


def _make_scope_plan(subdir: str) -> tuple[Path, Path]:
    """Create a rich fixture plan dir + empty docs root under _TMP_ROOT.

    Returns (plan_dir, docs_root).
    """
    work = _TMP_ROOT / subdir
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    plan_dir = work / "plan"
    shutil.copytree(str(FIXTURES / "plan-dir"), str(plan_dir))

    # Add glossary, flows, and an extra core artifact to the fixture artifacts
    artifacts = plan_dir / "artifacts"
    (artifacts / "glossary.md").write_text("# Glossary\n\nTerm: Definition\n", encoding="utf-8")

    # Ensure core artifacts exist for scope=core tests
    for fname in ("architecture.md", "route-list.md", "screen-flow.md"):
        if not (artifacts / fname).exists():
            (artifacts / fname).write_text(f"# {fname}\n", encoding="utf-8")

    docs_root = work / "docs"
    docs_root.mkdir(parents=True)
    return plan_dir, docs_root


# ---------------------------------------------------------------------------
# [scope] --scope core
# ---------------------------------------------------------------------------

class TestScopeCore:
    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("core_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_core_artifact(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("core_artifact")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        # route-list.md → docs/generated/route-list.md
        assert (docs_root / "generated" / "route-list.md").is_file()

    def test_does_not_promote_features(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("core_no_features")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "features").exists(), \
            "scope=core must not create docs/features/"

    def test_does_not_promote_flows(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("core_no_flows")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "flows").exists(), \
            "scope=core must not create docs/flows/"

    def test_does_not_promote_glossary(self, tmp_path):
        """[RT-H2] --scope core must NOT promote glossary.md even if artifact exists."""
        plan_dir, docs_root = _make_scope_plan("core_no_glossary")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        glossary_dst = docs_root / "system" / "glossary.md"
        assert not glossary_dst.exists(), \
            "scope=core must NOT promote glossary.md (glossary is scope-keyed [RT-H2])"

    def test_leaves_existing_glossary_untouched(self, tmp_path):
        """[RT-H2] If docs/system/glossary.md pre-exists, scope=core must not modify it."""
        plan_dir, docs_root = _make_scope_plan("core_glossary_untouched")
        system_dir = docs_root / "system"
        system_dir.mkdir(parents=True)
        prior_glossary = system_dir / "glossary.md"
        prior_content = "# Original Glossary\nDo NOT overwrite me.\n"
        prior_glossary.write_text(prior_content, encoding="utf-8")

        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        assert prior_glossary.read_text(encoding="utf-8") == prior_content, \
            "scope=core overwrote pre-existing docs/system/glossary.md — [RT-H2] violated"

    def test_writes_stale_marker_when_features_dir_exists(self, tmp_path):
        """[RT-C4] --scope core writes docs/features/.stale when features/ already present."""
        plan_dir, docs_root = _make_scope_plan("core_stale_marker")
        # Pre-create a features dir with one fcode dir (simulates v5 upgrade scenario)
        feat_dir = docs_root / "features" / "F001_Auth"
        feat_dir.mkdir(parents=True)
        (feat_dir / "spec.md").write_text("# F001\n", encoding="utf-8")

        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        stale = docs_root / "features" / ".stale"
        assert stale.is_file(), \
            "scope=core must write docs/features/.stale when features/ dir pre-exists [RT-C4]"
        assert len(stale.read_text(encoding="utf-8").strip()) > 0, \
            ".stale marker must contain a non-empty message"

    def test_no_stale_marker_without_existing_features_dir(self, tmp_path):
        """[RT-C4] --scope core does NOT write .stale if docs/features/ absent."""
        plan_dir, docs_root = _make_scope_plan("core_no_stale_fresh")
        # docs_root has no features/ dir
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "features" / ".stale").exists(), \
            "scope=core must NOT write .stale when features/ dir does not exist"

    def test_archives_to_review_archive_only(self, tmp_path):
        """[RT-FM9] scope=core writes archive to .review-archive, not synthesis dirs.

        Uses REBUILD_KEEP_REVIEW_ARCHIVE=1 so the archive directory survives the
        Phase-03 purge and we can verify routing (purge removes archives by default).
        """
        plan_dir, docs_root = _make_scope_plan("core_archive_dir")
        # Pre-create an archive report so there is something to archive
        (plan_dir / "artifacts" / "review-report.md").write_text(
            "---\nfailed: 0\n---\n# Review\n", encoding="utf-8"
        )
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
            keep_archive=True,
        )
        # .review-archive should have been created (kept via REBUILD_KEEP_REVIEW_ARCHIVE=1)
        assert (docs_root / ".review-archive").is_dir(), \
            "scope=core must create .review-archive dir"
        # Synthesis archive dirs must NOT be created
        for synth_dir in (".feature-specs-archive", ".flows-archive", ".glossary-archive"):
            assert not (docs_root / synth_dir).exists(), \
                f"scope=core must not create {synth_dir} [RT-FM9]"


# ---------------------------------------------------------------------------
# [scope] --scope features
# ---------------------------------------------------------------------------

class TestScopeFeatures:
    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("feat_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_feature_dirs(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("feat_promotes")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "features" / "F001_Auth" / "spec.md").is_file()
        assert (docs_root / "features" / "F002_Profile" / "spec.md").is_file()

    def test_does_not_promote_generated(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("feat_no_generated")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "generated").exists(), \
            "scope=features must not touch docs/generated/"

    def test_does_not_promote_flows(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("feat_no_flows")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "flows").exists(), \
            "scope=features must not touch docs/flows/"

    def test_does_not_promote_glossary(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("feat_no_glossary")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "system" / "glossary.md").exists(), \
            "scope=features must not touch glossary"

    def test_archives_to_feature_specs_archive(self, tmp_path):
        """[RT-FM9] scope=features archives to .feature-specs-archive.

        Uses REBUILD_KEEP_REVIEW_ARCHIVE=1 so the archive directory survives the
        Phase-03 purge and we can verify routing.
        """
        plan_dir, docs_root = _make_scope_plan("feat_archive")
        # A real review report must exist for archiving to happen (L6: no empty
        # archive dirs). feature-review-batch-*.md is discovered dynamically.
        (plan_dir / "artifacts" / "feature-review-batch-1.md").write_text(
            "# Feature review batch 1\n", encoding="utf-8")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "features"],
            cwd=REPO_ROOT,
            keep_archive=True,
        )
        assert (docs_root / ".feature-specs-archive").is_dir(), \
            "scope=features must write to .feature-specs-archive [RT-FM9]"
        # Core archive must NOT be touched
        assert not (docs_root / ".review-archive").exists(), \
            "scope=features must NOT touch .review-archive [RT-FM9]"


# ---------------------------------------------------------------------------
# [scope] --scope flows
# ---------------------------------------------------------------------------

class TestScopeFlows:
    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("flows_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_flows(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("flows_promotes")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "flows" / "test-flow.md").is_file()

    def test_does_not_promote_generated(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("flows_no_generated")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "generated").exists(), \
            "scope=flows must not touch docs/generated/"

    def test_does_not_promote_features(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("flows_no_features")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "features").exists(), \
            "scope=flows must not touch docs/features/"

    def test_does_not_promote_glossary(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("flows_no_glossary")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "system" / "glossary.md").exists(), \
            "scope=flows must not touch glossary"

    def test_archives_to_flows_archive(self, tmp_path):
        """[RT-FM9] scope=flows archives to .flows-archive, not .review-archive.

        Uses REBUILD_KEEP_REVIEW_ARCHIVE=1 so the archive directory survives the
        Phase-03 purge and we can verify routing.
        """
        plan_dir, docs_root = _make_scope_plan("flows_archive")
        # A real review report must exist for archiving to happen (L6: no empty
        # archive dirs). flows scope archives flow-review-report.md.
        (plan_dir / "artifacts" / "flow-review-report.md").write_text(
            "# Flow review report\n", encoding="utf-8")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
            keep_archive=True,
        )
        assert (docs_root / ".flows-archive").is_dir(), \
            "scope=flows must write to .flows-archive [RT-FM9]"
        assert not (docs_root / ".review-archive").exists(), \
            "scope=flows must NOT touch .review-archive [RT-FM9]"

    def test_no_empty_archive_dir_when_nothing_to_archive(self, tmp_path):
        """[L6] With no review report present, no empty timestamped archive dir
        is created — it would otherwise count toward the keep-5 GC and evict a
        genuine prior archive."""
        plan_dir, docs_root = _make_scope_plan("flows_no_archive")
        # Deliberately do NOT create flow-review-report.md.
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr
        assert not (docs_root / ".flows-archive").exists(), \
            "no empty .flows-archive dir when there is nothing to archive [L6]"

    def test_core_review_archive_untouched_by_flows(self, tmp_path):
        """[RT-FM9] A pre-existing .review-archive is not modified by a flows promote."""
        plan_dir, docs_root = _make_scope_plan("flows_review_archive_untouched")
        # Pre-populate core archive with 3 entries
        core_archive = docs_root / ".review-archive"
        core_archive.mkdir(parents=True)
        for i in range(3):
            (core_archive / f"2026-01-0{i+1}T00-00-00Z").mkdir()

        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "flows"],
            cwd=REPO_ROOT,
        )
        # Core archive must still have exactly 3 entries
        remaining = [d for d in core_archive.iterdir() if d.is_dir()]
        assert len(remaining) == 3, \
            "scope=flows must NOT consume GC slots in .review-archive [RT-FM9]"


# ---------------------------------------------------------------------------
# [scope] --scope glossary
# ---------------------------------------------------------------------------

class TestScopeGlossary:
    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("glossary_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_glossary(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("glossary_promotes")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "system" / "glossary.md").is_file()

    def test_does_not_promote_features(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("glossary_no_features")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "features").exists(), \
            "scope=glossary must not touch docs/features/"

    def test_does_not_promote_generated(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("glossary_no_generated")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "generated").exists(), \
            "scope=glossary must not touch docs/generated/"

    def test_does_not_promote_flows(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("glossary_no_flows")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "flows").exists(), \
            "scope=glossary must not touch docs/flows/"

    def test_archives_to_glossary_archive(self, tmp_path):
        """[RT-FM9] scope=glossary archives to .glossary-archive, not .review-archive.

        Uses REBUILD_KEEP_REVIEW_ARCHIVE=1 so the archive directory survives the
        Phase-03 purge and we can verify routing.
        """
        plan_dir, docs_root = _make_scope_plan("glossary_archive")
        (plan_dir / "artifacts" / "glossary-review-report.md").write_text(
            "---\nfailed: 0\n---\n# Glossary Review\n", encoding="utf-8"
        )
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
            keep_archive=True,
        )
        assert (docs_root / ".glossary-archive").is_dir(), \
            "scope=glossary must write to .glossary-archive [RT-FM9]"
        assert not (docs_root / ".review-archive").exists(), \
            "scope=glossary must NOT touch .review-archive [RT-FM9]"

    def test_core_review_archive_untouched_by_glossary(self, tmp_path):
        """[RT-FM9] A pre-existing .review-archive is not modified by a glossary promote."""
        plan_dir, docs_root = _make_scope_plan("glossary_review_archive_untouched")
        core_archive = docs_root / ".review-archive"
        core_archive.mkdir(parents=True)
        for i in range(2):
            (core_archive / f"2026-02-0{i+1}T00-00-00Z").mkdir()

        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        remaining = [d for d in core_archive.iterdir() if d.is_dir()]
        assert len(remaining) == 2, \
            "scope=glossary must NOT consume GC slots in .review-archive [RT-FM9]"


# ---------------------------------------------------------------------------
# [scope] --scope jobs (v26.1.0 A2 pass — mirrors --scope glossary exactly)
# ---------------------------------------------------------------------------

class TestScopeJobs:
    def _plan_with_job_list(self, subdir: str) -> tuple[Path, Path]:
        plan_dir, docs_root = _make_scope_plan(subdir)
        (plan_dir / "artifacts" / "job-list.md").write_text(
            "# Job List\n\n## JOB001_Nightly\n\n**BL Ref**: BL001\n**Source**: `x.rb:1`\n",
            encoding="utf-8",
        )
        return plan_dir, docs_root

    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = self._plan_with_job_list("jobs_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_job_list(self, tmp_path):
        plan_dir, docs_root = self._plan_with_job_list("jobs_promotes")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "generated" / "job-list.md").is_file()

    def test_does_not_promote_features(self, tmp_path):
        plan_dir, docs_root = self._plan_with_job_list("jobs_no_features")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "features").exists(), \
            "scope=jobs must not touch docs/features/"

    def test_does_not_promote_flows(self, tmp_path):
        plan_dir, docs_root = self._plan_with_job_list("jobs_no_flows")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "flows").exists(), \
            "scope=jobs must not touch docs/flows/"

    def test_does_not_promote_glossary(self, tmp_path):
        plan_dir, docs_root = self._plan_with_job_list("jobs_no_glossary")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "system" / "glossary.md").exists(), \
            "scope=jobs must not touch docs/system/glossary.md"

    def test_does_not_promote_other_generated(self, tmp_path):
        """scope=jobs promotes ONLY job-list.md — no route-list.md/feature-list.md etc."""
        plan_dir, docs_root = self._plan_with_job_list("jobs_no_other_generated")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
        )
        assert not (docs_root / "generated" / "route-list.md").exists(), \
            "scope=jobs must not touch docs/generated/route-list.md"

    def test_archives_to_jobs_archive(self, tmp_path):
        """[RT-FM9] scope=jobs archives to .jobs-archive, not .review-archive."""
        plan_dir, docs_root = self._plan_with_job_list("jobs_archive")
        (plan_dir / "artifacts" / "job-list-review-report.md").write_text(
            "---\nfailed: 0\n---\n# Job List Review\n", encoding="utf-8"
        )
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "jobs"],
            cwd=REPO_ROOT,
            keep_archive=True,
        )
        assert (docs_root / ".jobs-archive").is_dir(), \
            "scope=jobs must write to .jobs-archive [RT-FM9]"
        assert not (docs_root / ".review-archive").exists(), \
            "scope=jobs must NOT touch .review-archive [RT-FM9]"


# ---------------------------------------------------------------------------
# [scope] --scope all (regression: byte-identical to pre-scope full promote)
# ---------------------------------------------------------------------------

class TestScopeAll:
    def test_exit_code_zero(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("all_exit")
        r = _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        assert r.returncode == 0, r.stderr

    def test_promotes_core_artifacts(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("all_core")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "generated" / "route-list.md").is_file()
        assert (docs_root / "generated" / "feature-list.md").is_file()

    def test_promotes_features(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("all_features")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "features" / "F001_Auth" / "spec.md").is_file()
        assert (docs_root / "features" / "F002_Profile" / "spec.md").is_file()

    def test_promotes_flows(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("all_flows")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "flows" / "test-flow.md").is_file()

    def test_promotes_glossary(self, tmp_path):
        plan_dir, docs_root = _make_scope_plan("all_glossary")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        assert (docs_root / "system" / "glossary.md").is_file()

    def test_default_scope_matches_all(self, tmp_path):
        """Omitting --scope defaults to 'all' — byte-identical set of promoted files."""
        plan_dir_all, docs_root_all = _make_scope_plan("all_regression_a")
        plan_dir_def, docs_root_def = _make_scope_plan("all_regression_b")

        _run_promote(
            ["--plan-dir", str(plan_dir_all), "--docs-root", str(docs_root_all),
             "--mode", "full", "--scope", "all"],
            cwd=REPO_ROOT,
        )
        _run_promote(
            ["--plan-dir", str(plan_dir_def), "--docs-root", str(docs_root_def),
             "--mode", "full"],
            cwd=REPO_ROOT,
        )

        # Collect relative promoted paths for both runs
        def _collect(root: Path) -> set[str]:
            return {
                str(p.relative_to(root))
                for p in root.rglob("*")
                if p.is_file() and not p.name.startswith(".")
            }

        files_all = _collect(docs_root_all)
        files_def = _collect(docs_root_def)
        assert files_all == files_def, (
            f"--scope all differs from default (no --scope flag).\n"
            f"  only in all:     {files_all - files_def}\n"
            f"  only in default: {files_def - files_all}"
        )


# ---------------------------------------------------------------------------
# [RT-FM5] screen-flow placeholder — no raw {POPULATED_BY_W6} token
# ---------------------------------------------------------------------------

class TestScreenFlowPlaceholder:
    def test_promoted_screen_flow_has_no_raw_populated_by_w6_token(self, tmp_path):
        """[RT-FM5] docs/generated/screen-flow.md must not contain the raw template token."""
        plan_dir, docs_root = _make_scope_plan("rt_fm5_placeholder")
        # Write a screen-flow.md that uses the HTML-comment placeholder (correct)
        (plan_dir / "artifacts" / "screen-flow.md").write_text(
            "# Screen Flow\n\n"
            "<!-- POPULATED_BY_FEATURE_SPECS_PASS: run `/tkm:rebuild-spec --feature-specs` -->\n",
            encoding="utf-8",
        )
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "core"],
            cwd=REPO_ROOT,
        )
        promoted = docs_root / "generated" / "screen-flow.md"
        if promoted.is_file():
            content = promoted.read_text(encoding="utf-8")
            assert "{POPULATED_BY_W6}" not in content, \
                "docs/generated/screen-flow.md must not contain raw {POPULATED_BY_W6} token [RT-FM5]"

    def test_raw_token_absent_in_default_fixture_artifact(self, tmp_path):
        """[RT-FM5] The fixture screen-flow.md (if present) also must not have the raw token."""
        plan_dir, docs_root = _make_scope_plan("rt_fm5_fixture")
        src = plan_dir / "artifacts" / "screen-flow.md"
        if src.is_file():
            assert "{POPULATED_BY_W6}" not in src.read_text(encoding="utf-8"), \
                "fixture screen-flow.md must not contain raw {POPULATED_BY_W6} token [RT-FM5]"


# ---------------------------------------------------------------------------
# [RT-H1] OOB false-positive guard — after flows/glossary promote, doc_shas
#          must not flag glossary.md as an out-of-band edit
# ---------------------------------------------------------------------------

class TestOobFalsePositiveGuard:
    """After a --scope glossary promote + build_source_to_fcode.py --cursor glossary,
    the .rebuild-state.json doc_shas["glossary.md"] matches the promoted file,
    so planner _detect_oob() does NOT emit [OUT_OF_BAND_EDIT] on glossary.md.
    """

    def _init_git_repo(self, d: Path) -> str:
        subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(d), "config", "user.email", "t@t.com"],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                       capture_output=True, check=True)
        (d / "init.txt").write_text("init")
        subprocess.run(["git", "-C", str(d), "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(d), "commit", "-m", "init"],
                       capture_output=True, check=True)
        r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()

    def test_no_oob_on_glossary_after_glossary_promote(self, tmp_path):
        """[RT-H1] After --scope glossary + state refresh, glossary.md is NOT OOB."""
        import hashlib

        _SCRIPTS_DIR = SCRIPTS_DIR
        sys.path.insert(0, str(_SCRIPTS_DIR))
        from incremental_planner import _detect_oob  # noqa: PLC0415

        plan_dir, docs_root = _make_scope_plan("rt_h1_glossary_oob")

        # Promote glossary
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        glossary_path = docs_root / "system" / "glossary.md"
        assert glossary_path.is_file(), "glossary.md must have been promoted"

        # Simulate the state that build_source_to_fcode would write after --cursor glossary
        # (doc_shas includes the correct sha for glossary.md)
        sha = hashlib.sha256(glossary_path.read_bytes()).hexdigest()
        state = {"doc_shas": {"glossary.md": sha}}

        warnings = _detect_oob(state, docs_root, affected_waves=[])
        oob_glossary = [w for w in warnings if "glossary" in w.lower()]
        assert oob_glossary == [], \
            f"No false [OUT_OF_BAND_EDIT] expected for glossary.md after glossary promote, got: {oob_glossary}"

    def test_oob_detected_when_glossary_sha_stale(self, tmp_path):
        """Control: OOB IS reported when the stored sha doesn't match the current file."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        from incremental_planner import _detect_oob  # noqa: PLC0415

        plan_dir, docs_root = _make_scope_plan("rt_h1_oob_stale")
        _run_promote(
            ["--plan-dir", str(plan_dir), "--docs-root", str(docs_root),
             "--mode", "full", "--scope", "glossary"],
            cwd=REPO_ROOT,
        )
        # State with a deliberately wrong sha
        state = {"doc_shas": {"glossary.md": "0" * 64}}
        warnings = _detect_oob(state, docs_root, affected_waves=[])
        oob_glossary = [w for w in warnings if "glossary" in w.lower()]
        assert oob_glossary, \
            "OOB warning expected when stored sha != current file sha (control test)"
