#!/usr/bin/env python3
"""Structural extractor — COBOL CRUD/data (Phase 05, Track C).

Router-independent: does not touch extract_cobol_screen.py. Per `.cbl`/`.cob`/`.cpy`,
_cobol_unit_parse_lib.parse_file combines:
  - _cobol_data_lib: FILE-CONTROL/FD symbol table + OPEN-mode/ACCESS-MODE-gated
    WRITE/READ/REWRITE/DELETE -> C/R/U/D, datasets -> db_objects kind: "dataset".
  - _cobol_sql_lib: EXEC SQL...END-EXEC + cursor pass -> db_ops, SQL tables -> db_objects
    kind: "table"; EXECUTE IMMEDIATE/dynamic SQL -> confidence low + [UNVERIFIED].
under one byte-cap/timeout/exit-0-always guard (see that module for the fix 5/9 detail).

Emits the SAME neutral digest shape as extract_data_flow.py (units[].db_ops) and
extract_sql_schema.py (db_objects), via write_digest_atomic's shard_name override so
generation (SKILL.md) reads the canonical shard filenames unchanged while
update_manifest registers this extractor under its own key ("extract_cobol_data").
Only one data extractor runs per profile -> no clobber.

Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _cobol_unit_parse_lib import parse_file
from _extractor_lib import (
    is_extractor_completed,
    source_tree_hash,
    update_manifest,
    write_digest_atomic,
)

EXTRACTOR_NAME = "extract_cobol_data"
_DATA_FLOW_SHARD = "extract_data_flow"
_SQL_SCHEMA_SHARD = "extract_sql_schema"

_SOURCE_GLOBS = ["*.cbl", "*.cob", "*.cpy"]
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__", "target",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}


def extract(
    root: str | Path,
    plan_dir: str | Path,
    encoding: str = "utf-8",
    fallback: str = "latin-1",
    file_cap: int = 100_000,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the COBOL data extraction over root. Returns (data_flow_digest, sql_schema_digest)."""
    root_p = Path(root).resolve()
    plan_p = Path(plan_dir).resolve()

    units: list[dict[str, Any]] = []
    all_db_objects: list[dict[str, Any]] = []
    all_warnings: list[str] = []
    file_count = 0
    error_count = 0

    for dirpath, dirnames, filenames in os.walk(str(root_p), followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if file_count >= file_cap:
                all_warnings.append("file_cap_reached")
                break
            if not any(fnmatch.fnmatch(fn.lower(), g) for g in _SOURCE_GLOBS):
                continue

            full_path = Path(dirpath) / fn
            file_count += 1

            try:
                unit, objs, fw = parse_file(full_path, root_p, encoding, fallback)
            except Exception as e:  # belt-and-suspenders: exit-0-always at the walk level too
                unit, objs = None, []
                fw = [f"parse_error: {full_path.relative_to(root_p)}: {e}"]

            if any(w.startswith(("parse_timeout", "read_error", "parse_error")) for w in fw):
                error_count += 1
            if unit is not None:
                units.append(unit)
            all_db_objects.extend(objs)
            all_warnings.extend(fw)
        else:
            continue
        break  # file_cap hit

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tree_hash = source_tree_hash(root_p, _SOURCE_GLOBS)

    data_flow_digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": generated_at,
        "source_tree_hash": tree_hash,
        "units": units,
        "db_objects": [],
        "warnings": all_warnings,
    }
    sql_schema_digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": generated_at,
        "source_tree_hash": tree_hash,
        "units": [],
        "db_objects": all_db_objects,
        "warnings": all_warnings,
    }

    write_digest_atomic(plan_p, EXTRACTOR_NAME, data_flow_digest, shard_name=_DATA_FLOW_SHARD)
    write_digest_atomic(plan_p, EXTRACTOR_NAME, sql_schema_digest, shard_name=_SQL_SCHEMA_SHARD)
    update_manifest(plan_p, EXTRACTOR_NAME, file_count, error_count)
    return data_flow_digest, sql_schema_digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Structural extractor: COBOL file-I/O + EXEC SQL CRUD -> data-flow/sql-schema digest shards.",
    )
    parser.add_argument("--root", required=True, help="Project root to scan.")
    parser.add_argument("--plan-dir", required=True, help="Active plan directory.")
    parser.add_argument("--encoding", default="utf-8", help="Primary source encoding.")
    parser.add_argument("--fallback", default="latin-1", help="Fallback encoding.")
    parser.add_argument("--file-cap", type=int, default=100_000)
    args = parser.parse_args(argv)

    plan_p = Path(args.plan_dir).resolve()

    try:
        if is_extractor_completed(plan_p, EXTRACTOR_NAME):
            print(json.dumps({"status": "skipped", "reason": "already completed"}))
            return 0
        data_flow_digest, sql_schema_digest = extract(
            args.root, plan_p, args.encoding, args.fallback, args.file_cap
        )
        print(json.dumps({
            "status": "ok",
            "units": len(data_flow_digest["units"]),
            "db_objects": len(sql_schema_digest["db_objects"]),
            "warnings": len(data_flow_digest["warnings"]),
        }))
    except Exception as e:  # exit-0-always is enforced at the CLI boundary too
        print(json.dumps({"status": "error", "warning": f"extractor_failure: {e}"}), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
