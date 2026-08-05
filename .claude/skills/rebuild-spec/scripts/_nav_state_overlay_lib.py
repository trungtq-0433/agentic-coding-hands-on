# layout-exempt: rebuild-spec nav overlay — all docs/components paths here are this skill's own managed targets
"""System-state overlay helpers for rebuild-spec navigation (v14.1.0).

Extracted from _nav_components_io.py to keep each file under 200 LOC.

Provides role+reused overlay from docs/.rebuild-system-state.json
(fallback: .rebuild-components.json) and lang resolution from system-state
primary_lang. Stdlib only.
"""
from __future__ import annotations

import json
import os


def load_system_state_overlay(components_root: str) -> dict[str, dict]:
    """Load role+reused from docs/.rebuild-system-state.json (keyed by name).

    Falls back to .rebuild-components.json at the project root if system-state
    is absent. Returns a dict mapping component name -> {role, reused}.

    components_root is docs/components/; docs/ is its parent.
    """
    overlay: dict[str, dict] = {}

    # Primary: docs/.rebuild-system-state.json (parent of components_root)
    docs_root = os.path.dirname(components_root)
    sys_state_path = os.path.join(docs_root, ".rebuild-system-state.json")
    if os.path.isfile(sys_state_path):
        try:
            with open(sys_state_path, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("components", []):
                name = entry.get("name", "")
                if name:
                    overlay[name] = {
                        "role": entry.get("role", ""),
                        "reused": bool(entry.get("reused", False)),
                    }
            return overlay
        except (OSError, ValueError):
            pass

    # Fallback: .rebuild-components.json at project root (two levels up from docs/)
    project_root = os.path.dirname(docs_root)
    manifest_path = os.path.join(project_root, ".rebuild-components.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)
            entries = data if isinstance(data, list) else data.get("components", [])
            for entry in entries:
                name = entry.get("name", "")
                if name:
                    overlay[name] = {
                        "role": entry.get("role", ""),
                        "reused": bool(entry.get("reused", False)),
                    }
        except (OSError, ValueError):
            pass

    return overlay


def resolve_lang_from_state(lang: str | None, components_root: str) -> str | None:
    """Resolve lang from system-state primary_lang when lang is None (Fix 4).

    Returns the resolved lang string, or the original lang (possibly None)
    if system-state is absent or has no primary_lang.
    components_root is docs/components/; docs/ is its parent.
    """
    if lang is not None:
        return lang
    docs_root = os.path.dirname(components_root)
    sys_state_path = os.path.join(docs_root, ".rebuild-system-state.json")
    if os.path.isfile(sys_state_path):
        try:
            with open(sys_state_path, encoding="utf-8") as f:
                data = json.load(f)
            resolved = data.get("primary_lang")
            if resolved:
                return str(resolved)
        except (OSError, ValueError):
            pass
    return lang
