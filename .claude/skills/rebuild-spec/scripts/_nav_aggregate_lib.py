"""Aggregate (system-of-systems) system/ README renderer for rebuild-spec navigation.

Extracted from _nav_components_index.py to keep each file under 200 LOC.
Renders docs/<lang>/system/README.md in AGGREGATE_SYSTEM_ORDER (presence-pruned).
Stdlib only.

v16.0.0: dropped flat ## Files list; emits numbered reading-order table + role
reading-paths + components pointer (../../components/) + principles block via the
shared _nav_aggregate_render helpers (DRY with _nav_index._build_aggregate_index).
"""
from __future__ import annotations

import os

from _nav_aggregate_render import (
    components_pointer_row,
    principles_block,
    reading_order_rows,
    role_path_lines,
)
from _nav_lib import GEN_END, GEN_START, read_user_tail
from _nav_strings import AGGREGATE_ROLES, AGGREGATE_SYSTEM_ORDER, get_strings
from _nav_why_lib import build_why_clauses, load_json_file
from _system_synthesis_lib import sanitize_field


def _render_read_first(system_dir: str, ag: dict, meta: list | None = None) -> list[str]:
    """Render the reasoned "which service to read first + why" section (Phase 04, C1).

    Driven by the synthesis-written `.nav-metadata.json` side-channel. Absent / empty
    meta → empty list, so no dead section appears.

    Fix B (v23): when no cross-service edges were statically detected (all fan_in==0),
    the ranked rationale is noise — every line would read "called by 0". Instead, derive
    `no_deps` from the metadata rows (no schema change: fan_in already exists) and emit
    the no-deps intro + alphabetical list with ZERO per-service rationale lines. The stack
    name (if any row carries a non-empty "stack") is included as a parenthetical hint.

    meta: pre-loaded list from .nav-metadata.json (hoisted to avoid reading twice — DRY).
          When None, the function loads it itself for back-compat call sites.
    """
    if meta is None:
        meta_path = os.path.join(system_dir, ".nav-metadata.json")
        meta = load_json_file(meta_path)  # type: ignore[assignment]
    if not isinstance(meta, list) or not meta:
        return []
    heading = ag.get("read_first_heading", "Which service to read first")
    out: list[str] = ["", f"### {heading}", ""]

    # Fix B: derive no_deps from existing fan_in values — no schema change needed.
    no_deps = all(int(m.get("fan_in", 0)) == 0 for m in meta)

    if no_deps:
        # Determine stack hint from metadata rows (optional parenthetical).
        stacks = {sanitize_field(str(m.get("stack", ""))) for m in meta if m.get("stack")}
        stack_hint = f" ({', '.join(sorted(stacks))})" if stacks else ""
        intro_tpl = ag.get(
            "read_first_intro_no_deps",
            "Cross-service dependencies were not statically detected{stack_hint}. "
            "Services are listed alphabetically — reading order is not significant.",
        )
        intro = intro_tpl.format(stack_hint=stack_hint)
        out += [intro, ""]
        for rank, item in enumerate(
            sorted(meta, key=lambda m: str(m.get("service", ""))), start=1
        ):
            svc = sanitize_field(item.get("service", ""))
            out.append(f"{rank}. **{svc}**")
    else:
        intro = ag.get("read_first_intro", "")
        tpl = {
            "gateway": ag.get("rationale_gateway", "Entry point — {n} service(s) depend on it; start here."),
            "backend": ag.get("rationale_backend", "Backend service — called by {n}."),
            "frontend": ag.get("rationale_frontend", "Frontend / client — read after its backend services."),
            "reused": ag.get("rationale_reused", "Reused component — read after the services that consume it."),
        }
        if intro:
            out += [intro, ""]
        for item in sorted(meta, key=lambda m: m.get("rank", 0)):
            svc = sanitize_field(item.get("service", ""))  # render-time sanitize (project convention)
            key = str(item.get("rationale_key", "backend"))
            rationale = tpl.get(key, tpl["backend"]).format(n=item.get("fan_in", 0))
            out.append(f"{item.get('rank')}. **{svc}** — {rationale}")

    out.append("")
    return out


