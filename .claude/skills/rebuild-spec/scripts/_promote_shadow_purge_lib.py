"""Shadow/intermediate artifact purge after a successful aggregate promote.

Called from promote_drafts.py ONLY on the success path (after Step-4 sha manifest).
Never called on the exit-3 (0-promoted) guard path.

Deletes:
  - *.draft.md source files in artifacts_dir that were promoted this run
  - .system-scout-report.md under the resolved system docs root (best-effort)
  - .review-archive/ (or scope-specific archive dir) under docs_root (best-effort)
    unless REBUILD_KEEP_REVIEW_ARCHIVE=1

Keeps (NEVER touched):
  - per-component-confidence.md  (reading-order item #7, reader deliverable)
  - _service-digest.json, _source-to-fcode.json   (incremental state)
  - .rebuild-state.json, .rebuild-system-state.json (incremental state)

Stdlib only.  Python 3.9+.
"""
from __future__ import annotations

import os
import shutil
from typing import Iterable


# Files that must NEVER be deleted, regardless of name match.
_KEEP_EXACT: frozenset[str] = frozenset(
    [
        "per-component-confidence.md",
        "_service-digest.json",
        "_source-to-fcode.json",
        ".rebuild-state.json",
        ".rebuild-system-state.json",
    ]
)


def _safe_unlink(path: str, docs_root: str) -> None:
    """Unlink a single file with a path-guard and best-effort semantics.

    Silently no-ops if the file does not exist; prints a [WARN] on any OS error.
    Raises ValueError if path escapes docs_root (path-traversal guard).
    """
    real = os.path.realpath(os.path.abspath(path))
    base = os.path.realpath(os.path.abspath(docs_root))
    if os.path.commonpath([real, base]) != base:
        raise ValueError(
            f"[PURGE] path traversal rejected: {path!r} escapes {docs_root!r}"
        )
    basename = os.path.basename(path)
    if basename in _KEEP_EXACT:
        return
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass  # idempotent
    except OSError as exc:
        print(f"[WARN] purge: cannot delete {path}: {exc}")


def _safe_rmtree(path: str, docs_root: str) -> None:
    """Remove a directory tree with a path-guard and best-effort semantics.

    Silently no-ops if the directory does not exist; prints a [WARN] on any OS error.
    Raises ValueError if path escapes docs_root.
    """
    real = os.path.realpath(os.path.abspath(path))
    base = os.path.realpath(os.path.abspath(docs_root))
    if os.path.commonpath([real, base]) != base:
        raise ValueError(
            f"[PURGE] path traversal rejected: {path!r} escapes {docs_root!r}"
        )
    if not os.path.isdir(path):
        return  # idempotent
    try:
        shutil.rmtree(path)
    except OSError as exc:
        print(f"[WARN] purge: cannot remove {path}: {exc}")


def _purge_run_shadows(
    docs_root: str,
    artifacts_dir: str,
    promoted_srcs: Iterable[str],
    scope: str,
    archive_dir_name: str,
) -> None:
    """Delete shadow/intermediate artifacts produced this run, after a successful promote.

    Parameters
    ----------
    docs_root:
        Absolute path to the top-level docs directory (the --docs-root argument).
    artifacts_dir:
        Absolute path to the plan's artifacts/ directory.  *.draft.md source files
        that were promoted live here.
    promoted_srcs:
        The source paths (under artifacts_dir) that were actually promoted this run.
        Only *.draft.md files in this set are deleted; all others are skipped.
    scope:
        The promote scope ('core', 'all', 'features', etc.).  Used for the archive
        dir name lookup and for log messages.
    archive_dir_name:
        The archive subdirectory name under docs_root for this scope
        (e.g. '.review-archive' for core/all).
    """
    # ── 1. Delete *.draft.md source files that were promoted this run ────────
    for src in promoted_srcs:
        basename = os.path.basename(src)
        if not basename.endswith(".draft.md"):
            continue
        if basename in _KEEP_EXACT:
            continue
        _safe_unlink(src, artifacts_dir)

    # ── 2. Delete .system-scout-report.md (best-effort, multiple candidate dirs) ─
    # The file is written by synthesize_system.py to the resolved system docs root,
    # which may be docs_root/system/, docs_root/<lang>/system/, or docs_root/.
    _SCOUT = ".system-scout-report.md"
    candidate_dirs: list[str] = []
    # Primary candidates: docs_root/system/ and docs_root/ itself
    candidate_dirs.append(os.path.join(docs_root, "system"))
    candidate_dirs.append(docs_root)
    # Secondary: any docs_root/<lang>/system/ one level deep (per-lang layout)
    try:
        for entry in os.scandir(docs_root):
            if entry.is_dir() and not entry.name.startswith("."):
                sub = os.path.join(entry.path, "system")
                if os.path.isdir(sub):
                    candidate_dirs.append(sub)
    except OSError:
        pass

    for candidate in candidate_dirs:
        scout_path = os.path.join(candidate, _SCOUT)
        if os.path.isfile(scout_path):
            _safe_unlink(scout_path, docs_root)
            break  # only one expected per run

    # ── 3. Delete .review-archive/ root (opt-out via REBUILD_KEEP_REVIEW_ARCHIVE=1) ─
    if os.environ.get("REBUILD_KEEP_REVIEW_ARCHIVE", "0").strip() == "1":
        print(
            f"[INFO] purge: REBUILD_KEEP_REVIEW_ARCHIVE=1 — "
            f"keeping {archive_dir_name}/ (audit-retention mode)"
        )
        return

    archive_root = os.path.join(docs_root, archive_dir_name)
    _safe_rmtree(archive_root, docs_root)


def purge_system_drafts(system_dir: str, docs_root: str) -> list[str]:
    """Delete aggregate *.draft.md files in system_dir whose promoted sibling exists.

    For each ``<name>.draft.md`` in system_dir (non-recursive):
      - Derive the promoted sibling: ``<name>.md`` (strip the ``.draft`` infix,
        e.g. ``overview.draft.md`` → ``overview.md``).
      - Delete the draft ONLY when the promoted sibling exists on disk.
      - KEEP the draft when the sibling is absent — that means the promote gate
        did NOT run yet, and deleting would cause data loss.

    The path-traversal guard (``_safe_unlink``) and ``_KEEP_EXACT`` allowlist are
    applied for every candidate.

    Parameters
    ----------
    system_dir:
        Absolute path to the docs/<lang>/system/ directory (or docs/system/).
    docs_root:
        Absolute path used as the traversal-guard boundary (typically the parent
        of system_dir, i.e. docs/<lang>/ or docs/).

    Returns
    -------
    list[str]
        Absolute paths of files that were deleted (in discovery order).
    """
    deleted: list[str] = []
    try:
        entries = sorted(os.listdir(system_dir))
    except OSError as exc:
        print(f"[WARN] purge_system_drafts: cannot list {system_dir}: {exc}")
        return deleted

    for fname in entries:
        if not fname.endswith(".draft.md"):
            continue
        if fname in _KEEP_EXACT:
            continue
        # Derive the promoted sibling name: strip the ".draft" infix.
        # "overview.draft.md" → "overview.md"
        promoted_name = fname.replace(".draft.", ".", 1)
        promoted_path = os.path.join(system_dir, promoted_name)
        if not os.path.isfile(promoted_path):
            # Sibling absent → promote did not happen → keep the draft.
            continue
        draft_path = os.path.join(system_dir, fname)
        _safe_unlink(draft_path, docs_root)
        if not os.path.exists(draft_path):
            deleted.append(draft_path)

    return deleted
