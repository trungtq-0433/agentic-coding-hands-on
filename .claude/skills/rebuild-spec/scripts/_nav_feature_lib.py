# layout-exempt: rebuild-spec nav feature helpers — docs/features|screens paths are this skill's own output targets
"""Feature-tier navigation helpers for the single-component docs index (A3-A6).

Render logic kept out of _nav_index.py / build_navigation.py to hold them under the
200-LOC invariant: relationship_legend (A3 index block), role_path_note (A6),
build_feature_readme (A4), build_features_index (A5), write_feature_pass (A4/A5 guarded
2-zone write over docs/features/*/ only — never general recursion). Tolerant table
parsing lives in _nav_table_parse_lib. Stdlib only, deterministic, 2-zone preserving.
"""
from __future__ import annotations

import os
import re
import sys

from _nav_lib import GEN_END, GEN_START, read_user_tail
from _nav_route_lib import feature_route_section
from _nav_table_parse_lib import index_screen_list, norm_name, parse_screen_names

# Feature reading order — the 4 mandatory satellite files, plus the optional
# test-cases.md SIDECAR (v26.1.0 B6) appended last. Presence-pruned at render
# time, so a repo that never ran --test-cases sees byte-identical output (the
# 5th entry simply never survives the os.path.isfile() filter below).
FEATURE_FILE_ORDER = [
    "business-context.md",
    "screens.md",
    "technical-spec.md",
    "edge-cases.md",
    "test-cases.md",
]

_FXXX_DIR_RE = re.compile(r"^F\d{3}(?:_.*)?$")


# ---------------------------------------------------------------------------
# A3 — relationship-map legend (index block)
# ---------------------------------------------------------------------------

def relationship_legend(strings: dict, present_nums: set[int]) -> list[str]:
    """Return the static ID-relationship legend lines, or [] when pruned.

    Rendered only when the feature (5), screen (7), or route (9) inventory is
    present, so the legend never points at absent files. A bullet list under the
    locale heading. Route-list.md already owns reading-order gate number 9 (see
    _nav_strings.py READING_ORDER) — reused here rather than inventing a new gate.
    """
    rel_map = strings.get("relationship_map", [])
    if not rel_map or not (present_nums & {5, 7, 9}):
        return []
    heading = strings.get("relationship_map_heading", "How the ID systems relate")
    return [f"## {heading}", ""] + [f"- {ln}" for ln in rel_map] + [""]


# ---------------------------------------------------------------------------
# A4 — per-feature README (docs/features/F###_Slug/README.md)
# ---------------------------------------------------------------------------

def build_feature_readme(feature_dir: str, docs_root: str, lang: str | None,
                         timestamp: str, existing_content: str = "") -> str:
    """Render the 2-zone README.md for one docs/features/F###_Slug/ directory.

    Sections: a presence-pruned 4-file reading order, then a best-effort
    Screen → SCR### → spec table (resolved against generated/screen-list.md by
    name, or read directly when screens.md already carries an SCR### column).
    """
    from _nav_strings import get_strings  # local import — avoid import cycle at module load

    s = get_strings(lang)
    fr = s.get("feature_readme", {})
    feature = os.path.basename(feature_dir.rstrip(os.sep))
    title = fr.get("title", "Feature {feature} — Reading Guide").replace("{feature}", feature)
    purposes = fr.get("file_purposes", {})

    present = [f for f in FEATURE_FILE_ORDER
               if os.path.isfile(os.path.join(feature_dir, f))]

    lines = [f"# {title}", "", GEN_START,
             f"<!-- rebuild-spec navigation — generated {timestamp} -->", ""]
    if fr.get("intro"):
        lines += [fr["intro"], ""]

    if present:
        lines += [f"## {fr.get('order_heading', 'Reading order')}", ""]
        for i, fname in enumerate(present, start=1):
            purpose = purposes.get(fname)
            suffix = f" — {purpose}" if purpose else ""
            lines.append(f"{i}. [{fname}]({fname}){suffix}")
        lines.append("")

    # Best-effort screen table from screens.md, resolved via screen-list.md.
    screens = []
    screens_md_path = os.path.join(feature_dir, "screens.md")
    if os.path.isfile(screens_md_path):
        try:
            screens = parse_screen_names(_read(screens_md_path))
        except OSError:
            screens = []
    if screens:
        name_to_code = {}
        sl_path = os.path.join(docs_root, "generated", "screen-list.md")
        if os.path.isfile(sl_path):
            try:
                name_to_code = index_screen_list(_read(sl_path))
            except OSError:
                name_to_code = {}
        unresolved = fr.get("unresolved", "—")
        lines += [f"## {fr.get('screens_heading', 'Screens in this feature')}", "",
                  f"| {fr.get('col_screen', 'Screen')} | {fr.get('col_scr', 'SCR')} "
                  f"| {fr.get('col_spec', 'Spec')} |", "|---|---|---|"]
        for row in screens:
            code = row.get("scr") or name_to_code.get(norm_name(row["name"]))
            if code:
                spec = f"[spec.md](../../screens/{code}/spec.md)"
            else:
                code, spec = unresolved, unresolved
            lines.append(f"| {row['name']} | {code} | {spec} |")
        lines.append("")

    # Best-effort Route/API table (presence-pruned, best-effort file IO, per-route
    # spec-link caveat) — all delegated to _nav_route_lib to hold this file's LOC.
    lines += feature_route_section(feature_dir, docs_root, fr)

    lines += ["", GEN_END]
    return _finish(lines, existing_content)


