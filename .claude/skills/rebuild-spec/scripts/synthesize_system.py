#!/usr/bin/env python3
# layout-exempt: rebuild-spec synthesis pass — every docs/system path here is this skill's own output target
"""Phase D — System-of-systems synthesis pass for rebuild-spec.

Emits the system layer (language-mapped — docs/system or docs/<primary>/system).

v23.0.0 — BREAKING: derived-view projection removed (ADR-0002 dead code).
  - Component SOURCE lives at docs/<primary>/components/<name>/ (P04 relocation).
  - Secondary-lang mirrors are produced by translate-per-component (P05 translate-sync).
  - place_components / project_view / rung-selection removed from aggregate path.
  - _converge_components_to_source kept in migrate_docs_layout.py for one-time P07 migration.

v19.0.0 — BREAKING: Python is the SCANNER ONLY. It emits facts, the LLM authors all documents.
  - .system-scout-report.md written to the resolved system docs root (DATA tables only, no Mermaid).
  - per-component-confidence.md stays mechanical (Python writes it directly).
  - NO <name>.draft.md files are written by Python. The system-researcher LLM pass creates those
    from templates/aggregate/<name>-template.md + the scout report + component docs.

v18.0.0 (prior) — Python wrote <name>.draft.md via template substitution ({{SCOUT}} replaced).
v17.0.0 — aggregate-tier quality: entity dedup+junk-filter, Mermaid layer+saga charts,
  reasoned read-first nav, W7a-style review gate.
v13.0.0 — BREAKING: output path is language-mapped (per-lang projects → docs/<primary>/system).

RT2-F11: --aggregate BLOCK by default; --force-aggregate degraded-proceed.
RT2-F10: snapshot hash (incl. format version) in headers; stale sha → [WARN] stale_digest.
RT2-F6/F7: sanitize + length caps enforced in _system_synthesis_lib.
All writes via _path_lib._resolve_guarded. Stdlib only. Exit 0 advisory.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _lang_lib import (                                      # noqa: E402
    LAYOUT_SENTINEL, detect_layout_mode, normalize_lang, resolve_docs_root,
)
from _path_lib import _resolve_guarded                       # noqa: E402
from _synthesis_io_lib import (                              # noqa: E402
    atomic_write, check_completeness, collect_digest_paths,
    load_manifest, read_system_state, write_system_state,
)
from _synthesis_render_lib import render_per_component_confidence  # noqa: E402
from _synthesis_scout_lib import (                           # noqa: E402
    assemble_scout_report, build_scout_facts,
)
from _system_synthesis_lib import (                          # noqa: E402
    SYNTHESIS_FORMAT_VERSION, build_interaction_edges, correlate_entities,
    load_digests, snapshot_hash,
)


def _resolve_manifest(root: str, manifest_arg: str | None) -> str | None:
    if manifest_arg:
        return os.path.realpath(os.path.abspath(manifest_arg))
    default = os.path.join(os.path.realpath(os.path.abspath(root)),
                           ".rebuild-components.json")
    return default if os.path.isfile(default) else None


def _check_stale(snap: str, snap_file: str) -> None:
    if not os.path.isfile(snap_file):
        return
    try:
        prior = Path(snap_file).read_text(encoding="utf-8").strip()
        if prior != snap:
            print(
                f"[WARN] stale_digest: sha changed since last synthesis "
                f"(prior={prior[:12]}… current={snap[:12]}…)",
                file=sys.stderr,
            )
    except OSError:
        pass


def _read_state_lang(state_path: str) -> str:
    """Return the `primary_lang` recorded in a .rebuild-state.json (empty if absent)."""
    try:
        data = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(data.get("primary_lang") or "").strip() if isinstance(data, dict) else ""


def _discover_primary_lang(abs_root: str, override: str | None) -> str:
    """Resolve primary_lang for the synthesis output path (V1-Q3).

    `--primary-lang` override wins. Otherwise read every component
    docs/components/<name>/.rebuild-state.json plus the root docs/.rebuild-state.json
    and take the MAJORITY value. None found → 'en' fallback. A conflict (services
    disagree) → majority + [WARN] lang_conflict, continue (never block).
    """
    if override:
        return override
    comp_base = os.path.join(abs_root, "docs", "components")
    langs: list[str] = []
    if os.path.isdir(comp_base):
        for name in sorted(os.listdir(comp_base)):
            pl = _read_state_lang(os.path.join(comp_base, name, ".rebuild-state.json"))
            if pl:
                langs.append(pl)
    root_pl = _read_state_lang(os.path.join(abs_root, "docs", ".rebuild-state.json"))
    if root_pl:
        langs.append(root_pl)
    if not langs:
        # Last resort: check docs/.rebuild-system-state.json written by the previous
        # synthesis run.  This is the only reliable record after the P07 migration moves
        # component state to docs/<primary>/components/<name>/ and deletes docs/components/.
        system_state = read_system_state(os.path.join(abs_root, "docs"))
        if system_state:
            sp = str(system_state.get("primary_lang") or "").strip()
            if sp:
                langs.append(sp)
    if not langs:
        return "en"
    counts = Counter(langs)
    # Deterministic majority: highest count, ties broken by code (stable across runs).
    majority = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    if len(counts) > 1:
        print(
            f"[WARN] lang_conflict: components disagree on primary_lang "
            f"{dict(counts)} — picking majority '{majority}'",
            file=sys.stderr,
        )
    return majority


def _load_root_translations(abs_root: str) -> dict[str, Any]:
    """Return the root state dict (for detect_layout_mode's translations signal)."""
    try:
        data = json.loads(
            Path(os.path.join(abs_root, "docs", ".rebuild-state.json"))
            .read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_system_root(abs_root: str, primary_lang: str) -> tuple[str, bool, str]:
    """Resolve the language-mapped docs/system root, auto-migrating a flat legacy tree.

    Canonical consumer rule: detect_layout_mode + resolve_docs_root over an ABSOLUTE
    docs_base. en single-lang → docs/system (byte-identical, no-op). per-lang (non-en
    primary, or en + a registered secondary) → docs/<primary>/system; if the tree is
    still flat with no sentinel, auto-invoke migrate_docs_layout first (no orphaned
    flat copy). Returns (guarded_system_root, migrated, layout_mode). Raises ValueError
    on a path-unsafe lang (caller aborts).
    """
    docs_base = os.path.join(abs_root, "docs")
    lang = normalize_lang(primary_lang)  # path-guard; ValueError = hard abort
    state = _load_root_translations(abs_root)
    mode = detect_layout_mode(lang, docs_base=docs_base, state=state)
    rel = resolve_docs_root(lang, lang, multilang=(mode == "per-lang"))
    docs_root_lang = os.path.join(abs_root, *rel.split("/"))
    target_system = os.path.join(docs_root_lang, "system")
    flat_system = os.path.join(docs_base, "system")
    migrated = False
    sentinel_present = os.path.exists(
        os.path.join(docs_base, lang, LAYOUT_SENTINEL)
    )
    needs_migration = (
        docs_root_lang != docs_base
        and not sentinel_present
        and os.path.isdir(flat_system)
        and not os.path.isdir(target_system)
    )
    if needs_migration:
        from migrate_docs_layout import flip as migrate_flip  # local — avoid cycle
        from migrate_docs_layout import relocate_to_primary
        if lang == "en":
            rc = migrate_flip(Path(docs_base), "en", force_rename=False)
        else:
            rc, _moved = relocate_to_primary(Path(docs_base), lang)
        # A non-zero rc means the flip aborted (e.g. alias-dir coexistence). Do NOT
        # proceed to write into a per-lang root that was never created — that would
        # fork the tree (the orphaned-flat-copy the migration exists to prevent).
        if rc != 0:
            raise ValueError(
                f"auto-migration aborted (rc={rc}); resolve the docs/ layout manually "
                f"via migrate_docs_layout before re-running --aggregate"
            )
        migrated = True
        print(f"[INFO] auto-migrated flat docs/ → per-lang docs/{lang}/", file=sys.stderr)
        # Migration places the sentinel; re-detect so callers get the post-migration mode.
        mode = detect_layout_mode(lang, docs_base=docs_base, state=state)
    # v23 one-time component migration: converge root docs/components/ → docs/<primary>/components/.
    # Idempotent (sentinel-gated), soft-failure (WARN, never blocks synthesis).
    # Only needed for non-en repos that still have the old v20/v22 root layout.
    if lang != "en":
        try:
            from _component_migrate_lib import migrate_components_to_lang  # noqa: E402 local
            migrate_components_to_lang(Path(docs_base), lang)
        except Exception as _cme:  # noqa: BLE001
            print(f"[WARN] component-migrate-v23 failed (non-fatal): {_cme}", file=sys.stderr)
    # Purge stale DOCUMENT-MAP* files left by pre-v15 runs (idempotent, best-effort).
    try:
        from migrate_docs_layout import purge_document_maps  # local import — avoid cycle
        purge_document_maps(Path(docs_base))
    except Exception as _exc:  # noqa: BLE001
        print(f"[WARN] purge_document_maps failed (non-fatal): {_exc}", file=sys.stderr)
    # Guard the whole resolved root against the project root (traversal/symlink reject).
    return _resolve_guarded(target_system, abs_root), migrated, mode


def _write_artifacts(
    artifacts: dict[str, str], docs_root: str
) -> None:
    os.makedirs(docs_root, exist_ok=True)
    for fname, content in artifacts.items():
        raw = os.path.join(docs_root, fname)
        try:
            guarded = _resolve_guarded(raw, docs_root)
        except ValueError as exc:
            print(f"[ERROR] write-safety violation for {fname}: {exc}", file=sys.stderr)
            continue
        try:
            atomic_write(guarded, content)
            print(f"[OK] wrote {guarded}", file=sys.stderr)
        except OSError as exc:
            print(f"[ERROR] cannot write {fname}: {exc}", file=sys.stderr)


def _check_mirror_staleness(abs_root: str, manifest_entries: list[dict[str, Any]]) -> None:
    """Emit [WARN] mirror_stale when a reused component's recorded mirror sha drifts.

    For each manifest entry with status 'reused', compare the durable system state's
    recorded mirror source_sha against the live reused docs/.rebuild-state.json
    last_rebuild_sha.  A mismatch means the source component was rebuilt after the
    mirror was taken — the mirror is stale.
    """
    system_state = read_system_state(os.path.join(abs_root, "docs"))
    if not system_state:
        return
    component_states: dict[str, dict[str, Any]] = {
        str(c.get("name", "")): c
        for c in system_state.get("components", [])
        if isinstance(c, dict)
    }
    for entry in manifest_entries:
        if str(entry.get("status", "")) != "reused":
            continue
        name = str(entry.get("name", entry.get("path", "")))
        docs_path = str(entry.get("docs_path", ""))
        if not docs_path:
            continue
        # Live sha: read from <src>/docs/.rebuild-state.json last_rebuild_sha.
        live_state_path = os.path.join(
            abs_root, docs_path, ".rebuild-state.json"
        )
        if not os.path.isfile(live_state_path):
            continue
        try:
            live_state = json.loads(Path(live_state_path).read_text(encoding="utf-8"))
            live_sha = str(live_state.get("last_rebuild_sha", ""))
        except (OSError, json.JSONDecodeError):
            continue
        if not live_sha:
            continue
        # Recorded mirror sha: from durable system state.
        recorded_sha = str(component_states.get(name, {}).get("source_sha", ""))
        if recorded_sha and recorded_sha != live_sha:
            print(
                f"[WARN] mirror_stale: {name!r} — mirror sha {recorded_sha[:12]}… "
                f"differs from live {live_sha[:12]}…",
                file=sys.stderr,
            )


def synthesize(
    root: str,
    manifest: str | None,
    digest_dir: str | None,
    max_digest_age: int | None,
    force_aggregate: bool,
    primary_lang: str | None = None,
) -> int:
    abs_root = os.path.realpath(os.path.abspath(root))
    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    lang = _discover_primary_lang(abs_root, primary_lang)
    try:
        lang = normalize_lang(lang)  # path-guard up front; ValueError = hard abort
    except ValueError as exc:
        print(f"[ERROR] unsafe primary_lang {lang!r}: {exc}", file=sys.stderr)
        return 1
    try:
        docs_root, _migrated, layout_mode = _resolve_system_root(abs_root, lang)
    except (ValueError, OSError) as exc:
        print(f"[ERROR] cannot resolve system docs root: {exc}", file=sys.stderr)
        return 1

    manifest_path = _resolve_manifest(root, manifest)

    # v23: SOURCE components live at <lang_root>/components/ (lang-namespaced for non-en primaries).
    # en-primary: docs/components/ (byte-identical to v22, back-compat).
    # non-en primary (e.g. vi): docs/vi/components/.
    resolved_components_base = os.path.join(
        abs_root, *resolve_docs_root(lang, lang, multilang=False).split("/"), "components"
    )

    digest_paths = collect_digest_paths(root, digest_dir, max_digest_age,
                                        components_base=resolved_components_base)

    try:
        digests = load_digests(digest_paths)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # RT2-F11 — BLOCK guard
    ok, skipped = check_completeness(manifest_path, digests, force_aggregate)
    if not ok:
        for name in skipped:
            print(f"[BLOCKED] component_incomplete: {name}", file=sys.stderr)
        return 1
    if skipped:
        print(f"[WARN] --force-aggregate: skipped: {', '.join(skipped)}", file=sys.stderr)

    # Mirror-stale check (Phase 09): warn when a reused component's live sha drifted.
    manifest_entries = load_manifest(manifest_path) if manifest_path else []
    _check_mirror_staleness(abs_root, manifest_entries)

    if not digests:
        print("[WARN] no digests found — nothing to synthesize", file=sys.stderr)
        return 0

    snap = snapshot_hash(digests, version=SYNTHESIS_FORMAT_VERSION)
    _check_stale(snap, os.path.join(abs_root, ".rebuild-synthesis-snapshot"))

    edges = build_interaction_edges(digests)
    suggestions = correlate_entities(digests)

    # v19 — build facts dict (Python computes DATA only; LLM authors all documents).
    facts = build_scout_facts(
        digests=digests,
        edges=edges,
        suggestions=suggestions,
        snap=snap,
        abs_root=abs_root,
        layout_mode=layout_mode,
        primary_lang=lang,
    )

    # Step 1: Mechanical artifact — per-component-confidence.md (direct write, no template).
    artifacts: dict[str, str] = {
        "per-component-confidence.md": render_per_component_confidence(
            digests, timestamp, snap),
    }

    # Step 2: Write .system-scout-report.md (facts DATA only, no Mermaid, machine-generated).
    # The system-researcher LLM pass creates <name>.draft.md from the templates + this report.
    artifacts[".system-scout-report.md"] = assemble_scout_report(facts, timestamp)

    _write_artifacts(artifacts, docs_root)

    # Phase 04 — reasoned service reading-order side-channel.
    try:
        from _nav_metadata_lib import build_nav_metadata  # local — keep import surface small
        # Fix A (v23): build authoritative reused_map from manifest status — DRY: reuse
        # manifest_entries (same loop used at line ~401 for .rebuild-system-state.json).
        reused_map: dict[str, bool] = {
            str(entry.get("name", entry.get("path", ""))): str(entry.get("status", "")) == "reused"
            for entry in manifest_entries
        }
        nav_meta = build_nav_metadata(digests, edges, reused_map=reused_map)
        atomic_write(
            os.path.join(docs_root, ".nav-metadata.json"),
            json.dumps(nav_meta, ensure_ascii=False, indent=2) + "\n",
        )
    except OSError as exc:
        print(f"[WARN] could not write .nav-metadata.json: {exc}", file=sys.stderr)

    try:
        atomic_write(
            os.path.join(abs_root, ".rebuild-synthesis-snapshot"), snap + "\n"
        )
    except OSError:
        pass

    # Phase R4 — write durable docs/.rebuild-system-state.json.
    digest_source_sha: dict[str, str] = {
        str(d.get("service", "")): str(d.get("source_sha", ""))
        for d in digests
    }
    components_state = []
    for entry in manifest_entries:
        name = str(entry.get("name", entry.get("path", "")))
        svc_sha = digest_source_sha.get(name, "")
        if not svc_sha:
            svc_sha = digest_source_sha.get(name.rsplit("-", 1)[-1], "")
        if not svc_sha:
            print(
                f"[WARN] no_source_baseline: component {name!r} has no source_sha "
                f"— incremental baseline unavailable",
                file=sys.stderr,
            )
        components_state.append({
            "name": name,
            "role": str(entry.get("role", "")),
            "reused": str(entry.get("status", "")) == "reused",
            "source_sha": svc_sha,
            "mirror_sha": entry.get("sha"),
        })
    system_state_payload: dict[str, Any] = {
        "primary_lang": lang,
        "synthesis_format_version": SYNTHESIS_FORMAT_VERSION,
        "snapshot_hash": snap,
        "generated_at": timestamp,
        "components": components_state,
    }
    try:
        write_system_state(os.path.join(abs_root, "docs"), system_state_payload)
        print(
            f"[OK] wrote docs/.rebuild-system-state.json "
            f"({len(components_state)} component(s))",
            file=sys.stderr,
        )
    except OSError as exc:
        print(f"[WARN] could not write system state: {exc}", file=sys.stderr)

    return 0


def main() -> None:
    p = argparse.ArgumentParser(
        description="Phase D — synthesize system-level docs from neutral digests."
    )
    p.add_argument("--root", default=".", help="Monorepo root (default: cwd)")
    p.add_argument("--manifest", default=None,
                   help="Path to .rebuild-components.json")
    p.add_argument("--digest-collect", dest="digest_dir", default=None,
                   help="Explicit digest directory (polyrepo mode)")
    p.add_argument("--max-digest-age", dest="max_digest_age", type=int,
                   default=None, metavar="DAYS",
                   help="Reject digests older than N days")
    p.add_argument("--primary-lang", dest="primary_lang", default=None, metavar="CODE",
                   help="Override discovered primary_lang for the output path "
                        "(default: majority across component .rebuild-state.json / en)")
    p.add_argument("--aggregate", "--synthesize", action="store_true",
                   help="Run synthesis (BLOCK if any component is incomplete)")
    p.add_argument("--force-aggregate", dest="force_aggregate", action="store_true",
                   help="Degraded-proceed: synthesize over done components only")
    args = p.parse_args()
    if not args.aggregate and not args.force_aggregate:
        p.print_help()
        sys.exit(0)
    sys.exit(synthesize(
        root=args.root, manifest=args.manifest, digest_dir=args.digest_dir,
        max_digest_age=args.max_digest_age, force_aggregate=args.force_aggregate,
        primary_lang=args.primary_lang,
    ))


if __name__ == "__main__":
    main()
