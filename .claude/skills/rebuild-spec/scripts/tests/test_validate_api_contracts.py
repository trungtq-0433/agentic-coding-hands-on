"""Tests for validate_api_contracts.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_api_contracts import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CONTRACTS = """\
## Conventions

Shared response envelope and types.

| Type name | Fields |
|-----------|--------|
| UserDTO | id, name, email |

## REST Endpoints

kind: rest

### GET /api/users --- [EXTRACTED]

Lists users. Source: `src/controllers/users.py:42`

### POST /api/users --- [EXTRACTED]

Creates a user. Source: `src/controllers/users.py:88`
"""

MISSING_CONVENTIONS = """\
## REST Endpoints

kind: rest

### GET /api/users --- [EXTRACTED]

Source: `src/users.py:10`
"""

MISSING_KIND_SECTION = """\
## Conventions

Just conventions, no endpoint kind section.
"""

INVALID_KIND = """\
## Conventions

x

## SOAP Endpoints

kind: soap

### POST /soap/op --- [INFERRED]

Source: `src/soap.py:5`
"""

MISSING_CITATION = """\
## Conventions

x

## REST Endpoints

kind: rest

### GET /api/orders --- [EXTRACTED]

Lists orders but provides no file:line citation.
"""

DUPLICATE_KEY = """\
## Conventions

x

## REST Endpoints

kind: rest

### GET /api/users --- [EXTRACTED]

Source: `src/users.py:1`

### GET /api/users --- [INFERRED]

Source: `src/users.py:2`
"""

EMPTY_SURFACE = """\
## API Contracts

No synchronous API surface detected — this is a library/CLI project.
"""

SHARED_TYPE_REDEFINED = """\
## Conventions

Shared types.

| Type name | Fields |
|-----------|--------|
| UserDTO | id, name |

## REST Endpoints

kind: rest

### GET /api/users --- [EXTRACTED]

Source: `src/users.py:1`

**UserDTO**

| Field | Type |
|-------|------|
| id | int |
| name | str |
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str, completed: bool = False) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "api-contracts.md").write_text(content, encoding="utf-8")
    if completed:
        (artifacts / ".api-contracts.completed").write_text("", encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_contracts_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_CONTRACTS, completed=True)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0
    assert result["metrics"]["total"] == 2
    assert result["metrics"]["extracted"] == 2
    assert result["metrics"]["pct_extracted"] == 100.0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_missing_conventions_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_CONVENTIONS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiContracts.section_present" in rule_ids


def test_missing_kind_section_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_KIND_SECTION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiContracts.section_present" in rule_ids


def test_invalid_kind_fails(tmp_path):
    plan = _setup_plan(tmp_path, INVALID_KIND)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiContracts.kind_tag_valid" in rule_ids


def test_missing_citation_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiContracts.citation_missing" in rule_ids


def test_duplicate_key_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_KEY)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ApiContracts.duplicate_key" in rule_ids


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_empty_surface_warns(tmp_path):
    plan = _setup_plan(tmp_path, EMPTY_SURFACE, completed=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiContracts.empty_surface" in rule_ids


def test_shared_type_redefined_warns(tmp_path):
    plan = _setup_plan(tmp_path, SHARED_TYPE_REDEFINED, completed=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiContracts.shared_type_redefined" in rule_ids


def test_missing_completed_marker_warns(tmp_path):
    plan = _setup_plan(tmp_path, VALID_CONTRACTS, completed=False)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiContracts.completed_missing" in rule_ids


def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ApiContracts.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_single_file_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_CONTRACTS, completed=True)
    ac_file = plan / "artifacts" / "api-contracts.md"
    rc = main(["--api-contracts-file", str(ac_file), "--project-root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert json.loads(out.split("[METRIC]")[0])["status"] == "PASS"


def test_main_plan_dir_fail(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_CONTRACTS, completed=True)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "api_contracts" in summary["validators"]
    assert summary["validators"]["api_contracts"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2
