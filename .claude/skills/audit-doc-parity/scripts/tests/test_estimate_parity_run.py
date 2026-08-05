"""Tests for estimate_parity_run.py."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import estimate_parity_run as epr

FIXTURES = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# estimate() function
# ---------------------------------------------------------------------------

class TestEstimate:
    def test_no_docs_returns_zero_units(self, tmp_path):
        result = epr.estimate(tmp_path)
        assert result["units"] == 0
        assert result["cited_loc"] == 0
        assert result["bypass_gate"] is False

    def test_counts_feature_units(self, tmp_path):
        docs = tmp_path / "docs" / "features"
        for slug in ("F001_Foo", "F002_Bar"):
            d = docs / slug
            d.mkdir(parents=True)
            (d / "technical-spec.md").write_text("no citations\n")
        result = epr.estimate(tmp_path)
        assert result["units"] == 2

    def test_cited_loc_sum(self, tmp_path):
        docs = tmp_path / "docs" / "features" / "F001_Test"
        docs.mkdir(parents=True)
        # Write a doc with a citation spanning 10 lines
        (docs / "technical-spec.md").write_text(
            "**Source:** `src/app.py:1-10`\n"
        )
        result = epr.estimate(tmp_path)
        assert result["cited_loc"] == 10

    def test_feature_filter_sets_bypass(self, tmp_path):
        docs = tmp_path / "docs" / "features" / "F001_Test"
        docs.mkdir(parents=True)
        (docs / "technical-spec.md").write_text("no citations\n")
        result = epr.estimate(tmp_path, feature_filter="F001")
        assert result["bypass_gate"] is True

    def test_path_filter_sets_bypass(self, tmp_path):
        doc = tmp_path / "single.md"
        doc.write_text("no citations\n")
        result = epr.estimate(tmp_path, path_filter=doc)
        assert result["bypass_gate"] is True
        assert result["units"] == 1

    def test_system_docs_included_when_feature_filter(self, tmp_path):
        # System docs SHOULD appear even when --feature is set,
        # mirroring scope_doc_units._discover_doc_paths behavior (M1 alignment).
        docs_feat = tmp_path / "docs" / "features" / "F001_Test"
        docs_feat.mkdir(parents=True)
        (docs_feat / "technical-spec.md").write_text("x\n")
        docs_sys = tmp_path / "docs" / "generated"
        docs_sys.mkdir(parents=True)
        (docs_sys / "api-contracts.md").write_text("y\n")
        result = epr.estimate(tmp_path, feature_filter="F001")
        # 1 feature unit + 1 system doc = 2
        assert result["units"] == 2

    def test_est_agents_nonzero_when_units_present(self, tmp_path):
        docs = tmp_path / "docs" / "features" / "F001_Test"
        docs.mkdir(parents=True)
        (docs / "technical-spec.md").write_text("no citations\n")
        result = epr.estimate(tmp_path)
        assert result["est_agents"] >= 1

    def test_reason_in_output(self, tmp_path):
        result = epr.estimate(tmp_path)
        assert "reason" in result
        assert isinstance(result["reason"], str)


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------

class TestMain:
    def test_exit_zero_always(self, tmp_path):
        rc = epr.main(["--project-root", str(tmp_path)])
        assert rc == 0

    def test_outputs_valid_json(self, tmp_path, capsys):
        epr.main(["--project-root", str(tmp_path)])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "units" in data
        assert "cited_loc" in data
        assert "est_agents" in data
        assert "bypass_gate" in data
        assert "reason" in data

    def test_feature_flag_reflected(self, tmp_path, capsys):
        docs = tmp_path / "docs" / "features" / "F001_Test"
        docs.mkdir(parents=True)
        (docs / "technical-spec.md").write_text("no citations\n")
        epr.main(["--project-root", str(tmp_path), "--feature", "F001"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["bypass_gate"] is True

    def test_path_flag_reflected(self, tmp_path, capsys):
        doc = tmp_path / "single.md"
        doc.write_text("**Source:** `x.py:1-5`\n")
        epr.main(["--project-root", str(tmp_path), "--path", str(doc)])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["bypass_gate"] is True
        assert data["cited_loc"] == 5
