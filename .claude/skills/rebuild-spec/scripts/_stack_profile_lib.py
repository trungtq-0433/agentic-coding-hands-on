#!/usr/bin/env python3
"""Load, validate, and match stack-profiles (Phase A).

Trust boundary (RT-F5): profiles are loaded ONLY from the kit directory
`references/stack-profiles/`; never from the project under analysis. Extractor names
declared by a profile are validated against ALLOWED_EXTRACTORS before any extractor runs.

Glob safety (RT-F6): matching walks the tree with `os.walk(followlinks=False)` and a hard
file cap; `detection.globs` are evaluated with `fnmatch` against basenames only — never passed
to a shell or an unbounded walk.

Stdlib only.
"""
from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path

from _reused_root_lib import is_reused_root, read_reused_provenance

SCHEMA_VERSION = "22.1.0"

# Profiles live next to this lib, under references/stack-profiles/ (kit dir only).
PROFILES_DIR = Path(__file__).resolve().parent.parent / "references" / "stack-profiles"

# Extractor allowlist (RT-F5). A profile naming an extractor outside this set is rejected.
# Phase A ships extractors: [] everywhere; Phase B/D populate these.
ALLOWED_EXTRACTORS = {
    "extract_sql_schema",
    "extract_data_flow",
    "extract_service_topology",
    "extract_form_nav",
    "extract_cobol_screen",
    "extract_cobol_data",
}

# Directories never walked during detection (noise / vendored / VCS).
_SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", "__pycache__", "target",
    ".git", ".venv", "venv", ".idea", ".pytest_cache", "coverage",
}

_REQUIRED_KEYS = (
    "id", "display_name", "detected_language_heading", "detection",
    "source_encoding", "artifact_map", "screen_source", "extractors", "probe",
    "module_layout",
)

_VALID_ACTIONS = {"produce", "skip"}
_VALID_CLASSES = {"universal", "web", "stack-specific"}
# screen_source enum (v21.0.0). "form-module" reserved for a future oracle-forms profile.
# "cobol-screen" (Phase 01): one value routing SCREEN-SECTION vs BMS per-file (extract_cobol_screen).
# "ui-sniff" (Phase 01): Track D Tier-2 accept-path session override, reuses the dfm-form mechanism.
_VALID_SCREEN_SOURCES = {"route-view", "dfm-form", "form-module", "cobol-screen", "ui-sniff", "none"}


def validate_profile(profile: dict, stem: str) -> None:
    """Raise ValueError if profile violates the schema or trust boundary."""
    for key in _REQUIRED_KEYS:
        if key not in profile:
            raise ValueError(f"profile {stem!r}: missing required key {key!r}")
    if profile["id"] != stem:
        raise ValueError(f"profile {stem!r}: id {profile['id']!r} must equal filename stem")
    if not isinstance(profile["detection"].get("globs"), list):
        raise ValueError(f"profile {stem!r}: detection.globs must be a list")
    enc = profile["source_encoding"]
    if not isinstance(enc, dict) or "primary" not in enc or "fallback" not in enc:
        raise ValueError(f"profile {stem!r}: source_encoding needs primary + fallback")
    if not isinstance(profile["extractors"], list):
        raise ValueError(f"profile {stem!r}: extractors must be a list")
    bad = [e for e in profile["extractors"] if e not in ALLOWED_EXTRACTORS]
    if bad:
        raise ValueError(
            f"profile {stem!r}: extractor(s) {bad!r} not in allowlist {sorted(ALLOWED_EXTRACTORS)}"
        )
    if not isinstance(profile["probe"], dict) or "bootable" not in profile["probe"]:
        raise ValueError(f"profile {stem!r}: probe.bootable required")
    rd = profile.get("resource_decode")
    if rd is not None and not isinstance(rd, str):
        raise ValueError(f"profile {stem!r}: resource_decode must be null or a string")
    if "re_contract" in profile and not isinstance(profile["re_contract"], bool):
        raise ValueError(f"profile {stem!r}: re_contract must be a boolean")
    # Optional multi-component fields (Phase 01) — nullable lists of strings when present.
    # `component_boundary_globs`: basename globs that mark a component root (executables only,
    #   e.g. *.dpr) — overrides detection.globs for boundary detection ONLY (Phase 02).
    # `shared_layer_dirs`: dir basenames that are shared layers, never their own component (Phase 02/05).
    for opt_key in ("component_boundary_globs", "shared_layer_dirs"):
        if opt_key in profile:
            val = profile[opt_key]
            if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                raise ValueError(
                    f"profile {stem!r}: {opt_key} must be a list of strings when present"
                )
    if profile["screen_source"] not in _VALID_SCREEN_SOURCES:
        raise ValueError(
            f"profile {stem!r}: screen_source {profile['screen_source']!r} not in "
            f"{sorted(_VALID_SCREEN_SOURCES)}"
        )
    for art, spec in profile["artifact_map"].items():
        if not isinstance(spec, dict) or spec.get("action") not in _VALID_ACTIONS:
            raise ValueError(f"profile {stem!r}: artifact {art!r} action must be produce|skip")
        if spec.get("class") not in _VALID_CLASSES:
            raise ValueError(f"profile {stem!r}: artifact {art!r} class invalid")


