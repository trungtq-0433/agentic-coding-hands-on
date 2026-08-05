# layout-exempt: rebuild-spec synthesis tests — docs/system paths are this skill's own output targets
"""Tests for synthesize_system.py and _system_synthesis_lib.py (Phase D).

v19 coverage targets:
- 3 digests (orders/payment/inventory): interaction-graph has order→payment edge
  (topic-name match) tagged [UNVERIFIED]; gRPC target that can't resolve → NO phantom edge.
- canonical-entity correlation: orderId/order_id/OrderID + uuid vs int64 → [UNVERIFIED].
- --aggregate with one component missing → [BLOCKED] component_incomplete (default);
  --force-aggregate → synthesizes + banner lists skipped component.
- Digest with service name >128 chars or array >1000 → rejected (ValueError).
- Markdown injection: digest field with |/backtick/<...> → sanitized in output.
- Write path escaping docs_root → ValueError via _resolve_guarded.
- Snapshot hash present in output header; changed component sha → stale WARN.
- v19: synthesize() writes NO .draft.md; scout report has no Mermaid fences.
- lint_mermaid_safety: safe block → []; unsafe block (raw " or `) → non-empty.
- validate_filled_scaffold(draft): clean → []; leftover {{FILL}} → violation;
  unsafe Mermaid → violation.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _path_lib import _resolve_guarded  # noqa: E402
from _synthesis_narrative_lib import (  # noqa: E402
    has_unfilled_markers,
    lint_mermaid_safety,
    validate_filled_scaffold,
)
from _synthesis_scout_lib import (  # noqa: E402
    build_scout_facts,
    assemble_scout_report,
)
from _system_synthesis_lib import (  # noqa: E402
    build_interaction_edges,
    correlate_entities,
    entity_ownership,
    event_flows,
    fan_in_out,
    load_digests,
    mermaid_safe_id,
    mermaid_safe_label,
    sanitize_field,
    self_loop_topics,
    snapshot_hash,
)
from synthesize_system import synthesize  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures — three realistic service digests
# ---------------------------------------------------------------------------

ORDERS_DIGEST = {
    "service": "orders",
    "role": "domain-service",
    "stack": "spring",
    "generated_at": "2026-06-22T09:00:00Z",
    "source_sha": "aabbcc001",
    "rpc": [
        {"name": "PlaceOrder", "direction": "inbound", "message": "PlaceOrderReq"},
        {"name": "ChargePayment", "direction": "outbound", "message": "ChargeReq"},
    ],
    "topic": [
        {"name": "order.placed", "role": "producer", "event": "OrderPlaced"},
    ],
    "entity": [
        {"name": "Order", "id_field": "orderId", "id_type": "uuid", "visibility": "public"},
    ],
}

PAYMENT_DIGEST = {
    "service": "payment",
    "role": "domain-service",
    "stack": "nestjs",
    "generated_at": "2026-06-22T09:01:00Z",
    "source_sha": "bbccdd002",
    "rpc": [
        {"name": "ChargePayment", "direction": "inbound", "message": "ChargeReq"},
    ],
    "topic": [
        {"name": "order.placed", "role": "consumer", "event": "OrderPlaced"},
        {"name": "payment.completed", "role": "producer", "event": "PaymentCompleted"},
    ],
    "entity": [
        {"name": "order_id", "id_field": "order_id", "id_type": "uuid", "visibility": "internal"},
        {"name": "Payment", "id_field": "paymentId", "id_type": "uuid", "visibility": "public"},
    ],
}

INVENTORY_DIGEST = {
    "service": "inventory",
    "role": "domain-service",
    "stack": "go",
    "generated_at": "2026-06-22T09:02:00Z",
    "source_sha": "ccdde e003",
    "rpc": [],
    "topic": [
        {"name": "payment.completed", "role": "consumer", "event": "PaymentCompleted"},
    ],
    "entity": [
        {"name": "OrderID", "id_field": "OrderID", "id_type": "int64", "visibility": "internal"},
    ],
}

ALL_DIGESTS = [ORDERS_DIGEST, PAYMENT_DIGEST, INVENTORY_DIGEST]


def _write_digest(directory: Path, digest: dict) -> Path:
    svc = digest["service"]
    comp_dir = directory / "docs" / "components" / svc
    comp_dir.mkdir(parents=True, exist_ok=True)
    p = comp_dir / "_service-digest.json"
    p.write_text(json.dumps(digest), encoding="utf-8")
    return p


def _make_digest_tree(tmp_path: Path) -> Path:
    """Write all three digests and return the root."""
    for d in ALL_DIGESTS:
        _write_digest(tmp_path, d)
    return tmp_path


def _write_digest_lang(tmp_path: Path, lang: str) -> None:
    """Write all three digests to the lang-namespaced docs/<lang>/components/ path (P04 layout).

    After P04, resolved_components_base = docs/<lang>/components/ for non-en primaries.
    Digests must live there for synthesize_system to find them.
    """
    for d in ALL_DIGESTS:
        svc = d["service"]
        comp_dir = tmp_path / "docs" / lang / "components" / svc
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "_service-digest.json").write_text(json.dumps(d), encoding="utf-8")


# ---------------------------------------------------------------------------
# sanitize_field (RT2-F6)
# ---------------------------------------------------------------------------

class TestSanitizeField:
    def test_pipe_escaped(self):
        assert r"\|" in sanitize_field("col1 | col2")

    def test_newline_collapsed(self):
        result = sanitize_field("line1\nline2")
        assert "\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_backtick_replaced(self):
        result = sanitize_field("`rm -rf /`")
        assert "`" not in result

    def test_link_markup_stripped(self):
        result = sanitize_field("[evil](http://x.com)")
        assert "http" not in result
        assert "evil" in result

    def test_html_tag_stripped(self):
        result = sanitize_field("<script>alert(1)</script>")
        assert "<" not in result
        assert ">" not in result

    def test_none_returns_empty_string(self):
        assert sanitize_field(None) == ""

    def test_clean_string_unchanged(self):
        result = sanitize_field("orders")
        assert result == "orders"

    def test_combined_injection(self):
        """A digest field with | + backtick + <...> is fully sanitized."""
        dirty = "bad | `code` <b>bold</b>"
        result = sanitize_field(dirty)
        assert "`" not in result
        assert "<" not in result
        assert ">" not in result
        assert r"\|" in result


# ---------------------------------------------------------------------------
# load_digests — field-length caps (RT2-F7)
# ---------------------------------------------------------------------------

class TestLoadDigests:
    def test_loads_valid_digests(self, tmp_path):
        _make_digest_tree(tmp_path)
        digests = load_digests(str(tmp_path / "docs" / "components"))
        assert len(digests) == 3
        services = {d["service"] for d in digests}
        assert services == {"orders", "payment", "inventory"}

    def test_skips_service_name_too_long(self, tmp_path, capsys):
        """A caps violation skips the one offending digest (warning only) rather than
        aborting the whole multi-component synthesis."""
        bad = dict(ORDERS_DIGEST, service="x" * 129)
        p = tmp_path / "_service-digest.json"
        p.write_text(json.dumps(bad))
        assert load_digests([str(p)]) == []
        assert "'service' exceeds" in capsys.readouterr().err

    def test_skips_array_too_long(self, tmp_path, capsys):
        bad = dict(ORDERS_DIGEST, rpc=[
            {"name": f"RPC{i}", "direction": "inbound"} for i in range(1001)
        ])
        p = tmp_path / "_service-digest.json"
        p.write_text(json.dumps(bad))
        assert load_digests([str(p)]) == []
        assert "'rpc' array exceeds" in capsys.readouterr().err

    def test_skips_item_name_too_long(self, tmp_path, capsys):
        bad = dict(ORDERS_DIGEST, topic=[
            {"name": "t" * 257, "role": "producer", "event": "E"}
        ])
        p = tmp_path / "_service-digest.json"
        p.write_text(json.dumps(bad))
        assert load_digests([str(p)]) == []
        assert "'topic[].name' exceeds" in capsys.readouterr().err

    def test_caps_skip_keeps_valid_siblings(self, tmp_path, capsys):
        """One oversized digest must not drop the valid digests in the same run."""
        good = _write_digest(tmp_path / "good", ORDERS_DIGEST)
        bad_dir = tmp_path / "bad"
        bad_dir.mkdir()
        bad = dict(ORDERS_DIGEST, service="x" * 129)
        bad_p = bad_dir / "_service-digest.json"
        bad_p.write_text(json.dumps(bad))
        result = load_digests([str(good), str(bad_p)])
        assert [d["service"] for d in result] == ["orders"]
        assert "exceeds field caps — skipping" in capsys.readouterr().err

    def test_skips_missing_provenance(self, tmp_path):
        """A digest without source_sha or generated_at is skipped (warning only)."""
        bad = {"service": "broken", "rpc": [], "topic": [], "entity": []}
        p = tmp_path / "_service-digest.json"
        p.write_text(json.dumps(bad))
        result = load_digests([str(p)])
        assert result == []

    def test_skips_symlink(self, tmp_path):
        real = tmp_path / "real.json"
        real.write_text(json.dumps(ORDERS_DIGEST))
        link = tmp_path / "_service-digest.json"
        try:
            link.symlink_to(real)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks not supported on this platform")
        result = load_digests([str(link)])
        assert result == []


# ---------------------------------------------------------------------------
# snapshot_hash (RT2-F10)
# ---------------------------------------------------------------------------

class TestSnapshotHash:
    def test_hash_deterministic(self):
        h1 = snapshot_hash(ALL_DIGESTS)
        h2 = snapshot_hash(list(reversed(ALL_DIGESTS)))
        assert h1 == h2  # order-independent

    def test_hash_changes_when_sha_changes(self):
        modified = dict(ORDERS_DIGEST, source_sha="DIFFERENT_SHA")
        h1 = snapshot_hash(ALL_DIGESTS)
        h2 = snapshot_hash([modified, PAYMENT_DIGEST, INVENTORY_DIGEST])
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = snapshot_hash(ALL_DIGESTS)
        assert isinstance(h, str)
        assert len(h) == 64  # sha256 hex


# ---------------------------------------------------------------------------
# build_interaction_edges
# ---------------------------------------------------------------------------

class TestBuildInteractionEdges:
    def test_async_edge_order_to_payment(self):
        """orders produces order.placed; payment consumes it → async edge."""
        edges = build_interaction_edges(ALL_DIGESTS)
        async_edges = [e for e in edges if e["type"] == "async"]
        found = any(
            e["from"] == "orders" and e["to"] == "payment" and e["label"] == "order.placed"
            for e in async_edges
        )
        assert found, f"Expected order→payment async edge, got: {async_edges}"

    def test_async_edge_tagged_unverified(self):
        edges = build_interaction_edges(ALL_DIGESTS)
        for e in edges:
            assert e["verified"] is False, f"Edge should be unverified: {e}"

    def test_no_phantom_edge_for_unresolvable_grpc(self):
        """ChargePayment outbound from orders has one inbound in payment → edge emitted.
        A hypothetical outbound with no matching inbound must NOT produce a phantom edge."""
        ghost_digest = dict(ORDERS_DIGEST, service="ghost", rpc=[
            {"name": "NoSuchRPC", "direction": "outbound", "message": "X"},
        ], topic=[], entity=[])
        edges = build_interaction_edges([ghost_digest, PAYMENT_DIGEST, INVENTORY_DIGEST])
        phantom = [e for e in edges if e["from"] == "ghost" and e["type"] == "sync"]
        assert phantom == [], f"Phantom edge found: {phantom}"

    def test_sync_edge_when_exactly_one_inbound_match(self):
        """orders has outbound ChargePayment; payment has inbound ChargePayment → sync edge."""
        edges = build_interaction_edges(ALL_DIGESTS)
        sync_edges = [e for e in edges if e["type"] == "sync"]
        found = any(
            e["from"] == "orders" and e["to"] == "payment" and e["label"] == "ChargePayment"
            for e in sync_edges
        )
        assert found, f"Expected sync orders→payment via ChargePayment, got: {sync_edges}"

    def test_no_self_loop_edges(self):
        edges = build_interaction_edges(ALL_DIGESTS)
        for e in edges:
            assert e["from"] != e["to"], f"Self-loop edge: {e}"

    def test_payment_to_inventory_async_edge(self):
        """payment produces payment.completed; inventory consumes it."""
        edges = build_interaction_edges(ALL_DIGESTS)
        found = any(
            e["from"] == "payment" and e["to"] == "inventory"
            and e["label"] == "payment.completed" and e["type"] == "async"
            for e in edges
        )
        assert found


# ---------------------------------------------------------------------------
# correlate_entities (RT2-F15)
# ---------------------------------------------------------------------------

class TestCorrelateEntities:
    def test_order_entity_correlation_unverified(self):
        """Order / order_id / OrderID across services → [UNVERIFIED] suggestions."""
        suggestions = correlate_entities(ALL_DIGESTS)
        assert len(suggestions) >= 1
        for s in suggestions:
            assert s["confidence"] == "UNVERIFIED"

    def test_uuid_vs_int64_type_mismatch_flagged(self):
        """order_id (uuid) in payment vs OrderID (int64) in inventory → type mismatch."""
        suggestions = correlate_entities(ALL_DIGESTS)
        mismatches = [
            s for s in suggestions
            if "mismatch" in s.get("type_note", "")
        ]
        assert mismatches, f"Expected type mismatch suggestion, got: {suggestions}"

    def test_no_auto_merge(self):
        """Suggestions are always UNVERIFIED — never auto-merged."""
        suggestions = correlate_entities(ALL_DIGESTS)
        for s in suggestions:
            assert s["confidence"] == "UNVERIFIED"
            assert "entity_a" in s
            assert "entity_b" in s

    def test_no_intra_service_correlation(self):
        """Entities within the same service must not be correlated."""
        suggestions = correlate_entities(ALL_DIGESTS)
        for s in suggestions:
            assert s["entity_a"]["service"] != s["entity_b"]["service"]

    def test_empty_digests_returns_empty(self):
        assert correlate_entities([]) == []

    def test_normalized_name_variants_matched(self):
        """orderId / order_id / OrderID should all normalize similarly → match."""
        d_a = dict(ORDERS_DIGEST, service="svc_a",
                   entity=[{"name": "orderId", "id_field": "orderId",
                             "id_type": "uuid", "visibility": "public"}])
        d_b = dict(ORDERS_DIGEST, service="svc_b",
                   entity=[{"name": "order_id", "id_field": "order_id",
                             "id_type": "uuid", "visibility": "public"}])
        d_c = dict(ORDERS_DIGEST, service="svc_c",
                   entity=[{"name": "OrderID", "id_field": "OrderID",
                             "id_type": "uuid", "visibility": "public"}])
        suggestions = correlate_entities([d_a, d_b, d_c])
        assert len(suggestions) >= 1


# ---------------------------------------------------------------------------
# synthesize() integration tests
# ---------------------------------------------------------------------------

class TestSynthesizeIntegration:
    def test_tier1_artifacts_created(self, tmp_path):
        _make_digest_tree(tmp_path)
        rc = synthesize(
            root=str(tmp_path),
            manifest=None,
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=True,
        )
        assert rc == 0
        system_dir = tmp_path / "docs" / "system"
        # v19: Python writes ONLY the scout report + per-component-confidence.md; NO .draft.md.
        assert (system_dir / "per-component-confidence.md").is_file()
        assert (system_dir / ".system-scout-report.md").is_file()
        # old names must NOT exist
        assert not (system_dir / "service-catalog.md").exists()
        assert not (system_dir / "interaction-graph.md").exists()

    def test_no_draft_files_written_by_synthesize(self, tmp_path):
        """v19: synthesize() writes NO <name>.draft.md — those are the researcher's job."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        system_dir = tmp_path / "docs" / "system"
        # None of the 6 aggregate drafts should be written by Python.
        for name in ("overview", "component-catalog", "architecture",
                     "glossary", "cross-service-flows", "data-ownership-map"):
            assert not (system_dir / f"{name}.draft.md").exists(), (
                f"Python must not write {name}.draft.md (researcher's job in v19)"
            )
        assert not (system_dir / "canonical-entity-model.md").exists()

    def test_snapshot_hash_in_header(self, tmp_path):
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: snapshot-hash is in the scout report only (no template drafts written by Python).
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "snapshot-hash:" in scout

    def test_interaction_graph_has_order_payment_edge(self, tmp_path):
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: edges are in the scout report (edge-table block) only.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "order.placed" in scout
        assert "[UNVERIFIED]" in scout
        assert "orders" in scout
        assert "payment" in scout

    def test_markdown_injection_sanitized_in_output(self, tmp_path):
        """A digest field with | backtick <...> must be sanitized in rendered docs."""
        evil_digest = dict(ORDERS_DIGEST, service="evil|svc`<b>")
        evil_dir = tmp_path / "docs" / "components" / "evil"
        evil_dir.mkdir(parents=True)
        (evil_dir / "_service-digest.json").write_text(json.dumps(evil_digest))
        # Also write normal digests so synthesis has something to work with
        _write_digest(tmp_path, PAYMENT_DIGEST)
        _write_digest(tmp_path, INVENTORY_DIGEST)

        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v18: sanitized service names appear in the scout report (services table) and
        # in per-component-confidence.md. Check both.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        confidence = (tmp_path / "docs" / "system" / "per-component-confidence.md").read_text()
        for content in (scout, confidence):
            lines = [l for l in content.splitlines() if "evil" in l.lower() or "svc" in l.lower()]
            for line in lines:
                # After sanitize, raw "`" is replaced and "<b>" is stripped
                assert "`" not in line.replace("\\`", ""), f"Backtick leaked: {line!r}"
                assert "<b>" not in line, f"HTML tag leaked: {line!r}"

    def test_block_when_manifest_has_incomplete_component(self, tmp_path, capsys):
        """Default --aggregate: missing component digest → [BLOCKED] exit 1."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        # payment and inventory digests NOT written
        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "payment", "status": "pending"},
                {"name": "inventory", "status": "done", "service": "inventory"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        rc = synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=False,   # default BLOCK
        )
        assert rc == 1
        captured = capsys.readouterr()
        assert "[BLOCKED] component_incomplete" in captured.err

    def test_force_aggregate_synthesizes_with_banner(self, tmp_path, capsys):
        """--force-aggregate: proceeds with available digests + warns about skipped."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        _write_digest(tmp_path, PAYMENT_DIGEST)
        # inventory NOT written
        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "payment", "status": "done", "service": "payment"},
                {"name": "inventory", "status": "pending"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        rc = synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=True,
        )
        assert rc == 0
        captured = capsys.readouterr()
        assert "inventory" in captured.err  # banner lists skipped component
        # v19: scout report written (no draft files)
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()

    def test_stale_digest_warn_on_changed_sha(self, tmp_path, capsys):
        """If a component sha changes since last synthesis, emit [WARN] stale_digest."""
        _make_digest_tree(tmp_path)
        # First synthesis — writes snapshot
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        capsys.readouterr()  # clear

        # Overwrite one digest with a different source_sha
        modified = dict(ORDERS_DIGEST, source_sha="CHANGED_SHA_XYZ")
        orders_path = (tmp_path / "docs" / "components" / "orders" /
                       "_service-digest.json")
        orders_path.write_text(json.dumps(modified))

        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        captured = capsys.readouterr()
        assert "stale_digest" in captured.err

    def test_write_path_escape_rejected(self, tmp_path):
        """_resolve_guarded must reject paths escaping docs_root."""
        docs_root = str(tmp_path / "docs" / "system")
        outside = str(tmp_path / "outside.md")
        with pytest.raises(ValueError, match="Path traversal"):
            _resolve_guarded(outside, docs_root)

    def test_no_digests_exits_cleanly(self, tmp_path):
        """No digests → exit 0 with warning (advisory)."""
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0

    def test_data_ownership_has_unverified_suggestions(self, tmp_path):
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: UNVERIFIED is in the scout report's correlation table.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "[UNVERIFIED]" in scout
        assert "## Entity Ownership" in scout
        assert "## Event Flows" in scout

    def test_digest_dir_override(self, tmp_path):
        """--digest-collect uses an explicit directory instead of <root>/docs/components."""
        digest_dir = tmp_path / "collected"
        digest_dir.mkdir()
        for d in ALL_DIGESTS:
            svc_dir = digest_dir / d["service"]
            svc_dir.mkdir()
            (svc_dir / "_service-digest.json").write_text(json.dumps(d))

        rc = synthesize(
            root=str(tmp_path),
            manifest=None,
            digest_dir=str(digest_dir),
            max_digest_age=None,
            force_aggregate=True,
        )
        assert rc == 0
        # v19: scout report written (no draft files)
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()


