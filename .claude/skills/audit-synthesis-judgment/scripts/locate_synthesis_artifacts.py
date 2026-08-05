#!/usr/bin/env python3
"""Phase 01 — synthesis-tier artifact locator.

Resolves the lang-mapped docs root (via the copied `_citation_lib.resolve_docs_root`),
then emits a JSON manifest of every in-scope synthesis artifact present on disk. Feeds
Engine 1 (coverage), Engine 2 (boundary), Engine 3 (judgment).

Design-intent lives in the plan dir until rebuild-spec's D.5 promote, so it is located
specially: promoted `<docs_root>/system/design-intent.md` wins; otherwise a `--plan-dir`
names it explicitly. With no `--plan-dir` AND more than one candidate plan dir carrying a
`design-intent.md`, the locator REFUSES to guess — it logs the ambiguity and marks the
artifact absent (never silently picks the newest). [Red-team F13]

Absence is normal, not an error: a missing artifact is recorded `present: false` (feeds the
phase-02 gap accounting). The tool never reads outside the resolved docs root / named plan dir.

Stdlib only. Always exits 0 unless the docs root itself cannot be resolved (exit 2).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_docs_root, resolve_project_root  # noqa: E402

# Canonical layered paths relative to the resolved docs_root (v4 layout).
# Mirrors build_source_to_fcode.ARTIFACT_LAYERED + the feature/flows dirs.
_SCOPE_ARTIFACTS: dict[str, list[tuple[str, str, str]]] = {
    # scope -> [(kind, tier, rel_path_or_glob)]
    "feature-list": [
        ("feature-list", "generated", "generated/feature-list.md"),
        ("feature-spec", "features", "features/*/technical-spec.md"),
    ],
    "user-stories": [
        ("user-stories", "generated", "generated/user-stories.md"),
    ],
    "system": [
        ("glossary", "system", "system/glossary.md"),
        ("entities", "generated", "generated/entities.md"),
        ("business-rules", "system", "system/business-rules.md"),
        ("system-overview", "system", "system/overview.md"),
        ("architecture", "system", "system/architecture.md"),
        ("jobs", "generated", "generated/job-list.md"),
        ("flows", "flows", "flows/*.md"),
    ],
    # design-intent handled separately (plan-dir aware) — see _locate_design_intent
}

_DESIGN_INTENT_PROMOTED = "system/design-intent.md"
_DESIGN_INTENT_PLAN_REL = "artifacts/design-intent.md"


def _expand(docs_root: Path, kind: str, tier: str, rel: str) -> list[dict]:
    """Resolve one artifact spec (literal path or glob) to manifest entries."""
    entries: list[dict] = []
    if "*" in rel:
        matches = sorted(docs_root.glob(rel))
        if not matches:
            entries.append({"artifact": rel, "kind": kind, "tier": tier,
                            "path": str(docs_root / rel), "present": False})
        for m in matches:
            entries.append({"artifact": m.name, "kind": kind, "tier": tier,
                            "path": str(m), "present": m.is_file()})
    else:
        p = docs_root / rel
        entries.append({"artifact": Path(rel).name, "kind": kind, "tier": tier,
                        "path": str(p), "present": p.is_file()})
    return entries


def _locate_design_intent(project_root: Path, docs_root: Path,
                          plan_dir: str | None) -> tuple[dict, dict | None]:
    """Locate design-intent.md (plan-dir aware). Returns (entry, ambiguity_or_None).

    Order: promoted docs/system/design-intent.md → explicit --plan-dir → scan plans/*.
    >1 candidate plan dir with no --plan-dir → refuse (ambiguity), mark absent.
    """
    promoted = docs_root / _DESIGN_INTENT_PROMOTED
    if promoted.is_file():
        return ({"artifact": "design-intent.md", "kind": "design-intent",
                 "tier": "system", "path": str(promoted), "present": True}, None)

    if plan_dir:
        pd = Path(plan_dir)
        if not pd.is_absolute():
            pd = project_root / pd
        p = pd / _DESIGN_INTENT_PLAN_REL
        return ({"artifact": "design-intent.md", "kind": "design-intent",
                 "tier": "plan", "path": str(p), "present": p.is_file()}, None)

    # No --plan-dir: scan plans/*/artifacts/design-intent.md
    plans_root = project_root / "plans"
    candidates = sorted(plans_root.glob(f"*/{_DESIGN_INTENT_PLAN_REL}")) if plans_root.is_dir() else []
    if len(candidates) == 0:
        # Absence is normal (design-intent is EXPERIMENTAL/optional).
        return ({"artifact": "design-intent.md", "kind": "design-intent", "tier": "plan",
                 "path": str(plans_root / f"<plan>/{_DESIGN_INTENT_PLAN_REL}"), "present": False}, None)
    if len(candidates) == 1:
        c = candidates[0]
        return ({"artifact": "design-intent.md", "kind": "design-intent", "tier": "plan",
                 "path": str(c), "present": True}, None)
    # >1 candidate, no --plan-dir → REFUSE to guess (F13).
    ambiguity = {
        "kind": "design-intent",
        "reason": "multiple candidate plan dirs carry design-intent.md; --plan-dir required to disambiguate",
        "candidates": [str(c) for c in candidates],
    }
    entry = {"artifact": "design-intent.md", "kind": "design-intent", "tier": "plan",
             "path": None, "present": False, "note": "ambiguous — refused to guess (pass --plan-dir)"}
    return (entry, ambiguity)


def locate(project_root: Path, scope: str, docs_root_override: str | None,
           plan_dir: str | None) -> dict:
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))

    scopes = ["feature-list", "user-stories", "system"] if scope == "all" else [scope]
    include_design_intent = scope in ("all", "design-intent")

    artifacts: list[dict] = []
    ambiguities: list[dict] = []
    seen_paths: set[str] = set()

    for sc in scopes:
        for kind, tier, rel in _SCOPE_ARTIFACTS.get(sc, []):
            for entry in _expand(docs_root, kind, tier, rel):
                key = entry.get("path") or f"{entry['kind']}:{entry['artifact']}"
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                artifacts.append(entry)

    if include_design_intent:
        di_entry, di_amb = _locate_design_intent(project_root, docs_root, plan_dir)
        artifacts.append(di_entry)
        if di_amb:
            ambiguities.append(di_amb)

    return {
        "project_root": str(project_root),
        "docs_root": str(docs_root),
        "scope": scope,
        "artifacts": artifacts,
        "ambiguities": ambiguities,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Locate rebuild-spec synthesis-tier artifacts")
    p.add_argument("--project-root", default=None, help="Project root (default: git toplevel)")
    p.add_argument("--docs-root", default=None, help="Override the resolved docs root")
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "design-intent", "system", "all"])
    p.add_argument("--plan-dir", default=None,
                   help="Plan dir holding an un-promoted design-intent.md (required to disambiguate)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    if not project_root.is_dir():
        print(f"[ERROR] project root not found: {project_root}", file=sys.stderr)
        return 2

    result = locate(project_root, args.scope, args.docs_root, args.plan_dir)
    for amb in result["ambiguities"]:
        print(f"[WARN] ambiguous {amb['kind']}: {amb['reason']} "
              f"(candidates: {', '.join(amb['candidates'])})", file=sys.stderr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
