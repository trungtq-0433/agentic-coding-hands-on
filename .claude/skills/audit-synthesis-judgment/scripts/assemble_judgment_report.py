#!/usr/bin/env python3
"""Phase 05 — assemble judgment-report.md from the three engines' findings JSON.

Merges Engine 1 (coverage), Engine 2 (boundary), Engine 3 (judgment) → dedupes →
**anchor-gates every finding** (per-engine) → renders the report + machine-readable frontmatter →
applies the ONE result rule.

The load-bearing invariant is enforced HERE:
  - FAIL comes ONLY from Engine-1 deterministic counts (orphans/phantoms/redundancy) or the
    --strict-coverage graphable case (coverage_status == FAIL). A stochastic Engine-2/3 signal can
    NEVER increment those counts.
  - Every finding must carry its computed anchor or it is dropped + logged (never silently kept):
      Engine-1 FAIL → an `evidence` field · Engine-2 → a cited `clause` · Engine-3 → `adjudicated: true`.
  - coverage_status is surfaced LOUDLY, distinct from result — a no-graph PASS is never a verified PASS.

Pure assembly — no LLM, no verdict of its own beyond applying the rule. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_project_root  # noqa: E402


def _load(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _gate_engine1(coverage: dict, log: list[str]) -> tuple[list, list, list]:
    """Keep only FAIL findings that carry a deterministic evidence field."""
    def _gate(items, label):
        kept = []
        for f in items:
            if f.get("evidence"):
                kept.append(f)
            else:
                log.append(f"[WARN] dropped Engine-1 {label} with no evidence anchor: {f}")
        return kept
    return (_gate(coverage.get("orphans", []), "orphan"),
            _gate(coverage.get("phantoms", []), "phantom"),
            _gate(coverage.get("duplicates", []), "duplicate"))


def _gate_engine2(boundary: dict, log: list[str]) -> list:
    kept = []
    for f in boundary.get("findings", []):
        if f.get("verdict") == "UNVERIFIABLE":
            kept.append(f)
        elif f.get("clause") or f.get("anchor"):
            kept.append(f)
        else:
            log.append(f"[WARN] dropped Engine-2 finding with no cited clause: {f}")
    return kept


def _gate_engine3(judgment: dict, log: list[str]) -> list:
    kept = []
    for f in judgment.get("findings", []):
        if not f.get("adjudicated"):
            log.append(f"[WARN] dropped Engine-3 WARN without adjudicated=true: {f.get('target')}")
            continue
        if not f.get("anchor"):
            log.append(f"[WARN] dropped Engine-3 WARN without anchor: {f.get('target')}")
            continue
        kept.append(f)
    return kept


def _dedupe(findings: list[dict]) -> list[dict]:
    """Dedupe by (engine, unit, kind, evidence) — never by free text (R2)."""
    seen: set[tuple] = set()
    out: list[dict] = []
    for f in findings:
        unit = f.get("source_file") or f.get("screen") or f.get("target") or f.get("us") or ""
        key = (f.get("engine"), unit, f.get("kind"), f.get("evidence", "")[:120])
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def _result(orphans: int, phantoms: int, redundancy: int, coverage_status: str) -> str:
    """The ONE result rule. FAIL only from Engine-1 counts or the strict-coverage graphable case."""
    if orphans > 0 or phantoms > 0 or redundancy > 0 or coverage_status == "FAIL":
        return "FAIL"
    return "PASS"


def assemble(coverage: dict, boundary: dict, judgment: dict, scope: str) -> tuple[str, dict]:
    log: list[str] = []

    orphans, phantoms, duplicates = _gate_engine1(coverage, log)
    boundary_findings = _gate_engine2(boundary, log)
    judgment_findings = _gate_engine3(judgment, log)

    orphans = _dedupe(orphans)
    phantoms = _dedupe(phantoms)
    duplicates = _dedupe(duplicates)

    n_orphans, n_phantoms, n_redundancy = len(orphans), len(phantoms), len(duplicates)

    boundary_warn = [f for f in boundary_findings if f.get("verdict") == "WARN"]
    boundary_unver = [f for f in boundary_findings if f.get("verdict") == "UNVERIFIABLE"]

    coverage_status = coverage.get("coverage_status", "UNVERIFIABLE" if not coverage else "OK")
    boundary_status = boundary.get("boundary_status", "OK") if boundary else "OK"
    judgment_status = judgment.get("judgment_status", "OK") if judgment else "OK"

    n_unverifiable = (len(boundary_unver)
                      + len(coverage.get("phantoms_unverifiable", []))
                      + (1 if coverage.get("orphan_status") == "UNVERIFIABLE" else 0))

    result = _result(n_orphans, n_phantoms, n_redundancy, coverage_status)

    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    fm = [
        "---",
        f"orphans: {n_orphans}          # code-level, material → FAIL if >0",
        f"phantoms: {n_phantoms}         # material, complete-graph only → FAIL if >0",
        f"redundancy: {n_redundancy}       # LITERAL duplicate artifact only → FAIL if >0",
        f"boundary_warn: {len(boundary_warn)}    # Engine 2 IPE-conformance (over/under-merge, naming) → WARN",
        f"inference_warn: {len(judgment_findings)}   # Engine 3 (UNSUPPORTED / granularity / restates / naming) → WARN",
        f"unverifiable: {n_unverifiable}     # no/empty/partial graph, empty index, ambiguous",
        f"coverage_status: {coverage_status}     # LOUD, distinct from result — never silently PASS",
        f"boundary_status: {boundary_status}     # engine-completion accounting",
        f"judgment_status: {judgment_status}     # engine-completion accounting",
        f"result: {result}",
        "---",
    ]

    def _fail_section(items, prefix):
        if not items:
            return "_(none)_\n"
        out = []
        for i, f in enumerate(items, 1):
            out.append(f"### {prefix}{i}: {f.get('kind')} — {f.get('source_file') or ', '.join(f.get('paths', []))}")
            out.append(f"- **Evidence**: {f.get('evidence', '')}")
            out.append("")
        return "\n".join(out)

    def _warn_section(items):
        if not items:
            return "_(none)_\n"
        out = []
        for i, f in enumerate(items, 1):
            tgt = f.get("screen") or f.get("target") or f.get("us") or ""
            out.append(f"### W{i}: {f.get('kind')} ({f.get('engine')}) — {tgt}")
            out.append(f"- **Evidence**: {f.get('evidence', '')}")
            out.append(f"- **Anchor**: {f.get('clause') or f.get('anchor', '')}")
            sev = f.get("severity", "")
            exp = " · _experimental (design-intent)_" if f.get("experimental") else ""
            out.append(f"- **Severity**: {sev} · **Verdict**: WARN{exp}")
            out.append("")
        return "\n".join(out)

    def _unver_section():
        rows = []
        if coverage.get("orphan_status") == "UNVERIFIABLE":
            rows.append(f"- **coverage/orphans**: {coverage.get('orphan_reason', '')}")
        gs = coverage.get("graph_state", {})
        if coverage_status != "OK":
            rows.append(f"- **graph state**: {gs.get('status', '?')} — {gs.get('note', '')}")
        for u in coverage.get("phantoms_unverifiable", []):
            rows.append(f"- **phantom/{u.get('artifact')}**: {u.get('reason')}")
        for f in boundary_unver:
            rows.append(f"- **boundary**: {f.get('evidence')}")
        return "\n".join(rows) + "\n" if rows else "_(none)_\n"

    all_warn = boundary_warn + judgment_findings
    parts = [
        "\n".join(fm), "",
        f"# Synthesis Judgment Report — scope: {scope}", "",
        f"**Date**: {date_str} · **Result**: {result} · **Coverage status**: {coverage_status}", "",
        "---", "", "## Summary", "",
        "| Bucket | Count |", "|--------|-------|",
        f"| orphans (FAIL) | {n_orphans} |",
        f"| phantoms (FAIL) | {n_phantoms} |",
        f"| redundancy (FAIL) | {n_redundancy} |",
        f"| boundary WARN | {len(boundary_warn)} |",
        f"| inference/judgment WARN | {len(judgment_findings)} |",
        f"| unverifiable | {n_unverifiable} |",
        f"| **Result** | **{result}** |", "",
        "---", "", "## FAIL — deterministic coverage defects (Engine 1)", "",
        "### Orphans (code with no doc trace)", "", _fail_section(orphans, "O"),
        "### Phantoms (doc cites code with no graph node)", "", _fail_section(phantoms, "P"),
        "### Literal duplicate artifacts", "", _fail_section(duplicates, "D"),
        "---", "", "## WARN — boundary / judgment (advisory, never flips result)", "",
        _warn_section(all_warn),
        "---", "", "## UNVERIFIABLE (loud — not a verified PASS)", "", _unver_section(),
        "---", "", "## Engine-completion status", "",
        f"- coverage_status: **{coverage_status}**",
        f"- boundary_status: **{boundary_status}**",
        f"- judgment_status: **{judgment_status}**", "",
        "## How to remediate", "",
        "- FAIL orphans/phantoms → cite the missing source in a feature spec, or remove the phantom citation.",
        "- `coverage_status: UNVERIFIABLE` → build the graph (`graph_preflight`) and run `--feature-specs` first, then re-audit.",
        "- WARN → a human weighs each; none blocks. design-intent WARNs are experimental.", "",
    ]
    frontmatter_data = {
        "orphans": n_orphans, "phantoms": n_phantoms, "redundancy": n_redundancy,
        "boundary_warn": len(boundary_warn), "inference_warn": len(judgment_findings),
        "unverifiable": n_unverifiable, "coverage_status": coverage_status,
        "boundary_status": boundary_status, "judgment_status": judgment_status, "result": result,
        "_gate_log": log,
    }
    return ("\n".join(parts), frontmatter_data)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Assemble judgment-report.md from the three engines")
    p.add_argument("--coverage", default=None, help="Engine-1 findings JSON")
    p.add_argument("--boundary", default=None, help="Engine-2 findings JSON")
    p.add_argument("--judgment", default=None, help="Engine-3 assemble JSON")
    p.add_argument("--scope", default="all")
    p.add_argument("--out", required=True, help="judgment-report.md output path")
    p.add_argument("--project-root", default=None)
    args = p.parse_args(argv)

    resolve_project_root(args.project_root)  # validates/normalizes; report path is explicit
    coverage, boundary, judgment = _load(args.coverage), _load(args.boundary), _load(args.judgment)

    report, fm = assemble(coverage, boundary, judgment, args.scope)
    for line in fm["_gate_log"]:
        print(line, file=sys.stderr)

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(out_path, report)
    print(f"[assemble_judgment_report] result={fm['result']} coverage_status={fm['coverage_status']} → {out_path}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
