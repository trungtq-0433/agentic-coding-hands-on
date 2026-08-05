# layout-exempt: rebuild-spec — system scout block builder tests (v19)
"""Tests for the v19 scout block builders (DATA tables only — no Mermaid).

v19 BREAKING: Python no longer builds any Mermaid blocks. The Mermaid builder
functions (_build_topology_mermaid_block, _build_layer_mermaid_block,
_build_saga_sequence_block) and the template machinery (render_draft_from_template,
load_aggregate_template) are REMOVED from _synthesis_scout_lib.

Tests now cover:
- _build_edge_table_block: Markdown table, [UNVERIFIED] status
- _build_fan_in_out_table_block: Markdown table, correct counts
- build_scout_facts: returns DATA-only dict (no mermaid keys)
- assemble_scout_report: DATA sections only, no ```mermaid fences
- service_dependencies (unchanged utility in _system_synthesis_lib)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _synthesis_scout_lib import (  # noqa: E402
    _build_edge_table_block,
    _build_fan_in_out_table_block,
    assemble_scout_report,
    build_scout_facts,
)
from _system_synthesis_lib import build_interaction_edges, service_dependencies  # noqa: E402


ORDERS = {
    "service": "orders",
    "role": "domain-service",
    "stack": "spring",
    "generated_at": "2026-06-22T09:00:00Z",
    "source_sha": "aabbcc001",
    "rpc": [{"name": "PlaceOrder", "direction": "inbound", "message": "PlaceOrderReq"}],
    "topic": [{"name": "order.placed", "role": "producer", "event": "OrderPlaced"}],
    "entity": [{"name": "Order", "id_field": "orderId", "id_type": "uuid", "visibility": "public"}],
}

PAYMENT = {
    "service": "payment",
    "role": "domain-service",
    "stack": "nestjs",
    "generated_at": "2026-06-22T09:01:00Z",
    "source_sha": "bbccdd002",
    "rpc": [{"name": "ChargePayment", "direction": "inbound", "message": "ChargeReq"}],
    "topic": [
        {"name": "order.placed", "role": "consumer", "event": "OrderPlaced"},
        {"name": "payment.completed", "role": "producer", "event": "PaymentCompleted"},
    ],
    "entity": [{"name": "Payment", "id_field": "paymentId", "id_type": "uuid", "visibility": "public"}],
}

INVENTORY = {
    "service": "inventory",
    "role": "domain-service",
    "stack": "go",
    "generated_at": "2026-06-22T09:02:00Z",
    "source_sha": "ccddee003",
    "rpc": [],
    "topic": [{"name": "payment.completed", "role": "consumer", "event": "PaymentCompleted"}],
    "entity": [],
}


class TestEdgeTableBlock:
    """Verify _build_edge_table_block produces the expected Markdown table."""

    def test_has_header_row(self):
        out = _build_edge_table_block([])
        assert "| From | To | Type | Label | Status |" in out

    def test_no_edges_shows_none_detected(self):
        out = _build_edge_table_block([])
        assert "_(none detected)_" in out

    def test_edge_row_shows_unverified(self):
        edges = build_interaction_edges([ORDERS, PAYMENT])
        out = _build_edge_table_block(edges)
        assert "[UNVERIFIED]" in out
        assert "orders" in out
        assert "payment" in out

    def test_pipe_in_label_sanitized(self):
        """A topic name containing | must be sanitized in the table cell."""
        edges = [{"from": "a", "to": "b", "type": "async", "label": "ev|t", "verified": False}]
        out = _build_edge_table_block(edges)
        # sanitize_field escapes | to \|
        assert r"\|" in out


class TestFanInOutTableBlock:
    """Verify _build_fan_in_out_table_block produces the expected table."""

    def test_has_header_row(self):
        out = _build_fan_in_out_table_block([ORDERS, PAYMENT], [])
        assert "Fan-out" in out
        assert "Fan-in" in out

    def test_counts_correct(self):
        edges = build_interaction_edges([ORDERS, PAYMENT, INVENTORY])
        out = _build_fan_in_out_table_block([ORDERS, PAYMENT, INVENTORY], edges)
        assert "orders" in out
        assert "payment" in out


class TestBuildScoutFacts:
    """Verify build_scout_facts returns DATA-only blocks (no Mermaid keys)."""

    def test_returns_expected_data_keys(self):
        edges = build_interaction_edges([ORDERS, PAYMENT])
        facts = build_scout_facts(
            digests=[ORDERS, PAYMENT],
            edges=edges,
            suggestions=[],
            snap="testhash",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert "snapshot-hash" in facts
        assert "edge-table" in facts
        assert "fan-in-out-table" in facts
        assert "self-loop-topics" in facts
        assert "entity-ownership-table" in facts
        assert "correlation-table" in facts
        assert "event-flow-table" in facts
        assert "_services_table" in facts
        assert "_confidence_table" in facts

    def test_no_mermaid_keys_in_facts(self):
        """v19: no Mermaid keys in build_scout_facts — those are removed."""
        edges = build_interaction_edges([ORDERS, PAYMENT])
        facts = build_scout_facts(
            digests=[ORDERS, PAYMENT],
            edges=edges,
            suggestions=[],
            snap="testhash",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert "topology-mermaid" not in facts
        assert "layer-diagram-mermaid" not in facts
        assert "saga-sequence-mermaid" not in facts

    def test_snapshot_hash_value_stored(self):
        facts = build_scout_facts(
            digests=[ORDERS],
            edges=[],
            suggestions=[],
            snap="abc123def",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert facts["snapshot-hash"] == "abc123def"

    def test_services_table_has_reused_column(self):
        reused = dict(ORDERS, service="emp", provenance="docs-derived")
        facts = build_scout_facts(
            digests=[reused],
            edges=[],
            suggestions=[],
            snap="hash",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert "Reused" in facts["_services_table"]
        assert "yes" in facts["_services_table"]

    def test_services_table_has_docs_path_column(self):
        facts = build_scout_facts(
            digests=[ORDERS],
            edges=[],
            suggestions=[],
            snap="hash",
            abs_root="/tmp/myroot",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert "Docs path" in facts["_services_table"]
        assert "/tmp/myroot" in facts["_services_table"]


class TestAssembleScoutReport:
    """Verify assemble_scout_report emits DATA only — no Mermaid fences."""

    def _make_facts(self) -> dict[str, str]:
        edges = build_interaction_edges([ORDERS, PAYMENT])
        return build_scout_facts(
            digests=[ORDERS, PAYMENT],
            edges=edges,
            suggestions=[],
            snap="deadbeef",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )

    def test_no_mermaid_fences_in_report(self):
        """v19: scout report must NOT contain ```mermaid fences."""
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "```mermaid" not in report

    def test_report_has_services_section(self):
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "## Services" in report

    def test_report_has_edges_section(self):
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "## Edges" in report

    def test_report_has_confidence_section(self):
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "## Per-component Confidence" in report

    def test_snapshot_hash_in_comment(self):
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "snapshot-hash:" in report
        assert "deadbeef" in report

    def test_services_and_payment_in_report(self):
        facts = self._make_facts()
        report = assemble_scout_report(facts, "2026-06-25T00:00:00Z")
        assert "orders" in report
        assert "payment" in report


