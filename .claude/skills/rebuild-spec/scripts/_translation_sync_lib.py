"""_translation_sync_lib.py — Shared helpers for translation_sync_gate.py.

Extracted to keep the gate script under 200 LOC per project convention.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from _lang_lib import normalize_lang  # noqa: E402

# Doc areas mirrors TR.1 discoverAllPrimaryArtifacts in pipeline-translate.md:108-115
_DOC_AREAS = [
    ("system", "*.md"),
    ("generated", "*.md"),
    ("features", "*/*.md"),
    ("flows", "*.md"),
    ("screens", "*/*.md"),  # [lang-sync-fix] was missing — screen-specs skipped
    # [P05 / D6] Per-component mirrors: docs/<primary>/components/<name>/[.../**]/*.md
    # Component docs are nested: system/*.md, generated/*.md, features/<F>/*.md, flows/*.md.
    # "**/*.md" recurses into all subdirs; draft shadows are excluded in discover_artifacts.
    ("components", "**/*.md"),
]

# Re-sync command template — NEVER append --flows or any pass suffix
RESYNC_CMD = "/tkm:rebuild-spec --lang {lang}"

# Canonical "report missing" string — exact wording from pipeline-translate.md:383-384
REPORT_MISSING_MSG = (
    "⚠ auto-sync did NOT run (no translation-sync-report.json) — secondary mirrors may be stale. "
    "Re-run the pass, or sync manually with /tkm:rebuild-spec --lang <code>."
)


def load_state(path: Path) -> dict:
    """Load .rebuild-state.json; return {} if absent."""
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"cannot read state file {path}: {exc}") from exc


def secondary_langs(state: dict) -> list[str]:
    """Return secondary lang codes (never includes primary_lang).

    Dedupes by canonical (de-aliased) form so a partially-migrated state holding both
    an alias and its canonical key (e.g. `jp` + `ja`) yields ONE entry, not two that
    translate the same language twice. Raw keys are returned (first-seen wins) so
    downstream `translations.get(key)` lookups still resolve.
    """
    translations = state.get("translations") or {}
    primary = normalize_lang(state.get("primary_lang", "en"))
    seen: set[str] = set()
    result: list[str] = []
    for lang in translations:
        try:
            canon = normalize_lang(lang)
        except ValueError:
            continue
        if canon == primary or canon in seen:
            continue
        seen.add(canon)
        result.append(lang)
    return result


def is_stale(entry: dict, primary_cursor_sha: str, pass_name: str) -> bool:
    """A lang is stale when translated_from_sha != primary cursor OR pass not in passes_translated."""
    if entry.get("translated_from_sha") != primary_cursor_sha:
        return True
    if pass_name not in (entry.get("passes_translated") or []):
        return True
    return False


def discover_artifacts(primary_root: Path) -> list[str]:
    """Walk primary doc areas; return relative paths from primary_root.

    Mirrors discoverAllPrimaryArtifacts() in pipeline-translate.md:108-115.
    Includes screens/ — the [lang-sync-fix] omission bug is prevented by this explicit list.
    Draft shadows (<name>.draft.md) are excluded — they are transient write targets and
    must not enter the translation worklist.
    """
    results: list[str] = []
    for subdir, pattern in _DOC_AREAS:
        area = primary_root / subdir
        if area.is_dir():
            for p in sorted(area.glob(pattern)):
                if p.is_file() and not p.name.endswith(".draft.md"):
                    results.append(str(p.relative_to(primary_root)))
    return results


def parse_lang_statuses(raw: list[str]) -> dict[str, dict]:
    """Parse --lang-status entries: <lang>:<status>[:<reason>] → {lang: {status, reason?}}.

    Path-traversal safe: each lang code routed through normalize_lang.
    """
    result: dict[str, dict] = {}
    for entry in raw:
        parts = entry.split(":", 2)
        if len(parts) < 2:
            print(f"[WARN] ignoring malformed --lang-status entry: {entry!r}", file=sys.stderr)
            continue
        lang_raw, status = parts[0], parts[1]
        reason = parts[2] if len(parts) == 3 else None
        try:
            lang = normalize_lang(lang_raw)
        except ValueError as exc:
            print(f"[WARN] skipping unsafe lang code in --lang-status {entry!r}: {exc}", file=sys.stderr)
            continue
        record: dict = {"status": status}
        if reason:
            record["reason"] = reason
        result[lang] = record
    return result


def render_handoff(report: dict) -> str:
    """Render the canonical Secondary languages: handoff line from a report dict.

    Implements the 5 output cases documented in pipeline-translate.md § "5 canonical output cases".
    """
    langs = report.get("languages") or []
    if not langs:
        return "none registered"

    pass_name = report.get("pass", "")
    synced = [e["lang"] for e in langs if e.get("status") == "synced"]
    failed = [e["lang"] for e in langs if e.get("status") == "failed"]
    deferred = [e["lang"] for e in langs if e.get("status") == "deferred"]

    if not failed and not deferred:
        return f"synced {pass_name} → {', '.join(synced)} ({len(synced)}/{len(langs)})"

    parts: list[str] = []
    if synced:
        parts.append(f"synced: {', '.join(synced)}")
    if failed:
        parts.append(f"STALE (failed): {', '.join(failed)}")
    if deferred:
        parts.append(f"STALE (auto-sync off): {', '.join(deferred)}")

    stale = failed + deferred
    resync = " ; ".join(RESYNC_CMD.format(lang=lang) for lang in stale)
    return f"⚠ {' | '.join(parts)} — re-sync stale with {resync}"


def summarize_from_report(report_path: Path) -> str:
    """Read report on disk and return canonical handoff string (all 5 cases).

    Implements the render-from-disk path for all 5 canonical cases
    documented in pipeline-translate.md § "5 canonical output cases".
    """
    if not report_path.is_file() or report_path.stat().st_size == 0:
        return REPORT_MISSING_MSG
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return REPORT_MISSING_MSG
    return render_handoff(report)


def auto_sync_enabled() -> bool:
    """Return False when REBUILD_AUTO_SYNC_TRANSLATIONS=0."""
    return os.environ.get("REBUILD_AUTO_SYNC_TRANSLATIONS", "1") != "0"


def lang_docs_path(primary_root: Path, lang: str, primary_lang: str = "en") -> Path:
    """Return the absolute path of a secondary language's docs root.

    Mode-aware via the top-level `docs/` container, which holds every per-language
    dir. `primary_root` is either that container itself (single-lang / en-at-root,
    name == "docs") or `docs/<primary>/` (per-lang). In both layouts the secondary
    lands at `<docs-container>/<lang>` — never the doubled `docs/docs/<lang>` the
    old single-arg form produced once the primary lived under `docs/<primary>/`.
    """
    lang_n = normalize_lang(lang)
    if primary_root.name == "docs":
        docs_container = primary_root
    elif primary_root.parent.name == "docs":
        docs_container = primary_root.parent
    else:
        # Legacy fallback: treat primary_root as the container's parent join target.
        docs_container = primary_root
    return (docs_container / lang_n).resolve()


def compute_plan_worklist(
    state: dict,
    pass_name: str,
    primary_root: Path,
    stale_file: Path | None,
) -> dict:
    """Build the plan-mode worklist payload (no I/O side-effects).

    Returns the full dict to be JSON-serialised to stdout.
    """
    primary_cursor_sha = state.get("last_rebuild_sha") or ""
    sync_enabled = auto_sync_enabled()
    secondary = secondary_langs(state)
    translations = state.get("translations") or {}

    stale_artifacts: list[str] | None = None
    if stale_file and stale_file.is_file():
        try:
            data = json.loads(stale_file.read_text(encoding="utf-8"))
            stale_artifacts = data.get("changed_artifacts")
        except (json.JSONDecodeError, OSError):
            pass

    all_artifacts = discover_artifacts(primary_root) if primary_root.is_dir() else []

    languages: list[dict] = []
    for lang_raw in secondary:
        try:
            lang = normalize_lang(lang_raw)
        except ValueError as exc:
            print(f"[WARN] skipping invalid lang {lang_raw!r}: {exc}", file=sys.stderr)
            continue

        entry = translations.get(lang_raw) or {}
        is_first = not entry
        stale = is_first or is_stale(entry, primary_cursor_sha, pass_name)

        if not sync_enabled:
            languages.append({"lang": lang, "stale": True, "artifacts_to_translate": [], "deferred": True})
            continue

        arts = all_artifacts if (stale and is_first) else (
            (stale_artifacts if stale_artifacts is not None else all_artifacts) if stale else []
        )
        languages.append({"lang": lang, "stale": stale, "artifacts_to_translate": arts})

    return {
        "schema_version": 1,
        "pass": pass_name,
        "primary_cursor_sha": primary_cursor_sha,
        "auto_sync_enabled": sync_enabled,
        "languages": languages,
    }


def compute_finalize_result(
    state: dict,
    pass_name: str,
    primary_root: Path,
    lang_statuses: dict[str, dict],
) -> tuple[dict, dict]:
    """Verify promoted dirs, update state translations in-place, build report dict.

    Returns (updated_state, report_dict). Caller does the atomic writes.
    Anti-hallucination: "synced" claims without promoted dir are downgraded to "failed".
    """
    primary_cursor_sha = state.get("last_rebuild_sha") or ""
    primary_lang = state.get("primary_lang") or "en"
    translations: dict = state.setdefault("translations", {})

    lang_results: list[dict] = []
    for lang, info in lang_statuses.items():
        status = info.get("status", "failed")
        reason = info.get("reason")

        if status == "synced":
            ld = lang_docs_path(primary_root, lang, primary_lang)
            if not ld.is_dir():
                status = "failed"
                reason = "promoted_dir_missing"

        record: dict = {"lang": lang, "status": status}
        if reason:
            record["reason"] = reason
        lang_results.append(record)

        # (b) Cursor update — SINGLE writer on auto-sync path
        if status == "synced":
            prev = translations.get(lang) or {}
            new_passes = sorted(set(list(prev.get("passes_translated") or []) + [pass_name]))
            translations[lang] = {
                "translated_from_sha": primary_cursor_sha,
                "last_translate_run_sha": primary_cursor_sha,
                "passes_translated": new_passes,
            }

    report: dict = {
        "schema_version": 1,
        "pass": pass_name,
        "primary_cursor_sha": primary_cursor_sha,
        "auto_sync_enabled": auto_sync_enabled(),
        "languages": lang_results,
    }
    return state, report
