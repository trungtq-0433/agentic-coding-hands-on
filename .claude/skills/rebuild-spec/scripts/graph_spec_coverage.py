#!/usr/bin/env python3
"""[GRAPHIFY-INTEGRATION] Advisory coverage check: promoted spec vs graph ground truth.

After W9 promotion, verify with machine ground truth that the spec is COMPLETE:
  - every model-ish class in the graph is mentioned in docs/generated/entities.md
  - every route file on disk is mentioned in docs/generated/route-list.md
Prints a coverage report. ALWAYS exits 0 (advisory — naming conventions in specs may
legitimately differ; findings are warnings for the orchestrator/user, not a gate).

Usage: graph_spec_coverage.py --graph graphify-out/graph.json --repo . --docs docs
Stdlib only.
"""
from __future__ import annotations
import argparse, json, os, re, sys

# NOTE: /schemas/ (request/response DTOs) is deliberately EXCLUDED — entities.md covers
# domain entities, not API DTOs; including schemas produced noisy false warnings.
MODEL_PATH = re.compile(r"(^|/)(models|entities|domain)(/|$)")
SCHEMA_PATH = re.compile(r"(^|/)schemas(/|$)")
ROUTE_PATH = re.compile(r"(^|/)(routes|controllers|endpoints)(/|$)|urls\.py$")
SKIP_DIRS = {".git", "graphify-out", ".claude", "__pycache__", "node_modules", "vendor", ".venv", "docs", "plans"}
TEST_PAT = re.compile(r"(^|/)tests?(/|$)|_test\.|\.test\.|spec\.")


def is_class_label(label: str) -> bool:
    return bool(label) and label[0].isupper() and label.isidentifier()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--docs", default="docs")
    a = ap.parse_args()

    def read(rel):
        p = os.path.join(a.docs, rel)
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else None

    problems = 0

    # 1) model classes (graph) -> entities.md
    entities = read("generated/entities.md")
    try:
        g = json.load(open(a.graph, encoding="utf-8"))
        cls = sorted({n["label"] for n in g.get("nodes", [])
                      if MODEL_PATH.search(n.get("source_file") or "")
                      and not SCHEMA_PATH.search(n.get("source_file") or "")
                      and is_class_label(n.get("label", ""))})
    except Exception as e:
        print(f"coverage: cannot read graph ({e}) — skipped"); return 0
    if entities is None:
        print("coverage: docs/generated/entities.md missing — skipped entity check")
    else:
        missing = [c for c in cls if not re.search(r"\b" + re.escape(c) + r"\b", entities)]
        ok = len(cls) - len(missing)
        print(f"coverage[entities]: {ok}/{len(cls)} graph model classes mentioned in entities.md")
        for c in missing:
            print(f"  WARNING: class `{c}` exists in code but is not mentioned in entities.md")
        problems += len(missing)

    # 2) route files (disk) -> route-list.md
    routes = read("generated/route-list.md")
    route_files = []
    for root, dirs, fs in os.walk(a.repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in fs:
            rel = os.path.relpath(os.path.join(root, fn), a.repo).replace("\\", "/")
            if fn.endswith((".py", ".js", ".ts", ".php", ".rb", ".go")) and not TEST_PAT.search(rel) \
                    and ROUTE_PATH.search(rel) and not fn.startswith("__init__"):
                route_files.append(rel)
    if routes is None:
        print("coverage: docs/generated/route-list.md missing — skipped route check")
    else:
        missing = [f for f in sorted(route_files) if os.path.basename(f) not in routes and f not in routes]
        ok = len(route_files) - len(missing)
        print(f"coverage[routes]: {ok}/{len(route_files)} route files mentioned in route-list.md")
        for f in missing:
            print(f"  WARNING: route file `{f}` not mentioned in route-list.md")
        problems += len(missing)

    print(f"coverage: {'OK — spec fully covers graph ground truth' if problems == 0 else f'{problems} warning(s) — review before shipping the spec'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
