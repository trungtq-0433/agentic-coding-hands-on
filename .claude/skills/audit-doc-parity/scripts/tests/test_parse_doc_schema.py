"""Tests for parse_doc_schema.py."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from _citation_lib import read_text_safe
import parse_doc_schema as pds

FIXTURES = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent


def _read(name):
    result = read_text_safe(FIXTURES / name)
    assert result is not None
    return result[0]


# ---------------------------------------------------------------------------
# technical-spec parser
# ---------------------------------------------------------------------------

class TestParseTechnicalSpec:
    def setup_method(self):
        self.text = _read("doc_with_citations.md")
        self.items = pds._parse_technical_spec(self.text, "F001_Example",
                                                "fixtures/doc_with_citations.md")

    def _kind(self, k):
        return [i for i in self.items if i["kind"] == k]

    def test_fr_extracted(self):
        frs = self._kind("FR")
        assert len(frs) >= 2
        ids = [i["id"] for i in frs]
        assert "FR-001" in ids
        assert "FR-002" in ids

    def test_fr_fields(self):
        fr = next(i for i in self._kind("FR") if i["id"] == "FR-001")
        assert "description" in fr["fields"]
        assert "endpoint" in fr["fields"]
        assert "handler" in fr["fields"]
        assert "verifiable" in fr["fields"]

    def test_br_extracted(self):
        brs = self._kind("BR")
        assert len(brs) >= 1
        assert brs[0]["id"] == "BR-001"
        assert "rule" in brs[0]["fields"]
        assert "applies_to" in brs[0]["fields"]
        assert "linked_fr" in brs[0]["fields"]

    def test_int_with_output_subfields(self):
        ints = self._kind("INT")
        assert len(ints) >= 1
        f = ints[0]["fields"]
        assert "type" in f
        assert "target" in f
        assert "trigger" in f
        assert "payload" in f
        assert "failure_handling" in f
        # Output sub-field should be parsed from **Output:**
        assert "output" in f

    def test_entity_extracted(self):
        entities = self._kind("ENTITY")
        entity_tables = [e["fields"]["table"] for e in entities]
        assert "orders" in entity_tables

    def test_sc_extracted(self):
        scs = self._kind("SC")
        assert len(scs) >= 2
        ids = [s["id"] for s in scs]
        assert "SC-001" in ids


# ---------------------------------------------------------------------------
# behavior-logic parser
# ---------------------------------------------------------------------------

class TestParseBehaviorLogic:
    def setup_method(self):
        self.text = _read("doc_behavior_logic.md")
        self.items = pds._parse_behavior_logic(self.text, "system.behavior-logic",
                                                "fixtures/doc_behavior_logic.md")

    def test_bl_count(self):
        assert len(self.items) == 2

    def test_bl_fields(self):
        bl = self.items[0]
        assert bl["kind"] == "BL"
        assert bl["id"] == "BL001"
        f = bl["fields"]
        assert f["type"] == "event-listener"
        assert f["trigger"] == "order.placed"
        assert f["payload"] == "{order_id, user_id, total}"
        assert f["source_symbol"] == "handle_order_placed"
        assert "related_routes" in f
        assert "related_models" in f

    def test_bl_evidence_from_citation(self):
        # BL001 has a **Source:** citation
        bl1 = self.items[0]
        assert "fixtures/source_plain.py" in bl1["evidence"]

    def test_bl_evidence_fallback(self):
        # BL002 has no citation → falls back to doc path
        bl2 = self.items[1]
        assert "doc_behavior_logic.md" in bl2["evidence"]


# ---------------------------------------------------------------------------
# api parser
# ---------------------------------------------------------------------------

class TestParseApi:
    def setup_method(self):
        self.text = _read("doc_api_contracts.md")
        self.items = pds._parse_api(self.text, "system.api",
                                     "fixtures/doc_api_contracts.md")

    def test_endpoints_extracted(self):
        endpoints = [i for i in self.items if i["kind"] == "ENDPOINT"]
        assert len(endpoints) >= 2

    def test_endpoint_fields(self):
        ep = next(i for i in self.items
                  if i["kind"] == "ENDPOINT" and "export" in i["id"].lower())
        f = ep["fields"]
        assert f["method"] == "GET"
        assert "/api/orders/export" in f["path"]
        assert "auth" in f
        assert "request_shape" in f
        assert "response_shape" in f
        assert "status_codes" in f
        assert "error_envelope" in f

    def test_endpoint_with_citation(self):
        ep = next(i for i in self.items
                  if i["kind"] == "ENDPOINT" and "export" in i["id"].lower())
        assert "source_plain.py" in ep["evidence"]


# ---------------------------------------------------------------------------
# data-models parser
# ---------------------------------------------------------------------------

class TestParseDataModels:
    def setup_method(self):
        self.text = _read("doc_data_models.md")
        self.items = pds._parse_data_models(self.text, "system.data-models",
                                             "fixtures/doc_data_models.md")

    def _kind(self, k):
        return [i for i in self.items if i["kind"] == k]

    def test_entities_extracted(self):
        entities = self._kind("ENTITY")
        names = [e["id"] for e in entities]
        assert any("Order" in n for n in names)
        assert any("User" in n for n in names)

    def test_entity_attributes(self):
        order = next(e for e in self._kind("ENTITY") if "Order" in e["id"])
        attrs = order["fields"]["attributes"]
        assert len(attrs) >= 2
        col_names = [a["name"] for a in attrs]
        assert "id" in col_names

    def test_discriminator_extracted(self):
        discs = self._kind("DISC")
        assert len(discs) >= 1
        fields = [d["fields"]["field"] for d in discs]
        assert "status" in fields

    def test_validation_extracted(self):
        vals = self._kind("VALIDATION")
        assert len(vals) >= 1
        fields = [v["fields"]["field"] for v in vals]
        assert "email" in fields

    def test_validation_fields_structure(self):
        email_val = next(v for v in self._kind("VALIDATION")
                         if v["fields"]["field"] == "email")
        f = email_val["fields"]
        assert "constraint" in f
        assert "error_message" in f


# ---------------------------------------------------------------------------
# screen-spec parser
# ---------------------------------------------------------------------------

class TestParseScreenSpec:
    def setup_method(self):
        self.text = _read("doc_screen_spec.md")
        self.items = pds._parse_screen_spec(self.text, "F001_Example",
                                             "fixtures/doc_screen_spec.md")

    def _kind(self, k):
        return [i for i in self.items if i["kind"] == k]

    def test_flow_branches_extracted(self):
        branches = self._kind("FLOW_BRANCH")
        assert len(branches) >= 2

    def test_flow_branch_fields(self):
        br = self._kind("FLOW_BRANCH")[0]
        f = br["fields"]
        assert "decision_point" in f
        assert "condition" in f
        assert "outcome" in f

    def test_data_fields_extracted(self):
        fields = self._kind("DATA_FIELD")
        assert len(fields) >= 1
        bindings = [f["fields"]["binding"] for f in fields]
        assert any("order" in b.lower() for b in bindings)

    def test_data_field_structure(self):
        df = self._kind("DATA_FIELD")[0]
        f = df["fields"]
        assert "binding" in f
        assert "source" in f
        assert "format" in f
        assert "empty_behavior" in f
        assert "cross_ref" in f

    def test_ui_states_extracted(self):
        states = self._kind("UI_STATE")
        assert len(states) >= 2
        state_names = [s["fields"]["state"] for s in states]
        assert "loading" in state_names

    def test_ui_state_fields(self):
        st = self._kind("UI_STATE")[0]
        f = st["fields"]
        assert "state" in f
        assert "trigger" in f
        assert "visual_behavior" in f
        assert "user_action" in f

    def test_validations_extracted(self):
        vals = self._kind("VALIDATION")
        assert len(vals) >= 1
        field_names = [v["fields"]["field"] for v in vals]
        assert "email" in field_names

    def test_validation_fields(self):
        email = next(v for v in self._kind("VALIDATION")
                     if v["fields"]["field"] == "email")
        f = email["fields"]
        assert "required" in f
        assert "constraints" in f
        assert "error_message" in f
        assert "async_check" in f


# ---------------------------------------------------------------------------
# realistic technical-spec (list-form FR/SC, h3 BR/ALG blocks, 4-col ENTITY)
# ---------------------------------------------------------------------------

class TestParseTechnicalSpecRealistic:
    """Validates _parse_technical_spec against the real template forms."""

    def setup_method(self):
        self.text = _read("doc_technical_spec_realistic.md")
        self.items = pds._parse_technical_spec(
            self.text, "F001_Orders",
            "fixtures/doc_technical_spec_realistic.md",
        )

    def _kind(self, k):
        return [i for i in self.items if i["kind"] == k]

    def test_fr_list_form_all_three_extracted(self):
        frs = self._kind("FR")
        ids = [i["id"] for i in frs]
        assert "FR-001" in ids, f"FR-001 missing; got {ids}"
        assert "FR-002" in ids, f"FR-002 missing; got {ids}"
        assert "FR-003" in ids, f"FR-003 missing; got {ids}"
        assert len(frs) == 3, f"Expected 3 FRs, got {len(frs)}: {ids}"

    def test_fr_list_form_fields(self):
        fr = next(i for i in self._kind("FR") if i["id"] == "FR-001")
        f = fr["fields"]
        assert "description" in f and f["description"]
        assert "endpoint" in f and "GET" in f["endpoint"]
        assert "handler" in f and f["handler"]

    def test_fr_list_form_evidence_from_source_annotation(self):
        fr = next(i for i in self._kind("FR") if i["id"] == "FR-001")
        # **Source:** `code/orders.py:6-10` is on the line after the FR bullet
        assert "orders.py" in fr["evidence"]

    def test_alg_h3_block_extracted(self):
        algs = self._kind("ALG")
        ids = [i["id"] for i in algs]
        assert "ALG-001" in ids, f"ALG-001 missing; got {ids}"

    def test_alg_h3_block_fields(self):
        alg = next(i for i in self._kind("ALG") if i["id"] == "ALG-001")
        f = alg["fields"]
        assert "input" in f
        assert "output" in f
        assert "complexity" in f

    def test_sc_list_form_extracted(self):
        scs = self._kind("SC")
        ids = [i["id"] for i in scs]
        assert "SC-001" in ids, f"SC-001 missing; got {ids}"

    def test_sc_list_form_covers_field(self):
        sc = next(i for i in self._kind("SC") if i["id"] == "SC-001")
        assert "FR-001" in sc["fields"]["covers"]

    def test_entity_4col_table_extracted(self):
        entities = self._kind("ENTITY")
        assert len(entities) >= 1, "Expected at least 1 ENTITY"
        # id should be ENTITY-{table_name}, table is 'orders'
        eid = next((e for e in entities if "orders" in e["id"]), None)
        assert eid is not None, f"ENTITY-orders missing; got {[e['id'] for e in entities]}"

    def test_entity_4col_table_fields(self):
        entity = next(e for e in self._kind("ENTITY") if "orders" in e["id"])
        f = entity["fields"]
        assert "table" in f and f["table"] == "orders"
        assert "key_columns" in f and f["key_columns"]
        assert "purpose" in f and f["purpose"]

    def test_br_h3_block_extracted(self):
        brs = self._kind("BR")
        ids = [i["id"] for i in brs]
        assert "BR-001" in ids, f"BR-001 missing; got {ids}"

    def test_br_h3_block_fields(self):
        br = next(i for i in self._kind("BR") if i["id"] == "BR-001")
        f = br["fields"]
        assert "linked_fr" in f
        assert "applies_to" in f
        assert "rule" in f


# ---------------------------------------------------------------------------
# parse_unit integration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# SM parser — table form (SM-002) and bullet form (SM-001) coverage  (L1)
# ---------------------------------------------------------------------------

# SM-002: table-form state machine with 4-col Transitions table
_SM_TABLE_DOC = """\
# Technical Spec — SM Test

