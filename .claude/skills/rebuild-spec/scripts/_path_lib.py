# layout-exempt: rebuild-spec path helpers — all docs/components paths here are this skill's own managed targets
"""Shared path-safety helpers for rebuild-spec scripts.

Stdlib only. Consumers: build_navigation.py (Phase C), synthesize_system.py (Phase D),
the orchestrator path-resolution layer (Phase R — `--root`).
"""
from __future__ import annotations

import os
import sys
from typing import NamedTuple

from _lang_lib import resolve_docs_root  # noqa: E402


def component_name(rel_path: str) -> str:
    """Derive a collision-safe component `<name>` from a repo-relative sub-repo path.

    Path-based, NOT basename (RT2-F14): `services/payments/api` -> `services-payments-api`
    so `services/payments/api` and `billing/api` never collide on the bare basename `api`.
    """
    norm = rel_path.strip("/").replace("\\", "/")
    return norm.replace("/", "-") if norm else ""


class ComponentPaths(NamedTuple):
    name: str
    docs_root: str       # <root>/<lang_root>/components/<name>  (or <cwd>/docs in single-repo en mode)
    plan_dir: str        # plans/<active>/components/<name> (or plans/<active> in single-repo mode)
    state_file: str      # <docs_root>/.rebuild-state.json
    root: str            # the resolved, guarded sub-repo root (== project_root in single-repo mode)


def resolve_component_paths(
    project_root: str,
    active_plan_dir: str,
    root_arg: str | None = None,
    primary_lang: str | None = None,
) -> ComponentPaths:
    """Resolve docs_root / plan_dir / state_file, scoped by `--root <subrepo>` when given.

    Phase R single source of path resolution. `root_arg is None` reproduces the legacy single-repo
    layout EXACTLY for en-primary repos (docs at `<project_root>/docs`, state at
    `docs/.rebuild-state.json`, plan_dir unchanged) — so a run without `--root` is byte-for-byte
    backward-compatible when primary_lang is None/"en". When `root_arg` is given it MUST be a path
    under `project_root` (guarded — no `..`/symlink escape) and output is isolated per-component
    under `<comp_base>/components/<name>/` (centralized at the monorepo root).

    primary_lang (v23.0.0 — BREAKING for non-en):
        Routes the component SOURCE path through resolve_docs_root so a non-en primary writes/reads
        components under `docs/<primary>/components/<name>` instead of `docs/components/<name>`.
        en-primary (None or "en") stays `docs/components/<name>` — byte-identical to v22 (back-compat).

        CALLER NOTE: always pass the discovered primary_lang (from state.primary_lang or
        --primary-lang). If omitted on a non-en primary repo, components will still land at
        docs/components/ (old en layout) — the R1 risk.
    """
    eff_primary = primary_lang or "en"
    # Compute the language-namespaced components base:
    # resolve_docs_root("en","en") → "docs"; resolve_docs_root("vi","vi") → "docs/vi"
    comp_base = resolve_docs_root(eff_primary, eff_primary, multilang=False)

    # CALLER NOTE: always pass primary_lang on non-en repos. When omitted, eff_primary
    # defaults to "en" (safe for en repos, byte-compatible with v22). Non-en repos that
    # omit primary_lang will write to docs/components/ (old en layout) — the R1 risk.

    proj = os.path.realpath(os.path.abspath(project_root))
    if root_arg is None:
        docs_root = os.path.join(proj, comp_base.rstrip("/"))
        return ComponentPaths(
            name="",
            docs_root=docs_root,
            plan_dir=os.path.abspath(active_plan_dir),
            state_file=os.path.join(docs_root, ".rebuild-state.json"),
            root=proj,
        )
    # Guard: the sub-repo root must stay under the project root (path-traversal/symlink-escape reject).
    sub_root = _resolve_guarded(os.path.join(proj, root_arg), proj)
    rel = os.path.relpath(sub_root, proj)
    name = component_name(rel)
    if not name or name.startswith(".."):
        raise ValueError(f"--root {root_arg!r} does not resolve to a sub-path of the project root")
    docs_root = os.path.join(proj, comp_base.rstrip("/"), "components", name)
    return ComponentPaths(
        name=name,
        docs_root=docs_root,
        plan_dir=os.path.join(os.path.abspath(active_plan_dir), "components", name),
        state_file=os.path.join(docs_root, ".rebuild-state.json"),
        root=sub_root,
    )


def _resolve_guarded(path: str, base: str) -> str:
    """Resolve *path* and verify it stays under *base*.

    Returns the fully-resolved absolute path string.
    Raises ValueError if the resolved path escapes *base*.

    This is the canonical shared implementation — build_session_context.py keeps
    its own local copy (left untouched per spec), but all new consumers import from
    here to avoid copy-drift.
    """
    resolved = os.path.realpath(os.path.abspath(path))
    base_resolved = os.path.realpath(os.path.abspath(base))
    if os.path.commonpath([resolved, base_resolved]) != base_resolved:
        raise ValueError(f"Path traversal detected: {path!r} escapes {base!r}")
    return resolved
