# layout-exempt: rebuild-spec nav I/O — all docs/components paths here are this skill's own output targets
"""I/O wiring for the components-index renderers (build_navigation.run() helpers).

Separated from _nav_components_index.py (pure renderers) so each file stays
under 200 LOC. Stdlib only.

v14.1.0 changes:
- load_component_meta: overlays role+reused from docs/.rebuild-system-state.json
  (fallback: .rebuild-components.json). Keeps primary_lang from per-component state.
- write_components_index: also writes per-component top README.md (Fix 3).
- write_components_index: resolves lang from system-state primary_lang (Fix 4).
State overlay + lang-resolution helpers live in _nav_state_overlay_lib.py.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

from _nav_components_index import (
    build_component_system_readme,
    build_components_index_readme,
)
from _nav_index import build_index_readme as _build_top_index_readme
from _nav_state_overlay_lib import load_system_state_overlay, resolve_lang_from_state


def _atomic_write(path: str, content: str) -> None:
    """Write content to path atomically (rename-after-write)."""
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".nav_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_component_meta(components_root: str) -> list[dict]:
    """Read .rebuild-state.json from each immediate child of components_root.

    Returns a list of dicts: {name, role, reused, primary_lang}.
    Only children that have a .rebuild-state.json are included.

    v14.1.0: overlays role+reused from docs/.rebuild-system-state.json (or
    fallback .rebuild-components.json). The per-component .rebuild-state.json
    only has primary_lang reliably; role+reused come from the system-level state.
    """
    overlay = load_system_state_overlay(components_root)

    meta: list[dict] = []
    try:
        children = sorted(
            d for d in os.listdir(components_root)
            if os.path.isdir(os.path.join(components_root, d))
        )
    except OSError:
        return meta
    for child in children:
        state_path = os.path.join(components_root, child, ".rebuild-state.json")
        if not os.path.isfile(state_path):
            continue
        try:
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, ValueError):
            state = {}
        # Overlay: role+reused from system-state; primary_lang from per-component state.
        sys_entry = overlay.get(child, {})
        meta.append({
            "name": child,
            "role": sys_entry.get("role") or state.get("role", ""),
            "reused": sys_entry["reused"] if "reused" in sys_entry else bool(state.get("reused", False)),
            "primary_lang": state.get("primary_lang", "en"),
        })
    return meta


def write_components_index(docs_root: str, lang: str | None, timestamp: str) -> None:
    """Write components/README.md, each component's system/README.md, and top README.md.

    v14.1.0 changes:
    - Fix 3: also writes per-component top README.md (fixes mirror 404).
    - Fix 4: resolves lang from system-state primary_lang when lang is None.
    """
    components_root = os.path.join(docs_root, "components")
    effective_lang = resolve_lang_from_state(lang, components_root)
    meta = load_component_meta(components_root)
    if not meta:
        return
    # docs/components/README.md
    index_path = os.path.join(components_root, "README.md")
    existing = ""
    if os.path.isfile(index_path):
        try:
            with open(index_path, encoding="utf-8") as f:
                existing = f.read()
        except OSError:
            pass
    content = build_components_index_readme(
        components_root, meta, effective_lang, timestamp, existing
    )
    try:
        _atomic_write(index_path, content)
    except OSError as e:
        print(f"[ERROR] cannot write components/README.md: {e}", file=sys.stderr)
    # Per-component system/README.md AND top README.md
    for comp in meta:
        comp_dir = os.path.join(components_root, comp["name"])
        comp_lang = effective_lang or comp.get("primary_lang") or "en"

        # Fix 3: write top-level <component>/README.md (idempotent).
        top_readme = os.path.join(comp_dir, "README.md")
        existing_top = ""
        if os.path.isfile(top_readme):
            try:
                with open(top_readme, encoding="utf-8") as f:
                    existing_top = f.read()
            except OSError:
                pass
        try:
            top_content = _build_top_index_readme(comp_dir, comp_lang, timestamp, existing_top)
            _atomic_write(top_readme, top_content)
        except OSError as e:
            print(f"[ERROR] cannot write {top_readme}: {e}", file=sys.stderr)

        # Per-component system/README.md
        sys_dir = os.path.join(comp_dir, "system")
        if not os.path.isdir(sys_dir):
            continue
        sys_readme = os.path.join(sys_dir, "README.md")
        existing_sys = ""
        if os.path.isfile(sys_readme):
            try:
                with open(sys_readme, encoding="utf-8") as f:
                    existing_sys = f.read()
            except OSError:
                pass
        result = build_component_system_readme(sys_dir, comp_lang, timestamp, existing_sys)
        try:
            _atomic_write(sys_readme, result)
        except OSError as e:
            print(f"[ERROR] cannot write {sys_readme}: {e}", file=sys.stderr)