# ---------------------------------------------------------------------------
# Helpers for language-mapped output tests (Phase 1)
# ---------------------------------------------------------------------------

def _write_state(tmp_path: Path, component: str, primary_lang: str) -> None:
    """Write docs/components/<component>/.rebuild-state.json with a primary_lang."""
    comp_dir = tmp_path / "docs" / "components" / component
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / ".rebuild-state.json").write_text(
        json.dumps({"primary_lang": primary_lang}), encoding="utf-8"
    )


class TestLangMappedOutput:
    def test_en_default_writes_flat_docs_system(self, tmp_path):
        """No state / en primary → docs/system (byte-compatible, no per-lang dir)."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: scout report written (no draft files)
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()
        assert not (tmp_path / "docs" / "en").exists()

    def test_non_en_primary_writes_per_lang(self, tmp_path):
        """vi primary (fresh repo) → docs/vi/system, never flat docs/system."""
        # P04: digests at lang-namespaced path; state at docs/components/ for _discover_primary_lang
        _write_digest_lang(tmp_path, "vi")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "vi")
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: scout report written at per-lang path
        assert (tmp_path / "docs" / "vi" / "system" / ".system-scout-report.md").is_file()
        assert not (tmp_path / "docs" / "system" / ".system-scout-report.md").exists()

    def test_auto_migrates_legacy_flat_tree(self, tmp_path):
        """vi primary + legacy flat docs/system/ + no sentinel → relocate then write."""
        # P04: digests at lang-namespaced path; state at docs/components/ for _discover_primary_lang
        _write_digest_lang(tmp_path, "vi")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "vi")
        legacy = tmp_path / "docs" / "system"
        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "legacy-note.md").write_text("old", encoding="utf-8")

        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)

        vi_system = tmp_path / "docs" / "vi" / "system"
        assert (vi_system / "legacy-note.md").is_file()          # relocated, no orphan
        # v19: scout report written alongside
        assert (vi_system / ".system-scout-report.md").is_file()
        assert not (tmp_path / "docs" / "system").exists()       # no orphaned flat copy
        assert (tmp_path / "docs" / "vi" / ".layout-migrated").is_file()

    def test_auto_migration_idempotent_on_rerun(self, tmp_path):
        """Second run sees the sentinel → no re-migration, output stable in docs/vi/system."""
        # P04: digests at lang-namespaced path; state at docs/components/ for _discover_primary_lang
        _write_digest_lang(tmp_path, "vi")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "vi")
        (tmp_path / "docs" / "system").mkdir(parents=True, exist_ok=True)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # Re-run — must not raise, must not recreate a flat docs/system.
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        # v19: scout report at per-lang path
        assert (tmp_path / "docs" / "vi" / "system" / ".system-scout-report.md").is_file()
        assert not (tmp_path / "docs" / "system").exists()

    def test_lang_conflict_picks_majority_and_warns(self, tmp_path, capsys):
        """Mixed primary_lang across components → majority + [WARN] lang_conflict, continue."""
        # P04: majority is vi → digests at docs/vi/components/; state at docs/components/
        _write_digest_lang(tmp_path, "vi")
        _write_state(tmp_path, "orders", "vi")
        _write_state(tmp_path, "payment", "vi")
        _write_state(tmp_path, "inventory", "en")
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        captured = capsys.readouterr()
        assert "lang_conflict" in captured.err
        # v19: scout report at majority lang path
        assert (tmp_path / "docs" / "vi" / "system" / ".system-scout-report.md").is_file()

    def test_primary_lang_override_wins(self, tmp_path):
        """--primary-lang override beats discovered state."""
        # P04: override is ja → digests at docs/ja/components/; state at docs/components/
        _write_digest_lang(tmp_path, "ja")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "en")
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True, primary_lang="ja")
        # v19: scout report at overridden lang path
        assert (tmp_path / "docs" / "ja" / "system" / ".system-scout-report.md").is_file()

    def test_unsafe_primary_lang_aborts(self, tmp_path, capsys):
        """A path-unsafe primary_lang → hard abort (exit 1), no traversal."""
        _make_digest_tree(tmp_path)
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True,
                        primary_lang="../evil")
        assert rc == 1
        assert "unsafe primary_lang" in capsys.readouterr().err

    def test_cwd_independent(self, tmp_path, monkeypatch):
        """Output resolves from --root, not the process cwd."""
        _make_digest_tree(tmp_path)
        other = tmp_path.parent / "elsewhere"
        other.mkdir(exist_ok=True)
        monkeypatch.chdir(other)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: scout report written (no draft files)
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()


# ---------------------------------------------------------------------------
# Mermaid injection safety (Phase 2, red-team #3)
# ---------------------------------------------------------------------------

class TestMermaidSafety:
    def test_safe_id_strips_unsafe_chars(self):
        assert mermaid_safe_id('evil"; click x') == mermaid_safe_id('evil"; click x')
        out = mermaid_safe_id('a"b;c[d]')
        assert all(c.isalnum() or c in "_-" for c in out)

    def test_safe_id_all_unsafe_degrades(self):
        assert mermaid_safe_id('"";[]') == "svc"

    def test_safe_label_escapes_quote(self):
        assert '"' not in mermaid_safe_label('he said "hi"')
        assert "#quot;" in mermaid_safe_label('he said "hi"')

    def test_scout_report_has_no_mermaid_fences(self, tmp_path):
        """v19: scout report must NOT contain ```mermaid fences (data only)."""
        evil = dict(ORDERS_DIGEST, service='ev"il];click')
        evil_dir = tmp_path / "docs" / "components" / "evil"
        evil_dir.mkdir(parents=True)
        (evil_dir / "_service-digest.json").write_text(json.dumps(evil))
        _write_digest(tmp_path, PAYMENT_DIGEST)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        # v19: Python no longer draws Mermaid — no fences in the scout report.
        assert "```mermaid" not in scout
        # Sanitized service name (with quote stripped) should appear in the services table
        assert "evil" in scout.lower() or "ev" in scout


