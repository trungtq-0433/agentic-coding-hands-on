"""Tests for _shared_attribution_lib.py (Phase 05 — deterministic DB attribution)."""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _shared_attribution_lib as attr  # noqa: E402


class TestMatchesModuleLabel:
    def test_full_segment_match(self):
        assert attr.matches_module_label("DB/TABLE/POS/M_POS_HEAD.sql:5", "POS") is True

    def test_substring_not_a_segment_rejected(self):
        # The POS⊂POSDEN bug: POS must NOT match POSDEN.
        assert attr.matches_module_label("DB/TABLE/POSDEN/x.sql:1", "POS") is False

    def test_filename_substring_rejected(self):
        # "POS" appears inside the filename but is not a directory segment.
        assert attr.matches_module_label("DB/TABLE/RSV/M_POS_BACKUP.sql", "POS") is False

    def test_strips_line_locator(self):
        assert attr.matches_module_label("DB/SP/RSV/P_RSV.pks:42", "RSV") is True

    def test_windows_separators(self):
        assert attr.matches_module_label("DB\\TABLE\\POS\\x.sql", "POS") is True

    def test_empty_label_false(self):
        assert attr.matches_module_label("DB/TABLE/POS/x.sql", "") is False


class TestFilterSharedDigest:
    def _digest(self):
        return {
            "extractor": "extract_sql_schema",
            "db_objects": [
                {"kind": "table", "name": "M_POS_HEAD", "citation": "DB/TABLE/POS/M_POS_HEAD.sql:1"},
                {"kind": "table", "name": "M_RSV", "citation": "DB/TABLE/RSV/M_RSV.sql:1"},
                {"kind": "package", "name": "P_POS", "citation": "DB/SP/POS/P_POS.pks:1"},
                {"kind": "table", "name": "M_POSDEN", "citation": "DB/TABLE/POSDEN/x.sql:1"},
            ],
            "warnings": [],
        }

    def test_pos_view_only_pos(self):
        out = attr.filter_shared_digest_by_label(self._digest(), "POS")
        names = {o["name"] for o in out["db_objects"]}
        assert names == {"M_POS_HEAD", "P_POS"}        # POSDEN excluded (full-segment)
        assert out["filtered_for_label"] == "POS"

    def test_rsv_view_only_rsv(self):
        out = attr.filter_shared_digest_by_label(self._digest(), "RSV")
        names = {o["name"] for o in out["db_objects"]}
        assert names == {"M_RSV"}

    def test_no_segment_match_empty(self):
        out = attr.filter_shared_digest_by_label(self._digest(), "INV")
        assert out["db_objects"] == []

    def test_original_digest_not_mutated(self):
        d = self._digest()
        attr.filter_shared_digest_by_label(d, "POS")
        assert len(d["db_objects"]) == 4    # source untouched
