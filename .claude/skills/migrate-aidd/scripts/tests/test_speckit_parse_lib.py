"""Unit tests for speckit_parse_lib.py against the fixture speckit tree."""
from pathlib import Path

import pytest

from speckit_parse_lib import (
    _parse_research_sections,
    enumerate_features,
    find_constitution,
    parse_spec_md,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SPECS_DIR = FIXTURES_DIR / "specs"


class TestEnumerateFeatures:
    def test_finds_two_features(self):
        features = enumerate_features(str(SPECS_DIR))
        assert len(features) == 2

    def test_sorted_by_nnn(self):
        features = enumerate_features(str(SPECS_DIR))
        nnns = [f["nnn"] for f in features]
        assert nnns == sorted(nnns)

    def test_first_feature_nnn(self):
        features = enumerate_features(str(SPECS_DIR))
        assert features[0]["nnn"] == "001"

    def test_first_feature_slug(self):
        features = enumerate_features(str(SPECS_DIR))
        assert features[0]["slug"] == "create-taskify"

    def test_second_feature_slug(self):
        features = enumerate_features(str(SPECS_DIR))
        assert features[1]["slug"] == "add-auth"

    def test_has_spec_true_for_001(self):
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["has_spec"] is True

    def test_has_data_model_true_for_001(self):
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["has_data_model"] is True

    def test_has_plan_false_for_001(self):
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["has_plan"] is False

    def test_has_contracts_false_for_001(self):
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["has_contracts"] is False

    def test_contracts_src_none_when_absent(self):
        """P04: contracts_src is None when contracts/ dir is absent."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["contracts_src"] is None

    def test_has_contracts_true_for_002(self):
        """P04: 002-add-auth fixture has a contracts/ dir."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "002")
        assert feat["has_contracts"] is True

    def test_contracts_src_path_for_002(self):
        """P04: contracts_src records absolute path to contracts/ for 002."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "002")
        assert feat["contracts_src"] is not None
        contracts_path = Path(feat["contracts_src"])
        assert contracts_path.is_dir()
        assert contracts_path.name == "contracts"
        assert (contracts_path / "openapi.yaml").is_file()

    def test_has_research_false_for_001(self):
        """P05: 001-create-taskify has no research.md."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "001")
        assert feat["has_research"] is False
        assert feat["research_src"] is None
        assert feat["research_sections"] == []

    def test_has_research_true_for_002(self):
        """P05: 002-add-auth fixture has research.md."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "002")
        assert feat["has_research"] is True

    def test_research_src_path_for_002(self):
        """P05: research_src records absolute path to research.md for 002."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "002")
        assert feat["research_src"] is not None
        assert Path(feat["research_src"]).is_file()
        assert Path(feat["research_src"]).name == "research.md"

    def test_research_sections_for_002(self):
        """P05: research_sections lists H2 headings from research.md for spec-URI anchors."""
        features = enumerate_features(str(SPECS_DIR))
        feat = next(f for f in features if f["nnn"] == "002")
        sections = feat["research_sections"]
        assert isinstance(sections, list)
        assert len(sections) >= 3
        assert "Authentication Strategy" in sections
        assert "PKCE Flow" in sections
        assert "Session Storage" in sections

    def test_empty_dir_returns_empty_list(self, tmp_path):
        assert enumerate_features(str(tmp_path)) == []

    def test_nonexistent_dir_returns_empty_list(self):
        assert enumerate_features("/nonexistent/path/xyz") == []


class TestParseSpecMd:
    def test_us_count_for_001(self):
        path = SPECS_DIR / "001-create-taskify" / "spec.md"
        result = parse_spec_md(str(path))
        assert result["us_count"] == 2

    def test_fr_count_for_001(self):
        path = SPECS_DIR / "001-create-taskify" / "spec.md"
        result = parse_spec_md(str(path))
        assert result["fr_count"] == 2

    def test_title_for_001(self):
        path = SPECS_DIR / "001-create-taskify" / "spec.md"
        result = parse_spec_md(str(path))
        assert result["title"] == "Create Taskify"

    def test_us_count_for_002(self):
        path = SPECS_DIR / "002-add-auth" / "spec.md"
        result = parse_spec_md(str(path))
        assert result["us_count"] == 2

    def test_fr_count_for_002(self):
        path = SPECS_DIR / "002-add-auth" / "spec.md"
        result = parse_spec_md(str(path))
        assert result["fr_count"] == 2

    def test_missing_file_returns_zeros(self):
        result = parse_spec_md("/nonexistent/spec.md")
        assert result == {"title": "", "us_count": 0, "fr_count": 0}

    def test_empty_file_returns_zeros(self, tmp_path):
        p = tmp_path / "spec.md"
        p.write_text("")
        result = parse_spec_md(str(p))
        assert result["us_count"] == 0
        assert result["fr_count"] == 0


class TestParseResearchSections:
    """P05: _parse_research_sections extracts H2 headings for spec-URI anchors."""

    def test_returns_h2_headings_from_fixture(self):
        path = str(SPECS_DIR / "002-add-auth" / "research.md")
        sections = _parse_research_sections(path)
        assert "Authentication Strategy" in sections
        assert "PKCE Flow" in sections
        assert "Session Storage" in sections

    def test_returns_empty_list_for_missing_file(self):
        sections = _parse_research_sections("/nonexistent/research.md")
        assert sections == []

    def test_returns_empty_list_for_none_path(self):
        sections = _parse_research_sections(None)
        assert sections == []

    def test_returns_empty_list_for_file_with_no_h2(self, tmp_path):
        p = tmp_path / "research.md"
        p.write_text("# Title\nSome content\n### H3 ignored\n")
        sections = _parse_research_sections(str(p))
        assert sections == []

    def test_strips_trailing_whitespace_from_heading(self, tmp_path):
        p = tmp_path / "research.md"
        p.write_text("## My Section  \n\ncontent\n")
        sections = _parse_research_sections(str(p))
        assert sections == ["My Section"]


class TestFindConstitution:
    def test_finds_specify_memory_constitution(self):
        repo_root = str(FIXTURES_DIR)
        specs_root = str(SPECS_DIR)
        path = find_constitution(repo_root, specs_root)
        assert path is not None
        assert path.endswith("constitution.md")

    def test_returns_none_when_missing(self, tmp_path):
        specs = tmp_path / "specs"
        specs.mkdir()
        result = find_constitution(str(tmp_path), str(specs))
        assert result is None
