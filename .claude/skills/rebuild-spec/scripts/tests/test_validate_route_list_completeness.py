"""Tests for route-list COMPLETENESS checks (Phase 01).

New rules:
  RouteList.no_approximation_marker  (critical)
  RouteList.no_resource_summary_table (critical)
  RouteList.no_unexpanded_macro       (warning)

Also includes a _summary_lib regression test confirming that a route_list
critical propagates to overall_status=FAIL via recalculate_totals.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_route_list import validate, main  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write,
    derive_overall_status,
    load_summary,
    recalculate_totals,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Compressed resource-summary table (no Method/Path cols) PLUS approximation markers.
COMPRESSED_RESOURCE_SUMMARY = """\
## Backend Routes

| Resource | Actions |
|----------|---------|
| users | index, show, create, update, destroy |
| orders | index, show |

## Summary

~16 resources (+nhiều)
"""

# Approximation marker only (in body prose, not a table).
APPROX_IN_PROSE = """\
## Backend Routes

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/users | UserController@index |

see routes.rb for full list

## Summary

etc.
"""

# Unexpanded Rails resource macro as the Method column value.
UNEXPANDED_RAILS_RESOURCES = """\
## Backend Routes

| Method | Path | Handler |
|--------|------|---------|
| resources | /admin/users | AdminController |

## Summary

Auto-generated.
"""

# Valid complete list — no violations.
VALID_COMPLETE = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
| POST | /api/users | UserController@store | yes |
| GET | /api/users/{id} | UserController@show | yes |
| PUT | /api/users/{id} | UserController@update | yes |
| DELETE | /api/users/{id} | UserController@destroy | yes |

## Summary

5 routes total.
"""

# Route with a literal tilde in the path param — must NOT fire approximation check.
TILDE_PATH_PARAM = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/~user/profile | UserController@profile | yes |
| POST | /api/items | ItemController@store | yes |

## Summary

2 routes, tilde in path.
"""

# H1 regression: `etc.` in the Handler column of a table row — must NOT trigger critical.
ETC_IN_HANDLER_CELL = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index, etc. | yes |
| POST | /api/users | UserController@store | yes |

## Summary

2 routes total.
"""

# H1 regression: `etc.` in a prose (non-table) line inside the Backend Routes section → critical.
ETC_IN_PROSE_LINE = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |

and 30 more routes, etc.

## Summary

