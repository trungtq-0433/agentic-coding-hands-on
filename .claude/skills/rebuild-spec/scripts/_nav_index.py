# layout-exempt: rebuild-spec nav renderer — all docs/components paths here are this skill's own output targets or descriptive comments
"""Top-level reading-order docs/README.md renderer (rebuild-spec v16.0.0).

Handles the top-level reading-order index and (in per-lang mode) the root pointer.
Imports the shared 2-zone primitives from _nav_lib. Structure + prose come from
_nav_strings / _nav_strings_<lang>. Deterministic, stdlib only.

v14.1.0: detects aggregate root (system-of-systems layout) and renders an AGGREGATE
reading order instead of the single-component READING_ORDER. Non-aggregate path is
byte-identical. v16.0.0: aggregate signal is system/component-catalog.md (the unique
aggregate artifact; architecture.md is shared with single-component layouts).
v16.0.0: _build_aggregate_index uses shared helpers from _nav_aggregate_render
(DRY); adds role-paths to aggregate README; utility functions moved to
_nav_aggregate_render to keep this file under 200 LOC.
"""
from __future__ import annotations

import os

from _nav_aggregate_render import (
    entry_present,
    is_bare_docs_root,               # re-exported: callers import from _nav_index
    principles_block,
    read_primary_lang_from_state,    # re-exported: callers import from _nav_index
    resolve_root_readme_removal,     # re-exported: callers import from _nav_index
    role_path_lines,
)
from _nav_feature_lib import relationship_legend
from _nav_lib import GEN_END, GEN_START, read_user_tail
from _nav_strings import (
    AGGREGATE_SYSTEM_ORDER,
    QUICK_PATH,
    READING_ORDER,
    ROLES,
    get_strings,
)


def _is_aggregate_root(docs_root: str) -> bool:
    """Return True when docs_root is the aggregate (system-of-systems) layout.

    Detection (v16 parity names): presence of system/component-catalog.md.
    This is the unique aggregate signal — it never appears in a single-component
    layout (system/architecture.md is shared with single-component and cannot be
    used alone). New names only — no legacy aggregate repos (Validation S1).
    """
    sys_dir = os.path.join(docs_root, "system")
    return os.path.isfile(os.path.join(sys_dir, "component-catalog.md"))


