#!/usr/bin/env python3
"""Wave 9.5 — reverse-index + state file emitter.

Scans promoted feature specs, extracts source-file citations,
writes `_source-to-fcode.json` (reverse index) and `.rebuild-state.json` (state).

Stdlib only. Authority: ../references/incremental-state-schema.md.

Exit codes: 0 (success), 2 (internal error).

Note: exit code 1 (no spec files found) has been removed (RT-C5). An empty
docs/features/ is a valid state (core-only run); the script emits an empty-but-valid
index and returns 0. The previous exit-1 path blocked every core-only run.

Cursor isolation (--cursor, v5.0.0):
  Each pass advances ONLY its own cursor in .rebuild-state.json. Advancing a foreign
  cursor falsely would make the next core incremental skip real source changes.
  --cursor core       → advances last_rebuild_sha (default behavior, unchanged)
  --cursor feature-specs → advances last_feature_spec_run_sha only
  --cursor flows      → advances last_flows_run_sha only
  --cursor glossary   → advances last_glossary_run_sha only
                        AND refreshes doc_shas["glossary.md"] (RT-H1)
  --cursor api-contracts → advances last_api_contracts_run_sha only
                           AND refreshes doc_shas["api-contracts.md"]
  --cursor jobs       → advances last_jobs_run_sha only (v26.1.0 A2 pass, additive)
                        AND refreshes doc_shas["job-list.md"]
  --cursor test-cases → advances last_test_cases_run_sha only (v26.1.0 B6 pass, additive).
                        No doc_shas entry (per-feature sidecar, not a single core artifact) —
                        falls into the flows/feature-specs "preserve prior entirely" branch.
  --cursor design-intent → advances last_design_intent_run_sha only (v26.1.0 B5 pass,
                        EXPERIMENTAL/report-only — only ever invoked at D.5, post-confirmation).
                        AND refreshes doc_shas["design-intent.md"] (mirrors glossary/jobs — it
                        IS a single core-tier artifact, unlike test-cases' per-feature sidecar).
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _slug_lib import resolve_project_root  # noqa: E402

# v21.0.0 (RT-F4): stamped into .rebuild-state.json on every write so resume can detect a
# stale state (< 21.0.0) and re-run preflight detect. A state written before screen_source
# existed (≤ v20.x) would resume carrying a profile that fail-closes screens to "none"; the
# bump invalidates it so the profile re-resolves. Keep in sync with _stack_profile_lib.SCHEMA_VERSION.
STATE_SCHEMA_VERSION = "21.0.0"

FCODE_DIR_RE = re.compile(r"^(F[0-9]{3,4})")
INLINE_SOURCE_RE = re.compile(r"\*\*Source:\*\*\s+`([^`]+)`")
TABLE_CITE_RE = re.compile(r"`([^`]+\.[A-Za-z0-9]+(?::[0-9\-]+)?)`")
LINE_SUFFIX_RE = re.compile(r":[0-9\-]+$")

# Maps artifact filename → canonical path relative to docs_root (v4 layered layout).
ARTIFACT_LAYERED: dict[str, str] = {
    "route-list.md": "generated/route-list.md",
    "api-map.md": "generated/api-map.md",
    "data-model.md": "generated/entities.md",
    "screen-list.md": "generated/screen-list.md",
    "screen-flow.md": "generated/screen-flow.md",
    "behavior-logic.md": "generated/behavior-logic.md",
    "permissions.md": "system/permissions.md",
    "user-stories.md": "generated/user-stories.md",
    "feature-list.md": "generated/feature-list.md",
    "api-contracts.md": "generated/api-contracts.md",
    "glossary.md": "system/glossary.md",
    "business-rules.md": "system/business-rules.md",
    "system-overview.md": "system/overview.md",
}


def _parse_citations(spec_text: str) -> set[str]:
    """Extract cited file paths from spec markdown."""
    paths: set[str] = set()
    for m in INLINE_SOURCE_RE.finditer(spec_text):
        paths.add(m.group(1))
    in_section = False
    for line in spec_text.splitlines():
        if line.startswith("## Source Code References"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            for m in TABLE_CITE_RE.finditer(line):
                paths.add(m.group(1))
    return paths


def _normalize_path(raw: str) -> str:
    """Strip :lines suffix, normalize to forward-slash repo-relative."""
    cleaned = LINE_SUFFIX_RE.sub("", raw)
    posix = Path(cleaned).as_posix()
    return posix.lstrip("./")


def _extract_fcode(spec_path: Path) -> str | None:
    m = FCODE_DIR_RE.match(spec_path.parent.name)
    return m.group(1) if m else None


def _git_head_sha() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5, check=True,
    )
    return r.stdout.strip()


def _compute_doc_shas(docs_root: Path) -> dict[str, str]:
    """SHA-256 each core artifact from its canonical layered path under docs_root."""
    shas: dict[str, str] = {}
    if not docs_root.is_dir():
        return shas
    for artifact_name, rel_path in ARTIFACT_LAYERED.items():
        fpath = docs_root / rel_path
        if fpath.is_file():
            shas[artifact_name] = hashlib.sha256(fpath.read_bytes()).hexdigest()
    return shas


def build_index(specs_root: Path) -> dict[str, list[str]]:
    """Build {path: [F###, ...]} reverse index from feature spec files.

    [③ CRITICAL] Globs */technical-spec.md (v4 4-file layout). Falls back to */spec.md
    for backward compatibility with legacy single-file feature layouts.
    [RT-C5] Empty specs_root → valid empty index (returns {}), no exception.
    """
    path_to_fcodes: dict[str, set[str]] = {}

    # v4 primary: technical-spec.md holds ## Source Code References
    spec_files = sorted(specs_root.glob("*/technical-spec.md"))
    # Backward compat: also pick up legacy */spec.md files that aren't paired with technical-spec.md
    legacy_spec_files = [
        f for f in sorted(specs_root.glob("*/spec.md"))
        if not (f.parent / "technical-spec.md").is_file()
    ]
    all_spec_files = spec_files + legacy_spec_files

    # [RT-C5] Empty → valid empty index, return {} (exit 0)
    if not all_spec_files:
        return {}

    for spec_file in all_spec_files:
        fcode = _extract_fcode(spec_file)
        if not fcode:
            continue
        text = spec_file.read_text(encoding="utf-8", errors="replace")
        for raw_path in _parse_citations(text):
            norm = _normalize_path(raw_path)
            if norm:
                path_to_fcodes.setdefault(norm, set()).add(fcode)
    return {k: sorted(v) for k, v in sorted(path_to_fcodes.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wave 9.5 reverse-index emitter")
    parser.add_argument("--specs-root", required=True, help="Path to docs/features")
    parser.add_argument("--state-out", required=True, help="Output path for .rebuild-state.json")
    parser.add_argument("--index-out", required=True, help="Output path for _source-to-fcode.json")
    parser.add_argument("--docs-root", default=None, help="Path to docs/ (parent of features/); default: specs-root parent")
    parser.add_argument("--mode", default="full", choices=["full", "incremental"])
    parser.add_argument("--incremental-plan-json", default=None,
                        help="Path to .incremental-plan.json; reads screen_spec_shas_snapshot into state")
    parser.add_argument("--rebuilt-at", default=None, help="ISO-8601 timestamp (default: now)")
    parser.add_argument("--last-rebuild-sha", default=None,
                        help="Override last_rebuild_sha (default: git rev-parse HEAD). Used by bootstrap-from-git flow.")
    # [② CRITICAL] Cursor isolation: advance ONLY the specified pass cursor.
    # Default 'core' preserves existing behavior (last_rebuild_sha = HEAD).
    parser.add_argument(
        "--cursor",
        default="core",
        choices=["core", "feature-specs", "flows", "glossary", "api-contracts", "jobs", "test-cases", "design-intent"],
        help=(
            "Which pass cursor to advance in .rebuild-state.json (v5.0.0). "
            "'core' (default) advances last_rebuild_sha; "
            "'feature-specs' advances last_feature_spec_run_sha; "
            "'flows' advances last_flows_run_sha; "
            "'glossary' advances last_glossary_run_sha and refreshes doc_shas[glossary.md]; "
            "'api-contracts' advances last_api_contracts_run_sha and refreshes doc_shas[api-contracts.md]; "
            "'jobs' advances last_jobs_run_sha and refreshes doc_shas[job-list.md] (v26.1.0); "
            "'test-cases' advances last_test_cases_run_sha only, no doc_shas entry (v26.1.0); "
            "'design-intent' advances last_design_intent_run_sha and refreshes "
            "doc_shas[design-intent.md] (v26.1.0, EXPERIMENTAL — only reached post-confirmation)."
        ),
    )
    args = parser.parse_args(argv)

    specs_root = Path(args.specs_root).resolve()
    if not specs_root.is_dir():
        print(f"[ERROR] specs-root not found: {specs_root}", file=sys.stderr)
        return 1

    index = build_index(specs_root)
    # [RT-C5] Empty index is valid — do not exit 1. The old code did:
    #   if not index: if spec_count == 0: exit 1
    # Now: always proceed regardless of index emptiness.

    rebuilt_at = args.rebuilt_at or (_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    index_data = {"generated_at": rebuilt_at, "index": index}
    canonical = json.dumps(index, sort_keys=True, separators=(",", ":"))
    fcode_index_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # Resolve the SHA to stamp for this cursor.
    # --last-rebuild-sha is a bootstrap-from-git override for the CORE cursor only. Applying it
    # to a non-core cursor would silently misroute the override into last_feature_spec_run_sha /
    # last_flows_run_sha / last_glossary_run_sha, so it is ignored (with a warning) outside core.
    _override = args.last_rebuild_sha
    if _override and args.cursor != "core":
        print(
            f"[WARN] --last-rebuild-sha is only meaningful with --cursor core; "
            f"ignoring it for --cursor {args.cursor} (stamping HEAD instead)",
            file=sys.stderr,
        )
        _override = None
    if _override:
        sha_val = _override.lower()
        if not re.fullmatch(r"[0-9a-f]{7,40}", sha_val):
            print(f"[ERROR] --last-rebuild-sha invalid format: {args.last_rebuild_sha!r}", file=sys.stderr)
            return 2
        run_sha = sha_val
    else:
        try:
            run_sha = _git_head_sha()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            print(f"[ERROR] git rev-parse HEAD failed: {exc}", file=sys.stderr)
            return 2

    # Read prior state to preserve fields not updated this run (cursor isolation).
    _state_out_path = Path(args.state_out)
    _prior_state: dict = {}
    if _state_out_path.is_file():
        try:
            _prior_state = json.loads(_state_out_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            # Corrupt/unreadable state → all prior cursors fall back to "" below. Log so a
            # silent cursor reset (which forces the next core run into a full rebuild) is diagnosable.
            print(f"[WARN] could not read prior state {_state_out_path} ({exc}); cursors reset to empty", file=sys.stderr)

    docs_root = Path(args.docs_root).resolve() if args.docs_root else specs_root.parent
    current_doc_shas = _compute_doc_shas(docs_root)
    cursor = args.cursor

    # doc_shas feeds out-of-band-edit detection in the core planner (_detect_oob): it must
    # reflect the SHA each core artifact had the last time a pass legitimately wrote it.
    # Only the core pass owns the full set, so ONLY core does a full refresh. A non-core pass
    # that re-stamped every artifact would silently "bless" an out-of-band edit made since the
    # last core run, suppressing the warning the next core run should raise.
    #   core      → full refresh (owns all core artifacts)
    #   glossary  → [RT-H1] refresh ONLY glossary.md (the artifact it regenerates), preserve rest
    #   jobs      → refresh ONLY job-list.md (the artifact it regenerates), preserve rest (v26.1.0)
    #   design-intent → refresh ONLY design-intent.md, preserve rest (v26.1.0 B5, EXPERIMENTAL —
    #     this branch is only exercised at D.5, post user-confirmation; a report-only run that
    #     never confirms promotion never calls build_source_to_fcode.py with this cursor at all)
    #   flows / feature-specs / test-cases → touch no SINGLE core artifact tracked here
    #     (test-cases.md is per-feature, not a single doc_shas key, v26.1.0 B6) → preserve prior entirely
    prior_doc_shas = _prior_state.get("doc_shas", {}) or {}
    if cursor == "core":
        doc_shas = current_doc_shas
    elif cursor == "glossary":
        doc_shas = dict(prior_doc_shas)
        if "glossary.md" in current_doc_shas:
            doc_shas["glossary.md"] = current_doc_shas["glossary.md"]
    elif cursor == "api-contracts":
        doc_shas = dict(prior_doc_shas)
        if "api-contracts.md" in current_doc_shas:
            doc_shas["api-contracts.md"] = current_doc_shas["api-contracts.md"]
    elif cursor == "jobs":
        doc_shas = dict(prior_doc_shas)
        if "job-list.md" in current_doc_shas:
            doc_shas["job-list.md"] = current_doc_shas["job-list.md"]
    elif cursor == "design-intent":
        doc_shas = dict(prior_doc_shas)
        if "design-intent.md" in current_doc_shas:
            doc_shas["design-intent.md"] = current_doc_shas["design-intent.md"]
    else:  # flows, feature-specs, test-cases
        doc_shas = dict(prior_doc_shas)

    # [② CRITICAL] Build state: advance ONLY the cursor for this pass; preserve others.
    # Start from prior state and selectively update.
    state_data: dict = {
        # Always-updated fields:
        "schema_version": STATE_SCHEMA_VERSION,  # v21.0.0 (RT-F4): resume-invalidation gate
        "fcode_index_sha": fcode_index_sha,
        "mode": args.mode,
        "rebuilt_at": rebuilt_at,
        "doc_shas": doc_shas,
    }

    # Preserve primary_lang (set once on first run; stable thereafter).
    state_data["primary_lang"] = _prior_state.get("primary_lang", "")

    # Preserve translations map (secondary language cursors; Phase 03/04 writes these).
    state_data["translations"] = dict(_prior_state.get("translations", {}) or {})

    # Preserve all prior cursor values first, then stamp only the active cursor.
    # Core cursor: last_rebuild_sha
    state_data["last_rebuild_sha"] = _prior_state.get("last_rebuild_sha", "")
    # Feature-specs cursor
    state_data["last_feature_spec_run_sha"] = _prior_state.get("last_feature_spec_run_sha", "")
    # Flows cursor
    state_data["last_flows_run_sha"] = _prior_state.get("last_flows_run_sha", "")
    # Glossary cursor
    state_data["last_glossary_run_sha"] = _prior_state.get("last_glossary_run_sha", "")
    # API Contracts cursor
    state_data["last_api_contracts_run_sha"] = _prior_state.get("last_api_contracts_run_sha", "")
    # Jobs cursor (v26.1.0 A2 pass, additive — no migration needed, state file is additive-tolerant)
    state_data["last_jobs_run_sha"] = _prior_state.get("last_jobs_run_sha", "")
    # Test-cases cursor (v26.1.0 B6 pass, additive — no migration needed)
    state_data["last_test_cases_run_sha"] = _prior_state.get("last_test_cases_run_sha", "")
    # Design-intent cursor (v26.1.0 B5 pass, EXPERIMENTAL/report-only, additive — no migration
    # needed; only ever advanced at D.5, post user-confirmed promotion).
    state_data["last_design_intent_run_sha"] = _prior_state.get("last_design_intent_run_sha", "")

    # Now advance ONLY the active cursor.
    if cursor == "core":
        state_data["last_rebuild_sha"] = run_sha
    elif cursor == "feature-specs":
        state_data["last_feature_spec_run_sha"] = run_sha
    elif cursor == "flows":
        state_data["last_flows_run_sha"] = run_sha
    elif cursor == "glossary":
        state_data["last_glossary_run_sha"] = run_sha
    elif cursor == "api-contracts":
        state_data["last_api_contracts_run_sha"] = run_sha
    elif cursor == "jobs":
        state_data["last_jobs_run_sha"] = run_sha
    elif cursor == "test-cases":
        state_data["last_test_cases_run_sha"] = run_sha
    elif cursor == "design-intent":
        state_data["last_design_intent_run_sha"] = run_sha

    # screen_spec_shas: read from incremental plan snapshot or preserve prior value
    _screen_spec_shas: dict = {}
    if args.incremental_plan_json:
        _plan_path = Path(args.incremental_plan_json)
        if _plan_path.is_file():
            try:
                _plan_data = json.loads(_plan_path.read_text(encoding="utf-8"))
                _snapshot = _plan_data.get("screen_spec_shas_snapshot")
                if _snapshot is not None:
                    _screen_spec_shas = _snapshot
                else:
                    _screen_spec_shas = _prior_state.get("screen_spec_shas", {})
            except (json.JSONDecodeError, OSError):
                _screen_spec_shas = _prior_state.get("screen_spec_shas", {})
        else:
            _screen_spec_shas = _prior_state.get("screen_spec_shas", {})
    else:
        _screen_spec_shas = _prior_state.get("screen_spec_shas", {})

    if _screen_spec_shas is not None:
        state_data["screen_spec_shas"] = _screen_spec_shas

    for out_path, data in [(args.index_out, index_data), (args.state_out, state_data)]:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(str(tmp), str(p))

    return 0


if __name__ == "__main__":
    sys.exit(main())
