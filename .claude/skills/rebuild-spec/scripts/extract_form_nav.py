#!/usr/bin/env python3
"""Delphi form-nav extractor (Phase 03).

Parses .pas units for Show/ShowModal/CreateForm navigation, computes
transitive reachability from the .dpr root form, and emits a digest.
LIMITATION: `with` blocks / aliased form vars → conservative unverified.
Exit: always 0 (advisory). Stdlib only.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _extractor_lib import (
    decode_source,
    is_extractor_completed,
    source_tree_hash,
    update_manifest,
    write_digest_atomic,
)
from _form_nav_lib import analyse_unit, extract_dpr_forms

EXTRACTOR_NAME = "extract_form_nav"

_PAS_GLOBS = ["*.pas", "*.pp"]
_DPR_GLOBS = ["*.dpr"]
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}
_MAX_FILE_BYTES = 10 * 1024 * 1024


def _walk(root: Path, globs: list[str]) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if any(fnmatch.fnmatch(fn, g) for g in globs):
                found.append(Path(dirpath) / fn)
    return found


def _load(path: Path, root: Path, primary: str, fallback: str) -> tuple[str | None, list[str]]:
    rel = str(path.relative_to(root))
    warns: list[str] = []
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            warns.append(f"skipped_oversized: {rel}"); return None, warns
    except OSError as e:
        warns.append(f"stat_error: {rel}: {e}"); return None, warns
    try:
        text, dw = decode_source(path, primary, fallback)
        warns.extend(dw)
        return text, warns
    except OSError as e:
        warns.append(f"read_error: {rel}: {e}"); return None, warns


def extract(
    root: str | Path,
    plan_dir: str | Path,
    encoding: str = "utf-8",
    fallback: str = "latin-1",
) -> dict[str, Any]:
    root_p = Path(root).resolve()
    plan_p = Path(plan_dir).resolve()
    all_warnings: list[str] = []
    file_count = 0
    error_count = 0

    # Pass 1: analyse all .pas units
    unit_infos: list[dict[str, Any]] = []
    for path in _walk(root_p, _PAS_GLOBS):
        file_count += 1
        text, warns = _load(path, root_p, encoding, fallback)
        all_warnings.extend(warns)
        if any(w.startswith(("read_error", "stat_error")) for w in warns):
            error_count += 1
        if text is not None:
            unit_infos.append(analyse_unit(path, root_p, text, warns))

    # Build lookups: class → unit_name, unit_name → file, class → decl line
    class_to_unit: dict[str, str] = {}
    unit_to_file: dict[str, str] = {}
    class_decl_line: dict[str, int] = {}
    for info in unit_infos:
        unit_to_file[info["unit_name"]] = info["file"]
        for cls in info["form_classes"]:
            if cls not in class_to_unit:
                class_to_unit[cls] = info["unit_name"]
                class_decl_line[cls] = info["class_decl_line"].get(cls, 1)

    # Find root form from first .dpr Application.CreateForm
    root_class: str | None = None
    for dpr_path in _walk(root_p, _DPR_GLOBS):
        text, warns = _load(dpr_path, root_p, encoding, fallback)
        all_warnings.extend(warns)
        if text:
            creates = extract_dpr_forms(text)
            if creates:
                root_class = creates[0][0]
                break

    # Global var→class map (across all units) for cross-unit resolution
    global_var_to_class: dict[str, str] = {}
    for info in unit_infos:
        for var, cls in info["var_to_class"].items():
            if var not in global_var_to_class:
                global_var_to_class[var] = cls

    # Pass 2: build edges + adjacency for reachability
    edges: list[dict[str, Any]] = []
    adj: dict[str, set[str]] = {cls: set() for cls in class_to_unit}

    for info in unit_infos:
        if not info["form_classes"]:
            continue
        from_class = info["form_classes"][0]
        # E1: a .pas defining >1 form class is non-conventional; all this unit's nav edges are
        # attributed to the first form class. Surface it so the attribution is not silently wrong.
        if len(info["form_classes"]) > 1:
            all_warnings.append(
                f"multi_form_class: {info['file']} declares "
                f"{len(info['form_classes'])} form classes "
                f"({', '.join(info['form_classes'])}); nav edges attributed to "
                f"{from_class!r} (first declared)"
            )
        for raw_e in info["raw_edges"]:
            to_cls = raw_e["to_class"]
            raw_unverified = raw_e.get("unverified", False)
            # Attempt cross-unit resolution: raw "unverified" edges may be var names
            if raw_unverified and to_cls in global_var_to_class:
                to_cls = global_var_to_class[to_cls]
                raw_unverified = False
            unverified = raw_unverified or (to_cls not in class_to_unit)
            edge: dict[str, Any] = {
                "from": from_class,
                "to": to_cls,
                "kind": raw_e["kind"],
                "file": raw_e["file"],
                "line": raw_e["line"],
            }
            if unverified:
                edge["unverified"] = True
            edges.append(edge)
            if not unverified and to_cls in adj:
                adj.setdefault(from_class, set()).add(to_cls)

    # BFS reachability from root
    reachable: set[str] = set()
    if root_class and root_class in class_to_unit:
        queue: deque[str] = deque([root_class])
        reachable.add(root_class)
        while queue:
            cur = queue.popleft()
            for nb in adj.get(cur, set()):
                if nb not in reachable:
                    reachable.add(nb)
                    queue.append(nb)

    form_nodes = [
        {
            "name": cls,
            "unit": class_to_unit[cls],
            "file": unit_to_file.get(class_to_unit[cls], ""),
            "line": class_decl_line.get(cls, 1),
            "reach": "static" if cls in reachable else "unverified",
        }
        for cls in class_to_unit
    ]

    digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_tree_hash": source_tree_hash(root_p, _PAS_GLOBS + _DPR_GLOBS),
        "_limitation": (
            "with blocks and aliased form vars defeat naive regex; "
            "such edges are emitted as unverified rather than wrong edges. "
            "A .pas declaring >1 form class attributes its nav edges to the "
            "first-declared class (see warnings[] 'multi_form_class')."
        ),
        "root_form": root_class,
        "forms": form_nodes,
        "edges": edges,
        "warnings": all_warnings,
    }

    write_digest_atomic(plan_p, EXTRACTOR_NAME, digest)
    update_manifest(plan_p, EXTRACTOR_NAME, file_count, error_count)
    return digest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Delphi form-nav extractor.")
    p.add_argument("--root", required=True)
    p.add_argument("--plan-dir", required=True)
    p.add_argument("--encoding", default="utf-8")
    p.add_argument("--fallback", default="latin-1")
    args = p.parse_args(argv)
    plan_p = Path(args.plan_dir).resolve()
    if is_extractor_completed(plan_p, EXTRACTOR_NAME):
        print(json.dumps({"status": "skipped", "reason": "already completed"}))
        return 0
    digest = extract(args.root, plan_p, args.encoding, args.fallback)
    print(json.dumps({"status": "ok", "forms": len(digest["forms"]),
                      "edges": len(digest["edges"]), "warnings": len(digest["warnings"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
