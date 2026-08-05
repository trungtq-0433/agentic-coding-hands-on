#!/usr/bin/env python3
"""Structural extractor — SQL/DDL schema (Phase B).

Parses DDL across source files → db_objects digest shard.
Handles: CREATE TABLE/VIEW/SEQUENCE/TRIGGER and
         CREATE [OR REPLACE] PROCEDURE/PACKAGE/FUNCTION.

Exit code: always 0 (advisory). Per-file parse errors are [WARN], never crashes.
Writes: plans/<active>/artifacts/_digest_extract_sql_schema.json (atomic)
        plans/<active>/artifacts/_extraction-manifest.json (atomic update)

Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure scripts/ is importable when run directly
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _extractor_lib import (
    decode_source,
    is_extractor_completed,
    source_tree_hash,
    update_manifest,
    write_digest_atomic,
)
from _sql_parse_lib import (
    DbObject,
    extract_inline_columns,
    parse_column_line,
    parse_ddl_line,
    scrub_credentials,
)

EXTRACTOR_NAME = "extract_sql_schema"

_DDL_GLOBS = ["*.sql", "*.ddl", "*.pks", "*.pkb", "*.trg", "*.seq", "*.vw"]
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}

# Per-file timeouts
_FILE_TIMEOUT_S = 30
_FILE_LINE_CEILING = 50_000   # non-POSIX fallback: skip after this many lines


# ---------------------------------------------------------------------------
# Timeout helpers
# ---------------------------------------------------------------------------

class _ParseTimeout(Exception):
    pass


def _alarm_handler(signum: int, frame: object) -> None:  # noqa: ANN001
    raise _ParseTimeout


_HAS_SIGALRM = hasattr(signal, "SIGALRM")
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB — skip pathologically large source before reading


# ---------------------------------------------------------------------------
# Per-file DDL parser
# ---------------------------------------------------------------------------

def _parse_file(
    path: Path,
    root: Path,
    primary: str,
    fallback: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Parse a single file for DDL objects.

    Returns (db_objects, file_warnings, partial_warnings).
    db_objects: list of serialisable dicts.
    """
    rel = str(path.relative_to(root))
    warnings: list[str] = []

    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            warnings.append(f"skipped_oversized: {rel} exceeds "
                            f"{_MAX_FILE_BYTES // (1024 * 1024)}MB")
            return [], warnings, []
    except OSError as e:
        warnings.append(f"stat_error: {rel}: {e}")
        return [], warnings, []

    try:
        text, decode_warns = decode_source(path, primary, fallback)
        warnings.extend(decode_warns)
    except OSError as e:
        warnings.append(f"read_error: {rel}: {e}")
        return [], warnings, []

    db_objects: list[dict[str, Any]] = []
    current_obj: DbObject | None = None
    current_cols: list[str] = []
    inside_table = False

    lines = text.splitlines()

    def _process(lines_iter: list[str]) -> None:
        nonlocal current_obj, current_cols, inside_table
        for line_no, raw_line in enumerate(lines_iter, start=1):
            scrubbed, redacted = scrub_credentials(raw_line)
            citation = f"{rel}:{line_no}"

            if redacted:
                warnings.append(f"potential_credential_in_citation: {citation}")

            # Detect end of table body
            if inside_table and re.match(r'^\s*\)', scrubbed):
                inside_table = False
                if current_obj is not None:
                    obj_dict = {
                        "kind": current_obj.kind,
                        "name": current_obj.name,
                        "columns": list(current_cols),
                        "citation": current_obj.citation,
                    }
                    db_objects.append(obj_dict)
                    current_obj = None
                    current_cols = []
                continue

            # Accumulate columns inside CREATE TABLE
            if inside_table:
                col = parse_column_line(raw_line)
                if col:
                    current_cols.append(col)
                continue

            # Try DDL detection
            obj, new_inside = parse_ddl_line(scrubbed, line_no, rel)
            if obj is not None:
                # Flush any incomplete previous object
                if current_obj is not None:
                    obj_dict = {
                        "kind": current_obj.kind,
                        "name": current_obj.name,
                        "columns": list(current_cols),
                        "citation": current_obj.citation,
                    }
                    db_objects.append(obj_dict)
                current_obj = obj
                current_cols = []
                if new_inside:
                    # Single-line table `CREATE TABLE x (...);` — the column-list paren balances
                    # on this same line, so flush inline and DO NOT enter multi-line table mode
                    # (otherwise inside_table never resets and later statements get swallowed).
                    inline_cols, closed = extract_inline_columns(scrubbed)
                    if closed:
                        db_objects.append({
                            "kind": obj.kind,
                            "name": obj.name,
                            "columns": inline_cols,
                            "citation": obj.citation,
                        })
                        current_obj = None
                        current_cols = []
                    else:
                        inside_table = True
                        current_cols = inline_cols  # partial columns seen on the opening line
                else:
                    # Non-table objects are single-line → flush immediately
                    obj_dict = {
                        "kind": obj.kind,
                        "name": obj.name,
                        "columns": [],
                        "citation": obj.citation,
                    }
                    db_objects.append(obj_dict)
                    current_obj = None

    if _HAS_SIGALRM:
        old = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(_FILE_TIMEOUT_S)
        try:
            _process(lines)
        except _ParseTimeout:
            warnings.append(f"parse_timeout: {rel}")
            db_objects.clear()
            current_obj = None
            current_cols = []
            inside_table = False
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        # Non-POSIX fallback: line/byte ceiling
        if len(lines) > _FILE_LINE_CEILING:
            warnings.append(f"parse_timeout: {rel}")
        else:
            _process(lines)

    # Flush trailing open object (e.g. file ends without closing paren)
    if current_obj is not None:
        db_objects.append({
            "kind": current_obj.kind,
            "name": current_obj.name,
            "columns": list(current_cols),
            "citation": current_obj.citation,
        })

    return db_objects, warnings, []


