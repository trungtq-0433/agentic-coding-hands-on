#!/usr/bin/env python3
# layout-exempt: migrate_docs_layout — all docs/<layer> paths here are managed migration targets
"""migrate_docs_layout.py — one-time docs layout flip (single-lang → per-lang).

When an en-primary repo gains its FIRST secondary language, its English content
must move from the `docs/` root into `docs/<primary>/` so every language is a
sibling under `docs/`. This script performs that flip — atomic + idempotent via a
sentinel — and the related one-time alias rename (`docs/jp/` → `docs/ja/`) plus its
`.rebuild-state.json → translations` key migration.

Operations (mutually exclusive CLI modes):
  (default)             flip docs/ root → docs/<primary>/   (en-primary, at-root, no sentinel)
  --rollback            undo a PARTIAL flip (sentinel absent): docs/<primary>/* → docs/ root
  --rename-alias jp:ja  rename docs/jp/ → docs/ja/ (+ state key); abort if both exist

Idempotency is SENTINEL-ONLY: a populated `docs/<primary>/` without the sentinel is
a partial migration → resume per-directory, never a no-op. A repo whose primary is
not `en` is already per-lang shaped → the flip is a no-op.

Exit codes: 0 ok/no-op, 1 abort (coexistence / guard), 2 arg/IO error. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lang_lib import _ALIASES, _PATH_UNSAFE_RE, LAYOUT_SENTINEL, normalize_lang  # noqa: E402
from _summary_lib import atomic_write  # noqa: E402


def _safe_code(code: str) -> str:
    """Lowercase + path-safety guard WITHOUT de-aliasing.

    Used for the `--rename-alias` source arm: it is the LEGACY (non-canonical) dir
    name we are renaming FROM, so it must stay literal (`jp`, not `ja`) — but it must
    still be rejected if it carries path-traversal characters.
    """
    c = (code or "").strip().lower()
    if not c or _PATH_UNSAFE_RE.search(c):
        raise ValueError(f"unsafe or empty language code: {code!r}")
    return c


try:
    import fcntl  # POSIX advisory locks
    _HAS_FCNTL = True
except ImportError:  # pragma: no cover - Windows
    _HAS_FCNTL = False

# Generated/curated language layers that MOVE with a flip/relocate. Container-level files
# (.rebuild-state.json, _source-to-fcode.json, _promoted-sha256.txt) and human ADRs
# (decisions/) stay at the docs/ root and are NEVER moved.
# v20.0.0: `components/` is NOT in MOVED_LAYERS — it stays at docs/components/ as the
# lang-agnostic SOURCE of truth (v20) or at docs/<primary>/components/ for non-en primaries
# after the v23 P04 relocation. Legacy trees that still have a stray docs/<L>/components/
# from a prior v15 run are converged back to the source location by
# _converge_components_to_source (v20-era legacy helper; NOT called by the v23 P07 migration).
MOVED_LAYERS = ("system", "generated", "flows", "features", "screens")

# Backward-compat alias: callers that iterate ALL layers (e.g. rollback) may still
# include components to move it back on rollback. Keep LANGUAGE_LAYERS pointing to the
# full original set so existing code that references it (tests, callers) is not silently
# broken. The flip/relocate paths now use MOVED_LAYERS.
LANGUAGE_LAYERS = (*MOVED_LAYERS, "components")
LOCK_NAME = ".layout-flip.lock"
REVERSE_INDEX_NAME = "_source-to-fcode.json"
STATE_NAME = ".rebuild-state.json"


# --------------------------------------------------------------------------- #
# Locking — exclusive advisory lock around the whole operation (C3).
# --------------------------------------------------------------------------- #
class _Lock:
    """Exclusive lock context manager. fcntl.flock on POSIX, O_EXCL file on Windows."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fh = None
        self._fd = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if _HAS_FCNTL:
            self._fh = open(self.lock_path, "w")
            fcntl.flock(self._fh, fcntl.LOCK_EX)
        else:  # pragma: no cover - Windows
            # Spin-free single attempt: O_EXCL create. Stale lock requires manual clear.
            self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        return self

    def __exit__(self, *exc):
        if self._fh is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()
        if self._fd is not None:  # pragma: no cover - Windows
            os.close(self._fd)
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
        return False


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _sentinel_path(docs_base: Path, primary: str) -> Path:
    return docs_base / primary / LAYOUT_SENTINEL


