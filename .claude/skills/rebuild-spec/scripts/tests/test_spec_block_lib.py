"""Tests for scripts/_spec_block_lib.py."""
from pathlib import Path
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _spec_block_lib import find_blocks, has_linked_fr, find_blocks_missing_linked_fr


class TestBlockBoundaryDetection:
    def test_finds_br_block(self):
        text = "### BR-001_SomeRule\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "BR"
        assert blocks[0]["code"] == "BR-001_SomeRule"

    def test_finds_sm_block(self):
        text = "### SM-001_StateLifecycle\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "SM"

    def test_finds_alg_block(self):
        text = "### ALG-001_PricingCalc\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "ALG"

    def test_finds_int_block(self):
        text = "### INT-001_PaymentGateway\nsome content\n"
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["prefix"] == "INT"

    def test_block_end_is_next_h3(self):
        text = (
            "### BR-001_First\nline a\nline b\n"
            "### BR-002_Second\nline c\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 2
        # First block ends where second begins
        assert blocks[0]["block_end"] == blocks[1]["heading_line"]

    def test_last_block_end_is_total_lines(self):
        text = "### BR-001_Only\nline a\nline b\n"
        blocks = find_blocks(text)
        assert blocks[0]["block_end"] == len(text.splitlines())

    def test_heading_line_zero_based(self):
        text = "preamble\n### BR-001_Rule\ncontent\n"
        blocks = find_blocks(text)
        assert blocks[0]["heading_line"] == 1

    def test_ignores_non_block_headings(self):
        text = "## Overview\nsome text\n### Not-A-Block\nmore text\n"
        blocks = find_blocks(text)
        assert len(blocks) == 0

    def test_skips_block_heading_inside_backtick_fence(self):
        text = (
            "Some intro\n"
            "```\n"
            "### BR-001_InsideFence\n"
            "content inside fence\n"
            "```\n"
            "### BR-002_Outside\nreal content\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "BR-002_Outside"

    def test_skips_block_heading_inside_tilde_fence(self):
        text = (
            "~~~\n"
            "### INT-001_InsideTilde\n"
            "code here\n"
            "~~~\n"
            "### SM-001_Outside\ncontent\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "SM-001_Outside"

    def test_fence_with_language_tag_is_skipped(self):
        text = (
            "```markdown\n"
            "### ALG-001_Example\ncode\n"
            "```\n"
            "### BR-001_Real\nreal block\n"
        )
        blocks = find_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["code"] == "BR-001_Real"


class TestHasLinkedFr:
    def test_returns_true_when_linked_fr_present(self):
        text = "### BR-001_Rule\n**Linked FR:** FR-001\nmore content\n"
        blocks = find_blocks(text)
        assert has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])

    def test_returns_false_when_linked_fr_absent(self):
        text = "### BR-001_Rule\nsome content without linked fr\n"
        blocks = find_blocks(text)
        assert not has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])

    def test_does_not_cross_block_boundary(self):
        # Linked FR in second block should not count for first
        text = (
            "### BR-001_First\nno linked fr here\n"
            "### BR-002_Second\n**Linked FR:** FR-002\n"
        )
        blocks = find_blocks(text)
        assert not has_linked_fr(text, blocks[0]["heading_line"], blocks[0]["block_end"])
        assert has_linked_fr(text, blocks[1]["heading_line"], blocks[1]["block_end"])


class TestFindBlocksMissingLinkedFr:
    def test_returns_missing_blocks(self):
        text = "### BR-001_Rule\nno linked fr\n"
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 1
        assert missing[0]["code"] == "BR-001_Rule"

    def test_skips_blocks_with_linked_fr(self):
        text = "### BR-001_Rule\n**Linked FR:** FR-001\ncontent\n"
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 0

    def test_multi_block_partial_missing(self):
        text = (
            "### BR-001_HasIt\n**Linked FR:** FR-001\ncontent\n"
            "### BR-002_MissingIt\nno linked fr\n"
        )
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 1
        assert missing[0]["code"] == "BR-002_MissingIt"

    def test_empty_file_returns_empty_list(self):
        assert find_blocks_missing_linked_fr("") == []

    def test_multi_block_all_missing(self):
        text = (
            "### BR-001_RuleA\ncontent a\n"
            "### SM-001_StateMachine\ncontent b\n"
            "### ALG-001_Calc\ncontent c\n"
        )
        missing = find_blocks_missing_linked_fr(text)
        assert len(missing) == 3