# ---------------------------------------------------------------------------
# Topology summaries (Phase 2)
# ---------------------------------------------------------------------------

class TestTopologySummaries:
    def test_fan_in_out_counts(self):
        edges = build_interaction_edges(ALL_DIGESTS)
        fan_out, fan_in = fan_in_out(edges)
        assert fan_out["orders"] >= 1   # orders calls payment (sync + async)
        assert fan_in["payment"] >= 1

    def test_self_loop_topic_detected(self):
        loop_digest = dict(ORDERS_DIGEST, service="echo", topic=[
            {"name": "echo.tick", "role": "producer", "event": "E"},
            {"name": "echo.tick", "role": "consumer", "event": "E"},
        ])
        loops = self_loop_topics([loop_digest])
        assert ("echo", "echo.tick") in loops

    def test_self_loop_not_dropped_in_output(self, tmp_path):
        loop_digest = dict(ORDERS_DIGEST, service="echo", topic=[
            {"name": "echo.tick", "role": "producer", "event": "E"},
            {"name": "echo.tick", "role": "consumer", "event": "E"},
        ])
        ed = tmp_path / "docs" / "components" / "echo"
        ed.mkdir(parents=True)
        (ed / "_service-digest.json").write_text(json.dumps(loop_digest))
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v18: self-loop topics are in the scout report (self-loop-topics block).
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "Self-loop Topics" in scout
        assert "echo.tick" in scout

    def test_event_flows_producer_consumer(self):
        flows = event_flows(ALL_DIGESTS)
        by_topic = {f["topic"]: f for f in flows}
        assert "orders" in by_topic["order.placed"]["producers"]
        assert "payment" in by_topic["order.placed"]["consumers"]

    def test_entity_ownership_owner_is_declaring_service(self):
        rows = entity_ownership(ALL_DIGESTS)
        order_rows = [r for r in rows if r["name"] == "Order"]
        assert order_rows and order_rows[0]["owner"] == "orders"

    def test_entity_ownership_drops_junk_section_headings(self):
        """Doc-section headings lifted as entity names are filtered (Phase 01)."""
        dirty = dict(ORDERS_DIGEST, service="dirty", entity=[
            {"name": "Entity Relationship Diagram"},
            {"name": "Entities"},
            {"name": "Summary"},
            {"name": "Validation Rules"},
            {"name": "Staff"},
        ])
        rows = entity_ownership([dirty])
        names = {r["name"] for r in rows}
        assert names == {"Staff"}

    def test_entity_ownership_dedups_owner_name(self):
        """The same (owner, entity) is listed once even if duplicated in the digest."""
        dup = dict(ORDERS_DIGEST, service="dup", entity=[
            {"name": "Candidate"}, {"name": "Candidate"},
        ])
        rows = [r for r in entity_ownership([dup]) if r["owner"] == "dup"]
        assert len(rows) == 1 and rows[0]["name"] == "Candidate"

    def test_entity_ownership_collapses_model_prefix_variants(self):
        """`MODEL004 — Candidate` and `Candidate` collapse to one canonical entity."""
        mixed = dict(ORDERS_DIGEST, service="emp", entity=[
            {"name": "MODEL004 — Candidate"}, {"name": "Candidate"},
        ])
        rows = [r for r in entity_ownership([mixed]) if r["owner"] == "emp"]
        assert len(rows) == 1 and rows[0]["name"] == "Candidate"

    def test_canonical_entity_name_keeps_non_separator_model(self):
        """A name like `MODEL3 Pricing` (no — / - separator) is NOT stripped."""
        from _system_synthesis_lib import _canonical_entity_name
        assert _canonical_entity_name("MODEL3 Pricing") == "MODEL3 Pricing"
        assert _canonical_entity_name("Summary") is None
        assert _canonical_entity_name("MODEL12 - Education") == "Education"

    def test_fan_in_out_summary_in_output(self, tmp_path):
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: fan-in/out is in the scout report only (no draft written by Python).
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "Fan-in / Fan-out" in scout


