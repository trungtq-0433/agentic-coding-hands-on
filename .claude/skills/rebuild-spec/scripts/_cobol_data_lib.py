#!/usr/bin/env python3
"""COBOL file-I/O (FILE-CONTROL/FD/PROCEDURE DIVISION) pass for extract_cobol_data.py.

Builds a per-file symbol table joining SELECT/ASSIGN + FD, then walks PROCEDURE
DIVISION verb-by-verb via _cobol_verb_lib (WRITE/READ/REWRITE/DELETE -> C/R/U/D;
OPEN/CLOSE are state only, never classified as CRUD). EXEC SQL...END-EXEC spans
are skipped entirely (owned by _cobol_sql_lib.py).

OPEN handling [H1+H2]: lines are continuation-joined into one logical statement
first, then mode-split on INPUT/OUTPUT/I-O/EXTEND so each file token gets its own
preceding keyword's mode -- not the first one applied to every token. Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

from _cobol_dispatch_lib import is_comment_line
from _cobol_verb_lib import (
    DELETE_RE, READ_RE, REWRITE_RE, WRITE_RE,
    handle_delete, handle_read, handle_rewrite, handle_write,
)
from _sql_parse_lib import sanitize_identifier

_EXEC_SQL_START = re.compile(r'\bEXEC\s+SQL\b', re.IGNORECASE)
_END_EXEC = re.compile(r'\bEND-EXEC\b', re.IGNORECASE)

_SELECT_START = re.compile(r'^\s*SELECT\b', re.IGNORECASE)
_SELECT_NAME = re.compile(r'^\s*SELECT\s+(?:NOT\s+OPTIONAL\s+|OPTIONAL\s+)?([A-Za-z][\w-]*)', re.IGNORECASE)
_ASSIGN_KW = re.compile(r'\bASSIGN\b', re.IGNORECASE)
_LINE_SEQ = re.compile(r'\bORGANIZATION\s+(?:IS\s+)?LINE\s+SEQUENTIAL\b', re.IGNORECASE)
_ORG = re.compile(r'\bORGANIZATION\s+(?:IS\s+)?(SEQUENTIAL|INDEXED|RELATIVE)\b', re.IGNORECASE)
_ACCESS = re.compile(r'\bACCESS\s+(?:MODE\s+(?:IS\s+)?|IS\s+)?(SEQUENTIAL|RANDOM|DYNAMIC)\b', re.IGNORECASE)

_FD = re.compile(r'^\s*FD\s+([A-Za-z][\w-]*)', re.IGNORECASE)
_RECORD_01 = re.compile(r'^\s*01\s+([A-Za-z][\w-]*)', re.IGNORECASE)
_PROC_DIV = re.compile(r'^\s*PROCEDURE\s+DIVISION\b', re.IGNORECASE)

_OPEN_START = re.compile(r'^\s*OPEN\s+(.+)$', re.IGNORECASE)
_OPEN_MODE_KW = re.compile(r'\b(INPUT|OUTPUT|I-O|EXTEND)\b', re.IGNORECASE)
_CLOSE = re.compile(r'^\s*CLOSE\s+(.+)$', re.IGNORECASE)
_TOKEN = re.compile(r'[A-Za-z][\w-]*')

class FileSymbol:
    """Per-file state: FILE-CONTROL/FD facts + live OPEN/READ session state."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.organization: str | None = None
        self.access_mode = "SEQUENTIAL"  # COBOL default when no ACCESS clause given
        self.select_citation: str | None = None
        self.fd_seen = False
        self.open_mode: str | None = None
        self.read_since_open = False

def _known_tokens(text: str, symbols: dict[str, FileSymbol]) -> list[str]:
    """Whitespace-delimited identifiers in `text` that are known file names."""
    out: list[str] = []
    for tok in _TOKEN.findall(text):
        name = tok.upper()
        if name in symbols and name not in out:
            out.append(name)
    return out

def _finish_select(buffer: list[str], start_line: int, rel: str, symbols: dict[str, FileSymbol], warnings: list[str]) -> None:
    joined = " ".join(b.strip() for b in buffer)
    if not _ASSIGN_KW.search(joined):
        return  # not a FILE-CONTROL SELECT (defensive; ASSIGN is mandatory in this clause)
    m = _SELECT_NAME.match(joined)
    if not m:
        warnings.append(f"unparsed_select: {rel}:{start_line}")
        return
    name = m.group(1).upper()
    sym = symbols.setdefault(name, FileSymbol(name))
    sym.select_citation = f"{rel}:{start_line}"
    if _LINE_SEQ.search(joined):
        sym.organization = "LINE SEQUENTIAL"
    else:
        om = _ORG.search(joined)
        if om:
            sym.organization = om.group(1).upper()
    am = _ACCESS.search(joined)
    if am:
        sym.access_mode = am.group(1).upper()