### SM-002_OrderLifecycle
**Kind:** lifecycle
**States:** pending, confirmed, shipped, delivered, cancelled

#### Transitions

| From | To | Guard | Side effect |
|------|-----|-------|-------------|
| pending | confirmed | payment_received == true | send_confirmation_email() |
| confirmed | shipped | stock_reserved == true | notify_warehouse() |
| shipped | delivered | delivery_confirmed == true | update_inventory() |
| pending | cancelled | user_cancels == true | refund_initiated() |
"""

# SM-001: bullet-form state machine — no transitions table, should not crash
_SM_BULLET_DOC = """\
# Technical Spec — SM Test Bullet

### SM-001_OrderStatus
**Kind:** status
**States:** draft, active, closed

**Transition rules:**
- draft → active when activated by admin
- active → closed when end_date passed
"""


class TestParseStateMachine:
    """SM parser: table-form (SM-002) and bullet-form (SM-001)."""

    def _items(self, text):
        return pds._parse_technical_spec(text, "F_SM_Test", "fixtures/sm_test.md")

    def _sm(self, items, sm_id):
        return next((i for i in items if i["kind"] == "SM" and i["id"] == sm_id), None)

    # --- SM-002 table-form ---

    def test_sm_002_extracted(self):
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        assert sm is not None, "SM-002 not found"

    def test_sm_002_states_parsed(self):
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        states = sm["fields"]["states"]
        assert "pending" in states
        assert "confirmed" in states
        assert "shipped" in states

    def test_sm_002_transitions_count(self):
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        transitions = sm["fields"]["transitions"]
        assert len(transitions) == 4, f"Expected 4 transitions, got {len(transitions)}: {transitions}"

    def test_sm_002_transition_from_to_correct(self):
        """H1 fix: from_to must be 'From→To', NOT map guard to row[1]."""
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        t0 = sm["fields"]["transitions"][0]
        assert t0["from_to"] == "pending→confirmed", (
            f"from_to wrong: {t0['from_to']!r}; H1 column mapping may still be broken"
        )

    def test_sm_002_transition_guard_correct(self):
        """H1 fix: guard must be col[2] (Guard), not col[1] (To)."""
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        t0 = sm["fields"]["transitions"][0]
        assert t0["guard"] == "payment_received == true", (
            f"guard wrong: {t0['guard']!r}; expected col[2] value"
        )

    def test_sm_002_transition_side_effect_correct(self):
        """H1 fix: side_effect must be col[3], not missing."""
        items = self._items(_SM_TABLE_DOC)
        sm = self._sm(items, "SM-002")
        t0 = sm["fields"]["transitions"][0]
        assert t0["side_effect"] == "send_confirmation_email()", (
            f"side_effect wrong: {t0['side_effect']!r}; expected col[3] value"
        )

    # --- SM-001 bullet-form (no transitions table — must not crash) ---

    def test_sm_001_extracted_no_crash(self):
        """SM-001 bullet form: parser must not crash, yields states."""
        items = self._items(_SM_BULLET_DOC)
        sm = self._sm(items, "SM-001")
        assert sm is not None, "SM-001 not found"

    def test_sm_001_states_parsed(self):
        items = self._items(_SM_BULLET_DOC)
        sm = self._sm(items, "SM-001")
        states = sm["fields"]["states"]
        assert "draft" in states
        assert "active" in states
        assert "closed" in states

    def test_sm_001_transitions_empty_not_crash(self):
        """SM-001 bullet form yields no transitions (no table) — list is empty, no crash."""
        items = self._items(_SM_BULLET_DOC)
        sm = self._sm(items, "SM-001")
        # No transitions table → empty list is correct
        assert isinstance(sm["fields"]["transitions"], list)


class TestParseUnit:
    def test_technical_spec_unit(self):
        unit = {
            "unit": "F001_Example",
            "artifact": "technical-spec",
            "doc_paths": ["claude/skills/audit-doc-parity/scripts/tests/fixtures/doc_with_citations.md"],
        }
        result = pds.parse_unit(unit, PROJECT_ROOT)
        assert result["unit"] == "F001_Example"
        assert result["artifact"] == "technical-spec"
        assert isinstance(result["items"], list)
        kinds = {i["kind"] for i in result["items"]}
        assert "FR" in kinds

    def test_missing_doc_returns_empty(self):
        unit = {
            "unit": "F999_Missing",
            "artifact": "technical-spec",
            "doc_paths": ["docs/features/F999_Missing/technical-spec.md"],
        }
        result = pds.parse_unit(unit, PROJECT_ROOT)
        assert result["items"] == []