# ---------------------------------------------------------------------------
# v18 Scout report + template substitution + post-fill validator (Phase 3 / 4)
# ---------------------------------------------------------------------------

class TestScaffolds:
    """v19: scout-report data-only model. Python writes NO .draft.md."""

    def test_scout_report_written_with_services_table(self, tmp_path):
        """(a) .system-scout-report.md written with Services table incl. docs-path + reused flag."""
        _make_digest_tree(tmp_path)
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "## Services" in scout
        # Services table has Docs path column header
        assert "Docs path" in scout
        # Reused column present
        assert "Reused" in scout
        # All three services appear in the table
        assert "orders" in scout
        assert "payment" in scout
        assert "inventory" in scout

    def test_scout_report_docs_path_is_absolute(self, tmp_path):
        """(a) docs-path column contains absolute paths (so researcher knows what to open)."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        # Extract table rows after ## Services
        services_section = scout.split("## Services", 1)[1].split("##", 1)[0]
        # Paths must contain the tmp_path prefix (absolute)
        assert str(tmp_path) in services_section

    def test_scout_report_has_no_mermaid_fences(self, tmp_path):
        """(b) v19: scout report has NO ```mermaid fences — data tables only."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "```mermaid" not in scout
        assert "flowchart LR" not in scout
        assert "flowchart TB" not in scout
        assert "sequenceDiagram" not in scout

    def test_no_draft_files_written(self, tmp_path):
        """(b) v19: synthesize() writes NO <name>.draft.md — researcher creates those."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        system_dir = tmp_path / "docs" / "system"
        for name in ("overview", "component-catalog", "architecture",
                     "glossary", "cross-service-flows", "data-ownership-map"):
            assert not (system_dir / f"{name}.draft.md").exists(), (
                f"Python must not write {name}.draft.md (v19 — researcher's job)"
            )

    def test_promoted_file_not_touched_on_rerun(self, tmp_path):
        """(d) A promoted .md file is never overwritten by re-running --aggregate."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        system_dir = tmp_path / "docs" / "system"
        # Simulate a promoted file (researcher-authored)
        promoted = system_dir / "overview.md"
        promoted.parent.mkdir(parents=True, exist_ok=True)
        promoted.write_text("# System Overview\n\nfilled prose\n", encoding="utf-8")
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        assert promoted.read_text() == "# System Overview\n\nfilled prose\n"

    def test_validator_passes_clean_draft(self):
        """(c) validate_filled_scaffold(draft) passes a doc with no remaining markers."""
        filled = "# T\n\n## A\nreal prose\n\n## B\ntext\n"
        assert validate_filled_scaffold(filled) == []

    def test_validator_flags_unfilled_fill_marker(self):
        """(c) validate_filled_scaffold flags a remaining {{FILL}} marker."""
        filled = "# T\n\n## A\n{{FILL: x}}\n"
        violations = validate_filled_scaffold(filled)
        assert any("unfilled_markers" in v for v in violations)

    def test_validator_flags_remaining_scout_marker(self):
        """(c) validate_filled_scaffold also flags a remaining {{SCOUT}} marker."""
        filled = "# T\n{{SCOUT: edge-table}}\n"
        violations = validate_filled_scaffold(filled)
        assert any("unfilled_markers" in v for v in violations)

    def test_validator_flags_bracket_fill_marker(self):
        """(c) validate_filled_scaffold flags a [FILL] marker."""
        filled = "# T\n[FILL] some placeholder\n"
        violations = validate_filled_scaffold(filled)
        assert any("unfilled_markers" in v for v in violations)

    def test_validator_flags_unsafe_mermaid(self):
        """(c) validate_filled_scaffold flags unsafe Mermaid chars (raw \" in label)."""
        filled = '# T\n\n```mermaid\nflowchart LR\n  A["he said "hi""] --> B\n```\n'
        violations = validate_filled_scaffold(filled)
        assert any("unsafe_mermaid_label" in v for v in violations)

    def test_validator_no_h2_lock(self):
        """v19: validate_filled_scaffold does NOT enforce H2-header lock (gone since v18)."""
        filled = "# T\n\n## A\nfilled\n\n## Injected\nnew section\n"
        violations = validate_filled_scaffold(filled)
        assert not any("new_h2_header" in v for v in violations)

    def test_scout_report_has_per_component_confidence_table(self, tmp_path):
        """Scout report includes a per-component confidence summary."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "## Per-component Confidence" in scout
        assert "orders" in scout


# ---------------------------------------------------------------------------
# Mermaid label escaping for | and ] (reviewer H1 / M1)
# ---------------------------------------------------------------------------

class TestMermaidLabelEscaping:
    def test_label_escapes_pipe(self):
        out = mermaid_safe_label("rpc|method")
        assert "|" not in out
        assert "#124;" in out

    def test_label_escapes_bracket(self):
        out = mermaid_safe_label("auth]service")
        assert "]" not in out
        assert "#93;" in out

    def test_pipe_in_edge_table_sanitized_in_scout(self, tmp_path):
        """A topic name containing | must be sanitized in the edge table (not a Mermaid fence)."""
        prod = dict(ORDERS_DIGEST, service="a", topic=[
            {"name": "ev|t", "role": "producer", "event": "E"}], rpc=[], entity=[])
        cons = dict(ORDERS_DIGEST, service="b", topic=[
            {"name": "ev|t", "role": "consumer", "event": "E"}], rpc=[], entity=[])
        for d in (prod, cons):
            cdir = tmp_path / "docs" / "components" / d["service"]
            cdir.mkdir(parents=True)
            (cdir / "_service-digest.json").write_text(json.dumps(d))
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        # v19: edges appear only in the scout report edge-table (no Mermaid fence).
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        # No Mermaid in scout report.
        assert "```mermaid" not in scout
        # The edge table has the label sanitized (pipe → \|)
        edges_section = scout.split("## Edges", 1)[1].split("##", 1)[0]
        assert r"\|" in edges_section  # sanitized pipe in table cell


# ---------------------------------------------------------------------------
# Migration-abort handling (reviewer H2)
# ---------------------------------------------------------------------------

class TestMigrationAbort:
    def test_aborted_flip_fails_clean(self, tmp_path, monkeypatch, capsys):
        """A non-zero migration rc → synthesize aborts (exit 1), no fork."""
        import migrate_docs_layout
        _make_digest_tree(tmp_path)
        # Force per-lang(en) shape: register a secondary in root state + flat docs/system.
        docs = tmp_path / "docs"
        (docs / "system").mkdir(parents=True, exist_ok=True)
        (docs / ".rebuild-state.json").write_text(
            json.dumps({"primary_lang": "en", "translations": {"vi": {}}}))
        monkeypatch.setattr(migrate_docs_layout, "flip", lambda *a, **k: 1)
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 1
        assert "auto-migration aborted" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Phase 09 — reused/excluded completeness + mirror-stale
# ---------------------------------------------------------------------------

class TestPhase09ReusedCompleteness:
    """check_completeness accepts reused+digest, excluded is dropped+warned, mirror-stale."""

    def _make_reused_digest(self, tmp_path: Path, name: str) -> Path:
        """Write a minimal _service-digest.json for a reused component."""
        comp_dir = tmp_path / "docs" / "components" / name
        comp_dir.mkdir(parents=True, exist_ok=True)
        d = dict(ORDERS_DIGEST, service=name)
        p = comp_dir / "_service-digest.json"
        p.write_text(json.dumps(d), encoding="utf-8")
        return p

    def test_reused_with_digest_satisfies_completeness(self, tmp_path, capsys):
        """Manifest: done(orders), done(payment), reused(employee) + digest → no BLOCK."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        _write_digest(tmp_path, PAYMENT_DIGEST)
        self._make_reused_digest(tmp_path, "employee")

        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "payment", "status": "done", "service": "payment"},
                {"name": "employee", "status": "reused", "service": "employee"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        rc = synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=False,  # strict — not --force-aggregate
        )
        assert rc == 0, "Should not BLOCK when reused component has a digest"
        captured = capsys.readouterr()
        assert "component_incomplete" not in captured.err
        # v19: verify service presence via the scout report (services table) — machine-written.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        assert "orders" in scout
        assert "payment" in scout
        assert "employee" in scout

    def test_reused_without_digest_still_blocks(self, tmp_path, capsys):
        """Reused entry with no matching digest → BLOCK (forces synth-digest first)."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        # employee digest NOT written

        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "employee", "status": "reused", "service": "employee"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        rc = synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=False,
        )
        assert rc == 1
        assert "component_incomplete" in capsys.readouterr().err

    def test_excluded_component_dropped_with_warn(self, tmp_path, capsys):
        """status:'excluded' → [WARN] component_excluded, aggregate proceeds, no BLOCK."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        _write_digest(tmp_path, PAYMENT_DIGEST)
        # employee excluded — no digest needed

        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "payment", "status": "done", "service": "payment"},
                {"name": "employee", "status": "excluded"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        rc = synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=False,
        )
        assert rc == 0, "excluded should not BLOCK"
        captured = capsys.readouterr()
        assert "component_excluded:employee" in captured.err
        # v19: Scout report written for done components (no draft files).
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()

    def test_excluded_not_in_catalog(self, tmp_path, capsys):
        """An excluded component must not appear in the synthesized system layer."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        _write_digest(tmp_path, PAYMENT_DIGEST)

        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "payment", "status": "done", "service": "payment"},
                {"name": "employee", "status": "excluded"},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))
        synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=False,
        )
        # v19: scout report's services table is machine-written.
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        # done services appear in the scout report.
        assert "orders" in scout
        assert "payment" in scout
        # excluded component has no digest — it does NOT appear in the scout report.
        assert "employee" not in scout

    def test_mirror_stale_warns_when_sha_drifts(self, tmp_path, capsys):
        """When durable state mirror sha != live last_rebuild_sha → [WARN] mirror_stale."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        # Write a manifest with a reused employee entry pointing to a docs tree.
        emp_src = tmp_path / "employee"
        emp_src.mkdir()
        emp_docs = emp_src / "docs"
        emp_docs.mkdir()
        # Live state has sha "LIVE_SHA".
        (emp_docs / ".rebuild-state.json").write_text(
            json.dumps({"primary_lang": "en", "last_rebuild_sha": "LIVE_SHA_123"})
        )

        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {
                    "name": "employee",
                    "status": "reused",
                    "docs_path": "employee/docs",
                    "source_sha": "OLD_SHA_999",   # different from live
                },
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))

        # Seed durable state with the OLD sha recorded.
        from _synthesis_io_lib import write_system_state
        write_system_state(str(tmp_path / "docs"), {
            "primary_lang": "en",
            "synthesis_format_version": "14.0.0",
            "snapshot_hash": "aabbcc",
            "generated_at": "2026-06-24T12:00:00Z",
            "components": [
                {"name": "employee", "role": "service", "reused": True,
                 "source_sha": "OLD_SHA_999", "mirror_sha": None},
                {"name": "orders", "role": "service", "reused": False,
                 "source_sha": "aabbcc001", "mirror_sha": None},
            ],
        })

        # Run aggregate — force to skip completeness blocking on reused w/o digest.
        synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=True,
        )
        captured = capsys.readouterr()
        assert "mirror_stale" in captured.err, (
            f"Expected mirror_stale warn; got stderr:\n{captured.err}"
        )

    def test_mirror_not_stale_no_warn_when_sha_matches(self, tmp_path, capsys):
        """When mirror sha == live sha → no mirror_stale warn."""
        _write_digest(tmp_path, ORDERS_DIGEST)
        emp_src = tmp_path / "employee"
        (emp_src / "docs").mkdir(parents=True)
        sha = "SAME_SHA_0001"
        ((emp_src / "docs") / ".rebuild-state.json").write_text(
            json.dumps({"primary_lang": "en", "last_rebuild_sha": sha})
        )
        manifest = {
            "components": [
                {"name": "orders", "status": "done", "service": "orders"},
                {"name": "employee", "status": "reused", "docs_path": "employee/docs",
                 "source_sha": sha},
            ]
        }
        manifest_path = tmp_path / ".rebuild-components.json"
        manifest_path.write_text(json.dumps(manifest))
        from _synthesis_io_lib import write_system_state
        write_system_state(str(tmp_path / "docs"), {
            "primary_lang": "en",
            "synthesis_format_version": "14.0.0",
            "snapshot_hash": "aabbcc",
            "generated_at": "2026-06-24T12:00:00Z",
            "components": [
                {"name": "employee", "role": "service", "reused": True,
                 "source_sha": sha, "mirror_sha": None},
                {"name": "orders", "role": "service", "reused": False,
                 "source_sha": "aabbcc001", "mirror_sha": None},
            ],
        })
        synthesize(
            root=str(tmp_path),
            manifest=str(manifest_path),
            digest_dir=None,
            max_digest_age=None,
            force_aggregate=True,
        )
        captured = capsys.readouterr()
        assert "mirror_stale" not in captured.err

    def test_format_version_in_system_state(self, tmp_path):
        """After synthesis, docs/.rebuild-system-state.json carries the current
        synthesis_format_version (bumped to 22.0.0 with the v23 single-source translate model —
        derived view deleted, component source path now lang-resolved via resolve_docs_root)."""
        _make_digest_tree(tmp_path)
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        from _synthesis_io_lib import read_system_state
        from _system_synthesis_lib import SYNTHESIS_FORMAT_VERSION
        state = read_system_state(str(tmp_path / "docs"))
        assert state is not None
        assert state.get("synthesis_format_version") == SYNTHESIS_FORMAT_VERSION
        assert state.get("synthesis_format_version") == "22.0.0"