def load_profiles(profiles_dir: Path | None = None) -> dict[str, dict]:
    """Load + validate every *.json profile from the kit dir. Raises on invalid profile."""
    base = profiles_dir or PROFILES_DIR
    profiles: dict[str, dict] = {}
    for path in sorted(base.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        validate_profile(data, path.stem)
        profiles[data["id"]] = data
    return profiles


def match_profiles(
    root: str, profiles: dict[str, dict], file_cap: int = 50_000, sample_cap: int = 5
):
    """Walk root, fnmatch basenames against each profile's globs.

    Returns (matched, samples, warnings) where:
      matched  = [{id, hits, confidence}] sorted by hits desc (confidence normalized over total hits)
      samples  = {profile_id: [abs paths]} (capped) for the encoding smoke-check
      warnings = ["file_cap_reached"] when the walk stopped at the cap
    """
    hits = {pid: 0 for pid in profiles}
    samples: dict[str, list[str]] = {pid: [] for pid in profiles}
    warnings: list[str] = []
    count = 0
    capped = False
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            count += 1
            if count > file_cap:
                capped = True
                break
            for pid, p in profiles.items():
                globs = p["detection"]["globs"]
                if globs and any(fnmatch.fnmatch(fn, g) for g in globs):
                    hits[pid] += 1
                    if len(samples[pid]) < sample_cap:
                        samples[pid].append(os.path.join(dirpath, fn))
        if capped:
            break
    if capped:
        warnings.append("file_cap_reached")
    total = sum(hits.values())
    matched = [
        {"id": pid, "hits": h, "confidence": round(h / total, 4) if total else 0.0}
        for pid, h in hits.items()
        if h > 0
    ]
    matched.sort(key=lambda m: (-m["hits"], m["id"]))
    return matched, samples, warnings


# Files that mark a directory as a self-contained component / service root (Phase D).
_MANIFEST_MARKERS = {
    "package.json", "go.mod", "pom.xml", "build.gradle", "composer.json",
    "pyproject.toml", "Cargo.toml", "Gemfile",
}

# Role classification (Phase D2, RT2-F4b). Stack profiles are intentionally coarse — one
# `web-js-ts` profile matches a Nuxt frontend AND a Laravel backend alike — so the build-unit
# *role* cannot be read from the profile id. It is read from the dependency manifest CONTENT
# instead. Roles: "frontend" (browser/SPA/SSR build unit) | "backend" (server-side app) |
# "service" (recognized build unit, role indeterminate). The role is what lets the detector tell
# a co-deployed FE+BE product apart from a fleet of peer microservices (the `group` signal below).
_FRONTEND_DEP_MARKERS = (
    "nuxt", "next", "@angular/core", "@angular/cli", "react-dom", "react-native",
    "vue", "@vue/", "svelte", "@sveltejs/", "gatsby", "expo", "solid-js", "@remix-run/",
    "vite", "@vitejs/",
)
_BACKEND_DEP_MARKERS = (
    "express", "@nestjs/", "koa", "fastify", "@hapi/", "hapi", "apollo-server",
    "@adonisjs/", "sails", "restify", "@loopback/", "@feathersjs/",
)
# Python web frameworks → backend (read from pyproject.toml / requirements*.txt content).
_PY_BACKEND_MARKERS = ("django", "flask", "fastapi", "starlette", "tornado", "sanic", "aiohttp")

# Conventional monorepo *container* directory names. A wrapper with one of these basenames holds
# N independent build units by convention (e.g. `services/{auth,billing}`), so it is NEVER treated
# as a single-product group — even when its children happen to have complementary roles.
_CONTAINER_DIRS = {
    "apps", "packages", "services", "libs", "lib", "modules", "cmd", "pkg",
    "src", "examples", "tests", "test", "components", "projects",
}


def _read_json(path: str) -> dict | None:
    """Best-effort JSON read; None on any error (missing / malformed / unreadable)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def classify_role(comp_dir: str) -> str:
    """Map a component directory's manifest CONTENT to "frontend" | "backend" | "service".

    Precedence is deliberate: a server-side language manifest (composer/go/pom/gradle/Gemfile, or
    a web-framework pyproject) marks the unit "backend" even when a `package.json` is co-located —
    that package.json is almost always an asset-build helper (e.g. Laravel Mix / Vite for Blade),
    not a standalone frontend. A standalone `package.json` is then classified by its dependencies.
    """
    j = lambda *p: os.path.join(comp_dir, *p)  # noqa: E731
    # 1. Server-side language manifests → backend (these out-rank a co-located package.json).
    if os.path.exists(j("composer.json")):
        return "backend"
    if any(os.path.exists(j(m)) for m in ("go.mod", "pom.xml", "build.gradle", "Gemfile")):
        return "backend"
    for pyf in ("pyproject.toml", "requirements.txt", "requirements.in", "Pipfile"):
        if os.path.exists(j(pyf)):
            try:
                with open(j(pyf), encoding="utf-8", errors="ignore") as f:
                    text = f.read().lower()
            except OSError:
                text = ""
            return "backend" if any(m in text for m in _PY_BACKEND_MARKERS) else "service"
    # 2. JS/TS package.json → classify by declared dependencies.
    pkg = _read_json(j("package.json"))
    if pkg is not None:
        deps = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            d = pkg.get(key)
            if isinstance(d, dict):
                deps.update(d)
        dep_keys = [k.lower() for k in deps]
        if any(any(m in k for m in _FRONTEND_DEP_MARKERS) for k in dep_keys):
            return "frontend"
        if any(any(m in k for m in _BACKEND_DEP_MARKERS) for k in dep_keys):
            return "backend"
        return "service"
    # 3. Rust / other recognized build unit, role indeterminate.
    return "service"


def _parent_rel(rel: str) -> str:
    """Repo-relative parent dir of a `/`-joined relative path; `"."` for a top-level entry."""
    return "." if "/" not in rel else rel.rsplit("/", 1)[0]


def _assign_groups(components: list[dict]) -> None:
    """Tag co-deployed FE+BE build units with a shared `group` key (in place).

    A `group` is the relative path of a wrapper directory that (a) is below the scan root (not
    `"."`), (b) is NOT a conventional monorepo container (`_CONTAINER_DIRS`), and (c) directly
    holds ≥2 component roots whose roles are COMPLEMENTARY — at least one "frontend" AND at least
    one "backend". That is the signature of "one product = FE + BE in one named folder, no root
    manifest" (e.g. `ssv-wsm-employee/{frontend,backend}`), as opposed to peer microservices under
    `services/`. Members of such a wrapper share `group=<wrapper path>`; every other component
    keeps `group=None`. The grouping is ADVISORY — it tells the orchestrator these units are one
    product (their FE→BE relationship is an internal contract, not a cross-service edge), it does
    not itself merge them.
    """
    by_parent: dict[str, list[dict]] = {}
    for c in components:
        c.setdefault("group", None)
        if c["path"] == ".":
            continue
        par = _parent_rel(c["path"])
        if par == "." or par.rsplit("/", 1)[-1] in _CONTAINER_DIRS:
            continue
        by_parent.setdefault(par, []).append(c)
    for par, members in by_parent.items():
        if len(members) < 2:
            continue
        roles = {m["role"] for m in members}
        if "frontend" in roles and "backend" in roles:
            for m in members:
                m["group"] = par


def _is_under_shared(abspath: str, shared_abspaths: set[str]) -> bool:
    """True if `abspath` IS, or is nested under, any resolved shared-layer dir."""
    norm = os.path.normpath(abspath)
    for s in shared_abspaths:
        if norm == s or norm.startswith(s + os.sep):
            return True
    return False


def find_components(
    root: str,
    profiles: dict[str, dict],
    file_cap: int = 50_000,
    *,
    boundary_globs: list[str] | None = None,
    shared_abspaths: set[str] | None = None,
    warnings: list[str] | None = None,
) -> list[dict]:
    """Discover sub-repo components in a monorepo (Phase D, RT2-F4 — ADDITIVE).

    A component root is the SHALLOWEST directory (at or below `root`) that directly contains a
    manifest marker OR a profile detection-glob file; nested markers under a claimed root are not
    re-listed.  A sub-dir that contains docs/.rebuild-state.json (was previously rebuilt
    standalone) is claimed as a REUSED root BEFORE the marker check and stops descent.

    Returns `[{path, profile, role, group}]` sorted by path (path is repo-relative,
    `/`-joined; the project root itself is `"."`). `role` is classified from manifest content
    (`classify_role`); `group` links co-deployed FE+BE products (`_assign_groups`). Each
    component's profile is the highest-hit match within its own subtree. Discovery-only — never
    generates. Bounded by `file_cap`.

    Reused entries additionally carry: {status:"reused", docs_path, source_sha, is_git_root}.
    They are NEVER assigned a group (they already represent a whole product).

    Multi-executable boundary control (Phase 02 — keyword-only, default-None = legacy behavior):
      * `boundary_globs`: when given, ONLY these basename globs mark a component root (the
        `component_profile`'s `component_boundary_globs`, e.g. `*.dpr`) — a dir with only `.pas`
        and no executable is no longer claimed. None → all profiles' `detection.globs` (legacy).
      * `shared_abspaths`: resolved abspaths of shared-layer dirs (Common/DB). Any dir at/under one
        is excluded from claiming BEFORE the marker check and descent stops there — this is what
        defeats the oracle co-detection of `DB/` (Layer 1). On suppression a `shared_layer_excluded`
        warning is appended to `warnings` (Finding 4 — a real module named `DB`/`Common` is not
        silently dropped). None → no exclusion (legacy).
    """
    comp_roots: list[str] = []
    # Side-map: rel → provenance dict for reused roots
    reused_map: dict[str, dict] = {}
    shared = shared_abspaths or set()
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        count += len(filenames)
        if count > file_cap:
            break

        rel = os.path.relpath(dirpath, root)
        rel = "." if rel == "." else rel.replace(os.sep, "/")

        # Layer 1 — shared-layer exclusion (BEFORE reused + marker checks). A dir that is, or is
        # under, a resolved shared-layer dir is never its own component; stop descent so its
        # subtree (e.g. DB/SP/POS with oracle .pks/.pkb) cannot be co-claimed by another profile.
        if shared and _is_under_shared(os.path.abspath(dirpath), shared):
            # Warn once, at the shared root itself (not every nested dir — descent stops here).
            if warnings is not None and os.path.normpath(os.path.abspath(dirpath)) in shared:
                warnings.append(
                    f"shared_layer_excluded: {rel!r} (matches shared_layer_dirs; "
                    f"if this is a component, rename it or use --mono)"
                )
            dirnames[:] = []  # do not descend into a shared layer
            continue

        # Skip if an ancestor is already claimed (normal or reused).
        if any(rel == c or rel.startswith(c + "/") for c in comp_roots if c != "."):
            continue

        # REUSED-ROOT probe (highest priority — checked BEFORE manifest markers).
        if is_reused_root(dirpath, root):
            prov = read_reused_provenance(dirpath)
            prov["docs_path"] = (rel + "/docs") if rel != "." else "docs"
            comp_roots.append(rel)
            reused_map[rel] = prov
            dirnames[:] = []  # stop descent — the whole sub-tree is one unit
            continue

        has_marker = any(fn in _MANIFEST_MARKERS for fn in filenames)
        if not has_marker:
            # Layer 2 — boundary-glob source: executables only when boundary_globs given.
            if boundary_globs:
                has_marker = any(
                    fnmatch.fnmatch(fn, g) for fn in filenames for g in boundary_globs
                )
            else:
                for fn in filenames:
                    if any(
                        p["detection"]["globs"] and fnmatch.fnmatch(fn, g)
                        for p in profiles.values() for g in p["detection"]["globs"]
                    ):
                        has_marker = True
                        break
        if has_marker:
            comp_roots.append(rel)
            dirnames[:] = []  # do not descend into a claimed component

    components: list[dict] = []
    for cr in sorted(comp_roots):
        sub = root if cr == "." else os.path.join(root, *cr.split("/"))
        if cr in reused_map:
            prov = reused_map[cr]
            components.append({
                "path": cr,
                "profile": None,
                "role": classify_role(sub),
                "group": None,
                "status": "reused",
                "docs_path": prov["docs_path"],
                "source_sha": prov["source_sha"],
                "is_git_root": prov["is_git_root"],
            })
        else:
            matched, _, _ = match_profiles(sub, profiles, file_cap=file_cap)
            components.append({
                "path": cr,
                "profile": matched[0]["id"] if matched else None,
                "role": classify_role(sub),
                "group": None,
            })
    # _assign_groups must skip reused nodes (they have no group candidacy).
    _assign_groups([c for c in components if c.get("status") != "reused"])
    return components


# Shared-layer kind map (Phase 03): basename → extractor route. Default "source".
_SHARED_KIND = {"DB": "db"}


def shared_layers(root: str, profile: dict) -> tuple[list[dict], set[str]]:
    """Discover the shared-layer dirs declared by `profile.shared_layer_dirs` (Phase 03).

    Matches dir BASENAMES at any depth (KISS — no fnmatch). Returns:
      entries  = [{path (repo-relative, `/`-joined), kind ("db"|"source"), label (basename)}]
                 sorted by path — the manifest SIDECAR shape (`.rebuild-components-shared.json`).
      abspaths = normalized absolute paths — fed to `find_components(shared_abspaths=...)`.
    Profile without `shared_layer_dirs` → ([], set()).
    """
    basenames = set(profile.get("shared_layer_dirs") or [])
    entries: list[dict] = []
    abspaths: set[str] = set()
    seen: set[str] = set()
    if not basenames:
        return entries, abspaths
    for dirpath, dirnames, _ in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for d in sorted(dirnames):
            if d in basenames:
                ab = os.path.normpath(os.path.join(dirpath, d))
                rel = os.path.relpath(ab, root).replace(os.sep, "/")
                if rel in seen:
                    continue
                seen.add(rel)
                abspaths.add(ab)
                entries.append({"path": rel, "kind": _SHARED_KIND.get(d, "source"), "label": d})
    entries.sort(key=lambda e: e["path"])
    return entries, abspaths


def resolve_component_profile(
    root: str,
    matched: list[dict],
    profiles: dict[str, dict],
    file_cap: int = 50_000,
    pinned: str | None = None,
) -> tuple[str | None, list[str]]:
    """Resolve the COMPONENT-owning profile (Phase 03 — Finding 2 fix).

    `match_profiles` ranks by raw glob-hit count, so a DB-heavy repo can make `oracle-plsql`
    out-hit `delphi-vcl` and become the global `recommended` — which would kill auto-switch and
    the shared exclusion. So auto-switch + `shared_layer_dirs` are keyed NOT on `recommended` but
    on the **component_profile**: among matched profiles, the one whose
    `module_layout == "one-spec-per-unit"` AND that actually claims ≥2 component roots via its
    `component_boundary_globs`.

    Returns (component_profile_id | None, warnings). `pinned` (`--profile <id>`) forces the answer
    when it names a one-spec-per-unit profile. Two candidates tie → None + an ambiguity warning
    (the orchestrator must disambiguate with `--profile`).
    """
    warnings: list[str] = []
    if pinned is not None:
        p = profiles.get(pinned)
        if p is not None and p.get("module_layout") == "one-spec-per-unit":
            return pinned, warnings
        # Pinned profile isn't a one-spec-per-unit owner → no component_profile (single/mono path).
        return None, warnings

    candidates: list[str] = []
    for m in matched:
        pid = m["id"]
        p = profiles.get(pid)
        if not p or p.get("module_layout") != "one-spec-per-unit":
            continue
        boundary = p.get("component_boundary_globs")
        _, shared_abs = shared_layers(root, p)
        comps = find_components(
            root, profiles, file_cap=file_cap,
            boundary_globs=boundary, shared_abspaths=shared_abs,
        )
        roots = sum(1 for c in comps if c["path"] != ".")
        if roots >= 2:
            candidates.append(pid)
    if not candidates:
        return None, warnings
    if len(candidates) > 1:
        warnings.append(
            f"component_profile_ambiguous: {candidates!r} — multiple one-spec-per-unit profiles "
            f"claim ≥2 roots; pin one with --profile <id>"
        )
        return None, warnings
    return candidates[0], warnings


def collapse_groups(
    components: list[dict], root: str, profiles: dict[str, dict], file_cap: int = 50_000
) -> list[dict]:
    """Fold each `group`'s member build-units into ONE fullstack component (Product-group gate).

    The orchestrator calls this when the user (or `--auto`) elects to treat a co-deployed FE+BE
    product as a single component: every component sharing `group=<wrapper>` is replaced by one
    entry `{path: <wrapper>, profile: <re-matched over the wrapper subtree>, role: "fullstack",
    group: None}`, so a subsequent `--batch`/`--root <wrapper>` rebuild keeps the FE→BE contract in
    one spec. Ungrouped components pass through unchanged. Order is preserved (each group lands at
    its first member's position). Pure transform — no filesystem writes.
    """
    out: list[dict] = []
    seen_groups: set[str] = set()
    for c in components:
        g = c.get("group")
        if not g:
            out.append(c)
            continue
        if g in seen_groups:
            continue
        seen_groups.add(g)
        sub = root if g == "." else os.path.join(root, *g.split("/"))
        matched, _, _ = match_profiles(sub, profiles, file_cap=file_cap)
        out.append({
            "path": g,
            "profile": matched[0]["id"] if matched else c.get("profile"),
            "role": "fullstack",
            "group": None,
        })
    return out


def smoke_check_encoding(sample_paths: list[str], encoding: str, max_bytes: int = 5_000_000) -> list[str]:
    """Round-trip decode→encode a few sample files. Returns ['encoding_unverified'] on failure."""
    for path in sample_paths:
        try:
            with open(path, "rb") as f:
                raw = f.read(max_bytes)
            raw.decode(encoding).encode(encoding)
        except (UnicodeDecodeError, UnicodeEncodeError, LookupError, OSError):
            return ["encoding_unverified"]
    return []
