#!/usr/bin/env python3
# layout-exempt: rebuild-spec migration — docs/features|generated paths are managed targets
"""Idempotent migration (v25.0.0): backfill the feature↔API/route ID binding.

Unlike `migrate-feature-screen-ids.py` (reads an existing "Owned screens" bridge
in screen-flow.md), route-list.md has NO ownership bridge — ownership is DERIVED:
scan every `docs/features/F###/technical-spec.md`'s Artifact References table for
cited ROUTE### tokens, invert into {ROUTE### -> [citing F###]}. Uses
`_route_link_lib.artifact_ref_cited_routes` (per feature spec) instead of a
second hand-rolled parser — that function is the SAME one
`validate_feature_api_link.py`'s `check_owner_consistency` relies on for
citation-detection, so migration attribution and validator citation-detection can
never disagree (a prior, stricter, hardcoded-to-the-"API Map"-row parser risked
spurious `link.owner_mismatch` right after migration — reviewer finding). Heuristic:
"F### cites ROUTE### in its Codes Used column, therefore declares ownership" —
explicit and auditable, matching feature-list.md's "All route references are
valid" checklist assumption that technical-spec.md is authoritative. Unlike the
screen migration's single-owner `setdefault` ("first owner wins"), routes are
multi-owner: every citing F### is comma-joined (Phase 1's design).

Forward — assigns `Code` (ROUTE###) to each uncoded Backend Routes row in
          route-list.md, first-appearance order, contiguous 001..N (route-list.md
          is the ONE place ROUTE### is minted — no external source to resolve
          against, unlike screen names -> screen-list.md).
Reverse — assigns `Owner F###` from the citation map, or "—" when uncited
          (shared/infra route).

Idempotent: a Backend Routes table with BOTH a Code and Owner F### header is left
untouched. Non-destructive: only INSERTS the two columns, never rewrites Method/
Path/Handler/Middleware cells. No technical-spec.md files yet -> WARN + exit 0,
no changes ("run the feature-specs pass first").

No file locking: reads many technical-spec.md files but WRITES only ONE file
(route-list.md) — same single-writer single-file shape as
migrate-feature-screen-ids.py, which PR #158's locking hardening did NOT touch
(that targeted MULTI-file transactional writers: promote_drafts.py,
purge_system_drafts.py, migrate_docs_layout.py). Mirroring the sibling here
avoids an inconsistent new safety mechanism it lacks.

Stdlib only. Exit 0 on success/no-op/missing-bridge; non-zero only on write error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _id_schemes_lib import segment_text, token_re  # noqa: E402
from _nav_table_parse_lib import _SEP_ROW  # noqa: E402
from _route_link_lib import artifact_ref_cited_routes  # noqa: E402

_CODE_HEADER = re.compile(r"^code$")
_OWNER_HEADER = re.compile(r"^owner\b")
_ROUTE_CODE = token_re("ROUTE", "")


def _fenced_line_indices(text: str) -> set[int]:
    """Line indices (0-based, matching `text.splitlines()`) inside any fenced
    block (C1) — used to keep a documentation example table under `## Backend
    Routes` from being mistaken for a real span to migrate."""
    fenced: set[int] = set()
    line_no = 0
    for kind, chunk in segment_text(text):
        n_lines = chunk.count("\n") + (0 if chunk.endswith("\n") or not chunk else 1)
        if kind != "prose":
            fenced.update(range(line_no, line_no + n_lines))
        line_no += n_lines
    return fenced


def parse_technical_spec_citations(docs_root: Path) -> dict[str, list[str]]:
    """Map each cited ROUTE### -> ordered, deduped list of citing F### tokens.

    Reuses `_route_link_lib.artifact_ref_cited_routes` (same parser the
    validator/nav path already relies on) instead of a second hand-rolled
    scanner, so migration attribution and validator citation-detection can
    never disagree on which citations count.
    """
    out: dict[str, list[str]] = {}
    for spec in sorted(docs_root.glob("features/*/technical-spec.md")):
        fm = re.match(r"^(F\d{3})\w*", spec.parent.name)
        if not fm:
            continue
        fcode = fm.group(1)
        text = spec.read_text(encoding="utf-8")
        for route in artifact_ref_cited_routes(text):
            out.setdefault(route, [])
            if fcode not in out[route]:
                out[route].append(fcode)
    return out


# ---------------------------------------------------------------------------
# forward + reverse — insert Code / Owner F### columns into route-list.md
# ---------------------------------------------------------------------------

def _locate_backend_routes_tables(lines: list[str], fenced: set[int] = frozenset()) -> list[tuple[int, int]]:
    """Return [start, end) line ranges of every pipe-table under `## Backend Routes`.

    Template nests one table per `### File:` sub-heading, so this collects EVERY
    contiguous pipe-block before the next `## ` heading, generalizing
    `_locate_screen_list_table`'s bounded single-table scan to multiple tables.

    Fence-scoped (C1): `fenced` (from `_fenced_line_indices`) marks lines inside a
    fenced block; a `|`-prefixed line there is documentation, not a real table row,
    and is skipped like any other non-table line — a fabricated example under the
    heading can no longer be picked up as a real span.
    """
    head = re.compile(r"#+\s*Backend Routes\b", re.IGNORECASE)
    start = next((i + 1 for i, l in enumerate(lines) if head.match(l.strip())), None)
    if start is None:
        return []
    spans: list[tuple[int, int]] = []
    i = start
    n = len(lines)
    while i < n:
        s = lines[i].strip()
        if s.startswith("## "):
            break
        if s.startswith("|") and i not in fenced:
            tbl_start = i
            while i < n and lines[i].strip().startswith("|") and i not in fenced:
                i += 1
            spans.append((tbl_start, i))
        else:
            i += 1
    return spans


def _is_migrated_header(header_line: str) -> bool:
    """True if a Backend Routes header row already has BOTH Code and Owner F### cells."""
    cells = [c.strip().casefold() for c in header_line.strip().strip("|").split("|")]
    return any(_CODE_HEADER.match(h) for h in cells) and \
        any(_OWNER_HEADER.match(h) for h in cells)