def _write_sentinel(path: Path) -> None:
    """Atomic sentinel write: temp file + os.replace. The LAST write of a flip."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".layout-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("migrated\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _invalidate_reverse_index(docs_base: Path) -> bool:
    """Delete docs/_source-to-fcode.json so a post-flip run regenerates it. (H)"""
    idx = docs_base / REVERSE_INDEX_NAME
    if idx.is_file():
        idx.unlink()
        return True
    return False


def _migrate_state_alias_keys(docs_base: Path) -> list[str]:
    """Rename translations[alias] → translations[canonical] in .rebuild-state.json.

    Atomic (atomic_write). Keeps incremental staleness checks working; no orphan
    alias key lingers (Sec-F2). Returns the list of renamed keys for reporting.
    """
    state_path = docs_base / STATE_NAME
    if not state_path.is_file():
        return []
    import json
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    translations = state.get("translations")
    if not isinstance(translations, dict):
        return []
    renamed: list[str] = []
    for alias, canon in _ALIASES.items():
        if alias in translations:
            if canon not in translations:
                translations[canon] = translations.pop(alias)
            else:
                # Both keys present — canonical wins, drop the orphan alias key.
                translations.pop(alias)
            renamed.append(f"{alias}->{canon}")
    if renamed:
        atomic_write(state_path, state)
    return renamed


def _rename_alias_dirs(docs_base: Path, *, force: bool) -> tuple[list[str], str | None]:
    """Rename docs/<alias>/ → docs/<canonical>/ for every known alias pair.

    Coexistence (both dirs exist) ABORTS unless force (Sec-F4/FMA-F4). With force,
    merge alias files into canonical (never overwriting an existing canonical file),
    then remove the emptied alias dir. Returns (renamed, abort_message_or_None).
    """
    renamed: list[str] = []
    for alias, canon in _ALIASES.items():
        a_dir = docs_base / alias
        c_dir = docs_base / canon
        if not a_dir.is_dir():
            continue
        if c_dir.exists():
            if not force:
                a_n = sum(1 for _ in a_dir.rglob("*") if _.is_file())
                c_n = sum(1 for _ in c_dir.rglob("*") if _.is_file())
                return renamed, (
                    f"ABORT — both docs/{alias}/ ({a_n} files) and docs/{canon}/ ({c_n} files) "
                    f"exist. Refusing to clobber. Re-run with --force-rename-alias to merge "
                    f"docs/{alias}/ into docs/{canon}/."
                )
            _merge_dir(a_dir, c_dir)
            renamed.append(f"docs/{alias}->docs/{canon} (merged)")
        else:
            os.rename(a_dir, c_dir)
            renamed.append(f"docs/{alias}->docs/{canon}")
    return renamed, None


def _merge_dir(src: Path, dst: Path) -> None:
    """Move src/* into dst, never overwriting existing dst files; remove emptied src.

    When a src file collides with an existing dst file, canonical (dst) wins and the src
    copy is dropped. Such conflicts are REPORTED (not silently swallowed): the discarded
    src content may differ from canonical and is unrecoverable once src is removed.
    Symlinks are skipped — never dereferenced or moved across the merge.
    """
    conflicts: list[str] = []
    for item in src.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        rel = item.relative_to(src)
        target = dst / rel
        if target.exists():
            conflicts.append(str(rel))  # canonical wins; alias copy will be discarded
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(item), str(target))
    if conflicts:
        shown = ", ".join(conflicts[:10]) + (" …" if len(conflicts) > 10 else "")
        print(f"[WARN] {len(conflicts)} alias file(s) under {src} collided with canonical "
              f"copies in {dst}; the canonical version was kept and the alias copy "
              f"discarded (unrecoverable): {shown}", file=sys.stderr)

    def _on_rmtree_error(func, path, exc_info):  # noqa: ANN001 - shutil onerror signature
        print(f"[WARN] could not remove {path} during alias merge: {exc_info[1]}",
              file=sys.stderr)
    shutil.rmtree(src, onerror=_on_rmtree_error)


# --------------------------------------------------------------------------- #
# Migration helpers (v15.0.0)
# --------------------------------------------------------------------------- #

def purge_document_maps(docs_base: Path) -> int:
    """Delete DOCUMENT-MAP.md + DOCUMENT-MAP.draft.md at every tier under docs_base.

    Exact filename match only (no glob). Idempotent — absent files are silently
    skipped. Returns the count of deleted files. Archive dirs
    (.review-archive, .flows-archive, .feature-specs-archive) are walked normally
    since we only delete the two specific filenames and leave everything else intact.
    """
    targets = {"DOCUMENT-MAP.md", "DOCUMENT-MAP.draft.md"}
    count = 0
    try:
        for dirpath, _dirnames, filenames in os.walk(str(docs_base)):
            for fname in filenames:
                if fname in targets:
                    try:
                        os.unlink(os.path.join(dirpath, fname))
                        count += 1
                    except OSError as exc:
                        print(f"[WARN] could not delete {os.path.join(dirpath, fname)}: {exc}",
                              file=sys.stderr)
    except OSError as exc:
        print(f"[WARN] purge_document_maps walk failed: {exc}", file=sys.stderr)
    if count:
        print(f"[INFO] purged {count} DOCUMENT-MAP file(s)")
    return count


def _converge_components_to_source(docs_base: Path, primary: str) -> bool:
    """v20-era legacy helper: move docs/<primary>/components/ back to docs/components/.

    This is NOT called by the v23 P07 migration — P07 uses
    _component_migrate_lib.migrate_components_to_lang for the forward direction instead.
    Retained for historical tooling and test coverage only.

    Trees migrated under v15 may have docs/<primary>/components/ as the only copy.
    This converge moves it back to the canonical source location.
    Idempotent: no-op when docs/components/ already exists (already canonical).
    Returns True if a move was performed.
    """
    src = docs_base / primary / "components"
    dst = docs_base / "components"
    if not src.is_dir():
        return False
    if dst.exists():
        # Both exist (e.g. partial v20 upgrade): the canonical source wins; the legacy
        # docs/<primary>/components/ is left untouched (never clobbered) but flagged so
        # the operator knows a stale copy remains (M1).
        print(f"[WARN] converge: both {src} and {dst} exist — keeping canonical source "
              f"{dst}; legacy {src} left in place (stale; safe to delete manually).",
              file=sys.stderr)
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.rename(src, dst)
    print(f"[INFO] converge: moved {src} → {dst} (v20 source consolidation)")
    return True


def _catchup_components(docs_base: Path, primary: str) -> bool:
    """Deprecated v15 catch-up: kept for import compatibility, now a no-op.

    v20 model: components SOURCE stays at docs/components/ (never relocated into
    docs/<primary>/components/). Use _converge_components_to_source to move a
    legacy docs/<primary>/components/ BACK to the canonical source location.
    """
    return False


# --------------------------------------------------------------------------- #
# Modes
# --------------------------------------------------------------------------- #
def flip(docs_base: Path, primary: str, *, force_rename: bool) -> int:
    """Flip docs/ root → docs/<primary>/ for an en-primary repo. No-op otherwise."""
    primary = normalize_lang(primary)
    if primary != "en":
        print(f"[INFO] primary '{primary}' is non-en — already per-lang; flip is a no-op.")
        return 0

    with _Lock(docs_base / LOCK_NAME):
        sentinel = _sentinel_path(docs_base, primary)
        if sentinel.exists():
            # v23: the P07 component migration is migrate_components_to_lang (in
            # _component_migrate_lib); _converge_components_to_source is v20-era legacy only.
            print(f"[INFO] sentinel present ({sentinel}) — already migrated.")
            return 0

        target = docs_base / primary
        moved: list[str] = []
        for layer in MOVED_LAYERS:  # v20: MOVED_LAYERS excludes components
            src = docs_base / layer
            dst = target / layer
            if not src.is_dir():
                continue  # nothing to move (or already moved in a prior partial run)
            if dst.exists():
                print(f"[WARN] both {src} and {dst} exist — skipping (assume resumed).", file=sys.stderr)
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, dst)  # atomic per-directory; resume-safe
            moved.append(layer)

        # Alias dir rename (docs/jp -> docs/ja) + state key migration, under the lock.
        renamed_dirs, abort = _rename_alias_dirs(docs_base, force=force_rename)
        if abort:
            print(f"[ERROR] {abort}", file=sys.stderr)
            return 1
        renamed_keys = _migrate_state_alias_keys(docs_base)

        invalidated = _invalidate_reverse_index(docs_base)
        _write_sentinel(sentinel)  # FINAL write

    print(f"[INFO] flip complete — moved layers: {moved or 'none (resumed)'}; "
          f"alias dirs: {renamed_dirs or 'none'}; state keys: {renamed_keys or 'none'}; "
          f"reverse-index invalidated: {invalidated}; sentinel: {sentinel}")
    return 0


def relocate_to_primary(docs_base: Path, primary: str) -> tuple[int, list[str]]:
    """Relocate a flat legacy tree (docs/<layer>) into docs/<primary>/<layer>.

    Unlike :func:`flip` (which is en-primary-specific by design), this handles the
    synthesis case where the discovered primary is NON-en yet the content still sits
    flat at the docs/ root with no sentinel — the language-mapping the user asked for
    kicks in immediately. Idempotent via the sentinel: a populated docs/<primary>/ with
    the sentinel is a no-op. No silent fork — every flat language layer present moves,
    so no orphaned flat copy is left behind. Returns (rc, moved_layers).
    """
    primary = normalize_lang(primary)
    with _Lock(docs_base / LOCK_NAME):
        sentinel = _sentinel_path(docs_base, primary)
        if sentinel.exists():
            # v20: no catch-up move needed (components stays at source docs/components/).
            print(f"[INFO] sentinel present ({sentinel}) — already migrated.")
            return 0, []
        target = docs_base / primary
        moved: list[str] = []
        for layer in MOVED_LAYERS:  # v20: MOVED_LAYERS excludes components
            src = docs_base / layer
            dst = target / layer
            if not src.is_dir():
                continue
            if dst.exists():
                print(f"[WARN] both {src} and {dst} exist — skipping (assume resumed).",
                      file=sys.stderr)
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, dst)  # atomic per-directory; resume-safe
            moved.append(layer)
        _write_sentinel(sentinel)  # FINAL write
    print(f"[INFO] relocate complete — primary '{primary}'; moved layers: "
          f"{moved or 'none (resumed)'}; sentinel: {sentinel}")
    return 0, moved


def rollback(docs_base: Path, primary: str) -> int:
    """Undo a PARTIAL flip (sentinel absent): move docs/<primary>/* back to docs/ root."""
    primary = normalize_lang(primary)
    with _Lock(docs_base / LOCK_NAME):
        sentinel = _sentinel_path(docs_base, primary)
        if sentinel.exists():
            print(f"[ERROR] sentinel present ({sentinel}) — flip is COMPLETE, not partial. "
                  f"Refusing to roll back a finished migration.", file=sys.stderr)
            return 1
        target = docs_base / primary
        if not target.is_dir():
            print("[INFO] nothing to roll back — no partial target dir.")
            return 0
        restored: list[str] = []
        for layer in LANGUAGE_LAYERS:
            src = target / layer
            dst = docs_base / layer
            if not src.is_dir():
                continue
            if dst.exists():
                print(f"[WARN] {dst} already at root — skipping.", file=sys.stderr)
                continue
            os.rename(src, dst)
            restored.append(layer)
        # Remove the now-empty (or layer-free) partial target dir.
        try:
            if target.is_dir() and not any(target.iterdir()):
                target.rmdir()
        except OSError:
            pass
    print(f"[INFO] rollback complete — restored layers: {restored or 'none'}.")
    return 0


def rename_alias_only(docs_base: Path, spec: str, *, force: bool) -> int:
    """Standalone alias rename: --rename-alias <alias>:<canon> (+ state key)."""
    if ":" not in spec:
        print(f"[ERROR] --rename-alias expects <alias>:<canon>, got {spec!r}", file=sys.stderr)
        return 2
    # Both arms are path-safety-checked (stops `--rename-alias ../evil:ja` resolving
    # docs_base/../evil outside docs/). The source arm keeps its LITERAL legacy name
    # (NOT de-aliased — that's the dir we rename FROM); the canon arm is de-aliased.
    src_raw, _, canon_raw = spec.partition(":")
    try:
        alias = _safe_code(src_raw)
        canon = normalize_lang(canon_raw)
    except ValueError as exc:
        print(f"[ERROR] unsafe code in --rename-alias {spec!r}: {exc}", file=sys.stderr)
        return 2
    with _Lock(docs_base / LOCK_NAME):
        a_dir, c_dir = docs_base / alias, docs_base / canon
        if not a_dir.is_dir():
            print(f"[INFO] docs/{alias}/ absent — nothing to rename.")
            return 0
        if c_dir.exists() and not force:
            a_n = sum(1 for _ in a_dir.rglob("*") if _.is_file())
            c_n = sum(1 for _ in c_dir.rglob("*") if _.is_file())
            print(f"[ERROR] ABORT — both docs/{alias}/ ({a_n} files) and docs/{canon}/ "
                  f"({c_n} files) exist. Re-run with --force-rename-alias to merge.", file=sys.stderr)
            return 1
        if c_dir.exists():
            _merge_dir(a_dir, c_dir)
        else:
            os.rename(a_dir, c_dir)
        renamed_keys = _migrate_state_alias_keys(docs_base)
        # Mirror the flip path: the rename changes paths, so the reverse-index is stale.
        invalidated = _invalidate_reverse_index(docs_base)
    print(f"[INFO] renamed docs/{alias}/ → docs/{canon}/; state keys: {renamed_keys or 'none'}; "
          f"reverse-index invalidated: {invalidated}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Docs layout flip (single-lang → per-lang)")
    p.add_argument("--primary", default="en", help="Primary language code (default: en)")
    p.add_argument("--docs-base", default="docs", help="Docs base dir (default: docs)")
    p.add_argument("--rollback", action="store_true", help="Undo a partial flip")
    p.add_argument("--rename-alias", default=None, metavar="ALIAS:CANON",
                   help="Standalone alias dir rename, e.g. jp:ja")
    p.add_argument("--force-rename-alias", action="store_true",
                   help="Merge alias dir into canonical when both exist (no silent clobber)")
    args = p.parse_args(argv)

    docs_base = Path(args.docs_base).resolve()
    if not docs_base.exists():
        print(f"[ERROR] docs base not found: {docs_base}", file=sys.stderr)
        return 2

    try:
        if args.rename_alias:
            return rename_alias_only(docs_base, args.rename_alias, force=args.force_rename_alias)
        if args.rollback:
            return rollback(docs_base, args.primary)
        return flip(docs_base, args.primary, force_rename=args.force_rename_alias)
    except OSError as exc:
        print(f"[ERROR] migrate_docs_layout failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
