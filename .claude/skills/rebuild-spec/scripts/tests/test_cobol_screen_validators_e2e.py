"""Phase 04 (cobol-stack-and-generic-fallback plan) — Track-A release gate.

End-to-end: run the real COBOL SCREEN SECTION extractor against a real fixture
(`tests/fixtures/cobol_real_sample/inline_screen.cbl`) to get a real digest, hand-author
screen-list.md/screen-flow.md consistent with that digest (mirroring what the LLM doc-writer
would produce — this skill is scanner-only, Python emits no markdown itself), then run BOTH
owned validators (`validate_screen_list.py`, `validate_source_citations.py --re-mode`)
against the result with `--screen-source cobol-screen`.

This is the genuine green run gating Phase 4b (Track A SCREEN SECTION release), not just a
unit-level allowlist check. It also incidentally proves the `--screen-source cobol-screen`
CLI choice (added this phase) resolves end to end, and that citation-density >= 80% holds
for real COBOL-derived content.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from extract_cobol_screen import extract  # noqa: E402
from validate_screen_list import validate as validate_screen_list  # noqa: E402
from validate_source_citations import validate as validate_citations  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "cobol_real_sample" / "inline_screen.cbl"


def _run_extractor(tmp_path: Path) -> dict:
    """Copy the real fixture into an isolated project root and run the real extractor."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "inline_screen.cbl").write_text(
        FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    plan_dir = project_root / "plans" / "cobol-e2e"
    plan_dir.mkdir(parents=True)
    return extract(project_root, plan_dir)


def _screen_list_md(digest: dict) -> str:
    """Hand-author screen-list.md content consistent with the real digest's screens.

    Digest screens (real, from inline_screen.cbl): MENU-SCREEN (entry_citation
    inline_screen.cbl:44) -> performs -> ITEM-ENQUIRY-SCREEN (entry_citation
    inline_screen.cbl:54). Asserted below so this fixture stays honest if the extractor
    output ever shifts.
    """
    by_name = {s["screen"]: s for s in digest["screens"]}
    assert set(by_name) == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}
    menu = by_name["MENU-SCREEN"]
    item = by_name["ITEM-ENQUIRY-SCREEN"]
    assert menu["kind"] == "screen-section"
    assert item["kind"] == "screen-section"
    menu_cite = menu["entry_citation"]
    item_cite = item["entry_citation"]
    perform_edge = menu["flow_edges"][0]
    assert perform_edge["to"] == "ITEM-ENQUIRY-SCREEN"
    perform_cite = f"{perform_edge['file']}:{perform_edge['line']}"

    return f"""\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_MenuScreen | MENU-SCREEN | screen-section | **Source:** `{menu_cite}` |
| SCR002_ItemEnquiryScreen | ITEM-ENQUIRY-SCREEN | screen-section | **Source:** `{item_cite}` |

## SCR001_MenuScreen: MENU-SCREEN

Main stock enquiry menu screen; reachable via DISPLAY/ACCEPT MENU-SCREEN in BA000-SHOW-MENU. **Source:** `{menu_cite}`

- Component WS-OPTION: single-character menu selection field, AUTO. **Source:** `inline_screen.cbl:27`
- Related screen SCR002_ItemEnquiryScreen: ITEM-ENQUIRY-SCREEN (performs on option 1/2). **Source:** `{perform_cite}`

## SCR002_ItemEnquiryScreen: ITEM-ENQUIRY-SCREEN

Item enquiry detail screen; reachable via DISPLAY/ACCEPT ITEM-ENQUIRY-SCREEN in CA000-ITEM-ENQUIRY. **Source:** `{item_cite}`

- Component WS-ITEM-CODE: highlighted item-code input field. **Source:** `inline_screen.cbl:32`
- Related screen SCR001_MenuScreen: MENU-SCREEN (loop back after enquiry). **Source:** `inline_screen.cbl:56`
"""


