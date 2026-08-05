"""Phase 10 (cobol-stack-and-generic-fallback plan) — cross-track integration.

Every prior phase (01-09, 4b) proved itself in isolation via unit tests. This module proves
they COMPOSE: one `cobol` profile driving screen + CRUD/data extraction in a single pipeline
run (detect -> extract -> hand-render -> validate), a mixed SCREEN-SECTION+CICS-BMS repo
dispatched by the router in ONE run, and the Track D generic-fallback sniff -> accept path on
a genuinely unrecognized stack -- all against small, self-contained, ASCII, grammar-real
fixtures (see each `fixtures/<name>/README.md` for provenance).

`sys.path` already has scripts/ on it (see conftest.py).

Regression (Todo item 5, phase file): NOT duplicated here per the phase file's own note --
the full existing suite (web/Delphi/Oracle e2e fixture tests included) is run as a whole and
reported separately, not re-implemented in this module.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _stack_profile_lib as profile_lib  # noqa: E402
import _ui_sniff_accept_lib as accept_lib  # noqa: E402
import detect_stack_profile as dsp  # noqa: E402
import validate_crud_matrix  # noqa: E402
import validate_db_catalog  # noqa: E402
import validate_screen_list  # noqa: E402
import validate_source_citations  # noqa: E402
from extract_cobol_data import extract as extract_cobol_data  # noqa: E402
from extract_cobol_screen import extract as extract_cobol_screen  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
COBOL_SCREEN_SECTION = FIXTURES / "cobol_screen_section"
COBOL_MIXED = FIXTURES / "cobol_mixed"
UNKNOWN_MENU_LOOP = FIXTURES / "unknown_menu_loop"
PROFILES_DIR = profile_lib.PROFILES_DIR


# ---------------------------------------------------------------------------
# (a) E2E COBOL SCREEN SECTION: screens + CRUD/db-objects, all validators PASS
# ---------------------------------------------------------------------------

def _screen_list_md_for_screen_section(digest: dict) -> str:
    """Hand-render screen-list.md consistent with the real digest (mirrors the LLM
    doc-writer pass -- this skill is scanner-only, Python emits no markdown itself),
    same shape proven by test_cobol_screen_validators_e2e.py against the same
    underlying content (inline_screen.cbl, reused verbatim in this fixture)."""
    by_name = {s["screen"]: s for s in digest["screens"]}
    assert set(by_name) == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}
    menu = by_name["MENU-SCREEN"]
    item = by_name["ITEM-ENQUIRY-SCREEN"]
    menu_cite = menu["entry_citation"]
    item_cite = item["entry_citation"]
    perform_edge = menu["flow_edges"][0]
    perform_cite = f"{perform_edge['file']}:{perform_edge['line']}"

    return f"""\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_MenuScreen | MENU-SCREEN | screen-section | **Source:** `{menu_cite}` |
| SCR002_ItemEnquiryScreen | ITEM-ENQUIRY-SCREEN | screen-section | **Source:** `{item_cite}` |

## SCR001_MenuScreen: MENU-SCREEN

Main stock enquiry menu screen; reachable via DISPLAY/ACCEPT MENU-SCREEN. **Source:** `{menu_cite}`

- Component WS-OPTION: single-character menu selection field. **Source:** `{menu_cite}`
- Related screen SCR002_ItemEnquiryScreen: performs on option 1/2. **Source:** `{perform_cite}`

## SCR002_ItemEnquiryScreen: ITEM-ENQUIRY-SCREEN

Item enquiry detail screen; reachable via DISPLAY/ACCEPT ITEM-ENQUIRY-SCREEN. **Source:** `{item_cite}`

- Component WS-ITEM-CODE: highlighted item-code input field. **Source:** `{item_cite}`
"""


def _screen_flow_md_for_screen_section(digest: dict) -> str:
    by_name = {s["screen"]: s for s in digest["screens"]}
    menu_cite = by_name["MENU-SCREEN"]["entry_citation"]
    item_cite = by_name["ITEM-ENQUIRY-SCREEN"]["entry_citation"]
    perform_edge = by_name["MENU-SCREEN"]["flow_edges"][0]
    perform_cite = f"{perform_edge['file']}:{perform_edge['line']}"

    return f"""\
