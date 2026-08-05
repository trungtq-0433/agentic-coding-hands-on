#!/usr/bin/env python3
"""Cascade-aware incremental planner for rebuild-spec.

Decision oracle: reads state, git diff, scout-report → emits .incremental-plan.json.
Does NOT dispatch tasks — pipeline.md reads the payload and gates TaskCreate calls.

Exit codes: 0 = decision emitted, 1 = hard halt (prereqs missing), 2 = arg error.
Stdlib only. Authority: ../references/incremental-state-schema.md.
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Wave subject strings — must match pipeline.md verbatim.
# [RT-C6] Wave6.8 (process-flow) and Wave6.9 (glossary) removed — these are now
# separate standalone passes (--flows and --glossary). Their presence here caused
# the cascade planner to include them in core incremental runs, which is wrong.
CORE_ARTIFACT_TO_WAVE_SUBJECT: dict[str, str] = {
    "route-list.md": "Wave1: route-list",
    "data-model.md": "Wave1: data-model",
    "screen-list.md": "Wave2: screen-list + screen-flow",
    "screen-flow.md": "Wave2: screen-list + screen-flow",
    "behavior-logic.md": "Wave2: behavior-logic",
    "api-map.md": "Wave2.9: api-map",
    "permissions.md": "Wave3: permissions",
    "permissions-matrix.md": "Wave3: permissions",
    "user-stories.md": "Wave4: user-stories",
    "feature-list.md": "Wave5: feature-list",
}

# [RT-C6] Wave6.8 and Wave6.9 removed — they are now --flows and --glossary passes.
# api-contracts (AC.1; historical numbering Wave6.87) is a standalone pass (--api-contracts) — NOT in core cascade.
WAVE_ORDER = [
    "Wave1: route-list",
    "Wave1: data-model",
    "Wave2: screen-list + screen-flow",
    "Wave2: behavior-logic",
    "Wave2.9: api-map",
    "Wave3: permissions",
    "Wave4: user-stories",
    "Wave5: feature-list",
]

# Maps artifact filename → canonical path relative to docs_root (v4 layered layout).
# Used for OOB detection, hydration, and doc_shas snapshot.
ARTIFACT_LAYERED: dict[str, str] = {
    "route-list.md": "generated/route-list.md",
    "api-map.md": "generated/api-map.md",
    "api-contracts.md": "generated/api-contracts.md",
    "data-model.md": "generated/entities.md",
    "screen-list.md": "generated/screen-list.md",
    "screen-flow.md": "generated/screen-flow.md",
    "behavior-logic.md": "generated/behavior-logic.md",
    "permissions.md": "system/permissions.md",
    "permissions-matrix.md": "generated/permissions-matrix.md",
    "user-stories.md": "generated/user-stories.md",
    "feature-list.md": "generated/feature-list.md",
    "glossary.md": "system/glossary.md",
    "business-rules.md": "system/business-rules.md",
    "system-overview.md": "system/overview.md",
    "architecture.md": "system/architecture.md",
}

MANIFEST_FILES = frozenset({
    "package.json", "composer.json", "Gemfile", "pyproject.toml",
    "pom.xml", "build.gradle", "go.mod", "Cargo.toml",
})

# Cascade chains per file type (researcher-03 Q1 table).
# [RT-C6] Wave6.8: process-flow and Wave6.9: glossary removed from all chains.
CASCADE_CHAINS: dict[str, list[str]] = {
    "route": [
        "Wave1: route-list",
        "Wave2: screen-list + screen-flow",
        "Wave2: behavior-logic",
        "Wave2.9: api-map",
        "Wave3: permissions",
        "Wave4: user-stories",
        "Wave5: feature-list",
    ],
    "model": [
        "Wave1: data-model",
        "Wave2: screen-list + screen-flow",
        "Wave2: behavior-logic",
        "Wave2.9: api-map",
        "Wave3: permissions",
        "Wave4: user-stories",
        "Wave5: feature-list",
    ],
    "screen": [
        "Wave2: screen-list + screen-flow",
        "Wave2: behavior-logic",
        "Wave2.9: api-map",
        "Wave3: permissions",
        "Wave4: user-stories",
        "Wave5: feature-list",
    ],
    "background": [
        "Wave2: behavior-logic",
        "Wave2.9: api-map",
        "Wave3: permissions",
        "Wave4: user-stories",
        "Wave5: feature-list",
    ],
    "permission": [
        "Wave3: permissions",
        "Wave4: user-stories",
        "Wave5: feature-list",
    ],
}

# Artifacts whose regeneration marks downstream areas as stale (V7).
# Used to compute stale_features / stale_flows / stale_glossary booleans.
_DATA_MODEL_WAVES = {"Wave1: data-model"}
_SCREEN_FLOW_BEHAVIOR_WAVES = {
    "Wave2: screen-list + screen-flow",
    "Wave2: behavior-logic",
}


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _git_diff(since: str, head: str = "HEAD") -> list[tuple[str, str, str | None]]:
    """Return [(status, path, new_path_or_None)] from git diff."""
    r = subprocess.run(
        ["git", "diff", "--name-status", "--diff-filter=AMRD", "-M", f"{since}..{head}"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    rows: list[tuple[str, str, str | None]] = []
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows.append((parts[0][0], parts[1], parts[2]))
        elif len(parts) == 2:
            rows.append((parts[0][0], parts[1], None))
    return rows


def _git_sha_reachable(sha: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, timeout=10, check=False,
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _git_head_sha() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5, check=True,
    )
    return r.stdout.strip()


def _parse_scout_inventory(scout_path: Path) -> dict[str, str]:
    """Parse scout-report.md File Inventory → {path: type}."""
    inventory: dict[str, str] = {}
    if not scout_path.is_file():
        return inventory
    in_section = False
    found_section = False
    for line in scout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## File Inventory"):
            in_section = True
            found_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and "\t" in line:
            parts = line.split("\t", 1)
            if len(parts) == 2:
                inventory[parts[0].strip()] = parts[1].strip()
    if found_section and not inventory:
        print("[WARN] ## File Inventory section found but yielded 0 entries", file=sys.stderr)
    return inventory


def _classify_files(
    diff_rows: list[tuple[str, str, str | None]],
    inventory: dict[str, str],
) -> tuple[dict[str, list[str]], list[str]]:
    """Classify changed files by type. Returns (type_to_paths, unowned_new)."""
    classified: dict[str, list[str]] = {}
    unowned: list[str] = []
    for status, path, new_path in diff_rows:
        effective = new_path or path
        ftype = inventory.get(effective, "other")
        if status in ("A", "R") and effective not in inventory:
            unowned.append(effective)
        classified.setdefault(ftype, []).append(effective)
    return classified, unowned


def _cascade(types_present: set[str]) -> tuple[list[str], str | None]:
    """Compute affected_waves + cascade_chain description. Returns (waves, chain_desc)."""
    if "config" in types_present:
        return [], "FULL (config changed)"

    all_waves: list[str] = []
    chain_parts: list[str] = []
    for ftype in ["route", "model", "screen", "background", "permission"]:
        if ftype in types_present:
            chain = CASCADE_CHAINS[ftype]
            all_waves.extend(chain)
            chain_parts.append(f"{ftype} → {' → '.join(chain)}")

    seen: set[str] = set()
    ordered: list[str] = []
    for w in WAVE_ORDER:
        if w in all_waves and w not in seen:
            seen.add(w)
            ordered.append(w)

    chain_desc = "; ".join(chain_parts) if chain_parts else None
    return ordered, chain_desc


def _resolve_fcodes(
    reverse_index: dict, changed_paths: list[str],
    w5_reran: bool, canonical_path: Path,
) -> list[str]:
    if w5_reran:
        canonical = _load_json(canonical_path)
        if canonical and "features" in canonical:
            return sorted({f["fcode"] for f in canonical["features"]})
        return []
    index = reverse_index.get("index", {})
    fcodes: set[str] = set()
    for p in changed_paths:
        if p in index:
            fcodes.update(index[p])
    return sorted(fcodes)


def _detect_oob(
    state: dict, docs_root: Path, affected_waves: list[str],
) -> list[str]:
    """Compare current doc SHAs (layered paths) to state. Warn on out-of-band edits for non-affected artifacts."""
    warnings: list[str] = []
    old_shas = state.get("doc_shas", {})
    if not old_shas:
        return warnings
    for fname, old_sha in old_shas.items():
        subject = CORE_ARTIFACT_TO_WAVE_SUBJECT.get(fname)
        if subject and subject in affected_waves:
            continue
        rel = ARTIFACT_LAYERED.get(fname)
        fpath = (docs_root / rel) if rel else (docs_root / fname)
        if fpath.is_file():
            current = hashlib.sha256(fpath.read_bytes()).hexdigest()
            if current != old_sha:
                warnings.append(f"[OUT_OF_BAND_EDIT] {fname}")
    return warnings


def _detect_confidence_report_missing(docs_root: Path) -> list[str]:
    """A1 (v25.2.0) advisory scan: primary artifact on disk, its `confidence-report_<stem>.md`
    companion absent (pre-A1 corpus, or a prior best-effort write failure by
    derive_confidence_report.py).

    Strictly non-gating: unlike `_detect_oob`, these warnings are printed only — they are
    NEVER folded into the payload and NEVER trigger a fallback-to-full. See
    references/confidence-report-contract.md § Reconcile-time advisory.
    """
    warnings: list[str] = []
    for rel in ARTIFACT_LAYERED.values():
        fpath = docs_root / rel
        if fpath.is_file() and not (fpath.parent / f"confidence-report_{fpath.stem}.md").is_file():
            warnings.append(f"[CONFIDENCE_REPORT_MISSING] {rel}")
    for glob_pat, companion_name in (("features/*/technical-spec.md", "confidence-report_technical-spec.md"),
                                      ("screens/*/spec.md", "confidence-report_spec.md")):
        for fpath in sorted(docs_root.glob(glob_pat)):
            if not (fpath.parent / companion_name).is_file():
                warnings.append(f"[CONFIDENCE_REPORT_MISSING] {fpath.relative_to(docs_root)}")
    return warnings


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def _compute_stale_flags(
    affected_waves: list[str],
    affected_fcodes: list[str],
    reverse_index: dict,
    all_changed: list[str],
) -> tuple[bool, bool, bool]:
    """Compute (stale_features, stale_flows, stale_glossary) for V7 selective staleness.

    stale_features: ≥1 changed source file maps to an F### via the reverse-index.
    stale_flows: stale_features OR data-model/screen-flow/behavior-logic re-generated.
    stale_glossary: stale_features OR data-model re-generated.
    """
    # stale_features: any changed source touches a known fcode
    ri_index = reverse_index.get("index", {})
    stale_features = any(p in ri_index for p in all_changed)

    # Also stale if W5 reran (affected_fcodes would be non-empty from canonical list)
    if affected_fcodes:
        stale_features = True

    # stale_flows: stale_features OR screen-flow/behavior-logic/data-model wave in cascade
    affected_wave_set = set(affected_waves)
    data_model_reran = bool(affected_wave_set & _DATA_MODEL_WAVES)
    screen_flow_reran = bool(affected_wave_set & _SCREEN_FLOW_BEHAVIOR_WAVES)
    stale_flows = stale_features or data_model_reran or screen_flow_reran

    # stale_glossary: stale_features OR data-model re-generated
    stale_glossary = stale_features or data_model_reran

    return stale_features, stale_flows, stale_glossary


def _build_payload(
    mode: str, affected_waves: list[str], affected_fcodes: list[str],
    w5_reran: bool, cascade_chain: str | None, fallback_reason: str | None,
    fallback_to_full: bool, deleted_files: list[str],
    doc_shas_snapshot: dict[str, str], since_sha: str, head_sha: str,
    affected_screens: list[str] | None = None,
    screen_spec_shas_snapshot: dict[str, str] | None = None,
    affected_holistic_docs: list[str] | None = None,
    affected_flows: list[str] | None = None,
    stale_features: bool | None = None,
    stale_flows: bool | None = None,
    stale_glossary: bool | None = None,
) -> dict:
    payload: dict = {
        "affected_fcodes": affected_fcodes,
        "affected_waves": affected_waves,
        "cascade_chain": cascade_chain,
        "deleted_files": deleted_files,
        "doc_shas_snapshot": doc_shas_snapshot,
        "fallback_reason": fallback_reason,
        "fallback_to_full": fallback_to_full,
        "generated_at": os.environ.get("REBUILD_PLANNER_GENERATED_AT") or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head_sha": head_sha,
        "mode": mode,
        "since_sha": since_sha,
        "w5_reran": w5_reran,
    }
    # affected_screens: only emitted in incremental mode (omission means "all screens" in full mode)
    if mode != "full" and affected_screens is not None:
        payload["affected_screens"] = affected_screens
    # screen_spec_shas_snapshot: always include when provided (empty dict is valid — project has no screens)
    if screen_spec_shas_snapshot is not None:
        payload["screen_spec_shas_snapshot"] = screen_spec_shas_snapshot
    # Issue 2: holistic docs triggered when any cascade fires in incremental mode
    if mode == "incremental" and affected_holistic_docs is not None:
        payload["affected_holistic_docs"] = affected_holistic_docs
    if mode == "incremental" and affected_flows is not None:
        payload["affected_flows"] = affected_flows
    # [V7] Selective staleness flags (only for incremental core mode)
    if stale_features is not None:
        payload["stale_features"] = stale_features
    if stale_flows is not None:
        payload["stale_flows"] = stale_flows
    if stale_glossary is not None:
        payload["stale_glossary"] = stale_glossary
    return payload


def _parse_screen_sections(screen_list_path: Path) -> dict[str, tuple[str, str]]:
    """Parse screen-list.md SCR### sections → {SCR###: (slug, body)}.

    Slug is the part after the underscore in `## SCR###_Slug` headings.
    Body is the text between this heading line and the next SCR heading (exclusive).
    Returns empty dict if the file is absent.
    """
    if not screen_list_path.is_file():
        return {}
    lines = screen_list_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    heading_re = re.compile(r"^## (SCR\d{3,4}[a-z]?)(?:_(\w+))?")
    result: dict[str, tuple[str, str]] = {}
    current_code: str | None = None
    current_slug: str = ""
    current_body_lines: list[str] = []

    for line in lines:
        m = heading_re.match(line)
        if m:
            # Save previous section
            if current_code is not None:
                result[current_code] = (current_slug, "".join(current_body_lines))
            current_code = m.group(1)
            current_slug = m.group(2) or ""
            current_body_lines = []
        else:
            if current_code is not None:
                current_body_lines.append(line)

    # Flush last section
    if current_code is not None:
        result[current_code] = (current_slug, "".join(current_body_lines))

    return result


def _hash_screen_sections(parsed: dict[str, tuple[str, str]]) -> dict[str, str]:
    """Compute sha256 of each section body → {SCR###: hex_sha}."""
    return {
        code: hashlib.sha256(body.encode("utf-8")).hexdigest()
        for code, (slug, body) in parsed.items()
    }


def _resolve_screen_dirname(parsed: dict[str, tuple[str, str]], code: str) -> str:
    """Return 'SCR###_Slug' dirname; falls back to bare 'SCR###' when slug absent."""
    entry = parsed.get(code)
    return f"{code}_{entry[0]}" if entry and entry[0] else code


def _diff_screen_shas(
    prior: dict[str, str],
    current: dict[str, str],
    artifacts_screens: Path,
    parsed: dict[str, tuple[str, str]],
) -> list[str]:
    """Return sorted list of SCR codes that are NEW, CHANGED, or missing draft spec.md."""
    affected: set[str] = set()
    for code, sha in current.items():
        if prior.get(code) != sha:
            affected.add(code)
            continue
        # SHA matches but spec.md may be missing
        dirname = _resolve_screen_dirname(parsed, code)
        spec_path = artifacts_screens / dirname / "spec.md"
        if not spec_path.is_file():
            affected.add(code)
    return sorted(affected)


def _compute_doc_shas_snapshot(docs_root: Path) -> dict[str, str]:
    """Compute SHA-256 for each core artifact from its canonical layered path."""
    shas: dict[str, str] = {}
    for artifact_name, rel_path in ARTIFACT_LAYERED.items():
        fpath = docs_root / rel_path
        if fpath.is_file():
            shas[artifact_name] = hashlib.sha256(fpath.read_bytes()).hexdigest()
    return shas


def _hydrate(plan_dir: Path, docs_root: Path) -> int:
    """Wave -1 hydrate: copy non-affected artifacts from layered docs/ paths to artifacts/."""
    plan_path = plan_dir / "artifacts" / ".incremental-plan.json"
    plan_data = _load_json(plan_path)
    if not plan_data:
        print("[ERROR] .incremental-plan.json not found or unparseable", file=sys.stderr)
        return 1
    if plan_data.get("mode") == "full":
        return 0

    affected_waves = set(plan_data.get("affected_waves", []))
    affected_fcodes = set(plan_data.get("affected_fcodes", []))
    artifacts_dir = plan_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    missing_sources: list[str] = []

    # Core artifacts: copy from layered path if subject NOT in affected_waves
    for fname, subject in CORE_ARTIFACT_TO_WAVE_SUBJECT.items():
        rel = ARTIFACT_LAYERED.get(fname)
        src = (docs_root / rel) if rel else (docs_root / fname)
        dst = artifacts_dir / fname
        if subject not in affected_waves:
            if not src.is_file():
                missing_sources.append(fname)
            else:
                shutil.copy2(str(src), str(dst))

    # system-overview.md: always copy (no wave regenerates it pre-Issue-2)
    so_src = docs_root / ARTIFACT_LAYERED["system-overview.md"]
    so_dst = artifacts_dir / "system-overview.md"
    if so_src.is_file():
        shutil.copy2(str(so_src), str(so_dst))
    else:
        missing_sources.append("system-overview.md")

    # architecture.md: copy if present, else skip (like business-rules — NOT like
    # system-overview, which forces a full-rebuild fallback when absent). architecture is a
    # newer artifact; a legacy repo lacking it must not be forced into a full rebuild here.
    # No incremental wave regenerates it; it is always hydrated from the layered copy.
    arch_src = docs_root / ARTIFACT_LAYERED["architecture.md"]
    arch_dst = artifacts_dir / "architecture.md"
    if arch_src.is_file():
        shutil.copy2(str(arch_src), str(arch_dst))

    # business-rules.md: always copy (no wave regenerates it pre-Issue-2)
    br_src = docs_root / ARTIFACT_LAYERED["business-rules.md"]
    br_dst = artifacts_dir / "business-rules.md"
    if br_src.is_file():
        shutil.copy2(str(br_src), str(br_dst))

    # _canonical-fcodes.json: always hydrate
    canon_src = docs_root / "_canonical-fcodes.json"
    canon_dst = artifacts_dir / "_canonical-fcodes.json"
    if canon_src.is_file():
        shutil.copy2(str(canon_src), str(canon_dst))

    # Feature specs: copy non-affected F### from docs/features/
    features_src = docs_root / "features"
    features_dst = artifacts_dir / "features"
    if features_src.is_dir():
        for fdir in sorted(features_src.iterdir()):
            if not fdir.is_dir():
                continue
            fcode_match = re.match(r"^(F\d{3,4})", fdir.name)
            if not fcode_match:
                continue
            fcode = fcode_match.group(1)
            if fcode not in affected_fcodes:
                # Hydrate all 4 files (technical-spec.md, business-context.md, screens.md, edge-cases.md)
                for src_file in fdir.iterdir():
                    if not src_file.is_file():
                        continue
                    dst_file = features_dst / fdir.name / src_file.name
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_file), str(dst_file))

    # Flows: hydrate docs/flows/ → artifacts/flows/ (all flows, always; --flows pass re-synths all)
    flows_src = docs_root / "flows"
    flows_dst = artifacts_dir / "flows"
    if flows_src.is_dir():
        for flow_file in sorted(flows_src.iterdir()):
            if flow_file.is_file() and not flow_file.name.startswith("."):
                dst_file = flows_dst / flow_file.name
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(flow_file), str(dst_file))

    # Glossary: hydrate docs/system/glossary.md → artifacts/glossary.md
    glossary_src = docs_root / ARTIFACT_LAYERED["glossary.md"]
    glossary_dst = artifacts_dir / "glossary.md"
    if glossary_src.is_file():
        shutil.copy2(str(glossary_src), str(glossary_dst))

    # Screen specs: copy non-affected SCR### spec.md to artifacts/screens/
    affected_screens_set = set(plan_data.get("affected_screens") or [])
    screens_src = docs_root / "screens"
    screens_dst = artifacts_dir / "screens"
    if screens_src.is_dir() and "affected_screens" in plan_data:
        # Only hydrate when affected_screens field was present (omission means full mode)
        for sdir in sorted(screens_src.iterdir()):
            if not sdir.is_dir():
                continue
            m = re.match(r"^(SCR\d{3,4}[a-z]?)", sdir.name)
            if not m:
                continue
            code = m.group(1)
            if code in affected_screens_set:
                continue
            spec_src = sdir / "spec.md"
            if spec_src.is_file():
                spec_dst = screens_dst / sdir.name / "spec.md"
                spec_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(spec_src), str(spec_dst))

    # First-run guard: missing source → auto-fallback to full
    if missing_sources:
        fallback_reason = f"docs/ baseline missing — first incremental on fresh repo (missing: {', '.join(missing_sources)})"
        print(f"[INFO] {fallback_reason}", file=sys.stderr)
        plan_data["mode"] = "full"
        plan_data["fallback_reason"] = fallback_reason
        plan_data["fallback_to_full"] = True
        _atomic_write(plan_path, plan_data)
        return 0

    # Update doc_shas_snapshot after hydration
    shas: dict[str, str] = {}
    for md in sorted(artifacts_dir.glob("*.md")):
        if md.is_file():
            shas[md.name] = hashlib.sha256(md.read_bytes()).hexdigest()
    plan_data["doc_shas_snapshot"] = shas
    _atomic_write(plan_path, plan_data)
    return 0