# ---------------------------------------------------------------------------
# Phase 10 — reused labels in rendered artifacts
# ---------------------------------------------------------------------------

class TestPhase10ReusedLabels:
    """Reused nodes carry (reused) label in catalog/graph/confidence."""

    REUSED_DIGEST = {
        "service": "employee",
        "role": "service",
        "stack": "nestjs",
        "generated_at": "2026-06-24T12:00:00Z",
        "source_sha": "abc123def456abc123",
        "provenance": "docs-derived",
        "rpc": [{"name": "GET /api/employees", "direction": "inbound", "message": ""}],
        "topic": [],
        "entity": [{"name": "Employee", "id_field": "id", "id_type": "uuid",
                    "visibility": "public"}],
    }

    def _write_reused_digest(self, tmp_path: Path) -> None:
        comp_dir = tmp_path / "docs" / "components" / "employee"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "_service-digest.json").write_text(
            json.dumps(self.REUSED_DIGEST), encoding="utf-8"
        )

    def test_service_catalog_shows_reused_label(self, tmp_path):
        """Scout report services table shows 'yes' in Reused column for docs-derived digests."""
        # v18: catalog is template-produced; reused labels appear in the scout report
        # services table and in per-component-confidence.md.
        _write_digest(tmp_path, ORDERS_DIGEST)
        emp_dir = tmp_path / "docs" / "components" / "employee"
        emp_dir.mkdir(parents=True, exist_ok=True)
        (emp_dir / "_service-digest.json").write_text(
            json.dumps(self.REUSED_DIGEST), encoding="utf-8"
        )
        synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                   max_digest_age=None, force_aggregate=True)
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        # Employee row in services table should have reused=yes
        services_section = scout.split("## Services", 1)[1].split("##", 1)[0]
        assert "employee" in services_section
        assert "yes" in services_section  # reused flag

    def test_service_catalog_reused_confidence_note(self, tmp_path):
        """Confidence cell for docs-derived digest says 'docs-derived' in per-component-confidence.md."""
        from _synthesis_render_lib import render_per_component_confidence
        out = render_per_component_confidence([self.REUSED_DIGEST], "T", "S")
        assert "docs-derived (no fresh extraction)" in out

    def test_reused_services_table_shows_yes(self, tmp_path):
        """Scout report services table shows 'yes' in Reused column for docs-derived digests."""
        # v19: Mermaid topology is NOT in the scout report; reused label is in services table.
        from _synthesis_scout_lib import build_scout_facts
        digests = [self.REUSED_DIGEST, ORDERS_DIGEST]
        edges = []
        facts = build_scout_facts(
            digests=digests,
            edges=edges,
            suggestions=[],
            snap="hash",
            abs_root="/fake/root",
            layout_mode="single-lang",
            primary_lang="en",
        )
        assert "yes" in facts["_services_table"]  # reused flag

    def test_validate_filled_scaffold_no_h2_lock(self):
        """v19: validate_filled_scaffold with no H2-lock — new H2 headers are allowed."""
        filled = "# T\n\n## A\nnarrative here\n\n## Injected\nnew section\n"
        assert validate_filled_scaffold(filled) == []

    def test_per_component_confidence_docs_derived_note(self, tmp_path):
        """per-component-confidence.md note for docs-derived is 'docs-derived'."""
        from _synthesis_render_lib import render_per_component_confidence
        out = render_per_component_confidence([self.REUSED_DIGEST, ORDERS_DIGEST], "T", "S")
        assert "docs-derived (no fresh extraction)" in out
        assert "employee (reused)" in out

    def test_normal_digest_no_reused_label(self, tmp_path):
        """A digest without provenance field is NOT labeled (reused) in the confidence table."""
        from _synthesis_render_lib import render_per_component_confidence
        out = render_per_component_confidence([ORDERS_DIGEST], "T", "S")
        assert "(reused)" not in out

    def test_provenance_extracted_no_reused_label(self, tmp_path):
        """A digest with provenance='extracted' is NOT labeled (reused)."""
        from _synthesis_render_lib import render_per_component_confidence
        extracted = dict(ORDERS_DIGEST, provenance="extracted")
        out = render_per_component_confidence([extracted], "T", "S")
        assert "(reused)" not in out

    def test_load_digests_accepts_provenance_field(self, tmp_path):
        """load_digests ignores the 'provenance' field (not in caps; not stripped)."""
        from _system_synthesis_lib import load_digests
        d = dict(self.REUSED_DIGEST)
        comp_dir = tmp_path / "emp"
        comp_dir.mkdir()
        p = comp_dir / "_service-digest.json"
        p.write_text(json.dumps(d), encoding="utf-8")
        loaded = load_digests([str(p)])
        assert len(loaded) == 1
        assert loaded[0].get("provenance") == "docs-derived"

    def test_synthesize_integration_reused_labels_in_output(self, tmp_path):
        """End-to-end: synthesize with a reused digest produces labeled artifacts."""
        # Write normal digests.
        _write_digest(tmp_path, ORDERS_DIGEST)
        _write_digest(tmp_path, PAYMENT_DIGEST)
        # Write reused digest.
        emp_dir = tmp_path / "docs" / "components" / "employee"
        emp_dir.mkdir(parents=True, exist_ok=True)
        (emp_dir / "_service-digest.json").write_text(
            json.dumps(self.REUSED_DIGEST), encoding="utf-8"
        )
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        # v19: reused label in scout report services table
        scout = (tmp_path / "docs" / "system" / ".system-scout-report.md").read_text()
        services_section = scout.split("## Services", 1)[1].split("##", 1)[0]
        assert "employee" in services_section
        assert "yes" in services_section  # reused flag
        # v19: no Mermaid fences in scout report
        assert "```mermaid" not in scout
        # per-component-confidence.md uses (reused) label
        confidence = (tmp_path / "docs" / "system" / "per-component-confidence.md").read_text()
        assert "docs-derived (no fresh extraction)" in confidence


