"""Tests for validate_crud_matrix.py (Phase B gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_crud_matrix import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

VALID_MATRIX = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS | ✓ | ✓ |   |   | id, total | **Source:** `src/Orders.pas:42` |
| ORDER_ITEMS |   | ✓ |   |   | id, order_id | **Source:** `src/Orders.pas:87` |

## Feature: F002 Customers

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| CUSTOMERS | ✓ | ✓ | ✓ |   | id, name | **Source:** `src/Customers.pas:15` |

## Cross-Module Tables

| Table | Features | Operations | Source |
|-------|----------|------------|--------|
| ORDERS | F001, F002 | C, R | **Source:** `src/Orders.pas:42` |
"""

MISSING_CITATION = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS | ✓ | ✓ |   |   | id, total | no citation here |
| ORDER_ITEMS |   | ✓ |   |   | id | **Source:** `src/Orders.pas:87` |
"""

INVALID_OP_TOKEN = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS | X | ✓ |   |   | id | **Source:** `src/Orders.pas:42` |
"""

PIPE_IN_TABLE_NAME = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS\\|EXTRA | ✓ |   |   |   | id | **Source:** `src/Orders.pas:1` |
"""

PIPE_UNESCAPED_IN_NAME = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS | ✓ |   |   |   | id | **Source:** `src/Orders.pas:1` |
"""

DYNAMIC_SQL_DIGEST = {
    "extractor": "extract_data_flow",
    "generated_at": "2026-06-22T09:00:00Z",
    "source_tree_hash": "abc123",
    "units": [
        {
            "path": "src/DynamicReport.pas",
            "uses": [],
            "db_ops": [],
            "forms": [],
            "parse_coverage": {
                "static_sql_found": 0,
                "dynamic_sql_detected": True,
                "confidence": "low",
            },
        }
    ],
    "db_objects": [],
    "warnings": [],
}

DYNAMIC_SQL_WITH_OPS_DIGEST = {
    "extractor": "extract_data_flow",
    "generated_at": "2026-06-22T09:00:00Z",
    "source_tree_hash": "abc123",
    "units": [
        {
            "path": "src/DynamicReport.pas",
            "uses": [],
            "db_ops": [
                {"table": "ORDERS", "op": "R", "columns": ["id"], "line": 10,
                 "citation": "src/DynamicReport.pas:10", "confidence": "low"},
            ],
            "forms": [],
            "parse_coverage": {
                "static_sql_found": 0,
                "dynamic_sql_detected": True,
                "confidence": "low",
            },
        }
    ],
    "db_objects": [],
    "warnings": [],
}

DB_OBJECTS_MD = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header | **Source:** `ddl/tables.sql:1` |
| ORDER_ITEMS | Line items | **Source:** `ddl/tables.sql:10` |
| CUSTOMERS | Customer master | **Source:** `ddl/tables.sql:20` |
"""

DATASET_MATRIX = """\
## Feature: F001 Customer Maintenance

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| CUSTFILE | ✓ | ✓ | ✓ |   | cust-id, cust-name | **Source:** `src/CUSTMAST.cbl:88` |
"""

DATASET_DB_OBJECTS_MD = """\
## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| CUSTFILE | Customer master flat file (VSAM KSDS) | **Source:** `src/CUSTMAST.cbl:42` |
"""

MIXED_DATASET_TABLE_MATRIX = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| ORDERS | ✓ | ✓ |   |   | id, total | **Source:** `src/Orders.pas:42` |
| CUSTFILE | ✓ | ✓ | ✓ |   | cust-id | **Source:** `src/CUSTMAST.cbl:88` |
"""

MIXED_DATASET_TABLE_DB_OBJECTS_MD = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header | **Source:** `ddl/tables.sql:1` |

## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| CUSTFILE | Customer master flat file (VSAM KSDS) | **Source:** `src/CUSTMAST.cbl:42` |
"""


# ---------------------------------------------------------------------------
# Plan setup helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, matrix_content: str,
                db_objects_content: str | None = None,
                digest: dict | None = None) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "crud-matrix.md").write_text(matrix_content, encoding="utf-8")

    if db_objects_content is not None:
        docs = tmp_path / "docs" / "generated"
        docs.mkdir(parents=True)
        (docs / "db-objects.md").write_text(db_objects_content, encoding="utf-8")

    if digest is not None:
        (artifacts / "_digest_extract_data_flow.json").write_text(
            json.dumps(digest), encoding="utf-8"
        )

    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_matrix_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_MATRIX, db_objects_content=DB_OBJECTS_MD)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


def test_valid_matrix_no_cross_ref_files_passes(tmp_path):
    """Without db-objects.md or data-model, cross-ref check is skipped (no critical)."""
    plan = _setup_plan(tmp_path, VALID_MATRIX)
    result = validate(plan, tmp_path)
    # No critical issues — cross-ref downgraded when no reference files present
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_missing_citation_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.citation_missing" in rule_ids


def test_invalid_op_token_fails(tmp_path):
    """Op token 'X' is not in {C, R, U, D, ✓, ✗, -, empty}."""
    plan = _setup_plan(tmp_path, INVALID_OP_TOKEN)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.invalid_op_token" in rule_ids


# ---------------------------------------------------------------------------
# Tests — cross-ref
# ---------------------------------------------------------------------------

def test_table_present_in_db_objects_passes(tmp_path):
    """Table referenced in matrix exists in db-objects.md → no cross-ref warning."""
    plan = _setup_plan(tmp_path, VALID_MATRIX, db_objects_content=DB_OBJECTS_MD)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.table_unknown" not in warn_ids


def test_table_absent_from_both_ref_files_warns(tmp_path):
    """Table not in db-objects.md nor data-model → WARN (not critical)."""
    matrix = """\
