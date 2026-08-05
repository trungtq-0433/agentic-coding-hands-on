#!/usr/bin/env python3
"""Detect the stack-profile(s) of a project root (Phase A).

Scans the project root, matches detection globs of every kit profile, and emits an advisory
JSON report on stdout. Exit code is ALWAYS 0 — detection never aborts the pipeline; the
ask-don't-abort decision lives in the orchestrator (SKILL.md Preflight).

Output contract: see references/stack-profiles/_schema.md § detect_stack_profile.py output.

Stdlib only. Profile load/match/validate live in _stack_profile_lib.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from _stack_profile_lib import (
    SCHEMA_VERSION,
    classify_role,
    collapse_groups,
    find_components,
    load_profiles,
    match_profiles,
    resolve_component_profile,
    shared_layers,
    smoke_check_encoding,
)
from _path_lib import component_name
import _content_sniff_lib

# v22.1.0 (Phase 08, Track D): additive `ui_sniff` key(s) in detect()'s return dict.
# SCHEMA_VERSION is the single source of truth in _stack_profile_lib.py -- imported, not
# shadowed, so every consumer of either module sees the same value.

# Named + tunable (Risk Assessment): sniff triggers when the top match's confidence is
# BELOW this threshold. v1 default is 0.0 -- i.e. sniff ONLY on a genuinely empty match
# (`matched == []`), never on a low-but-nonzero confidence match yet.
_UI_SNIFF_CONFIDENCE_THRESHOLD = 0.0


def _safe_sniff(path: str, file_cap: int) -> dict:
    """Run `sniff_ui`, guarded: a sniff failure must never crash detection -- detection
    stays advisory/exit-0 even when the fallback sniff pass itself errors out."""
    try:
        return _content_sniff_lib.sniff_ui(path, file_cap)
    except Exception as e:  # noqa: BLE001 -- sniff failure must degrade, never propagate
        return {"tier": 0, "error": str(e)}


def detect(
    root: str,
    file_cap: int,
    sample_cap: int,
    collapse: bool = False,
    mono: bool = False,
    pinned_profile: str | None = None,
) -> dict:
    abs_root = os.path.realpath(os.path.abspath(root))
    profiles = load_profiles()
    if pinned_profile is not None and pinned_profile not in profiles:
        raise ValueError(
            f"--profile {pinned_profile!r} is not a known stack-profile "
            f"(known: {sorted(profiles)})"
        )
    matched, samples, warnings = match_profiles(
        abs_root, profiles, file_cap=file_cap, sample_cap=sample_cap
    )

    # recommended is the STABLE single Phase-A contract (highest hits); --profile pins it.
    recommended = pinned_profile or (matched[0]["id"] if matched else None)
    confidence = (
        next((m["confidence"] for m in matched if m["id"] == recommended), 0.0)
        if recommended else 0.0
    )
    encoding = None
    heading = None
    if recommended:
        prof = profiles[recommended]
        encoding = prof["source_encoding"]["primary"]
        heading = prof["detected_language_heading"]
        warnings += smoke_check_encoding(samples.get(recommended, []), encoding)

    # Component-owning profile (Phase 03 — Finding 2): auto-switch + shared exclusion are keyed on
    # the one-spec-per-unit profile that claims ≥2 roots, NOT the global hit-count `recommended`.
    component_profile, cp_warnings = resolve_component_profile(
        abs_root, matched, profiles, file_cap=file_cap, pinned=pinned_profile
    )
    warnings += cp_warnings

    # Boundary globs + shared-layer dirs are resolved from the COMPONENT profile (or none).
    boundary_globs = None
    shared_abspaths: set[str] | None = None
    shared: list[dict] = []
    if component_profile:
        cp = profiles[component_profile]
        boundary_globs = cp.get("component_boundary_globs")
        shared, shared_abspaths = shared_layers(abs_root, cp)

    # ADDITIVE (RT2-F4): components[] per sub-repo, alongside the stable single recommended_profile.
    # A flat/single repo → one entry mapping the top-level recommendation. Caller (Phase A preflight)
    # reads recommended_profile and is unaffected; Phase D synthesis reads components[].
    components = find_components(
        abs_root, profiles, file_cap=file_cap,
        boundary_globs=boundary_globs, shared_abspaths=shared_abspaths, warnings=warnings,
    )
    if not components:
        components = [{
            "path": ".", "profile": recommended,
            "role": classify_role(abs_root), "group": None,
        }]

    # Product-group gate (RT2-F4b): --collapse-groups folds each FE+BE group into one fullstack
    # component BEFORE the collision check, so a subsequent --batch keeps the FE→BE contract in one spec.
    if collapse:
        components = collapse_groups(components, abs_root, profiles, file_cap=file_cap)

    # Preflight collision check (RT2-F14): two entries must not derive the same <name>.
    names: dict[str, str] = {}
    for c in components:
        nm = component_name(c["path"]) or "."
        if nm in names and names[nm] != c["path"]:
            warnings.append(f"component_name_collision: {names[nm]!r} and {c['path']!r} → {nm!r}")
        names[nm] = c["path"]

    # Product-group advisory (RT2-F4b): co-deployed FE+BE build units under one named wrapper are
    # ONE product, not peer microservices. Surface so the orchestrator can offer to treat the group
    # as a single component and keep the FE→BE contract in one spec (never a cross-service edge).
    groups: dict[str, list[dict]] = {}
    for c in components:
        g = c.get("group")
        if g:
            groups.setdefault(g, []).append(c)
    for g in sorted(groups):
        members = ", ".join(f"{m['path']} ({m['role']})" for m in groups[g])
        warnings.append(
            f"component_group: {g!r} → [{members}] — co-deployed frontend+backend, likely one "
            f"product; consider treating the group as a single component (FE→BE is an internal "
            f"contract, not a cross-service edge)"
        )

    # Reused-root advisory (Phase 05): surface reused components so the orchestrator
    # can trigger the reuse/rebuild/exclude gate (Phase 06).
    for c in components:
        if c.get("status") == "reused":
            warnings.append(
                f"component_reused: {c['path']!r} — has docs/.rebuild-state.json; "
                f"orchestrator must choose reuse/rebuild/exclude before --batch"
            )

    # Content-sniff fallback pass (Phase 08, Track D): a signal source when structural profile
    # matching found nothing. Perf-critical: zero scan cost on a recognized stack, so the branch
    # below only ever calls `sniff_ui`/`_safe_sniff` when there is something to compensate for.
    top_confidence = matched[0]["confidence"] if matched else 0.0
    if not matched or top_confidence < _UI_SNIFF_CONFIDENCE_THRESHOLD:
        # Root-level miss: sniff the whole tree once. This walk already covers every
        # component under it, so the per-component branch below is skipped entirely --
        # never double-scan the same files via both root AND per-component sniffing.
        ui_sniff = _safe_sniff(abs_root, file_cap)
    else:
        # Root matched -- stay zero-cost by default. [fix 12] A masked unrecognized
        # component can still hide inside an otherwise-recognized monorepo (e.g. web +
        # Oracle siblings with one unclassified dir): sniff ONLY that component's own
        # path, not the whole root again. Reused components (status "reused") are
        # excluded -- they carry `profile: None` too, but they are previously-documented
        # roots (docs/.rebuild-state.json), not unrecognized tech; sniffing them would be
        # wasted work and a category error for Track D's purpose.
        ui_sniff = {"tier": 0}
        for c in components:
            if c.get("profile") is None and c.get("status") != "reused":
                sub = abs_root if c["path"] == "." else os.path.join(abs_root, *c["path"].split("/"))
                c["ui_sniff"] = _safe_sniff(sub, file_cap)

    # Auto-switch recommendation (Phase 03). A plain single run that detects a component_profile
    # SHOULD enter the --emit-manifest→--batch→--aggregate loop instead of the single-repo path.
    # Predicate: component_profile exists AND --mono not set. (The orchestrator additionally
    # bypasses when the user explicitly scoped `--root <subrepo>`; that never reaches here.)
    # Detection-only — detect() REPORTS; the orchestrator (SKILL.md preflight) acts on it.
    n_components = sum(1 for c in components if c.get("path") != ".")
    auto_switch = bool(component_profile) and not mono
    if mono and component_profile:
        auto_switch_reason = "--mono override"
    elif auto_switch:
        auto_switch_reason = (
            f"{n_components} components, component_profile={component_profile} one-spec-per-unit"
        )
    else:
        auto_switch_reason = "no component_profile (single/monolithic repo)"

    return {
        "schema_version": SCHEMA_VERSION,
        "root": abs_root,
        "matched": matched,
        "recommended_profile": recommended,
        "confidence": confidence,
        "encoding": encoding,
        "detected_language_heading": heading,
        "components": components,
        "component_profile": component_profile,
        "auto_switch": auto_switch,
        "auto_switch_reason": auto_switch_reason,
        "shared": shared,
        "ui_sniff": ui_sniff,
        "warnings": warnings,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Detect stack-profile(s) of a project root.")
    p.add_argument("--root", default=".", help="Project root to scan (default: CWD)")
    p.add_argument("--file-cap", type=int, default=50_000, help="Max files to walk (RT-F6 DoS cap)")
    p.add_argument("--sample-cap", type=int, default=5, help="Max sample files per profile for encoding smoke-check")
    p.add_argument("--emit-manifest", action="store_true",
                   help="Write the multi-component run-plan (.rebuild-components.json) from components[] (Phase D)")
    p.add_argument("--collapse-groups", action="store_true",
                   help="Fold each co-deployed FE+BE group into one 'fullstack' component (Product-group gate, RT2-F4b)")
    p.add_argument("--mono", action="store_true",
                   help="Force single monolithic component: auto_switch=false even when ≥2 components detected (Phase 03 escape hatch)")
    p.add_argument("--profile", default=None,
                   help="Pin the authoritative stack-profile id (disambiguates Delphi+Oracle co-detection); also sets component_profile when it is a one-spec-per-unit owner (Phase 03)")
    p.add_argument("--manifest", default=None,
                   help="Manifest path (default: <root>/.rebuild-components.json). Used by --emit-manifest/--batch/--aggregate.")
    args = p.parse_args()
    try:
        result = detect(
            args.root, args.file_cap, args.sample_cap,
            collapse=args.collapse_groups, mono=args.mono, pinned_profile=args.profile,
        )
    except (ValueError, json.JSONDecodeError, OSError) as e:
        # Profile-load failure (e.g. bad/untrusted profile) is the one fatal case: a corrupt
        # allowlist/schema must not silently degrade. Surface on stderr, still exit non-zero=2.
        print(f"error: stack-profile detection failed: {e}", file=sys.stderr)
        sys.exit(2)

    if args.emit_manifest:
        # Run-plan write (atomic + lock + collision check) lives in _components_manifest_lib (Phase D).
        # The component manifest stays a JSON ARRAY; shared layers go in a SIDECAR (Phase 03 Finding 1).
        from _components_manifest_lib import (  # lazy: only needed for this mode
            emit_manifest, emit_shared_sidecar, shared_sidecar_path,
        )
        manifest_path = args.manifest or os.path.join(result["root"], ".rebuild-components.json")
        emit_manifest(manifest_path, result["components"], result["root"])
        sidecar_path = shared_sidecar_path(manifest_path)
        emit_shared_sidecar(sidecar_path, result["shared"], result["root"])
        print(json.dumps({"status": "manifest_emitted", "manifest": manifest_path,
                          "shared_sidecar": sidecar_path,
                          "components": len(result["components"]),
                          "shared": len(result["shared"])}, indent=2))
        sys.exit(0)

    print(json.dumps(result, indent=2, sort_keys=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
