"""Engine 1 — code-level orphan detection.

An ORPHAN is a source symbol present in `graph.json` but (a) absent from
`_source-to-fcode.json` (no feature spec cites it) AND (b) with zero mention in ANY in-scope
doc AND (c) material at the symbol level AND (d) in a graph-complete language. This is the gap
W7a does NOT cover — W7a gates cross-artifact references (route/entity/screen/US with no F###),
never a *source file/symbol with no doc trace at all* [Red-team Scope-F5].

Empty-index guard [RT-C5 / Red-team FM-F2]: the core-only pass emits `_source-to-fcode.json`
empty-but-valid before `--feature-specs` runs. A naive diff would then flag EVERY node as an
orphan → mass false FAIL. So: empty index AND absent `docs/features/` → orphans are UNVERIFIABLE,
never FAIL.

Materiality is symbol-level, not just path globs [Red-team FM-F7]: private/non-exported symbols,
common framework hooks, and generated/vendored/test/migration paths are exempt. What was filtered
is logged, never silent. Stdlib only.
"""
from __future__ import annotations

import re
from pathlib import Path

from _graph_state_lib import lang_of

# Path-level exemptions (mirror audit-doc-parity legacy group A + generated/migration).
_EXEMPT_PATH_RE = re.compile(
    r"(^|/)(tests?|test|__tests__|spec|specs|mocks?|fixtures?|vendor|third_party|"
    r"node_modules|dist|build|generated|gen|migrations?|__pycache__|\.venv|venv)(/|$)"
    r"|_test\.|\.test\.|\.spec\.|\.min\.|\.d\.ts$|_pb2\.py$"
)

# Symbol names that are framework hooks / entrypoints, not documentation-worthy units.
_EXEMPT_SYMBOLS = {
    "main", "__init__", "__main__", "setup", "teardown", "setUp", "tearDown",
    "setUpClass", "tearDownClass", "conftest",
}


def _normalize(path: str, repo_root: Path) -> str:
    """Normalise a graph source_file to repo-relative posix (matching index keys)."""
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(repo_root)
        except ValueError:
            pass
    return p.as_posix().lstrip("./")


def _symbol_of(node: dict) -> str:
    for key in ("label", "name", "symbol", "id"):
        v = node.get(key)
        if isinstance(v, str) and v:
            return v
    return "<anon>"


def _is_material(rel_path: str, symbol: str) -> tuple[bool, str]:
    """Return (material, reason_if_not)."""
    if _EXEMPT_PATH_RE.search(rel_path):
        return (False, "non-material path (test/vendor/generated/migration)")
    if symbol in _EXEMPT_SYMBOLS:
        return (False, f"framework hook / entrypoint symbol '{symbol}'")
    if symbol.startswith("_") and not symbol.startswith("__"):
        return (False, f"private/non-exported symbol '{symbol}'")
    return (True, "")


def _doc_mentions(rel_path: str, doc_texts: list[str]) -> bool:
    """True if the file path or its basename appears in any in-scope doc."""
    base = Path(rel_path).name
    for text in doc_texts:
        if rel_path in text or base in text:
            return True
    return False


def find_orphans(
    graph_nodes: list[dict],
    source_to_fcode_index: dict,
    doc_texts: list[str],
    repo_root: Path,
    unverifiable_languages: set[str],
    features_dir_present: bool,
) -> dict:
    """Detect code-level orphans.

    Returns:
        {
          "status": "OK" | "UNVERIFIABLE",
          "reason": "<why unverifiable, if so>",
          "orphans": [ {source_file, symbol, lang, evidence, kind: "ORPHAN"} ],
          "filtered": [ {source_file, symbol, reason} ],   # logged, never silent
        }
    """
    index = source_to_fcode_index.get("index", source_to_fcode_index) \
        if isinstance(source_to_fcode_index, dict) else {}
    index_keys = set(index.keys()) if isinstance(index, dict) else set()

    # Empty-index guard (RT-C5): empty-but-valid index + no docs/features → cannot judge orphans.
    if not index_keys and not features_dir_present:
        return {"status": "UNVERIFIABLE",
                "reason": "empty-but-valid _source-to-fcode.json and no docs/features/ "
                          "(core-only run) — orphan coverage cannot be judged; run --feature-specs first",
                "orphans": [], "filtered": []}

    orphans: list[dict] = []
    filtered: list[dict] = []
    for node in graph_nodes:
        src = node.get("source_file")
        if not src:
            continue
        rel = _normalize(src, repo_root)
        lang = lang_of(rel)
        if lang in unverifiable_languages:
            continue  # partial-graph language → not judged here
        if rel in index_keys:
            continue  # cited by a feature spec → covered
        symbol = _symbol_of(node)
        material, why = _is_material(rel, symbol)
        if not material:
            filtered.append({"source_file": rel, "symbol": symbol, "reason": why})
            continue
        if _doc_mentions(rel, doc_texts):
            continue  # documented somewhere, just not via a feature citation
        orphans.append({
            "source_file": rel, "symbol": symbol, "lang": lang or "unknown",
            "evidence": f"{rel} — graph node '{symbol}' has no feature-spec citation and no doc mention",
            "kind": "ORPHAN",
        })
    # De-dup orphans by (file, symbol).
    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for o in orphans:
        key = (o["source_file"], o["symbol"])
        if key not in seen:
            seen.add(key)
            deduped.append(o)
    return {"status": "OK", "reason": "", "orphans": deduped, "filtered": filtered}
