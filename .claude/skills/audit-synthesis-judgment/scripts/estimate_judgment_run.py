#!/usr/bin/env python3
"""Phase 05 — estimate & gate the default `--scope all` sweep (advisory).

Counts in-scope synthesis artifacts × the engines that will run, and the Engine-3 candidate
budget (the LLM-heavy part). `--scope <one>` sets bypass_gate: true (mirrors audit-doc-parity's
`--feature`/`--path` bypass). Exit 0 always — the orchestrator enforces the gate, not this script.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_project_root  # noqa: E402
import locate_synthesis_artifacts as locator  # noqa: E402

# Rough Engine-3 LLM cost: judges + refuters per candidate.
_REFUTERS_PER_CANDIDATE = 2  # medium+ default


def estimate(project_root: Path, scope: str, docs_root_override: str | None,
             plan_dir: str | None) -> dict:
    loc = locator.locate(project_root, scope, docs_root_override, plan_dir)
    present = [a for a in loc["artifacts"] if a.get("present")]
    n_artifacts = len(present)

    # Engines that run for the scope. Engine 1 always; Engine 2 needs user-stories; Engine 3 for judgment scopes.
    engines = ["coverage(1)"]
    if scope in ("all", "user-stories"):
        engines.append("boundary(2)")
    if scope in ("all", "user-stories", "design-intent", "feature-list"):
        engines.append("judgment(3)")

    bypass = scope != "all"
    # Engine-3 candidate estimate: ~ artifacts × a small constant (inference/naming/restates/granularity).
    est_candidates = n_artifacts * 6 if "judgment(3)" in engines else 0
    est_llm_calls = est_candidates * (1 + _REFUTERS_PER_CANDIDATE)  # 1 judge + N refuters each

    if n_artifacts == 0:
        reason = "no in-scope synthesis artifacts discovered"
    elif bypass:
        reason = f"bypass_gate=true (--scope {scope}); {n_artifacts} artifact(s), engines {engines}"
    else:
        reason = (f"full sweep: {n_artifacts} artifact(s) × engines {engines}; "
                  f"~{est_candidates} Engine-3 candidates → ~{est_llm_calls} LLM calls")

    return {
        "scope": scope, "artifacts_present": n_artifacts, "engines": engines,
        "est_engine3_candidates": est_candidates, "est_llm_calls": est_llm_calls,
        "bypass_gate": bypass, "reason": reason,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Estimate audit-synthesis-judgment run scope (advisory)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--docs-root", default=None)
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "design-intent", "system", "all"])
    p.add_argument("--plan-dir", default=None)
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    result = estimate(project_root, args.scope, args.docs_root, args.plan_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