## Navigation Map

```mermaid
graph TD
    A[Start] -->|DISPLAY MENU-SCREEN| B[SCR001_MenuScreen]
    B -->|PERFORM on option 1/2| C[SCR002_ItemEnquiryScreen]
```

## Screen Access Paths

| From Screen | To Screen | Action/Trigger | Source |
|-------------|-----------|-----------------|--------|
| Start | SCR001_MenuScreen | Program entry, DISPLAY/ACCEPT MENU-SCREEN | **Source:** `{menu_cite}` |
| SCR001_MenuScreen | SCR002_ItemEnquiryScreen | Option 1 or 2, PERFORM | **Source:** `{perform_cite}` |

## Screen Transitions

### SCR001_MenuScreen (MENU-SCREEN)

Entry point of the program. **Source:** `{menu_cite}`

- Entry: program start, no caller. **Source:** `{menu_cite}`
- Exit: to SCR002_ItemEnquiryScreen on option 1/2 selection. **Source:** `{perform_cite}`

### SCR002_ItemEnquiryScreen (ITEM-ENQUIRY-SCREEN)

Reachable via DISPLAY/ACCEPT. **Source:** `{item_cite}`

- Entry: from SCR001_MenuScreen via PERFORM. **Source:** `{perform_cite}`
"""


def _crud_matrix_md_for_screen_section(data_flow_digest: dict) -> str:
    """Hand-render crud-matrix.md from the real extract_cobol_data.py digest: one row
    per db_op (STOCK's full C/R/U/D verb set), each carrying its own citation."""
    unit = next(u for u in data_flow_digest["units"] if u["path"] == "stock_crud.cbl")
    ops_by_op = {op["op"]: op for op in unit["db_ops"]}
    assert set(ops_by_op) == {"C", "R", "U", "D"}

    def _row(op: str) -> str:
        marks = ["✓" if op == col else " " for col in ("C", "R", "U", "D")]
        cite = ops_by_op[op]["citation"]
        return f"| STOCK | {marks[0]} | {marks[1]} | {marks[2]} | {marks[3]} |  | **Source:** `{cite}` |"

    rows = "\n".join(_row(op) for op in ("C", "R", "U", "D"))
    return f"""\
## Feature: Stock Enquiry (COBOL flat-file CRUD)

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
{rows}
"""


def _db_objects_md_for_screen_section(sql_schema_digest: dict) -> str:
    obj = next(o for o in sql_schema_digest["db_objects"] if o["name"] == "STOCK")
    assert obj["kind"] == "dataset"
    return f"""\
## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| STOCK | Indexed stock master dataset (flat-file/VSAM-style, DYNAMIC access) | **Source:** `{obj['citation']}` |
"""


class TestCobolScreenSectionEndToEnd:
    """Part (a): a COBOL repo that previously produced NO screens now produces cited
    screen-list/flow + CRUD/db-objects, and all four validators PASS."""

    def test_detect_stack_profile_recommends_cobol(self):
        out = dsp.detect(str(COBOL_SCREEN_SECTION), file_cap=50_000, sample_cap=5)
        assert out["recommended_profile"] == "cobol"

    def test_extract_cobol_screen_produces_cited_nonempty_screens(self, tmp_path):
        digest = extract_cobol_screen(COBOL_SCREEN_SECTION, tmp_path)
        assert digest["screens"], "expected non-empty screens[]"
        names = {s["screen"] for s in digest["screens"]}
        assert names == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}
        for s in digest["screens"]:
            assert s["entry_citation"]
            assert s["entry_citation"].startswith("inline_screen.cbl:")

    def test_extract_cobol_data_produces_cited_nonempty_crud_and_db_objects(self, tmp_path):
        data_flow, sql_schema = extract_cobol_data(COBOL_SCREEN_SECTION, tmp_path)
        stock_unit = next(u for u in data_flow["units"] if u["path"] == "stock_crud.cbl")
        assert stock_unit["db_ops"], "expected non-empty db_ops[]"
        assert {op["op"] for op in stock_unit["db_ops"]} == {"C", "R", "U", "D"}
        for op in stock_unit["db_ops"]:
            assert op["citation"].startswith("stock_crud.cbl:")
        assert sql_schema["db_objects"], "expected non-empty db_objects[]"
        for obj in sql_schema["db_objects"]:
            assert obj["citation"].startswith("stock_crud.cbl:")

    def test_all_four_validators_pass(self, tmp_path):
        project_root = tmp_path
        plan_dir = project_root / "plans" / "cobol-e2e"
        artifacts = plan_dir / "artifacts"
        artifacts.mkdir(parents=True)

        screen_digest = extract_cobol_screen(COBOL_SCREEN_SECTION, plan_dir)
        data_flow_digest, sql_schema_digest = extract_cobol_data(COBOL_SCREEN_SECTION, plan_dir)

        (artifacts / "screen-list.md").write_text(
            _screen_list_md_for_screen_section(screen_digest), encoding="utf-8"
        )
        (artifacts / "screen-flow.md").write_text(
            _screen_flow_md_for_screen_section(screen_digest), encoding="utf-8"
        )
        (artifacts / "crud-matrix.md").write_text(
            _crud_matrix_md_for_screen_section(data_flow_digest), encoding="utf-8"
        )
        (artifacts / "db-objects.md").write_text(
            _db_objects_md_for_screen_section(sql_schema_digest), encoding="utf-8"
        )

        sl_result = validate_screen_list.validate(plan_dir, project_root, screen_source="cobol-screen")
        assert sl_result["status"] == "PASS", sl_result["issues"]

        cite_result = validate_source_citations.validate(
            plan_dir, project_root, single=None, re_mode=True, density_min=0.8
        )
        all_issues = [i for spec in cite_result["specs"].values() for i in spec["issues"]]
        critical = [i for i in all_issues if i["severity"] == "critical"]
        assert critical == [], critical

        crud_result = validate_crud_matrix.validate(plan_dir, project_root)
        assert crud_result["status"] == "PASS", crud_result["issues"]

        db_result = validate_db_catalog.validate(plan_dir, project_root)
        assert db_result["status"] == "PASS", db_result["issues"]


