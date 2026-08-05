"""Tests for `_md_scan_lib.py` — shared fence/comment/escape-aware markdown primitives
(PR #176 phase-01). Each of the 5 rewired scanners' regression tests exercise these
helpers indirectly; this file unit-covers them directly.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _md_scan_lib import (  # noqa: E402
    iter_lines_with_fence,
    mask_fenced,
    split_table_row,
    strip_comments,
    strip_disclaimer_blocks,
)


class TestIterLinesWithFence:
    def test_no_fence_all_lines_unfenced(self):
        text = "a\nb\nc"
        got = list(iter_lines_with_fence(text))
        assert got == [(1, "a", False), (2, "b", False), (3, "c", False)]

    def test_backtick_fence_marks_content_and_delimiters(self):
        text = "before\n```\ninside\n```\nafter"
        got = list(iter_lines_with_fence(text))
        assert got == [
            (1, "before", False),
            (2, "```", True),
            (3, "inside", True),
            (4, "```", True),
            (5, "after", False),
        ]

    def test_tilde_fence_supported(self):
        text = "before\n~~~\ninside\n~~~\nafter"
        got = list(iter_lines_with_fence(text))
        assert [in_fence for _, _, in_fence in got] == [False, True, True, True, False]

    def test_mixed_marker_inside_fence_does_not_close_early(self):
        # A ``` fence containing a stray ~~~ line must stay open until the matching ```.
        text = "```\n~~~\nstill inside\n```\nafter"
        got = list(iter_lines_with_fence(text))
        assert [in_fence for _, _, in_fence in got] == [True, True, True, True, False]

    def test_heading_shaped_line_inside_fence_reported_as_fenced(self):
        text = "```python\n# Note: see handler\n```\n{placeholder}"
        got = list(iter_lines_with_fence(text))
        assert got[1] == (2, "# Note: see handler", True)
        assert got[3] == (4, "{placeholder}", False)

    def test_unterminated_fence_stays_in_fence_to_eof(self):
        text = "```\nline1\nline2"
        got = list(iter_lines_with_fence(text))
        assert all(in_fence for _, _, in_fence in got[1:])

    def test_indented_fence_marker_detected(self):
        text = "  ```\ninside\n  ```\nafter"
        got = list(iter_lines_with_fence(text))
        assert [in_fence for _, _, in_fence in got] == [True, True, True, False]


class TestStripComments:
    def test_single_line_comment_removed(self):
        assert strip_comments("a<!-- x -->b") == "ab"

    def test_multiline_comment_blanked_but_line_count_preserved(self):
        # Inspection rework (v26.1.1): a multi-line comment is replaced by its own
        # newlines so downstream line_start diagnostics keep mapping to the original doc.
        text = "a<!--\nmulti\nline\n-->b"
        got = strip_comments(text)
        assert got == "a\n\n\nb"
        assert len(got.splitlines()) == len(text.splitlines())
        assert "multi" not in got

    def test_line_numbers_after_multiline_comment_stable(self):
        lines = ["# Title", "<!--", "hidden 1", "hidden 2", "-->", "## Real Heading"]
        got = strip_comments("\n".join(lines)).splitlines()
        assert got[5] == "## Real Heading"  # still line 6 (index 5) post-strip

    def test_multiple_comments_all_removed(self):
        text = "<!-- one -->keep<!-- two -->"
        assert strip_comments(text) == "keep"

    def test_no_comment_unchanged(self):
        assert strip_comments("plain text") == "plain text"


class TestStripDisclaimerBlocks:
    def test_block_removed(self):
        text = "before\n<!-- disclaimer:start -->\nsecret [INFERRED] text\n<!-- disclaimer:end -->\nafter"
        out = strip_disclaimer_blocks(text)
        assert "[INFERRED]" not in out
        assert "before" in out and "after" in out

    def test_case_insensitive_markers(self):
        text = "<!-- DISCLAIMER:START -->x<!-- Disclaimer:End -->keep"
        assert strip_disclaimer_blocks(text) == "keep"

    def test_multiple_blocks_all_removed(self):
        text = "<!-- disclaimer:start -->a<!-- disclaimer:end -->mid<!-- disclaimer:start -->b<!-- disclaimer:end -->"
        assert strip_disclaimer_blocks(text) == "mid"

    def test_unterminated_block_left_untouched(self):
        text = "<!-- disclaimer:start -->never closed"
        assert strip_disclaimer_blocks(text) == text

    def test_no_block_unchanged(self):
        assert strip_disclaimer_blocks("plain text") == "plain text"


class TestMaskFenced:
    def test_fenced_lines_blanked_others_kept(self):
        text = "keep1\n```\nsecret\n```\nkeep2"
        masked = mask_fenced(text)
        assert masked.splitlines() == ["keep1", "", "", "", "keep2"]

    def test_line_count_preserved(self):
        text = "a\n```\nb\nc\n```\nd\ne"
        assert len(mask_fenced(text).splitlines()) == len(text.splitlines())

    def test_offsets_preserved_for_post_fence_content(self):
        text = "## Heading\n```\n| fake | table |\n|---|---|\n```\n| real | table |\n|---|---|\n"
        masked = mask_fenced(text)
        lines = masked.splitlines()
        # The real table survives at its original line offsets; the fake one is blanked.
        assert lines[0] == "## Heading"
        assert lines[1] == "" and lines[2] == "" and lines[3] == "" and lines[4] == ""
        assert lines[5] == "| real | table |"
        assert lines[6] == "|---|---|"

    def test_no_fence_unchanged_content(self):
        text = "a\nb\nc"
        assert mask_fenced(text).splitlines() == ["a", "b", "c"]


class TestSplitTableRow:
    def test_plain_row_matches_simple_split_semantics(self):
        assert split_table_row("| a | b | c |") == ["a", "b", "c"]

    def test_escaped_pipe_kept_as_one_cell(self):
        row = r"| POST /orders | `orders` | id, total | INSERT\|UPDATE | sum | `src/handler.py:15` |"
        cells = split_table_row(row)
        assert cells == [
            "POST /orders", "`orders`", "id, total", "INSERT|UPDATE", "sum",
            "`src/handler.py:15`",
        ]

    def test_multiple_escaped_pipes_in_one_cell(self):
        row = r"| {INSERT\|UPDATE\|DELETE} | x |"
        assert split_table_row(row) == ["{INSERT|UPDATE|DELETE}", "x"]

    def test_empty_middle_cell_preserved(self):
        assert split_table_row("| a | | c |") == ["a", "", "c"]

    def test_outer_pipes_do_not_produce_empty_edge_cells(self):
        assert split_table_row("|a|b|") == ["a", "b"]
