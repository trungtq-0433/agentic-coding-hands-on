# layout-exempt: component migration — docs/<primary>/components paths here are managed migration targets
"""_component_migrate_lib.py — v23 one-time component-tree migration helper.

For v20/v22 repos whose primary language is NOT en, the canonical component source
location changed from docs/components/ (root) to docs/<primary>/components/ in v23
(P04). This module performs the one-time, idempotent, atomic migration that converges
the old root tree into the new per-lang location.

Direction: docs/components/<name>/  →  docs/<primary>/components/<name>/
(The OPPOSITE of _converge_components_to_source in migrate_docs_layout.py, which
handles the legacy v15 direction. Both are kept intact — different call sites.)

Sentinel: docs/<primary>/.components-migrated-v23
Lock: docs/.layout-flip.lock  (reused — same POSIX advisory lock as the main flip)

Stdlib only. Raised exceptions propagate to the caller (synthesize_system.py) which
handles them as a soft warning rather than a hard abort.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lang_lib import COMPONENTS_V23_SENTINEL, normalize_lang  # noqa: E402
from migrate_docs_layout import _Lock, LOCK_NAME  # noqa: E402


def _files_identical(path_a: Path, path_b: Path) -> bool:
    """Return True when two files are byte-identical. Reads in 64 KiB chunks."""
    if path_a.stat().st_size != path_b.stat().st_size:
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        while True:
            chunk_a = fa.read(65536)
            chunk_b = fb.read(65536)
            if chunk_a != chunk_b:
                return False
            if not chunk_a:
                return True


def _trees_identical(src: Path, dst: Path) -> tuple[bool, list[str]]:
    """Compare two directory trees file-by-file.

    Returns (identical: bool, differing_rel_paths: list[str]).
    A file present in src but absent in dst counts as differing.
    Symlinks are skipped in both trees.
    """
    differing: list[str] = []
    for item in src.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        rel = item.relative_to(src)
        counterpart = dst / rel
        if not counterpart.is_file():
            differing.append(str(rel))
            continue
        if not _files_identical(item, counterpart):
            differing.append(str(rel))
    # Also catch files in dst not present in src (shouldn't happen for a generated
    # derived view, but be defensive).
    for item in dst.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        rel = item.relative_to(dst)
        if not (src / rel).exists():
            differing.append(str(rel))
    return (len(differing) == 0), differing


def _prune_generated_root_readme(docs_base: Path) -> None:
    """Remove the root docs/README.md if it is purely generated; leave hand-written ones.

    Delegates decision to _nav_aggregate_render.resolve_root_readme_removal (the
    same logic used by the nav render path — single source of truth for "generated?").
    """
    readme = docs_base / "README.md"
    if not readme.is_file():
        return
    try:
        from _nav_aggregate_render import resolve_root_readme_removal  # noqa: E402 local
    except ImportError:
        # Guard: if the render module is unavailable in a trimmed test context, skip pruning.
        print("[WARN] _component_migrate_lib: could not import resolve_root_readme_removal "
              "— root README.md not pruned (non-fatal).", file=sys.stderr)
        return
    content = readme.read_text(encoding="utf-8", errors="replace")
    action, tail = resolve_root_readme_removal(content)
    if action == "delete":
        readme.unlink()
        print("[INFO] component-migrate-v23: removed generated root docs/README.md")
    elif action == "preserve":
        # Keep only the user-written tail (strip the generated navigation zone).
        fd, tmp = tempfile.mkstemp(dir=str(docs_base), prefix=".readme-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(tail)
            os.replace(tmp, readme)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        print("[INFO] component-migrate-v23: preserved user tail of root docs/README.md "
              "(generated nav zone stripped)")
    # action == "skip" → hand-written, leave untouched (resolve_root_readme_removal already warned)


def migrate_components_to_lang(docs_base: Path, primary: str) -> bool:
    """v23 one-time migration: move root docs/components/ into docs/<primary>/components/.

    This is the v23 direction (root → lang-namespaced), the OPPOSITE of
    migrate_docs_layout._converge_components_to_source (lang → root, v15→v20 direction).
    Both coexist: they handle different migration eras and must not be conflated.

    Rules:
    - en-primary: no-op (en source legitimately lives at docs/components/).
    - Sentinel present: no-op (already migrated).
    - docs/components/ absent: no-op (nothing to migrate; new repo or already clean).
    - Byte-identical trees: prune root docs/components/; lang-namespaced wins.
    - Differing trees: keep both, emit [WARN], do NOT delete (data-loss prevention).
    - Atomic: lock + temp-dir rename so a crash leaves either old or new intact.
    - Also prunes a purely-generated root docs/README.md (after tree migration).

    Returns True if migration was performed, False on no-op.
    Raises OSError on unexpected filesystem failures.
    """
    primary = normalize_lang(primary)
    if primary == "en":
        return False  # en source lives at docs/components/ by design — no migration needed

    sentinel = docs_base / primary / COMPONENTS_V23_SENTINEL
    root_src = docs_base / "components"
    lang_dst = docs_base / primary / "components"

    with _Lock(docs_base / LOCK_NAME):
        if sentinel.exists():
            return False  # idempotent: already done

        if not root_src.is_dir():
            # Nothing at the old root location — either a fresh v23 repo or already clean.
            # Write the sentinel so we skip this check on future runs (fast-path).
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            _write_sentinel_atomic(sentinel)
            return False

        if not lang_dst.is_dir():
            # Lang destination does not exist yet: simple atomic rename (no comparison needed).
            lang_dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(root_src, lang_dst)
            print(f"[INFO] component-migrate-v23: moved {root_src} → {lang_dst} "
                  f"(new lang-namespaced source)")
            _prune_generated_root_readme(docs_base)
            _write_sentinel_atomic(sentinel)
            return True

        # Both root and lang dirs exist: compare byte-by-byte.
        identical, differing = _trees_identical(root_src, lang_dst)
        if identical:
            # Common case: derived view was a byte-exact copy. Prune the root duplicate.
            shutil.rmtree(str(root_src))
            print(f"[INFO] component-migrate-v23: removed byte-identical root {root_src}; "
                  f"canonical source is {lang_dst}")
            _prune_generated_root_readme(docs_base)
            _write_sentinel_atomic(sentinel)
            return True
        else:
            # Trees differ — refuse to destroy unmerged content (v15 data-loss lesson).
            shown = ", ".join(differing[:5]) + (" …" if len(differing) > 5 else "")
            print(
                f"[WARN] component-migrate-v23: {root_src} and {lang_dst} have "
                f"{len(differing)} differing file(s): {shown}. "
                f"Lang-namespaced tree ({lang_dst}) is authoritative. "
                f"Root tree left in place — resolve manually then re-run --aggregate.",
                file=sys.stderr,
            )
            return False


def _write_sentinel_atomic(sentinel: Path) -> None:
    """Write sentinel file via temp + os.replace (atomic, matches migrate_docs_layout pattern)."""
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(sentinel.parent), prefix=".comp-mig-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("migrated-v23\n")
        os.replace(tmp, sentinel)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
