"""Tests for validate_route_list.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_route_list import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_ROUTE_LIST = """\
## Backend Routes

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | /api/users | UserController@index | yes | List all users |
| POST | /api/users | UserController@store | yes | Create user |
| PUT | /api/users/{id} | UserController@update | yes | Update user |
| DELETE | /api/users/{id} | UserController@destroy | yes | Delete user |

## Summary

4 routes total.
"""

DUPLICATE_ROUTE = """\
## Backend Routes

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | /api/users | UserController@index | yes | List all users |
| GET | /api/users | UserController@index | yes | Duplicate! |
| POST | /api/users | UserController@store | yes | Create user |

## Summary

Routes with duplicate.
"""

DUPLICATE_ROUTE_WHITESPACE = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
|  GET | /api/users | UserController@index | yes |
|GET|/api/users|UserController@index|yes|

## Summary

Padded + compact rows for the SAME route — skipped by the old single-space gate regex.
"""

MISSING_HANDLER = """\
## Backend Routes

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | /api/users |  | yes | Missing handler |
| POST | /api/users | UserController@store | yes | OK |

## Summary

One missing handler.
"""

MISSING_BACKEND_SECTION = """\
## Routes Overview

| Method | Path | Handler |
|--------|------|---------|
| GET | /api/users | UserController@index |

## Summary

No backend routes section.
"""

MISSING_SUMMARY_SECTION = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
"""

MERGED_WITH_DUPLICATE_HEADER = """\
## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
| POST | /api/orders | OrderController@store | yes |

## Summary

First fragment.

## Backend Routes

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/products | ProductController@index | yes |

## Summary

Second fragment — duplicate header from merge.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "route-list.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_route_list_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_ROUTE_LIST)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_route_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_ROUTE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "RouteList.no_dup_route" in rule_ids


def test_duplicate_route_whitespace_variants_fail(tmp_path):
    """Padded `|  GET |` and compact `|GET|` rows for the same route must still dup-detect."""
    plan = _setup_plan(tmp_path, DUPLICATE_ROUTE_WHITESPACE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "RouteList.no_dup_route" in rule_ids


def test_missing_backend_section_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_BACKEND_SECTION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "RouteList.required_sections" in rule_ids


def test_merged_with_duplicate_header_fails(tmp_path):
    """Fragment merge producing two ## Backend Routes sections must be caught."""
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "RouteList.single_header" in rule_ids


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_missing_handler_warns(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_HANDLER)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "RouteList.citation_present" in rule_ids


def test_missing_summary_section_warns(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_SUMMARY_SECTION)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "RouteList.required_sections" in rule_ids


def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "RouteList.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_ROUTE_LIST)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_single_file_fail(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_ROUTE)
    rl_file = plan / "artifacts" / "route-list.md"
    rc = main(["--route-list-file", str(rl_file), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_ROUTE_LIST)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "route_list" in summary["validators"]
    assert summary["validators"]["route_list"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2