# ---------------------------------------------------------------------------
# (b) E2E mixed-paradigm: router dispatches BOTH paradigms in ONE run, one
# merged screen digest, no --profile pin needed
# ---------------------------------------------------------------------------

class TestCobolMixedParadigmEndToEnd:
    def test_detect_stack_profile_recommends_cobol_no_pin_needed(self):
        out = dsp.detect(str(COBOL_MIXED), file_cap=50_000, sample_cap=5)
        assert out["recommended_profile"] == "cobol"
        assert out["confidence"] > 0.0

    def test_router_merges_both_paradigms_into_one_digest(self, tmp_path):
        digest = extract_cobol_screen(COBOL_MIXED, tmp_path)
        screens = digest["screens"]
        assert len(screens) == 3

        by_kind: dict[str, list[dict]] = {}
        for s in screens:
            by_kind.setdefault(s["kind"], []).append(s)
        assert set(by_kind) == {"screen-section", "cics-bms"}

        section_names = {s["screen"] for s in by_kind["screen-section"]}
        assert section_names == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}
        bms_names = {s["screen"] for s in by_kind["cics-bms"]}
        assert bms_names == {"ORDRMAP"}

        for s in screens:
            assert s["entry_citation"], f"{s['screen']} missing a citation"


# ---------------------------------------------------------------------------
# (c) Generic-fallback (Track D): Tier-2 sniff verdict + headless accept-path,
# never mutates references/stack-profiles/
# ---------------------------------------------------------------------------

def _snapshot_profiles_dir() -> dict[str, str]:
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(PROFILES_DIR.glob("*"))
        if p.is_file()
    }


