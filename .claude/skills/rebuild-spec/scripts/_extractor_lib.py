#!/usr/bin/env python3
"""Shared helpers for structural extractors (Phase B).

Provides:
- decode_source(path, primary, fallback) — encoding-aware file reader
- source_tree_hash(root, globs)           — sha256 fingerprint of source tree
- write_digest_atomic(plan_dir, name, d)  — atomic shard write
- update_manifest(plan_dir, name, ...)    — atomic manifest read-modify-write

os.walk uses followlinks=False + a hard file cap throughout.
Stdlib only.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Hard cap on files walked during tree hash — avoids surprises on huge monorepos.
DEFAULT_WALK_FILE_CAP = 100_000

# ---------------------------------------------------------------------------
# decode_source
# ---------------------------------------------------------------------------

def decode_source(path: str | Path, primary: str, fallback: str) -> tuple[str, list[str]]:
    """Read a source file with encoding-safe fallback chain.

    Tries:
      1. primary encoding (strict)
      2. fallback encoding (strict)
      3. primary encoding with errors="replace"

    Returns (text, warnings) where warnings may contain
    "decode_fallback: <path>" if the primary encoding failed.
    """
    p = Path(path)
    warnings: list[str] = []

    # Step 1: try primary
    try:
        return p.read_text(encoding=primary, errors="strict"), warnings
    except (UnicodeDecodeError, UnicodeError):
        pass

    # Step 2: try fallback
    if fallback and fallback != primary:
        try:
            text = p.read_text(encoding=fallback, errors="strict")
            warnings.append(f"decode_fallback: {p}")
            return text, warnings
        except (UnicodeDecodeError, UnicodeError):
            pass

    # Step 3: lossy replace
    warnings.append(f"decode_fallback: {p}")
    return p.read_text(encoding=primary, errors="replace"), warnings


# ---------------------------------------------------------------------------
# source_tree_hash
# ---------------------------------------------------------------------------

def source_tree_hash(
    root: str | Path,
    globs: list[str],
    file_cap: int = DEFAULT_WALK_FILE_CAP,
) -> str:
    """SHA-256 of sorted (relative-path + str(mtime)) entries matching globs.

    followlinks=False prevents symlink loops. Capped at file_cap files.
    """
    root_p = Path(root).resolve()
    _SKIP_DIRS = {
        "node_modules", "vendor", "dist", "build", "__pycache__", "target",
        ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
    }
    entries: list[str] = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(str(root_p), followlinks=False):
        dirnames[:] = [
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for fn in filenames:
            count += 1
            if count > file_cap:
                break
            # Case-insensitive: case-sensitive filesystems (Linux) report uppercase
            # extensions (.SQL/.PAS) that lowercase globs would otherwise miss.
            if not globs or any(fnmatch.fnmatch(fn.lower(), g) for g in globs):
                full = Path(dirpath) / fn
                try:
                    mtime = full.stat().st_mtime
                except OSError:
                    mtime = 0.0
                rel = str(full.relative_to(root_p))
                entries.append(f"{rel}\t{mtime}")
        if count > file_cap:
            break

    payload = "\n".join(sorted(entries)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Artifact directory helper
# ---------------------------------------------------------------------------

def _artifacts_dir(plan_dir: str | Path) -> Path:
    d = Path(plan_dir) / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# write_digest_atomic
# ---------------------------------------------------------------------------

def write_digest_atomic(
    plan_dir: str | Path,
    extractor_name: str,
    digest_dict: dict[str, Any],
    shard_name: str | None = None,
) -> Path:
    """Write _digest_<shard_name or extractor_name>.json atomically via tmp → os.replace.

    `shard_name` (Phase 01, additive) lets an extractor write to a canonical shard filename
    that differs from its own script name (e.g. a data extractor writing to the shared
    `_digest_data_flow.json` shape while `update_manifest` still registers its own
    `extractor_name` key). Default `None` preserves current behavior: `_digest_<extractor_name>.json`.

    Returns the final Path.
    """
    artifacts = _artifacts_dir(plan_dir)
    shard = shard_name or extractor_name
    target = artifacts / f"_digest_{shard}.json"
    payload = json.dumps(digest_dict, indent=2, ensure_ascii=False)

    fd, tmp_path = tempfile.mkstemp(
        prefix=f"_digest_{shard}_",
        suffix=".json.tmp",
        dir=str(artifacts),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


# ---------------------------------------------------------------------------
# update_manifest
# ---------------------------------------------------------------------------

_MANIFEST_NAME = "_extraction-manifest.json"


def update_manifest(
    plan_dir: str | Path,
    extractor_name: str,
    file_count: int,
    error_count: int,
) -> None:
    """Atomic read-modify-write of _extraction-manifest.json.

    Sets manifest[extractor_name] = {completed, file_count, error_count, generated_at}.
    Uses tmp → os.replace for atomicity.
    """
    artifacts = _artifacts_dir(plan_dir)
    manifest_path = artifacts / _MANIFEST_NAME

    # Read existing (best-effort)
    manifest: dict[str, Any] = {}
    try:
        with open(str(manifest_path), encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    manifest[extractor_name] = {
        "completed": True,
        "file_count": file_count,
        "error_count": error_count,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    payload = json.dumps(manifest, indent=2, ensure_ascii=False)
    fd, tmp_path = tempfile.mkstemp(
        prefix="_manifest_",
        suffix=".json.tmp",
        dir=str(artifacts),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, str(manifest_path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def is_extractor_completed(plan_dir: str | Path, extractor_name: str) -> bool:
    """Return True if manifest marks this extractor completed:true."""
    artifacts = _artifacts_dir(plan_dir)
    manifest_path = artifacts / _MANIFEST_NAME
    try:
        with open(str(manifest_path), encoding="utf-8") as fh:
            manifest = json.load(fh)
        return bool(manifest.get(extractor_name, {}).get("completed", False))
    except (FileNotFoundError, json.JSONDecodeError):
        return False
