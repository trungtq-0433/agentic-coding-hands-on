#!/usr/bin/env python3
# layout-exempt: rebuild-spec validator — docs/features|generated paths are managed targets
"""Phase 2 (v25.0.0) — feature↔API/route ID-link deterministic validator.

Binds ROUTE###/F### both ways + twin-consistency:
  forward  — technical-spec.md / behavior-logic.md {ROUTE###} cites (Artifact
             References' Codes Used col) resolve to route-list.md's Code column.
  reverse  — route-list.md's Owner F### cell(s) resolve to feature-list.md.
  twin     — a feature's forward ROUTE### cite must be IN that route's reverse
             Owner F### set (multi-owner aware); a silent double-claim across
             features is a real correctness bug, not a WIP state.

Degradation contract (CRITICAL — never break un-migrated repos):
  - NO Code/Owner F### columns at all → WARN `link.pre_migration`.
  - column PRESENT but code unresolvable → FAIL `link.route_unresolved` /
    `link.feature_unresolved` (real drift on a migrated doc).
  - empty/"—"/placeholder cell on a migrated table → soft `link.unmapped` WARN.
    An unclaimed Owner (`—`) is NOT a twin-consistency mismatch.

Resolution is by the bare ROUTE###/F### prefix (numeric scheme, no slug question).
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
from _route_link_lib import (  # noqa: E402
    artifact_ref_cited_routes, build_route_inventory, build_route_owner_map_with_dups,
    iter_route_owner_rows,
)
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, recalculate_totals,
)

VALIDATOR = "feature_api_link"

_F_PREFIX = re.compile(r"\bF\d{3}", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"^\s*(—|-|\{.*\}|n/?a)?\s*$", re.IGNORECASE)


def _issue(sev: str, rid: str, file_path: str, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": file_path}, "message": msg}


def _prefix(code: str, pat: re.Pattern) -> str | None:
    m = pat.search(code or "")
    return m.group(0).upper() if m else None


def check_technical_spec(text: str, route_inventory: set[str], file_path: str) -> list[dict]:
    """Forward: {ROUTE###} cells in Artifact References' Codes Used column resolve."""
    issues: list[dict] = []
    for code in sorted(artifact_ref_cited_routes(text)):
        if code not in route_inventory:
            issues.append(_issue("critical", "link.route_unresolved", file_path,
                                 f"ROUTE code {code!r} does not resolve to route-list.md"))
    return issues


def check_route_list_owners(text: str, feature_inventory: set[str], file_path: str) -> list[dict]:
    """Reverse: each Owner F### cell (multi-value aware) resolves to feature-list.md."""
    rows = iter_route_owner_rows(text)
    if rows is None:
        return [_issue("warning", "link.pre_migration", file_path,
                       "route-list.md Backend Routes has no Code/Owner F### columns "
                       "(pre-migration); run migrate-feature-api-ids.py")]
    issues: list[dict] = []
    for route_code, owner_cell in rows:
        if route_code.startswith("{"):
            continue  # template placeholder row
        if _PLACEHOLDER.match(owner_cell):
            issues.append(_issue("warning", "link.unmapped", file_path,
                                 f"route {route_code!r} has no Owner F### yet (unmapped)"))
            continue
        for tok in re.split(r"[,/]", owner_cell):
            pref = _prefix(tok, _F_PREFIX)
            if pref is not None and pref not in feature_inventory:
                issues.append(_issue("critical", "link.feature_unresolved", file_path,
                                     f"Owner {tok.strip()!r} for route {route_code!r} does "
                                     f"not resolve to feature-list.md"))
    return issues


def check_owner_consistency(text: str, feature_dir_name: str,
                             route_owner: dict[str, set[str]], file_path: str) -> list[dict]:
    """Twin-consistency: a feature's forward ROUTE### citation must appear in that
    route's reverse Owner F### set. `—`/absent owner (empty set) is unclaimed, not
    a mismatch — only a DISAGREEING owner set is a real double-claim bug."""
    fcode = _prefix(feature_dir_name, _F_PREFIX)
    if fcode is None:
        return []
    issues: list[dict] = []
    for route_code in sorted(artifact_ref_cited_routes(text)):
        owners = route_owner.get(route_code)
        if not owners:
            continue  # route unresolved (already reported) or unclaimed — not a mismatch
        if fcode not in owners:
            issues.append(_issue("critical", "link.owner_mismatch", file_path,
                                 f"{feature_dir_name} cites {route_code!r} but route-list.md "
                                 f"Owner F### is {sorted(owners)!r} — twin-consistency mismatch"))
    return issues


def _build_feature_inventory(text: str) -> set[str]:
    """Bare F### prefixes named anywhere in feature-list.md."""
    return {m.group(0).upper() for m in _F_PREFIX.finditer(text or "")}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_inventory(root: Path, name: str) -> Path | None:
    for cand in (root / "generated" / name, root / name):
        if cand.is_file():
            return cand
    return None


def validate(root: Path) -> dict:
    """Walk a docs/ or artifacts/ root and aggregate forward + reverse + twin issues."""
    issues: list[dict] = []
    rl = _find_inventory(root, "route-list.md")
    fl = _find_inventory(root, "feature-list.md")

    # Inventory ABSENT ⇒ skip that direction (missing ≠ drift; only an EXISTING
    # inventory that lacks the code is real drift — never fail on a partial run).
    if rl is None:
        issues.append(_issue("warning", "link.inventory_absent", str(root / "generated"),
                             "route-list.md not found — forward ROUTE### link check skipped"))
    else:
        rl_text = _read(rl)
        # Pre-migration route-list.md (no Code/Owner F### columns) ⇒ the forward
        # inventory is necessarily empty, so every existing {ROUTE###} citation would
        # look "unresolvable" — that is NOT drift, it is exactly the advertised-but-
        # unimplemented state this release fixes. Emit ONE warning for the forward
        # direction and skip per-citation criticals entirely (mirrors check_screens_md).
        if iter_route_owner_rows(rl_text) is None:
            issues.append(_issue("warning", "link.pre_migration", str(rl),
                                 "route-list.md Backend Routes has no Code/Owner F### "
                                 "columns (pre-migration); run migrate-feature-api-ids.py"))
        else:
            route_inv = build_route_inventory(rl_text)
            route_owner, route_dups = build_route_owner_map_with_dups(root)
            for code in sorted(route_dups):
                issues.append(_issue("critical", "link.route_duplicate", str(rl),
                                     f"route {code!r} declared in multiple Backend Routes "
                                     f"rows — ROUTE### must be globally unique"))
            for spec in sorted((root / "features").glob("*/technical-spec.md")):
                issues += check_technical_spec(_read(spec), route_inv, str(spec))
                issues += check_owner_consistency(_read(spec), spec.parent.name, route_owner, str(spec))
            for bl in sorted((root / "features").glob("*/behavior-logic.md")):
                issues += check_technical_spec(_read(bl), route_inv, str(bl))

    if fl is None:
        issues.append(_issue("warning", "link.inventory_absent", str(root / "generated"),
                             "feature-list.md not found — reverse Owner F### link check skipped"))
    elif rl is not None:
        feat_inv = _build_feature_inventory(_read(fl))
        issues += check_route_list_owners(rl_text, feat_inv, str(rl))

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
    p = argparse.ArgumentParser(description="rebuild-spec v25 feature↔API/route link validator")
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
