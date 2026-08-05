#!/usr/bin/env python3
r"""SQL/DDL parsing + security passes for structural extractors (Phase B).

Security (RT-F7): scrub_credentials(line) -- redact before any line enters a citation.
Safety (RT-F9): line-by-line, anchored patterns, no greedy multiline.
Identifier safety (RT-F10): sanitize_identifier(name) -- Markdown-safe.

DDL parsing: parse_ddl_line / parse_column_line.
DML parsing + dynamic-SQL detection live in _sql_dml_lib.py (same package).

Stdlib only.
"""
from __future__ import annotations

import re
from typing import NamedTuple

_MAX_IDENTIFIER_LEN = 128


# ---------------------------------------------------------------------------
# RT-F10: identifier sanitize
# ---------------------------------------------------------------------------

def sanitize_identifier(name: str) -> str:
    r"""Make an identifier safe for Markdown table cells.

    Removes | (breaks columns), newline -> space, removes backticks, truncates.
    """
    name = name.replace("\n", " ").replace("\r", " ")
    name = name.replace("`", "")
    name = name.replace("|", "")   # remove raw pipe -- Markdown-safe
    return name[:_MAX_IDENTIFIER_LEN]


# ---------------------------------------------------------------------------
# RT-F7: credential scrub
# ---------------------------------------------------------------------------

_CRED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'(IDENTIFIED\s+BY\s+)\S+', re.IGNORECASE), r'\1<redacted>'),
    (re.compile(r'(PASSWORD\s*=\s*)\S+', re.IGNORECASE), r'\1<redacted>'),
    (re.compile(r'(PWD\s*=\s*)\S+', re.IGNORECASE), r'\1<redacted>'),
    (re.compile(r'(Password\s*=\s*)[^;"\'\s]+', re.IGNORECASE), r'\1<redacted>'),
    (re.compile(r'((?:password|pwd)=)[^&;"\'\s]+', re.IGNORECASE), r'\1<redacted>'),
    (re.compile(r'(Data\s+Source\s*=[^;]*;[^;]*Password\s*=\s*)\S+', re.IGNORECASE),
     r'\1<redacted>'),
    (re.compile(r'(\d{1,3}(?:\.\d{1,3}){3}:\d+:[^:\s]+:)\S+'), r'\1<redacted>'),
    # RT-F7 (H1): URL-embedded creds `scheme://user:pass@host` (sqlalchemy/pg/PHP DSN).
    (re.compile(r'(//[^:/@\s]+):[^@/\s]+@'), r'\1:<redacted>@'),
    # RT-F7 (H1): Oracle slash/CONNECT creds `user/pass@tns` and `CONNECT app/pw@db`
    # (jdbc:oracle:thin:scott/tiger@host, SQL*Plus CONNECT, TOraSession ConnectionString).
    (re.compile(r'\b(\w+)/[^/@\s]+@(\w)', re.IGNORECASE), r'\1/<redacted>@\2'),
]


def scrub_credentials(line: str) -> tuple[str, bool]:
    """Scrub secret values from a line. Returns (scrubbed_line, redacted_bool).

    RT-F7 (H2): a credential is treated as REAL only when it appears in the CODE portion of the
    line (before any `--` line comment). This avoids a false `potential_credential_in_citation`
    alarm on a commented `-- IDENTIFIED BY ...` while still redacting it from the returned text.
    """
    code_part = line.split("--", 1)[0]
    result = line
    redacted = False
    for pattern, repl in _CRED_PATTERNS:
        in_code = bool(pattern.search(code_part))  # decide flagging from the ORIGINAL code portion
        new = pattern.sub(repl, result)
        if new != result:
            result = new          # always redact the value (defense-in-depth, comments incl.)
            if in_code:
                redacted = True   # flag only when the credential is real code, not a comment
    return result, redacted


# ---------------------------------------------------------------------------
# DDL object types
# ---------------------------------------------------------------------------

class DbObject(NamedTuple):
    kind: str          # table|view|sequence|trigger|procedure|package|function
    name: str          # sanitized
    columns: list[str] # populated for table/view only
    citation: str      # "path:line_no"


_DDL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "table"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?VIEW\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "view"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?SEQUENCE\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "sequence"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "trigger"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "procedure"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?PACKAGE(?:\s+BODY)?\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "package"),
    (re.compile(r'^\s*CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:\w+\.)?(\w+)', re.IGNORECASE), "function"),
]

# Column lines start with either leading whitespace OR a leading comma
# (Oracle leading-comma DDL style: `,\tCAPTION VARCHAR2(40)`).
_COL_DEF  = re.compile(r'^(?:\s+|,)\s*(\w+)\s+\w', re.IGNORECASE)
_COL_SKIP = re.compile(
    r'^\s*,?\s*(?:CONSTRAINT|PRIMARY|UNIQUE|FOREIGN|CHECK|INDEX|KEY|TABLESPACE|STORAGE|PARTITION|\))',
    re.IGNORECASE,
)


def parse_ddl_line(
    line: str,
    line_no: int,
    path: str,
    inside_create_table: bool = False,
) -> tuple[DbObject | None, bool]:
    """Detect a CREATE statement on this line. Returns (obj_or_None, new_inside_table)."""
    scrubbed, _ = scrub_credentials(line)
    citation = f"{path}:{line_no}"
    for pattern, kind in _DDL_PATTERNS:
        m = pattern.match(scrubbed)
        if m:
            name = sanitize_identifier(m.group(1))
            return DbObject(kind=kind, name=name, columns=[], citation=citation), (kind == "table")
    return None, inside_create_table


def parse_column_line(line: str) -> str | None:
    """Extract a column name from a line inside a CREATE TABLE block, or None."""
    scrubbed, _ = scrub_credentials(line)
    if _COL_SKIP.match(scrubbed) or re.match(r'^\s*\)', scrubbed):
        return None
    m = _COL_DEF.match(scrubbed)
    return sanitize_identifier(m.group(1)) if m else None


_COL_CONSTRAINT_KW = {
    "CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "INDEX", "KEY",
}


def extract_inline_columns(line: str) -> tuple[list[str], bool]:
    """Parse columns from a single-line `CREATE TABLE x (...)` definition.

    Returns (column_names, closed) where `closed` is True when the column-list
    parenthesis balances on this line (i.e. the table is fully defined inline, so the
    caller must NOT enter multi-line `inside_table` mode — the bug a single-line table
    otherwise triggers: the flag never resets and later statements are swallowed).
    """
    start = line.find("(")
    if start < 0:
        return [], False
    depth = 0
    seg = ""
    segments: list[str] = []
    closed = False
    for ch in line[start:]:
        if ch == "(":
            depth += 1
            if depth == 1:
                continue  # skip the outer opening paren
        elif ch == ")":
            depth -= 1
            if depth == 0:
                segments.append(seg)
                closed = True
                break
        if depth == 1 and ch == ",":
            segments.append(seg)
            seg = ""
        else:
            seg += ch
    cols: list[str] = []
    for s in segments:
        m = re.match(r"\s*(\w+)", s)
        if not m:
            continue
        if m.group(1).upper() in _COL_CONSTRAINT_KW:
            continue
        cols.append(sanitize_identifier(m.group(1)))
    return cols, closed
