#!/usr/bin/env python3
r"""Parsing + repo-index helpers for `_cobol_screen_section_lib.py` (Phase 02).

Regex/scan functions take pre-split `lines: list[str]`; `build_copy_index`/
`resolve_copy_target` do a bounded filesystem walk + realpath containment
check for COPY-target resolution instead.

LIMITATION: header detection is an anchored name+period heuristic (a bare
verb statement like `EXIT.` could rarely misread as a header). `_SEQ`
tolerates an optional 4-6 digit sequence-number prefix. Stdlib only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from _cobol_dispatch_lib import is_comment_line

_SEQ = r"(?:\d{4,6}\s+)?"

_PROC_DIVISION_RE = re.compile(r"\bPROCEDURE\s+DIVISION\b", re.IGNORECASE)
_SCREEN_SECTION_RE = re.compile(r"\bSCREEN\s+SECTION\b", re.IGNORECASE)
_ANY_SECTION_OR_DIVISION_RE = re.compile(r"\b(?:[A-Z0-9-]+\s+SECTION|[A-Z]+\s+DIVISION)\b", re.IGNORECASE)
_LEVEL01_RE = re.compile(rf"^\s*{_SEQ}01\s+([A-Za-z0-9-]+)", re.IGNORECASE)
_COPY_RE = re.compile(rf"^\s*{_SEQ}COPY\s+(.+?)\.\s*$", re.IGNORECASE)
_ACCEPT_DISPLAY_RE = re.compile(r"\b(?:ACCEPT|DISPLAY)\s+([A-Za-z0-9-]+)", re.IGNORECASE)
_PERFORM_RE = re.compile(r"\bPERFORM\s+([A-Za-z0-9-]+)", re.IGNORECASE)
# [C3 fix] two adjacent `\s*` once flanked an optional SECTION token -> O(n^2) backtracking
# on a dot-less whitespace run (~2s @ 40k spaces). Alternation puts each `\s*` behind a
# mandatory literal so each backtracks independently -> O(n).
_HEADER_RE = re.compile(rf"^\s*{_SEQ}([A-Za-z][A-Za-z0-9-]*)(?:\s*(SECTION)\s*\.|\s*\.)\s*$", re.IGNORECASE)

_MAX_IDENT_LEN = 128

def sanitize_identifier(name: str) -> str:
    """RT-F10: strip Markdown-hostile chars before a name enters the digest."""
    clean = name.replace("|", "").replace("`", "").replace("\n", " ").replace("\r", " ")
    return clean.strip()[:_MAX_IDENT_LEN]

def find_screen_section_bounds(lines: list[str]) -> tuple[int, int] | None:
    """Return 0-based (start, end) content range (end exclusive) of SCREEN SECTION."""
    start = None
    for idx, raw in enumerate(lines):
        if is_comment_line(raw):
            continue
        if _SCREEN_SECTION_RE.search(raw):
            start = idx + 1
            break
    if start is None:
        return None
    end = len(lines)
    for idx in range(start, len(lines)):
        if is_comment_line(lines[idx]):
            continue
        if _ANY_SECTION_OR_DIVISION_RE.search(lines[idx]):
            end = idx
            break
    return start, end

def find_procedure_division_start(lines: list[str]) -> int | None:
    """0-based index of the first line AFTER `PROCEDURE DIVISION.`, or None."""
    for idx, raw in enumerate(lines):
        if is_comment_line(raw):
            continue
        if _PROC_DIVISION_RE.search(raw):
            return idx + 1
    return None

def collect_inline_records(lines: list[str], start: int, end: int) -> list[tuple[str, int]]:
    """01-level record names in [start, end). Returns (name, 0-based line)."""
    out: list[tuple[str, int]] = []
    for idx in range(start, end):
        if is_comment_line(lines[idx]):
            continue
        m = _LEVEL01_RE.match(lines[idx])
        if m:
            out.append((m.group(1), idx))
    return out

def collect_copy_statements(lines: list[str], start: int, end: int) -> list[tuple[str, int]]:
    """`COPY <target>.` statements in [start, end). Returns (target, 0-based line)."""
    out: list[tuple[str, int]] = []
    for idx in range(start, end):
        if is_comment_line(lines[idx]):
            continue
        m = _COPY_RE.match(lines[idx])
        if m:
            out.append((m.group(1).strip(), idx))
    return out

def scan_reachability(lines: list[str], proc_start: int) -> dict[str, int]:
    """First (min) 0-based line where each screen name is ACCEPT/DISPLAY'd."""
    seen: dict[str, int] = {}
    for idx in range(proc_start, len(lines)):
        if is_comment_line(lines[idx]):
            continue
        for m in _ACCEPT_DISPLAY_RE.finditer(lines[idx]):
            name = m.group(1).upper()
            if name not in seen:
                seen[name] = idx
    return seen

