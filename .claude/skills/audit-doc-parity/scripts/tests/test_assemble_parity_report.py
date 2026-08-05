"""Tests for assemble_parity_report.py."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import assemble_parity_report as apr

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_finding(verdict, unit="F001", field="auth",
                  adjudicated=True, severity="critical",
                  doc_says="admin only", code_reality="no role check",
                  confidence="EXTRACTED:0.9"):
    return {
        "verdict": verdict,
        "unit": unit,
        "kind": "FR",
        "field": field,
        "doc_location": f"docs/features/{unit}/technical-spec.md:42",
        "doc_says": doc_says,
        "code_reality": code_reality,
        "evidence_line": f"src/api/{unit.lower()}.ts:88",
        "severity": severity,
        "confidence": confidence,
        "adjudicated": adjudicated,
    }


def _make_verdicts(findings, project="testapp", features=5, claims=None):
    return {
        "project": project,
        "scope": {
            "mode": "sweep",
            "features": features,
            "claims": claims or len(findings),
        },
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# _count_by_verdict
# ---------------------------------------------------------------------------

class TestCountByVerdict:
    def test_empty(self):
        counts = apr._count_by_verdict([])
        assert counts["MATCH"] == 0
        assert counts["DRIFT"] == 0

    def test_mixed(self):
        findings = [
            _make_finding("MATCH"),
            _make_finding("MATCH"),
            _make_finding("DRIFT"),
            _make_finding("FABRICATED"),
            _make_finding("MISSING", severity="warning"),
            _make_finding("UNVERIFIABLE", severity="warning"),
        ]
        counts = apr._count_by_verdict(findings)
        assert counts["MATCH"] == 2
        assert counts["DRIFT"] == 1
        assert counts["FABRICATED"] == 1
        assert counts["MISSING"] == 1
        assert counts["UNVERIFIABLE"] == 1


# ---------------------------------------------------------------------------
# _parity_score
# ---------------------------------------------------------------------------

class TestParityScore:
    def test_all_match(self):
        counts = {"MATCH": 10, "DRIFT": 0, "FABRICATED": 0, "MISSING": 0, "UNVERIFIABLE": 0}
        assert apr._parity_score(counts) == 1.0

    def test_all_drift(self):
        counts = {"MATCH": 0, "DRIFT": 5, "FABRICATED": 0, "MISSING": 0, "UNVERIFIABLE": 0}
        assert apr._parity_score(counts) == 0.0

    def test_zero_denominator(self):
        # Only MISSING and UNVERIFIABLE — denominator is 0 → score 0.0
        counts = {"MATCH": 0, "DRIFT": 0, "FABRICATED": 0, "MISSING": 3, "UNVERIFIABLE": 2}
        assert apr._parity_score(counts) == 0.0

    def test_mixed(self):
        counts = {"MATCH": 8, "DRIFT": 1, "FABRICATED": 1, "MISSING": 2, "UNVERIFIABLE": 3}
        # 8 / (8+1+1) = 0.8; MISSING and UNVERIFIABLE excluded from denominator
        assert abs(apr._parity_score(counts) - 0.8) < 1e-9

    def test_unverifiable_excluded_from_denominator(self):
        # 5 MATCH, 5 UNVERIFIABLE → denominator = 5+0+0 = 5 → score 1.0
        counts = {"MATCH": 5, "DRIFT": 0, "FABRICATED": 0, "MISSING": 0, "UNVERIFIABLE": 5}
        assert apr._parity_score(counts) == 1.0

    def test_missing_excluded_from_denominator(self):
        counts = {"MATCH": 3, "DRIFT": 0, "FABRICATED": 0, "MISSING": 10, "UNVERIFIABLE": 0}
        assert apr._parity_score(counts) == 1.0


# ---------------------------------------------------------------------------
# _result
# ---------------------------------------------------------------------------

class TestResult:
    def test_pass_when_no_drift_no_fabricated(self):
        counts = {"MATCH": 5, "DRIFT": 0, "FABRICATED": 0, "MISSING": 2, "UNVERIFIABLE": 1}
        assert apr._result(counts) == "PASS"

    def test_fail_when_drift(self):
        counts = {"MATCH": 5, "DRIFT": 1, "FABRICATED": 0, "MISSING": 0, "UNVERIFIABLE": 0}
        assert apr._result(counts) == "FAIL"

    def test_fail_when_fabricated(self):
        counts = {"MATCH": 5, "DRIFT": 0, "FABRICATED": 1, "MISSING": 0, "UNVERIFIABLE": 0}
        assert apr._result(counts) == "FAIL"

    def test_missing_alone_does_not_fail(self):
        counts = {"MATCH": 0, "DRIFT": 0, "FABRICATED": 0, "MISSING": 10, "UNVERIFIABLE": 0}
        assert apr._result(counts) == "PASS"

    def test_unverifiable_alone_does_not_fail(self):
        counts = {"MATCH": 0, "DRIFT": 0, "FABRICATED": 0, "MISSING": 0, "UNVERIFIABLE": 10}
        assert apr._result(counts) == "PASS"


# ---------------------------------------------------------------------------
# assemble() — report structure
# ---------------------------------------------------------------------------

class TestAssemble:
    def _run(self, findings, **kw):
        data = _make_verdicts(findings, **kw)
        return apr.assemble(data, PROJECT_ROOT)

    def test_frontmatter_present(self):
        report = self._run([_make_finding("MATCH")])
        assert report.startswith("---")
        assert "parity_score:" in report
        assert "result:" in report

    def test_pass_result_in_frontmatter(self):
        report = self._run([_make_finding("MATCH")])
        assert "result: PASS" in report

    def test_fail_result_when_drift(self):
        report = self._run([_make_finding("DRIFT")])
        assert "result: FAIL" in report

    def test_fail_result_when_fabricated(self):
        report = self._run([_make_finding("FABRICATED")])
        assert "result: FAIL" in report

    def test_pass_when_only_missing(self):
        report = self._run([_make_finding("MISSING", severity="warning")])
        assert "result: PASS" in report

    def test_pass_when_only_unverifiable(self):
        report = self._run([_make_finding("UNVERIFIABLE", severity="warning")])
        assert "result: PASS" in report

    def test_critical_section_rendered(self):
        report = self._run([_make_finding("DRIFT")])
        assert "## Critical" in report
        assert "DRIFT" in report
        assert "C1:" in report

    def test_warning_section_rendered(self):
        report = self._run([_make_finding("MISSING", severity="warning")])
        assert "## Warning" in report
        assert "MISSING" in report
        assert "W1:" in report

    def test_match_section_rolled_up(self):
        report = self._run([_make_finding("MATCH"), _make_finding("MATCH", field="handler")])
        assert "## Verified (MATCH)" in report
        assert "✓" in report

    def test_none_placeholder_when_no_criticals(self):
        report = self._run([_make_finding("MATCH")])
        # Critical section should show "(none)"
        assert "_(none)_" in report

    def test_none_placeholder_when_no_warnings(self):
        report = self._run([_make_finding("DRIFT")])
        # Warning section should show "(none)"
        assert "_(none)_" in report

    def test_summary_table_counts(self):
        findings = [
            _make_finding("MATCH"),
            _make_finding("DRIFT"),
            _make_finding("FABRICATED"),
            _make_finding("MISSING", severity="warning"),
            _make_finding("UNVERIFIABLE", severity="warning"),
        ]
        report = self._run(findings)
        assert "| MATCH | 1 |" in report
        assert "| DRIFT | 1 |" in report
        assert "| FABRICATED | 1 |" in report
        assert "| MISSING | 1 |" in report
        assert "| UNVERIFIABLE | 1 |" in report

    def test_metrics_section(self):
        report = self._run([_make_finding("MATCH")])
        assert "## Metrics" in report
        assert "Parity score" in report
        assert "Features audited" in report

    def test_parity_score_formatted(self):
        # 1 MATCH → score 1.0 → "100.0%" in metrics
        report = self._run([_make_finding("MATCH")])
        assert "100.0%" in report

    def test_four_faces_in_critical_finding(self):
        report = self._run([_make_finding("DRIFT", doc_says="admin only",
                                          code_reality="no role check")])
        assert "**Doc**:" in report
        assert "**Doc says**:" in report
        assert "**Code reality**:" in report
        assert "**Verdict**:" in report

    def test_unadjudicated_drift_still_rendered(self, capsys):
        # Iron Law #3: renders but emits stderr warning
        report = self._run([_make_finding("DRIFT", adjudicated=False)])
        assert "DRIFT" in report
        captured = capsys.readouterr()
        assert "adjudicated" in captured.err.lower() or "iron law" in captured.err.lower()


# ---------------------------------------------------------------------------
# main() CLI — roundtrip
# ---------------------------------------------------------------------------

class TestMainCli:
    def test_roundtrip(self, tmp_path):
        verdicts_path = tmp_path / "verdicts.json"
        out_path = tmp_path / "parity-report.md"
        findings = [
            _make_finding("MATCH"),
            _make_finding("DRIFT"),
            _make_finding("MISSING", severity="warning"),
        ]
        verdicts_path.write_text(
            json.dumps(_make_verdicts(findings, project="myapp")), encoding="utf-8"
        )
        rc = apr.main([
            "--verdicts", str(verdicts_path),
            "--out", str(out_path),
            "--project-root", str(PROJECT_ROOT),
        ])
        assert rc == 0
        assert out_path.is_file()
        content = out_path.read_text(encoding="utf-8")
        assert "result: FAIL" in content
        assert "myapp" in content

    def test_missing_verdicts_file_returns_2(self, tmp_path):
        rc = apr.main([
            "--verdicts", str(tmp_path / "nonexistent.json"),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 2

    def test_atomic_write_no_partial(self, tmp_path):
        # Verify .tmp file is cleaned up (os.replace used)
        verdicts_path = tmp_path / "verdicts.json"
        out_path = tmp_path / "parity-report.md"
        verdicts_path.write_text(
            json.dumps(_make_verdicts([_make_finding("MATCH")])), encoding="utf-8"
        )
        apr.main(["--verdicts", str(verdicts_path), "--out", str(out_path)])
        tmp_file = out_path.with_suffix(".tmp")
        assert not tmp_file.exists()
        assert out_path.exists()
