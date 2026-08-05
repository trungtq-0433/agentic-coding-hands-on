"""Tests for validate_screen_list.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_screen_list import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SCREEN_LIST = """\
## Screen Index

| SCR Code | Name | Route | Auth |
|----------|------|-------|------|
| SCR001_Login | Login | /login | no |
| SCR002_Dashboard | Dashboard | /dashboard | yes |
| SCR003_UserList | User List | /users | yes |

## SCR001_Login

**Route:** /login
**Auth:** no

### Regions

| REG Code | Name | Description |
|----------|------|-------------|
| REG001 | LoginForm | Email + password form |
| REG002 | ErrorMessage | Inline validation errors |

## SCR002_Dashboard

**Route:** /dashboard
**Auth:** yes

### Regions

| REG Code | Name | Description |
|----------|------|-------------|
| REG001 | StatsPanel | Summary metrics |
| REG002 | RecentActivity | Last 10 events |

## SCR003_UserList

**Route:** /users
**Auth:** yes

### Regions

| REG Code | Name | Description |
|----------|------|-------------|
| REG001 | UserTable | Paginated user rows |
"""

DUPLICATE_SCR = """\
## Screen Index

| SCR Code | Name |
|----------|------|
| SCR001_Login | Login |
| SCR001_Login | Login Again |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | LoginForm |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | AnotherForm |
"""

DUPLICATE_REG_WITHIN_SCR = """\
## Screen Index

| SCR Code | Name |
|----------|------|
| SCR001_Login | Login |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | LoginForm |
| REG001 | DuplicateForm |
| REG002 | ErrorMessage |
"""

DUPLICATE_REG_SUFFIXED = """\
## Screen Index

| SCR Code | Name |
|----------|------|
| SCR001_Login | Login |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001_LoginForm | Login form A |
| REG001_LoginForm | Login form B (duplicate) |
| REG002_ErrorMessage | Errors |
"""

ORPHAN_REG = """\
## Screen Index

| SCR Code | Name |
|----------|------|
| SCR001_Login | Login |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | LoginForm |

## Some Other Section

### Orphaned Regions

| REG Code | Name |
|----------|------|
| REG002 | OrphanRegion |
"""

MISSING_SCREEN_INDEX = """\
## SCR001_Login

**Route:** /login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | LoginForm |
"""

MERGED_WITH_DUPLICATE_HEADER = """\
## Screen Index

| SCR Code | Name |
|----------|------|
| SCR001_Login | Login |

## SCR001_Login

### Regions

| REG Code | Name |
|----------|------|
| REG001 | LoginForm |

## Screen Index

| SCR Code | Name |
|----------|------|
| SCR002_Dashboard | Dashboard |

## SCR002_Dashboard

### Regions

| REG Code | Name |
|----------|------|
| REG001 | StatsPanel |
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "screen-list.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_screen_list_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_SCREEN_LIST)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS", result["issues"]
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_scr_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_SCR)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_dup_scr" in rule_ids


def test_duplicate_reg_within_scr_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_REG_WITHIN_SCR)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_dup_reg" in rule_ids


def test_duplicate_suffixed_reg_fails(tmp_path):
    """Slug-suffixed REG codes (REG001_LoginForm) must dup-detect — `\\b` used to miss them."""
    plan = _setup_plan(tmp_path, DUPLICATE_REG_SUFFIXED)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_dup_reg" in rule_ids


def test_orphan_reg_fails(tmp_path):
    plan = _setup_plan(tmp_path, ORPHAN_REG)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.orphan_reg" in rule_ids


# ---------------------------------------------------------------------------
# Tests — v21.0.0 stack-aware route decoupling (--screen-source)
# ---------------------------------------------------------------------------

WILDCARD_ROUTE_LIST = """\
## Screen Index

| SCR Code | Name | Route | Auth |
|----------|------|-------|------|
| SCR001_Admin | Admin | /admin/* | yes |

## SCR001_Admin

**Route:** /admin/*
**Auth:** yes
"""


def test_wildcard_route_fails_under_route_view(tmp_path):
    # Default (route-view): a wildcard route is a critical no_wildcard_route violation.
    plan = _setup_plan(tmp_path, WILDCARD_ROUTE_LIST)
    result = validate(plan, tmp_path)  # screen_source defaults to route-view
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_wildcard_route_bypassed_under_dfm_form(tmp_path):
    # dfm-form: there are no routes, so the route-specific wildcard check is skipped.
    # (A Delphi screen-list would never carry `/admin/*`; this proves the bypass.)
    plan = _setup_plan(tmp_path, WILDCARD_ROUTE_LIST)
    result = validate(plan, tmp_path, screen_source="dfm-form")
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids


def test_structural_checks_still_run_under_dfm_form(tmp_path):
    # Structural checks are stack-neutral: a duplicate ## Screen Index still fails for dfm-form.
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path, screen_source="dfm-form")
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.single_header" in rule_ids


# ---------------------------------------------------------------------------
# Tests — Phase 04 (cobol-stack-and-generic-fallback plan): screen_source
# `cobol-screen` (SCREEN SECTION + CICS BMS, real now/proactive) and `ui-sniff`
# (Track D accept-path, Phase 09 — proactive, not yet built). Both added to the
# `--screen-source` allowlist in ONE additive edit, mirroring the dfm-form diff shape.
# ---------------------------------------------------------------------------

