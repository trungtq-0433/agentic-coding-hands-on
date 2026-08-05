"""Validation check functions for estimation JSON.

Each check returns a list of issue dicts with keys:
  check, severity ("error"|"warning"), message, and optionally id.
"""

import sys
from pathlib import Path

try:
    from agentic_estimate.generators.estimate_render_helpers import all_tasks_from_option
except ImportError:
    # Skill root is 2 levels up: scripts/ → estimate/
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from agentic_estimate.generators.estimate_render_helpers import all_tasks_from_option

SP_MD_RATIO = 0.5
SP_MD_TOLERANCE = 0.50
MAX_SP_PER_TASK = 13
MAX_TOTAL_SP = 500
MIN_BUFFER_PCT = 10
MIN_TESTING_PCT = 15


def _min_buffer(task: dict) -> int:
    effort = task.get("effort", {})
    buffers = [
        r.get("buffer_pct", 0) for r in effort.values() if isinstance(r, dict) and "buffer_pct" in r
    ]
    return min(buffers) if buffers else 0


def extract_tasks(data: dict) -> list[dict]:
    """Extract all tasks from both old (flat) and new (hierarchical) schemas."""
    if data.get("requirements"):
        return data["requirements"]
    tasks = []
    for opt in data.get("options", []):
        for t in all_tasks_from_option(opt):
            tasks.append(
                {
                    "id": t.get("id", "?"),
                    "title": t.get("name", "?"),
                    "story_points": t.get("story_points", 0),
                    "man_days": t.get("total_md", 0),
                    "effort": t.get("effort", {}),
                    "buffer_pct": _min_buffer(t),
                }
            )
    return tasks


def check_requirements_have_estimates(data: dict) -> list[dict]:
    issues = []
    for req in extract_tasks(data):
        missing = []
        if req.get("story_points") is None:
            missing.append("story_points")
        if not req.get("man_days"):
            missing.append("man_days")
        if missing:
            issues.append(
                {
                    "check": "requirement_estimates",
                    "severity": "error",
                    "id": req.get("id", "?"),
                    "message": f"{req.get('title', '?')} missing: {', '.join(missing)}",
                }
            )
    return issues


def check_sp_limit(data: dict) -> list[dict]:
    issues = []
    for req in extract_tasks(data):
        sp = req.get("story_points", 0)
        if sp and sp > MAX_SP_PER_TASK:
            issues.append(
                {
                    "check": "sp_limit",
                    "severity": "error",
                    "id": req.get("id", "?"),
                    "message": f"{req.get('title', '?')}: {sp} SP > {MAX_SP_PER_TASK} — must split",
                }
            )
    return issues


def check_buffer(data: dict) -> list[dict]:
    summary = data.get("summary", {})
    buffer = summary.get("buffer_percentage", 0)
    if not buffer:
        buffers = [_min_buffer(t) for t in extract_tasks(data) if _min_buffer(t)]
        if buffers and min(buffers) < MIN_BUFFER_PCT:
            return [
                {
                    "check": "buffer",
                    "severity": "error",
                    "message": f"Min buffer {min(buffers)}% < minimum {MIN_BUFFER_PCT}%",
                }
            ]
        return []
    if buffer < MIN_BUFFER_PCT:
        return [
            {
                "check": "buffer",
                "severity": "error",
                "message": f"Buffer {buffer}% < minimum {MIN_BUFFER_PCT}%",
            }
        ]
    return []


