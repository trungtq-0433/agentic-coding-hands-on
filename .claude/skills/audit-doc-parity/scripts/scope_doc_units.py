#!/usr/bin/env python3
"""Step 1a — Discover behavioral doc units and assemble code regions.

Discovers docs per regen-schema-contract.md § Artifact discovery map,
parses **Source:** citations, and assembles code regions (citation span +
enclosing function/class block via a simple brace/indent heuristic).

LIMITATION: The enclosing-block extractor uses a simple brace/indent
heuristic, not a full AST. It works for common C-family and Python shapes
but may miss closures, decorators, or deeply nested constructs. Per the
phase-02 risk note, full AST parsing is out of scope for this phase.

Emits doc-units.json. Stdlib only. Never emits verdicts.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import (  # noqa: E402
    STATUS_OK, CitationRef, parse_citations, read_text_safe,
    resolve_citation, resolve_docs_root, resolve_project_root, validate_citation,
)

# ---------------------------------------------------------------------------
# Exclusion skip-set (legacy group A — both directions)
# Mirrors rebuild-spec de-facto convention from _credential_scrub_lib.py,
# extract_data_flow.py, and _extractor_lib.py.
# ---------------------------------------------------------------------------
_EXCLUDED_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build",
    "target", "__pycache__", ".venv",
}
_EXCLUDED_PATTERNS = re.compile(
    r"(\.min\.js|\.min\.css|\.lock|package-lock\.json|"
    r"yarn\.lock|composer\.lock|Gemfile\.lock)$"
)
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mp3", ".avi", ".mov", ".wav",
    ".pyc", ".pyo",
}

# File-size cap for enclosing-block extraction (lines). Configurable via env.
_DEFAULT_BLOCK_CAP = int(os.environ.get("AUDIT_PARITY_BLOCK_CAP", "2000"))

# Artifact discovery map (regen-schema-contract.md § Artifact discovery map)
# Each entry: (glob_pattern_relative_to_docs, artifact_type, granularity)
_DISCOVERY_MAP = [
    # Per-feature technical-spec
    ("features/*/technical-spec.md",   "technical-spec",  "feature"),
    # Per-feature screen-spec (either name)
    ("features/*/screen-spec.md",      "screen-spec",     "feature"),
    ("features/*/screens.md",          "screen-spec",     "feature"),
    # System-level docs
    ("system/behavior-logic.md",       "behavior-logic",  "system"),
    ("generated/behavior-logic.md",    "behavior-logic",  "system"),
    ("generated/api-*.md",             "api",             "system"),
    ("generated/api-contracts.md",     "api",             "system"),
    ("generated/api-map.md",           "api",             "system"),
    ("api-contracts.md",               "api",             "system"),
    ("api-map.md",                     "api",             "system"),
    ("generated/entities.md",          "data-models",     "system"),
    ("generated/data-model.md",        "data-models",     "system"),
    ("data-model.md",                  "data-models",     "system"),
    ("entities.md",                    "data-models",     "system"),
]

_FCODE_RE = re.compile(r"^(F\d{3})_")


def _is_excluded_path(path: Path, project_root: Path) -> bool:
    """Return True if the path is in an excluded dir/pattern (group A)."""
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        rel = path
    for part in rel.parts:
        if part in _EXCLUDED_DIRS:
            return True
    if _EXCLUDED_PATTERNS.search(path.name):
        return True
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return True
    return False


def _discover_doc_paths(docs_root: Path, feature_filter: str | None,
                         path_filter: Path | None) -> list[tuple[Path, str, str]]:
    """Return list of (doc_path, artifact_type, unit_id) to process."""
    if path_filter:
        artifact = _infer_artifact(path_filter)
        unit_id = _make_unit_id(path_filter, artifact)
        return [(path_filter, artifact, unit_id)]

    results: list[tuple[Path, str, str]] = []
    seen: set[Path] = set()

    for pattern, artifact_type, granularity in _DISCOVERY_MAP:
        for doc_path in sorted(docs_root.glob(pattern)):
            if not doc_path.is_file() or doc_path in seen:
                continue
            if feature_filter:
                # Only include paths that belong to the requested feature dir
                if granularity == "feature":
                    parent_name = doc_path.parent.name
                    if not parent_name.startswith(feature_filter):
                        continue
                else:
                    # System docs: include when feature filter is set only if
                    # they carry citations relevant to the feature (include all)
                    pass
            seen.add(doc_path)
            unit_id = _make_unit_id(doc_path, artifact_type)
            results.append((doc_path, artifact_type, unit_id))

    return results


def _infer_artifact(path: Path) -> str:
    name = path.stem.lower()
    if "technical-spec" in name or "technical_spec" in name:
        return "technical-spec"
    if "screen" in name:
        return "screen-spec"
    if "behavior" in name or "behaviour" in name:
        return "behavior-logic"
    if "api" in name:
        return "api"
    if "data-model" in name or "entities" in name or "entity" in name:
        return "data-models"
    return "technical-spec"


def _make_unit_id(doc_path: Path, artifact_type: str) -> str:
    parent = doc_path.parent.name
    m = _FCODE_RE.match(parent)
    if m:
        return parent  # e.g. F012_OrderExport
    if artifact_type == "behavior-logic":
        return "system.behavior-logic"
    if artifact_type == "api":
        return f"system.{doc_path.stem}"
    if artifact_type == "data-models":
        return f"system.{doc_path.stem}"
    return f"system.{doc_path.stem}"


# ---------------------------------------------------------------------------
# Enclosing-block extraction (simple brace/indent heuristic)
# ---------------------------------------------------------------------------

def _extract_enclosing_block_brace(lines: list[str], anchor_start: int, anchor_end: int,
                                    cap: int) -> tuple[int, int, bool]:
    """Find the enclosing { } block for the anchor span (0-based indices).

    Walks backward from anchor_start to find an opening '{', then forward
    to find the matching '}'. Falls back to the anchor span if not found.
    Returns (block_start, block_end, truncated) with 0-based indices.

    LIMITATION: Does not handle string literals or nested lambdas correctly.
    """
    n = len(lines)
    # Walk back to find opening brace line
    open_line = anchor_start
    depth = 0
    for i in range(anchor_start, -1, -1):
        for ch in reversed(lines[i]):
            if ch == "}":
                depth += 1
            elif ch == "{":
                if depth == 0:
                    open_line = i
                    break
                depth -= 1
        else:
            continue
        break

    # Walk forward to find closing brace
    depth = 0
    close_line = anchor_end
    started = False
    for i in range(open_line, n):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}" and started:
                depth -= 1
                if depth == 0:
                    close_line = i
                    break
        else:
            if started and depth == 0:
                break
            continue
        break

    block_len = close_line - open_line + 1
    if block_len > cap:
        return anchor_start, anchor_end, True
    return open_line, close_line, False


def _extract_enclosing_block_indent(lines: list[str], anchor_start: int, anchor_end: int,
                                     cap: int) -> tuple[int, int, bool]:
    """Find the enclosing indented block (Python-style) for the anchor span.

    Looks for a def/class line with less indentation above anchor_start,
    then extends to where indentation returns to the same level.
    Returns (block_start, block_end, truncated) with 0-based indices.

    LIMITATION: Decorators and multi-line signatures may not be fully captured.
    Falls back to anchor span if no def/class header found.
    """
    n = len(lines)
    if anchor_start >= n:
        return anchor_start, anchor_end, False

    # Determine anchor indentation
    anchor_indent = len(lines[anchor_start]) - len(lines[anchor_start].lstrip())

    # Walk backward for def/class header at lower indentation
    header_line = anchor_start
    _DEF_CLASS_RE = re.compile(r"^\s*(def |class |async def )")
    for i in range(anchor_start, -1, -1):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent < anchor_indent and _DEF_CLASS_RE.match(line):
            header_line = i
            break

    # Walk forward: extend until indentation drops back to header level or less
    header_stripped = lines[header_line].lstrip()
    header_indent = len(lines[header_line]) - len(header_stripped)
    end_line = anchor_end
    for i in range(header_line + 1, n):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            end_line = i  # blank lines included
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= header_indent and i > header_line:
            break
        end_line = i

    block_len = end_line - header_line + 1
    if block_len > cap:
        return anchor_start, anchor_end, True
    return header_line, end_line, False


def _extract_enclosing_block(all_lines: list[str], start_0: int, end_0: int,
                              path: Path, cap: int) -> tuple[int, int, bool]:
    """Dispatch to brace or indent heuristic based on file extension."""
    _BRACE_EXTS = {
        ".js", ".ts", ".jsx", ".tsx", ".java", ".cs", ".php",
        ".c", ".cpp", ".h", ".go", ".rs", ".swift", ".kt",
        ".rb", ".scala", ".groovy",
    }
    ext = path.suffix.lower()
    if ext in _BRACE_EXTS:
        return _extract_enclosing_block_brace(all_lines, start_0, end_0, cap)
    # Python and everything else: indent heuristic
    return _extract_enclosing_block_indent(all_lines, start_0, end_0, cap)


def _is_excluded_raw(raw_path: str) -> bool:
    """Pre-resolution exclusion check on raw citation path string (group A).

    Catches node_modules/*, vendor/*, etc. before we even try to resolve.
    """
    parts = Path(raw_path).parts
    for part in parts:
        if part in _EXCLUDED_DIRS:
            return True
    if _EXCLUDED_PATTERNS.search(raw_path):
        return True
    suffix = Path(raw_path).suffix.lower()
    if suffix in _BINARY_SUFFIXES:
        return True
    return False


def _build_region(ref: CitationRef, doc_path: Path, project_root: Path,
                   cap: int) -> dict | None:
    """Validate citation and build a code region dict.

    Returns None if the cited file is under an excluded path.
    Returns a region dict with status info (truncated, unverifiable, etc.).
    """
    # Group A exclusion: check raw path before resolving (catches node_modules etc.)
    if _is_excluded_raw(ref.raw_path):
        return None

    result = validate_citation(ref, doc_path, project_root)
    resolved = result.get("resolved_path")

    # Group A exclusion: also check resolved path (catches symlinks into excluded dirs)
    if resolved and _is_excluded_path(resolved, project_root):
        return None

    if result["status"] != STATUS_OK:
        try:
            rel = str(resolved.relative_to(project_root)) if resolved else ref.raw_path
        except ValueError:
            rel = ref.raw_path
        return {
            "path": rel,
            "start": ref.start,
            "end": ref.end,
            "code": None,
            "truncated": False,
            "unverifiable": True,
            "unverifiable_reason": result["status"],
        }

    # Read full file for enclosing-block extraction.
    # Guard against TOCTOU: file may disappear between validate_citation and here.
    _second_read = read_text_safe(resolved)
    if _second_read is None:
        try:
            rel = str(resolved.relative_to(project_root)) if resolved else ref.raw_path
        except ValueError:
            rel = ref.raw_path
        return {
            "path": rel,
            "start": ref.start,
            "end": ref.end,
            "code": None,
            "truncated": False,
            "unverifiable": True,
            "unverifiable_reason": "file_unreadable_after_validation",
        }
    all_text, _ = _second_read
    all_lines = all_text.splitlines()

    start_0 = ref.start - 1  # convert to 0-based
    end_0 = ref.end - 1

    block_start, block_end, truncated = _extract_enclosing_block(
        all_lines, start_0, end_0, resolved, cap
    )

    code_lines = all_lines[block_start: block_end + 1]

    try:
        rel_path = str(resolved.relative_to(project_root))
    except ValueError:
        rel_path = str(resolved)

    return {
        "path": rel_path,
        # Report the enclosing block range (1-based) so callers know exact lines
        "start": block_start + 1,
        "end": block_end + 1,
        # The originally cited span within the block
        "citation_start": ref.start,
        "citation_end": ref.end,
        "code": "\n".join(code_lines),
        "truncated": truncated,
        "unverifiable": False,
        "unverifiable_reason": None,
    }


def _process_doc(doc_path: Path, artifact_type: str, unit_id: str,
                  project_root: Path, cap: int) -> dict:
    """Process a single doc file into a unit dict."""
    read_result = read_text_safe(doc_path)
    if read_result is None:
        return {
            "unit": unit_id,
            "artifact": artifact_type,
            "doc_paths": [str(doc_path.relative_to(project_root))],
            "regions": [],
            "citation_coverage": False,
            "unverifiable": [{"reason": "doc_unreadable", "doc": str(doc_path)}],
        }

    doc_text, _ = read_result
    citations = parse_citations(doc_text)

    regions: list[dict] = []
    unverifiable: list[dict] = []

    for ref in citations:
        region = _build_region(ref, doc_path, project_root, cap)
        if region is None:
            # Excluded path — skip silently (group A)
            continue
        if region["unverifiable"]:
            unverifiable.append({
                "raw_path": ref.raw_path,
                "doc_line": ref.line_no,
                "reason": region["unverifiable_reason"],
            })
        regions.append(region)

    try:
        rel_doc = str(doc_path.relative_to(project_root))
    except ValueError:
        rel_doc = str(doc_path)

    return {
        "unit": unit_id,
        "artifact": artifact_type,
        "doc_paths": [rel_doc],
        "regions": regions,
        "citation_coverage": len(citations) > 0,
        "unverifiable": unverifiable,
    }


def _merge_screen_spec_into_technical(units: list[dict]) -> list[dict]:
    """Fold screen-spec units into the matching technical-spec unit if they share
    the same feature dir (regen-schema-contract.md: screen-spec granularity = feature)."""
    tech_by_unit: dict[str, dict] = {}
    screen_units: list[dict] = []
    other_units: list[dict] = []

    for u in units:
        if u["artifact"] == "technical-spec":
            tech_by_unit[u["unit"]] = u
        elif u["artifact"] == "screen-spec":
            screen_units.append(u)
        else:
            other_units.append(u)

    for su in screen_units:
        fcode_match = _FCODE_RE.match(su["unit"])
        if fcode_match:
            # Find matching technical-spec unit with same fcode prefix
            matched = None
            for key in tech_by_unit:
                if key.startswith(fcode_match.group(1)):
                    matched = key
                    break
            if matched:
                # Fold: extend doc_paths and regions
                tech_by_unit[matched]["doc_paths"].extend(su["doc_paths"])
                tech_by_unit[matched]["regions"].extend(su["regions"])
                tech_by_unit[matched]["unverifiable"].extend(su["unverifiable"])
                if su["citation_coverage"]:
                    tech_by_unit[matched]["citation_coverage"] = True
                continue
        # No matching technical-spec — keep as standalone screen-spec unit
        other_units.append(su)

    return list(tech_by_unit.values()) + other_units


def _atomic_write(path: Path, data: object) -> None:
    """Write JSON atomically via .tmp + os.replace (pattern from rebuild-spec)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Discover doc units and assemble code regions")
    p.add_argument("--project-root", default=None, help="Project root (default: git toplevel)")
    p.add_argument("--feature", default=None, metavar="F###",
                   help="Limit discovery to a single feature code (e.g. F012)")
    p.add_argument("--path", default=None, metavar="DOC",
                   help="Process a single doc file instead of auto-discovery")
    p.add_argument("--out", default="doc-units.json", metavar="FILE",
                   help="Output path (default: doc-units.json)")
    p.add_argument("--block-cap", type=int, default=_DEFAULT_BLOCK_CAP,
                   metavar="LINES",
                   help="Max lines for enclosing-block extraction before falling back "
                        "to cited span (default: %(default)s, or env AUDIT_PARITY_BLOCK_CAP)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    docs_root = resolve_docs_root(project_root)

    path_filter: Path | None = None
    if args.path:
        path_filter = Path(args.path).resolve()
        if not path_filter.is_file():
            print(f"[ERROR] --path is not a file: {path_filter}", file=sys.stderr)
            return 2

    if not docs_root.is_dir() and path_filter is None:
        print(f"[ERROR] docs/ directory not found under project root: {project_root}",
              file=sys.stderr)
        return 2

    doc_entries = _discover_doc_paths(docs_root, args.feature, path_filter)
    if not doc_entries:
        print("[WARN] no doc units discovered — check --project-root or --feature",
              file=sys.stderr)
        units: list[dict] = []
    else:
        units_raw = [
            _process_doc(doc_path, artifact_type, unit_id, project_root, args.block_cap)
            for doc_path, artifact_type, unit_id in doc_entries
        ]
        units = _merge_screen_spec_into_technical(units_raw)

    out_path = Path(args.out).resolve()
    _atomic_write(out_path, units)
    print(f"[scope_doc_units] wrote {len(units)} unit(s) → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
