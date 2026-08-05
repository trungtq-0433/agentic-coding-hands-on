"""Tests for extensions/api/build_api_design.py (_csafe Excel formula injection gate).

Tests that _csafe prefixes single quote to values starting with =+-@ and leaves others unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REBUILD_SPEC_ROOT = SCRIPTS_DIR.parent
EXTENSIONS_API = REBUILD_SPEC_ROOT / "extensions" / "api"
sys.path.insert(0, str(EXTENSIONS_API))
sys.path.insert(0, str(SCRIPTS_DIR))

# build_api_design imports openpyxl at module load. CI installs pytest only
# (the kit venv ships openpyxl); skip cleanly where the optional extension dep
# is absent so a missing import never aborts collection for the whole suite.
pytest.importorskip("openpyxl")

from build_api_design import _csafe  # noqa: E402


class TestCsafeFormulaInjectionGate:
    def test_csafe_prefix_equals_sign(self):
        """Regression: string starting with = is prefixed with single quote."""
        result = _csafe("=HYPERLINK(\"http://example.com\")")
        assert result.startswith("'")
        assert result == "'=HYPERLINK(\"http://example.com\")"

    def test_csafe_prefix_plus_sign(self):
        """Regression: string starting with + is prefixed with single quote."""
        result = _csafe("+1234567890")
        assert result.startswith("'")
        assert result == "'+1234567890"

    def test_csafe_prefix_minus_sign(self):
        """Regression: string starting with - is prefixed with single quote."""
        result = _csafe("-500")
        assert result.startswith("'")
        assert result == "'-500"

    def test_csafe_prefix_at_sign(self):
        """Regression: string starting with @ is prefixed with single quote."""
        result = _csafe("@indirect(\"A1\")")
        assert result.startswith("'")
        assert result == "'@indirect(\"A1\")"

    def test_csafe_plain_string_unchanged(self):
        """Regression guard: plain string without formula chars is unchanged."""
        result = _csafe("plain text")
        assert result == "plain text"
        assert not result.startswith("'")

    def test_csafe_alphanumeric_unchanged(self):
        """Regression guard: alphanumeric strings unchanged."""
        result = _csafe("Hello123")
        assert result == "Hello123"

    def test_csafe_string_starting_with_space_unchanged(self):
        """Regression guard: string starting with space is unchanged."""
        result = _csafe(" +formula")
        assert result == " +formula"
        # Not prefixed because first char is space, not +

    def test_csafe_empty_string_unchanged(self):
        """Regression guard: empty string unchanged."""
        result = _csafe("")
        assert result == ""

    def test_csafe_integer_unchanged(self):
        """Regression guard: non-string values pass through unchanged."""
        result = _csafe(42)
        assert result == 42

    def test_csafe_float_unchanged(self):
        """Regression guard: float values unchanged."""
        result = _csafe(3.14)
        assert result == 3.14

    def test_csafe_none_unchanged(self):
        """Regression guard: None value unchanged."""
        result = _csafe(None)
        assert result is None

    def test_csafe_boolean_unchanged(self):
        """Regression guard: boolean values unchanged."""
        result_true = _csafe(True)
        assert result_true is True
        result_false = _csafe(False)
        assert result_false is False

    def test_csafe_list_unchanged(self):
        """Regression guard: list unchanged."""
        test_list = ["a", "b"]
        result = _csafe(test_list)
        assert result == test_list

    def test_csafe_string_with_formula_in_middle_unchanged(self):
        """Regression guard: = in middle of string is NOT prefixed."""
        result = _csafe("URL=http://example.com")
        assert result == "URL=http://example.com"
        # Not prefixed because first char is not =