def _build_aggregate_index(docs_root: str, lang: str | None, timestamp: str,
                            existing_content: str = "") -> str:
    """Render docs/README.md for a system-of-systems (aggregate) layout.

    Phase 04 C2: a THIN pointer — it links to system/README.md (which owns the numbered
    reading-order table + role-paths) plus a components-index pointer and the principles
    block. It no longer duplicates the artifact table or role-paths.
    """
    s = get_strings(lang)
    ag = s.get("aggregate_index", {})
    title = ag.get("title", "System of Systems — Reading Order")
    intro = ag.get("intro", "")
    comps_ptr_label = ag.get("components_pointer_label", "All components")
    comps_ptr_desc = ag.get("components_pointer_desc", "Per-component documentation index")

    sys_dir = os.path.join(docs_root, "system")
    present_files = [
        f for f in AGGREGATE_SYSTEM_ORDER
        if os.path.isfile(os.path.join(sys_dir, f))
    ]

    lines = [
        f"# {title}", "",
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "",
    ]
    if intro:
        lines += [intro, ""]

    # Thin pointer to the full reading order (Phase 04, C2). The numbered system table +
    # role-paths live in system/README.md; the parent README only points there so the two
    # files no longer duplicate the same table. Role-paths are intentionally NOT repeated
    # here — they reference the numbered table that now lives only in system/README.md.
    if present_files:
        pointer = ag.get("parent_pointer",
                         "Full reading order: [system/README.md](system/README.md).")
        lines += [pointer, ""]

    # Components index pointer as a plain line (the parent README is a thin pointer now,
    # so there is no reading-order table to host a table row — Phase 04, C2). Prefer the
    # NEARER components dir: checking the parent first lets a stray repo-root components/
    # (source code) hijack the pointer in single-lang (docs_root = docs/). Nearer-first
    # holds for every layout: single-lang & per-lang-v15 → docs_root/components;
    # per-lang-v14 (shared docs/components) → parent.
    parent = os.path.dirname(docs_root.rstrip(os.sep))
    if os.path.isdir(os.path.join(docs_root, "components")):
        comps_rel = "components/"
    elif os.path.isdir(os.path.join(parent, "components")):
        comps_rel = "../components/"
    else:
        comps_rel = None
    if comps_rel:
        lines += [f"- [{comps_ptr_label}]({comps_rel}) — {comps_ptr_desc}", ""]

    # Principles block.
    lines += principles_block(s.get("principles_label", "Principles"), s.get("principles", []))
    lines += ["", GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    content = "\n".join(lines) + user_tail
    return content if content.endswith("\n") else content + "\n"


def build_index_readme(docs_root: str, lang: str | None, timestamp: str,
                       existing_content: str = "") -> str:
    """Render the top-level reading-order docs/README.md (2-zone).

    Detects aggregate (system-of-systems) layout by presence of
    system/component-catalog.md and delegates to _build_aggregate_index.
    Non-aggregate path is byte-identical to pre-v14.1.0.

    Numbers, link targets, and role number-paths come from READING_ORDER/ROLES
    (lang-independent); only prose comes from get_strings(lang), so the generated
    zone is byte-identical across languages except for prose.
    """
    if _is_aggregate_root(docs_root):
        return _build_aggregate_index(docs_root, lang, timestamp, existing_content)

    s = get_strings(lang)
    descs = s["artifact_descriptions"]
    reading_why = s.get("reading_why", {})  # causal clause per layer-1-3 entry key
    h_num, h_doc, h_ans = s["col_headers"]
    # Presence is resolved once up front so the role paths and the layer tables
    # prune against the same set of files-on-disk.
    present_nums = {
        e["num"] for layer in READING_ORDER for e in layer["entries"]
        if entry_present(docs_root, e)
    }
    lines = [
        f"# {s['title']}", "",
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "",
        s["intro"], "",
    ]
    # Quick-path — same pruning as roles, so it never lists an absent artifact.
    quick = [n for n in QUICK_PATH if n in present_nums]
    if quick:
        lines += [f"**{s['quick_path_label']}: " + " → ".join(map(str, quick)) + "**", ""]
    # Role reading-paths — drop numbers whose artifact is absent; skip empty roles.
    # Reuses the shared aggregate helper (DRY); role_notes/note_gate add the A6
    # new_dev → feature-traversal pointer, gated on the features entry (16) surviving.
    lines += role_path_lines(
        present_nums, ROLES, s["role_labels"], s["roles_heading"],
        role_notes=s.get("role_notes", {}), note_gate=16,
    )
    omitted = False
    for layer in READING_ORDER:
        present = [e for e in layer["entries"] if e["num"] in present_nums]
        if len(present) != len(layer["entries"]):
            omitted = True  # any absent artifact (conditional or not) → footnote
        if not present:
            continue
        lines += [f"## {layer['layer']}. {s['layer_labels'][layer['layer']]}", ""]
        lines += [f"> {s['layer_intros'][layer['layer']]}", ""]
        lines += [f"| {h_num} | {h_doc} | {h_ans} |", "|---|---|---|"]
        for e in present:
            target = e["link"] if "glob" in e else e["path"]
            label = e["link"] if "glob" in e else os.path.basename(e["path"])
            desc = descs[e["key"]]
            clause = reading_why.get(e["key"])  # layers 1-3 only; absent ⇒ omitted
            if clause:
                desc = f"{desc} — {clause}"
            lines.append(f"| {e['num']} | [{label}]({target}) | {desc} |")
        lines.append("")
        if any(e.get("feature_note") for e in present):
            lines += [f"> {ln}" for ln in s["feature_traversal"]] + [""]
    # Relationship-map legend (A3) — extracted to _nav_feature_lib to keep this file < 200 LOC.
    lines += relationship_legend(s, present_nums)
    if omitted:
        lines += [f"_{s['footnote']}_", ""]
    lines += [f"### {s['principles_label']}", ""]
    lines += [f"- {p}" for p in s["principles"]]
    lines += ["", GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    content = "\n".join(lines) + user_tail
    return content if content.endswith("\n") else content + "\n"

