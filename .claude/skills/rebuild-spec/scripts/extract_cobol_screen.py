#!/usr/bin/env python3
"""COBOL screen router (Phase 01 foundation).

Sniffs each COBOL source file and dispatches it to the right paradigm lib:
  - basename `*.bms` OR an anchored BMS macro line (`DFHMSD`/`DFHMDI`/`DFHMDF` in the
    operand-column shape, never a bare substring check) -> `_cobol_bms_lib`
  - `SCREEN SECTION` keyword present -> `_cobol_screen_section_lib`
  - a file matching BOTH is fed to BOTH libs and their ScreenRecs are merged at finalize()
  - neither -> no screen contribution (file skipped)

Fixed contract (owned here so Phase 02/03 never reopen this router):
  each lib exposes `feed(path, lines)` (accumulate) + `finalize() -> list[ScreenRec]`,
  called once per lib after every source file has been seen (BMS needs a whole-corpus
  MAPSET join before it can emit).

Guards: per-file byte cap, post-decode EBCDIC/binary sanity check (never a silent
zero-screen result), try/except around every feed() call, exit 0 always (advisory).
Contract: decode_source(), atomic digest-shard write, manifest update, credential scrub
happens in the paradigm libs (Phase 02/03) — this router does not parse content itself.

Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _cobol_bms_lib import BmsLib
from _cobol_dispatch_lib import (
    looks_like_cobol,
    matches_bms_macro,
    matches_exec_cics_map,
    matches_screen_section,
)
from _cobol_screen_section_lib import ScreenSectionLib
from _extractor_lib import (
    decode_source,
    is_extractor_completed,
    source_tree_hash,
    update_manifest,
    write_digest_atomic,
)

EXTRACTOR_NAME = "extract_cobol_screen"

_SOURCE_GLOBS = ["*.cbl", "*.cob", "*.cpy", "*.bms"]
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__", "target",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}
_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB — skip pathologically large source before reading


def _process_file(
    path: Path,
    root: Path,
    section_lib: ScreenSectionLib,
    bms_lib: BmsLib,
    primary: str,
    fallback: str,
) -> list[str]:
    """Sniff + dispatch one file. Returns warnings; never raises (exit-0-always contract)."""
    rel = str(path.relative_to(root))
    warnings: list[str] = []

    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            warnings.append(
                f"skipped_oversized: {rel} exceeds {_MAX_FILE_BYTES // (1024 * 1024)}MB"
            )
            return warnings
    except OSError as e:
        warnings.append(f"stat_error: {rel}: {e}")
        return warnings

    try:
        text, decode_warns = decode_source(path, primary, fallback)
        warnings.extend(decode_warns)
    except OSError as e:
        warnings.append(f"read_error: {rel}: {e}")
        return warnings

    lines = text.splitlines()

    # [Red-team fix 4] Never silently report zero screens on an EBCDIC/binary mis-guess.
    if not looks_like_cobol(lines):
        warnings.append(f"possible_ebcdic_or_binary: {rel}")
        return warnings

    # A calling program that only references a map (EXEC CICS SEND/RECEIVE MAP) without
    # containing its own BMS macro definitions -- the normal real-world split between a
    # map deck and the programs that use it -- must still reach BmsLib, else the
    # reachability join never sees its only evidence for that program.
    is_bms = (
        path.suffix.lower() == ".bms"
        or matches_bms_macro(lines)
        or matches_exec_cics_map(lines)
    )
    is_screen_section = matches_screen_section(lines)

    if is_bms:
        try:
            bms_lib.feed(rel, lines)
        except Exception as e:  # exit-0-always: never let a lib bug crash the router
            warnings.append(f"parse_error: {rel}: {e}")
    if is_screen_section:
        try:
            section_lib.feed(rel, lines)
        except Exception as e:
            warnings.append(f"parse_error: {rel}: {e}")

    return warnings


def extract(
    root: str | Path,
    plan_dir: str | Path,
    encoding: str = "utf-8",
    fallback: str = "latin-1",
    file_cap: int = 100_000,
) -> dict[str, Any]:
    """Run the COBOL screen router over root. Returns the digest dict."""
    root_p = Path(root).resolve()
    plan_p = Path(plan_dir).resolve()

    section_lib = ScreenSectionLib(root=root_p)
    bms_lib = BmsLib()

    all_warnings: list[str] = []
    file_count = 0
    error_count = 0

    for dirpath, dirnames, filenames in os.walk(str(root_p), followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if file_count >= file_cap:
                all_warnings.append("file_cap_reached")
                break
            if not any(fnmatch.fnmatch(fn.lower(), g) for g in _SOURCE_GLOBS):
                continue

            full_path = Path(dirpath) / fn
            file_count += 1

            try:
                warns = _process_file(full_path, root_p, section_lib, bms_lib, encoding, fallback)
            except Exception as e:  # belt-and-suspenders: exit-0-always at the file level too
                warns = [f"parse_error: {full_path.relative_to(root_p)}: {e}"]

            if any(w.startswith(("read_error", "stat_error", "parse_error")) for w in warns):
                error_count += 1
            all_warnings.extend(warns)
        else:
            continue
        break  # file_cap hit

    screens = section_lib.finalize() + bms_lib.finalize()

    digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_tree_hash": source_tree_hash(root_p, _SOURCE_GLOBS),
        "screens": screens,
        "warnings": all_warnings,
    }

    write_digest_atomic(plan_p, EXTRACTOR_NAME, digest)
    update_manifest(plan_p, EXTRACTOR_NAME, file_count, error_count)
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="COBOL screen router: SCREEN-SECTION/BMS sniff-dispatch -> screens digest shard.",
    )
    parser.add_argument("--root", required=True, help="Project root to scan.")
    parser.add_argument("--plan-dir", required=True, help="Active plan directory.")
    parser.add_argument("--encoding", default="utf-8", help="Primary source encoding.")
    parser.add_argument("--fallback", default="latin-1", help="Fallback encoding.")
    parser.add_argument("--file-cap", type=int, default=100_000)
    args = parser.parse_args(argv)

    plan_p = Path(args.plan_dir).resolve()

    # Exit-0-always is enforced at the CLI boundary too — malformed input must never crash.
    try:
        if is_extractor_completed(plan_p, EXTRACTOR_NAME):
            print(json.dumps({"status": "skipped", "reason": "already completed"}))
            return 0
        digest = extract(args.root, plan_p, args.encoding, args.fallback, args.file_cap)
        print(json.dumps({
            "status": "ok",
            "screens": len(digest["screens"]),
            "warnings": len(digest["warnings"]),
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "warning": f"router_failure: {e}"}), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
