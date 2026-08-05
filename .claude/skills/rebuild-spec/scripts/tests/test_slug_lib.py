"""Tests for _slug_lib.py — derive_slug, is_valid_slug, load_canonical,
parse_feature_list_fallback. Coverage per phase-05 test matrix.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _slug_lib import (
    derive_slug,
    is_valid_slug,
    load_canonical,
    parse_feature_list_fallback,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ---------------------------------------------------------------------------
# derive_slug
# ---------------------------------------------------------------------------

class TestDeriveSlug:
    def test_simple_name(self):
        assert derive_slug("F001", "Authentication") == "F001_Authentication"

    def test_ampersand_replaced(self):
        # Slug grammar: each token → capitalize first char, lowercase rest.
        # Tokens: "User","Profile","And","Settings" → "User","Profile","And","Settings"
        assert derive_slug("F042", "User Profile & Settings") == "F042_UserProfileAndSettings"

    def test_slash_stripped(self):
        assert derive_slug("F015", "Order checkout / payment") == "F015_OrderCheckoutPayment"

    def test_digit_leading_token(self):
        # "2FA" → token "2fa" → capitalize first → "2fa" (digit, no change)
        assert derive_slug("F008", "2FA flow") == "F008_2faFlow"

    def test_hyphen_stripped(self):
        assert derive_slug("F022", "Reset-password (email)") == "F022_ResetPasswordEmail"

    def test_extra_spaces(self):
        assert derive_slug("F030", "Inventory  bulk   import") == "F030_InventoryBulkImport"

    def test_invalid_fcode_raises(self):
        with pytest.raises(ValueError, match="invalid fcode"):
            derive_slug("X001", "name")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty slug"):
            derive_slug("F001", "")

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValueError, match="empty slug"):
            derive_slug("F001", "   ")

    def test_punctuation_only_name_raises(self):
        with pytest.raises(ValueError, match="empty slug"):
            derive_slug("F001", "---")


# ---------------------------------------------------------------------------
# is_valid_slug
# ---------------------------------------------------------------------------

class TestIsValidSlug:
    def test_valid_short(self):
        assert is_valid_slug("F001_Auth") is True

    def test_valid_long(self):
        assert is_valid_slug("F999_UserProfileAndSettings") is True

    def test_two_digit_fcode_invalid(self):
        assert is_valid_slug("F1_Auth") is False

    def test_hyphen_in_name_invalid(self):
        assert is_valid_slug("F001_Bad-Slug") is False

    def test_space_in_name_invalid(self):
        assert is_valid_slug("F001_Bad Slug") is False

    def test_no_underscore_invalid(self):
        assert is_valid_slug("F001Auth") is False

    def test_lowercase_fcode_invalid(self):
        assert is_valid_slug("f001_Auth") is False


# ---------------------------------------------------------------------------
# load_canonical
# ---------------------------------------------------------------------------

class TestLoadCanonical:
    def test_returns_none_when_absent(self, tmp_path):
        assert load_canonical(tmp_path) is None

    def test_returns_dict_when_present(self):
        plan_dir = FIXTURES / "plan-good"
        result = load_canonical(plan_dir)
        assert isinstance(result, dict)
        assert "features" in result
        assert len(result["features"]) == 2

    def test_raises_on_malformed_json(self, tmp_path):
        artifacts = tmp_path / "artifacts"
        artifacts.mkdir()
        (artifacts / "_canonical-fcodes.json").write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="malformed JSON"):
            load_canonical(tmp_path)

    def test_feature_slugs_match_expected(self):
        plan_dir = FIXTURES / "plan-good"
        result = load_canonical(plan_dir)
        slugs = [f["slug"] for f in result["features"]]
        assert "F001_Auth" in slugs
        assert "F002_Search" in slugs


# ---------------------------------------------------------------------------
# parse_feature_list_fallback
# ---------------------------------------------------------------------------

class TestParseFeatureListFallback:
    def test_extracts_rows_from_well_formed_list(self):
        flist = FIXTURES / "plan-good" / "artifacts" / "feature-list.md"
        result = parse_feature_list_fallback(flist)
        assert len(result) == 2
        slugs = [f["slug"] for f in result]
        assert "F001_Auth" in slugs
        assert "F002_Search" in slugs

    def test_returns_empty_when_file_absent(self, tmp_path):
        result = parse_feature_list_fallback(tmp_path / "nonexistent.md")
        assert result == []

    def test_result_sorted_by_fcode(self):
        flist = FIXTURES / "plan-good" / "artifacts" / "feature-list.md"
        result = parse_feature_list_fallback(flist)
        fcodes = [f["fcode"] for f in result]
        assert fcodes == sorted(fcodes)

    def test_no_duplicates(self):
        flist = FIXTURES / "plan-good" / "artifacts" / "feature-list.md"
        result = parse_feature_list_fallback(flist)
        slugs = [f["slug"] for f in result]
        assert len(slugs) == len(set(slugs))

    def test_legacy_plan_without_canonical(self):
        flist = FIXTURES / "plan-legacy-no-canonical" / "artifacts" / "feature-list.md"
        result = parse_feature_list_fallback(flist)
        assert len(result) == 1
        assert result[0]["slug"] == "F001_Auth"
