"""Tests for _spec_constants.py.

F8 (v26.0.0, acsim-learnings phase-03): permanent regression guarding Decision 2 — the two
new A3/B4 headings must NEVER be added to REQUIRED_H2_TECH (that exact-order check has no
degradation window; A3/B4 are gated by a dedicated validator instead). Also guards
REQUIRED_CCL_H3 and REQUIRED_H2_BC/REQUIRED_H2_SCR for the same reason (any future section
belongs behind a dedicated validator, not the exact-order constants).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _spec_constants import (  # noqa: E402
    A3_HEADING,
    B4_HEADING,
    REQUIRED_CCL_H3,
    REQUIRED_H2_BC,
    REQUIRED_H2_SCR,
    REQUIRED_H2_TECH,
)


class TestF8RegressionGuard:
    def test_a3_heading_not_in_required_h2_tech(self):
        assert A3_HEADING not in REQUIRED_H2_TECH

    def test_b4_heading_not_in_required_h2_tech(self):
        assert B4_HEADING not in REQUIRED_H2_TECH

    def test_a3_heading_not_in_required_ccl_h3(self):
        assert A3_HEADING not in REQUIRED_CCL_H3

    def test_b4_heading_not_in_required_ccl_h3(self):
        assert B4_HEADING not in REQUIRED_CCL_H3

    def test_a3_heading_not_in_required_h2_bc_or_scr(self):
        assert A3_HEADING not in REQUIRED_H2_BC
        assert A3_HEADING not in REQUIRED_H2_SCR

    def test_b4_heading_not_in_required_h2_bc_or_scr(self):
        assert B4_HEADING not in REQUIRED_H2_BC
        assert B4_HEADING not in REQUIRED_H2_SCR

    def test_headings_are_distinct_top_level_h2(self):
        assert A3_HEADING.startswith("## ")
        assert B4_HEADING.startswith("## ")
        assert A3_HEADING != B4_HEADING
