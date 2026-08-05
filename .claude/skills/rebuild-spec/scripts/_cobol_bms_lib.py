#!/usr/bin/env python3
"""COBOL/CICS BMS macro paradigm accumulator (Phase 03).

Router contract (`extract_cobol_screen.py`, Phase 01): `feed(path, lines)` accumulates;
`finalize() -> list[ScreenRec]` resolves the whole-corpus MAPSET->source index + EXEC CICS
SEND/RECEIVE MAP join. `ScreenRec`: {screen, kind, reachable, entry_citation, flow_edges[],
unverified, raw}.

Pipeline: DFHMSD/DFHMDI/DFHMDF macros (via `_cobol_bms_grammar_lib`) build map defs; AIF/AGO
conditional-assembly spans exclude DFHMDF fields inside them from emission entirely (fix 13 --
never merged-then-tagged, no fabricated combined geometry); EXEC CICS SEND/RECEIVE MAP joins
for reachability + entry citation + flow edges; a copybook's `<map>I`/`<map>O` symbolic-map
record is the fallback source when no macro source exists (unverified, attrs unknown); a map
referenced but defined nowhere surfaces as its own ScreenRec with `raw.warning =
"mapset_undefined"` (fix M1) -- `finalize()` has no side warning channel, so a synthetic
ScreenRec IS the signal, never a silent skip.

Streaming, bounded lookahead only (RT-F9 -- no greedy multiline regex). Stdlib only.
"""
from __future__ import annotations

import re
from typing import Any

import _cobol_bms_grammar_lib as grammar
from _cobol_dispatch_lib import matches_bms_macro

_MAX_FILE_BYTES = 10 * 1024 * 1024
_FILE_CAP = 5_000  # bounded MAPSET-index accumulation (mirrors _stack_profile_lib file_cap)
_MAX_EXEC_BLOCK_LINES = 20  # bounded lookahead for a multi-line EXEC CICS ... END-EXEC block

_COND_MARKERS = {"AIF", "AGO", "SETA", "SETB"}
_EXEC_START_RE = re.compile(r"EXEC\s+CICS\s+(SEND|RECEIVE)\b", re.IGNORECASE)
_MAP_ARG_RE = re.compile(r"MAP\s*\(\s*['\"]?([A-Za-z0-9$#@_-]+)['\"]?\s*\)", re.IGNORECASE)
_END_EXEC_RE = re.compile(r"END-EXEC", re.IGNORECASE)
_SYMBOLIC_01_RE = re.compile(r"^\s*01\s+([A-Za-z0-9$#@_-]+)\b", re.IGNORECASE)
_CREDENTIAL_RE = re.compile(r"(PASSWORD|PWD)\s*=\s*\S+", re.IGNORECASE)
_COPYBOOK_NOTE = "attrs unknown -- symbolic-map copybook only, no BMS macro source"
_LABEL_TRIVIAL_LEN = 3  # values this short or shorter can't be meaningfully secret or prose


def _sanitize_identifier(s: str, max_len: int = 80) -> str:
    """RT-F10: strip Markdown-hostile chars + cap length before an identifier is ever cited."""
    return s.replace("|", "").replace("`", "").replace("\n", " ")[:max_len]


def _scrub_credentials(text: str) -> str:
    """RT-F7-style scrub: redact PASSWORD=/PWD=<secret> before a line becomes a citation."""
    return _CREDENTIAL_RE.sub(lambda m: f"{m.group(1)}=<redacted>", text)


def _looks_like_secret_shaped(value: str) -> bool:
    """C5 fix: `opnds["INITIAL"]` is already `INITIAL=`-stripped, so the KEY=VALUE
    `_CREDENTIAL_RE` above can never re-match it (structural no-op) -- scrub by shape
    instead. A value reads as human prose (survives un-redacted) if it is trivially short,
    contains a space (multi-word label, e.g. "Enter customer name:"), or is a single word
    ending in ':' (e.g. "NAME:"). Anything else non-trivial -- a bare opaque word/token,
    with or without digits -- is treated as secret-shaped (favors safety over fidelity)."""
    v = value.strip().strip("'\"")
    if len(v) <= _LABEL_TRIVIAL_LEN or any(c.isspace() for c in v):
        return False
    return not (v.endswith(":") and v[:-1].isalpha())


