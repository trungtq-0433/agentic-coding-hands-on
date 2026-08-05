"""Engine 1 — graph-state classification.

`graphify-out/graph.json` is a gitignored, session-local build artifact — "no graph" usually
means "not built this session" (fresh CI checkout), NOT "stack unsupported". This lib classifies
the graph's usability so orphan/phantom checks never produce a false FAIL (or a false clean) on a
degraded graph. Four states, all of which set `coverage_status` LOUDLY:

  ABSENT   — graph.json missing/unreadable         → orphan/phantom UNVERIFIABLE
  EMPTY    — graph.json present but 0 nodes          → orphan/phantom UNVERIFIABLE
  PARTIAL  — a repo language has ZERO graph nodes    → that language's files UNVERIFIABLE (both dirs)
  STALE    — graph build commit != git HEAD          → orphan/phantom UNVERIFIABLE
  OK       — graph present, non-empty, all repo langs represented, not stale

Never silently resolves to PASS. Stdlib only.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

STATUS_OK = "OK"
STATUS_ABSENT = "ABSENT"
STATUS_EMPTY = "EMPTY"
STATUS_PARTIAL = "PARTIAL"
STATUS_STALE = "STALE"

# Languages graphify (an AST indexer for mainstream languages) can actually index. A repo language
# OUTSIDE this set (SQL, COBOL, Pascal) is one graphify never indexes — its absence from the graph
# is EXPECTED, not a PARTIAL defect. Kept here (the lowest-level lib) as the single source; coverage_engine
# imports it. Must stay in sync with the _EXT_LANG values below.
GRAPHABLE_LANGS = {"python", "javascript", "typescript", "java", "go", "ruby", "php", "csharp"}

# Extension → language. Covers the stacks rebuild-spec profiles target.
_EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".cob": "cobol", ".cbl": "cobol", ".cpy": "cobol", ".cobol": "cobol",
    ".pas": "pascal", ".dfm": "pascal", ".dpr": "pascal", ".dpk": "pascal",
    ".sql": "plsql", ".pks": "plsql", ".pkb": "plsql", ".pls": "plsql", ".prc": "plsql",
    ".java": "java", ".go": "go", ".rb": "ruby", ".php": "php", ".cs": "csharp",
}

# Directories never counted as application source (mirror graph_spec_coverage.SKIP_DIRS).
_SKIP_DIRS = {".git", "graphify-out", ".claude", "__pycache__", "node_modules",
             "vendor", ".venv", "venv", "docs", "plans", "dist", "build", ".idea", ".vscode"}


def _lang_of(path: str) -> str | None:
    return _EXT_LANG.get(Path(path).suffix.lower())


def _repo_languages(repo_root: Path) -> set[str]:
    """Languages present in the repo's application source (best-effort file walk)."""
    langs: set[str] = set()
    for dirpath, dirnames, filenames in _walk(repo_root):
        for fn in filenames:
            lang = _lang_of(fn)
            if lang:
                langs.add(lang)
    return langs


def _walk(repo_root: Path):
    import os
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        yield root, dirs, files


def _git_head(repo_root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=5, check=False)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return None


def _graph_build_commit(graph: dict) -> str | None:
    """Best-effort: find a build-commit field in the graph metadata. graphify may or may not
    stamp one; when absent, staleness is undeterminable → we do NOT fabricate STALE."""
    for key in ("commit", "sha", "rev", "head", "git_sha", "build_commit"):
        v = graph.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    meta = graph.get("meta") or graph.get("metadata") or {}
    if isinstance(meta, dict):
        for key in ("commit", "sha", "rev", "head", "git_sha", "build_commit"):
            v = meta.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def load_graph_nodes(graph_path: Path) -> list[dict] | None:
    """Return the node list, or None if the graph is absent/unreadable."""
    if not graph_path.is_file():
        return None
    try:
        g = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    nodes = g.get("nodes")
    return nodes if isinstance(nodes, list) else []


