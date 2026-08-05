"""Components run-plan manifest library (Phase D).

Read/write `.rebuild-components.json` run-plan with atomic writes + file locking (RT2-F5).
Path canonicalization + validation on every read (no `..`, must stay under project_root).
SHA verification when status==done (manifest tamper guard).

Signal→field: manifest entry `path` (relative, guarded) → component status tracking.
File-locking helpers live in _manifest_lock_lib (split for size — RT2 <200 lines rule).
Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

from _path_lib import component_name, _resolve_guarded
from _manifest_lock_lib import lock_file, unlock_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_entry_path(entry_path: str, project_root: str) -> None:
    """Raise ValueError if path is absolute, contains '..', or escapes project_root."""
    if os.path.isabs(entry_path):
        raise ValueError(f"Manifest entry path must be relative, got: {entry_path!r}")
    if ".." in entry_path.replace("\\", "/").split("/"):
        raise ValueError(f"Manifest entry path contains '..': {entry_path!r}")
    _resolve_guarded(os.path.join(project_root, entry_path), project_root)


def _sha256_file(path: str) -> str:
    """SHA-256 hex digest of a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write_json(path: str, data: Any) -> None:
    """Write JSON atomically via tmp → os.replace."""
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    dir_ = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix="_manifest_", suffix=".json.tmp", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# emit_manifest
# ---------------------------------------------------------------------------

def emit_manifest(path: str, components: list[dict[str, Any]], project_root: str) -> None:
    """Write a fresh run-plan manifest from detect's components[].

    PREFLIGHT COLLISION CHECK (RT2-F14): two entries producing the same
    component_name → raise ValueError BEFORE writing anything.
    Writes atomically (tmp → os.replace); no lock needed (single writer at emit time).
    """
    seen: dict[str, str] = {}
    entries = []
    for comp in components:
        cpath = comp["path"]
        name = component_name(cpath)
        if not name:
            raise ValueError(f"component_name empty for path: {cpath!r}")
        if name in seen:
            raise ValueError(
                f"Component name collision: {seen[name]!r} and {cpath!r} both derive "
                f"{name!r} (RT2-F14). Rename one sub-repo path."
            )
        seen[name] = cpath
        # Reused components carry extra provenance fields and keep status:"reused".
        is_reused = comp.get("status") == "reused"
        entry: dict[str, Any] = {
            "path": cpath, "name": name,
            "profile": comp.get("profile", ""), "role": comp.get("role", ""),
            "group": comp.get("group"),
            "size_est": comp.get("size_est", 0),
            "timeout_hint": comp.get("timeout_hint", 3600),
            "max_loc": comp.get("max_loc", 0),
            "status": "reused" if is_reused else "pending",
            "sha": None, "fail_reason": None,
            "updated_at": _now_iso(),
        }
        if is_reused:
            entry["docs_path"] = comp.get("docs_path", "")
            entry["source_sha"] = comp.get("source_sha", "")
            entry["is_git_root"] = bool(comp.get("is_git_root", False))
        entries.append(entry)
    _atomic_write_json(path, entries)


# ---------------------------------------------------------------------------
# shared-layer sidecar (Phase 03)
# ---------------------------------------------------------------------------
#
# The component manifest is a JSON ARRAY (load_manifest raises on anything else, and 4 consumers
# + tests assume a list). Wrapping it in a `{components, shared}` object would break all of them
# (RT-Finding 1 BLOCKER). So shared-layer discovery lives in a SIDECAR file next to the manifest:
# `<manifest-stem>-shared.json` (e.g. `.rebuild-components-shared.json`). A run with no sidecar
# (or older runs) → shared == [] → the component manifest is byte-identical to today.

def shared_sidecar_path(manifest_path: str) -> str:
    """Sidecar path for a manifest path: insert `-shared` before the extension."""
    base, ext = os.path.splitext(manifest_path)
    return f"{base}-shared{ext or '.json'}"


