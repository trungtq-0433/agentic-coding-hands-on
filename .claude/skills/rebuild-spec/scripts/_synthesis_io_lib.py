# layout-exempt: rebuild-spec synthesis I/O — all docs/components paths here are this skill's own managed targets
"""I/O helpers for synthesize_system.py (Phase D).

Handles manifest loading, digest-path collection, completeness checking, and
the durable docs/.rebuild-system-state.json writer/reader (Phase R4).
Kept separate so synthesize_system.py stays under 200 lines.

Stdlib only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any

# Schema version for docs/.rebuild-system-state.json. Bump when the shape changes.
SYSTEM_STATE_SCHEMA_VERSION = "1"
SYSTEM_STATE_FILENAME = ".rebuild-system-state.json"


def atomic_write(path: str, content: str) -> None:
    """Write content to path atomically (tmp → os.replace)."""
    dir_ = os.path.dirname(path) or "."
    os.makedirs(dir_, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".synth_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_manifest(manifest_path: str) -> list[dict[str, Any]]:
    """Load .rebuild-components.json; return list of component entries."""
    try:
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] cannot load manifest {manifest_path}: {exc}", file=sys.stderr)
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("components", [])
    return []


def collect_digest_paths(
    root: str,
    digest_dir: str | None,
    max_age_days: int | None,
    components_base: str | None = None,
) -> list[str]:
    """Walk root/docs/components (or digest_dir) and collect _service-digest.json paths.

    ``components_base`` overrides the default ``<root>/docs/components`` search root
    without touching the public ``digest_dir`` polyrepo flag.  Pass it when the
    components layer has been relocated by a per-lang migration (e.g.
    ``<root>/docs/<lang>/components``).  ``digest_dir`` still wins when provided.
    """
    import datetime
    search_base = digest_dir or components_base or os.path.join(root, "docs", "components")
    if not os.path.isdir(search_base):
        return []
    now = datetime.datetime.utcnow()
    paths: list[str] = []
    for dirpath, _dirs, files in os.walk(search_base):
        for fname in files:
            if fname != "_service-digest.json":
                continue
            fpath = os.path.join(dirpath, fname)
            if max_age_days is not None:
                try:
                    age = (now - datetime.datetime.utcfromtimestamp(
                        os.path.getmtime(fpath))).days
                    if age > max_age_days:
                        print(f"[WARN] digest too old ({age}d): {fpath}", file=sys.stderr)
                        continue
                except OSError:
                    pass
            paths.append(fpath)
    return sorted(paths)


def check_completeness(
    manifest_path: str | None,
    digests: list[dict[str, Any]],
    force: bool,
) -> tuple[bool, list[str]]:
    """Return (ok, skipped_names). ok=False means BLOCK (only raised when force=False).

    Satisfied statuses: 'done' or 'reused' (a synthesised digest must be loaded for
    either — a 'reused' entry with NO digest still BLOCKs so the orchestrator runs
    synth_digest_from_docs first).

    'excluded' entries are DROPPED with [WARN] component_excluded:<name> and are NOT
    counted as incomplete (the user explicitly accepted dangling refs).

    Any other status is skipped (counted as incomplete).
    """
    if not manifest_path:
        return True, []
    entries = load_manifest(manifest_path)
    done_svcs = {str(d.get("service", "")) for d in digests}
    skipped: list[str] = []
    for entry in entries:
        name = str(entry.get("name", entry.get("path", "")))
        status = str(entry.get("status", ""))

        if status == "excluded":
            print(f"[WARN] component_excluded:{name}", file=sys.stderr)
            continue  # dropped — not counted as incomplete

        satisfied_statuses = {"done", "reused"}
        if status not in satisfied_statuses:
            skipped.append(name)
            continue

        # status is 'done' or 'reused' — a matching digest must have been loaded.
        svc = str(entry.get("service", name))
        if svc not in done_svcs and name not in done_svcs:
            skipped.append(name)

    if skipped and not force:
        return False, skipped
    return True, skipped


# ---------------------------------------------------------------------------
# Durable root docs-state (Phase R4)
# ---------------------------------------------------------------------------

def write_system_state(docs_base: str, payload: dict[str, Any]) -> None:
    """Atomically write docs/.rebuild-system-state.json.

    ``docs_base`` must be the absolute path to the project's docs/ directory.
    ``payload`` is the caller-supplied dict (see schema below); this function
    adds ``schema_version`` and writes atomically via tmp → os.replace.

    Minimalist schema (KISS — only what index + regen gate need):
    {
      "schema_version": "1",
      "primary_lang": str,
      "synthesis_format_version": str,
      "snapshot_hash": str,
      "generated_at": str,           # ISO-8601 UTC
      "components": [
        {
          "name": str,
          "role": str,
          "reused": bool,
          "source_sha": str,         # empty-string when unavailable
          "mirror_sha": str | null    # optional; digest sha from manifest
        },
        ...
      ]
    }
    """
    state_path = os.path.join(docs_base, SYSTEM_STATE_FILENAME)
    data: dict[str, Any] = {"schema_version": SYSTEM_STATE_SCHEMA_VERSION}
    data.update(payload)
    dir_ = os.path.dirname(os.path.abspath(state_path)) or "."
    os.makedirs(dir_, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=".sysstate_tmp_", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, state_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_system_state(docs_base: str) -> dict[str, Any] | None:
    """Read docs/.rebuild-system-state.json; return parsed dict or None on miss/error."""
    state_path = os.path.join(docs_base, SYSTEM_STATE_FILENAME)
    try:
        with open(state_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] cannot read system state {state_path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    return data
