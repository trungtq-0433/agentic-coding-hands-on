#!/usr/bin/env python3
r"""DML parsing + dynamic-SQL detection for structural extractors (Phase B).

Companion to _sql_parse_lib.py (DDL/security). Kept separate to honour the
200-line-per-file budget.

parse_dml_line(line, line_no, path) -> list[DbOp]
  Detects INSERT/SELECT/UPDATE/DELETE/MERGE. Also extracts SQL embedded inside
  single-quoted string literals on the same line (Delphi SQL.Text := '...').
  Returns empty list for non-DML lines.

is_dynamic_sql_line(line) -> bool  (RT-F8)
  Flags: SQL.Add(, SQL.Text := <var>, Format('%s'), ExecuteDirect(<var>),
         identifier := identifier + identifier  variable concatenation.
  Does NOT flag static string-literal assignments or // comment lines.

Stdlib only.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from _sql_parse_lib import sanitize_identifier, scrub_credentials


class DbOp(NamedTuple):
    table: str
    op: str          # C | R | U | D
    columns: list[str]
    line: int
    citation: str    # "path:line"
    confidence: str  # high | medium | low


# ---------------------------------------------------------------------------
# DML patterns — search (not match) to find SQL anywhere on the line or
# inside a string literal extracted from it.
# ---------------------------------------------------------------------------

_DML_INSERT = re.compile(r'\bINSERT\s+(?:OR\s+\w+\s+)?INTO\s+(?:\w+\.)?(\w+)', re.IGNORECASE)
_DML_SELECT = re.compile(r'\bSELECT\b', re.IGNORECASE)
_DML_FROM   = re.compile(r'\bFROM\s+(?:\w+\.)?(\w+)', re.IGNORECASE)
_DML_UPDATE = re.compile(r'\bUPDATE\s+(?:\w+\.)?(\w+)\s+SET\b', re.IGNORECASE)
_DML_DELETE = re.compile(r'\bDELETE\s+FROM\s+(?:\w+\.)?(\w+)', re.IGNORECASE)
_DML_MERGE  = re.compile(r'\bMERGE\s+INTO\s+(?:\w+\.)?(\w+)', re.IGNORECASE)

_INSERT_COLS = re.compile(
    r'\bINSERT\s+(?:OR\s+\w+\s+)?INTO\s+\w+\s*\(([^)]{0,512})\)', re.IGNORECASE)
_UPDATE_COLS     = re.compile(r'\bSET\s+((?:\w+\s*=[^,\n]{0,80},?\s*){1,20})', re.IGNORECASE)
_UPDATE_COL_NAME = re.compile(r'(\w+)\s*=')

# Single-quoted string literals — non-greedy, capped at 1024 chars, no multiline.
_QUOTED_SQL = re.compile(r"'([^']{1,1024})'")
_SQL_KEYWORD = re.compile(r'\b(?:SELECT|INSERT|UPDATE|DELETE|MERGE)\b', re.IGNORECASE)


def _extract_insert_cols(text: str) -> list[str]:
    m = _INSERT_COLS.search(text)
    if not m:
        return []
    return [sanitize_identifier(c.strip()) for c in m.group(1).split(",") if c.strip()]


def _extract_update_cols(text: str) -> list[str]:
    m = _UPDATE_COLS.search(text)
    if not m:
        return []
    return [sanitize_identifier(c) for c in _UPDATE_COL_NAME.findall(m.group(1))]


def _candidates(line: str) -> list[str]:
    """Return the line itself plus any quoted string literals that contain SQL keywords."""
    result = [line]
    for m in _QUOTED_SQL.finditer(line):
        content = m.group(1)
        if _SQL_KEYWORD.search(content):
            result.append(content)
    return result


def parse_dml_line(line: str, line_no: int, path: str) -> list[DbOp]:
    """Parse DML from one line (bare SQL and/or embedded string literals).

    MERGE emits both C and U ops. Deduplicates (table, op) pairs.
    """
    scrubbed, _ = scrub_credentials(line)
    citation = f"{path}:{line_no}"
    ops: list[DbOp] = []
    seen: set[tuple[str, str]] = set()

    for cand in _candidates(scrubbed):
        m = _DML_INSERT.search(cand)
        if m:
            t = sanitize_identifier(m.group(1))
            if (t, "C") not in seen:
                seen.add((t, "C"))
                ops.append(DbOp(t, "C", _extract_insert_cols(cand), line_no, citation, "high"))

        m = _DML_UPDATE.search(cand)
        if m:
            t = sanitize_identifier(m.group(1))
            if (t, "U") not in seen:
                seen.add((t, "U"))
                ops.append(DbOp(t, "U", _extract_update_cols(cand), line_no, citation, "high"))

        m = _DML_DELETE.search(cand)
        if m:
            t = sanitize_identifier(m.group(1))
            if (t, "D") not in seen:
                seen.add((t, "D"))
                ops.append(DbOp(t, "D", [], line_no, citation, "high"))

        m = _DML_MERGE.search(cand)
        if m:
            t = sanitize_identifier(m.group(1))
            for op_char in ("C", "U"):
                if (t, op_char) not in seen:
                    seen.add((t, op_char))
                    ops.append(DbOp(t, op_char, [], line_no, citation, "high"))

        if _DML_SELECT.search(cand):
            m2 = _DML_FROM.search(cand)
            if m2:
                t = sanitize_identifier(m2.group(1))
                if (t, "R") not in seen:
                    seen.add((t, "R"))
                    ops.append(DbOp(t, "R", [], line_no, citation, "high"))

    return ops


# ---------------------------------------------------------------------------
# RT-F8: dynamic SQL detection
# ---------------------------------------------------------------------------

_DELPHI_COMMENT = re.compile(r'\s*//.*$')

# SQL.Add( — always dynamic
_DYN_SQL_ADD = re.compile(r'\bSQL\.Add\s*\(', re.IGNORECASE)

# SQL.Text := <variable>  but NOT  SQL.Text := 'literal'
# Lookahead skips optional whitespace then rejects a leading quote.
_DYN_SQL_TEXT_VAR = re.compile(r'\bSQL\.Text\s*:=\s*(?!\s*[\'"])', re.IGNORECASE)

# ExecuteDirect(<variable>) — not a string literal
_DYN_EXECUTE = re.compile(r'\bExecuteDirect\s*\(\s*\w', re.IGNORECASE)

# Format('...%s...', ...) — building SQL via Format
_DYN_FORMAT = re.compile(r"\bFormat\s*\(\s*'[^']*%[sd][^']*'", re.IGNORECASE)

# var := var + var  (no trailing string literal on RHS)
_DYN_CONCAT = re.compile(r'\w+\s*:=\s*\w+\s*\+\s*\w+\s*(?:;|$)', re.IGNORECASE)


def is_dynamic_sql_line(line: str) -> bool:
    """Return True if this line exhibits dynamic SQL construction (RT-F8).

    Strips Delphi // comments first; ignores plain string-literal assignments.
    """
    stripped = _DELPHI_COMMENT.sub("", line).rstrip()
    if not stripped:
        return False
    return bool(
        _DYN_SQL_ADD.search(stripped)
        or _DYN_SQL_TEXT_VAR.search(stripped)
        or _DYN_EXECUTE.search(stripped)
        or _DYN_FORMAT.search(stripped)
        or _DYN_CONCAT.search(stripped)
    )
