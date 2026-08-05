#!/usr/bin/env python3
# layout-exempt: rebuild-spec migration — docs/features|screens|generated paths are managed targets
"""Idempotent migration (v26.0.0): flags specs missing A3 `## Source Walkthrough` and/or
B4 `## DB Impact per Event`.

Unlike `migrate-feature-screen-ids.py` (which backfills a column resolvable purely from
existing doc cross-refs), A3/B4 cannot be mechanically backfilled from doc text alone — both
require re-reading source code, which only the researcher pass can do (Q3,
research/researcher-01-pass-extension-mechanics.md). This script NEVER edits a file; it only
reports which specs still need a re-run of the researcher pass.

Idempotent: a spec that already carries both headings is a silent no-op. Stdlib only.
Exit 0 always — this is a reporting tool, not a gate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _spec_constants import A3_HEADING, B4_HEADING  # noqa: E402


def _has_section(text: str, heading: str) -> bool:
    return any(ln.rstrip() == heading for ln in text.splitlines())


def _read(spec: Path) -> str | None:
    """Read `spec`; None (never raise) on any OSError — unreadable/vanished/broken symlink.
    Mirrors validate_reading_guide_db_impact.py's `_read()` and the v24 precedent
    (migrate-feature-screen-ids.py) — this script's contract is "exit 0 always"."""
    try:
        return spec.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"[WARN] {spec}: unreadable, skipping ({exc}).")
        return None


def migrate(docs_root: Path) -> int:
    tech_specs = sorted(docs_root.glob("features/*/technical-spec.md"))
    screen_specs = sorted(docs_root.glob("screens/*/spec.md"))
    if not tech_specs and not screen_specs:
        print(f"[WARN] no technical-spec.md or screen spec.md found under {docs_root} — "
              "run the core/feature-specs/screen-specs pass first; no changes made.")
        return 0

    # Minor fix: a file `_read` can't open (permission-denied, vanished, broken symlink)
    # was previously `continue`d straight past every tally — silently dropped from both the
    # missing-count AND the summary line, indistinguishable from "already compliant". It now
    # gets its own `unreadable` category so the summary is honest about what was skipped.
    missing_walkthrough = missing_db_impact = unreadable = 0
    for spec in tech_specs:
        text = _read(spec)
        if text is None:
            unreadable += 1
            continue
        if not _has_section(text, A3_HEADING):
            missing_walkthrough += 1
            print(f"[WARN] {spec}: missing {A3_HEADING!r} — requires re-running researcher "
                  "pass (not backfillable from doc text).")
        if not _has_section(text, B4_HEADING):
            missing_db_impact += 1
            print(f"[WARN] {spec}: missing {B4_HEADING!r} — requires re-running researcher "
                  "pass (not backfillable from doc text).")
    for spec in screen_specs:
        text = _read(spec)
        if text is None:
            unreadable += 1
            continue
        if not _has_section(text, A3_HEADING):
            missing_walkthrough += 1
            print(f"[WARN] {spec}: missing {A3_HEADING!r} — requires re-running researcher "
                  "pass (not backfillable from doc text).")

    total = len(tech_specs) + len(screen_specs)
    if missing_walkthrough == 0 and missing_db_impact == 0 and unreadable == 0:
        print(f"already migrated — all {total} spec(s) carry the required sections; "
              "no changes needed.")
    else:
        unreadable_note = f", {unreadable} unreadable — not checked" if unreadable else ""
        print(f"scanned {total} spec(s): {missing_walkthrough} missing {A3_HEADING!r}, "
              f"{missing_db_impact} missing {B4_HEADING!r} (technical-spec.md only)"
              f"{unreadable_note}. "
              "No files modified — re-run the researcher pass for the flagged specs.")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(
        description="Flag specs missing Source Walkthrough (A3) / DB Impact per Event (B4) "
                     "sections (v26.0.0)")
    p.add_argument("--docs-root", default="./docs", type=Path,
                   help="docs/ (or docs/<lang>/) root (default: ./docs)")
    args = p.parse_args()
    sys.exit(migrate(args.docs_root))


if __name__ == "__main__":
    main()
