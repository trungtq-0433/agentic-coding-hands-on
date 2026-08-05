"""Tests for validate_db_catalog.py (Phase B gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_db_catalog import validate, main, _parse_catalog  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CATALOG = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header record | **Source:** `ddl/tables.sql:1` |
| ORDER_ITEMS | Line items per order | **Source:** `ddl/tables.sql:10` |
| CUSTOMERS | Customer master data | **Source:** `ddl/tables.sql:20` |

## Views

| Name | Purpose | Source |
|------|---------|--------|
| V_ORDER_SUMMARY | Aggregated order totals | **Source:** `ddl/views.sql:1` |

## Stored Procedures

| Name | Purpose | Source |
|------|---------|--------|
| SP_PROCESS_ORDER | Validates and commits an order | **Source:** `src/procs/orders.pks:1` |

## Sequences

| Name | Purpose | Source |
|------|---------|--------|
| SEQ_ORDER_ID | Auto-increment PK for ORDERS | **Source:** `ddl/sequences.sql:1` |

## Triggers

| Name | Purpose | Source |
|------|---------|--------|
| TRG_ORDERS_AUDIT | Audit log on ORDERS insert/update | **Source:** `ddl/triggers.sql:1` |
"""

DUPLICATE_NAME_SAME_KIND = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | First occurrence | **Source:** `ddl/tables.sql:1` |
| ORDERS | Duplicate! | **Source:** `ddl/tables.sql:5` |
"""

DUPLICATE_NAME_DIFF_KIND = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Table occurrence | **Source:** `ddl/tables.sql:1` |

## Views

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | View with same name — allowed (different kind) | **Source:** `ddl/views.sql:1` |
"""

MISSING_CITATION = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header | no citation here |
| CUSTOMERS | Customer data | **Source:** `ddl/tables.sql:10` |
"""

UNSAFE_IDENTIFIER = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header | **Source:** `ddl/tables.sql:1` |
| SHIP|MENT | Unescaped pipe in name produces extra column | **Source:** `ddl/tables.sql:5` |
"""

ESCAPED_IDENTIFIER = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header | **Source:** `ddl/tables.sql:1` |
"""

DATASET_CATALOG = """\
## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| CUSTFILE | Customer master flat file (VSAM KSDS) | **Source:** `src/CUSTMAST.cbl:42` |
| ORDFILE | Order transaction file (sequential) | **Source:** `src/ORDPROC.cbl:15` |
"""

MIXED_DATASET_TABLE_CATALOG = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| ORDERS | Order header record | **Source:** `ddl/tables.sql:1` |

## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| CUSTFILE | Customer master flat file (VSAM KSDS) | **Source:** `src/CUSTMAST.cbl:42` |
"""


# ---------------------------------------------------------------------------
# Plan setup helper
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, catalog_content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "db-objects.md").write_text(catalog_content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_catalog_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_CATALOG)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


def test_same_name_different_kind_passes(tmp_path):
    """Same name in two different kind sections is allowed."""
    plan = _setup_plan(tmp_path, DUPLICATE_NAME_DIFF_KIND)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_name_same_kind_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_NAME_SAME_KIND)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.duplicate_name" in rule_ids


def test_missing_citation_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.citation_missing" in rule_ids


def test_only_uncited_object_flagged(tmp_path):
    """Only the uncited row should be flagged, not the cited one."""
    plan = _setup_plan(tmp_path, MISSING_CITATION)
    result = validate(plan, tmp_path)
    citation_issues = [i for i in result["issues"]
                       if i["rule_id"] == "DbCatalog.citation_missing"]
    # ORDERS has no citation, CUSTOMERS does — only 1 issue
    assert len(citation_issues) == 1
    assert "ORDERS" in citation_issues[0]["message"]


