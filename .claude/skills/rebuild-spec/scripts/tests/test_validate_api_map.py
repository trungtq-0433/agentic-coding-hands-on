"""Tests for validate_api_map.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_api_map import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_API_MAP = """\
## Endpoints by Domain

### Users

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | /api/users | UserController@index | yes | List users |
| POST | /api/users | UserController@store | yes | Create user |
| GET | /api/users/{id} | UserController@show | yes | Get user |

### Orders

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | /api/orders | OrderController@index | yes | List orders |
| POST | /api/orders | OrderController@store | yes | Create order |
| DELETE | /api/orders/{id} | OrderController@destroy | yes | Delete order |
"""

DUPLICATE_ENDPOINT = """\
## Endpoints by Domain

### Users

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
| POST | /api/users | UserController@store | yes |

### Duplicate Domain

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
"""

DUPLICATE_ENDPOINT_WHITESPACE = """\
## Endpoints by Domain

### Users

| Method | Path | Handler | Auth |
|--------|------|---------|------|
|  GET | /api/users | UserController@index | yes |
|GET|/api/users|UserController@index|yes|
"""

MISSING_HANDLER = """\
## Endpoints by Domain

### Products

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/products |  | yes |
| POST | /api/products | ProductController@store | yes |
"""

MISSING_ENDPOINTS_SECTION = """\
## API Overview

Some text here.

### Subsection

Content without proper section header.
"""

MERGED_WITH_DUPLICATE_HEADER = """\
## Endpoints by Domain

### Auth

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| POST | /api/login | AuthController@login | no |
| POST | /api/logout | AuthController@logout | yes |

## Endpoints by Domain

### Users

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/users | UserController@index | yes |
"""

CROSS_DOMAIN_DUPLICATE = """\
## Endpoints by Domain

### DomainA

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/shared | DomainAController@show | yes |

### DomainB

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | /api/shared | DomainBController@show | yes |
"""

BACKTICK_VS_BARE_DUPLICATE = """\
## Endpoints by Domain

### Users

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `/api/users` | UserController@index | yes |
| GET | /api/users | UserController@index | yes |
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "api-map.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_api_map_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_API_MAP)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_endpoint_within_domain_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_ENDPOINT)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.no_dup_endpoint" in rule_ids


def test_duplicate_endpoint_whitespace_variants_fail(tmp_path):
    """Padded `|  GET |` and compact `|GET|` rows for the same endpoint must dup-detect."""
    plan = _setup_plan(tmp_path, DUPLICATE_ENDPOINT_WHITESPACE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.no_dup_endpoint" in rule_ids


def test_duplicate_endpoint_cross_domain_fails(tmp_path):
    plan = _setup_plan(tmp_path, CROSS_DOMAIN_DUPLICATE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.no_dup_endpoint" in rule_ids


def test_backtick_vs_bare_path_duplicate_fails(tmp_path):
    """Template emits backtick-wrapped paths; a backtick path and its bare twin must dup-detect."""
    plan = _setup_plan(tmp_path, BACKTICK_VS_BARE_DUPLICATE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.no_dup_endpoint" in rule_ids


def test_missing_endpoints_section_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_ENDPOINTS_SECTION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.required_sections" in rule_ids


def test_merged_with_duplicate_header_fails(tmp_path):
    """Fragment merge producing two ## Endpoints by Domain sections must be caught."""
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiMap.single_header" in rule_ids


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_missing_handler_warns(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_HANDLER)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiMap.handler_present" in rule_ids


def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiMap.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_API_MAP)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_single_file_fail(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_ENDPOINT)
    am_file = plan / "artifacts" / "api-map.md"
    rc = main(["--api-map-file", str(am_file), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_API_MAP)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "api_map" in summary["validators"]
    assert summary["validators"]["api_map"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2