def _list_flow_files(docs_root: Path) -> list[str]:
    """Return sorted list of flow filenames in docs_root/flows/."""
    flows_dir = docs_root / "flows"
    if not flows_dir.is_dir():
        return []
    return sorted(
        f.name for f in flows_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )


def _list_all_fcodes(docs_root: Path, canonical_path: Path) -> list[str]:
    """Return all F### codes from canonical JSON, or from docs/features/ as fallback."""
    canonical = _load_json(canonical_path)
    if canonical and "features" in canonical:
        return sorted({f["fcode"] for f in canonical["features"]})
    # Fallback: scan docs/features/
    features_dir = docs_root / "features"
    if features_dir.is_dir():
        fcodes: list[str] = []
        for d in sorted(features_dir.iterdir()):
            if d.is_dir():
                m = re.match(r"^(F\d{3,4})", d.name)
                if m:
                    fcodes.append(m.group(1))
        return sorted(set(fcodes))
    return []


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cascade-aware incremental planner")
    p.add_argument("--full", action="store_true", help="Force full rebuild")
    p.add_argument("--since", default=None, help="Override base SHA for diff")
    p.add_argument("--dry-run", action="store_true", help="Print decision, no file write")
    p.add_argument("--features", default=None, help="Manual F### override (comma-sep)")
    p.add_argument("--plan-dir", required=True, help="Active plan directory")
    p.add_argument("--docs-root", default=None, help="Docs root directory (docs/)")
    p.add_argument("--docs-specs", default=None,
                   help="Deprecated alias for --docs-root; kept for backward compat")
    p.add_argument("--scout-report", default=None, help="Path to scout-report.md")
    p.add_argument("--out", default=None, help="Output path for .incremental-plan.json")
    p.add_argument("--threshold", type=float, default=None, help="Diff threshold (0.0-1.0)")
    p.add_argument("--hydrate", action="store_true", help="Run Wave -1 hydrate mode")
    # New standalone-pass planner modes (v5.0.0)
    p.add_argument("--feature-specs", action="store_true",
                   help="Plan mode for the --feature-specs pass: diff source since "
                        "last_feature_spec_run_sha (this pass's own cursor; empty → first run → all "
                        "fcodes), map to affected fcodes via reverse-index.")
    p.add_argument("--flows", action="store_true",
                   help="Plan mode for the --flows pass: always re-synth all flows.")
    p.add_argument("--glossary", action="store_true",
                   help="Plan mode for the --glossary pass: always re-synth glossary.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan_dir = Path(args.plan_dir).resolve()

    docs_root_arg = args.docs_root or args.docs_specs
    if not docs_root_arg:
        print("[ERROR] --docs-root is required", file=sys.stderr)
        return 2
    docs_root = Path(docs_root_arg).resolve()

    if args.hydrate:
        return _hydrate(plan_dir, docs_root)

    # Mutually-exclusive guard
    if args.full and args.since:
        print("[ERROR] --full and --since are mutually exclusive", file=sys.stderr)
        return 2

    out_path = Path(args.out) if args.out else plan_dir / "artifacts" / ".incremental-plan.json"
    try:
        head_sha = _git_head_sha()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"[ERROR] git rev-parse HEAD failed: {exc}", file=sys.stderr)
        return 1

    # ── Standalone pass planner modes (v5.0.0) ────────────────────────────────

    # --feature-specs mode: diff source since last_feature_spec_run_sha (this pass's OWN
    # cursor), map to fcodes via reverse-index. The feature-specs pass must NOT diff from
    # last_rebuild_sha (the core cursor): a prior core run advances last_rebuild_sha, which
    # would shrink the feature-specs diff to ~empty and silently leave specs stale. The
    # cursor is empty until --feature-specs has run, so the first run processes ALL fcodes.
    # Authority: references/pipeline-feature-specs.md (step 2), references/incremental-state-schema.md.
    # [RT-C1] absent index → all fcodes.
    if args.feature_specs:
        state_path = docs_root / ".rebuild-state.json"
        state = _load_json(state_path) or {}
        canonical_path = plan_dir / "artifacts" / "_canonical-fcodes.json"
        if not canonical_path.is_file():
            canonical_path = docs_root / "_canonical-fcodes.json"

        ri_path = docs_root / "_source-to-fcode.json"
        reverse_index = _load_json(ri_path) if ri_path.is_file() else None

        since_sha = state.get("last_feature_spec_run_sha", "")
        all_fcodes = _list_all_fcodes(docs_root, canonical_path)

        if reverse_index is None:
            # [RT-C1] Index absent → all fcodes, never halt
            print("[INFO] _source-to-fcode.json absent — scheduling all fcodes (no incremental possible)", file=sys.stderr)
            affected_fcodes = all_fcodes
            fallback_reason = "index_absent"
        elif not since_sha:
            # First --feature-specs run (cursor empty) → process all fcodes.
            print("[INFO] feature-specs: first run (no last_feature_spec_run_sha) — processing all fcodes", file=sys.stderr)
            affected_fcodes = all_fcodes
            fallback_reason = "first_run"
        elif not _git_sha_reachable(since_sha):
            print(f"[INFO] feature-specs: last_feature_spec_run_sha {since_sha[:7]} unreachable — processing all fcodes", file=sys.stderr)
            affected_fcodes = all_fcodes
            fallback_reason = "sha_unreachable"
        else:
            try:
                diff_rows = _git_diff(since_sha, "HEAD")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
                print(f"[ERROR] git diff failed: {exc}", file=sys.stderr)
                return 1
            all_changed = [r[2] or r[1] for r in diff_rows]
            ri_index = reverse_index.get("index", {})
            affected_set: set[str] = set()
            for p in all_changed:
                if p in ri_index:
                    affected_set.update(ri_index[p])
            affected_fcodes = sorted(affected_set) if affected_set else []
            fallback_reason = None

        payload = {
            "mode": "feature-specs",
            "affected_fcodes": affected_fcodes,
            "fallback_reason": fallback_reason,
            "generated_at": os.environ.get("REBUILD_PLANNER_GENERATED_AT") or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "head_sha": head_sha,
            "since_sha": since_sha,
        }
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=feature-specs fcodes={len(affected_fcodes)} fallback={fallback_reason or 'none'}")
        return 0

    # --flows mode: always re-synth all flows (cross-feature; no per-entity diff).
    if args.flows:
        all_flow_files = _list_flow_files(docs_root)
        payload = {
            "mode": "flows",
            "affected_flows": all_flow_files,
            "generated_at": os.environ.get("REBUILD_PLANNER_GENERATED_AT") or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "head_sha": head_sha,
        }
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=flows flows={len(all_flow_files)}")
        return 0

    # --glossary mode: always re-synth glossary (cross-feature; no per-entity diff).
    if args.glossary:
        payload = {
            "mode": "glossary",
            "generated_at": os.environ.get("REBUILD_PLANNER_GENERATED_AT") or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "head_sha": head_sha,
        }
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print("[INFO] mode=glossary")
        return 0

    # ── Core planner (default) ─────────────────────────────────────────────────

    # --features passthrough: skip cascade, emit minimal payload
    if args.features:
        fcodes = [f.strip() for f in args.features.split(",") if f.strip()]
        payload = _build_payload(
            mode="incremental", affected_waves=[], affected_fcodes=fcodes,
            w5_reran=False, cascade_chain=None, fallback_reason=None,
            fallback_to_full=False, deleted_files=[],
            doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha="", head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=incremental waves=0 fcodes={len(fcodes)} fallback=none (--features override)")
        return 0

    # Prereq checks (hard halt conditions 1-3)
    scout_path = Path(args.scout_report) if args.scout_report else plan_dir / "artifacts" / "scout-report.md"
    if not scout_path.is_file():
        print(f"[ERROR] scout-report.md not found: {scout_path}", file=sys.stderr)
        return 1
    canonical_path = plan_dir / "artifacts" / "_canonical-fcodes.json"
    if not canonical_path.is_file():
        canonical_path = docs_root / "_canonical-fcodes.json"
        if not canonical_path.is_file():
            print(f"[ERROR] _canonical-fcodes.json not found", file=sys.stderr)
            return 1
    ri_path = docs_root / "_source-to-fcode.json"
    if not ri_path.is_file():
        print(f"[ERROR] _source-to-fcode.json not found: {ri_path}", file=sys.stderr)
        return 1

    reverse_index = _load_json(ri_path) or {}

    # --full flag (condition 9)
    if args.full:
        # W2.5: compute screen sha snapshot from docs/generated/screen-list.md if present
        _sl_path = docs_root / "generated" / "screen-list.md"
        _screen_shas_full = _hash_screen_sections(_parse_screen_sections(_sl_path))
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=None,
            fallback_reason="explicit --full flag", fallback_to_full=False,
            deleted_files=[], doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha="", head_sha=head_sha,
            screen_spec_shas_snapshot=_screen_shas_full,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=full waves={len(WAVE_ORDER)} fcodes=all fallback=explicit_full")
        return 0

    # Load state (condition 4)
    state_path = docs_root / ".rebuild-state.json"
    state = _load_json(state_path)
    if not state:
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=None,
            fallback_reason="state_missing", fallback_to_full=True,
            deleted_files=[], doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha="", head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print("[INFO] mode=full waves=all fcodes=all fallback=state_missing")
        return 0

    since_sha = args.since or state.get("last_rebuild_sha", "")

    # SHA reachability (condition 5)
    if not since_sha or not _git_sha_reachable(since_sha):
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=None,
            fallback_reason="sha_unreachable", fallback_to_full=True,
            deleted_files=[], doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha=since_sha, head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=full waves=all fcodes=all fallback=sha_unreachable")
        return 0

    # Git diff
    try:
        diff_rows = _git_diff(since_sha, "HEAD")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"[ERROR] git diff failed: {exc}", file=sys.stderr)
        return 1
    all_changed = [r[2] or r[1] for r in diff_rows]
    deleted_files = [r[1] for r in diff_rows if r[0] == "D"]

    # Threshold check (condition 6)
    threshold = args.threshold or float(os.environ.get("REBUILD_INCREMENTAL_THRESHOLD", "0.30"))
    inventory = _parse_scout_inventory(scout_path)
    total_source = len(inventory) if inventory else 0
    if total_source > 0 and len(all_changed) / total_source > threshold:
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=None,
            fallback_reason=f"threshold_exceeded ({len(all_changed)}/{total_source} > {threshold})",
            fallback_to_full=True, deleted_files=deleted_files,
            doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha=since_sha, head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=full waves=all fcodes=all fallback=threshold_exceeded")
        return 0

    # Manifest check (condition 7)
    manifest_changed = any(Path(p).name in MANIFEST_FILES for p in all_changed)
    if manifest_changed:
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True,
            cascade_chain="FULL (manifest changed)",
            fallback_reason="manifest_changed", fallback_to_full=True,
            deleted_files=deleted_files,
            doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha=since_sha, head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print("[INFO] mode=full waves=all fcodes=all fallback=manifest_changed")
        return 0

    # Classify files
    classified, unowned = _classify_files(diff_rows, inventory)

    # Unowned new source check (condition 8)
    if unowned:
        new_source = [f for f in unowned if not f.startswith(("docs/", "plans/", "tests/", "test/"))]
        if new_source:
            payload = _build_payload(
                mode="full", affected_waves=list(WAVE_ORDER),
                affected_fcodes=[], w5_reran=True, cascade_chain=None,
                fallback_reason=f"unowned_new_source ({', '.join(new_source[:3])})",
                fallback_to_full=True, deleted_files=deleted_files,
                doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
                since_sha=since_sha, head_sha=head_sha,
            )
            if args.dry_run:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                _atomic_write(out_path, payload)
            print(f"[INFO] mode=full waves=all fcodes=all fallback=unowned_new_source")
            return 0

    # Cascade engine
    types_present = set(classified.keys()) - {"other"}
    affected_waves, cascade_chain = _cascade(types_present)

    # config type triggers full
    if cascade_chain and cascade_chain.startswith("FULL"):
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=cascade_chain,
            fallback_reason="config_changed", fallback_to_full=True,
            deleted_files=deleted_files,
            doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha=since_sha, head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print("[INFO] mode=full waves=all fcodes=all fallback=config_changed")
        return 0

    w5_reran = "Wave5: feature-list" in affected_waves
    affected_fcodes = _resolve_fcodes(reverse_index, all_changed, w5_reran, canonical_path)

    # [V7] Compute selective staleness flags for downstream pass notifications
    stale_features, stale_flows, stale_glossary = _compute_stale_flags(
        affected_waves, affected_fcodes, reverse_index, all_changed,
    )

    # W2.5: compute screen sha diff for incremental mode
    _prior_screen_shas = state.get("screen_spec_shas", {})
    _sl_path_inc = docs_root / "generated" / "screen-list.md"
    if not _sl_path_inc.is_file():
        _sl_path_inc = plan_dir / "artifacts" / "screen-list.md"
        if _sl_path_inc.is_file():
            print("[WARN] docs/generated/screen-list.md absent; using artifacts copy for screen sha diff", file=sys.stderr)
    _parsed_screens = _parse_screen_sections(_sl_path_inc)
    _current_screen_shas = _hash_screen_sections(_parsed_screens)
    if not _current_screen_shas and _prior_screen_shas:
        # screen-list.md absent or has no SCR sections — treat all prior screens as affected (conservative)
        print("[WARN] screen-list.md has no SCR sections; treating all prior tracked screens as affected", file=sys.stderr)
        _affected_screens = sorted(_prior_screen_shas.keys())
    else:
        _affected_screens = _diff_screen_shas(
            _prior_screen_shas,
            _current_screen_shas,
            plan_dir / "artifacts" / "screens",
            _parsed_screens,
        )

    # [v25.2.0] A1 confidence-report advisory — print-only, never affects mode/payload/exit
    # code (contrast with the OOB block below, which DOES fall back to full).
    for w in _detect_confidence_report_missing(docs_root):
        print(w, file=sys.stderr)

    # OOB-edit detection — fallback to full if non-affected artifacts were edited
    oob_warnings = _detect_oob(state, docs_root, affected_waves)
    if oob_warnings:
        for w in oob_warnings:
            print(w, file=sys.stderr)
        payload = _build_payload(
            mode="full", affected_waves=list(WAVE_ORDER),
            affected_fcodes=[], w5_reran=True, cascade_chain=cascade_chain,
            fallback_reason="oob_edits_detected", fallback_to_full=True,
            deleted_files=deleted_files,
            doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
            since_sha=since_sha, head_sha=head_sha,
        )
        if args.dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            _atomic_write(out_path, payload)
        print(f"[INFO] mode=full waves=all fcodes=all fallback=oob_edits_detected ({len(oob_warnings)} edits)")
        return 0

    # Issue 2: when any cascade fires, flag holistic docs for regeneration
    _holistic_docs: list[str] | None = None
    _affected_flows: list[str] | None = None
    if affected_waves:
        _holistic_docs = ["system-overview.md", "business-rules.md"]
        _affected_flows = _list_flow_files(docs_root)

    payload = _build_payload(
        mode="incremental", affected_waves=affected_waves,
        affected_fcodes=affected_fcodes, w5_reran=w5_reran,
        cascade_chain=cascade_chain, fallback_reason=None,
        fallback_to_full=False, deleted_files=deleted_files,
        doc_shas_snapshot=_compute_doc_shas_snapshot(docs_root),
        since_sha=since_sha, head_sha=head_sha,
        affected_screens=_affected_screens,
        screen_spec_shas_snapshot=_current_screen_shas,
        affected_holistic_docs=_holistic_docs,
        affected_flows=_affected_flows,
        stale_features=stale_features,
        stale_flows=stale_flows,
        stale_glossary=stale_glossary,
    )

    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _atomic_write(out_path, payload)

    print(f"[INFO] mode=incremental waves={len(affected_waves)} fcodes={len(affected_fcodes)} fallback=none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
