# layout-exempt: rebuild-spec nav renderer — all docs/components paths here are this skill's own output targets
"""Components-index renderers for rebuild-spec navigation (Phase 03).

Two renderers that follow the same structure-vs-prose split as _nav_index:
  - build_components_index_readme: docs/components/README.md — module table
    in reading-order (gateway → backend → frontend → fullstack → reused).
  - build_component_system_readme: docs/components/<c>/system/README.md —
    fixed reading order overview → architecture → business-rules → permissions
    (presence-pruned). Both are 2-zone (GEN_START/GEN_END), stdlib-only.

Role-rank table is lang-independent (numbers/ordering); prose labels come from
the components_index block added to all three _nav_strings_<lang> modules.
I/O wiring (load_component_meta, write_components_index) lives in _nav_components_io.py.
Aggregate system/ renderer lives in _nav_aggregate_lib.py.
"""
from __future__ import annotations

import os

from _nav_lib import GEN_END, GEN_START, file_description, read_user_tail
from _nav_strings import get_strings

# ---------------------------------------------------------------------------
# Role-rank table (lang-independent — structure, not prose)
# ---------------------------------------------------------------------------

# Base rank by normalized role string. Lower = earlier in reading order.
_ROLE_BASE_RANK: dict[str, int] = {
    "gateway": 0,
    "api-gateway": 0,
    "api_gateway": 0,
    "backend": 1,
    "service": 1,
    "frontend": 2,
    "fullstack": 3,
}

# Reused components sort after fresh peers at the same rank (+10 offset).
_REUSED_RANK_OFFSET = 10


def _role_rank(role: str, reused: bool) -> int:
    """Return the sort key for a component given its role and reused flag."""
    normalized = (role or "").lower().replace(" ", "-")
    base = _ROLE_BASE_RANK.get(normalized, 1)  # unknown → backend/service default
    return base + (_REUSED_RANK_OFFSET if reused else 0)


def _sort_components(components_meta: list[dict]) -> list[dict]:
    """Return components sorted by (role_rank, name).

    components_meta is a list of dicts: {name, role, reused, primary_lang, ...}.
    """
    return sorted(
        components_meta,
        key=lambda c: (_role_rank(c.get("role", ""), bool(c.get("reused"))), c.get("name", ""))
    )


# ---------------------------------------------------------------------------
# System-dir reading order (presence-pruned, fixed sequence)
# ---------------------------------------------------------------------------

_SYSTEM_READING_ORDER = [
    "overview.md",
    "architecture.md",
    "business-rules.md",
    "permissions.md",
]


def _system_files_present(system_dir: str) -> list[str]:
    """Return those files from _SYSTEM_READING_ORDER that exist on disk."""
    result = []
    for fname in _SYSTEM_READING_ORDER:
        if os.path.isfile(os.path.join(system_dir, fname)):
            result.append(fname)
    return result


# ---------------------------------------------------------------------------
# Renderer 1 — docs/components/README.md (components index)
# ---------------------------------------------------------------------------

def build_components_index_readme(
    components_root: str,
    components_meta: list[dict],
    lang: str | None,
    timestamp: str,
    existing_content: str = "",
) -> str:
    """Render docs/components/README.md — module table in reading order.

    components_root: absolute path to docs/components/
    components_meta: list of {name, role, reused, primary_lang} per component
    lang/timestamp: locale and generation time
    existing_content: current file content for 2-zone tail preservation
    """
    s = get_strings(lang)
    ci = s.get("components_index", {})

    title = ci.get("title", "Components Index")
    intro = ci.get("intro", "")
    col_num = ci.get("col_num", "#")
    col_module = ci.get("col_module", "Module")
    col_role = ci.get("col_role", "Role")
    role_labels: dict[str, str] = ci.get("role_labels", {})
    reused_marker = ci.get("reused_marker", "(reused)")

    sorted_meta = _sort_components(components_meta)

    lines = [
        f"# {title}", "",
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "",
    ]
    if intro:
        lines += [intro, ""]

    if sorted_meta:
        lines += [f"| {col_num} | {col_module} | {col_role} |", "|---|---|---|"]
        for idx, comp in enumerate(sorted_meta, start=1):
            name = comp.get("name", "")
            role = comp.get("role", "")
            reused = bool(comp.get("reused"))
            role_label = role_labels.get(role, role_labels.get(
                role.replace("-", "_"), role_labels.get(
                    role.replace("_", "-"), role)))
            # Escape link-text brackets so a component dir name containing [ or ] cannot
            # break the Markdown link/table cell.
            display_name = name.replace("[", "\\[").replace("]", "\\]")
            if reused:
                display_name = f"{display_name} {reused_marker}"
            # Index lives at docs/components/README.md → link is relative to it
            link = f"{name}/README.md"
            lines.append(f"| {idx} | [{display_name}]({link}) | {role_label} |")
        lines.append("")
    else:
        lines.append("_(no components found)_")
        lines.append("")

    lines += [GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    idx_content = "\n".join(lines) + user_tail
    return idx_content if idx_content.endswith("\n") else idx_content + "\n"


# ---------------------------------------------------------------------------
# Renderer 2 — docs/components/<c>/system/README.md (component system index)
# ---------------------------------------------------------------------------

def build_component_system_readme(
    system_dir: str,
    lang: str | None,
    timestamp: str,
    existing_content: str = "",
) -> str:
    """Render docs/components/<c>/system/README.md in fixed reading order.

    Presence-pruned: only files that exist on disk are listed.
    system_dir: absolute path to the component's system/ directory.
    """
    s = get_strings(lang)
    ci = s.get("components_index", {})
    sys_title = ci.get("system_readme_title", "System Documentation — Reading Order")

    present = _system_files_present(system_dir)

    lines = [
        f"# {sys_title}", "",
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "",
        "## Files", "",
    ]
    if present:
        for fname in present:
            lines.append(f"- [{fname}]({fname}) — {file_description(fname)}")
    else:
        lines.append("_(no system documentation files found)_")
    lines += ["", GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    sys_content = "\n".join(lines) + user_tail
    return sys_content if sys_content.endswith("\n") else sys_content + "\n"

