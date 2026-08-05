"""Tests for validate_screen_flow.py (Wave 6.875 gate)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_screen_flow import validate, main  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SCREEN_FLOW = """\
## Navigation Map

```
[Login] --> [Dashboard] --> [UserList]
                       \\--> [OrderList]
```

## Screen Access Paths

| Screen | Access Path | Auth Required |
|--------|-------------|---------------|
| SCR001_Login | /login | no |
| SCR002_Dashboard | /dashboard | yes |
| SCR003_UserList | /users | yes |

## Screen Transitions

### SCR001_Login

| From | To | Trigger | Condition |
|------|----|---------|-----------|
| SCR001_Login | SCR002_Dashboard | submit valid credentials | authenticated |

### SCR002_Dashboard

| From | To | Trigger | Condition |
|------|----|---------|-----------|
| SCR002_Dashboard | SCR003_UserList | click Users link | always |
"""

DUPLICATE_SCR_IN_TRANSITIONS = """\
## Navigation Map

Simple map.

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR003_Error | error |
"""

MISSING_NAV_MAP = """\
## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |
"""

MISSING_ACCESS_PATHS = """\
## Navigation Map

Simple map.

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |
"""

MISSING_TRANSITIONS = """\
## Navigation Map

Simple map.

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |
"""

MERGED_WITH_DUPLICATE_HEADER = """\
## Navigation Map

First fragment nav map.

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |

## Navigation Map

Second fragment nav map — duplicate from merge.

## Screen Transitions

### SCR002_Dashboard

| From | To | Trigger |
|------|----|---------|
| SCR002_Dashboard | SCR003_UserList | click |
"""

# Duplicate ## Screen Transitions with DISJOINT SCR codes (SCR001 vs SCR003) and a single
# Navigation Map. no_dup_scr_flow cannot see this (codes don't collide); only a per-section
# single_header guard catches it. This was a false PASS before the fix.
DUPLICATE_TRANSITIONS_DISJOINT_SCR = """\
## Navigation Map

Single nav map.

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |

## Screen Transitions

### SCR003_Settings

| From | To | Trigger |
|------|----|---------|
| SCR003_Settings | SCR004_Profile | click |
"""

# Duplicate ## Screen Access Paths (single Nav Map + single Transitions).
DUPLICATE_ACCESS_PATHS = """\
## Navigation Map

Single nav map.

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR001_Login | /login |

## Screen Transitions

### SCR001_Login

| From | To | Trigger |
|------|----|---------|
| SCR001_Login | SCR002_Dashboard | login |

## Screen Access Paths

| Screen | Access Path |
|--------|-------------|
| SCR003_Settings | /settings |
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_plan(tmp_path: Path, content: str) -> Path:
    plan = tmp_path / "test-plan"
    artifacts = plan / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "screen-flow.md").write_text(content, encoding="utf-8")
    return plan


# ---------------------------------------------------------------------------
# Tests — PASS
# ---------------------------------------------------------------------------

def test_valid_screen_flow_passes(tmp_path):
    plan = _setup_plan(tmp_path, VALID_SCREEN_FLOW)
    result = validate(plan, tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["critical"] == 0
    assert result["summary"]["warning"] == 0


# ---------------------------------------------------------------------------
# Tests — FAIL (critical)
# ---------------------------------------------------------------------------

def test_duplicate_scr_in_transitions_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_SCR_IN_TRANSITIONS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenFlow.no_dup_scr_flow" in rule_ids


def test_missing_nav_map_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_NAV_MAP)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenFlow.required_sections" in rule_ids


def test_missing_access_paths_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_ACCESS_PATHS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenFlow.required_sections" in rule_ids


def test_missing_transitions_fails(tmp_path):
    plan = _setup_plan(tmp_path, MISSING_TRANSITIONS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenFlow.required_sections" in rule_ids


def test_merged_with_duplicate_header_fails(tmp_path):
    """Fragment merge producing two ## Navigation Map sections must be caught."""
    plan = _setup_plan(tmp_path, MERGED_WITH_DUPLICATE_HEADER)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "critical"]
    assert "ScreenFlow.single_header" in rule_ids


def test_duplicate_transitions_disjoint_scr_fails(tmp_path):
    """Two ## Screen Transitions with non-overlapping SCR codes — caught by single_header,
    not no_dup_scr_flow. Was a false PASS before the per-section header guard."""
    plan = _setup_plan(tmp_path, DUPLICATE_TRANSITIONS_DISJOINT_SCR)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    crit = [i for i in result["issues"] if i["severity"] == "critical"]
    assert any(i["rule_id"] == "ScreenFlow.single_header"
               and "Screen Transitions" in i["message"] for i in crit)


def test_duplicate_access_paths_fails(tmp_path):
    plan = _setup_plan(tmp_path, DUPLICATE_ACCESS_PATHS)
    result = validate(plan, tmp_path)
    assert result["status"] == "FAIL"
    crit = [i for i in result["issues"] if i["severity"] == "critical"]
    assert any(i["rule_id"] == "ScreenFlow.single_header"
               and "Screen Access Paths" in i["message"] for i in crit)


# ---------------------------------------------------------------------------
# Tests — WARN
# ---------------------------------------------------------------------------

def test_missing_file_warns(tmp_path):
    plan = tmp_path / "test-plan"
    (plan / "artifacts").mkdir(parents=True)
    result = validate(plan, tmp_path)
    assert result["summary"]["critical"] == 0
    rule_ids = [i["rule_id"] for i in result["issues"] if i["severity"] == "warning"]
    assert "ScreenFlow.completed_missing" in rule_ids


# ---------------------------------------------------------------------------
# Tests — CLI / main()
# ---------------------------------------------------------------------------

def test_main_plan_dir_pass(tmp_path, capsys):
    plan = _setup_plan(tmp_path, VALID_SCREEN_FLOW)
    rc = main(["--plan-dir", str(plan), "--project-root", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "PASS"


def test_main_single_file_fail(tmp_path, capsys):
    plan = _setup_plan(tmp_path, DUPLICATE_SCR_IN_TRANSITIONS)
    sf_file = plan / "artifacts" / "screen-flow.md"
    rc = main(["--screen-flow-file", str(sf_file), "--project-root", str(tmp_path)])
    assert rc == 1


def test_main_summary_out(tmp_path):
    plan = _setup_plan(tmp_path, VALID_SCREEN_FLOW)
    summary_path = tmp_path / "validation-summary.json"
    rc = main([
        "--plan-dir", str(plan),
        "--project-root", str(tmp_path),
        "--summary-out", str(summary_path),
    ])
    assert rc == 0
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text())
    assert "screen_flow" in summary["validators"]
    assert summary["validators"]["screen_flow"]["status"] == "PASS"


def test_main_invalid_plan_dir(tmp_path, capsys):
    rc = main(["--plan-dir", str(tmp_path / "nonexistent"), "--project-root", str(tmp_path)])
    assert rc == 2