def build_aggregate_system_readme(
    system_dir: str,
    lang: str | None,
    timestamp: str,
    existing_content: str = "",
) -> str:
    """Render docs/<lang>/system/README.md for a system-of-systems layout.

    Emits (inside GEN_START/GEN_END):
      - title
      - intro line (why this order)
      - numbered reading-order table (bare links, e.g. overview.md)
      - role reading-paths (new_dev / reviewer / pm), absence-pruned
      - components reading-order pointer (../../components/README.md), omitted
        when no components index exists on disk (no dead links)
      - principles block

    Any user content below GEN_END is preserved verbatim (read_user_tail).

    system_dir: absolute path to the system-of-systems system/ directory.
    """
    s = get_strings(lang)
    ag = s.get("aggregate_index", {})
    ci = s.get("components_index", {})
    title = ci.get("system_readme_title", "System Documentation — Reading Order")
    intro = ag.get("intro", "")
    comps_ptr_label = ag.get("components_pointer_label", "All components")
    comps_ptr_desc = ag.get("components_pointer_desc", "Per-component documentation index")
    roles_heading = s.get("roles_heading", "Read by role")
    role_labels = s.get("role_labels", {})

    # Presence-prune: only files from AGGREGATE_SYSTEM_ORDER that exist on disk.
    present_files = [
        f for f in AGGREGATE_SYSTEM_ORDER
        if os.path.isfile(os.path.join(system_dir, f))
    ]
    present_nums = {i for i, f in enumerate(AGGREGATE_SYSTEM_ORDER, 1) if f in present_files}

    # Hoist nav-metadata load once — shared by why_clauses + _render_read_first (DRY).
    nav_meta: list | None = load_json_file(os.path.join(system_dir, ".nav-metadata.json"))
    if not isinstance(nav_meta, list):
        nav_meta = None

    # Build why_clauses: C-faithful (researcher .nav-why.json) > C-cheap (static strings).
    why_clauses = build_why_clauses(system_dir, s)

    lines = [
        f"# {title}", "",
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "",
    ]
    if intro:
        lines += [intro, ""]

    # Numbered reading-order table with causal why-read-here clauses.
    lines += reading_order_rows(present_files, "", s["col_headers"], why_clauses)

    # Reasoned "read this service first + why" section (Phase 04, C1) — from the
    # synthesis-written .nav-metadata.json. Pass pre-loaded meta to avoid re-reading.
    lines += _render_read_first(system_dir, ag, meta=nav_meta)

    # Components pointer from the system/ README. Two layouts (mirror _nav_index):
    #  - components at docs/components/ (sibling of the lang dir) → ../../components/
    #    from docs/<lang>/system/.
    #  - components at docs/<lang>/components/ (per-lang v15 flip) OR docs/components/ in
    #    single-lang (system_dir = docs/system/, parent = docs/) → ../components/.
    parent = os.path.dirname(system_dir.rstrip(os.sep))        # docs/<lang>/ (per-lang) or docs/ (single)
    grandparent = os.path.dirname(parent)                       # docs/ (per-lang) or repo-root (single)
    # Prefer the NEARER components dir. Checking grandparent first lets a stray repo-root
    # components/ (source code, common in FE repos) hijack the pointer in single-lang.
    # Nearer-first is correct for every layout: single-lang & per-lang-v15 → parent
    # (docs/components or docs/<lang>/components); per-lang-v14 (shared docs/components) → grandparent.
    if os.path.isdir(os.path.join(parent, "components")):
        comps_rel = "../components/"
    elif os.path.isdir(os.path.join(grandparent, "components")):
        comps_rel = "../../components/"
    else:
        comps_rel = None

    next_idx = len(present_files) + 1
    ptr_row = components_pointer_row(next_idx, comps_rel, comps_ptr_label, comps_ptr_desc)
    if ptr_row:
        lines.append(ptr_row)
    lines.append("")

    # Role reading-paths.
    lines += role_path_lines(present_nums, AGGREGATE_ROLES, role_labels, roles_heading)

    # Principles block.
    lines += principles_block(s.get("principles_label", "Principles"), s.get("principles", []))
    lines += ["", GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    result = "\n".join(lines) + user_tail
    return result if result.endswith("\n") else result + "\n"
