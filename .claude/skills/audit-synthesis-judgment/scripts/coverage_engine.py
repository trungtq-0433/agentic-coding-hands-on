#!/usr/bin/env python3
"""Engine 1 — deterministic coverage (the ONLY FAIL source).

Orchestrates: graph_preflight (best-effort build) → graph-state gate → orphans → phantoms →
literal-duplicate redundancy → advisory validator roll-up → findings JSON + `coverage_status`.

This engine does NOT decide the final PASS/FAIL — phase 05's assembler does. It emits the
deterministic material findings and a LOUD `coverage_status` so a degraded graph can never
resolve to a silent PASS. Engine-2/3 (stochastic) signals never reach these counts.

Stdlib only. Exit 0 always (advisory emitter; the assembler + consumer gate).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_docs_root, resolve_project_root  # noqa: E402
import _graph_state_lib as gs  # noqa: E402
import _coverage_orphan_lib as orphan_lib  # noqa: E402
import _coverage_phantom_lib as phantom_lib  # noqa: E402
import _redundancy_lib as redundancy_lib  # noqa: E402
import locate_synthesis_artifacts as locator  # noqa: E402

# Languages graphify can index → "graphable" (single source in _graph_state_lib). COBOL / Pascal /
# PL-SQL are NOT graphable — a missing graph there is EXPECTED, not a defect.
_GRAPHABLE_LANGS = gs.GRAPHABLE_LANGS

_REBUILD_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "rebuild-spec" / "scripts"

# The ENUMERATED, judgment-relevant validator subset (advisory roll-up; NEVER a FAIL source).
# Rationale for each + why the other 15 are excluded lives in references/coverage-contract.md.
_DOCS_ROOT_VALIDATORS = ["validate_source_citations", "validate_feature_spec"]
_PLAN_DIR_VALIDATORS = ["validate_feature_existence"]  # id_contiguity handled per-artifact below


def _run_preflight(repo_root: Path) -> None:
    """Best-effort: build the graph if missing this session (mirrors rebuild-spec's always-run)."""
    script = _REBUILD_SCRIPTS / "graph_preflight.py"
    if not script.is_file():
        return
    try:
        subprocess.run([sys.executable, str(script)], cwd=str(repo_root),
                       capture_output=True, text=True, timeout=600, check=False)
    except (subprocess.SubprocessError, OSError):
        pass


def _load_index(docs_root: Path) -> tuple[dict, bool]:
    """Load _source-to-fcode.json; return (data, features_dir_present)."""
    index_path = docs_root / "_source-to-fcode.json"
    features_present = (docs_root / "features").is_dir() and any((docs_root / "features").glob("*/"))
    if index_path.is_file():
        try:
            return (json.loads(index_path.read_text(encoding="utf-8")), features_present)
        except (json.JSONDecodeError, OSError):
            pass
    return ({"index": {}}, features_present)


def _resolve_graphable(stack: str | None, repo_langs: list[str]) -> tuple[bool, str]:
    """Resolve whether the target stack is graphable. --stack profile wins; else infer from langs."""
    if stack:
        prof = _REBUILD_SCRIPTS.parent / "references" / "stack-profiles" / f"{stack}.json"
        if prof.is_file():
            try:
                data = json.loads(prof.read_text(encoding="utf-8"))
                if "graphable" in data:
                    return (bool(data["graphable"]), f"stack-profile {stack}.json graphable={data['graphable']}")
            except (json.JSONDecodeError, OSError):
                pass
    graphable = any(l in _GRAPHABLE_LANGS for l in repo_langs)
    return (graphable, f"inferred from repo languages {repo_langs} (graphable langs present: {graphable})")


def _run_validator_subset(docs_root: Path, plan_dir: str | None,
                          design_intent_path: str | None, project_root: Path) -> dict:
    """Best-effort advisory roll-up of the enumerated validator subset. Never raises."""
    results: dict[str, dict] = {}

    def _call(name: str, extra_args: list[str]) -> None:
        script = _REBUILD_SCRIPTS / f"{name}.py"
        if not script.is_file():
            results[name] = {"ran": False, "reason": "validator script not found"}
            return
        with tempfile.NamedTemporaryFile("r", suffix=".json", delete=False) as tf:
            out = tf.name
        try:
            subprocess.run([sys.executable, str(script), *extra_args,
                            "--project-root", str(project_root), "--summary-out", out],
                           capture_output=True, text=True, timeout=120, check=False)
            data = json.loads(Path(out).read_text(encoding="utf-8"))
            results[name] = {"ran": True, "overall_status": data.get("overall_status"),
                             "totals": data.get("totals", {})}
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
            results[name] = {"ran": False, "reason": f"{type(exc).__name__}: {exc}"}
        finally:
            try:
                Path(out).unlink()
            except OSError:
                pass

    for name in _DOCS_ROOT_VALIDATORS:
        _call(name, ["--docs-root", str(docs_root)])
    if design_intent_path and Path(design_intent_path).is_file():
        _call("validate_design_intent_density", ["--design-intent-file", design_intent_path])
    if plan_dir:
        for name in _PLAN_DIR_VALIDATORS:
            _call(name, ["--plan-dir", plan_dir])
        _call("validate_id_contiguity", ["--artifact", "user-stories", "--plan-dir", plan_dir])
    return results


def run(project_root: Path, scope: str, docs_root_override: str | None, plan_dir: str | None,
        graph_path: Path, strict_coverage: bool, stack: str | None,
        do_preflight: bool, run_validators: bool) -> dict:
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))

    if do_preflight:
        _run_preflight(project_root)

    state = gs.classify(graph_path, project_root)
    unverifiable_langs = set(state["unverifiable_languages"])

    loc = locator.locate(project_root, scope, docs_root_override, plan_dir)
    artifacts = loc["artifacts"]
    doc_texts: list[str] = []
    for art in artifacts:
        if art.get("present") and art.get("path"):
            try:
                doc_texts.append(Path(art["path"]).read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    index_data, features_present = _load_index(docs_root)
    orphan_res = orphan_lib.find_orphans(
        state["nodes"], index_data, doc_texts, project_root,
        unverifiable_langs, features_present)
    phantom_res = phantom_lib.find_phantoms(
        artifacts, state["nodes"], project_root, state["status"], unverifiable_langs)
    redundancy_res = redundancy_lib.find_duplicate_artifacts(artifacts)

    # coverage_status: loud, distinct from result.
    graphable, graphable_reason = _resolve_graphable(stack, state["repo_languages"])
    coverage_status = "OK"
    if state["status"] != gs.STATUS_OK or orphan_res["status"] == "UNVERIFIABLE":
        coverage_status = "UNVERIFIABLE"
    strict_fail = (strict_coverage and graphable
                   and state["status"] in (gs.STATUS_ABSENT, gs.STATUS_EMPTY,
                                            gs.STATUS_PARTIAL, gs.STATUS_STALE))
    if strict_fail:
        coverage_status = "FAIL"

    design_intent_path = next((a["path"] for a in artifacts
                               if a["kind"] == "design-intent" and a.get("present")), None)
    validators = _run_validator_subset(docs_root, plan_dir, design_intent_path, project_root) \
        if run_validators else {}

    return {
        "engine": "coverage",
        "coverage_status": coverage_status,
        "graph_state": {k: state[k] for k in ("status", "note", "graph_languages",
                                              "repo_languages", "unverifiable_languages")},
        "graphable": graphable,
        "graphable_reason": graphable_reason,
        "strict_coverage": strict_coverage,
        "strict_fail": strict_fail,
        "orphan_status": orphan_res["status"],
        "orphan_reason": orphan_res["reason"],
        "orphans": orphan_res["orphans"],
        "orphans_filtered": orphan_res["filtered"],
        "phantoms": phantom_res["phantoms"],
        "phantoms_unverifiable": phantom_res["unverifiable"],
        "duplicates": redundancy_res["duplicates"],
        "duplicates_exempted": redundancy_res["exempted"],
        "validators": validators,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Engine 1 — deterministic coverage (the only FAIL source)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--docs-root", default=None)
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "design-intent", "system", "all"])
    p.add_argument("--plan-dir", default=None)
    p.add_argument("--graph", default=None, help="graph.json path (default: <root>/graphify-out/graph.json)")
    p.add_argument("--strict-coverage", action="store_true", default=False)
    p.add_argument("--stack", default=None, help="stack-profile name (resolves `graphable`)")
    p.add_argument("--no-preflight", action="store_true", default=False,
                   help="skip the graph_preflight build (tests / offline)")
    p.add_argument("--no-validators", action="store_true", default=False,
                   help="skip the advisory validator roll-up")
    p.add_argument("--out", default=None, help="write findings JSON here (default: stdout)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    graph_path = (Path(args.graph).resolve() if args.graph
                  else project_root / "graphify-out" / "graph.json")

    result = run(project_root, args.scope, args.docs_root, args.plan_dir, graph_path,
                 args.strict_coverage, args.stack, not args.no_preflight, not args.no_validators)

    payload = json.dumps(result, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(out)
        print(f"[coverage_engine] wrote → {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