def test_unsafe_identifier_fails(tmp_path):
    """Unescaped | in object name → critical."""
    plan = _setup_plan(tmp_path, UNSAFE_IDENTIFIER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.unsafe_identifier" in rule_ids


# ---------------------------------------------------------------------------
# Tests — Markdown safety (RT-F10)
# ---------------------------------------------------------------------------

def test_normal_identifier_no_unsafe_flag(tmp_path):
    """A clean object name must NOT trigger unsafe_identifier."""
    plan = _setup_plan(tmp_path, ESCAPED_IDENTIFIER)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.unsafe_identifier" not in rule_ids


# ---------------------------------------------------------------------------
# Tests — missing file
# ---------------------------------------------------------------------------

def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "DbCatalog.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — all valid kinds accepted
# ---------------------------------------------------------------------------

def test_all_valid_kinds_accepted(tmp_path):
    """table, view, procedure, sequence, trigger, package, function all accepted."""
    catalog = """\
## Tables

| Name | Purpose | Source |
|------|---------|--------|
| T1 | A table | **Source:** `ddl/t.sql:1` |

## Views

| Name | Purpose | Source |
|------|---------|--------|
| V1 | A view | **Source:** `ddl/v.sql:1` |

## Stored Procedures

| Name | Purpose | Source |
|------|---------|--------|
| P1 | A procedure | **Source:** `ddl/p.sql:1` |

## Sequences

| Name | Purpose | Source |
|------|---------|--------|
| S1 | A sequence | **Source:** `ddl/s.sql:1` |

## Triggers

| Name | Purpose | Source |
|------|---------|--------|
| TR1 | A trigger | **Source:** `ddl/tr.sql:1` |

## Packages

| Name | Purpose | Source |
|------|---------|--------|
| PKG1 | A package | **Source:** `ddl/pkg.sql:1` |

## Functions

| Name | Purpose | Source |
|------|---------|--------|
| FN1 | A function | **Source:** `ddl/fn.sql:1` |
"""
    plan = _setup_plan(tmp_path, catalog)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_CATALOG)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_critical_returns_1(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_NAME_SAME_KIND)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_CATALOG)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "db_catalog" in summary["validators"]
    assert summary["validators"]["db_catalog"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2


# ---------------------------------------------------------------------------
# Tests — Regression: empty file and missing separator row (critical fails)
# ---------------------------------------------------------------------------

def test_empty_catalog_fails_critical(tmp_path):
    """Regression: empty db-objects.md now fails (status=FAIL, critical) not PASS."""
    plan = _setup_plan(tmp_path, "")
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.empty" in rule_ids


def test_whitespace_only_catalog_fails_critical(tmp_path):
    """Regression: whitespace-only db-objects.md now fails (critical)."""
    plan = _setup_plan(tmp_path, "   \n  \n  ")
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.empty" in rule_ids


def test_section_without_separator_fails_critical(tmp_path):
    """Regression: section header and table rows with NO separator row now fails (critical)."""
    catalog = """\
## Tables

| Name | Purpose | Source |
| ORDERS | Order header | **Source:** `ddl/tables.sql:1` |
"""
    plan = _setup_plan(tmp_path, catalog)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.no_rows_parsed" in rule_ids


def test_well_formed_catalog_still_passes(tmp_path):
    """Regression guard: a catalog WITH separator row still PASSes."""
    plan = _setup_plan(tmp_path, VALID_CATALOG)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — Phase 06: dataset kind (COBOL flat-file/VSAM)
# ---------------------------------------------------------------------------

def test_datasets_heading_collects_rows_regression():
    """[Fix 8 regression guard] '## Datasets' MUST be present in SECTION_KIND_MAP so its
    rows are actually collected. Adding 'dataset' to VALID_KINDS alone is not enough: an
    unrecognized heading maps to cur_kind=None and _parse_catalog() silently drops every row
    under it (never flagged, never erroring) — this test proves that does NOT happen here.
    """
    objects, issues = _parse_catalog(DATASET_CATALOG.splitlines(), "docs/generated/db-objects.md")
    assert len(objects) == 2, (
        f"Datasets rows were silently dropped (fix 8 regression) — got {len(objects)} objects"
    )
    assert all(o["kind"] == "dataset" for o in objects)
    assert {o["name"] for o in objects} == {"CUSTFILE", "ORDFILE"}
    assert issues == []


def test_dataset_row_passes_validation(tmp_path):
    """A well-formed, cited dataset row under '## Datasets' passes validate() cleanly."""
    plan = _setup_plan(tmp_path, DATASET_CATALOG)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


def test_dataset_missing_citation_fails(tmp_path):
    """Dataset rows are held to the same citation contract as every other kind."""
    catalog = """\
## Datasets

| Name | Purpose | Source |
|------|---------|--------|
| CUSTFILE | Customer master flat file | no citation here |
"""
    plan = _setup_plan(tmp_path, catalog)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "DbCatalog.citation_missing" in rule_ids


def test_mixed_dataset_and_table_catalog_both_collected(tmp_path):
    """A catalog with BOTH '## Tables' and '## Datasets' sections collects both kinds."""
    objects, issues = _parse_catalog(MIXED_DATASET_TABLE_CATALOG.splitlines(),
                                      "docs/generated/db-objects.md")
    kinds = {o["kind"] for o in objects}
    assert kinds == {"table", "dataset"}
    assert issues == []

    plan = _setup_plan(tmp_path, MIXED_DATASET_TABLE_CATALOG)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0


def test_dataset_in_valid_kinds():
    """'dataset' must be a recognized kind (not just mapped from a heading)."""
    from validate_db_catalog import VALID_KINDS
    assert "dataset" in VALID_KINDS