def emit_shared_sidecar(path: str, shared: list[dict[str, Any]], project_root: str) -> None:
    """Write the shared-layer sidecar (atomic). Each entry: {path, kind, label}.

    `path` runs through the same `_validate_entry_path` guard as manifest entries (no `..`, must
    stay under project_root). `path` here is the SIDECAR path, not the manifest path.
    """
    entries = []
    for s in shared:
        spath = s["path"]
        _validate_entry_path(spath, project_root)
        entries.append({
            "path": spath,
            "kind": s.get("kind", "source"),
            "label": s.get("label", os.path.basename(spath.rstrip("/"))),
        })
    _atomic_write_json(path, entries)


def load_shared_sidecar(path: str, project_root: str = "") -> list[dict[str, Any]]:
    """Load + validate the shared-layer sidecar; missing file → []."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)
    if not isinstance(entries, list):
        raise ValueError(f"Shared sidecar must be a JSON array, got: {type(entries)}")
    for entry in entries:
        if "path" not in entry:
            raise ValueError(f"Shared sidecar entry missing 'path': {entry!r}")
        if project_root:
            _validate_entry_path(entry["path"], project_root)
    return entries


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------

def load_manifest(path: str, project_root: str = "") -> list[dict[str, Any]]:
    """Load and validate manifest; raise on path traversal or done-without-sha."""
    with open(path, encoding="utf-8") as fh:
        entries = json.load(fh)
    if not isinstance(entries, list):
        raise ValueError(f"Manifest must be a JSON array, got: {type(entries)}")
    for entry in entries:
        if "path" not in entry:
            raise ValueError(f"Manifest entry missing 'path': {entry!r}")
        if project_root:
            _validate_entry_path(entry["path"], project_root)
        # Only "done" requires a sha; "reused" has no digest yet so sha is allowed null.
        if entry.get("status") == "done" and not entry.get("sha"):
            raise ValueError(
                f"Manifest entry status=done but sha is null: {entry['path']!r}"
            )
    return entries


# ---------------------------------------------------------------------------
# next_pending / mark_done / mark_failed
# ---------------------------------------------------------------------------

def next_pending(manifest: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return first entry with status=='pending', or None."""
    for entry in manifest:
        if entry.get("status") == "pending":
            return entry
    return None


def mark_done(path: str, comp_path: str, sha: str) -> None:
    """Atomically mark a component done + store its digest sha (RT2-F5)."""
    if not sha:
        raise ValueError(f"sha required when marking done (path={comp_path!r})")
    _locked_update(path, comp_path, {"status": "done", "sha": sha, "fail_reason": None})


def mark_failed(path: str, comp_path: str, reason: str) -> None:
    """Atomically mark a component failed with a reason string."""
    _locked_update(path, comp_path, {"status": "failed", "sha": None, "fail_reason": reason})


def _locked_update(manifest_path: str, comp_path: str, updates: dict[str, Any]) -> None:
    """Exclusive-locked read-modify-write of one manifest entry (RT2-F5)."""
    lock_path = manifest_path + ".lock"
    lock_fd = open(lock_path, "a", encoding="utf-8")
    try:
        lock_file(lock_fd)
        with open(manifest_path, encoding="utf-8") as fh:
            entries = json.load(fh)
        found = False
        for entry in entries:
            if entry.get("path") == comp_path:
                entry.update(updates)
                entry["updated_at"] = _now_iso()
                found = True
                break
        if not found:
            raise ValueError(f"No manifest entry with path={comp_path!r}")
        _atomic_write_json(manifest_path, entries)
    finally:
        unlock_file(lock_fd)
        lock_fd.close()
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# verify_sha
# ---------------------------------------------------------------------------

def verify_sha(manifest_path: str, comp_path: str, digest_file: str) -> bool:
    """Return True iff stored sha matches the digest file on disk."""
    with open(manifest_path, encoding="utf-8") as fh:
        entries = json.load(fh)
    for entry in entries:
        if entry.get("path") == comp_path:
            if entry.get("status") != "done":
                return False
            return (entry.get("sha") or "") == _sha256_file(digest_file)
    return False