## Feature: F001 Foo

| Table | C | R | U | D | Columns | Source |
|-------|---|---|---|---|---------|--------|
| UNKNOWN_TABLE | ✓ |   |   |   | id | **Source:** `src/Foo.pas:1` |
"""
    db_objs = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| OTHER_TABLE | Something | **Source:** `ddl/tables.sql:1` |
"""
    plan = _setup_plan(tmp_path, matrix, db_objects_content=db_objs)
    result = validate(plan, tmp_path)
    # Must be WARN not FAIL
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.table_unknown" in warn_ids


# ---------------------------------------------------------------------------
# Tests — Markdown safety (RT-F10)
# ---------------------------------------------------------------------------

def test_escaped_pipe_in_table_name_does_not_break_columns(tmp_path):
    """An escaped \\| in table name is valid — validator must not miscount columns."""
    plan = _setup_plan(tmp_path, PIPE_IN_TABLE_NAME)
    result = validate(plan, tmp_path)
    # Should not produce column_drift critical for escaped pipe
    crit_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.column_drift" not in crit_ids


# ---------------------------------------------------------------------------
# Tests — RT-F8 dynamic SQL WARN
# ---------------------------------------------------------------------------

def test_dynamic_sql_unit_zero_crud_warns(tmp_path):
    """Unit with dynamic_sql_detected:true and 0 CRUD entries → WARN."""
    # Matrix has no rows for DynamicReport.pas, digest has it as dynamic with 0 ops
    plan = _setup_plan(tmp_path, VALID_MATRIX, digest=DYNAMIC_SQL_DIGEST)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.dynamic_sql_no_crud" in warn_ids


def test_dynamic_sql_unit_with_ops_no_warn(tmp_path):
    """Unit with dynamic_sql_detected:true BUT has db_ops → no RT-F8 WARN."""
    plan = _setup_plan(tmp_path, VALID_MATRIX, digest=DYNAMIC_SQL_WITH_OPS_DIGEST)
    result = validate(plan, tmp_path)
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.dynamic_sql_no_crud" not in warn_ids


def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_MATRIX, db_objects_content=DB_OBJECTS_MD)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_critical_returns_1(tmp_path, capsys):
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_MATRIX)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "crud_matrix" in summary["validators"]
    assert summary["validators"]["crud_matrix"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2


# ---------------------------------------------------------------------------
# Tests — Regression: empty file and missing separator row (critical fails)
# ---------------------------------------------------------------------------

def test_empty_file_fails_critical(tmp_path):
    """Regression: empty crud-matrix.md now fails (status=FAIL, critical) not PASS."""
    plan = _setup_plan(tmp_path, "")
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.empty" in rule_ids


def test_whitespace_only_file_fails_critical(tmp_path):
    """Regression: whitespace-only crud-matrix.md now fails (critical)."""
    plan = _setup_plan(tmp_path, "   \n  \n  ")
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.empty" in rule_ids


def test_pipe_table_without_separator_fails_critical(tmp_path):
    """Regression: table-like content with NO separator row now fails (critical)."""
    matrix = """\
## Feature: F001 Orders

| Table | C | R | U | D | Columns | Source |
| ORDERS | ✓ | ✓ |   |   | id, total | **Source:** `src/Orders.pas:42` |
"""
    plan = _setup_plan(tmp_path, matrix)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "CrudMatrix.no_rows_parsed" in rule_ids


def test_well_formed_matrix_still_passes(tmp_path):
    """Regression guard: a matrix WITH separator row still PASSes."""
    plan = _setup_plan(tmp_path, VALID_MATRIX, db_objects_content=DB_OBJECTS_MD)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — Phase 06: dataset-kind cross-ref
# ---------------------------------------------------------------------------

def test_crud_cell_referencing_dataset_cross_references(tmp_path):
    """A CRUD cell whose 'table' is actually a dataset object (cataloged under
    '## Datasets' in db-objects.md) must cross-reference cleanly — no table_unknown warn."""
    plan = _setup_plan(tmp_path, DATASET_MATRIX, db_objects_content=DATASET_DB_OBJECTS_MD)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.table_unknown" not in warn_ids


def test_crud_matrix_mixed_dataset_and_table_both_cross_reference(tmp_path):
    """A matrix mixing a table row and a dataset row, cross-referenced against a
    db-objects.md that catalogs both kinds — neither is flagged unknown."""
    plan = _setup_plan(tmp_path, MIXED_DATASET_TABLE_MATRIX,
                       db_objects_content=MIXED_DATASET_TABLE_DB_OBJECTS_MD)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    warn_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "CrudMatrix.table_unknown" not in warn_ids