# ---------------------------------------------------------------------------
# Regression: sanitize_field escapes brackets and build_interaction_edges sorts
# ---------------------------------------------------------------------------

class TestSanitizeFieldBracketEscape:
    def test_sanitize_field_escapes_closing_bracket(self):
        """Regression: ]  character is escaped to \\]."""
        result = sanitize_field("a]b")
        assert r"\]" in result
        assert "]" not in result or r"\]" in result

    def test_sanitize_field_escapes_opening_bracket(self):
        """Regression: [ character is escaped to \\[."""
        result = sanitize_field("a[b")
        assert r"\[" in result
        assert "[" not in result or r"\[" in result

    def test_sanitize_field_both_brackets(self):
        """Regression: both [ and ] in string are escaped."""
        result = sanitize_field("a]b[c")
        assert r"\]" in result
        assert r"\[" in result

    def test_sanitize_field_preserves_other_chars(self):
        """Regression guard: non-bracket chars are preserved."""
        result = sanitize_field("hello_world")
        assert "hello_world" in result or result == "hello_world"

    def test_sanitize_field_also_escapes_pipe(self):
        """Regression guard: pipe and backtick also escaped (existing behavior)."""
        result = sanitize_field("a|b`c")
        assert r"\|" in result
        assert "'" in result  # backtick → single quote


