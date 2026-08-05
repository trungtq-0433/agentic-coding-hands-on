"""Unit tests for _id_schemes_lib.py — scheme registry, regex, find_codes,
build_renumber_map, find_overflow_tokens."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _id_schemes_lib import (  # noqa: E402
    ARTIFACT_OWNS,
    SCHEMES,
    SIBLING_MATRIX,
    build_renumber_map,
    find_codes,
    find_codes_scoped,
    find_fence_only_codes,
    find_overflow_tokens,
    resolve_artifact_files,
    token_re,
)


# ---------------------------------------------------------------------------
# Registry sanity
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_all_artifact_prefixes_in_schemes(self):
        for _artifact, prefixes in ARTIFACT_OWNS.items():
            for p in prefixes:
                assert p in SCHEMES, f"{p} missing from SCHEMES"

    def test_sibling_keys_in_schemes(self):
        for prefix in SIBLING_MATRIX:
            assert prefix in SCHEMES

    def test_reg_scope_per_screen(self):
        assert SCHEMES["REG"]["scope"] == "per-screen"

    def test_disc_sep_hyphen(self):
        assert SCHEMES["DISC"]["sep"] == "-"

    def test_reg_not_in_artifact_owns(self):
        for prefixes in ARTIFACT_OWNS.values():
            assert "REG" not in prefixes, "REG must never be globally renumbered"

    def test_route_in_schemes(self):
        assert "ROUTE" in SCHEMES
        assert SCHEMES["ROUTE"] == {"sep": "", "scope": "global"}

    def test_route_list_owns_route(self):
        assert ARTIFACT_OWNS["route-list"] == ["ROUTE"]

    def test_route_sibling_matrix_entries_exist(self):
        # F7 guard: every listed sibling must be a plausible artifacts/ filename
        for sib in SIBLING_MATRIX["ROUTE"]:
            assert sib.endswith(".md")

    def test_route_sibling_matrix_excludes_screen_flow(self):
        # No grep-verified ROUTE### citation in screen-flow-template.md (F7 guard)
        assert "screen-flow.md" not in SIBLING_MATRIX["ROUTE"]


# ---------------------------------------------------------------------------
# token_re
# ---------------------------------------------------------------------------

class TestTokenRe:
    def test_matches_three_digits(self):
        pat = token_re("US", "")
        assert pat.search("US001") is not None

    def test_no_match_four_digits(self):
        pat = token_re("US", "")
        # 4-digit token must NOT be matched by 3-digit regex
        assert pat.search("US1000") is None

    def test_no_match_two_digits(self):
        pat = token_re("US", "")
        assert pat.search("US01") is None

    def test_word_boundary_left(self):
        # A letter immediately before the prefix must suppress match
        pat = token_re("US", "")
        assert pat.search("XUS001") is None

    def test_word_boundary_right(self):
        # A digit immediately after the 3 digits must suppress match
        pat = token_re("US", "")
        assert pat.search("US0010") is None

    def test_slug_tail_not_consumed(self):
        pat = token_re("US", "")
        m = pat.search("US005_Login")
        assert m is not None
        # Only the 3 digit group is captured — slug tail untouched
        assert m.group(1) == "005"
        end = m.end()
        assert "US005_Login"[end:] == "_Login"

    def test_disc_sep_hyphen(self):
        pat = token_re("DISC", "-")
        assert pat.search("DISC-001") is not None
        assert pat.search("DISC001") is None  # missing sep

    def test_caches_same_instance(self):
        p1 = token_re("BL", "")
        p2 = token_re("BL", "")
        assert p1 is p2


# ---------------------------------------------------------------------------
# find_codes
# ---------------------------------------------------------------------------

class TestFindCodes:
    def test_document_order(self):
        text = "US005 then US001 then US013"
        codes = find_codes(text, "US", "")
        assert codes == ["US005", "US001", "US013"]

    def test_dedup_first_occurrence(self):
        text = "US001 US005 US001 US013"
        codes = find_codes(text, "US", "")
        assert codes == ["US001", "US005", "US013"]

    def test_empty_text(self):
        assert find_codes("", "US", "") == []

    def test_no_tokens(self):
        assert find_codes("nothing here", "US", "") == []

    def test_disc_sep(self):
        codes = find_codes("DISC-001 then DISC-003", "DISC", "-")
        assert codes == ["DISC-001", "DISC-003"]

    def test_scans_whole_text_including_fences(self):
        text = "```python\nUS005\n```\nUS001"
        codes = find_codes(text, "US", "")
        assert "US005" in codes
        assert "US001" in codes

    def test_ignores_four_plus_digits(self):
        codes = find_codes("US1000 US001", "US", "")
        assert "US1000" not in codes
        assert "US001" in codes

    def test_slug_tail_preserved_in_result(self):
        # find_codes returns full code without slug — slug is after the match
        codes = find_codes("US005_Login", "US", "")
        assert codes == ["US005"]

    def test_per_spec_tokens_not_collected_by_us(self):
        # FR-001, SC-002, DEC-003 should not be picked up by US-prefix scanner
        text = "FR-001 SC-002 DEC-003 US005"
        codes = find_codes(text, "US", "")
        assert codes == ["US005"]


# ---------------------------------------------------------------------------
# build_renumber_map
# ---------------------------------------------------------------------------

class TestBuildRenumberMap:
    def test_gap_compaction(self):
        codes = ["US001", "US005", "US013"]
        m = build_renumber_map(codes, "US", "")
        assert m == {"US005": "US002", "US013": "US003"}

    def test_already_contiguous_returns_empty(self):
        codes = ["US001", "US002", "US003"]
        assert build_renumber_map(codes, "US", "") == {}

    def test_document_order_stability(self):
        # First seen in doc order gets lowest new number
        codes = ["US013", "US005", "US001"]
        m = build_renumber_map(codes, "US", "")
        assert m["US013"] == "US001"
        assert m["US005"] == "US002"
        assert m["US001"] == "US003"

    def test_disc_sep(self):
        codes = ["DISC-001", "DISC-003"]
        m = build_renumber_map(codes, "DISC", "-")
        assert m == {"DISC-003": "DISC-002"}

    def test_single_code_already_001(self):
        assert build_renumber_map(["US001"], "US", "") == {}

    def test_single_code_not_001(self):
        m = build_renumber_map(["US005"], "US", "")
        assert m == {"US005": "US001"}

    def test_chain_collision_safe(self):
        # US003→US002 while US005→US003 — the MAP itself is just old→new;
        # the two-phase apply is what prevents clobber (tested in renumber tests).
        codes = ["US001", "US002", "US003", "US005"]
        m = build_renumber_map(codes, "US", "")
        # US001,002,003 are already contiguous so only US005 moves
        assert m == {"US005": "US004"}

    def test_route_gap_compaction(self):
        # ROUTE### uses the same WORD###/sep="" shape as US/SCR/F — sanity-check
        # it behaves identically end-to-end through the real registry values.
        codes = ["ROUTE001", "ROUTE005"]
        m = build_renumber_map(codes, "ROUTE", SCHEMES["ROUTE"]["sep"])
        assert m == {"ROUTE005": "ROUTE002"}


# ---------------------------------------------------------------------------
# find_overflow_tokens
# ---------------------------------------------------------------------------

class TestFindOverflowTokens:
    def test_detects_four_digit(self):
        tokens = find_overflow_tokens("US1000 present", "US", "")
        assert tokens == ["US1000"]

    def test_ignores_three_digit(self):
        tokens = find_overflow_tokens("US001 US999", "US", "")
        assert tokens == []

    def test_dedup_preserves_order(self):
        tokens = find_overflow_tokens("US1000 US2000 US1000", "US", "")
        assert tokens == ["US1000", "US2000"]

    def test_disc_overflow(self):
        tokens = find_overflow_tokens("DISC-1000", "DISC", "-")
        assert tokens == ["DISC-1000"]

    def test_no_overflow(self):
        assert find_overflow_tokens("nothing here", "US", "") == []


# ---------------------------------------------------------------------------
# resolve_artifact_files
# ---------------------------------------------------------------------------

class TestResolveArtifactFiles:
    def test_default_single_file_exists(self, tmp_path):
        """Default artifact → [artifacts/<artifact>.md] when file exists."""
        art_dir = tmp_path / "artifacts"
        art_dir.mkdir()
        f = art_dir / "user-stories.md"
        f.write_text("content", encoding="utf-8")
        result = resolve_artifact_files(tmp_path, "user-stories")
        assert result == [f]

    def test_default_single_file_missing_returns_empty(self, tmp_path):
        """Default artifact → [] when file does not exist."""
        (tmp_path / "artifacts").mkdir()
        result = resolve_artifact_files(tmp_path, "user-stories")
        assert result == []

    def test_process_flows_returns_sorted_md_files(self, tmp_path):
        """process-flows → sorted list of artifacts/flows/*.md."""
        flows_dir = tmp_path / "artifacts" / "flows"
        flows_dir.mkdir(parents=True)
        b = flows_dir / "b.md"
        a = flows_dir / "a.md"
        b.write_text("b", encoding="utf-8")
        a.write_text("a", encoding="utf-8")
        result = resolve_artifact_files(tmp_path, "process-flows")
        # Sorted by filename
        assert result == [a, b]

    def test_process_flows_empty_dir_returns_empty(self, tmp_path):
        """process-flows with empty flows/ → []."""
        (tmp_path / "artifacts" / "flows").mkdir(parents=True)
        result = resolve_artifact_files(tmp_path, "process-flows")
        assert result == []

    def test_process_flows_missing_dir_returns_empty(self, tmp_path):
        """process-flows with no flows/ dir → []."""
        (tmp_path / "artifacts").mkdir()
        result = resolve_artifact_files(tmp_path, "process-flows")
        assert result == []

    def test_process_flows_non_md_files_excluded(self, tmp_path):
        """process-flows: only .md files are returned (not .completed, .json, etc.)."""
        flows_dir = tmp_path / "artifacts" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "a.md").write_text("a", encoding="utf-8")
        (flows_dir / ".completed").write_text("", encoding="utf-8")
        (flows_dir / "meta.json").write_text("{}", encoding="utf-8")
        result = resolve_artifact_files(tmp_path, "process-flows")
        names = [f.name for f in result]
        assert "a.md" in names
        assert ".completed" not in names
        assert "meta.json" not in names


# ---------------------------------------------------------------------------
# find_codes_scoped (A4: prose+mermaid scope only)
# ---------------------------------------------------------------------------

class TestFindCodesScoped:
    def test_prose_token_included(self):
        codes = find_codes_scoped("US001 prose", "US", "")
        assert "US001" in codes

    def test_mermaid_token_included(self):
        text = "```mermaid\ngraph TD\n    A[US003_Login]\n```\n"
        codes = find_codes_scoped(text, "US", "")
        assert "US003" in codes

    def test_python_fence_token_excluded(self):
        text = "US001 prose\n```python\n# US005\n```\n"
        codes = find_codes_scoped(text, "US", "")
        assert "US001" in codes
        assert "US005" not in codes

    def test_unclosed_fence_token_excluded(self):
        """Token in an unclosed code fence at EOF → excluded from scoped result."""
        text = "US001 prose\n```python\n# US007 in unclosed fence\n"
        codes = find_codes_scoped(text, "US", "")
        assert "US001" in codes
        assert "US007" not in codes

    def test_document_order_preserved(self):
        text = "US005 first\nUS001 second\n"
        codes = find_codes_scoped(text, "US", "")
        assert codes == ["US005", "US001"]

    def test_empty_text(self):
        assert find_codes_scoped("", "US", "") == []

    def test_no_tokens(self):
        assert find_codes_scoped("nothing here", "US", "") == []

    def test_dedup_within_scope(self):
        text = "US001 twice\nUS001 again\nUS002 other\n"
        codes = find_codes_scoped(text, "US", "")
        assert codes.count("US001") == 1

    def test_disc_sep_scoped(self):
        text = "DISC-001 entry\n```bash\n# DISC-003 in bash\n```\n"
        codes = find_codes_scoped(text, "DISC", "-")
        assert "DISC-001" in codes
        assert "DISC-003" not in codes


# ---------------------------------------------------------------------------
# find_fence_only_codes (A4: warns for skipped fence tokens)
# ---------------------------------------------------------------------------

class TestFindFenceOnlyCodes:
    def test_fence_only_code_detected(self):
        text = "US001 prose\n```python\n# US005\n```\n"
        fence_only = find_fence_only_codes(text, "US", "")
        assert "US005" in fence_only

    def test_prose_code_not_in_fence_only(self):
        text = "US001 prose\n```python\n# US005\n```\n"
        fence_only = find_fence_only_codes(text, "US", "")
        assert "US001" not in fence_only

    def test_code_in_both_prose_and_fence_not_fence_only(self):
        text = "US001 prose\n```python\n# US001 in fence too\n```\n"
        fence_only = find_fence_only_codes(text, "US", "")
        assert "US001" not in fence_only

    def test_mermaid_not_fence_only(self):
        """Mermaid tokens are in scoped result → not classified as fence-only."""
        text = "```mermaid\n    A[US003]\n```\n"
        fence_only = find_fence_only_codes(text, "US", "")
        assert "US003" not in fence_only

    def test_empty_text(self):
        assert find_fence_only_codes("", "US", "") == []

    def test_no_fence_only_when_all_in_prose(self):
        text = "US001 prose\nUS002 prose\n"
        assert find_fence_only_codes(text, "US", "") == []