def classify(graph_path: Path, repo_root: Path) -> dict:
    """Classify graph usability.

    Returns:
        {
          "status": OK|ABSENT|EMPTY|PARTIAL|STALE,
          "coverage_status": OK|UNVERIFIABLE,
          "nodes": [...] | [],
          "graph_languages": [...],
          "repo_languages": [...],
          "unverifiable_languages": [...],   # PARTIAL: repo langs with no nodes
          "note": "<human reason>",
        }
    """
    nodes = load_graph_nodes(graph_path)
    repo_langs = sorted(_repo_languages(repo_root))

    if nodes is None:
        return {"status": STATUS_ABSENT, "coverage_status": "UNVERIFIABLE", "nodes": [],
                "graph_languages": [], "repo_languages": repo_langs,
                "unverifiable_languages": repo_langs,
                "note": "graph.json absent/unreadable — build with graph_preflight before a coverage FAIL is possible"}

    if not nodes:
        return {"status": STATUS_EMPTY, "coverage_status": "UNVERIFIABLE", "nodes": [],
                "graph_languages": [], "repo_languages": repo_langs,
                "unverifiable_languages": repo_langs,
                "note": "graph.json present but has 0 nodes — treated as no coverage ground truth"}

    graph_langs = set()
    for n in nodes:
        lang = _lang_of(n.get("source_file") or "")
        if lang:
            graph_langs.add(lang)

    # A repo language graphify CANNOT index (SQL, COBOL, Pascal, …) is always UNVERIFIABLE — its
    # absence from the graph is expected, NEVER a PARTIAL defect. Only a GRAPHABLE repo language
    # missing from the graph signals a truly partial index. This is why a plain JS/TS app with a
    # `migrations/*.sql` folder stays coverage_status OK (SQL is non-graphable, not "missing").
    non_graphable_repo = sorted(l for l in repo_langs if l not in GRAPHABLE_LANGS)
    missing_graphable = sorted(l for l in repo_langs if l in GRAPHABLE_LANGS and l not in graph_langs)
    unverifiable = sorted(set(non_graphable_repo) | set(missing_graphable))

    # STALE check (best-effort; only fires when the graph actually stamps a commit).
    build_commit = _graph_build_commit_from_path(graph_path)
    head = _git_head(repo_root)
    if build_commit and head and not head.startswith(build_commit) and not build_commit.startswith(head):
        return {"status": STATUS_STALE, "coverage_status": "UNVERIFIABLE", "nodes": nodes,
                "graph_languages": sorted(graph_langs), "repo_languages": repo_langs,
                "unverifiable_languages": repo_langs,
                "note": f"graph built at {build_commit[:12]} != HEAD {head[:12]} — rebuild before a coverage FAIL"}

    # PARTIAL check: a GRAPHABLE repo language with zero graph nodes (graphify should have indexed it).
    if missing_graphable:
        return {"status": STATUS_PARTIAL, "coverage_status": "UNVERIFIABLE", "nodes": nodes,
                "graph_languages": sorted(graph_langs), "repo_languages": repo_langs,
                "unverifiable_languages": unverifiable,
                "note": f"graph indexed {sorted(graph_langs)} but repo also has graphable "
                        f"{missing_graphable} with no nodes — findings on {unverifiable} files are UNVERIFIABLE"}

    return {"status": STATUS_OK, "coverage_status": "OK", "nodes": nodes,
            "graph_languages": sorted(graph_langs), "repo_languages": repo_langs,
            "unverifiable_languages": non_graphable_repo,
            "note": ("graph complete for all graphable repo languages"
                     + (f"; non-graphable {non_graphable_repo} are UNVERIFIABLE (graphify does not index them)"
                        if non_graphable_repo else ""))}


def _graph_build_commit_from_path(graph_path: Path) -> str | None:
    try:
        g = json.loads(graph_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return _graph_build_commit(g) if isinstance(g, dict) else None


def lang_of(path: str) -> str | None:
    """Public helper — language of a source path (phantom/orphan libs share the map)."""
    return _lang_of(path)
