"""Tests for _manifest_pass_status_lib.py (v16.1.0 per-pass batch driver).

Coverage (from phase-03 success criteria):
- next_pending_pass: core-done gate, DAG prereq, reused/excluded skip, first-eligible order
- mark_pass_done / mark_pass_failed: status set, failed not re-picked, nested merge no-clobber,
  retry-success clears fail reason, comp-not-found raises
- resume sim: 20 core-done, feature-specs 1-6 done → returns #7
- pass_summary: done/pending/failed/blocked counts
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _components_manifest_lib as mlib  # noqa: E402
import _manifest_pass_status_lib as plib  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_components(n: int, prefix: str = "services/svc") -> list[dict]:
    return [
        {
            "path": f"{prefix}-{i:02d}",
            "profile": "spring",
            "role": "domain-service",
            "size_est": 100,
            "timeout_hint": 3600,
            "max_loc": 10000,
        }
        for i in range(1, n + 1)
    ]


def _emit(tmp_path, comps) -> str:
    manifest_path = str(tmp_path / ".rebuild-components.json")
    mlib.emit_manifest(manifest_path, comps, str(tmp_path))
    return manifest_path


def _mark_core_done(manifest_path, comp_paths) -> None:
    sha = "0" * 64
    for cp in comp_paths:
        mlib.mark_done(manifest_path, cp, sha)


# ---------------------------------------------------------------------------
# next_pending_pass
# ---------------------------------------------------------------------------

class TestNextPendingPass:
    def test_core_not_done_returns_none(self, tmp_path):
        """Core pending/reused/excluded entries are all skipped."""
        comps = _make_components(2)
        manifest_path = _emit(tmp_path, comps)
        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "feature-specs") is None

    def test_reused_entry_skipped(self, tmp_path):
        """A reused component (status != done) is never eligible for any pass."""
        reused = {
            "path": "employee", "profile": None, "role": "service", "group": None,
            "status": "reused", "docs_path": "employee/docs",
            "source_sha": "a" * 40, "is_git_root": False,
        }
        manifest_path = _emit(tmp_path, [reused])
        entries = mlib.load_manifest(manifest_path, str(tmp_path))
        assert plib.next_pending_pass(entries, "feature-specs") is None

    def test_core_done_feature_specs_absent_returns_entry(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, "feature-specs")
        assert nxt is not None
        assert nxt["path"] == comps[0]["path"]

    def test_dag_flows_blocked_until_feature_specs_done(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])

        # feature-specs not done yet → flows blocked
        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "flows") is None

        # after feature-specs done → flows eligible
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, "flows")
        assert nxt is not None
        assert nxt["path"] == comps[0]["path"]

    def test_dag_glossary_requires_feature_specs(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "glossary") is None

    def test_dag_test_cases_blocked_until_feature_specs_done(self, tmp_path):
        """v26.1.0 B6 pass: test-cases requires feature-specs (same DAG class as flows/glossary)."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])

        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "test-cases") is None

        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, "test-cases")
        assert nxt is not None
        assert nxt["path"] == comps[0]["path"]

    def test_returns_first_eligible_in_manifest_order(self, tmp_path):
        comps = _make_components(3)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [c["path"] for c in comps])
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, "feature-specs")
        assert nxt["path"] == comps[0]["path"]

    def test_invalid_pass_name_raises(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        entries = mlib.load_manifest(manifest_path)
        with pytest.raises(ValueError):
            plib.next_pending_pass(entries, "bogus-pass")

    @pytest.mark.parametrize("pass_name", ["feature-specs", "screen-specs", "jobs", "design-intent"])
    def test_no_prereq_passes_eligible_once_core_done(self, tmp_path, pass_name):
        """feature-specs, screen-specs, jobs, AND design-intent need only core done (no pass prereqs)."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, pass_name)
        assert nxt is not None
        assert nxt["path"] == comps[0]["path"]


# ---------------------------------------------------------------------------
# mark_pass_done / mark_pass_failed
# ---------------------------------------------------------------------------

class TestMarkPass:
    def test_mark_done_makes_pass_ineligible(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "feature-specs") is None

    def test_failed_is_not_re_picked(self, tmp_path):
        """Only 'pending' is re-picked; 'failed' stays out of next_pending_pass."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_failed(manifest_path, comps[0]["path"], "feature-specs", "boom")
        entries = mlib.load_manifest(manifest_path)
        assert plib.next_pending_pass(entries, "feature-specs") is None
        e = entries[0]
        assert e["pass_status"]["feature-specs"] == "failed"
        assert e["pass_fail_reason"]["feature-specs"] == "boom"

    def test_nested_merge_no_clobber(self, tmp_path):
        """done feature-specs then failed flows → both keys survive."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        plib.mark_pass_failed(manifest_path, comps[0]["path"], "flows", "net err")
        entries = mlib.load_manifest(manifest_path)
        pstatus = entries[0]["pass_status"]
        assert pstatus["feature-specs"] == "done"
        assert pstatus["flows"] == "failed"
        assert entries[0]["pass_fail_reason"]["flows"] == "net err"

    def test_done_clears_prior_fail_reason(self, tmp_path):
        """Retry success: mark_pass_done removes the stale fail reason."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_failed(manifest_path, comps[0]["path"], "feature-specs", "boom")
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["pass_status"]["feature-specs"] == "done"
        assert "feature-specs" not in entries[0].get("pass_fail_reason", {})

    def test_comp_path_not_found_raises(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        with pytest.raises(ValueError):
            plib.mark_pass_done(manifest_path, "no/such/comp", "feature-specs")

    def test_screen_specs_done_makes_ineligible(self, tmp_path):
        """screen-specs follows the same mark→ineligible path as feature-specs."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "screen-specs")
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["pass_status"]["screen-specs"] == "done"
        assert plib.next_pending_pass(entries, "screen-specs") is None

    def test_mark_pass_done_jobs_does_not_raise(self, tmp_path):
        """F1 regression: 'jobs' must be registered in PASS_NAMES/PASS_PREREQS —
        mark_pass_done('jobs') previously raised ValueError('Unknown pass') for any
        pass name not in the hardcoded list. v26.1.0 A2 pass registration."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "jobs")  # must not raise
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["pass_status"]["jobs"] == "done"
        assert plib.next_pending_pass(entries, "jobs") is None
        assert "jobs" in plib.PASS_NAMES

    def test_mark_pass_done_test_cases_does_not_raise(self, tmp_path):
        """F1 regression: 'test-cases' must be registered in PASS_NAMES/PASS_PREREQS —
        mark_pass_done('test-cases') previously raised ValueError('Unknown pass') for any
        pass name not in the hardcoded list. v26.1.0 B6 pass registration."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        plib.mark_pass_done(manifest_path, comps[0]["path"], "test-cases")  # must not raise
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["pass_status"]["test-cases"] == "done"
        assert plib.next_pending_pass(entries, "test-cases") is None
        assert "test-cases" in plib.PASS_NAMES

    def test_mark_pass_done_design_intent_does_not_raise(self, tmp_path):
        """F1 regression: 'design-intent' must be registered in PASS_NAMES/PASS_PREREQS —
        mark_pass_done('design-intent') previously raised ValueError('Unknown pass') for any
        pass name not in the hardcoded list. v26.1.0 B5 pass registration (EXPERIMENTAL,
        report-only — but the manifest-eligibility registration is unconditional)."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "design-intent")  # must not raise
        entries = mlib.load_manifest(manifest_path)
        assert entries[0]["pass_status"]["design-intent"] == "done"
        assert plib.next_pending_pass(entries, "design-intent") is None
        assert "design-intent" in plib.PASS_NAMES

    def test_invalid_pass_name_raises(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        with pytest.raises(ValueError):
            plib.mark_pass_done(manifest_path, comps[0]["path"], "nope")
        with pytest.raises(ValueError):
            plib.mark_pass_failed(manifest_path, comps[0]["path"], "nope", "r")

    def test_core_status_untouched(self, tmp_path):
        """Pass updates must never alter the core status/sha (back-compat)."""
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        before = mlib.load_manifest(manifest_path)[0]
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        after = mlib.load_manifest(manifest_path)[0]
        assert after["status"] == "done"
        assert after["sha"] == before["sha"]


# ---------------------------------------------------------------------------
# resume simulation
# ---------------------------------------------------------------------------

class TestResume:
    def test_resume_feature_specs_at_7_of_20(self, tmp_path):
        comps = _make_components(20)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [c["path"] for c in comps])
        for c in comps[:6]:
            plib.mark_pass_done(manifest_path, c["path"], "feature-specs")
        entries = mlib.load_manifest(manifest_path)
        nxt = plib.next_pending_pass(entries, "feature-specs")
        assert nxt is not None
        assert nxt["path"] == comps[6]["path"]


# ---------------------------------------------------------------------------
# pass_summary
# ---------------------------------------------------------------------------

class TestPassSummary:
    def test_counts_blocked_done_pending_failed(self, tmp_path):
        comps = _make_components(4)
        manifest_path = _emit(tmp_path, comps)
        # 3 core done, 1 still pending (blocked for every pass)
        _mark_core_done(manifest_path, [c["path"] for c in comps[:3]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        plib.mark_pass_failed(manifest_path, comps[1]["path"], "feature-specs", "x")
        # comps[2] feature-specs still pending
        entries = mlib.load_manifest(manifest_path)
        summary = plib.pass_summary(entries)

        fs = summary["feature-specs"]
        assert fs["done"] == 1
        assert fs["failed"] == 1
        assert fs["pending"] == 1   # comps[2]
        assert fs["blocked"] == 1   # comps[3] core pending

        # flows: comps[0] has feature-specs done → pending; comps[1] failed prereq,
        # comps[2] feature-specs pending → both blocked; comps[3] core pending → blocked
        flows = summary["flows"]
        assert flows["pending"] == 1   # comps[0]
        assert flows["blocked"] == 3
        assert flows["done"] == 0
        assert flows["failed"] == 0

    def test_all_pass_names_present(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        entries = mlib.load_manifest(manifest_path)
        summary = plib.pass_summary(entries)
        assert set(summary) == set(plib.PASS_NAMES)


# ---------------------------------------------------------------------------
# lock-file cleanup
# ---------------------------------------------------------------------------

class TestLockCleanup:
    def test_no_lock_file_left_behind(self, tmp_path):
        comps = _make_components(1)
        manifest_path = _emit(tmp_path, comps)
        _mark_core_done(manifest_path, [comps[0]["path"]])
        plib.mark_pass_done(manifest_path, comps[0]["path"], "feature-specs")
        assert not Path(manifest_path + ".lock").exists()
        assert list(tmp_path.glob("*.json.tmp")) == []