def find_blocks(lines: list[str], proc_start: int) -> list[tuple[str, bool, int]]:
    """Paragraph/section headers from proc_start to EOF: (name upper, is_section, line)."""
    out: list[tuple[str, bool, int]] = []
    for idx in range(proc_start, len(lines)):
        if is_comment_line(lines[idx]):
            continue
        m = _HEADER_RE.match(lines[idx])
        if m:
            out.append((m.group(1).upper(), bool(m.group(2)), idx))
    return out

def screens_in_range(lines: list[str], span: tuple[int, int]) -> set[str]:
    """ACCEPT/DISPLAY screen names anywhere in the [start, end) span."""
    start, end = span
    names: set[str] = set()
    for idx in range(start, end):
        if is_comment_line(lines[idx]):
            continue
        for m in _ACCEPT_DISPLAY_RE.finditer(lines[idx]):
            names.add(m.group(1).upper())
    return names

def performs_in_range(lines: list[str], span: tuple[int, int]) -> list[tuple[str, int]]:
    """`PERFORM <target>` occurrences in the [start, end) span: (target upper, line)."""
    start, end = span
    out: list[tuple[str, int]] = []
    for idx in range(start, end):
        if is_comment_line(lines[idx]):
            continue
        for m in _PERFORM_RE.finditer(lines[idx]):
            out.append((m.group(1).upper(), idx))
    return out

def compute_spans(
    blocks: list[tuple[str, bool, int]], total_len: int
) -> tuple[dict[str, tuple[int, int]], dict[str, tuple[int, int]]]:
    """Return (fine_spans, section_spans): name -> (start, end) 0-based, end exclusive.
    `fine_spans` = each block's own lines up to the next block of ANY kind.
    `section_spans` = SECTION blocks only, aggregating nested paragraphs up to the
    next SECTION (or EOF), so `PERFORM <section-name>` resolves every screen in it."""
    fine: dict[str, tuple[int, int]] = {}
    for i, (name, _is_sec, idx) in enumerate(blocks):
        end = blocks[i + 1][2] if i + 1 < len(blocks) else total_len
        fine[name] = (idx, end)

    section: dict[str, tuple[int, int]] = {}
    sec_positions = [i for i, b in enumerate(blocks) if b[1]]
    for pos, i in enumerate(sec_positions):
        name, _, idx = blocks[i]
        nxt = sec_positions[pos + 1] if pos + 1 < len(sec_positions) else None
        end = blocks[nxt][2] if nxt is not None else total_len
        section[name] = (idx, end)

    return fine, section

def build_copy_index(root: Path, file_cap: int, skip_dirs: set[str]) -> dict[str, Path]:
    """Bounded `os.walk(followlinks=False)` index: lowercase basename -> first match.
    Partial index on cap (never blocks on scanning the full corpus first)."""
    index: dict[str, Path] = {}
    count = 0
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for fn in filenames:
            count += 1
            if count > file_cap:
                return index
            key = fn.lower()
            if key not in index:
                index[key] = Path(dirpath) / fn
    return index

def resolve_copy_target(token: str, root: Path, index: dict[str, Path]) -> Path | None:
    """Look up `token`'s basename in `index`; reject any path escaping `root`."""
    candidate = index.get(Path(token).name.lower())
    if candidate is None:
        return None
    try:
        real = os.path.realpath(str(candidate))
        real_root = os.path.realpath(str(root))
        if os.path.commonpath([real, real_root]) != real_root:
            return None  # [Red-team fix 6] containment escape -> unresolved
    except (OSError, ValueError):
        return None
    return Path(real)

# [C4] per-file cap on flow edges — unbounded S x D cross-product (400/side -> 160k) blew the digest up.
_MAX_FLOW_EDGES_PER_FILE = 5000

def cap_flow_edges(records: dict[str, dict], edges: list[tuple[str, dict]], path: str, overflow: bool) -> None:
    """Append deduped `(src_key, edge)` pairs up to the cap; mark touched records on `overflow`."""
    kept = edges[:_MAX_FLOW_EDGES_PER_FILE]
    for src, edge in kept:
        records[src]["flow_edges"].append(edge)
    if overflow:
        for src in {s for s, _ in kept}:
            records[src]["raw"]["flow_edges_truncated"] = path
