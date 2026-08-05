#!/usr/bin/env python3
# layout-exempt: rebuild-spec migration — docs/features|screens|generated paths are managed targets
"""Idempotent migration (v24.0.0): backfill the feature↔screen ID binding.

Forward  — adds the `SCR###` column to each docs/features/F###/screens.md Screen List,
           resolving each row's screen name via generated/screen-list.md (the same Name
           strings the researcher authored → reliable). Unresolved rows get "—".
Reverse  — adds `**Feature**: F###_Name` to each docs/screens/SCR###/spec.md header,
           sourced from screen-flow.md § Feature Entry Points (the only ownership signal).

Idempotent: a screens.md that already has an SCR### column, or a spec.md that already
has a **Feature** line, is left untouched. Non-destructive: only inserts a column/line —
never rewrites prose cells. If the § Feature Entry Points bridge is absent, the migration
reports and exits 0 WITHOUT changes ("run the core rebuild first").

Stdlib only. Exit 0 on success/no-op/missing-bridge; non-zero only on write error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _nav_table_parse_lib import index_screen_list, norm_name  # noqa: E402

_SCR_TOKEN = re.compile(r"\bSCR\d{3}(?:_\w+)?")
_F_PREFIX = re.compile(r"\bF\d{3}")
_FXXX_DIR = re.compile(r"^F\d{3}(?:_.*)?$")
_SCRXXX_DIR = re.compile(r"^SCR\d{3}(?:_.*)?$")
_SCR_HEADER = re.compile(r"\bscr(\b|#|\d)")


def parse_entry_points(screen_flow_md: str) -> dict[str, str]:
    """Map each owned SCR### code → its owning feature token (F###_Name).

    Reads the `## Feature Entry Points` section, splits on `### F###_Name`, and within
    each block takes the `**Owned screens**` sub-bullets as the ownership signal (entry/
    exit screens may belong to OTHER features). Returns {} when the bridge is absent.
    """
    m = re.search(r"^##\s+Feature Entry Points\s*$(.*?)(?=^##\s|\Z)",
                  screen_flow_md, re.MULTILINE | re.DOTALL)
    if not m:
        return {}
    body = m.group(1)
    out: dict[str, str] = {}
    blocks = re.split(r"^###\s+(F\d{3}\w*)\s*$", body, flags=re.MULTILINE)
    # re.split keeps captured group: [pre, fcode1, body1, fcode2, body2, ...]
    for i in range(1, len(blocks) - 1, 2):
        fcode = blocks[i].strip()
        block = blocks[i + 1]
        owned = _owned_section(block)
        for scr in _SCR_TOKEN.findall(owned):
            out.setdefault(scr, fcode)  # first owner wins
    return out


def _owned_section(block: str) -> str:
    """Return the text of the `**Owned screens/forms**` sub-block within a feature block."""
    lines = block.splitlines()
    collecting = False
    owned: list[str] = []
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^- \*\*Owned (?:screens|forms)\*\*\s*:?(.*)$", s)
        if m:
            collecting = True
            owned.append(m.group(1))  # capture any code inline on the heading (reviewer I1)
            continue
        if collecting and re.match(r"^- \*\*", s):
            break  # next top-level bullet (Exit screens) → owned block ended
        if collecting:
            owned.append(ln)
    return "\n".join(owned)


# ---------------------------------------------------------------------------
# forward — insert the SCR### column into a screens.md Screen List table
# ---------------------------------------------------------------------------

def _locate_screen_list_table(lines: list[str]) -> tuple[int, int] | None:
    """Return the [start, end) line range of the Screen List table, or None.

    Scans from the `## Screen List` heading to the FIRST contiguous block of pipe
    rows, skipping intervening blank/comment/note lines. Bounded by the next `## `
    heading (so a background-only feature with no table yields None). Returning an
    exact line window — NOT set membership — is what stops a second identically-
    headed table elsewhere in screens.md from being corrupted (reviewer C1).
    """
    head = re.compile(r"#+\s*Screen List\b", re.IGNORECASE)
    start = next((i + 1 for i, l in enumerate(lines) if head.match(l.strip())), None)
    if start is None:
        return None
    tbl_start = None
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("## "):
            return None  # next section reached, no table
        if s.startswith("|"):
            tbl_start = i
            break
    if tbl_start is None:
        return None
    tbl_end = tbl_start
    while tbl_end < len(lines) and lines[tbl_end].strip().startswith("|"):
        tbl_end += 1
    return tbl_start, tbl_end


def backfill_screens_md(text: str, name_to_code: dict[str, str]) -> tuple[str, bool, int]:
    """Insert an SCR### column (2nd) into the Screen List table. Returns
    (new_text, changed, unresolved_count). No-op if the column already exists or no table.
    """
    lines = text.splitlines(keepends=True)
    span = _locate_screen_list_table(lines)
    if span is None:
        return text, False, 0
    tbl_start, tbl_end = span
    header_cells = [c.strip() for c in lines[tbl_start].strip().strip("|").split("|")]
    if any(_SCR_HEADER.search(h.casefold()) for h in header_cells):
        return text, False, 0  # already migrated
    unresolved = 0
    for idx in range(tbl_start, tbl_end):
        ln = lines[idx]
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        eol = ln[len(ln.rstrip("\r\n")):]  # preserve LF or CRLF (reviewer M1)
        pos = idx - tbl_start  # 0=header, 1=separator, 2+=data
        if pos == 0:
            cells.insert(1, "SCR###")
        elif pos == 1:
            cells.insert(1, "--------")
        else:
            code = name_to_code.get(norm_name(cells[0])) if cells else None
            if not code:
                unresolved += 1
            cells.insert(1, code or "—")
        lines[idx] = "| " + " | ".join(cells) + " |" + eol
    return "".join(lines), True, unresolved


# ---------------------------------------------------------------------------
# reverse — insert the **Feature** backlink into a screen-spec header
# ---------------------------------------------------------------------------

def backfill_screen_spec(text: str, feature_token: str) -> tuple[str, bool]:
    """Insert `**Feature**: <token>` after the **Screen** header line. No-op if present."""
    if re.search(r"^\*\*Feature\*\*\s*:", text, re.MULTILINE):
        return text, False
    m = re.search(r"^\*\*Screen\*\*\s*:.*$", text, re.MULTILINE)
    if not m:
        return text, False
    insert_at = m.end()
    return text[:insert_at] + f"\n**Feature**: {feature_token}" + text[insert_at:], True


def migrate(docs_root: Path) -> int:
    sf = docs_root / "generated" / "screen-flow.md"
    scr_to_feat = parse_entry_points(sf.read_text(encoding="utf-8")) if sf.is_file() else {}
    if not scr_to_feat:
        print("[WARN] no § Feature Entry Points bridge found in screen-flow.md — "
              "run the core rebuild first; no changes made.")
        return 0

    sl = docs_root / "generated" / "screen-list.md"
    name_to_code = index_screen_list(sl.read_text(encoding="utf-8")) if sl.is_file() else {}

    changed = unresolved = errors = 0
    for screens_md in sorted((docs_root / "features").glob("*/screens.md")):
        text = screens_md.read_text(encoding="utf-8")
        new_text, did, miss = backfill_screens_md(text, name_to_code)
        unresolved += miss
        if did:
            try:
                screens_md.write_text(new_text, encoding="utf-8")
                changed += 1
            except OSError as e:
                print(f"[ERROR] {screens_md}: {e}", file=sys.stderr); errors += 1
    for spec in sorted((docs_root / "screens").glob("*/spec.md")):
        sm = _SCRXXX_DIR.match(spec.parent.name)
        if not sm:
            continue
        scr_pref = re.match(r"SCR\d{3}", spec.parent.name).group(0)
        token = next((f for s, f in scr_to_feat.items() if s.startswith(scr_pref)), None)
        if not token:
            continue
        text = spec.read_text(encoding="utf-8")
        new_text, did = backfill_screen_spec(text, token)
        if did:
            try:
                spec.write_text(new_text, encoding="utf-8")
                changed += 1
            except OSError as e:
                print(f"[ERROR] {spec}: {e}", file=sys.stderr); errors += 1

    print(f"migrated {changed} file(s); {unresolved} unresolved screen name(s) left as '—'."
          if changed else "already migrated — no changes needed.")
    return 1 if errors else 0


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill feature↔screen ID binding (v24.0.0)")
    p.add_argument("--docs-root", default="./docs", type=Path,
                   help="docs/ (or docs/<lang>/) root (default: ./docs)")
    args = p.parse_args()
    sys.exit(migrate(args.docs_root))


if __name__ == "__main__":
    main()
