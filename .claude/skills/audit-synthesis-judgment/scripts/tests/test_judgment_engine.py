"""Tests for Engine 3 — granularity stat, prepare extraction, assemble survival/accounting."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import _granularity_lib as gran  # noqa: E402
import judgment_engine as je  # noqa: E402


# --------------------------------------------------------------- granularity
class TestGranularity:
    def test_outlier_flagged(self):
        metrics = {f"F{i:03d}": 5.0 for i in range(10)}
        metrics["F999"] = 200.0
        res = gran.find_outliers(metrics)
        assert any(o["feature"] == "F999" and o["direction"] == "coarse" for o in res["outliers"])

    def test_uniform_set_clean(self):
        metrics = {f"F{i:03d}": 5.0 for i in range(10)}
        res = gran.find_outliers(metrics)
        assert res["outliers"] == []

    def test_too_few_features_no_signal(self):
        res = gran.find_outliers({"F001": 1.0, "F002": 99.0})
        assert res["outliers"] == []


# --------------------------------------------------------------- prepare
class TestPrepare:
    def _corpus(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "generated").mkdir(parents=True)
        (docs / "system").mkdir(parents=True)
        (docs / "generated" / "user-stories.md").write_text(
            "## US001_Create: Create Order\n\nAs a user, I want to create an order "
            "so that I can track my purchases.\n", encoding="utf-8")
        (docs / "system" / "design-intent.md").write_text(
            "# Design Intent\n\n[INFERRED] The system uses soft-delete across all models to "
            "preserve an audit trail, though no ADR documents this.\n\n"
            "This paragraph merely restates the business-rules content about order lifecycle "
            "without adding any new rationale about why the lifecycle is shaped this way at all here.\n",
            encoding="utf-8")
        return tmp_path

    def test_extracts_inference_and_restatement(self, tmp_path):
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        dims = {c["dimension"] for c in res["candidates"]}
        assert "inference-validity" in dims
        assert "restates-w/o-why" in dims
        assert "naming" in dims

    def test_so_that_extracted(self, tmp_path):
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        inf = [c for c in res["candidates"] if c["dimension"] == "inference-validity"]
        assert any("so that" in c["text"] for c in inf)

    def test_design_intent_flagged_experimental(self, tmp_path):
        root = self._corpus(tmp_path)
        res = je.prepare(root, "all", None, None)
        di = [c for c in res["candidates"] if c["target"] == "design-intent"]
        assert di and all(c["experimental"] for c in di)

    def test_citation_adjacent_paragraph_exempt(self, tmp_path):
        docs = tmp_path / "docs" / "system"
        docs.mkdir(parents=True)
        docs.joinpath("design-intent.md").write_text(
            "# DI\n\nThis long paragraph cites its source and therefore must be exempt from the "
            "restatement judge because it is a mandated quote. **Source:** `docs/decisions/ADR-001.md`\n",
            encoding="utf-8")
        res = je.prepare(tmp_path, "design-intent", None, None)
        assert [c for c in res["candidates"] if c["dimension"] == "restates-w/o-why"] == []


# --------------------------------------------------------------- assemble
def _cand(cid, dim, verdict="WARN", refutations=None, confidence=0.9, anchor="a computed anchor",
          experimental=False):
    c = {"id": cid, "dimension": dim, "verdict": verdict, "confidence": confidence,
         "anchor": anchor, "experimental": experimental, "target": cid, "text": "x"}
    if refutations is not None:
        c["refutations"] = refutations
    return c


class TestAssemble:
    def test_survives_majority_refutation(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity",
                  refutations=[{"refuted": False}, {"refuted": False}, {"refuted": True}])]}
        res = je.assemble(judged, "medium")
        assert len(res["findings"]) == 1 and res["findings"][0]["adjudicated"] is True
        assert res["judgment_status"] == "OK"

    def test_refuted_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity",
                  refutations=[{"refuted": True}, {"refuted": True}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []
        assert any("refutation" in d["reason"] for d in res["dropped"])

    def test_no_anchor_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", anchor="",
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []
        assert any("anchor" in d["reason"] for d in res["dropped"])

    def test_low_confidence_dropped(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", confidence=0.3,
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert res["findings"] == []

    def test_single_refuter_only_at_low(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", refutations=[{"refuted": False}])]}
        assert len(je.assemble(judged, "low")["findings"]) == 1     # low: single refuter OK
        assert je.assemble(judged, "medium")["findings"] == []      # medium: needs ≥2

    def test_dead_subagent_is_partial_not_clean(self):
        judged = {"expected_count": 2, "candidates": [
            _cand("i1", "inference-validity", refutations=[{"refuted": False}, {"refuted": False}]),
            {"id": "i2", "dimension": "naming", "anchor": "a"}]}  # no verdict → judge died
        res = je.assemble(judged, "medium")
        assert res["judgment_status"] == "PARTIAL"
        assert res["returned"] == 1 and res["expected"] == 2

    def test_all_dead_is_failed(self):
        judged = {"expected_count": 2, "candidates": [
            {"id": "i1", "dimension": "naming", "anchor": "a"},
            {"id": "i2", "dimension": "naming", "anchor": "a"}]}
        assert je.assemble(judged, "medium")["judgment_status"] == "FAILED"

    def test_engine3_never_fail_verdict(self):
        judged = {"expected_count": 1, "candidates": [
            _cand("i1", "inference-validity", experimental=True,
                  refutations=[{"refuted": False}, {"refuted": False}])]}
        res = je.assemble(judged, "medium")
        assert all(f["verdict"] == "WARN" for f in res["findings"])
        assert all(f["experimental"] for f in res["findings"])
