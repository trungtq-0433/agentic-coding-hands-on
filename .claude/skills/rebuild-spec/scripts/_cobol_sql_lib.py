#!/usr/bin/env python3
r"""EXEC SQL...END-EXEC pass for extract_cobol_data.py (dialect-agnostic: DB2/Pro*COBOL shape).

Blocks are non-nested and lexically simple: accumulate from `EXEC SQL` to `END-EXEC`,
strip `:`-host-var markers (map to WORKING-STORAGE names), then classify:
  - static SELECT/INSERT/UPDATE/DELETE  -> reuse _sql_dml_lib.parse_dml_line (DRY)
  - CREATE TABLE/VIEW/...              -> reuse _sql_parse_lib.parse_ddl_line (DRY)
  - DECLARE cursor CURSOR FOR SELECT.. -> register cursor->table (mirrors the file-join
                                          pattern keyed on cursor-name); no CRUD op yet
  - FETCH cursor                       -> R op against the cursor's registered table
  - OPEN/CLOSE cursor                  -> state only, same as file OPEN/CLOSE (no-op:
                                          falls through every check below, emits nothing)
  - EXECUTE IMMEDIATE / dynamic SQL    -> [AMBIGUOUS]/low confidence via the caller's
                                          dynamic_sql_detected flag; NEVER fabricate a table

Credential scrub (RT-F7) runs on every raw line before it can enter a citation.

Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

from _cobol_dispatch_lib import is_comment_line
from _sql_dml_lib import parse_dml_line
from _sql_parse_lib import (
    extract_inline_columns,
    parse_ddl_line,
    sanitize_identifier,
    scrub_credentials,
)

_EXEC_SQL_START = re.compile(r'\bEXEC\s+SQL\b', re.IGNORECASE)
_END_EXEC = re.compile(r'\bEND-EXEC\b', re.IGNORECASE)
_EXEC_SQL_BODY = re.compile(r'\bEXEC\s+SQL\b(.*)\bEND-EXEC\b', re.IGNORECASE)

_DECLARE_CURSOR = re.compile(r'\bDECLARE\s+([\w-]+)\s+CURSOR\s+FOR\b', re.IGNORECASE)
_FETCH_CURSOR = re.compile(r'\bFETCH\s+([\w-]+)\b', re.IGNORECASE)
_EXECUTE_IMMEDIATE = re.compile(r'\bEXECUTE\s+IMMEDIATE\b', re.IGNORECASE)
_FROM_TABLE = re.compile(r'\bFROM\s+(\w+)', re.IGNORECASE)
_HOST_VAR = re.compile(r':(\w+)')

_MAX_BLOCK_CHARS = 4096  # RT-F9: bounded scan, never an unbounded/greedy multiline match


def _strip_host_vars(text: str) -> str:
    """Strip `:` host-var markers so downstream table/column regexes see plain names.

    Quote-aware: a colon inside a single-quoted SQL string/time literal (e.g. the
    `'08:00:00'` in `WHERE ORDER_TIME > '08:00:00'`) is data, not a host-var marker,
    and must survive unstripped -- a naive whole-string regex sub corrupts it."""
    out: list[str] = []
    in_quote = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
            out.append(ch)
            i += 1
            continue
        if not in_quote:
            m = _HOST_VAR.match(text, i)
            if m:
                out.append(m.group(1))
                i = m.end()
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _mask_for_boundary_scan(line: str) -> str:
    """[C2] Quote-aware scan for boundary detection ONLY: blank `--` SQL line comments
    and single-quoted literal contents so 'END-EXEC'/'EXEC SQL' inside either can't
    spuriously open/close a block (classification still uses the raw, unmasked line)."""
    out: list[str] = []
    in_quote = False
    i, n = 0, len(line)
    while i < n:
        if not in_quote and line[i:i + 2] == "--":
            break
        ch = line[i]
        if ch == "'":
            in_quote = not in_quote
            out.append(ch)
        else:
            out.append("#" if in_quote else ch)
        i += 1
    return "".join(out)


def _handle_block(
    block_lines: list[str],
    start_line: int,
    rel: str,
    cursor_table: dict[str, str | None],
    db_ops: list[dict[str, Any]],
    db_objects: list[dict[str, Any]],
    warnings: list[str],
) -> bool:
    """Classify one EXEC SQL...END-EXEC block. Returns True iff it is dynamic SQL."""
    citation = f"{rel}:{start_line}"
    scrubbed_lines = []
    for raw in block_lines:
        s, redacted = scrub_credentials(raw)
        if redacted:
            warnings.append(f"potential_credential_in_citation: {citation}")
        scrubbed_lines.append(s)
    joined = _strip_host_vars(" ".join(scrubbed_lines))[:_MAX_BLOCK_CHARS]
    m_body = _EXEC_SQL_BODY.search(joined)
    body = m_body.group(1).strip() if m_body else joined

    if _EXECUTE_IMMEDIATE.search(body):
        warnings.append(f"dynamic_sql_detected: {citation}")
        return True

    m = _DECLARE_CURSOR.search(body)
    if m:
        name = m.group(1).upper()
        tm = _FROM_TABLE.search(body)
        table = sanitize_identifier(tm.group(1)) if tm else None
        cursor_table[name] = table
        if table is None:
            warnings.append(f"unresolved_cursor_source: {name} at {citation}")
        return False

    m = _FETCH_CURSOR.search(body)
    if m:
        name = m.group(1).upper()
        table = cursor_table.get(name)
        if table is None:
            warnings.append(f"unknown_cursor: {name} at {citation}")
            return False
        db_ops.append({
            "table": table, "op": "R", "columns": [], "line": start_line,
            "citation": citation, "confidence": "high",
        })
        return False

    # OPEN/CLOSE <cursor-name> — state only, same treatment as a file OPEN/CLOSE: no DDL
    # keyword and no DML keyword matches below, so this naturally falls through as a no-op.

    obj, _inside = parse_ddl_line(body, start_line, rel)
    if obj is not None:
        cols, _closed = extract_inline_columns(body)
        db_objects.append({"kind": obj.kind, "name": obj.name, "columns": cols, "citation": obj.citation})
        return False

    for op in parse_dml_line(body, start_line, rel):
        db_ops.append({
            "table": op.table, "op": op.op, "columns": list(op.columns),
            "line": op.line, "citation": op.citation, "confidence": op.confidence,
        })
    return False


def parse_exec_sql(lines: list[str], rel: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], bool]:
    """Parse every EXEC SQL...END-EXEC block (non-nested) in one COBOL unit.
    Returns (db_ops, db_objects, warnings, dynamic_detected)."""
    db_ops: list[dict[str, Any]] = []
    db_objects: list[dict[str, Any]] = []
    warnings: list[str] = []
    cursor_table: dict[str, str | None] = {}
    dynamic_detected = False

    block: list[str] | None = None
    block_start = 0

    for idx, raw in enumerate(lines):
        line_no = idx + 1
        if is_comment_line(raw):
            # [C1] a col-7 commented-out `* EXEC SQL...END-EXEC` block must never be
            # scanned for boundaries -- skip it entirely, live or accumulating.
            continue
        scan = _mask_for_boundary_scan(raw)
        if block is None:
            if _EXEC_SQL_START.search(scan):
                block = [raw]
                block_start = line_no
                if _END_EXEC.search(scan):
                    dyn = _handle_block(block, block_start, rel, cursor_table, db_ops, db_objects, warnings)
                    dynamic_detected = dynamic_detected or dyn
                    block = None
            continue
        block.append(raw)
        if _END_EXEC.search(scan):
            dyn = _handle_block(block, block_start, rel, cursor_table, db_ops, db_objects, warnings)
            dynamic_detected = dynamic_detected or dyn
            block = None

    if block is not None:
        warnings.append(f"unterminated_exec_sql: {rel}:{block_start}")

    return db_ops, db_objects, warnings, dynamic_detected