def build_features_index(features_dir: str, docs_root: str, lang: str | None,
                         timestamp: str, existing_content: str = "") -> str:
    """Render docs/features/README.md — an index of every F###_Slug/ subfolder (A5).

    Lists each feature subdir with a link into its folder. Summaries from
    generated/feature-list.md are best-effort (omitted on parse miss).
    """
    from _nav_strings import get_strings  # local import — avoid import cycle

    s = get_strings(lang)
    fi = s.get("features_index", {})
    subdirs = sorted(
        d for d in _listdir(features_dir)
        if _FXXX_DIR_RE.match(d) and os.path.isdir(os.path.join(features_dir, d))
    )
    lines = [f"# {fi.get('title', 'Features — Index')}", "", GEN_START,
             f"<!-- rebuild-spec navigation — generated {timestamp} -->", ""]
    if fi.get("intro"):
        lines += [fi["intro"], ""]
    for d in subdirs:
        lines.append(f"- [{d}]({d}/)")
    lines += ["", GEN_END]
    return _finish(lines, existing_content)


# ---------------------------------------------------------------------------
# small IO + assembly helpers (kept private; never raise on read)
# ---------------------------------------------------------------------------

def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _listdir(path: str) -> list[str]:
    try:
        return os.listdir(path)
    except OSError:
        return []


def _finish(lines: list[str], existing_content: str) -> str:
    """Append the preserved user tail and guarantee a trailing newline (2-zone)."""
    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    content = "\n".join(lines) + user_tail
    return content if content.endswith("\n") else content + "\n"


def _guarded_write(raw: str, docs_root: str, content) -> None:
    """Write content (str or existing→str callable) via the RT-F14 guard. Never raises."""
    from _nav_components_io import _atomic_write
    from _path_lib import _resolve_guarded
    try:
        guarded = _resolve_guarded(raw, docs_root)
    except ValueError as e:
        print(f"[ERROR] write-safety violation for {raw}: {e}", file=sys.stderr)
        return
    existing = ""
    if os.path.isfile(guarded):
        try:
            existing = _read(guarded)
        except OSError:
            pass
    body = content(existing) if callable(content) else content
    try:
        _atomic_write(guarded, body)
    except OSError as e:
        print(f"[ERROR] cannot write {guarded}: {e}", file=sys.stderr)


def write_feature_pass(docs_root: str, lang: str | None, timestamp: str) -> None:
    """Write per-feature READMEs (A4) and the features index (A5).

    Restricted to docs/features/*/ — NEVER general recursion (so it can never write
    stray READMEs into screens/SCR###/ etc.). Each write is 2-zone + guarded. A
    features/ dir with no F### subdir produces nothing (index suppressed).
    """
    features_dir = os.path.join(docs_root, "features")
    if not os.path.isdir(features_dir):
        return
    fxxx = sorted(
        d for d in _listdir(features_dir)
        if _FXXX_DIR_RE.match(d) and os.path.isdir(os.path.join(features_dir, d))
    )
    for d in fxxx:
        fdir = os.path.join(features_dir, d)
        raw = os.path.join(fdir, "README.md")
        _guarded_write(
            raw, docs_root,
            lambda existing, _fd=fdir: build_feature_readme(_fd, docs_root, lang, timestamp, existing),
        )
    # A5 — features index, only when ≥1 F### subdir exists (scoped suppression).
    if fxxx:
        idx_raw = os.path.join(features_dir, "README.md")
        _guarded_write(
            idx_raw, docs_root,
            lambda existing: build_features_index(features_dir, docs_root, lang, timestamp, existing),
        )