# A screen-section-derived row: a real COBOL SCREEN SECTION screen has no Routes/URLs,
# same as dfm-form. Mirrors the real digest shape from inline_screen.cbl (see
# test_cobol_screen_validators_e2e.py for the full end-to-end run).
COBOL_SCREEN_SECTION_LIST = """\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_MenuScreen | MENU-SCREEN | screen-section | **Source:** `inline_screen.cbl:44` |

## SCR001_MenuScreen: MENU-SCREEN

Main stock enquiry menu screen. **Source:** `inline_screen.cbl:44`

### Regions

| REG Code | Name | Description |
|----------|------|-------------|
| REG001 | MenuOptions | Numbered menu choices |
"""

# A CICS BMS-derived row (proactive — Phase 03 already built the BMS extractor; this is a
# realistic BMS-shaped screen-list fragment, not yet exercised end-to-end by a real digest).
COBOL_BMS_LIST = """\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_OrderMap | ORDMAPO | cics-bms | **Source:** `ORDMAP.bms:12` |

## SCR001_OrderMap: ORDMAPO

CICS BMS map ORDMAPO in mapset ORDMAP, SEND/RECEIVE joined. **Source:** `ORDMAP.bms:12`
"""

# A ui-sniff row (Track D Tier-2 accept-path, Phase 09 — not yet built). Proactive: only
# proves the `--screen-source ui-sniff` value is accepted and structural checks still apply;
# ui-sniff leads cite arbitrary/generic source files, not necessarily COBOL.
UI_SNIFF_LIST = """\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_AccountSummary | AccountSummary | ui-sniff | **Source:** `src/legacy/account_screen.txt:5` |

## SCR001_AccountSummary: AccountSummary

Screen sniffed by the Track D accept-path session. **Source:** `src/legacy/account_screen.txt:5`
"""

# A screen row marked [UNVERIFIED] (e.g. an unresolved COPY target, or a form with no proven
# static inbound edge) — must still structurally validate; the validator has no special-cased
# handling of the literal token, it is just prose.
UNVERIFIED_SCREEN_LIST = """\
## Screen Index

| Code | Name | Kind | Source |
|------|------|------|--------|
| SCR001_UnresolvedCopy | UNRESOLVED-SCREEN | screen-section | [UNVERIFIED] |

## SCR001_UnresolvedCopy: UNRESOLVED-SCREEN

[UNVERIFIED] — COPY target could not be resolved; no source citation available.
"""


def test_wildcard_route_bypassed_under_cobol_screen(tmp_path):
    # cobol-screen (SCREEN SECTION/BMS): no routes exist, so the wildcard-route check is
    # skipped, same rationale as dfm-form.
    plan = _setup_plan(tmp_path, WILDCARD_ROUTE_LIST)
    result = validate(plan, tmp_path, screen_source="cobol-screen")
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids


def test_wildcard_route_bypassed_under_ui_sniff(tmp_path):
    # ui-sniff (Track D accept-path, proactive): same route-free rationale.
    plan = _setup_plan(tmp_path, WILDCARD_ROUTE_LIST)
    result = validate(plan, tmp_path, screen_source="ui-sniff")
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids


def test_structural_checks_still_run_under_cobol_screen(tmp_path):
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path, screen_source="cobol-screen")
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.single_header" in rule_ids


def test_screen_section_row_passes(tmp_path):
    plan = _setup_plan(tmp_path, COBOL_SCREEN_SECTION_LIST)
    result = validate(plan, tmp_path, screen_source="cobol-screen")
    assert result["status"] == "PASS", result["issues"]


def test_cics_bms_row_passes(tmp_path):
    # Proactive: Phase 03's BMS extractor output flows through this same validator path.
    plan = _setup_plan(tmp_path, COBOL_BMS_LIST)
    result = validate(plan, tmp_path, screen_source="cobol-screen")
    assert result["status"] == "PASS", result["issues"]


def test_ui_sniff_row_passes(tmp_path):
    # Proactive: Phase 09 (Track D accept-path) doesn't exist yet — just prove the
    # `ui-sniff` screen_source value is accepted and a plausible row validates cleanly.
    plan = _setup_plan(tmp_path, UI_SNIFF_LIST)
    result = validate(plan, tmp_path, screen_source="ui-sniff")
    assert result["status"] == "PASS", result["issues"]


def test_unverified_row_passes_under_cobol_screen(tmp_path):
    plan = _setup_plan(tmp_path, UNVERIFIED_SCREEN_LIST)
    result = validate(plan, tmp_path, screen_source="cobol-screen")
    assert result["status"] == "PASS", result["issues"]


def test_main_cli_accepts_cobol_screen_source(tmp_path, capsys):
    # Before this phase's edit, argparse rejected `--screen-source cobol-screen` (exit 2).
    plan = _setup_plan(tmp_path, COBOL_SCREEN_SECTION_LIST)
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--screen-source", "cobol-screen",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_cli_accepts_ui_sniff_source(tmp_path, capsys):
    plan = _setup_plan(tmp_path, UI_SNIFF_LIST)
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--screen-source", "ui-sniff",
    ])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_missing_screen_index_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_SCREEN_INDEX)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.required_sections" in rule_ids


def test_merged_with_duplicate_header_fails(tmp_path):
    """Fragment merge producing two ## Screen Index sections must be caught."""
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.single_header" in rule_ids


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ScreenList.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_SCREEN_LIST)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_single_file_fail(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_SCR)
    sl_file = plan / "artifacts" / "screen-list.md"
    rc = main(["--screen-list-file", str(sl_file), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_SCREEN_LIST)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "screen_list" in summary["validators"]
    assert summary["validators"]["screen_list"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2
