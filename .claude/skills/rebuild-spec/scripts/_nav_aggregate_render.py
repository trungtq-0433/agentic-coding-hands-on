"""Shared aggregate README rendering helpers + nav utility functions.

The aggregate render helpers are called by BOTH _nav_index._build_aggregate_index
(top-level docs/<lang>/README.md) and _nav_aggregate_lib.build_aggregate_system_readme
(docs/<lang>/system/README.md). Keeps both callers DRY and under 200 LOC.

Callers differ only in link_prefix and pointer_rel:
  - Top-level index:   link_prefix="system/", pointer_rel="../components/"
  - System-subdir:     link_prefix="",         pointer_rel="../../components/"

Also hosts _entry_present, read_primary_lang_from_state, is_bare_docs_root, and
resolve_root_readme_removal (moved here to keep _nav_index.py under 200 LOC).
"""
from __future__ import annotations

import glob as _glob
import json
import os
import sys
from pathlib import Path

from _lang_lib import normalize_lang
from _nav_lib import GEN_END, file_description, read_user_tail


def reading_order_rows(
    present_files: list[str],
    link_prefix: str,
    col_headers: tuple[str, str, str],
    why_clauses: dict[str, str] | None = None,
) -> list[str]:
    """Return markdown table lines for a numbered reading-order table.

    present_files: filenames in order, already presence-pruned.
    link_prefix:   prepended to each filename for the link target.
    col_headers:   (num_hdr, doc_hdr, ans_hdr) locale strings.
    why_clauses:   optional filename→clause map; when provided, the causal clause
                   is appended to the "what it answers" cell as " — <clause>".
                   Absent key → clause omitted for that row (graceful degradation).
                   Default None preserves today's output (back-compat).
    Returns a list of lines (no trailing newline per line).
    """
    h_num, h_doc, h_ans = col_headers
    rows = [f"| {h_num} | {h_doc} | {h_ans} |", "|---|---|---|"]
    for idx, fname in enumerate(present_files, start=1):
        target = f"{link_prefix}{fname}"
        desc = file_description(fname)
        if why_clauses:
            clause = why_clauses.get(fname)
            if clause:
                desc = f"{desc} — {clause}"
        rows.append(f"| {idx} | [{fname}]({target}) | {desc} |")
    return rows


def role_path_lines(
    present_nums: set[int],
    roles: list[dict],
    role_labels: dict[str, str],
    heading: str,
    role_notes: dict[str, str] | None = None,
    note_gate: int | None = None,
) -> list[str]:
    """Return role reading-path lines (markdown bullet list under a heading).

    present_nums: set of 1-indexed positions that exist on disk.
    roles:        ROLES / AGGREGATE_ROLES list — each dict has "key" and "path".
    role_labels:  locale role_labels dict keyed by role key.
    heading:      locale roles_heading string.
    role_notes:   optional {role_key: note}; the note is appended to that role's line
                  as " — <note>" (A6 single-component feature pointer). Default None
                  preserves today's output (back-compat with the aggregate caller).
    note_gate:    optional entry number that must survive pruning (be in the role's
                  seq) for the note to render — so a note never points at an absent
                  artifact. None ⇒ render the note whenever one exists.
    Returns a list of lines, or [] if no role produces a non-empty sequence.
    """
    role_notes = role_notes or {}
    role_lines = []
    for r in roles:
        seq = [n for n in r["path"] if n in present_nums]
        if seq:
            label = role_labels.get(r["key"], r["key"])
            line = f"- **{label}:** " + " → ".join(str(n) for n in seq)
            note = role_notes.get(r["key"])
            if note and (note_gate is None or note_gate in seq):
                line += f" — {note}"
            role_lines.append(line)
    if not role_lines:
        return []
    return [f"## {heading}", ""] + role_lines + [""]


