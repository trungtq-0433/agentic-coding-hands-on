#!/usr/bin/env python3
"""PROCEDURE DIVISION file-verb -> CRUD classification (companion to _cobol_data_lib.py).

Split out to honour the 200-LOC-per-file budget. Holds the READ/WRITE/REWRITE/DELETE
regexes and their legality-gated handlers -- WRITE->C, READ->R, REWRITE->U, DELETE->D.
OPEN/CLOSE are pure state (handled by the caller) and never reach this module.

Legality (never a false classification -- WARN + skip instead):
  - READ needs open_mode in {INPUT, I-O}.
  - WRITE needs open_mode in {OUTPUT, EXTEND, I-O}.
  - REWRITE needs open_mode == I-O, a prior READ in this open session, and an
    organization that is NOT LINE SEQUENTIAL.
  - DELETE needs open_mode == I-O and organization NOT LINE SEQUENTIAL.

WRITE/REWRITE address a *record* name (the FD's 01-level); READ/DELETE address the
*file* name directly -- `record_to_file` (built by the caller from FD->01 adjacency)
bridges the two.

Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

from _sql_parse_lib import sanitize_identifier

READ_RE = re.compile(r'^\s*READ\s+([A-Za-z][\w-]*)', re.IGNORECASE)
WRITE_RE = re.compile(r'^\s*WRITE\s+([A-Za-z][\w-]*)', re.IGNORECASE)
REWRITE_RE = re.compile(r'^\s*REWRITE\s+([A-Za-z][\w-]*)', re.IGNORECASE)
DELETE_RE = re.compile(r'^\s*DELETE\s+([A-Za-z][\w-]*)', re.IGNORECASE)

_OPEN_MODES_FOR_READ = {"INPUT", "I-O"}
_OPEN_MODES_FOR_WRITE = {"OUTPUT", "EXTEND", "I-O"}


def _emit(db_ops: list[dict[str, Any]], name: str, op: str, line_no: int, citation: str) -> None:
    db_ops.append({
        "table": sanitize_identifier(name), "op": op, "columns": [],
        "line": line_no, "citation": citation, "confidence": "high",
    })


def _resolve_write_target(name, symbols, record_to_file):
    file_name = record_to_file.get(name, name if name in symbols else None)
    return symbols.get(file_name) if file_name else None


def handle_read(name, line_no, rel, symbols, db_ops, warnings) -> None:
    citation = f"{rel}:{line_no}"
    sym = symbols.get(name)
    if sym is None:
        warnings.append(f"unknown_file_verb: READ {name} at {citation}")
        return
    if sym.open_mode not in _OPEN_MODES_FOR_READ:
        warnings.append(f"illegal_verb_for_mode: READ {name} open_mode={sym.open_mode} at {citation}")
        return
    sym.read_since_open = True
    _emit(db_ops, name, "R", line_no, citation)


def handle_write(name, line_no, rel, symbols, record_to_file, db_ops, warnings) -> None:
    citation = f"{rel}:{line_no}"
    sym = _resolve_write_target(name, symbols, record_to_file)
    if sym is None:
        warnings.append(f"unknown_file_verb: WRITE {name} at {citation}")
        return
    if sym.open_mode not in _OPEN_MODES_FOR_WRITE:
        warnings.append(f"illegal_verb_for_mode: WRITE {name} open_mode={sym.open_mode} at {citation}")
        return
    _emit(db_ops, sym.name, "C", line_no, citation)


def handle_rewrite(name, line_no, rel, symbols, record_to_file, db_ops, warnings) -> None:
    citation = f"{rel}:{line_no}"
    sym = _resolve_write_target(name, symbols, record_to_file)
    if sym is None:
        warnings.append(f"unknown_file_verb: REWRITE {name} at {citation}")
        return
    if sym.organization == "LINE SEQUENTIAL":
        warnings.append(f"illegal_verb_for_mode: REWRITE {name} on LINE SEQUENTIAL file at {citation}")
        return
    if sym.open_mode != "I-O" or not sym.read_since_open:
        warnings.append(f"illegal_verb_for_mode: REWRITE {name} without prior READ/OPEN I-O at {citation}")
        return
    _emit(db_ops, sym.name, "U", line_no, citation)


def handle_delete(name, line_no, rel, symbols, db_ops, warnings) -> None:
    citation = f"{rel}:{line_no}"
    sym = symbols.get(name)
    if sym is None:
        warnings.append(f"unknown_file_verb: DELETE {name} at {citation}")
        return
    if sym.organization == "LINE SEQUENTIAL" or sym.open_mode != "I-O":
        warnings.append(f"illegal_verb_for_mode: DELETE {name} open_mode={sym.open_mode} at {citation}")
        return
    _emit(db_ops, name, "D", line_no, citation)
