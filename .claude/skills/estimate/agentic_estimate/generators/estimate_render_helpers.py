"""Shared helpers for role-based estimate renderers (markdown + Excel)."""

from __future__ import annotations


def get_roles(data: dict) -> tuple[list[str], dict[str, str]]:
    """Extract active roles and display names from estimate data."""
    params = data.get("parameters", {})
    roles = params.get("active_roles", ["fe", "be", "qa_manual"])
    names = params.get("role_names", {})
    return roles, names


def role_display(slug: str, names: dict[str, str]) -> str:
    """Get display name for a role slug."""
    return names.get(slug, slug.upper())


def task_role_md(task: dict, role: str) -> int | None:
    """Get MD for a role from task's effort dict. None if role not present."""
    effort = task.get("effort", {})
    entry = effort.get(role)
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("md", 0)
    return 0


def role_md_cells(task: dict, roles: list[str]) -> list[str]:
    """Format role MD values for table display. '-' if role not present."""
    return [str(v) if (v := task_role_md(task, r)) is not None else "-" for r in roles]


def sum_role_md(tasks: list[dict], role: str) -> int:
    """Sum MD across tasks for a given role."""
    total = 0
    for t in tasks:
        md = task_role_md(t, role)
        if md is not None:
            total += md
    return total


def task_total_md(task: dict) -> int:
    """Get total_md from task, or compute from effort if missing."""
    if "total_md" in task:
        return task["total_md"]
    effort = task.get("effort", {})
    return sum(e.get("md", 0) for e in effort.values() if isinstance(e, dict))


def all_tasks_from_option(option: dict) -> list[dict]:
    """Extract all tasks from an option (categories or flat)."""
    tasks = []
    for cat in option.get("categories", []):
        tasks.extend(cat.get("tasks", []))
    tasks.extend(option.get("tasks", []))
    return tasks
