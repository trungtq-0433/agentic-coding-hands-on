"""Unit tests for _file_schema_lib.py (shared vocab + populated-schema detection)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _file_schema_lib import (  # noqa: E402
    FILE_EXCHANGE_VOCAB,
    has_populated_file_schema,
    is_file_exchange,
)

# ---------------------------------------------------------------------------
# is_file_exchange — vocab match
# ---------------------------------------------------------------------------

def test_vocab_matches_import():
    assert is_file_exchange("This algorithm handles CSV import of orders.") is True


def test_vocab_matches_export_case_insensitive():
    assert is_file_exchange("EXPORT the report to XLSX") is True


def test_vocab_matches_upload():
    assert is_file_exchange("Bulk upload of product catalog") is True


def test_vocab_matches_download():
    assert is_file_exchange("Users can download their invoice history") is True


def test_vocab_no_match_plain_text():
    assert is_file_exchange("Validates the user's password and returns a token.") is False


def test_important_substring_not_matched():
    """'important' must NOT match \\bimport\\b — no boundary after 'import' inside it."""
    assert is_file_exchange("This is important business logic for the order flow.") is False


def test_reporting_substring_not_matched():
    """'reporting' must NOT match \\bport\\b or \\bimport\\b substrings."""
    assert is_file_exchange("Generates a reporting dashboard summary.") is False


def test_vocab_constant_contains_expected_words():
    assert FILE_EXCHANGE_VOCAB == {
        "import", "export", "csv", "xlsx", "upload", "download", "bulk",
    }


# ---------------------------------------------------------------------------
# has_populated_file_schema — populated vs vague vs N/A
# ---------------------------------------------------------------------------

POPULATED_BODY = """\
**Input:** CSV file upload
**Output:** created order count
**File Schema**: | Column | Type | Required | Notes |
|--------|------|----------|-------|
| order_id | string | yes | Unique order identifier |
| sku | string | yes | Product SKU |
"""

VAGUE_PLACEHOLDER_BODY = """\
**Input:** CSV file upload
**Output:** created order count
**File Schema**: {`| Column | Type | Required | Notes |` table (or sheet-name + column-list per sheet for multi-sheet XLSX) — sourced from `validateHeader()`/schema-array/column-mapping | `N/A — not a file-exchange type`}
"""

NA_STRING_BODY = """\
**Input:** normalized user record
**Output:** validated profile
**File Schema**: N/A — not a file-exchange type
"""

NO_LABEL_BODY = """\
**Input:** normalized user record
**Output:** validated profile
"""

NA_MISUSE_BODY = """\
**Input:** CSV file of orders to import
**Output:** created order count
**File Schema**: N/A — not a file-exchange type
"""


def test_populated_table_detected():
    assert has_populated_file_schema(POPULATED_BODY) is True


def test_vague_placeholder_not_populated():
    assert has_populated_file_schema(VAGUE_PLACEHOLDER_BODY) is False


def test_na_string_not_populated():
    assert has_populated_file_schema(NA_STRING_BODY) is False


def test_missing_label_not_populated():
    assert has_populated_file_schema(NO_LABEL_BODY) is False


def test_na_misuse_case_not_populated():
    """Vocab-matching block using the N/A string anyway is a contradiction —
    has_populated_file_schema() treats it as not-populated so callers warn."""
    assert is_file_exchange(NA_MISUSE_BODY) is True
    assert has_populated_file_schema(NA_MISUSE_BODY) is False