def _finish_open(buffer: list[str], symbols: dict[str, FileSymbol]) -> None:
    """[H1+H2] Mode-split a joined OPEN: each token gets its own preceding keyword's mode."""
    m = _OPEN_START.match(" ".join(b.strip() for b in buffer).rstrip("."))
    if not m:
        return
    mode = None
    for part in _OPEN_MODE_KW.split(m.group(1)):
        token = part.strip().upper()
        if token in ("INPUT", "OUTPUT", "I-O", "EXTEND"):
            mode = token
        elif mode:
            for name in _known_tokens(part, symbols):
                symbols[name].open_mode = mode
                symbols[name].read_since_open = False

def parse_file_verbs(lines: list[str], rel: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Parse FILE-CONTROL/FD/PROCEDURE DIVISION verbs -> (db_ops, dataset_objects, warnings)."""
    warnings: list[str] = []
    db_ops: list[dict[str, Any]] = []
    symbols: dict[str, FileSymbol] = {}
    record_to_file: dict[str, str] = {}
    pending_fd_file: str | None = None
    select_buffer: list[str] | None = None
    select_start_line = 0
    open_buffer: list[str] | None = None
    in_exec_sql = False

    for idx, raw in enumerate(lines):
        line_no = idx + 1
        if is_comment_line(raw) or not raw.strip():
            continue

        if in_exec_sql:
            if _END_EXEC.search(raw):
                in_exec_sql = False
            continue
        if _EXEC_SQL_START.search(raw):
            in_exec_sql = not bool(_END_EXEC.search(raw))
            continue

        if select_buffer is not None:
            select_buffer.append(raw)
            if raw.rstrip().endswith("."):
                _finish_select(select_buffer, select_start_line, rel, symbols, warnings)
                select_buffer = None
            continue
        if _SELECT_START.match(raw):
            select_buffer = [raw]
            select_start_line = line_no
            if raw.rstrip().endswith("."):
                _finish_select(select_buffer, select_start_line, rel, symbols, warnings)
                select_buffer = None
            continue

        if open_buffer is not None:
            open_buffer.append(raw)
            if raw.rstrip().endswith("."):
                _finish_open(open_buffer, symbols)
                open_buffer = None
            continue
        if _OPEN_START.match(raw):
            open_buffer = [raw]
            if raw.rstrip().endswith("."):
                _finish_open(open_buffer, symbols)
                open_buffer = None
            continue

        if _PROC_DIV.match(raw):
            pending_fd_file = None
            continue
        m = _FD.match(raw)
        if m:
            pending_fd_file = m.group(1).upper()
            if pending_fd_file in symbols:
                symbols[pending_fd_file].fd_seen = True
            continue
        m = _RECORD_01.match(raw)
        if m and pending_fd_file:
            record_to_file[m.group(1).upper()] = pending_fd_file
            continue

        m = _CLOSE.match(raw)
        if m:
            for name in _known_tokens(m.group(1), symbols):
                symbols[name].open_mode = None
                symbols[name].read_since_open = False
            continue
        for rx, handler, needs_rec in (
            (READ_RE, handle_read, False), (WRITE_RE, handle_write, True),
            (REWRITE_RE, handle_rewrite, True), (DELETE_RE, handle_delete, False),
        ):
            m = rx.match(raw)
            if not m:
                continue
            if needs_rec:
                handler(m.group(1).upper(), line_no, rel, symbols, record_to_file, db_ops, warnings)
            else:
                handler(m.group(1).upper(), line_no, rel, symbols, db_ops, warnings)
            break

    if select_buffer is not None:
        warnings.append(f"unterminated_select: {rel}:{select_start_line}")

    dataset_objects = [
        {
            "kind": "dataset",
            "name": sanitize_identifier(name),
            "columns": [],
            "citation": sym.select_citation or f"{rel}:0",
        }
        for name, sym in symbols.items()
    ]
    return db_ops, dataset_objects, warnings
