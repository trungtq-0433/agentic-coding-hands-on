"""Reused-root detection helpers for Phase 05 (Reuse≠Exclude).

A "reused sub-root" is a directory (below the scan root) that:
  - Contains docs/.rebuild-state.json (was independently rebuilt standalone), AND
  - Is NOT the scan root itself.

Such a directory is claimed as ONE component with status="reused" and provenance
fields (docs_path, source_sha, is_git_root).  Descent is halted (dirnames[:]=[]
inside find_components) so a FE+BE product like `employee/{backend,frontend}` is
NOT split into peer build units.

Reused nodes are NEVER assigned to a group — they represent a whole product.

Stdlib only.
"""
from __future__ import annotations

import json
import os

# The sentinel filename that marks a reused standalone rebuild.
REBUILD_STATE_FILE = ".rebuild-state.json"
REUSED_DOCS_SUBDIR = "docs"


def is_reused_root(dirpath: str, scan_root: str) -> bool:
    """Return True when dirpath (not the scan root) contains docs/.rebuild-state.json."""
    if os.path.realpath(dirpath) == os.path.realpath(scan_root):
        return False
    state_file = os.path.join(dirpath, REUSED_DOCS_SUBDIR, REBUILD_STATE_FILE)
    return os.path.isfile(state_file)


def read_reused_provenance(dirpath: str) -> dict:
    """Read provenance fields from a reused root's docs/.rebuild-state.json.

    Returns:
        {
          "source_sha":  str  — last_rebuild_sha from state; "" if absent/zero,
          "is_git_root": bool — True if .git exists as a dir OR file (worktree),
          "docs_path":   str  — relative subdirectory path; caller sets this from rel,
        }
    """
    state_file = os.path.join(dirpath, REUSED_DOCS_SUBDIR, REBUILD_STATE_FILE)
    source_sha = ""
    try:
        with open(state_file, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            sha_raw = data.get("last_rebuild_sha", "")
            if isinstance(sha_raw, str) and sha_raw and sha_raw != "0" * 40:
                source_sha = sha_raw
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    # Detect git root: both isdir (normal clone) and isfile (worktree) must succeed.
    git_marker = os.path.join(dirpath, ".git")
    is_git_root = os.path.isdir(git_marker) or os.path.isfile(git_marker)

    return {
        "source_sha": source_sha,
        "is_git_root": is_git_root,
        # docs_path is rel + "/docs"; populated by find_components with the rel path
        "docs_path": "",
    }
