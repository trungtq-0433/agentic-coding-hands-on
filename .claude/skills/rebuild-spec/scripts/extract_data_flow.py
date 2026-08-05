#!/usr/bin/env python3
"""Structural extractor — data flow / CRUD operations (Phase B).

For each source unit, parses embedded SQL (Delphi inline SQL, generic ORM/SQL)
→ units[].db_ops {table, op, columns, line, citation, confidence}
   + parse_coverage {static_sql_found, dynamic_sql_detected, confidence}

Dynamic SQL (RT-F8): ops from units with dynamic SQL carry confidence=low.
Credential scrub (RT-F7) runs before any line enters a citation.
Markdown-safe identifiers (RT-F10).
Per-file timeout via signal.alarm (POSIX) or line ceiling (non-POSIX) (RT-F9).
Atomic digest shard + manifest (RT-F11). Exit 0 always (advisory).

Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from _sql_dml_lib import is_dynamic_sql_line, parse_dml_line
from _sql_parse_lib import scrub_credentials

EXTRACTOR_NAME = "extract_data_flow"

# Source globs to scan for embedded SQL / DML
_SOURCE_GLOBS = [
    "*.pas", "*.pp",        # Delphi / Pascal
    "*.sql", "*.ddl",       # raw SQL
    "*.pks", "*.pkb",       # Oracle package spec / body
    "*.py",                 # Python ORM / raw SQL
    "*.java",               # Java JDBC
    "*.cs",                 # C# ADO / EF
    "*.rb",                 # Ruby AR / raw SQL
    "*.php",                # PHP PDO
    "*.go",                 # Go database/sql
]

_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}

_FILE_TIMEOUT_S = 30
_FILE_LINE_CEILING = 50_000

_HAS_SIGALRM = hasattr(signal, "SIGALRM")
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB — skip pathologically large source before reading


class _ParseTimeout(Exception):
    pass


def _alarm_handler(signum: int, frame: object) -> None:  # noqa: ANN001
    raise _ParseTimeout


# ---------------------------------------------------------------------------
# Per-file unit parser
# ---------------------------------------------------------------------------

def _parse_file(
    path: Path,
    root: Path,
    primary: str,
    fallback: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse one source file for embedded DML.

    Returns (unit_dict | None, warnings).
    unit_dict matches the digest schema units[] entry.
    """
    rel = str(path.relative_to(root))
    warnings: list[str] = []

    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            warnings.append(f"skipped_oversized: {rel} exceeds "
                            f"{_MAX_FILE_BYTES // (1024 * 1024)}MB")
            return None, warnings
    except OSError as e:
        warnings.append(f"stat_error: {rel}: {e}")
        return None, warnings

    try:
        text, decode_warns = decode_source(path, primary, fallback)
        warnings.extend(decode_warns)
    except OSError as e:
        warnings.append(f"read_error: {rel}: {e}")
        return None, warnings

    db_ops: list[dict[str, Any]] = []
    static_sql_found = 0
    dynamic_sql_detected = False
    lines = text.splitlines()

    def _process(lines_iter: list[str]) -> None:
        nonlocal static_sql_found, dynamic_sql_detected

        for line_no, raw_line in enumerate(lines_iter, start=1):
            scrubbed, redacted = scrub_credentials(raw_line)
            citation = f"{rel}:{line_no}"

            if redacted:
                warnings.append(f"potential_credential_in_citation: {citation}")

            # Dynamic SQL detection (RT-F8)
            if is_dynamic_sql_line(raw_line):
                dynamic_sql_detected = True

            # DML parsing
            ops = parse_dml_line(scrubbed, line_no, rel)
            for op in ops:
                static_sql_found += 1
                confidence = op.confidence
                # If we've detected dynamic SQL anywhere in this file, downgrade
                db_ops.append({
                    "table": op.table,
                    "op": op.op,
                    "columns": list(op.columns),
                    "line": op.line,
                    "citation": op.citation,
                    "confidence": confidence,
                })

    timed_out = False
    if _HAS_SIGALRM:
        old = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(_FILE_TIMEOUT_S)
        try:
            _process(lines)
        except _ParseTimeout:
            warnings.append(f"parse_timeout: {rel}")
            db_ops.clear()
            static_sql_found = 0
            timed_out = True
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        if len(lines) > _FILE_LINE_CEILING:
            warnings.append(f"parse_timeout: {rel}")
            timed_out = True
        else:
            _process(lines)

    if timed_out:
        return None, warnings

    # RT-F8: downgrade confidence on all ops + flag unverified if dynamic SQL detected.
    if dynamic_sql_detected:
        for op_dict in db_ops:
            op_dict["confidence"] = "low"
            op_dict["unverified"] = True  # rendered as [UNVERIFIED] by the W1.b prose step

    # Determine unit-level coverage confidence (contract enum: high|medium|low).
    if dynamic_sql_detected:
        coverage_confidence = "low"
    elif static_sql_found > 0:
        coverage_confidence = "high"
    else:
        coverage_confidence = "medium"  # parsed cleanly but found no SQL — not "high" certainty

    unit: dict[str, Any] = {
        "path": rel,
        "uses": [],      # Delphi `uses` clause — not parsed here (separate pass)
        "db_ops": db_ops,
        "forms": [],     # Delphi form names — not parsed here
        "parse_coverage": {
            "static_sql_found": static_sql_found,
            "dynamic_sql_detected": dynamic_sql_detected,
            "confidence": coverage_confidence,
        },
    }
    return unit, warnings


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
    """Run data-flow extraction over root. Returns the digest dict."""
    root_p = Path(root).resolve()
    plan_p = Path(plan_dir).resolve()

    units: list[dict[str, Any]] = []
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
            if not any(fnmatch.fnmatch(fn.lower(), g) for g in _SOURCE_GLOBS):
                continue

            full_path = Path(dirpath) / fn
            file_count += 1

            unit, fw = _parse_file(full_path, root_p, encoding, fallback)
            if any(
                w.startswith("parse_timeout") or w.startswith("read_error")
                for w in fw
            ):
                error_count += 1
            if unit is not None:
                units.append(unit)
            all_warnings.extend(fw)

        else:
            continue
        break  # file_cap hit

    digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_tree_hash": source_tree_hash(root_p, _SOURCE_GLOBS),
        "units": units,
        "db_objects": [],   # populated by extract_sql_schema; empty here per contract
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
        description="Structural extractor: data-flow / CRUD ops → units digest shard.",
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
        "units": len(digest["units"]),
        "warnings": len(digest["warnings"]),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
