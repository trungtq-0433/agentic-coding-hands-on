#!/usr/bin/env python3
"""Fixed-column HLASM/BMS macro tokenizer (Phase 03).

Column convention (per the phase spec, standard CICS BMS assembler layout):
  - label:        cols 1-8   (0-indexed line[0:8])
  - macro name:   cols 10-15 (0-indexed line[9:15]) -- DFHMSD/DFHMDI/DFHMDF/AIF/AGO/... all
                  fit this 6-char window
  - operand text: cols 16-71 (0-indexed line[15:71])
  - continuation: col 72     (0-indexed line[71:72]) non-blank -> the next physical line
                  continues the operand, itself resuming at col 16
  - comment:      `*` at col 1 -> whole line skipped

This module ONLY tokenizes fixed columns + reassembles continuations. It has no opinion on
which macro names matter (DFHMSD vs AIF vs anything else) or what operands mean semantically
-- that interpretation lives in `_cobol_bms_lib.py`.

Streaming, line-by-line -- never a greedy multiline match (RT-F9).
Stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_COND_DIRECTIVES = {"AIF", "AGO"}
_TARGET_LABEL_RE = re.compile(r"\.([A-Za-z][A-Za-z0-9$#@]*)")


@dataclass
class BmsStatement:
    """One logical macro statement; continuation lines already merged into `operands`."""

    label: str
    macro: str
    operands: str
    start_line: int  # 1-based, first physical line
    end_line: int  # 1-based, last physical line (== start_line unless continued)


def is_comment_line(line: str) -> bool:
    """BMS/HLASM comment convention: `*` in column 1."""
    return line[:1] == "*"


def _operand_chunk(line: str) -> tuple[str, bool]:
    """Slice one physical line's operand text (cols 16-71) + continuation flag (col 72)."""
    cont_char = line[71:72] if len(line) > 71 else ""
    continues = bool(cont_char.strip())
    chunk = line[15:71] if continues else line[15:]
    return chunk.rstrip(), continues


def tokenize(lines: list[str]) -> list[BmsStatement]:
    """Split fixed-column BMS/HLASM source into logical statements (continuations merged).

    A new statement starts on any non-comment, non-blank line carrying a non-blank macro
    field (cols 10-15). Continuation state is tracked from the PREVIOUS line's col-72 flag,
    never guessed from the current line's blankness (a genuinely blank-label statement and a
    continuation line look the same at cols 1-9).
    """
    pending: dict | None = None
    built: list[dict] = []

    for idx, raw in enumerate(lines):
        lineno = idx + 1
        if is_comment_line(raw):
            continue
        if pending is not None and pending["continuing"]:
            chunk, continuing = _operand_chunk(raw)
            pending["operand_parts"].append(chunk)
            pending["end_line"] = lineno
            pending["continuing"] = continuing
            continue
        if not raw.strip():
            continue
        macro = raw[9:15].strip() if len(raw) > 9 else ""
        if not macro:
            continue  # not a macro-shaped line -- plain text/data, not our concern
        label = raw[0:8].strip()
        operand_chunk, continuing = _operand_chunk(raw)
        pending = {
            "label": label,
            "macro": macro,
            "operand_parts": [operand_chunk],
            "start_line": lineno,
            "end_line": lineno,
            "continuing": continuing,
        }
        built.append(pending)

    return [
        BmsStatement(
            label=s["label"],
            macro=s["macro"],
            operands="".join(s["operand_parts"]),
            start_line=s["start_line"],
            end_line=s["end_line"],
        )
        for s in built
    ]


def split_operands(text: str) -> dict[str, str]:
    """Split a BMS operand string into an upper-cased `KEY -> value` dict.

    Splits on top-level commas only -- parens/quotes protect internal commas, e.g.
    `POS=(1,1),INITIAL='A, B'` yields 2 parts, not 3. A bare keyword with no `=` is stored
    with an empty value.
    """
    parts: list[str] = []
    depth = 0
    quote = ""
    buf: list[str] = []
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch == "(":
            depth += 1
            buf.append(ch)
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
            continue
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))

    result: dict[str, str] = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, _, val = part.partition("=")
            result[key.strip().upper()] = val.strip()
        else:
            result[part.upper()] = ""
    return result


def conditional_spans(stmts: list[BmsStatement]) -> list[tuple[int, int]]:
    """AIF/AGO -> target-label line ranges (HLASM conditional-assembly control flow).

    A "span" is the run of physical lines strictly between a directive and the label
    statement it names, e.g. `AIF (&V EQ 1).OLDMAP` targets a later `.OLDMAP  ANOP` statement.
    An unresolvable target (label not found, or found before the directive) yields no span --
    the caller still treats the file as touched by conditional assembly via a raw macro-name
    scan, this function only supplies the exclusion bounds it can prove.
    """
    label_lines = {s.label: s.start_line for s in stmts if s.label}
    spans: list[tuple[int, int]] = []
    for s in stmts:
        if s.macro.upper() not in _COND_DIRECTIVES:
            continue
        m = _TARGET_LABEL_RE.search(s.operands)
        target_line = label_lines.get("." + m.group(1)) if m else None
        if target_line is None or target_line <= s.start_line:
            continue
        spans.append((s.start_line + 1, target_line - 1))
    return spans


def in_span(lineno: int, spans: list[tuple[int, int]]) -> bool:
    return any(a <= lineno <= b for a, b in spans)