def check_sp_md_ratio(data: dict) -> list[dict]:
    """SP/Man-Days ratio ~0.5 (±50%). Skipped for multi-role estimates."""
    issues = []
    for req in extract_tasks(data):
        sp = req.get("story_points", 0)
        md = req.get("man_days", 0)
        if not sp or not md:
            continue

        effort = req.get("effort", {})
        if effort and isinstance(effort, dict):
            role_entries = [r for r in effort.values() if isinstance(r, dict) and "md" in r]
            if len(role_entries) > 1:
                continue
            role_mds = [r.get("md", 0) for r in role_entries]
            effective_md = role_mds[0] if role_mds else md
        else:
            effective_md = md

        ratio = sp / effective_md
        lo = SP_MD_RATIO * (1 - SP_MD_TOLERANCE)
        hi = SP_MD_RATIO * (1 + SP_MD_TOLERANCE)
        if ratio < lo or ratio > hi:
            issues.append(
                {
                    "check": "sp_md_ratio",
                    "severity": "warning",
                    "id": req.get("id", "?"),
                    "message": f"{req.get('title', '?')}: ratio {ratio:.2f} outside [{lo:.2f}, {hi:.2f}]",
                }
            )
    return issues


def check_total_sp(data: dict) -> list[dict]:
    tasks = extract_tasks(data)
    summary = data.get("summary", {})
    total = summary.get("total_story_points", 0)
    if not total:
        total = sum(t.get("story_points", 0) for t in tasks)
    if total > MAX_TOTAL_SP:
        return [
            {
                "check": "total_sp",
                "severity": "warning",
                "message": f"Total {total} SP > {MAX_TOTAL_SP} — consider splitting into phases",
            }
        ]
    return []


def check_assumptions(data: dict) -> list[dict]:
    assumptions = data.get("assumptions", [])
    if not assumptions:
        return [
            {
                "check": "assumptions",
                "severity": "warning",
                "message": "No assumptions documented",
            }
        ]
    return []


def check_testing_phase(data: dict) -> list[dict]:
    phases = data.get("phases", [])
    if not phases:
        return []

    dev_days = sum(p.get("man_days", 0) for p in phases if "develop" in p.get("name", "").lower())
    test_days = sum(p.get("man_days", 0) for p in phases if "test" in p.get("name", "").lower())

    if dev_days > 0 and test_days > 0:
        pct = (test_days / dev_days) * 100
        if pct < MIN_TESTING_PCT:
            return [
                {
                    "check": "testing_phase",
                    "severity": "warning",
                    "message": f"Testing {pct:.0f}% of dev time < minimum {MIN_TESTING_PCT}%",
                }
            ]
    return []


def check_role_consistency(data: dict) -> list[dict]:
    issues = []
    active = set(data.get("parameters", {}).get("active_roles", []))
    for task in extract_tasks(data):
        effort = task.get("effort", {})
        if not effort:
            issues.append(
                {
                    "check": "role_effort",
                    "severity": "error",
                    "id": task["id"],
                    "message": f"{task['title']}: effort object is empty",
                }
            )
            continue
        for role in effort:
            if active and role not in active:
                issues.append(
                    {
                        "check": "role_unknown",
                        "severity": "warning",
                        "id": task["id"],
                        "message": f"{task['title']}: role '{role}' not in active_roles",
                    }
                )
        computed = sum(r.get("md", 0) for r in effort.values() if isinstance(r, dict))
        declared = task.get("man_days", 0)
        if abs(computed - declared) > 1:
            issues.append(
                {
                    "check": "total_md_mismatch",
                    "severity": "error",
                    "id": task["id"],
                    "message": f"{task['title']}: total_md={declared} but sum of role mds={computed}",
                }
            )
    return issues


ALL_CHECKS = [
    check_requirements_have_estimates,
    check_sp_limit,
    check_buffer,
    check_sp_md_ratio,
    check_total_sp,
    check_assumptions,
    check_testing_phase,
    check_role_consistency,
]


def validate(data: dict, strict: bool = False) -> dict:
    """Run all validation checks and return result dict."""
    all_issues = []
    for check_fn in ALL_CHECKS:
        all_issues.extend(check_fn(data))

    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    passed = len(errors) == 0 if not strict else len(all_issues) == 0

    return {
        "passed": passed,
        "errors": len(errors),
        "warnings": len(warnings),
        "issues": all_issues,
    }