def _render_screen_list_md_from_sparse(screens: list[dict]) -> str:
    """Minimal hand-rendered screen-list.md from a sparse ui-sniff digest, same shape
    proven by test_ui_sniff_accept.py's TestEndToEndValidatorPass."""
    lines = ["# Screen List", "", "## Screen Index", "", "| Code | Name | Type |", "|------|------|------|"]
    codes = []
    for i, screen in enumerate(screens, start=1):
        code = f"SCR{i:03d}_{screen['screen'][:20]}"
        codes.append(code)
        lines.append(f"| {code} | {screen['screen']} | ui-sniff-lead |")
    lines.append("")
    for code, screen in zip(codes, screens):
        lines.append(f"## {code}: {screen['screen']}")
        lines.append("")
        lines.append(
            f"[UNVERIFIED] lead sniffed from `{screen['entry_citation']}` "
            f"(family: {screen['raw']['family']})."
        )
        lines.append("")
        lines.append(f"- Reachability: {'static' if screen['reachable'] else '[UNVERIFIED]'} — `{screen['entry_citation']}`")
        lines.append("")
    return "\n".join(lines)


class TestGenericFallbackUiSniffAcceptPath:
    def test_no_stack_profile_matched_and_tier2_verdict_with_citations(self):
        out = dsp.detect(str(UNKNOWN_MENU_LOOP), file_cap=50_000, sample_cap=5)
        assert out["matched"] == []
        assert out["recommended_profile"] is None
        assert out["ui_sniff"]["tier"] == 2
        assert out["ui_sniff"]["signals"], "expected at least one cited signal"
        for sig in out["ui_sniff"]["signals"]:
            assert sig["citation"]

    def test_planted_secret_is_scrubbed_before_reaching_any_citation(self):
        out = dsp.detect(str(UNKNOWN_MENU_LOOP), file_cap=50_000, sample_cap=5)
        citations = [s["citation"] for s in out["ui_sniff"]["signals"]]
        assert any("login.sh" in c for c in citations), "expected the planted-secret file to be sniffed"
        for c in citations:
            assert "hunter2secret" not in c
        dialog_citations = [c for c in citations if "login.sh" in c]
        assert any("<redacted>" in c for c in dialog_citations)

    def test_full_accept_flow_end_to_end_never_mutates_kit_profiles(self, tmp_path):
        before = _snapshot_profiles_dir()
        assert before, "sanity: stack-profiles dir must be non-empty for this test to mean anything"

        out = dsp.detect(str(UNKNOWN_MENU_LOOP), file_cap=50_000, sample_cap=5)
        assert out["ui_sniff"]["tier"] == 2
        signals = out["ui_sniff"]["signals"]

        # Drive the ACCEPT path headlessly, simulating what SKILL.md's ACCEPT branch invokes.
        plan_dir = tmp_path / "plan"
        digest_path = accept_lib.write_ui_sniff_digest(plan_dir, signals, summary=out["ui_sniff"]["summary"])
        digest = json.loads(digest_path.read_text(encoding="utf-8"))
        assert digest["screens"]
        assert all(s["unverified"] is True for s in digest["screens"])

        with open(PROFILES_DIR / "generic-source.json", encoding="utf-8") as f:
            base_profile = json.load(f)
        assert base_profile["screen_source"] == "none"

        overridden = accept_lib.override_profile_for_ui_sniff(base_profile)
        assert overridden["screen_source"] == "ui-sniff"
        assert overridden["artifact_map"]["screen-list"]["action"] == "produce"
        assert overridden["artifact_map"]["screen-flow"]["action"] == "produce"
        accept_lib.write_profile_override_sidecar(plan_dir, overridden)

        # Hand-render + validate the sparse screen-list.
        artifacts = plan_dir / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "screen-list.md").write_text(
            _render_screen_list_md_from_sparse(digest["screens"]), encoding="utf-8"
        )
        result = validate_screen_list.validate(plan_dir, tmp_path, screen_source="ui-sniff")
        assert result["status"] == "PASS", result["issues"]
        assert result["summary"]["critical"] == 0

        after = _snapshot_profiles_dir()
        assert after == before, "no file under references/stack-profiles/ may be mutated by the accept path"