class TestServiceDependencies:
    """Verify service_dependencies resolves edges correctly (unchanged in v19)."""

    def test_service_dependencies_resolved_only(self):
        edges = build_interaction_edges([ORDERS, PAYMENT, INVENTORY])
        deps = service_dependencies(edges)
        assert isinstance(deps, dict)
        assert "orders" in deps
        assert "payment" in deps["orders"]

    def test_service_dependencies_sorted(self):
        edges = build_interaction_edges([ORDERS, PAYMENT, INVENTORY])
        deps = service_dependencies(edges)
        for svc_list in deps.values():
            assert svc_list == sorted(svc_list)

    def test_service_dependencies_unique(self):
        edges = build_interaction_edges([ORDERS, PAYMENT, INVENTORY])
        deps = service_dependencies(edges)
        for svc_list in deps.values():
            assert len(svc_list) == len(set(svc_list))

    def test_service_dependencies_empty_shows_none(self):
        edges = build_interaction_edges([INVENTORY])
        deps = service_dependencies(edges)
        assert deps.get("inventory", []) == []

    def test_service_dependencies_includes_services_with_outbound_edges(self):
        edges = build_interaction_edges([ORDERS, PAYMENT, INVENTORY])
        deps = service_dependencies(edges)
        assert "orders" in deps
        assert "payment" in deps
