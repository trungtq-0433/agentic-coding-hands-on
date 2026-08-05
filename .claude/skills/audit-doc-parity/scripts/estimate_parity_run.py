#!/usr/bin/env python3
"""Step 0 — Estimate & gate (advisory).

Counts in-scope doc units + total cited LoC, prints a cost/scope estimate.
Shaped after rebuild-spec/scripts/estimate_artifact_loc.py.

--feature / --path callers set bypass_gate: true in output.
Exit 0 always (advisory — the orchestrator enforces the gate, not this script).
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import (  # noqa: E402
    parse_citations, read_text_safe, resolve_docs_root, resolve_project_root,
)

# Avg LLM agent budget per unit (regen + diff): rough empirical estimate.
# One agent per feature unit is the current fan-out shape.
_AVG_LOC_PER_UNIT = 200   # cited LoC per unit (typical technical-spec)
_DEFAULT_LOC_GATE = int(__import__("os").environ.get("AUDIT_PARITY_LOC_GATE", "2000"))

# Discovery map: mirrors scope_doc_units.py _DISCOVERY_MAP patterns
_FEATURE_TECH_SPEC_GLOB = "features/*/technical-spec.md"
_SYSTEM_GLOBS = [
    "system/behavior-logic.md",
    "generated/behavior-logic.md",
    "generated/api-*.md",
    "generated/api-contracts.md",
    "generated/api-map.md",
    "api-contracts.md",
    "api-map.md",
    "generated/entities.md",
    "generated/data-model.md",
    "data-model.md",
    "entities.md",
]


def _count_cited_loc(doc_path: Path) -> int:
    """Return total line-span of all **Source:** citations in a doc."""
    result = read_text_safe(doc_path)
    if result is None:
        return 0
    text, _ = result
    refs = parse_citations(text)
    return sum(max(0, r.end - r.start + 1) for r in refs)


def _discover_units(docs_root: Path, feature_filter: str | None,
                    path_filter: Path | None) -> list[Path]:
    """Return doc paths to process (mirrors scope_doc_units discovery)."""
    if path_filter:
        return [path_filter] if path_filter.is_file() else []

    paths: list[Path] = []
    seen: set[Path] = set()

    # Feature technical-specs
    for p in sorted(docs_root.glob(_FEATURE_TECH_SPEC_GLOB)):
        if not p.is_file() or p in seen:
            continue
        if feature_filter and not p.parent.name.startswith(feature_filter):
            continue
        paths.append(p)
        seen.add(p)

    # System docs: always included regardless of feature filter.
    # Mirrors scope_doc_units._discover_doc_paths: system docs carry API/behavior
    # citations that bear on any feature, so they are always in scope.
    for pattern in _SYSTEM_GLOBS:
        for p in sorted(docs_root.glob(pattern)):
            if p.is_file() and p not in seen:
                paths.append(p)
                seen.add(p)

    return paths


def estimate(project_root: Path, feature_filter: str | None = None,
             path_filter: Path | None = None) -> dict:
    docs_root = resolve_docs_root(project_root)
    doc_paths = _discover_units(docs_root, feature_filter, path_filter)

    unit_count = len(doc_paths)
    cited_loc = sum(_count_cited_loc(p) for p in doc_paths)
    bypass = feature_filter is not None or path_filter is not None

    # Rough agent estimate: 1 agent per unit (regen) + 1 shared diff pass
    est_agents = max(1, unit_count) if unit_count else 0

    if unit_count == 0:
        reason = "no doc units discovered"
    elif bypass:
        reason = f"bypass_gate=true (--feature/--path set); {unit_count} unit(s), {cited_loc} cited LoC"
    else:
        reason = (
            f"{unit_count} unit(s) × ~{_AVG_LOC_PER_UNIT} LoC/unit = "
            f"~{unit_count * _AVG_LOC_PER_UNIT} est LoC; "
            f"actual cited LoC = {cited_loc}"
        )

    return {
        "units": unit_count,
        "cited_loc": cited_loc,
        "est_agents": est_agents,
        "bypass_gate": bypass,
        "reason": reason,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="Estimate audit-doc-parity run scope (advisory, exit 0 always)"
    )
    p.add_argument("--project-root", default=None, help="Project root (default: git toplevel)")
    p.add_argument("--feature", default=None, metavar="F###",
                   help="Limit to a single feature (sets bypass_gate: true)")
    p.add_argument("--path", default=None, metavar="DOC",
                   help="Single doc file (sets bypass_gate: true)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    path_filter = Path(args.path).resolve() if args.path else None

    result = estimate(project_root, feature_filter=args.feature, path_filter=path_filter)
    print(json.dumps(result, indent=2))
    return 0   # always advisory


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
