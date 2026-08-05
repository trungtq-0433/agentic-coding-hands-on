"""Shared spec structure constants. Stdlib only — zero imports.

Single source of truth for required H2 sections and skeleton content.
Referenced by validate_feature_spec.py and scaffold_spec.py.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Required H2 sections — ORDER IS LOAD-BEARING (validator checks exact order)
# ---------------------------------------------------------------------------

REQUIRED_H2_TECH = [
    "## Overview",
    "## Polymorphic Behavior",
    "## Cross-Cutting Logic",
    "## User Stories",
    "## Key Entities",
    "## Artifact References",
    "## Assumptions",
    "## Source Code References",
    "## Unresolved Questions",
]

REQUIRED_H2_BC = [
    "## Why It Matters",
    "## Who Uses It",
    "## What They Do",
]

REQUIRED_H2_SCR = [
    "## Screen List",
    "## User Journey",
]

# ---------------------------------------------------------------------------
# CCL H3 sections (used by scaffold to pre-populate the CCL body)
# ---------------------------------------------------------------------------

REQUIRED_CCL_H3 = [
    "### Requirements",
    "### Business Rules",
    "### Decision Logic",
    "### State Machines",
    "### Algorithms",
    "### External Integrations",
    "### Verification",
]

# ---------------------------------------------------------------------------
# A3/B4 (v26.0.0) — NEW REQUIRED sections gated by a DEDICATED validator
# (validate_reading_guide_db_impact.py), never added to REQUIRED_H2_TECH above
# (Decision 2 — the exact-order check has no degradation window; see
# references/confidence-report-contract.md § A3 navigational-entries amendment
# and plans/260707-0803-acsim-learnings-rebuild-spec/phase-03-*.md).
# Single source of truth for the heading text: scaffold_spec.py,
# validate_reading_guide_db_impact.py, and migrate-reading-guide-db-impact.py
# all import these instead of re-declaring the literal strings.
# ---------------------------------------------------------------------------

A3_HEADING = "## Source Walkthrough"
B4_HEADING = "## DB Impact per Event"

# ---------------------------------------------------------------------------
# Edge-cases skeleton — markdown table with ≥1 placeholder data row.
# Must pass _check_edge_cases with no warning (needs ≥1 non-separator,
# non-header data row, i.e. a line starting with `|` that is NOT `|---|`
# and does NOT start with `| Scenario`).
# ---------------------------------------------------------------------------

EDGE_CASES_SKELETON = """\
| Scenario | Input | Expected | Severity |
|----------|-------|----------|----------|
| (placeholder — replace with real edge case) | — | — | low |
"""
