"""Tests for validate_screen_list.py — wildcard/composite SCR guard (Phase 02).

Covers:
- Wildcard in table row Path column → FAIL ScreenList.no_wildcard_route
- Wildcard in Routes/URLs bullet line → FAIL ScreenList.no_wildcard_route
- :splat pattern → FAIL
- /... (Remix splat) → FAIL
- Double-star /** → FAIL
- Mid-path wildcard /admin/*/settings → FAIL (A1)
- Trailing wildcard /admin/* → FAIL (A1)
- :id param /admin/:id → PASS (A1, not a wildcard)
- Valid multi-file screen list (concrete routes only) → PASS
- Description prose containing '*' does NOT false-fire
- Asterisk inside a word (e.g. "admin*") does NOT false-fire
"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_screen_list import validate  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Wildcard in Screen Index table Path column (researcher-01 §3 WILDCARD_COMPOSITE_SCREEN fixture)
WILDCARD_IN_INDEX_TABLE = """\
## Screen Index

| SCR### | Name | Path Pattern |
|--------|------|-------------|
| SCR001 | Admin System | /admin/system/* |

## SCR001

**Type**: composite

### Routes/URLs

- /admin/system/dashboard
"""

# Wildcard in Routes/URLs bullet inside SCR body
WILDCARD_IN_ROUTE_BULLET = """\
## Screen Index

| SCR### | Name |
|--------|------|
| SCR001 | Admin System |

## SCR001

**Type**: composite

### Routes/URLs

- /admin/*
"""

# :splat pattern in table row
SPLAT_IN_TABLE = """\
## Screen Index

| SCR### | Name | Path |
|--------|------|------|
| SCR001 | Catch-all | /:splat |

## SCR001

### Routes/URLs

- /:splat
"""

# /... Remix splat in route bullet
REMIX_SPLAT_IN_BULLET = """\
## Screen Index

| SCR### | Name |
|--------|------|
| SCR001 | Remix Splat |

## SCR001

### Routes/URLs

- /admin/...
"""

# Double-star wildcard /** in table
DOUBLE_STAR_IN_TABLE = """\
## Screen Index

| SCR### | Name | Route |
|--------|------|-------|
| SCR001 | Deep Wildcard | /api/** |

## SCR001

### Routes/URLs

- /api/**
"""

# Valid multi-file screen list: only concrete routes, no wildcards
VALID_MULTI_SCREEN = """\
## Screen Index

| SCR### | Name | Route |
|--------|------|-------|
| SCR001 | Admin Users | /admin/users |
| SCR002 | Admin Settings | /admin/settings |
| SCR003 | Admin Logs | /admin/logs |

## SCR001

**Type**: atomic

### Routes/URLs

- /admin/users

## SCR002

**Type**: atomic

### Routes/URLs

- /admin/settings

## SCR003

**Type**: atomic

### Routes/URLs

- /admin/logs
"""

# Description prose containing '*' — must NOT fire no_wildcard_route
PROSE_WITH_ASTERISK = """\
## Screen Index

| SCR### | Name |
|--------|------|
| SCR001 | Dashboard |

## SCR001

**Type**: composite

### Description

This screen displays metrics. Data is loaded via /api/metrics endpoints.
Note: fields marked with * are required.

### Routes/URLs

- /dashboard
"""

# Asterisk inside a word (e.g. admin*) in a description line — must NOT fire
WORD_WITH_ASTERISK_PROSE = """\
## Screen Index

| SCR### | Name |
|--------|------|
| SCR001 | Login |

## SCR001

### Description

Bold **text** and admin* references do not count as wildcards.

### Routes/URLs

- /login
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    (plan / "artifacts" / "screen-list.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — FAIL: wildcard patterns trigger ScreenList.no_wildcard_route
# ---------------------------------------------------------------------------

def test_wildcard_in_index_table_fails(tmp_path):
    """Single-star wildcard in Screen Index table column → critical."""
    plan = _setup_plan(tmp_path, WILDCARD_IN_INDEX_TABLE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_wildcard_in_route_bullet_fails(tmp_path):
    """Single-star wildcard in Routes/URLs bullet inside SCR body → critical."""
    plan = _setup_plan(tmp_path, WILDCARD_IN_ROUTE_BULLET)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_splat_in_table_fails(tmp_path):
    """:splat pattern in table row → critical."""
    plan = _setup_plan(tmp_path, SPLAT_IN_TABLE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_remix_splat_in_bullet_fails(tmp_path):
    """/... Remix splat in route bullet → critical."""
    plan = _setup_plan(tmp_path, REMIX_SPLAT_IN_BULLET)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_double_star_in_table_fails(tmp_path):
    """Double-star wildcard /** in table → critical."""
    plan = _setup_plan(tmp_path, DOUBLE_STAR_IN_TABLE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


# ---------------------------------------------------------------------------
# Tests — PASS: valid multi-file screen list
# ---------------------------------------------------------------------------

def test_valid_multi_screen_passes(tmp_path):
    """Concrete routes only (no wildcards) → PASS."""
    plan = _setup_plan(tmp_path, VALID_MULTI_SCREEN)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS", result["issues"]
    assert result["summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# Tests — no false positive: prose containing '*' must not fire
# ---------------------------------------------------------------------------

def test_prose_asterisk_no_false_fire(tmp_path):
    """Description prose with '* are required' note must NOT trigger no_wildcard_route."""
    plan = _setup_plan(tmp_path, PROSE_WITH_ASTERISK)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids


def test_word_asterisk_no_false_fire(tmp_path):
    """Asterisk inside a word (admin*) in description prose must NOT trigger no_wildcard_route."""
    plan = _setup_plan(tmp_path, WORD_WITH_ASTERISK_PROSE)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids


# ---------------------------------------------------------------------------
# Tests — A1: mid-path and trailing wildcards, :id params (not wildcards)
# ---------------------------------------------------------------------------

MID_PATH_WILDCARD_IN_TABLE = """\
## Screen Index

| SCR### | Name | Path |
|--------|------|------|
| SCR001 | Admin Settings | /admin/*/settings |

## SCR001

### Routes/URLs

- /admin/*/settings
"""

ID_PARAM_IN_TABLE = """\
## Screen Index

| SCR### | Name | Path |
|--------|------|------|
| SCR001 | Admin Detail | /admin/:id |

## SCR001

### Routes/URLs

- /admin/:id
"""


def test_mid_path_wildcard_in_table_fails(tmp_path):
    """A1: mid-path wildcard /admin/*/settings in table → critical."""
    plan = _setup_plan(tmp_path, MID_PATH_WILDCARD_IN_TABLE)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_trailing_wildcard_still_fails(tmp_path):
    """A1: trailing /admin/* still fires — regression guard."""
    plan = _setup_plan(tmp_path, WILDCARD_IN_ROUTE_BULLET)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL", result["issues"]
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenList.no_wildcard_route" in rule_ids


def test_id_param_no_false_fire(tmp_path):
    """A1: :id named param /admin/:id must NOT trigger no_wildcard_route."""
    plan = _setup_plan(tmp_path, ID_PARAM_IN_TABLE)
    result = validate(plan, tmp_path)
    rule_ids = [i["rule_id"] for i in result["issues"]]
    assert "ScreenList.no_wildcard_route" not in rule_ids
