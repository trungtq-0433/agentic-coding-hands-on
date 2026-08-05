"""Render breakdown JSON to overview markdown (L1 + L2 content)."""

from __future__ import annotations


def render(data: dict) -> str:
    level = data.get("breakdown_level", 2)
    lines = _header(data)

    for epic in data.get("epics", []):
        lines.extend(_render_epic(epic, data, level))

    return "\n".join(lines) + "\n"


def _header(data: dict) -> list[str]:
    source = data.get("source", "pre-estimate")
    md_label = f" | **Source**: {source}" if source else ""
    return [
        f"# Task Breakdown: {data['project_name']}",
        "",
        f"**Date**: {data.get('generated_date', '—')}{md_label} | **Level**: L{data.get('breakdown_level', 2)}",
        "",
        "---",
    ]


def _render_epic(epic: dict, data: dict, level: int) -> list[str]:
    stories = epic.get("stories", [])
    role_names = data.get("role_names", {})
    involved_roles = _epic_roles(epic, data.get("active_roles", []))
    roles_str = ", ".join(role_names.get(r, r.upper()) for r in involved_roles)

    md_str = ""
    if epic.get("total_md") is not None:
        md_str = f" | **{epic['total_md']} MD**"

    lines = [
        "",
        f"## {epic['id']}: {epic['name']}",
    ]

    if epic.get("description"):
        lines.append(epic["description"])

    story_count = len(stories)
    lines.append(f"Stories: {story_count} | Roles: {roles_str}{md_str}")

    if level >= 2 and stories:
        for story in stories:
            lines.extend(_render_story(story, data))

    return lines


def _render_story(story: dict, data: dict) -> list[str]:
    role_names = data.get("role_names", {})
    md_str = ""
    if story.get("total_md") is not None:
        md_str = f" ({story['total_md']} MD)"

    ref_str = ""
    if story.get("estimate_ref"):
        ref_str = f" *(ref: {story['estimate_ref']})*"

    lines = [
        "",
        f"### {story['id']}: {story['name']}{md_str}{ref_str}",
    ]

    tasks = story.get("tasks", [])
    if tasks:
        for task in tasks:
            role_display = role_names.get(task["role"], task["role"].upper())
            task_md = f" ({task['md']} MD)" if task.get("md") is not None else ""
            lines.append(f"- {role_display}: {task['name']}{task_md}")
    else:
        if story.get("description"):
            lines.append(story["description"])

    return lines


def _epic_roles(epic: dict, active_roles: list[str]) -> list[str]:
    found: set[str] = set()
    for story in epic.get("stories", []):
        for task in story.get("tasks", []):
            found.add(task.get("role", ""))
    if not found:
        return active_roles
    return [r for r in active_roles if r in found]
