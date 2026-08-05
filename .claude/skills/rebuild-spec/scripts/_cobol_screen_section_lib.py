#!/usr/bin/env python3
"""COBOL SCREEN SECTION paradigm accumulator (Phase 02).

Router contract (`extract_cobol_screen.py`, frozen): `feed(path, lines)` accumulates;
`finalize() -> list[ScreenRec]` runs once after every file is fed. ScreenRec:
{screen, kind, reachable, entry_citation, flow_edges[], unverified, raw}. Screen =
each `01`-level record in SCREEN SECTION (inline or COPY-resolved). Reachable =
ACCEPT/DISPLAY <record> anywhere in PROCEDURE DIVISION. flow_edges = PERFORM-chain
screen->screen edges, same shape as Delphi form-nav edges.

COPY resolution needs a root (frozen `ScreenSectionLib()` signature means a
router-driven run always degrades COPY targets to [UNVERIFIED] unless `root=`
is passed). Bounded `os.walk` + `_SKIP_DIRS` + `copy_file_cap`; realpath
containment check rejects any resolved path escaping `root`. Stdlib only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from _cobol_screen_section_parse_lib import (
    _MAX_FLOW_EDGES_PER_FILE,
    build_copy_index,
    cap_flow_edges,
    collect_copy_statements,
    collect_inline_records,
    compute_spans,
    find_blocks,
    find_procedure_division_start,
    find_screen_section_bounds,
    performs_in_range,
    resolve_copy_target,
    sanitize_identifier,
    scan_reachability,
    screens_in_range,
)
from _extractor_lib import decode_source
from _stack_profile_lib import _SKIP_DIRS

_MAX_LINES = 200_000  # RT-F9 soft ceiling — never assume unbounded input, even pre-decoded
_DEFAULT_COPY_FILE_CAP = 20_000
_MAX_FILE_BYTES = 10 * 1024 * 1024  # [H4] mirror extract_cobol_screen.py's router-level cap


class ScreenSectionLib:
    """Accumulates SCREEN SECTION source files; parses once at `finalize()`."""

    def __init__(self, root: str | Path | None = None, copy_file_cap: int = _DEFAULT_COPY_FILE_CAP) -> None:
        self._fed: list[tuple[str, list[str]]] = []
        self._root = Path(root).resolve() if root is not None else None
        self._copy_file_cap = copy_file_cap
        self._copy_index: dict[str, Path] | None = None

    def feed(self, path: str, lines: list[str]) -> None:
        """Accumulate one file's (relative path, source lines) for later parsing."""
        self._fed.append((path, lines[:_MAX_LINES]))

    def finalize(self) -> list[dict[str, Any]]:
        """Return parsed ScreenRecs. Never raises — a bad file is skipped, not fatal."""
        recs: list[dict[str, Any]] = []
        for path, lines in self._fed:
            try:
                recs.extend(self._parse_file(path, lines))
            except Exception:  # exit-0-always: one bad file must not lose the rest
                continue
        return recs

    def _parse_file(self, path: str, lines: list[str]) -> list[dict[str, Any]]:
        bounds = find_screen_section_bounds(lines)
        if bounds is None:
            return []
        sc_start, sc_end = bounds
        proc_start = find_procedure_division_start(lines)
        reach = scan_reachability(lines, proc_start) if proc_start is not None else {}

        records: dict[str, dict[str, Any]] = {}  # upper(name) -> ScreenRec

        for name, decl_idx in collect_inline_records(lines, sc_start, sc_end):
            self._add_record(records, name, path, decl_idx, reach, False, {})

        for token, copy_idx in collect_copy_statements(lines, sc_start, sc_end):
            self._resolve_copy(records, token, path, copy_idx, reach)

        if proc_start is not None:
            self._attach_flow_edges(records, lines, path, proc_start)

        return list(records.values())

    def _add_record(
        self, records: dict[str, dict[str, Any]], name: str, path: str, decl_idx: int,
        reach: dict[str, int], unverified: bool, raw: dict[str, Any],
    ) -> None:
        key = name.upper()
        line_idx = reach.get(key)
        reachable = line_idx is not None
        cite_idx = line_idx if reachable else decl_idx
        records[key] = {
            "screen": sanitize_identifier(name),
            "kind": "screen-section",
            "reachable": reachable,
            "entry_citation": f"{path}:{cite_idx + 1}",
            "flow_edges": [],
            "unverified": unverified,
            "raw": raw,
        }

    def _unresolved_copy_record(self, token: str, path: str, copy_idx: int, reason: str) -> dict[str, Any]:
        placeholder = Path(token).stem or token
        return {
            "screen": sanitize_identifier(placeholder),
            "kind": "screen-section",
            "reachable": False,
            "entry_citation": f"{path}:{copy_idx + 1}",
            "flow_edges": [],
            "unverified": True,
            "raw": {"copy_target": token, "reason": reason},
        }

    def _resolve_copy(
        self, records: dict[str, dict[str, Any]], token: str, path: str,
        copy_idx: int, reach: dict[str, int],
    ) -> None:
        copy_citation = f"{path}:{copy_idx + 1}"
        target = self._lookup_copy(token)
        nested: list[tuple[str, int]] = []
        reason = "unresolved_or_escaped"
        if target is not None:
            try:
                # [H4] every other read path caps at _MAX_FILE_BYTES before decoding --
                # a COPY-resolved read must never bypass that invariant.
                if target.stat().st_size > _MAX_FILE_BYTES:
                    reason = "oversized_copybook"
                else:
                    text, _warns = decode_source(target, "utf-8", "latin-1")
                    copy_lines = text.splitlines()
                    nested = collect_inline_records(copy_lines, 0, len(copy_lines))
                    reason = "no_01_record_in_copybook"
            except OSError:
                reason = "read_error"

        if not nested:
            rec = self._unresolved_copy_record(token, path, copy_idx, reason)
            records[rec["screen"].upper()] = rec
            return

        for name, _decl_idx in nested:
            self._add_record(
                records, name, path, copy_idx, reach, False,
                {"copy_target": token, "copy_citation": copy_citation},
            )

    def _iter_candidate_edges(
        self, fine: dict[str, tuple[int, int]], fine_screens: dict[str, set[str]],
        section_screens: dict[str, set[str]], lines: list[str], records: dict[str, dict[str, Any]],
    ):
        """Lazily yield (src, dst, perform_idx); a caller `break` halts generation right
        there instead of materializing the full S x D cross-product per PERFORM."""
        for name, span in fine.items():
            src_screens = fine_screens.get(name) or set()
            if not src_screens:
                continue
            for target, perform_idx in performs_in_range(lines, span):
                dst_screens = fine_screens.get(target) or section_screens.get(target) or set()
                for src in (s for s in src_screens if s in records):
                    for dst in dst_screens:
                        if dst != src and dst in records:
                            yield src, dst, perform_idx

    def _attach_flow_edges(
        self, records: dict[str, dict[str, Any]], lines: list[str], path: str, proc_start: int,
    ) -> None:
        # [C4] lazy generation + early break bounds COMPUTE time too, not just output size.
        if not (blocks := find_blocks(lines, proc_start)):
            return
        fine, section = compute_spans(blocks, len(lines))
        fine_screens = {n: screens_in_range(lines, span) for n, span in fine.items()}
        section_screens = {n: screens_in_range(lines, span) for n, span in section.items()}
        edges: list[tuple[str, dict[str, Any]]] = []
        seen: set[tuple[str, str, int]] = set()
        overflow = False
        for src, dst, perform_idx in self._iter_candidate_edges(fine, fine_screens, section_screens, lines, records):
            if (src, dst, perform_idx) in seen:
                continue
            if len(edges) >= _MAX_FLOW_EDGES_PER_FILE:
                overflow = True
                break
            seen.add((src, dst, perform_idx))
            edges.append((src, {
                "from": records[src]["screen"], "to": records[dst]["screen"],
                "kind": "performs", "file": path, "line": perform_idx + 1,
            }))
        cap_flow_edges(records, edges, path, overflow)

    def _lookup_copy(self, token: str) -> Path | None:
        if self._root is None:
            return None
        if self._copy_index is None:
            self._copy_index = build_copy_index(self._root, self._copy_file_cap, _SKIP_DIRS)
        return resolve_copy_target(token, self._root, self._copy_index)
