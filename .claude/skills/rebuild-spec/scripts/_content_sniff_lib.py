#!/usr/bin/env python3
"""Content-sniff signal library (Phase 07, Track D) -- pure, stdlib-only.

`sniff_ui(root, file_cap)` walks an UNRECOGNIZED-stack repo for hidden-UI evidence:
keyword-family hits (see `_content_sniff_signals_lib`) plus a language-agnostic
menu-loop structural detector, tiered per phase-07's confidence taxonomy (reusing
the EXTRACTED/INFERRED/AMBIGUOUS spirit from the `confidence` skill, not
reinventing it):

  Tier 0: no hit -- silent.
  Tier 1: single keyword, no structural corroboration -- scan metadata ONLY,
          never surfaced as a doc claim (INFERRED/AMBIGUOUS territory).
  Tier 2: keyword + structural corroboration (stdin-read AND menu-loop AND no
          GUI-toolkit import, all within the same file) -- gated behind a later
          Phase 09 user question, cited file:line evidence only, never
          auto-generates a screen artifact (EXTRACTED-grade evidence).

Zero filesystem writes, zero network, zero side effects -- a later phase (08)
owns wiring this into detect_stack_profile.py. Walk discipline (_SKIP_DIRS, file
cap) mirrors `_stack_profile_lib.match_profiles` -- reused, not reinvented.

Every signal's citation is `relpath:line: <scrubbed excerpt>`. `_excerpt()` routes
each line through BOTH scrubbers before it is embedded (fix C6): the
generic-secret scrub (CLI flags/api_key/token/secret/password/Bearer/PEM/
URI-credential shapes, `_content_sniff_signals_lib.scrub_generic_secret`) AND
the SQL-shaped credential scrub (connection-string/DSN shapes,
`_sql_parse_lib.scrub_credentials`) -- so no secret shape survives depending
on which scrubber happens to recognize it.

Stdlib only.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from _content_sniff_signals_lib import (
    SIGNAL_FAMILIES,
    STDIN_READ_TOKENS,
    VB6_FORM_SUFFIX,
    apply_guards,
    is_gui_toolkit_import,
    scan_menu_loop,
    scrub_generic_secret,
)
from _sql_parse_lib import scrub_credentials

# Intra-file deadline check cadence (fix C7) -- checked every K lines inside a
# single file's scan, not just between files in the os.walk loop.
_DEADLINE_CHECK_EVERY = 512

# Mirrors _stack_profile_lib._SKIP_DIRS (walk discipline reused, not reinvented).
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__", "target",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}

_MAX_FILE_BYTES = 10 * 1024 * 1024   # red-team fix 9 -- per-file byte cap
_DEFAULT_DEADLINE_SECONDS = 30.0     # red-team fix 11 -- aggregate wall-clock bound


def _excerpt(line: str) -> str:
    """Scrubbed, length-bounded line text safe to embed in a citation. Routes
    through BOTH scrubbers (fix C6): generic-secret shapes, then the
    SQL-shaped credential scrub."""
    text = scrub_generic_secret(line.strip())
    text, _redacted = scrub_credentials(text)
    return text[:300]


def _scan_file(
    lines: list[str],
    rel: str,
    deadline_check: Callable[[], bool] = lambda: False,
) -> tuple[list[dict], bool, bool, bool]:
    """Scan one file's lines. Returns (signals, stdin_ok, menu_loop_hit,
    deadline_hit); stdin_ok requires a stdin-read hit AND no GUI-toolkit
    import in-file. `deadline_hit` (fix C7): bailed early, mid-file, to a
    partial verdict instead of overrunning the aggregate deadline."""
    signals: list[dict] = []
    file_has_exec_cics = any("EXEC CICS" in ln.upper() for ln in lines)
    file_has_gui_import = any(is_gui_toolkit_import(ln) for ln in lines)
    stdin_hit = False
    deadline_hit = False
    for idx, line in enumerate(lines, start=1):
        if idx % _DEADLINE_CHECK_EVERY == 0 and deadline_check():
            deadline_hit = True
            break
        for fp in SIGNAL_FAMILIES:
            if not fp.regex.search(line) or apply_guards(fp.family, fp.token, line, file_has_exec_cics):
                continue
            stdin_hit = stdin_hit or fp.token in STDIN_READ_TOKENS
            signals.append({
                "family": fp.family,
                "token": fp.token,
                "citation": f"{rel}:{idx}: {_excerpt(line)}",
                "structural": False,
            })
    menu_line: int | None = None
    if not deadline_hit:
        menu_line, menu_deadline_hit = scan_menu_loop(lines, file_has_exec_cics, deadline_check)
        deadline_hit = deadline_hit or menu_deadline_hit
    if menu_line is not None:
        # "[code]" provenance marker (fix C8): only a code-shaped, non-comment
        # loop-start line reaches here -- make that guarantee visible.
        signals.append({
            "family": "menu_loop",
            "token": "menu-loop",
            "citation": f"{rel}:{menu_line}: [code] {_excerpt(lines[menu_line - 1])}",
            "structural": True,
        })
    return signals, stdin_hit and not file_has_gui_import, menu_line is not None, deadline_hit


def sniff_ui(
    root: str,
    file_cap: int = 50_000,
    deadline_seconds: float = _DEFAULT_DEADLINE_SECONDS,
) -> dict:
    """Pure signal scan of `root`. Returns `{tier: 0|1|2, signals: [...], summary}`.

    No filesystem writes, no network. Bounded by the same file cap + walk
    discipline as detection, a per-file byte cap (fix 9), and an aggregate
    wall-clock deadline (fix 11) checked BOTH between files AND inside a
    single file's line loop every `_DEADLINE_CHECK_EVERY` lines (fix C7) --
    never hangs on a large/heterogeneous repo, nor on one dense file."""
    signals: list[dict] = []
    tier2_eligible = False
    count = 0
    deadline_hit = False
    file_cap_hit = False
    start = time.monotonic()
    deadline_check: Callable[[], bool] = lambda: time.monotonic() - start > deadline_seconds

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if deadline_check():
            deadline_hit = True
            break
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if deadline_check():
                deadline_hit = True
                break
            count += 1
            if count > file_cap:
                file_cap_hit = True
                break
            path = Path(dirpath) / fn
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > _MAX_FILE_BYTES:
                continue
            rel = os.path.relpath(str(path), root)
            if path.suffix.lower() == VB6_FORM_SUFFIX:
                signals.append({
                    "family": "vb6_inputbox", "token": ".frm",
                    "citation": f"{rel}:0: <VB6 form file marker>", "structural": False,
                })
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            file_signals, stdin_ok, menu_hit, file_deadline_hit = _scan_file(
                text.splitlines(), rel, deadline_check
            )
            signals.extend(file_signals)
            if file_deadline_hit:
                deadline_hit = True
                break
            if stdin_ok and menu_hit:
                tier2_eligible = True
        if deadline_hit or file_cap_hit:
            break

    notes: list[str] = []
    if file_cap_hit:
        notes.append("file_cap_reached")
    if deadline_hit:
        notes.append("sniff_deadline_reached")

    tier = 0
    if signals:
        tier = 2 if tier2_eligible else 1

    summary = f"{len(signals)} signal(s), tier={tier}"
    if notes:
        summary += " (" + ", ".join(notes) + ")"
    return {"tier": tier, "signals": signals, "summary": summary}
