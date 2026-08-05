"""Engine 1 — phantom detection.

A PHANTOM is a synthesis artifact that cites `file:line` code which maps to NO node in the
graph — the doc describes a feature/US/flow whose code does not exist. Resolved by parsing each
artifact's `**Source:**` citations (reusing the copied `_citation_lib` regex) and cross-checking
the cited file against the set of files that carry graph nodes.

Graph-completeness gate [Red-team FM-F3]: a cited file is only a PHANTOM when the graph is
COMPLETE for that file's language. On a no-/partial-graph language the same citation is
UNVERIFIABLE — a partial graph must never manufacture a false phantom. File-level matching (any
node in that file) is the unit, to avoid false positives from graphify node granularity.

Stdlib only. No verdict of its own beyond PHANTOM / UNVERIFIABLE tagging.
"""
from __future__ import annotations

from pathlib import Path

from _citation_lib import parse_citations
from _graph_state_lib import lang_of


def _graph_files(graph_nodes: list[dict], repo_root: Path) -> set[str]:
    """Repo-relative posix set of every source file that carries a graph node."""
    files: set[str] = set()
    for n in graph_nodes:
        src = n.get("source_file")
        if not src:
            continue
        p = Path(src)
        if p.is_absolute():
            try:
                p = p.relative_to(repo_root)
            except ValueError:
                pass
        files.add(p.as_posix().lstrip("./"))
    return files


def _normalize_cited(raw: str) -> str:
    return Path(raw).as_posix().lstrip("./")


def find_phantoms(
    artifacts: list[dict],
    graph_nodes: list[dict],
    repo_root: Path,
    graph_status: str,
    unverifiable_languages: set[str],
) -> dict:
    """Detect phantom citations across in-scope artifacts.

    `artifacts` items: {"path": <abs>, "kind": ..., "present": bool}. Only present files parsed.

    Returns:
        {
          "phantoms": [ {artifact, source_file, cited_line, lang, evidence, kind: "PHANTOM"} ],
          "unverifiable": [ {artifact, source_file, reason} ],
        }
    """
    phantoms: list[dict] = []
    unverifiable: list[dict] = []

    # Absent/empty/stale graph → every citation is UNVERIFIABLE (cannot resolve to nodes).
    graph_complete_globally = graph_status == "OK" or graph_status == "PARTIAL"

    graph_files = _graph_files(graph_nodes, repo_root) if graph_nodes else set()

    for art in artifacts:
        if not art.get("present"):
            continue
        path = art.get("path")
        if not path:
            continue
        p = Path(path)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ref in parse_citations(text):
            rel = _normalize_cited(ref.raw_path)
            lang = lang_of(rel)
            # Language not graph-complete (absent/empty graph, or a partial-graph language) → UNVERIFIABLE.
            if not graph_complete_globally or (lang in unverifiable_languages) or (lang is None):
                unverifiable.append({
                    "artifact": art.get("kind", p.name),
                    "source_file": rel,
                    "reason": f"citation on a non-graph-complete language ({lang or 'unknown'}) — cannot resolve to a node",
                })
                continue
            if rel not in graph_files:
                phantoms.append({
                    "artifact": art.get("kind", p.name),
                    "source_file": rel,
                    "cited_line": ref.start,
                    "lang": lang,
                    "evidence": f"{rel}:{ref.start} cited in {art.get('kind', p.name)} maps to no graph node "
                                f"(language {lang} fully indexed)",
                    "kind": "PHANTOM",
                })
    # De-dup by (artifact, file, line).
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for ph in phantoms:
        key = (ph["artifact"], ph["source_file"], ph["cited_line"])
        if key not in seen:
            seen.add(key)
            deduped.append(ph)
    return {"phantoms": deduped, "unverifiable": unverifiable}
