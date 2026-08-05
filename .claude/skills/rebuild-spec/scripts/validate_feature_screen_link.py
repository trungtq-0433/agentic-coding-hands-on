#!/usr/bin/env python3
# layout-exempt: rebuild-spec validator — docs/features|screens|generated paths are managed targets
"""Phase B (v24.0.0) — feature↔screen ID-link deterministic validator.

Binds the two ID systems both ways and checks each side resolves:
  forward  — every screens.md Screen-List row's SCR### ∈ screen-list.md inventory
  reverse  — every screen-spec **Feature** F### ∈ feature-list.md inventory

Degradation contract (CRITICAL — never break un-migrated repos):
  - NO SCR### column at all / NO **Feature** line at all → WARN `link.pre_migration`
    (whole-file signal: this doc predates the binding; do not fail the build).
  - column/line PRESENT but the code is unresolvable → FAIL `link.scr_unresolved`
    / `link.feature_unresolved` (real drift on a migrated doc).
  - an empty / "—" / placeholder cell on a migrated table → soft `link.unmapped`
    WARN (still being filled in; not drift).

Resolution is by the bare SCR###/F### prefix, so a slug mismatch
(SCR001_Login vs SCR001_LoginForm) still resolves; only a wrong NUMBER fails.

Stdlib only. Exit codes: 0 (PASS/WARN), 1 (FAIL critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _nav_table_parse_lib import _first_table_after, _split_row  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, recalculate_totals,
)

VALIDATOR = "feature_screen_link"

_SCR_PREFIX = re.compile(r"\bSCR\d{3}", re.IGNORECASE)
_F_PREFIX = re.compile(r"\bF\d{3}", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"^\s*(—|-|\{.*\}|n/?a)?\s*$", re.IGNORECASE)
_BACKGROUND = re.compile(r"background\s+feature", re.IGNORECASE)


def _issue(sev: str, rid: str, file_path: str, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": file_path}, "message": msg}


def _prefix(code: str, pat: re.Pattern) -> str | None:
    m = pat.search(code or "")
    return m.group(0).upper() if m else None


def build_inventory(text: str, pat: re.Pattern) -> set[str]:
    """Return the set of bare ID prefixes (SCR###/F###) named anywhere in text."""
    return {m.group(0).upper() for m in pat.finditer(text or "")}


# "scr" followed by a boundary, "#", or a digit — matches "SCR" / "SCR###" but NOT
# "Screen" (where "scr" is followed by the word char "e").
_SCR_HEADER = re.compile(r"\bscr(\b|#|\d)")


def _scr_column_idx(header: list[str]) -> int | None:
    for i, h in enumerate(header):
        if _SCR_HEADER.search(h.casefold()):
            return i
    return None


def check_screens_md(text: str, scr_inventory: set[str], file_path: str) -> list[dict]:
    """Forward check: each SCR### in the Screen List table resolves to the inventory."""
    if _BACKGROUND.search(text) and not _first_table_after(text, r"#+\s*Screen List\b"):
        return []  # background-only feature, no UI table — N/A
    table = _first_table_after(text, r"#+\s*Screen List\b")
    if len(table) < 2:
        return []  # no parseable table — nothing to bind (not a migration signal)
    header = _split_row(table[0])
    scr_idx = _scr_column_idx(header)
    if scr_idx is None:
        return [_issue("warning", "link.pre_migration", file_path,
                       "screens.md Screen List has no SCR### column (pre-migration); "
                       "run migrate-feature-screen-ids.py")]
    issues: list[dict] = []
    for raw in table[2:]:
        cells = _split_row(raw)
        if scr_idx >= len(cells):
            continue
        name = cells[0] if cells else "?"
        if name.startswith("{"):
            continue  # template placeholder row
        cell = cells[scr_idx]
        if _PLACEHOLDER.match(cell):
            issues.append(_issue("warning", "link.unmapped", file_path,
                                 f"screen {name!r} has no SCR### yet (unmapped)"))
            continue
        pref = _prefix(cell, _SCR_PREFIX)
        if pref is None or pref not in scr_inventory:
            issues.append(_issue("critical", "link.scr_unresolved", file_path,
                                 f"SCR code {cell!r} for screen {name!r} does not resolve "
                                 f"to screen-list.md"))
    return issues


def check_screen_spec(text: str, feature_inventory: set[str], file_path: str) -> list[dict]:
    """Reverse check: the **Feature** header backlink resolves to feature-list.md."""
    m = re.search(r"^\*\*Feature\*\*\s*:\s*(.+)$", text, re.MULTILINE)
    if m is None:
        return [_issue("warning", "link.pre_migration", file_path,
                       "screen-spec header has no **Feature** backlink (pre-migration); "
                       "run migrate-feature-screen-ids.py")]
    value = m.group(1).strip()
    if _PLACEHOLDER.match(value) or value.startswith("{"):
        return [_issue("warning", "link.unmapped", file_path,
                       "screen-spec **Feature** backlink is not filled in yet")]
    pref = _prefix(value, _F_PREFIX)
    if pref is None or pref not in feature_inventory:
        return [_issue("critical", "link.feature_unresolved", file_path,
                       f"Feature code {value!r} does not resolve to feature-list.md")]
    return []


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def validate(root: Path) -> dict:
    """Walk a docs/ or artifacts/ root and aggregate forward + reverse link issues."""
    issues: list[dict] = []
    # Inventories: prefer generated/ (docs layout); fall back to root (artifacts layout).
    def _find(name: str) -> Path | None:
        for cand in (root / "generated" / name, root / name):
            if cand.is_file():
                return cand
        return None

    sl = _find("screen-list.md")
    fl = _find("feature-list.md")

    # Inventory ABSENT ⇒ cannot verify ⇒ skip that direction (a missing inventory is not
    # drift — failing here would wrongly break a screen-specs-only or partial run). Only an
    # inventory that EXISTS but lacks the code is real drift.
    if sl is None:
        issues.append(_issue("warning", "link.inventory_absent", str(root / "generated"),
                             "screen-list.md not found — forward SCR### link check skipped"))
    else:
        scr_inv = build_inventory(_read(sl), _SCR_PREFIX)
        for screens_md in sorted((root / "features").glob("*/screens.md")):
            issues += check_screens_md(_read(screens_md), scr_inv, str(screens_md))
    if fl is None:
        issues.append(_issue("warning", "link.inventory_absent", str(root / "generated"),
                             "feature-list.md not found — reverse Feature link check skipped"))
    else:
        feat_inv = build_inventory(_read(fl), _F_PREFIX)
        for spec in sorted((root / "screens").glob("*/spec.md")):
            issues += check_screen_spec(_read(spec), feat_inv, str(spec))

    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec v24 feature↔screen link validator")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--docs-root", help="docs/ (or docs/<lang>/) root to validate")
    g.add_argument("--plan-dir", help="plan dir; validates <plan>/artifacts/")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    proj = resolve_project_root(args.project_root)

    root = (Path(args.docs_root) if args.docs_root
            else Path(args.plan_dir) / "artifacts").resolve()
    if not root.is_dir():
        print(f"[ERROR] root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        assert_under(root, proj)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    try:
        result = validate(root)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, proj)
            summary = load_summary(sp, root.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"], "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2
    return 1 if result["summary"]["critical"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