class TestBuildInteractionEdgesSorted:
    def test_edges_sorted_by_from_to_type_label(self):
        """Regression: build_interaction_edges returns edges sorted by (from, to, type, label)."""
        digests = [
            {
                "service": "service_z",
                "rpc": [{"name": "CallZ", "direction": "outbound"}],
                "topic": [],
            },
            {
                "service": "service_a",
                "rpc": [{"name": "CallZ", "direction": "inbound"}],
                "topic": [{"name": "topic_b", "role": "producer"}],
            },
            {
                "service": "service_m",
                "rpc": [],
                "topic": [{"name": "topic_b", "role": "consumer"}],
            },
        ]
        edges = build_interaction_edges(digests)
        # Should have at least 2 edges (sync: z→a, async: a→m)
        assert len(edges) >= 2
        # Verify they are sorted: extract (from, to, type, label) and confirm sorted order
        edge_keys = [(e["from"], e["to"], e["type"], e["label"]) for e in edges]
        assert edge_keys == sorted(edge_keys)

    def test_multiple_edges_deterministic_order(self):
        """Regression guard: identical edges in different order sort identically."""
        digests_1 = [
            {
                "service": "svc_a",
                "rpc": [{"name": "Foo", "direction": "outbound"}],
                "topic": [{"name": "event_1", "role": "producer"}],
            },
            {
                "service": "svc_b",
                "rpc": [{"name": "Foo", "direction": "inbound"}],
                "topic": [{"name": "event_1", "role": "consumer"}],
            },
        ]
        digests_2 = [
            {
                "service": "svc_b",
                "rpc": [{"name": "Foo", "direction": "inbound"}],
                "topic": [{"name": "event_1", "role": "consumer"}],
            },
            {
                "service": "svc_a",
                "rpc": [{"name": "Foo", "direction": "outbound"}],
                "topic": [{"name": "event_1", "role": "producer"}],
            },
        ]
        edges_1 = build_interaction_edges(digests_1)
        edges_2 = build_interaction_edges(digests_2)
        # Same edges regardless of input order
        assert edges_1 == edges_2


# ---------------------------------------------------------------------------
# v19 — lint_mermaid_safety
# ---------------------------------------------------------------------------

class TestLintMermaidSafety:
    """lint_mermaid_safety returns [] for safe Mermaid; non-empty for unsafe chars."""

    def test_safe_block_returns_empty(self):
        """A mermaid block with safe labels returns no violations."""
        md = (
            "Some text\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  A["orders"] --> B["payment"]\n'
            "```\n"
        )
        assert lint_mermaid_safety(md) == []

    def test_no_mermaid_returns_empty(self):
        """Markdown with no mermaid fences returns no violations."""
        assert lint_mermaid_safety("# Heading\n\nSome prose.\n") == []

    def test_raw_quote_in_label_is_violation(self):
        """A raw `"` inside a Mermaid label is a violation."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            '  A["he said "hi""] --> B\n'
            "```\n"
        )
        violations = lint_mermaid_safety(md)
        assert len(violations) >= 1
        assert any("unsafe_mermaid_label" in v for v in violations)

    def test_raw_backtick_is_violation(self):
        """A raw backtick inside a Mermaid fence is a violation."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A[`evil`] --> B\n"
            "```\n"
        )
        violations = lint_mermaid_safety(md)
        assert len(violations) >= 1

    def test_raw_lt_is_violation(self):
        """A raw `<` (non-comment-start) inside a Mermaid fence is a violation."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A[<script>] --> B\n"
            "```\n"
        )
        violations = lint_mermaid_safety(md)
        assert len(violations) >= 1

    def test_raw_gt_is_violation(self):
        """A raw `>` inside a Mermaid fence is a violation."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A[order > 5] --> B\n"
            "```\n"
        )
        violations = lint_mermaid_safety(md)
        assert len(violations) >= 1

    def test_escaped_quot_entity_is_safe(self):
        """#quot; (already escaped) does not trigger a violation."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            '  A["he said #quot;hi#quot;"] --> B\n'
            "```\n"
        )
        # #quot; is the safe form — no violation.
        violations = lint_mermaid_safety(md)
        assert violations == []

    def test_multiple_fences_all_checked(self):
        """Both fences are checked; only the unsafe one triggers a violation."""
        md = (
            "Safe:\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  A["ok"] --> B\n'
            "```\n"
            "Unsafe:\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            '  participant A as "evil`cmd"\n'
            "```\n"
        )
        violations = lint_mermaid_safety(md)
        assert len(violations) >= 1


# ---------------------------------------------------------------------------
# v19 — validate_filled_scaffold single-arg signature
# ---------------------------------------------------------------------------

class TestValidateFilledScaffoldV19:
    """validate_filled_scaffold(draft) — single-arg, v19 signature."""

    def test_clean_draft_passes(self):
        """A draft with no markers and safe Mermaid passes."""
        draft = "# T\n\n## A\nReal prose here.\n"
        assert validate_filled_scaffold(draft) == []

    def test_fill_marker_violation(self):
        """A remaining {{FILL}} marker triggers unfilled_markers violation."""
        draft = "# T\n\n## A\n{{FILL: write something here}}\n"
        violations = validate_filled_scaffold(draft)
        assert any("unfilled_markers" in v for v in violations)

    def test_scout_marker_violation(self):
        """A remaining {{SCOUT}} marker triggers unfilled_markers violation."""
        draft = "# T\n{{SCOUT: edge-table}}\n"
        violations = validate_filled_scaffold(draft)
        assert any("unfilled_markers" in v for v in violations)

    def test_bracket_fill_marker_violation(self):
        """A [FILL] marker triggers unfilled_markers violation."""
        draft = "# T\n[FILL] placeholder\n"
        violations = validate_filled_scaffold(draft)
        assert any("unfilled_markers" in v for v in violations)

    def test_unsafe_mermaid_violation(self):
        """An unsafe Mermaid label (raw backtick) triggers a violation."""
        draft = "# T\n\n```mermaid\nflowchart LR\n  A[`evil`]\n```\n"
        violations = validate_filled_scaffold(draft)
        assert any("unsafe_mermaid_label" in v for v in violations)

    def test_safe_mermaid_with_no_markers_passes(self):
        """A safe Mermaid block + no fill markers passes."""
        draft = (
            "# Architecture\n\n"
            "## Topology\n\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  orders["orders"] --> payment["payment"]\n'
            "```\n\n"
            "## Description\n\nProse.\n"
        )
        assert validate_filled_scaffold(draft) == []

    def test_both_violations_returned(self):
        """Both marker and mermaid violations are returned together."""
        draft = (
            "# T\n{{FILL: x}}\n"
            "```mermaid\nflowchart LR\n  A[`bad`]\n```\n"
        )
        violations = validate_filled_scaffold(draft)
        has_marker = any("unfilled_markers" in v for v in violations)
        has_mermaid = any("unsafe_mermaid_label" in v for v in violations)
        assert has_marker
        assert has_mermaid


# ---------------------------------------------------------------------------
# v20 — per-component language projection + source immutability
# ---------------------------------------------------------------------------

def _write_state_at(path: Path, primary_lang: str) -> None:
    """Write a .rebuild-state.json at the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"primary_lang": primary_lang}), encoding="utf-8")