def components_pointer_row(
    next_idx: int,
    pointer_rel: str | None,
    label: str,
    desc: str,
) -> str | None:
    """Return a single markdown table row for the components pointer, or None.

    next_idx:    the row number (len(present_files) + 1).
    pointer_rel: relative path to the components index, e.g. "../components/" or
                 "../../components/". Pass None to suppress the row (no dead link).
    label:       locale components_pointer_label string.
    desc:        locale components_pointer_desc string.
    Returns a formatted table row string, or None when pointer_rel is None.
    """
    if pointer_rel is None:
        return None
    return f"| {next_idx} | [{label}]({pointer_rel}) | {desc} |"


def principles_block(label: str, principles: list[str]) -> list[str]:
    """Return lines for the principles block (heading + bullet list).

    Returns a list of lines with a trailing empty string before the caller adds GEN_END.
    """
    lines = [f"### {label}", ""]
    lines += [f"- {p}" for p in principles]
    return lines


# ---------------------------------------------------------------------------
# Nav utility functions (moved from _nav_index.py to keep it under 200 LOC)
# ---------------------------------------------------------------------------

def entry_present(docs_root: str, entry: dict) -> bool:
    """True if an entry's artifact exists on disk (single path or glob)."""
    if "path" in entry:
        return os.path.isfile(os.path.join(docs_root, entry["path"]))
    matches = _glob.glob(os.path.join(docs_root, entry["glob"]))
    if entry["glob"].endswith("/"):
        # features/*/ — a match counts only if the dir holds at least one .md
        for m in matches:
            if not os.path.isdir(m):
                continue
            try:
                if any(f.endswith(".md") for f in os.listdir(m)):
                    return True
            except OSError:
                continue
        return False
    return bool(matches)


def read_primary_lang_from_state(docs_root: str) -> str:
    """Read primary_lang from docs_root/.rebuild-state.json; fall back to 'en'."""
    try:
        data = json.loads(
            Path(os.path.join(docs_root, ".rebuild-state.json")).read_text(encoding="utf-8")
        )
        if isinstance(data, dict):
            return str(data.get("primary_lang") or "").strip() or "en"
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return "en"


def is_bare_docs_root(docs_root: str, primary_lang: str) -> bool:
    """True when docs_root is the bare docs/ root (NOT docs/<lang>/).

    Detects by comparing the last path segment to the normalized primary_lang.
    e.g. docs_root='/abs/docs' → segment='docs' ≠ 'en'/'vi' → True.
         docs_root='/abs/docs/en' → segment='en' == primary → False.
    """
    segment = os.path.basename(docs_root.rstrip(os.sep))
    try:
        return segment != normalize_lang(primary_lang)
    except ValueError:
        return True


def resolve_root_readme_removal(existing_content: str) -> tuple[str, str | None]:
    """Decide what to do with the bare docs/ root README.md in per-lang mode.

    Per-lang projects have a single entry point — docs/<primary_lang>/README.md.
    The root docs/README.md is NOT generated (v18 — was a ~3-line pointer in v15-v17).
    This resolver removes the generated root index but never destroys hand-written prose:

      ("delete", None)     — no file, or a purely rebuild-spec-generated README
                             (GEN markers with no user tail) → caller removes the file.
      ("preserve", tail)   — a user tail exists below GEN_END → caller rewrites the file
                             with ONLY that tail (the generated index zone is dropped).
      ("skip", None)       — a hand-written README with no generated markers → caller
                             leaves it untouched (we never delete the user's own file).
    """
    if not existing_content.strip():
        return ("delete", None)
    if GEN_END not in existing_content:
        # Hand-written root README — not ours to delete.
        print("[WARN] root_readme_no_markers: existing root README has no generated markers — "
              "leaving it untouched (per-lang mode does not generate a root README).",
              file=sys.stderr)
        return ("skip", None)
    user_tail = read_user_tail(existing_content)
    if user_tail.strip():
        body = user_tail.lstrip("\n")
        return ("preserve", body if body.endswith("\n") else body + "\n")
    return ("delete", None)