def backfill_route_list(
    text: str, citation_map: dict[str, list[str]]
) -> tuple[str, bool, int, list[str]]:
    """Insert `Code` (3rd) and `Owner F###` (4th) columns into every un-migrated
    Backend Routes table. Returns (new_text, changed, unattributed_count, warnings).

    Idempotency is decided PER TABLE (C1): a route-list.md can be in a
    half-migrated state (hand-edited, or a partial prior run) where one
    `### File:` sub-table already has both columns and another doesn't — each
    span's own header decides whether that table is touched; already-migrated
    tables are left byte-identical. ROUTE### numbering stays globally contiguous
    by seeding the counter from 1 + the highest existing ROUTE### found in any
    already-migrated table, so a partial re-run keeps numbering stable.

    C1: fenced example tables under the heading are excluded from span detection
    (never migrated, never counted toward numbering).
    C2: a data row whose cell count doesn't match the header (e.g. an unescaped
    `|` inside Path/Handler) is left byte-identical and WARNed — never written
    corrupted, matching the "empty cell -> WARN" degradation contract's spirit.
    C5: a table missing its `|---|` separator row is detected via `_SEP_ROW`
    (shared with `_nav_table_parse_lib.data_rows`) so the first data row is
    treated as data, not mistaken for the separator and overwritten.
    """
    lines = text.splitlines(keepends=True)
    fenced = _fenced_line_indices(text)
    spans = _locate_backend_routes_tables(lines, fenced)
    if not spans:
        return text, False, 0, []

    migrated_spans = {s for s in spans if _is_migrated_header(lines[s[0]])}
    if len(migrated_spans) == len(spans):
        return text, False, 0, []  # every table already migrated — true no-op

    next_num = 1
    for tbl_start, tbl_end in migrated_spans:
        table_text = "".join(lines[tbl_start:tbl_end])
        for m in _ROUTE_CODE.finditer(table_text):
            next_num = max(next_num, int(m.group(1)) + 1)

    unattributed = 0
    warnings: list[str] = []
    for tbl_start, tbl_end in spans:
        if (tbl_start, tbl_end) in migrated_spans:
            continue  # untouched, byte-identical
        header_cells = lines[tbl_start].strip().strip("|").split("|")
        header_n = len(header_cells)
        has_sep = tbl_end - tbl_start > 1 and _SEP_ROW.match(lines[tbl_start + 1].strip() or "")
        for idx in range(tbl_start, tbl_end):
            ln = lines[idx]
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            eol = ln[len(ln.rstrip("\r\n")):]  # preserve LF or CRLF
            pos = idx - tbl_start  # 0=header, 1=sep-or-data (see has_sep), 2+=data
            if pos == 0:
                cells[2:2] = ["Code", "Owner F###"]
            elif pos == 1 and has_sep:
                cells[2:2] = ["------", "------------"]
            else:
                if len(cells) != header_n:
                    warnings.append(
                        f"route-list.md: table row {idx + 1} cell-count {len(cells)} != "
                        f"header {header_n} (embedded '|'?) — left unmigrated"
                    )
                    continue  # never write a corrupted row (C2)
                code = f"ROUTE{next_num:03d}"
                next_num += 1
                owners = citation_map.get(code)
                owner_cell = ", ".join(owners) if owners else "—"
                if not owners:
                    unattributed += 1
                cells[2:2] = [code, owner_cell]
            lines[idx] = "| " + " | ".join(cells) + " |" + eol
    return "".join(lines), True, unattributed, warnings


def migrate(docs_root: Path) -> int:
    specs = sorted(docs_root.glob("features/*/technical-spec.md"))
    if not specs:
        print("[WARN] no docs/features/*/technical-spec.md files found — "
              "run the feature-specs pass first; no changes made.")
        return 0

    citation_map = parse_technical_spec_citations(docs_root)

    rl = docs_root / "generated" / "route-list.md"
    if not rl.is_file():
        print("no docs/generated/route-list.md found — no changes needed.")
        return 0

    text = rl.read_text(encoding="utf-8")
    new_text, changed, unattributed, warnings = backfill_route_list(text, citation_map)
    for w in warnings:
        print(f"[WARN] {w}", file=sys.stderr)
    if not changed:
        print("already migrated — no changes needed.")
        return 0

    try:
        rl.write_text(new_text, encoding="utf-8")
    except OSError as e:
        print(f"[ERROR] {rl}: {e}", file=sys.stderr); return 1

    print(f"migrated 1 file(s); {unattributed} route(s) left unattributed ('—').")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill feature↔API/route ID binding (v25.0.0)")
    p.add_argument("--docs-root", default="./docs", type=Path,
                   help="docs/ (or docs/<lang>/) root (default: ./docs)")
    args = p.parse_args()
    sys.exit(migrate(args.docs_root))


if __name__ == "__main__":
    main()
