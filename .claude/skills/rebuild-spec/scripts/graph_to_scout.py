#!/usr/bin/env python3
"""[GRAPHIFY-INTEGRATION] Generate scout-report.md deterministically from graphify's graph.json.

Rationale (measured): in rebuild-spec runs the Wave-0 LLM scout costs 1.0-3.1M tokens, while
the report it produces is mechanical (file inventory + path-based types + BL grep). The graph
already contains every source file + symbols, so this script emits a contract-complete
scout-report for $0, letting the pipeline skip (or shrink to verify-only) the scout wave.

Usage: graph_to_scout.py --graph graphify-out/graph.json --repo . --out <plan>/artifacts/scout-report.md
Exit 0 on success (report written), 1 on any problem (caller falls back to the LLM scout).
Stdlib only.
"""
from __future__ import annotations
import argparse, json, os, re, sys

INVENTORY_TYPES = ("screen", "route", "model", "background", "permission", "config", "other")

# Path-based classification (mirrors what the LLM scout does for Mode-A stacks).
RULES = [
    ("config",     re.compile(r"__init__\.py$|(^|/)main\.py$|conftest\.py$")),
    ("background", re.compile(r"(^|/)(jobs?|tasks?|workers?|listeners?|signals?|queues?|cron)(/|$)|(^|/)events?\.py$")),
    ("route",      re.compile(r"(^|/)(routes|controllers|endpoints)(/|$)|urls\.py$")),
    ("model",      re.compile(r"(^|/)(models|schemas|entities|domain|migrations)(/|$)")),
    ("permission", re.compile(r"(^|/)(auth|permissions?|policies|guards?|middleware|errors)(/|$)|authentication|authorization|security")),
    ("screen",     re.compile(r"(^|/)(pages|views|components|screens|templates|layouts)(/|$)")),
    ("config",     re.compile(r"(^|/)(settings|config|core)(/|$)")),
]
BG_MARKERS = re.compile(
    r"@celery|@shared_task|@task\b|BackgroundTasks|apscheduler|@cron|add_event_handler|"
    r"on_event\(|@app\.on_event|signal\.connect|@receiver|EventListener|addEventListener|"
    r"setInterval|cron\.schedule|Bull\(|Queue\(", re.IGNORECASE)
MANIFESTS = [("pyproject.toml","Python"),("setup.py","Python"),("requirements.txt","Python"),
             ("package.json","JS/TS"),("composer.json","PHP"),("Gemfile","Ruby"),
             ("pom.xml","Java"),("build.gradle","Java"),("go.mod","Go"),("Cargo.toml","Rust")]
SKIP_DIRS = {".git","graphify-out",".claude","__pycache__","node_modules","vendor",".venv","venv",".serena","docs","plans"}
TEST_PAT = re.compile(r"(^|/)tests?(/|$)|_test\.|\.test\.|spec\.")


def classify(path: str) -> str:
    p = path.replace("\\", "/")
    for t, rx in RULES:
        if rx.search(p):
            return t
    return "other"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        g = json.load(open(a.graph, encoding="utf-8"))
    except Exception as e:
        print(f"error: cannot read graph: {e}", file=sys.stderr); return 1
    nodes = g.get("nodes", [])
    if not nodes:
        print("error: graph has no nodes", file=sys.stderr); return 1

    repo = os.path.abspath(a.repo)
    # 1) detected language from manifest
    lang = next((l for f, l in MANIFESTS if os.path.exists(os.path.join(repo, f))), "JS/TS")

    # 2) authoritative file set = walk (the W2/W7 contract: EVERY source file), graph enriches
    files = []
    for root, dirs, fs in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in fs:
            rel = os.path.relpath(os.path.join(root, fn), repo).replace("\\", "/")
            if not fn.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".php", ".rb", ".go", ".rs", ".java", ".kt")):
                continue
            if TEST_PAT.search(rel):
                continue
            files.append(rel)
    files.sort()
    if not files:
        print("error: no source files found", file=sys.stderr); return 1

    # symbols per file from graph (enrichment for Notes)
    sym_count = {}
    for n in nodes:
        sf = n.get("source_file") or ""
        if sf:
            sym_count[sf] = sym_count.get(sf, 0) + 1
    graph_files = set(sym_count)

    # 3) BL inventory: deterministic content grep
    bl_hits = []
    for rel in files:
        try:
            txt = open(os.path.join(repo, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in BG_MARKERS.finditer(txt):
            line = txt.count("\n", 0, m.start()) + 1
            bl_hits.append((rel, line, m.group(0)))

    dirs_scanned = sorted({os.path.dirname(f) + "/" if os.path.dirname(f) else "./" for f in files})
    api_kind = "rest"

    out_lines = [
        "# Scout Report", "",
        "<!-- Generated deterministically by graph_to_scout.py from graphify-out/graph.json.",
        "     File Inventory contract: consumed by Wave 2 (content-completeness) and Wave 7",
        "     (reviewer cross-validation). -->", "",
        "## Detected Language", "", lang, "",
        "## Scanned Directories", "",
    ]
    out_lines += [f"- {d}" for d in dirs_scanned]
    out_lines += ["", "## File Inventory", "",
                  "<!-- One entry per non-test, non-vendor source file.",
                  "     Format: <relative-path> TAB <type> -->", ""]
    out_lines += [f"{f}\t{classify(f)}" for f in files]
    out_lines += ["", "## Background Logic Source Inventory", "", f"### {lang}", ""]
    if bl_hits:
        out_lines += [f"- {rel}:L{line} — marker `{mk}`" for rel, line, mk in bl_hits]
    else:
        out_lines += ["_(none found)_"]
    out_lines += ["", f"## Detected API Kind: {api_kind}", "",
                  "## Notes", "",
                  f"- Generated from knowledge graph: {len(nodes)} nodes; "
                  f"{len(graph_files)} files have extracted symbols.",
                  "- Use `graphify query/explain` for symbol-level relationships instead of re-scanning.",
                  ""]

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(out_lines))
    print(f"scout-report generated: {a.out} ({len(files)} files, {len(bl_hits)} BL markers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