31 routes total.
"""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    (plan / "artifacts" / "route-list.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Test: H1 regression — etc. in table cell vs prose
# ---------------------------------------------------------------------------

def test_etc_in_handler_cell_no_false_positive(tmp_path):
    """H1: `etc.` in Handler column cell must NOT trigger RouteList.no_approximation_marker."""
    plan = _setup_plan(tmp_path, ETC_IN_HANDLER_CELL)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert not approx_issues, (
        f"False positive: 'etc.' in handler cell triggered approximation marker check: {approx_issues}"
    )
    assert result["status"] == "PASS"


def test_etc_in_prose_line_detected(tmp_path):
    """H1: `etc.` in a prose (non-table) line signals compression → critical."""
    plan = _setup_plan(tmp_path, ETC_IN_PROSE_LINE)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert approx_issues, "Expected critical for 'etc.' in prose line"
    assert all(i["severity"] == "critical" for i in approx_issues)
    assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Test: resource-summary table (critical)
# ---------------------------------------------------------------------------

def test_resource_summary_compression_detected(tmp_path):
    """A | Resource | Actions | table without Method/Path → critical."""
    plan = _setup_plan(tmp_path, COMPRESSED_RESOURCE_SUMMARY)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "RouteList.no_resource_summary_table" in rule_ids


def test_resource_summary_severity_is_critical(tmp_path):
    plan = _setup_plan(tmp_path, COMPRESSED_RESOURCE_SUMMARY)
    result = validate(plan, tmp_path)
    crits = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "RouteList.no_resource_summary_table" in crits


# ---------------------------------------------------------------------------
# Test: approximation markers (critical)
# ---------------------------------------------------------------------------

def test_approximation_marker_tilde_n_detected(tmp_path):
    """~16 resources in the summary body → critical."""
    plan = _setup_plan(tmp_path, COMPRESSED_RESOURCE_SUMMARY)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "RouteList.no_approximation_marker" in rule_ids


def test_approximation_marker_viet_detected(tmp_path):
    """(+nhiều) marker → critical."""
    plan = _setup_plan(tmp_path, COMPRESSED_RESOURCE_SUMMARY)
    result = validate(plan, tmp_path)
    crits = [i for i in result["issues"]
             if i["rule_id"] == "RouteList.no_approximation_marker" and i["severity"] == "critical"]
    assert crits, "Expected at least one critical for approximation marker"


def test_see_routes_rb_detected(tmp_path):
    """'see routes.rb' prose line → critical."""
    plan = _setup_plan(tmp_path, APPROX_IN_PROSE)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "RouteList.no_approximation_marker" in rule_ids


def test_etc_marker_detected(tmp_path):
    """'etc.' in body → critical."""
    plan = _setup_plan(tmp_path, APPROX_IN_PROSE)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "RouteList.no_approximation_marker" in rule_ids


# ---------------------------------------------------------------------------
# Test: unexpanded macro (warning)
# ---------------------------------------------------------------------------

def test_unexpanded_rails_macro_detected(tmp_path):
    """Row with 'resources' as Method column → warning."""
    plan = _setup_plan(tmp_path, UNEXPANDED_RAILS_RESOURCES)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "RouteList.no_unexpanded_macro" in rule_ids


def test_unexpanded_macro_severity_is_warning(tmp_path):
    plan = _setup_plan(tmp_path, UNEXPANDED_RAILS_RESOURCES)
    result = validate(plan, tmp_path)
    warns = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "RouteList.no_unexpanded_macro" in warns


def test_unexpanded_macro_status_is_warn_not_fail(tmp_path):
    """Macro-only violation → WARN (not FAIL), since no critical issues."""
    plan = _setup_plan(tmp_path, UNEXPANDED_RAILS_RESOURCES)
    result = validate(plan, tmp_path)
    # The macro row also lacks a valid HTTP method — no dup/citation issues triggered.
    assert result["summary"]["critical"] == 0
    assert result["status"] == "WARN"


# ---------------------------------------------------------------------------
# Test: valid complete list → PASS
# ---------------------------------------------------------------------------

def test_valid_complete_list_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_COMPLETE)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


# ---------------------------------------------------------------------------
# Test: tilde path param must NOT false-fire
# ---------------------------------------------------------------------------

def test_tilde_path_param_no_false_positive(tmp_path):
    """A literal ~ in a URL path cell must not trigger RouteList.no_approximation_marker."""
    plan = _setup_plan(tmp_path, TILDE_PATH_PARAM)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert not approx_issues, (
        f"False positive: tilde in URL path triggered approximation marker check: {approx_issues}"
    )
    assert result["status"] == "PASS"


# ---------------------------------------------------------------------------
# Test: _summary_lib regression — route_list critical sets overall_status=FAIL
# ---------------------------------------------------------------------------

def test_route_list_critical_propagates_to_overall_status_fail(tmp_path):
    """recalculate_totals must sum route_list critical into totals → overall_status=FAIL."""
    summary_path = tmp_path / "validation-summary.json"
    plan = _setup_plan(tmp_path, COMPRESSED_RESOURCE_SUMMARY)

    # Run the validator with --summary-out so it writes the slot.
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])

    assert rc == 1, "Validator should exit 1 (FAIL) for compressed route list"
    assert summary_path.is_file()

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "route_list" in data["validators"]
    assert data["validators"]["route_list"]["status"] == "FAIL"
    # recalculate_totals must have included route_list criticals
    assert data["totals"]["critical"] > 0
    assert data["overall_status"] == "FAIL"


def test_route_list_warning_only_propagates_to_overall_status_warn(tmp_path):
    """recalculate_totals must sum route_list warnings → overall_status=WARN (not FAIL)."""
    summary_path = tmp_path / "validation-summary.json"
    plan = _setup_plan(tmp_path, UNEXPANDED_RAILS_RESOURCES)

    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])

    assert rc == 0, "Validator should exit 0 (WARN) for unexpanded macro only"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["totals"]["critical"] == 0
    assert data["totals"]["warning"] > 0
    assert data["overall_status"] == "WARN"


def test_recalculate_totals_route_list_slot_standalone():
    """Unit test recalculate_totals directly with a pre-populated route_list slot."""
    summary = {
        "validators": {
            "route_list": {
                "status": "FAIL",
                "summary": {"critical": 2, "warning": 1},
                "issues": [],
            }
        },
        "totals": {},
    }
    recalculate_totals(summary)
    assert summary["totals"]["critical"] == 2
    assert summary["totals"]["warning"] == 1
    assert derive_overall_status(summary) == "FAIL"


def test_recalculate_totals_screen_list_slot_standalone():
    """screen_list slot is also included by recalculate_totals."""
    summary = {
        "validators": {
            "screen_list": {
                "status": "WARN",
                "summary": {"critical": 0, "warning": 3},
                "issues": [],
            }
        },
        "totals": {},
    }
    recalculate_totals(summary)
    assert summary["totals"]["critical"] == 0
    assert summary["totals"]["warning"] == 3
    assert derive_overall_status(summary) == "WARN"


def test_recalculate_totals_no_double_count_feature_existence():
    """feature_existence must not be double-counted (it's in the explicit allowlist, not route_list/screen_list)."""
    summary = {
        "validators": {
            "feature_existence": {
                "status": "FAIL",
                "summary": {"critical": 1, "warning": 0},
                "issues": [],
            },
            "route_list": {
                "status": "WARN",
                "summary": {"critical": 0, "warning": 1},
                "issues": [],
            },
        },
        "totals": {},
    }
    recalculate_totals(summary)
    # feature_existence contributes 1 critical; route_list contributes 1 warning — no double-count
    assert summary["totals"]["critical"] == 1
    assert summary["totals"]["warning"] == 1


# ---------------------------------------------------------------------------
# Tests — A2: APPROX_RE narrowed to file-reference form
# ---------------------------------------------------------------------------

SEE_ROUTES_HEADING = """\
## Backend Routes

## See Routes Overview

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/users | UserController@index |

## Summary

1 route.
"""

SEE_ROUTES_SECTION_PROSE = """\
## Backend Routes

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/users | UserController@index |

See routes section for authentication paths.

## Summary

1 route.
"""

SEE_ROUTES_FILE_REF = """\
## Backend Routes

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/users | UserController@index |

see routes.rb for full list

## Summary

1 route.
"""


def test_see_routes_heading_no_false_positive(tmp_path):
    """A2: '## See Routes Overview' heading must NOT trigger no_approximation_marker."""
    plan = _setup_plan(tmp_path, SEE_ROUTES_HEADING)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert not approx_issues, (
        f"False positive on heading: {approx_issues}"
    )


def test_see_routes_section_prose_no_false_positive(tmp_path):
    """A2: 'See routes section for auth paths' prose must NOT trigger no_approximation_marker."""
    plan = _setup_plan(tmp_path, SEE_ROUTES_SECTION_PROSE)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert not approx_issues, (
        f"False positive on prose 'See routes section': {approx_issues}"
    )


def test_see_routes_file_ref_detected(tmp_path):
    """A2: 'see routes.rb for full list' → critical no_approximation_marker."""
    plan = _setup_plan(tmp_path, SEE_ROUTES_FILE_REF)
    result = validate(plan, tmp_path)
    approx_issues = [i for i in result["issues"]
                     if i["rule_id"] == "RouteList.no_approximation_marker"]
    assert approx_issues, "Expected critical for 'see routes.rb' file reference"
    assert all(i["severity"] == "critical" for i in approx_issues)
