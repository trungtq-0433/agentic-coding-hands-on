#!/usr/bin/env python3
"""Per-file parse guard for extract_cobol_data.py: byte cap, timeout, exit-0-always.

Split out to honour the 200-LOC-per-file budget. Wraps the two content passes
(_cobol_data_lib.parse_file_verbs + _cobol_sql_lib.parse_exec_sql) with:
  - [Red-team fix 9] per-file byte cap via path.stat().st_size BEFORE read.
  - Per-file timeout (signal.alarm on POSIX; line-count ceiling fallback elsewhere),
    mirroring extract_data_flow.py:148-156.
  - [Red-team fix 5] try/except Exception around the WHOLE guarded region -> a single
    `[WARN] parse_error: <path>` and skip, extending the timeout-only guard to ANY
    exception (never a crash, always exit 0).

Stdlib only.
"""
from __future__ import annotations

import signal
from pathlib import Path
from typing import Any

from _cobol_data_lib import parse_file_verbs
from _cobol_sql_lib import parse_exec_sql
from _extractor_lib import decode_source

_FILE_TIMEOUT_S = 30
_FILE_LINE_CEILING = 50_000
_HAS_SIGALRM = hasattr(signal, "SIGALRM")
_MAX_FILE_BYTES = 10 * 1024 * 1024  # [Red-team fix 9]


class _ParseTimeout(Exception):
    pass


def _alarm_handler(signum: int, frame: object) -> None:  # noqa: ANN001
    raise _ParseTimeout


def parse_file(
    path: Path, root: Path, primary: str, fallback: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    """Parse one COBOL unit. Returns (unit_dict | None, db_objects, warnings).

    Never raises: any exception (not just a timeout) becomes `[WARN] parse_error` and the
    file is skipped ([Red-team fix 5] — exit-0 ENFORCED, not merely asserted).
    """
    rel = str(path.relative_to(root))
    warnings: list[str] = []

    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            warnings.append(f"skipped_oversized: {rel} exceeds {_MAX_FILE_BYTES // (1024 * 1024)}MB")
            return None, [], warnings
    except OSError as e:
        warnings.append(f"stat_error: {rel}: {e}")
        return None, [], warnings

    try:
        text, decode_warns = decode_source(path, primary, fallback)
        warnings.extend(decode_warns)
    except OSError as e:
        warnings.append(f"read_error: {rel}: {e}")
        return None, [], warnings

    lines = text.splitlines()
    db_ops: list[dict[str, Any]] = []
    db_objects: list[dict[str, Any]] = []
    dynamic_detected = False
    static_count = 0

    def _run() -> None:
        nonlocal dynamic_detected, static_count
        file_ops, file_objs, file_warns = parse_file_verbs(lines, rel)
        warnings.extend(file_warns)
        db_ops.extend(file_ops)
        db_objects.extend(file_objs)
        static_count += len(file_ops)

        sql_ops, sql_objs, sql_warns, dyn = parse_exec_sql(lines, rel)
        warnings.extend(sql_warns)
        db_ops.extend(sql_ops)
        db_objects.extend(sql_objs)
        static_count += len(sql_ops)
        dynamic_detected = dyn

    timed_out = False
    try:
        if _HAS_SIGALRM:
            old = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(_FILE_TIMEOUT_S)
            try:
                _run()
            except _ParseTimeout:
                warnings.append(f"parse_timeout: {rel}")
                db_ops.clear()
                db_objects.clear()
                timed_out = True
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        else:
            if len(lines) > _FILE_LINE_CEILING:
                warnings.append(f"parse_timeout: {rel}")
                timed_out = True
            else:
                _run()
    except Exception as e:  # [Red-team fix 5] ANY exception -> WARN, never a crash.
        warnings.append(f"parse_error: {rel}: {e}")
        return None, [], warnings

    if timed_out:
        return None, [], warnings

    if dynamic_detected:
        for op in db_ops:
            op["confidence"] = "low"
            op["unverified"] = True  # rendered as [UNVERIFIED] downstream
        coverage_confidence = "low"
    elif static_count > 0:
        coverage_confidence = "high"
    else:
        coverage_confidence = "medium"

    unit: dict[str, Any] = {
        "path": rel,
        "uses": [],
        "db_ops": db_ops,
        "forms": [],
        "parse_coverage": {
            "static_sql_found": static_count,
            "dynamic_sql_detected": dynamic_detected,
            "confidence": coverage_confidence,
        },
    }
    return unit, db_objects, warnings
