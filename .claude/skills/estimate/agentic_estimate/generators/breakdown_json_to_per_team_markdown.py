"""Render breakdown JSON to per-team markdown files (L2 story list, L3 tasks + AC)."""

from __future__ import annotations


def render(data: dict) -> dict[str, str]:
    """Return {role_slug: markdown_content} for each active role with tasks."""
    active_roles = data.get("active_roles", [])
    role_names = data.get("role_names", {})
    level = data.get("breakdown_level", 3)
    result: dict[str, str] = {}

    for role in active_roles:
        content = _render_role(data, role, role_names, level)
        if content:
            result[role] = content

    return result


def _render_role(data: dict, role: str, role_names: dict, level: int) -> str | None:
    display_name = role_names.get(role, role.upper())
    epics_content: list[str] = []
    total_md = 0
    has_tasks = False

    for epic in data.get("epics", []):
        epic_lines, epic_md, epic_has = _render_epic_for_role(epic, role, role_names, level)
        if epic_has:
            epics_content.extend(epic_lines)
            total_md += epic_md
            has_tasks = True

    if not has_tasks:
        return None

    is_pre = data.get("source") == "pre-estimate"
    md_label = "TBD" if is_pre else f"{total_md} MD"

    lines = [
        f"# {display_name} Tasks: {data['project_name']}",
        "",
        f"**Date**: {data.get('generated_date', '—')} | **Total**: {md_label}",
        "",
        "---",
    ]
    lines.extend(epics_content)

    return "\n".join(lines) + "\n"


def _render_epic_for_role(
    epic: dict, role: str, role_names: dict, level: int
) -> tuple[list[str], int, bool]:
    lines: list[str] = []
    epic_md = 0
    has_tasks = False

    for story in epic.get("stories", []):
        story_lines, story_md, story_has = _render_story_for_role(story, role, role_names, level)
        if story_has:
            if not has_tasks:
                lines.append("")
                lines.append(f"## {epic['id']}: {epic['name']}")
            lines.extend(story_lines)
            epic_md += story_md
            has_tasks = True

    return lines, epic_md, has_tasks


def _render_story_for_role(
    story: dict, role: str, role_names: dict, level: int
) -> tuple[list[str], int, bool]:
    tasks = [t for t in story.get("tasks", []) if t.get("role") == role]
    if not tasks:
        return [], 0, False

    story_md = sum(t.get("md") or 0 for t in tasks)
    md_str = f" ({story_md} MD)" if any(t.get("md") is not None for t in tasks) else ""

    lines = [
        "",
        f"### {story['id']}: {story['name']}{md_str}",
    ]

    if level >= 3:
        for task in tasks:
            lines.extend(_render_task(task))
    else:
        for task in tasks:
            task_md = f" ({task['md']} MD)" if task.get("md") is not None else ""
            lines.append(f"- {task['name']}{task_md}")

    return lines, story_md, True


def _render_task(task: dict) -> list[str]:
    md_str = f" ({task['md']} MD)" if task.get("md") is not None else ""
    lines = [
        "",
        f"#### {task['id']}: {task['name']}{md_str}",
    ]

    if task.get("description"):
        lines.append(task["description"])

    checklist = task.get("checklist", [])
    if checklist:
        lines.append("")
        for item in checklist:
            lines.append(f"- [ ] {item}")

    ac = task.get("acceptance_criteria", [])
    if ac:
        lines.append("")
        lines.append("**AC:**")
        for item in ac:
            lines.append(f"- {item}")

    return lines
