"""Tests for Phase 05 — the result-rule truth table + per-engine anchor gate + loud coverage_status."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import assemble_judgment_report as asm  # noqa: E402
import estimate_judgment_run as est  # noqa: E402


def _cov(*, orphans=None, phantoms=None, duplicates=None, coverage_status="OK",
         orphan_status="OK", phantoms_unverifiable=None):
    return {"coverage_status": coverage_status, "orphan_status": orphan_status,
            "orphans": orphans or [], "phantoms": phantoms or [],
            "duplicates": duplicates or [], "phantoms_unverifiable": phantoms_unverifiable or [],
            "graph_state": {"status": "OK", "note": ""}}


def _fm(report_text: str) -> dict:
    fm = {}
    m = re.search(r"^---\n(.*?)\n---", report_text, re.S)
    for line in m.group(1).splitlines():
        k, _, rest = line.partition(":")
        val = rest.split("#")[0].strip()
        fm[k.strip()] = val
    return fm


class TestResultRule:
    def test_one_orphan_fails(self):
        cov = _cov(orphans=[{"kind": "ORPHAN", "source_file": "a.py", "evidence": "x"}])
        report, data = asm.assemble(cov, {}, {}, "all")
        assert data["result"] == "FAIL" and data["orphans"] == 1

    def test_one_phantom_fails(self):
        cov = _cov(phantoms=[{"kind": "PHANTOM", "source_file": "g.py", "evidence": "x"}])
        _r, data = asm.assemble(cov, {}, {}, "all")
        assert data["result"] == "FAIL" and data["phantoms"] == 1

    def test_one_duplicate_fails(self):
        cov = _cov(duplicates=[{"kind": "DUP_ARTIFACT", "paths": ["a", "b"], "evidence": "x"}])
        _r, data = asm.assemble(cov, {}, {}, "all")
        assert data["result"] == "FAIL" and data["redundancy"] == 1

    def test_ten_warns_still_pass(self):
        boundary = {"boundary_status": "OK", "findings": [
            {"engine": "boundary", "kind": "OVER_MERGE", "verdict": "WARN", "clause": "c",
             "evidence": "e", "screen": f"SCR{i}"} for i in range(10)]}
        _r, data = asm.assemble(_cov(), boundary, {}, "all")
        assert data["result"] == "PASS" and data["boundary_warn"] == 10

    def test_no_graph_unverifiable_but_pass(self):
        cov = _cov(coverage_status="UNVERIFIABLE", orphan_status="UNVERIFIABLE")
        _r, data = asm.assemble(cov, {}, {}, "all")
        assert data["result"] == "PASS" and data["coverage_status"] == "UNVERIFIABLE"

    def test_strict_coverage_fail(self):
        cov = _cov(coverage_status="FAIL")
        _r, data = asm.assemble(cov, {}, {}, "all")
        assert data["result"] == "FAIL"

    def test_frontmatter_parses_from_report(self):
        cov = _cov(orphans=[{"kind": "ORPHAN", "source_file": "a.py", "evidence": "x"}])
        report, _data = asm.assemble(cov, {}, {}, "all")
        fm = _fm(report)
        assert fm["result"] == "FAIL" and fm["orphans"] == "1" and fm["coverage_status"] == "OK"


class TestAnchorGate:
    def test_engine1_without_evidence_dropped(self):
        cov = _cov(orphans=[{"kind": "ORPHAN", "source_file": "a.py"}])  # no evidence
        _r, data = asm.assemble(cov, {}, {}, "all")
        assert data["orphans"] == 0
        assert any("no evidence anchor" in m for m in data["_gate_log"])

    def test_engine3_without_adjudicated_dropped(self):
        judgment = {"judgment_status": "OK", "findings": [
            {"engine": "judgment", "kind": "UNSUPPORTED", "verdict": "WARN",
             "anchor": "a", "adjudicated": False, "target": "t"}]}
        _r, data = asm.assemble(_cov(), {}, judgment, "all")
        assert data["inference_warn"] == 0
        assert any("adjudicated=true" in m for m in data["_gate_log"])

    def test_engine3_adjudicated_kept(self):
        judgment = {"judgment_status": "OK", "findings": [
            {"engine": "judgment", "kind": "UNSUPPORTED", "verdict": "WARN",
             "anchor": "a", "adjudicated": True, "target": "t"}]}
        _r, data = asm.assemble(_cov(), {}, judgment, "all")
        assert data["inference_warn"] == 1

    def test_no_stochastic_signal_increments_fail_counts(self):
        # A boundary MISSING_US and a judgment UNSUPPORTED must NOT touch orphans/phantoms/redundancy.
        boundary = {"findings": [{"engine": "boundary", "kind": "MISSING_US", "verdict": "WARN",
                                  "clause": "c", "evidence": "e", "screen": "S"}]}
        judgment = {"findings": [{"engine": "judgment", "kind": "UNSUPPORTED", "verdict": "WARN",
                                  "anchor": "a", "adjudicated": True, "target": "t"}]}
        _r, data = asm.assemble(_cov(), boundary, judgment, "all")
        assert data["orphans"] == 0 and data["phantoms"] == 0 and data["redundancy"] == 0
        assert data["result"] == "PASS"


class TestStatusPropagation:
    def test_partial_judgment_status_surfaced(self):
        judgment = {"judgment_status": "PARTIAL", "findings": []}
        _r, data = asm.assemble(_cov(), {}, judgment, "all")
        assert data["judgment_status"] == "PARTIAL"


class TestEstimate:
    def test_scope_all_no_bypass(self, tmp_path):
        (tmp_path / "docs" / "generated").mkdir(parents=True)
        (tmp_path / "docs" / "generated" / "user-stories.md").write_text("x", encoding="utf-8")
        r = est.estimate(tmp_path, "all", None, None)
        assert r["bypass_gate"] is False

    def test_single_scope_bypasses(self, tmp_path):
        (tmp_path / "docs" / "generated").mkdir(parents=True)
        r = est.estimate(tmp_path, "user-stories", None, None)
        assert r["bypass_gate"] is True