def _scrub_initial(value: str) -> tuple[str, bool]:
    """Redact a secret-shaped INITIAL literal unconditionally; flag the field for a human
    to confirm (never a silent leak). Returns (value-or-redacted, manual_review)."""
    if not _looks_like_secret_shaped(value):
        return value, False
    q = value[:1] if value[:1] in ("'", '"') else ""
    return f"{q}<redacted>{q}", True


def _rec(name: str, reachable: bool, citation: str, edges: list[str], unverified: bool, raw: dict) -> dict:
    return {
        "screen": name, "kind": "cics-bms", "reachable": reachable, "entry_citation": citation,
        "flow_edges": edges, "unverified": unverified, "raw": raw,
    }


def _review_note(excluded_count: int) -> str:
    if excluded_count:
        return (f"conditional-assembly guard: {excluded_count} field(s) excluded "
                "(assembly-time-exclusive branch, geometry not fabricated)")
    return "conditional-assembly tokens (AIF/AGO/SETA/SETB) detected in source"


def _parse_bms_deck(path: str, lines: list[str], mapsets: dict[str, str], maps: dict[str, Any]) -> None:
    stmts = grammar.tokenize(lines)
    cond_present = any(s.macro.upper() in _COND_MARKERS for s in stmts)
    spans = grammar.conditional_spans(stmts) if cond_present else []
    current_mapset: str | None = None
    current_map: dict[str, Any] | None = None

    for s in stmts:
        macro = s.macro.upper()
        if macro == "DFHMSD":
            if s.label:
                mapsets.setdefault(s.label, f"{path}:{s.start_line}")
                current_mapset = s.label
        elif macro == "DFHMDI" and s.label:
            entry = maps.setdefault(s.label, {
                "mapset": current_mapset, "citation": f"{path}:{s.start_line}",
                "fields": [], "manual_review": False, "excluded_field_count": 0,
            })
            entry["manual_review"] = entry["manual_review"] or cond_present
            current_map = entry
        elif macro == "DFHMDF" and current_map is not None:
            if grammar.in_span(s.start_line, spans):
                current_map["excluded_field_count"] += 1
                current_map["manual_review"] = True
                continue
            opnds = grammar.split_operands(s.operands)
            initial, needs_review = _scrub_initial(opnds.get("INITIAL", ""))
            current_map["fields"].append({
                "name": _sanitize_identifier(s.label or "(unnamed)"),
                "pos": opnds.get("POS", ""), "length": opnds.get("LENGTH", ""),
                "attrb": opnds.get("ATTRB", ""), "color": opnds.get("COLOR", ""),
                "initial": initial, "manual_review": needs_review,
                "citation": f"{path}:{s.start_line}",
            })


def _parse_exec_cics(path: str, lines: list[str], exec_refs: dict[str, list[tuple[str, int, str]]]) -> None:
    n = len(lines)
    i = 0
    while i < n:
        raw = lines[i]
        if grammar.is_comment_line(raw) or not _EXEC_START_RE.search(raw):
            i += 1
            continue
        start_line = i + 1
        block = [raw]
        j = i
        while j < n - 1 and not _END_EXEC_RE.search(lines[j]) and (j - i) < _MAX_EXEC_BLOCK_LINES:
            j += 1
            block.append(lines[j])
        m = _MAP_ARG_RE.search(" ".join(block))
        if m:
            map_name = _sanitize_identifier(m.group(1).upper())
            exec_refs.setdefault(map_name, []).append((path, start_line, _scrub_credentials(raw.strip())))
        i = j + 1


def _looks_like_bms_source(path: str, lines: list[str]) -> bool:
    """Restricts symbolic-map copybook harvesting to genuinely BMS-adjacent files.

    The router now also feeds ordinary COBOL calling programs to this lib whenever they
    merely reference `EXEC CICS SEND/RECEIVE MAP` (no BMS macros of their own -- the normal
    real-world split between a map deck and its callers). Those programs' WORKING-STORAGE
    sections routinely declare unrelated `01 ...-IO.`/`01 ...-O.` records; scanning them for
    "symbolic map" candidates would fabricate phantom screens from ordinary data.

    [Wave 7 review, second occurrence of the same fabrication class] `.cpy` alone is NOT a
    reliable discriminator -- it is COBOL's generic copybook extension, used for ordinary
    shared data/procedural fragments, not exclusively for BMS-generated symbolic maps. A
    `.cpy` file that itself contains an `EXEC CICS` statement is, by definition, NOT a pure
    symbolic-map copybook (those are BMS-macro-assembly output: bare `<map>I`/`<map>O` data
    records only, never their own executable CICS calls -- the calling program issues
    EXEC CICS, not the map copybook). Require the ABSENCE of `EXEC CICS` in a `.cpy` file
    before treating it as copybook-harvest-eligible, so a procedural `.cpy` carrying both a
    real EXEC CICS reference AND an unrelated `01 ...-O.` record no longer gets that record
    fabricated into a phantom screen."""
    if path.lower().endswith(".bms") or matches_bms_macro(lines):
        return True
    if path.lower().endswith(".cpy"):
        return not any(
            _EXEC_START_RE.search(ln) for ln in lines if not grammar.is_comment_line(ln)
        )
    return False


