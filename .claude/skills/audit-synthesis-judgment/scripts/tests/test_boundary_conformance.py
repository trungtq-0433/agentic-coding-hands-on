"""Tests for Engine 2 — IPE protocol-conformance boundary check."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import _ipe_parse_lib as ipe_parse  # noqa: E402
import _ipe_conformance_lib as ipe_conf  # noqa: E402
import boundary_conformance  # noqa: E402


# --- fixtures --------------------------------------------------------------

_CONFORMANT = """# User Stories

## Interaction Inventory

| Screen | Element | Type | Action | Endpoint |
|--------|---------|------|--------|---------|
| SCR001_Orders | Create btn | primary-action | create order | POST /api/orders |
| SCR001_Orders | Delete btn | destructive-action | delete order | DELETE /api/orders/:id |

## Screen → US Map

| Screen | US Codes |
|--------|---------|
| SCR001_Orders | US001, US002 |

## US001_CreateOrder: Create Order

## US002_DeleteOrder: Delete Order
"""

# 86-vs-354 shape: 4 interactions across 3 distinct endpoints (+0 destructive) → min 3 US,
# but only 1 US mapped → OVER_MERGE.
_OVER_MERGED = """# User Stories

## Interaction Inventory

| Screen | Element | Type | Action | Endpoint |
|--------|---------|------|--------|---------|
| SCR001_Hub | Create btn | primary-action | create | POST /api/create |
| SCR001_Hub | Export btn | secondary-action | export | GET /api/export |
| SCR001_Hub | Import btn | system-action | import | POST /api/import |
| SCR001_Hub | Sync btn | system-action | sync | POST /api/sync |

## Screen → US Map

| Screen | US Codes |
|--------|---------|
| SCR001_Hub | US001 |

## US001_ManageHub: Manage Hub
"""

_BLANK_ENDPOINT = """# User Stories

## Interaction Inventory

| Screen | Element | Type | Action | Endpoint |
|--------|---------|------|--------|---------|
| SCR001_X | A btn | primary-action | do a | |
| SCR001_X | B btn | secondary-action | do b | |

## Screen → US Map

| Screen | US Codes |
|--------|---------|
| SCR001_X | US001 |

## US001_DoA: Do A
"""


class TestParse:
    def test_parses_inventory_map_titles(self):
        p = ipe_parse.parse(_CONFORMANT)
        assert p.has_inventory and p.has_screen_map
        assert len(p.interactions) == 2
        assert p.screen_to_us["SCR001_Orders"] == ["US001", "US002"]
        assert p.us_titles["US001_CreateOrder"] == "Create Order"

    def test_skips_placeholder_rows(self):
        # The literal template (with {TOKEN}s) must yield zero real interactions.
        tmpl = Path(__file__).parent.parent.parent.parent / "rebuild-spec" / "templates" / "user-stories-template.md"
        p = ipe_parse.parse(tmpl.read_text(encoding="utf-8"))
        assert p.interactions == []


class TestConformance:
    def test_conformant_no_findings(self):
        p = ipe_parse.parse(_CONFORMANT)
        findings = ipe_conf.run_checks(p, "route-view")
        merge = [f for f in findings if f["kind"] in ("OVER_MERGE", "UNDER_SPLIT", "MISSING_US")]
        assert merge == []

    def test_over_merge_flagged_with_clause(self):
        p = ipe_parse.parse(_OVER_MERGED)
        findings = ipe_conf.run_checks(p, "route-view")
        over = [f for f in findings if f["kind"] == "OVER_MERGE"]
        assert len(over) == 1
        assert over[0]["verdict"] == "WARN"
        assert "Step-3" in over[0]["clause"]

    def test_anti_crud_flagged(self):
        p = ipe_parse.parse(_OVER_MERGED)  # title "Manage Hub"
        findings = ipe_conf.run_checks(p, "route-view")
        naming = [f for f in findings if f["kind"] == "NAMING"]
        assert len(naming) == 1 and "Step-4" in naming[0]["clause"]

    def test_blank_endpoint_unverifiable_not_guess(self):
        p = ipe_parse.parse(_BLANK_ENDPOINT)
        findings = ipe_conf.run_checks(p, "route-view")
        assert any(f["verdict"] == "UNVERIFIABLE" for f in findings)
        assert all(f["kind"] != "OVER_MERGE" for f in findings)

    def test_unsupported_screen_source_unverifiable(self):
        p = ipe_parse.parse(_OVER_MERGED)
        findings = ipe_conf.run_checks(p, "none")
        # merge check UNVERIFIABLE, but anti-CRUD still runs
        assert any(f["verdict"] == "UNVERIFIABLE" for f in findings)
        assert any(f["kind"] == "NAMING" for f in findings)

    def test_absent_inventory_unverifiable(self):
        p = ipe_parse.parse("# User Stories\n\n## US001_Foo: Create Foo\n")
        findings = ipe_conf.run_checks(p, "route-view")
        assert any(f["verdict"] == "UNVERIFIABLE" and f["kind"] == "UNVERIFIABLE" for f in findings)

    def test_no_finding_ever_flips_to_fail(self):
        p = ipe_parse.parse(_OVER_MERGED)
        findings = ipe_conf.run_checks(p, "route-view")
        assert all(f["verdict"] in ("WARN", "UNVERIFIABLE") for f in findings)
        assert all(f["engine"] == "boundary" for f in findings)


class TestOrchestrator:
    def test_run_on_over_merged_corpus(self, tmp_path):
        docs = tmp_path / "docs" / "generated"
        docs.mkdir(parents=True)
        (docs / "user-stories.md").write_text(_OVER_MERGED, encoding="utf-8")
        res = boundary_conformance.run(tmp_path, None, None, "web-js-ts", None)
        assert res["boundary_status"] == "OK"
        assert res["screen_source"] == "route-view"
        assert any(f["kind"] == "OVER_MERGE" for f in res["findings"])

    def test_absent_user_stories_ok_empty(self, tmp_path):
        res = boundary_conformance.run(tmp_path, None, None, None, None)
        assert res["boundary_status"] == "OK" and res["findings"] == []
        assert res["user_stories_present"] is False