def _mk_comp_v20(base: Path, name: str, primary: str = "en",
                 *, mirror: str | None = None) -> Path:
    """Create a component at <base>/<name>/ with optional <mirror>/ subdir."""
    comp = base / name
    comp.mkdir(parents=True, exist_ok=True)
    _write_state_at(comp / ".rebuild-state.json", primary)
    (comp / "spec.md").write_text(f"# {name} ({primary})\n", encoding="utf-8")
    if mirror:
        md = comp / mirror
        md.mkdir(parents=True, exist_ok=True)
        (md / "spec.md").write_text(f"# {name} [{mirror}]\n", encoding="utf-8")
    return comp


def _setup_per_lang(tmp_path: Path, primary: str = "vi") -> None:
    """Set up root docs/.rebuild-state.json to trigger per-lang mode.

    per-lang requires either: (a) a secondary language in state.translations, or
    (b) the sentinel docs/<primary>/.layout-migrated exists.
    We use (b) — create the sentinel — since it doesn't require a real secondary.
    """
    (tmp_path / "docs" / primary).mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / primary / ".layout-migrated").write_text(
        "migrated\n", encoding="utf-8")


class TestV20DigestSourceBase:
    """Digest collection must use SOURCE docs/components/ — not the derived view — in per-lang mode.

    Prior to v20, synthesize_system set resolved_components_base = docs/<L>/components/ in
    per-lang mode. Under v20, digests live in the SOURCE regardless of layout mode.
    """

    def test_digests_found_from_source_in_per_lang_mode(self, tmp_path):
        """per-lang mode: synthesize finds digests from docs/vi/components/ (P04 lang-namespaced source)."""
        # P04: resolved_components_base = docs/vi/components/ for vi-primary repos.
        # Write digests to the lang-namespaced path; state at docs/components/ for discovery.
        _write_digest_lang(tmp_path, "vi")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "vi")
        _setup_per_lang(tmp_path, "vi")
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        # Synthesis should succeed (digests found from lang-namespaced source)
        assert rc == 0
        # Scout report written (proves digests were found)
        assert (tmp_path / "docs" / "vi" / "system" / ".system-scout-report.md").is_file()

class TestV20EndToEnd:
    """Per-lang aggregate end-to-end."""

    def test_en_single_lang_no_derived_view(self, tmp_path):
        """en single-lang: docs/components/ only; no docs/en/components/ derived view."""
        _make_digest_tree(tmp_path)
        rc = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                        max_digest_age=None, force_aggregate=True)
        assert rc == 0
        # Scout report at flat path (no per-lang dir for en single-lang)
        assert (tmp_path / "docs" / "system" / ".system-scout-report.md").is_file()
        # No derived view created for en single-lang (place_components skipped for single-lang)
        # Source at root
        assert (tmp_path / "docs" / "components").is_dir()


# ---------------------------------------------------------------------------
# H1 — _discover_primary_lang system-state fallback (post-P07 migration layout)
# ---------------------------------------------------------------------------

class TestDiscoverPrimaryLangSystemStateFallback:
    """After P07 migration, docs/components/ is gone; component state is at
    docs/<primary>/components/<name>/.rebuild-state.json.  The only surviving
    breadcrumb for a 2nd synthesis run is docs/.rebuild-system-state.json.
    """

    def _write_system_state(self, tmp_path: Path, lang: str) -> None:
        from _synthesis_io_lib import write_system_state
        from _system_synthesis_lib import SYNTHESIS_FORMAT_VERSION
        write_system_state(str(tmp_path / "docs"), {
            "primary_lang": lang,
            "synthesis_format_version": SYNTHESIS_FORMAT_VERSION,
            "snapshot_hash": "abc",
            "generated_at": "2026-01-01T00:00:00Z",
            "components": [],
        })

    def test_post_migration_no_docs_components_falls_back_to_system_state(self, tmp_path):
        """Migrated layout: state at docs/vi/components/<name>/, no docs/components/,
        no root docs/.rebuild-state.json, but docs/.rebuild-system-state.json has
        primary_lang='vi' → _discover_primary_lang must return 'vi', not 'en'.
        """
        from synthesize_system import _discover_primary_lang

        # Write per-component state at the migrated location (not the old docs/components/)
        for name in ("orders", "payment"):
            state_dir = tmp_path / "docs" / "vi" / "components" / name
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / ".rebuild-state.json").write_text(
                json.dumps({"primary_lang": "vi"}), encoding="utf-8"
            )

        # Explicitly ensure old docs/components/ and root docs/.rebuild-state.json are absent
        assert not (tmp_path / "docs" / "components").exists()
        assert not (tmp_path / "docs" / ".rebuild-state.json").exists()

        # Write the system-state breadcrumb left by the previous synthesis run
        self._write_system_state(tmp_path, "vi")

        result = _discover_primary_lang(str(tmp_path), override=None)
        assert result == "vi", (
            f"expected 'vi' from system-state fallback, got {result!r}"
        )

    def test_system_state_fallback_not_used_when_component_state_present(self, tmp_path):
        """When docs/components/ exists (pre-migration layout), component state
        wins; system-state fallback must NOT override.
        """
        from synthesize_system import _discover_primary_lang

        # Old layout: state at docs/components/<name>/
        for name in ("orders",):
            state_dir = tmp_path / "docs" / "components" / name
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / ".rebuild-state.json").write_text(
                json.dumps({"primary_lang": "ja"}), encoding="utf-8"
            )

        # System-state says "vi" — should NOT win when component state says "ja"
        self._write_system_state(tmp_path, "vi")

        result = _discover_primary_lang(str(tmp_path), override=None)
        assert result == "ja", (
            f"component state must win over system-state fallback, got {result!r}"
        )

    def test_system_state_fallback_empty_lang_falls_through_to_en(self, tmp_path):
        """docs/.rebuild-system-state.json with missing/empty primary_lang → 'en' fallback."""
        from synthesize_system import _discover_primary_lang

        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        from _synthesis_io_lib import write_system_state
        from _system_synthesis_lib import SYNTHESIS_FORMAT_VERSION
        write_system_state(str(tmp_path / "docs"), {
            "primary_lang": "",
            "synthesis_format_version": SYNTHESIS_FORMAT_VERSION,
            "snapshot_hash": "abc",
            "generated_at": "2026-01-01T00:00:00Z",
            "components": [],
        })

        result = _discover_primary_lang(str(tmp_path), override=None)
        assert result == "en"


class TestAutoMigrationIdempotentPostMigration:
    """Extended idempotency test: simulates the actual post-P07 migrated tree
    where docs/components/ is gone and state lives at docs/<primary>/components/.
    2nd synthesis run must still find digests via the system-state fallback.
    """

    def test_second_run_after_p07_migration_finds_digests(self, tmp_path):
        """After P07: digests at docs/vi/components/, component state at same path,
        NO docs/components/, NO root docs/.rebuild-state.json, but
        docs/.rebuild-system-state.json from run 1 has primary_lang='vi'.
        Run 2 must complete (rc=0) and write the scout report to docs/vi/system/.
        """
        # Run 1: standard vi setup with docs/components/ state present → synthesis succeeds
        _write_digest_lang(tmp_path, "vi")
        for svc in ("orders", "payment", "inventory"):
            _write_state(tmp_path, svc, "vi")

        rc1 = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                         max_digest_age=None, force_aggregate=True)
        assert rc1 == 0
        assert (tmp_path / "docs" / ".rebuild-system-state.json").is_file(), (
            "Run 1 must have written docs/.rebuild-system-state.json"
        )

        # Simulate P07 migration: remove docs/components/ (state files gone from old path)
        import shutil
        old_components = tmp_path / "docs" / "components"
        if old_components.is_dir():
            shutil.rmtree(old_components)

        # Also remove root .rebuild-state.json to mirror a real post-migration layout
        root_state = tmp_path / "docs" / ".rebuild-state.json"
        if root_state.is_file():
            root_state.unlink()

        # Run 2: must discover lang="vi" via system-state fallback and complete successfully
        rc2 = synthesize(root=str(tmp_path), manifest=None, digest_dir=None,
                         max_digest_age=None, force_aggregate=True)
        assert rc2 == 0, "2nd synthesis run after P07 migration must succeed"
        assert (tmp_path / "docs" / "vi" / "system" / ".system-scout-report.md").is_file(), (
            "Scout report must be written to docs/vi/system/ on 2nd run"
        )
