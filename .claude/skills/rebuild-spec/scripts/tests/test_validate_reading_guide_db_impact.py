# layout-exempt: rebuild-spec A3/B4 validator tests — docs paths are managed targets
"""Tests for validate_reading_guide_db_impact.py (v26.0.0, acsim-learnings phase-03).

Covers the shared degradation contract for both families (A3 `## Source Walkthrough` in
technical-spec.md + screen-spec spec.md; B4 `## DB Impact per Event` in technical-spec.md
only): absent → WARN pre_migration; empty body → CRITICAL malformed; unfilled placeholder →
WARN unmapped; well-formed → no issues; B4 N/A escape; B4 uncited Operation cell → WARN.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import validate_reading_guide_db_impact as v  # noqa: E402


def _sev(issues, rid):
    return [i for i in issues if i["rule_id"] == rid]


# ---------------------------------------------------------------------------
# A3 — Source Walkthrough (shared check, both families)
# ---------------------------------------------------------------------------

class TestSourceWalkthrough:
    def test_absent_is_pre_migration_warn(self):
        text = "## Overview\n\nSome content.\n"
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.pre_migration")) == 1
        assert issues[0]["severity"] == "warning"

    def test_empty_body_is_malformed_critical(self):
        text = "## Source Walkthrough\n\n## Unresolved Questions\n\nx\n"
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.malformed")) == 1
        assert issues[0]["severity"] == "critical"

    def test_unfilled_placeholder_is_unmapped_warn(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
                "## Unresolved Questions\n")
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_filled_content_passes(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `models/order.rb:1-40` — defines the Order entity.\n\n"
                "## Unresolved Questions\n")
        assert v.check_source_walkthrough(text, "f") == []

    def test_bounded_by_next_h2_not_leaking_into_following_section(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `x.rb:1-2` — real content.\n\n"
                "## DB Impact per Event\n\nN/A — read-only feature, no DB writes.\n")
        issues = v.check_source_walkthrough(text, "f")
        assert issues == []


# ---------------------------------------------------------------------------
# B4 — DB Impact per Event (technical-spec.md only)
# ---------------------------------------------------------------------------

class TestDbImpact:
    def test_absent_is_pre_migration_warn(self):
        text = "## Overview\n\nSome content.\n"
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.pre_migration")) == 1
        assert issues[0]["severity"] == "warning"

    def test_empty_body_is_malformed_critical(self):
        text = "## DB Impact per Event\n\n## Unresolved Questions\n"
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.malformed")) == 1
        assert issues[0]["severity"] == "critical"

    def test_no_table_and_not_na_is_malformed_critical(self):
        text = "## DB Impact per Event\n\nSome prose but no table at all.\n"
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.malformed")) == 1

    def test_na_escape_passes(self):
        text = "## DB Impact per Event\n\nN/A — read-only feature, no DB writes.\n"
        assert v.check_db_impact(text, "f") == []

    def test_placeholder_only_table_is_unmapped_warn(self):
        text = ("## DB Impact per Event\n\n"
                "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
                "|---|---|---|---|---|---|\n"
                "| {METHOD /path} | `{table}` | {cols} | {op} | {derivation} | `{path:line}` |\n")
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_cited_row_passes(self):
        text = ("## DB Impact per Event\n\n"
                "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
                "|---|---|---|---|---|---|\n"
                "| POST /orders | `orders` | total | INSERT | from cart | "
                "`app/OrdersController.rb:10-20` |\n")
        assert v.check_db_impact(text, "f") == []

    def test_inferred_row_passes(self):
        text = ("## DB Impact per Event\n\n"
                "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
                "|---|---|---|---|---|---|\n"
                "| checkout.completed | `orders` | status | UPDATE | set on completion | "
                "[INFERRED] — write site not pinpointed |\n")
        assert v.check_db_impact(text, "f") == []

    def test_uncited_row_is_warn(self):
        text = ("## DB Impact per Event\n\n"
                "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
                "|---|---|---|---|---|---|\n"
                "| POST /orders | `orders` | total | INSERT | from cart | |\n")
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.uncited")) == 1
        assert issues[0]["severity"] == "warning"


# ---------------------------------------------------------------------------
# C1 regression — fenced heading-shaped line must not truncate the section body
# (phase-01, attack/t3_placeholder_hidden_by_fence + t3_control_no_fence)
# ---------------------------------------------------------------------------

class TestFenceAwareSectionBoundary:
    def test_fenced_heading_shaped_line_no_longer_hides_trailing_placeholder(self):
        # Was PASS before the C1 fix: the fence-blind boundary regex stopped the body
        # right before the fenced "# Note:" line, hiding the {placeholder} that follows it.
        text = (
            "# Technical Spec\n\n"
            "## Source Walkthrough\n\n"
            "Reading order:\n\n"
            "```python\n"
            "# Note: see handler\n"
            "```\n"
            "{Ordered reading list (data model -> entry point -> view -> logic), 1 file per "
            "step, with a 1-sentence \"why start here.\"}\n\n"
            "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
            "## DB Impact per Event\n\n"
            "N/A — no DB writes in this feature.\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_control_no_fence_still_warns_unmapped_parity(self):
        # Same content minus the fence — must produce the identical WARN (parity proof).
        text = (
            "# Technical Spec\n\n"
            "## Source Walkthrough\n\n"
            "Reading order:\n\n"
            "{Ordered reading list (data model -> entry point -> view -> logic), 1 file per "
            "step, with a 1-sentence \"why start here.\"}\n\n"
            "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
            "## DB Impact per Event\n\n"
            "N/A — no DB writes in this feature.\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_tilde_fenced_heading_shaped_line_also_handled(self):
        text = (
            "## Source Walkthrough\n\n"
            "~~~\n# fake heading\n~~~\n"
            "{still unfilled}\n\n"
            "## Unresolved Questions\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1


# ---------------------------------------------------------------------------
# R2 regression — B4 table extraction must ignore a fenced EXAMPLE table
# ---------------------------------------------------------------------------

class TestFencedExampleTableIgnored:
    def test_fenced_example_table_not_mistaken_for_the_real_one(self):
        text = (
            "## DB Impact per Event\n\n"
            "Example (do not edit):\n\n"
            "```\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| FAKE | fake | fake | fake | fake | fake |\n"
            "```\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| POST /orders | `orders` | total | INSERT | from cart | "
            "`app/OrdersController.rb:10-20` |\n"
        )
        assert v.check_db_impact(text, "f") == []

    def test_fenced_example_table_with_uncited_fake_row_does_not_leak_a_warning(self):
        text = (
            "## DB Impact per Event\n\n"
            "```\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| FAKE | fake | fake | fake | fake | |\n"
            "```\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|---|---|---|---|---|---|\n"
            "| POST /orders | `orders` | total | INSERT | from cart | "
            "`app/OrdersController.rb:10-20` |\n"
        )
        issues = v.check_db_impact(text, "f")
        assert issues == []


# ---------------------------------------------------------------------------
# I3 regression — escaped `\|` in a B4 cell must not shift columns
# (attack/t4_b4_escaped_pipe)
# ---------------------------------------------------------------------------

class TestEscapedPipeInB4Row:
    def test_escaped_pipe_operation_cell_does_not_cause_false_uncited(self):
        text = (
            "## Source Walkthrough\n\n"
            "Real content, no placeholders here at all, fully documented.\n\n"
            "## DB Impact per Event\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|-----------------|-------|---------|-----------|-------------------|--------|\n"
            "| POST /orders | `orders` | id, total | INSERT\\|UPDATE | sum of line items | "
            "`src/handler.py:15` |\n"
        )
        issues = v.check_db_impact(text, "f")
        assert issues == []

    def test_escaped_pipe_row_with_genuinely_missing_citation_still_warns(self):
        text = (
            "## DB Impact per Event\n\n"
            "| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |\n"
            "|-----------------|-------|---------|-----------|-------------------|--------|\n"
            "| POST /orders | `orders` | id, total | INSERT\\|UPDATE | sum of line items | |\n"
        )
        issues = v.check_db_impact(text, "f")
        assert len(_sev(issues, "db_impact.uncited")) == 1


# ---------------------------------------------------------------------------
# integration: validate() over both families + main() exit codes + summary merge
# ---------------------------------------------------------------------------

_TECH_WELL_FORMED = (
    "## Source Walkthrough\n\n1. **File:** `x.rb:1-2` — real content.\n\n"
    "## DB Impact per Event\n\nN/A — read-only feature, no DB writes.\n"
)
_SCREEN_WELL_FORMED = "## Source Walkthrough\n\n1. **File:** `x.vue:1-2` — real content.\n"


def _make_docs(tmp_path: Path, tech_body: str = _TECH_WELL_FORMED,
               screen_body: str = _SCREEN_WELL_FORMED) -> Path:
    docs = tmp_path / "docs"
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text(tech_body, encoding="utf-8")
    scr = docs / "screens" / "SCR001_Login"
    scr.mkdir(parents=True)
    (scr / "spec.md").write_text(screen_body, encoding="utf-8")
    return docs


class TestIntegration:
    def test_validate_passes_on_well_formed_docs(self, tmp_path):
        docs = _make_docs(tmp_path)
        result = v.validate(docs)
        assert result["status"] == "PASS", result["issues"]

    def test_validate_warns_on_pre_migration_docs(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Overview\n\nx\n", screen_body="## Purpose\n\nx\n")
        result = v.validate(docs)
        assert result["status"] == "WARN"
        rids = {i["rule_id"] for i in result["issues"]}
        assert "reading_guide.pre_migration" in rids
        assert "db_impact.pre_migration" in rids

    def test_validate_fails_on_malformed_docs(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Source Walkthrough\n\n## Unresolved Questions\n")
        result = v.validate(docs)
        assert result["status"] == "FAIL"

    def test_main_exit_zero_on_warn(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Overview\n\nx\n", screen_body="## Purpose\n\nx\n")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_main_exit_one_on_critical(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Source Walkthrough\n\n## Unresolved Questions\n")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 1

    def test_summary_merge(self, tmp_path):
        docs = _make_docs(tmp_path)
        sp = tmp_path / "validation-summary.json"
        v.main(["--docs-root", str(docs), "--project-root", str(tmp_path),
                "--summary-out", str(sp)])
        data = json.loads(sp.read_text())
        assert "reading_guide_db_impact" in data["validators"]