def _screen_flow_md(digest: dict) -> str:
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
    B -->|PERFORM CA000-ITEM-ENQUIRY on option 1/2| C[SCR002_ItemEnquiryScreen]
    C -->|GO TO BA010 loop back| B
```

## Screen Access Paths

| From Screen | To Screen | Action/Trigger | Source |
|-------------|-----------|-----------------|--------|
| Start | SCR001_MenuScreen | Program entry, DISPLAY/ACCEPT MENU-SCREEN | **Source:** `{menu_cite}` |
| SCR001_MenuScreen | SCR002_ItemEnquiryScreen | Option 1 or 2, PERFORM CA000-ITEM-ENQUIRY | **Source:** `{perform_cite}` |
| SCR002_ItemEnquiryScreen | SCR001_MenuScreen | GO TO BA010 loop back | **Source:** `inline_screen.cbl:56` |

## Screen Transitions

### SCR001_MenuScreen (MENU-SCREEN)

Entry point of the program; reachable via DISPLAY/ACCEPT in BA000-SHOW-MENU. **Source:** `{menu_cite}`

- Entry: program start, no caller (top-level SECTION). **Source:** `inline_screen.cbl:42`
- Exit: to SCR002_ItemEnquiryScreen on option 1/2 selection. **Source:** `{perform_cite}`

### SCR002_ItemEnquiryScreen (ITEM-ENQUIRY-SCREEN)

Reachable via DISPLAY/ACCEPT in CA000-ITEM-ENQUIRY. **Source:** `{item_cite}`

- Entry: from SCR001_MenuScreen via PERFORM CA000-ITEM-ENQUIRY. **Source:** `{perform_cite}`
- Exit: back to SCR001_MenuScreen via unconditional loop. **Source:** `inline_screen.cbl:56`
"""


def test_screen_section_digest_shape(tmp_path):
    """Sanity: the real extractor run on the real fixture produces the 2 expected screens."""
    digest = _run_extractor(tmp_path)
    assert digest["extractor"] == "extract_cobol_screen"
    names = {s["screen"] for s in digest["screens"]}
    assert names == {"MENU-SCREEN", "ITEM-ENQUIRY-SCREEN"}
    assert not digest["warnings"]


def test_cobol_screen_list_passes_validate_screen_list(tmp_path):
    """Track-A release gate part 1: validate_screen_list.py PASSes on real COBOL output."""
    digest = _run_extractor(tmp_path)
    plan_dir = tmp_path / "project" / "plans" / "cobol-e2e"
    artifacts = plan_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "screen-list.md").write_text(_screen_list_md(digest), encoding="utf-8")

    result = validate_screen_list(plan_dir, tmp_path / "project", screen_source="cobol-screen")
    assert result["status"] == "PASS", result["issues"]
    assert result["summary"]["critical"] == 0


def test_cobol_screen_flow_and_list_pass_citation_density(tmp_path):
    """Track-A release gate part 2: validate_source_citations.py --re-mode PASSes,
    with citation-density >= 80% on both screen-list.md and screen-flow.md."""
    digest = _run_extractor(tmp_path)
    project_root = tmp_path / "project"
    plan_dir = project_root / "plans" / "cobol-e2e"
    artifacts = plan_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "screen-list.md").write_text(_screen_list_md(digest), encoding="utf-8")
    (artifacts / "screen-flow.md").write_text(_screen_flow_md(digest), encoding="utf-8")

    result = validate_citations(plan_dir, project_root, single=None, re_mode=True, density_min=0.8)
    all_issues = [i for spec in result["specs"].values() for i in spec["issues"]]
    critical = [i for i in all_issues if i["severity"] == "critical"]
    density_warns = [i for i in all_issues if i["rule_id"] == "citation_density_low"]
    assert critical == [], critical
    assert density_warns == [], (
        f"citation density below 80% threshold: {density_warns}"
    )
    assert "screen-list" in result["specs"]
    assert "screen-flow" in result["specs"]
