"""Per-feature Route/API table resolution + rendering (Phase 4, v25.0.0).

Split out of _nav_feature_lib.py to hold that file under the 200-LOC invariant
(mirrors how _nav_table_parse_lib.py was pulled out earlier for the Screens table).
Reuses Phase 2/3's _route_link_lib.py parsing so the validator and nav render never
drift on what counts as a Backend Routes table or a Code/Owner column (DRY).

  - route_label_map()      — {ROUTE### -> (Method, Path)} from route-list.md
  - build_route_table_rows() — per-cited-ROUTE### row dicts for a feature's
                                technical-spec.md, resolved against route-list.md
  - render_route_section() — the presence-pruned Markdown block for build_feature_readme

No per-route files exist (unlike screens/SCR###/spec.md) — every row's "Spec" link
target is the single route-list.md, not a per-route deep link. Best-effort:
missing/pre-migration route-list.md never crashes, it just yields unresolved rows.
"""
from __future__ import annotations

import os

from _nav_table_parse_lib import _split_row, data_rows
from _route_link_lib import _all_backend_routes_tables, artifact_ref_cited_routes, route_columns

_METHOD_HEADER = "method"
_PATH_HEADER = "path"


def route_label_map(route_list_md: str) -> dict[str, tuple[str, str]]:
    """Build {ROUTE### -> (Method, Path)} from route-list.md's Backend Routes tables.

    route-list.md's documented shape is one sub-table per `### File:` heading, not a
    single monolithic table — loops over every sub-table (via
    _all_backend_routes_tables) so routes defined in the 2nd+ table still resolve.
    Empty when no sub-table has a Code column, or the file is unparseable —
    best-effort, never raises.
    """
    labels: dict[str, tuple[str, str]] = {}
    for table in _all_backend_routes_tables(route_list_md):
        if len(table) < 2:
            continue
        header = _split_row(table[0])
        header_cf = [h.casefold() for h in header]
        code_idx, _owner_idx = route_columns(header)
        if code_idx is None:
            continue
        method_idx = next((i for i, h in enumerate(header_cf) if h == _METHOD_HEADER), None)
        path_idx = next((i for i, h in enumerate(header_cf) if h == _PATH_HEADER), None)
        for raw in data_rows(table):
            cells = _split_row(raw)
            if code_idx >= len(cells):
                continue
            code = cells[code_idx].strip().upper()
            if not code or code.startswith("{"):
                continue
            method = cells[method_idx].strip() if method_idx is not None and method_idx < len(cells) else ""
            path = cells[path_idx].strip() if path_idx is not None and path_idx < len(cells) else ""
            labels[code] = (method, path)
    return labels


def build_route_table_rows(technical_spec_md: str, route_list_md: str | None) -> list[dict]:
    """Return one row dict per ROUTE### cited in technical-spec.md's Artifact
    References, resolved against route-list.md.

    Each row: {"code": str, "method": str|None, "path": str|None}. method/path are
    None when route_list_md is absent, pre-migration, or the code doesn't resolve —
    the caller renders those as the locale's "unresolved" marker. [] when the
    feature cites no ROUTE### at all (presence-pruning signal for the caller).
    """
    codes = artifact_ref_cited_routes(technical_spec_md)
    if not codes:
        return []
    labels = route_label_map(route_list_md) if route_list_md else {}
    rows = []
    for code in sorted(codes):
        method, path = labels.get(code, (None, None))
        rows.append({"code": code, "method": method or None, "path": path or None})
    return rows


def render_route_section(rows: list[dict], fr: dict) -> list[str]:
    """Render the presence-pruned Route/API Markdown block, or [] when rows is empty.

    Link target is always ../../generated/route-list.md — routes have no per-route
    spec file the way screens have spec.md, so every row links the same file.
    """
    if not rows:
        return []
    unresolved = fr.get("unresolved", "—")
    heading = fr.get("routes_heading", "Routes used by this feature")
    col_route = fr.get("col_route", "Route")
    col_owner = fr.get("col_route_owner", "Method + Path")
    col_spec = fr.get("col_route_spec", "Spec")
    lines = [f"## {heading}", "",
             f"| {col_route} | {col_owner} | {col_spec} |", "|---|---|---|"]
    spec_link = "[route-list.md](../../generated/route-list.md)"
    for row in rows:
        if row["method"] and row["path"]:
            label = f"{row['method']} {row['path']}"
            spec = spec_link
        else:
            label, spec = unresolved, unresolved
        lines.append(f"| {row['code']} | {label} | {spec} |")
    lines.append("")
    return lines


def feature_route_section(feature_dir: str, docs_root: str, fr: dict) -> list[str]:
    """Read one feature's technical-spec.md + generated/route-list.md off disk and
    render the presence-pruned Route/API section — the single call
    build_feature_readme() makes into this module. Best-effort: any read failure
    (absent file, OSError) degrades to an empty/unresolved result, never raises.
    """
    tech_spec_path = os.path.join(feature_dir, "technical-spec.md")
    if not os.path.isfile(tech_spec_path):
        return []
    try:
        with open(tech_spec_path, encoding="utf-8") as fh:
            tech_spec_md = fh.read()
    except OSError:
        return []
    route_list_md = None
    rl_path = os.path.join(docs_root, "generated", "route-list.md")
    if os.path.isfile(rl_path):
        try:
            with open(rl_path, encoding="utf-8") as fh:
                route_list_md = fh.read()
        except OSError:
            route_list_md = None
    rows = build_route_table_rows(tech_spec_md, route_list_md)
    return render_route_section(rows, fr)