def _parse_copybook(path: str, lines: list[str], candidates: dict[str, tuple[str, int]]) -> None:
    for idx, raw in enumerate(lines):
        m = None if grammar.is_comment_line(raw) else _SYMBOLIC_01_RE.match(raw)
        if not m:
            continue
        record = m.group(1).upper()
        if len(record) < 2 or record[-1] not in ("I", "O"):
            continue
        candidates.setdefault(_sanitize_identifier(record[:-1]), (path, idx + 1))


class BmsLib:
    """Accumulates BMS/asm + COBOL source files; resolves screens once every file is seen."""

    def __init__(self) -> None:
        self._fed: list[tuple[str, list[str]]] = []
        self._cap_reached = False

    def feed(self, path: str, lines: list[str]) -> None:
        """Accumulate one file's (relative path, source lines) for later parsing."""
        if len(self._fed) >= _FILE_CAP:
            self._cap_reached = True
            return
        if sum(len(line) for line in lines) > _MAX_FILE_BYTES:
            return  # defensive re-check -- router already caps raw bytes before decode
        self._fed.append((path, lines))

    def finalize(self) -> list[dict[str, Any]]:
        """Resolve the MAPSET->source index + EXEC CICS join, return ScreenRec[]."""
        mapsets: dict[str, str] = {}
        maps: dict[str, Any] = {}
        copybooks: dict[str, tuple[str, int]] = {}
        exec_refs: dict[str, list[tuple[str, int, str]]] = {}

        for path, lines in self._fed:
            _parse_bms_deck(path, lines, mapsets, maps)
            if _looks_like_bms_source(path, lines):
                _parse_copybook(path, lines, copybooks)
            _parse_exec_cics(path, lines, exec_refs)

        screens: list[dict[str, Any]] = []

        for name, entry in maps.items():
            refs = exec_refs.get(name, [])
            raw: dict[str, Any] = {"mapset": entry["mapset"], "fields": entry["fields"]}
            if entry["mapset"] and mapsets.get(entry["mapset"]):
                raw["mapset_citation"] = mapsets[entry["mapset"]]
            if entry["manual_review"]:
                raw["manual_review"] = True
                raw["note"] = _review_note(entry["excluded_field_count"])
            screens.append(_rec(
                name, bool(refs),
                f"{refs[0][0]}:{refs[0][1]}" if refs else entry["citation"],
                [f"{r[0]}:{r[1]}" for r in refs],
                (not refs) or entry["manual_review"], raw,
            ))

        for name, refs in exec_refs.items():
            if name in maps:
                continue
            citation = f"{refs[0][0]}:{refs[0][1]}"
            edges = [f"{r[0]}:{r[1]}" for r in refs]
            if name in copybooks:
                cpy_path, cpy_line = copybooks[name]
                raw = {"fields": [], "note": _COPYBOOK_NOTE, "copybook_citation": f"{cpy_path}:{cpy_line}"}
            else:
                # [Medium fix M1] referenced but defined nowhere -- surfaced, never silent.
                raw = {
                    "fields": [], "warning": "mapset_undefined",
                    "note": f"EXEC CICS references map {name!r} but no .bms/asm source or "
                            "symbolic-map copybook defines it -- layout unrecoverable",
                }
            screens.append(_rec(name, True, citation, edges, True, raw))

        for name, (cpy_path, cpy_line) in copybooks.items():
            if name in maps or name in exec_refs:
                continue
            screens.append(_rec(name, False, f"{cpy_path}:{cpy_line}", [], True,
                                 {"fields": [], "note": _COPYBOOK_NOTE}))

        return screens
