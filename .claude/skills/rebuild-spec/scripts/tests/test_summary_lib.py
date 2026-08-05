"""Tests for _summary_lib.py — load_summary, merge_validator_result,
recalculate_totals, derive_overall_status, atomic_write.
Coverage per phase-05 test matrix.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _summary_lib import (
    SCHEMA_VERSION,
    atomic_write,
    derive_overall_status,
    load_summary,
    merge_validator_result,
    recalculate_totals,
)


# ---------------------------------------------------------------------------
# load_summary
# ---------------------------------------------------------------------------

class TestLoadSummary:
    def test_seeds_new_schema_when_absent(self, tmp_path):
        path = tmp_path / "validation-summary.json"
        result = load_summary(path, "test-plan")
        assert result["schema_version"] == SCHEMA_VERSION
        assert result["plan"] == "test-plan"
        assert result["overall_status"] == "PASS"
        assert result["totals"] == {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0}
        assert result["validators"] == {}

    def test_returns_existing_data_when_present(self, tmp_path):
        path = tmp_path / "validation-summary.json"
        existing = {
            "schema_version": SCHEMA_VERSION,
            "plan": "old-plan",
            "overall_status": "WARN",
            "generated_at": "2026-01-01T00:00:00Z",
            "totals": {"critical": 0, "warning": 2, "passed_specs": 1, "failed_specs": 0},
            "validators": {"feature_existence": {"status": "WARN", "summary": {"critical": 0, "warning": 2}, "issues": []}},
        }
        path.write_text(json.dumps(existing), encoding="utf-8")
        result = load_summary(path, "new-plan")
        # plan is always overwritten to caller's value
        assert result["plan"] == "new-plan"
        assert result["overall_status"] == "WARN"
        assert result["validators"]["feature_existence"]["status"] == "WARN"

    def test_backfills_missing_default_keys(self, tmp_path):
        path = tmp_path / "validation-summary.json"
        # Write minimal JSON missing several optional keys
        path.write_text(json.dumps({"plan": "x"}), encoding="utf-8")
        result = load_summary(path, "x")
        assert "schema_version" in result
        assert "validators" in result
        assert "totals" in result
        assert "overall_status" in result

    def test_seeds_fresh_on_corrupt_file(self, tmp_path):
        path = tmp_path / "validation-summary.json"
        path.write_text("{bad json", encoding="utf-8")
        result = load_summary(path, "recover-plan")
        assert result["plan"] == "recover-plan"
        assert result["validators"] == {}


# ---------------------------------------------------------------------------
# merge_validator_result
# ---------------------------------------------------------------------------

class TestMergeValidatorResult:
    def _base_summary(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "plan": "p",
            "overall_status": "PASS",
            "generated_at": "2026-01-01T00:00:00Z",
            "totals": {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0},
            "validators": {},
        }

    def test_inserts_feature_existence_slot(self):
        summary = self._base_summary()
        result = {"status": "FAIL", "summary": {"critical": 1, "warning": 0}, "issues": [
            {"severity": "critical", "rule_id": "existence.folder_missing",
             "location": {"file": "artifacts/features/F002_Search", "line": None},
             "message": "folder missing"}
        ]}
        merge_validator_result(summary, "feature_existence", result)
        assert "feature_existence" in summary["validators"]
        assert summary["validators"]["feature_existence"]["status"] == "FAIL"
        assert len(summary["validators"]["feature_existence"]["issues"]) == 1

    def test_merges_per_fcode_for_feature_spec(self):
        summary = self._base_summary()
        result = {
            "specs": {
                "F001_Auth": {
                    "spec_path": "artifacts/features/F001_Auth/spec.md",
                    "issues": [
                        {"validator": "feature_spec", "severity": "critical",
                         "rule_id": "FeatureSpec.required_sections",
                         "location": {"file": "...", "line": None}, "message": "missing H2"}
                    ],
                }
            }
        }
        merge_validator_result(summary, "feature_spec", result)
        specs = summary["validators"]["specs"]
        assert "F001_Auth" in specs
        assert specs["F001_Auth"]["status"] == "FAIL"
        assert specs["F001_Auth"]["summary"]["critical"] == 1

    def test_merges_per_fcode_for_citation(self):
        summary = self._base_summary()
        result = {
            "specs": {
                "F001_Auth": {
                    "spec_path": "artifacts/features/F001_Auth/spec.md",
                    "issues": [
                        {"validator": "citation", "severity": "warning",
                         "rule_id": "citation.unreadable",
                         "location": {"file": "...", "line": 10}, "message": "unreadable"}
                    ],
                }
            }
        }
        merge_validator_result(summary, "citation", result)
        specs = summary["validators"]["specs"]
        assert specs["F001_Auth"]["status"] == "WARN"
        assert specs["F001_Auth"]["summary"]["warning"] == 1

    def test_merge_does_not_duplicate_issues_on_rerun(self):
        summary = self._base_summary()
        issue = {"validator": "feature_spec", "severity": "critical",
                 "rule_id": "FeatureSpec.required_sections",
                 "location": {"file": "x", "line": None}, "message": "m"}
        result = {"specs": {"F001_Auth": {"spec_path": "x", "issues": [issue]}}}
        merge_validator_result(summary, "feature_spec", result)
        merge_validator_result(summary, "feature_spec", result)
        # Second merge replaces, so still 1 issue
        assert len(summary["validators"]["specs"]["F001_Auth"]["issues"]) == 1


# ---------------------------------------------------------------------------
# recalculate_totals
# ---------------------------------------------------------------------------

class TestRecalculateTotals:
    def _make_summary(self, fe_crit=0, fe_warn=0, spec_entries=None):
        summary = {
            "validators": {
                "feature_existence": {
                    "status": "PASS",
                    "summary": {"critical": fe_crit, "warning": fe_warn},
                    "issues": [],
                },
                "specs": spec_entries or {},
            },
            "totals": {},
        }
        return summary

    def test_sums_critical_and_warning_across_validators(self):
        spec_entries = {
            "F001_Auth": {"status": "FAIL", "summary": {"critical": 2, "warning": 1}, "issues": []},
            "F002_Search": {"status": "WARN", "summary": {"critical": 0, "warning": 3}, "issues": []},
        }
        summary = self._make_summary(fe_crit=1, fe_warn=1, spec_entries=spec_entries)
        recalculate_totals(summary)
        assert summary["totals"]["critical"] == 3   # 1 + 2 + 0
        assert summary["totals"]["warning"] == 5    # 1 + 1 + 3

    def test_counts_pass_fail_specs(self):
        spec_entries = {
            "F001_Auth": {"status": "FAIL", "summary": {"critical": 1, "warning": 0}, "issues": []},
            "F002_Search": {"status": "PASS", "summary": {"critical": 0, "warning": 0}, "issues": []},
        }
        summary = self._make_summary(spec_entries=spec_entries)
        recalculate_totals(summary)
        assert summary["totals"]["failed_specs"] == 1
        assert summary["totals"]["passed_specs"] == 1

    def test_zero_totals_when_no_issues(self):
        summary = self._make_summary()
        recalculate_totals(summary)
        assert summary["totals"] == {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0}


# ---------------------------------------------------------------------------
# derive_overall_status
# ---------------------------------------------------------------------------

class TestDeriveOverallStatus:
    def _summary(self, critical=0, warning=0, failed_specs=0, passed_specs=0):
        return {"totals": {"critical": critical, "warning": warning,
                           "failed_specs": failed_specs, "passed_specs": passed_specs}}

    def test_fail_when_critical_present(self):
        assert derive_overall_status(self._summary(critical=1)) == "FAIL"

    def test_fail_when_failed_specs_present(self):
        assert derive_overall_status(self._summary(failed_specs=1)) == "FAIL"

    def test_fail_when_both_critical_and_failed(self):
        assert derive_overall_status(self._summary(critical=2, failed_specs=1)) == "FAIL"

    def test_warn_when_only_warnings(self):
        assert derive_overall_status(self._summary(warning=3)) == "WARN"

    def test_pass_when_all_zero(self):
        assert derive_overall_status(self._summary()) == "PASS"

    def test_pass_when_only_passed_specs(self):
        assert derive_overall_status(self._summary(passed_specs=5)) == "PASS"


# ---------------------------------------------------------------------------
# atomic_write
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    def test_writes_file_and_file_exists(self, tmp_path):
        path = tmp_path / "out.json"
        data = {"key": "value", "number": 42}
        atomic_write(path, data)
        assert path.exists()

    def test_content_is_valid_json(self, tmp_path):
        path = tmp_path / "out.json"
        data = {"schema_version": 1, "plan": "test"}
        atomic_write(path, data)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["plan"] == "test"

    def test_no_tmp_file_left_behind(self, tmp_path):
        path = tmp_path / "out.json"
        atomic_write(path, {"x": 1})
        tmp = path.with_suffix(".json.tmp")
        assert not tmp.exists()

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "out.json"
        atomic_write(path, {"ok": True})
        assert path.exists()


# ---------------------------------------------------------------------------
# id_contiguity slot — direct-set wiring (F12: NOT inside specs sub-dict)
# ---------------------------------------------------------------------------

class TestIdContiguitySlot:
    def _base_summary(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "plan": "p",
            "overall_status": "PASS",
            "generated_at": "2026-01-01T00:00:00Z",
            "totals": {"critical": 0, "warning": 0, "passed_specs": 0, "failed_specs": 0},
            "validators": {},
        }

    def test_slot_lands_at_top_level_validators(self):
        """id_contiguity must be a direct child of validators, not inside specs."""
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "FAIL",
            "summary": {"critical": 1, "warning": 0},
            "issues": [{"severity": "critical", "rule_id": "contiguity.gap",
                        "location": {"file": "artifacts/user-stories.md", "line": None},
                        "message": "US002 missing"}],
        }
        recalculate_totals(summary)
        assert "id_contiguity" in summary["validators"]
        assert "id_contiguity" not in summary["validators"].get("specs", {})

    def test_critical_in_id_contiguity_slot_raises_overall_status_to_fail(self):
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "FAIL",
            "summary": {"critical": 1, "warning": 0},
            "issues": [],
        }
        recalculate_totals(summary)
        summary["overall_status"] = derive_overall_status(summary)
        assert summary["overall_status"] == "FAIL"

    def test_critical_counted_in_totals(self):
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "FAIL",
            "summary": {"critical": 2, "warning": 0},
            "issues": [],
        }
        recalculate_totals(summary)
        assert summary["totals"]["critical"] == 2

    def test_warning_counted_in_totals(self):
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "WARN",
            "summary": {"critical": 0, "warning": 3},
            "issues": [],
        }
        recalculate_totals(summary)
        assert summary["totals"]["warning"] == 3

    def test_warning_only_does_not_flip_to_fail(self):
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "WARN",
            "summary": {"critical": 0, "warning": 1},
            "issues": [],
        }
        recalculate_totals(summary)
        summary["overall_status"] = derive_overall_status(summary)
        assert summary["overall_status"] == "WARN"

    def test_zero_issues_slot_does_not_change_pass(self):
        summary = self._base_summary()
        summary["validators"]["id_contiguity"] = {
            "status": "PASS",
            "summary": {"critical": 0, "warning": 0},
            "issues": [],
        }
        recalculate_totals(summary)
        summary["overall_status"] = derive_overall_status(summary)
        assert summary["overall_status"] == "PASS"
        assert summary["totals"]["critical"] == 0

    def test_id_contiguity_and_feature_existence_totals_accumulate(self):
        """Both slots contribute to totals independently."""
        summary = self._base_summary()
        summary["validators"]["feature_existence"] = {
            "status": "WARN",
            "summary": {"critical": 0, "warning": 1},
            "issues": [],
        }
        summary["validators"]["id_contiguity"] = {
            "status": "FAIL",
            "summary": {"critical": 1, "warning": 0},
            "issues": [],
        }
        recalculate_totals(summary)
        assert summary["totals"]["critical"] == 1
        assert summary["totals"]["warning"] == 1