# ---------------------------------------------------------------------------
# Main extraction logic
# ---------------------------------------------------------------------------

def extract(
    root: str | Path,
    plan_dir: str | Path,
    encoding: str = "utf-8",
    fallback: str = "latin-1",
    file_cap: int = 100_000,
) -> dict[str, Any]:
    """Run DDL extraction over root. Returns the digest dict."""
    root_p = Path(root).resolve()
    plan_p = Path(plan_dir).resolve()

    all_db_objects: list[dict[str, Any]] = []
    all_warnings: list[str] = []
    file_count = 0
    error_count = 0

    for dirpath, dirnames, filenames in os.walk(str(root_p), followlinks=False):
        dirnames[:] = [
            d for d in dirnames
            if d not in _SKIP_DIRS and not d.startswith(".")
        ]
        for fn in filenames:
            if file_count >= file_cap:
                all_warnings.append("file_cap_reached")
                break
            # Case-insensitive: case-sensitive filesystems (Linux) report .SQL/.PAS
            # uppercase extensions that lowercase globs would otherwise miss.
            if not any(fnmatch.fnmatch(fn.lower(), g) for g in _DDL_GLOBS):
                continue

            full_path = Path(dirpath) / fn
            file_count += 1

            db_objs, fw, _ = _parse_file(full_path, root_p, encoding, fallback)
            if any(w.startswith("parse_timeout") or w.startswith("read_error") for w in fw):
                error_count += 1
            all_db_objects.extend(db_objs)
            all_warnings.extend(fw)

        else:
            continue
        break  # file_cap hit in inner loop

    digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_tree_hash": source_tree_hash(root_p, _DDL_GLOBS),
        "units": [],
        "db_objects": all_db_objects,
        "warnings": all_warnings,
    }

    write_digest_atomic(plan_p, EXTRACTOR_NAME, digest)
    update_manifest(plan_p, EXTRACTOR_NAME, file_count, error_count)
    return digest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Structural extractor: SQL/DDL schema → db_objects digest shard.",
    )
    parser.add_argument("--root", required=True, help="Project root to scan.")
    parser.add_argument("--plan-dir", required=True, help="Active plan directory.")
    parser.add_argument("--encoding", default="utf-8", help="Primary source encoding.")
    parser.add_argument("--fallback", default="latin-1", help="Fallback encoding.")
    parser.add_argument("--file-cap", type=int, default=100_000)
    args = parser.parse_args(argv)

    plan_p = Path(args.plan_dir).resolve()

    # RT-F11: resume — skip if already completed
    if is_extractor_completed(plan_p, EXTRACTOR_NAME):
        print(json.dumps({"status": "skipped", "reason": "already completed"}))
        return 0

    digest = extract(args.root, plan_p, args.encoding, args.fallback, args.file_cap)
    print(json.dumps({
        "status": "ok",
        "db_objects": len(digest["db_objects"]),
        "warnings": len(digest["warnings"]),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
