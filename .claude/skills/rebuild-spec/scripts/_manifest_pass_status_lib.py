"""Per-pass status primitives for the multi-component `--batch` driver (v16.1.0).

Extends the run-plan manifest with a nested `pass_status` field so the driver can
auto-loop the remaining passes (feature-specs / screen-specs / flows / glossary) per
component, the same way core is looped — durable status, failure-isolation, resume.

Design (Hướng A):
- core `status` is UNTOUCHED (byte-identical back-compat); this module only ever reads it.
- `pass_status` / `pass_fail_reason` are nested dicts merged in place (never clobbered).
- A pass is eligible only when core `status == "done"` (reused/excluded loại) AND every
  prereq pass is done. `flows`/`glossary` require `feature-specs`; the others need only core.
- A pass "done" does NOT carry a sha — output is a docs tree, idempotent & disk-verifiable
  (unlike core, which pins the sha of `_service-digest.json`).
- `emit_manifest` is unchanged: `pass_status` absent ≡ all passes pending.

Reuses the lock + atomic-write + timestamp helpers from _components_manifest_lib (DRY).
Stdlib only.
"""
from __future__ import annotations

import json
import os
from typing import Any

from _components_manifest_lib import _now_iso, _atomic_write_json
from _manifest_lock_lib import lock_file, unlock_file


PASS_NAMES = ["feature-specs", "screen-specs", "flows", "glossary", "jobs", "test-cases", "design-intent"]

# Prereqs BEYOND core-done. The driver's `for pass` loop already orders these
# correctly; this map is the safety net inside next_pending_pass.
PASS_PREREQS: dict[str, list[str]] = {
    "feature-specs": [],
    "screen-specs": [],
    "flows": ["feature-specs"],
    "glossary": ["feature-specs"],
    # jobs needs only core (re-projection of behavior-logic.md, same prereq class
    # as screen-specs) — v26.1.0 A2 pass.
    "jobs": [],
    # test-cases needs feature-specs (it EXPANDS technical-spec.md/edge-cases.md,
    # same prereq class as flows/glossary) — v26.1.0 B6 pass.
    "test-cases": ["feature-specs"],
    # design-intent needs only core (architecture.md + business-rules.md + entities.md;
    # no feature-specs dependency — system-level, not feature-level) — v26.1.0 B5 pass,
    # EXPERIMENTAL/report-only. Same prereq class as jobs/screen-specs.
    "design-intent": [],
}


def _validate_pass(pass_name: str) -> None:
    if pass_name not in PASS_NAMES:
        raise ValueError(
            f"Unknown pass {pass_name!r}; expected one of {PASS_NAMES}"
        )


def _prereqs_done(entry: dict[str, Any], pass_name: str) -> bool:
    """True iff every prereq pass for pass_name is done on this entry."""
    pstatus = entry.get("pass_status") or {}
    return all(pstatus.get(p) == "done" for p in PASS_PREREQS[pass_name])


def next_pending_pass(
    manifest: list[dict[str, Any]], pass_name: str
) -> dict[str, Any] | None:
    """First entry eligible for pass_name, or None.

    Eligible ⇔ core ``status == "done"`` (reused/excluded/pending loại) AND every
    prereq pass done AND ``pass_status.get(pass_name, "pending") == "pending"``.
    Raises ValueError if pass_name is unknown.
    """
    _validate_pass(pass_name)
    for entry in manifest:
        if entry.get("status") != "done":
            continue
        if not _prereqs_done(entry, pass_name):
            continue
        pstatus = entry.get("pass_status") or {}
        if pstatus.get(pass_name, "pending") == "pending":
            return entry
    return None


def mark_pass_done(manifest_path: str, comp_path: str, pass_name: str) -> None:
    """Nested-merge pass_status[pass_name]="done"; clear any prior fail reason.

    No sha required (pass output is a verifiable docs tree). Validates pass_name.
    """
    _validate_pass(pass_name)
    _locked_update_pass(manifest_path, comp_path, pass_name, "done")


def mark_pass_failed(
    manifest_path: str, comp_path: str, pass_name: str, reason: str
) -> None:
    """Nested-merge pass_status[pass_name]="failed" + pass_fail_reason[pass_name]=reason."""
    _validate_pass(pass_name)
    _locked_update_pass(manifest_path, comp_path, pass_name, "failed", reason)


def pass_summary(manifest: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """{pass_name: {"done", "pending", "failed", "blocked"}} for the resume report.

    'blocked' = core not done OR a prereq pass not done (not its turn yet).
    """
    summary: dict[str, dict[str, int]] = {
        p: {"done": 0, "pending": 0, "failed": 0, "blocked": 0} for p in PASS_NAMES
    }
    for entry in manifest:
        core_done = entry.get("status") == "done"
        pstatus = entry.get("pass_status") or {}
        for pass_name in PASS_NAMES:
            if not core_done or not _prereqs_done(entry, pass_name):
                summary[pass_name]["blocked"] += 1
                continue
            state = pstatus.get(pass_name, "pending")
            bucket = state if state in ("done", "failed") else "pending"
            summary[pass_name][bucket] += 1
    return summary


def _locked_update_pass(
    manifest_path: str,
    comp_path: str,
    pass_name: str,
    status: str,
    reason: str | None = None,
) -> None:
    """Exclusive-locked read-modify-write of one entry's nested pass status.

    Mirrors _components_manifest_lib._locked_update but merges into nested dicts so
    sibling passes are never clobbered. Raises ValueError if comp_path is absent.
    """
    lock_path = manifest_path + ".lock"
    lock_fd = open(lock_path, "a", encoding="utf-8")
    try:
        lock_file(lock_fd)
        with open(manifest_path, encoding="utf-8") as fh:
            entries = json.load(fh)
        found = False
        for entry in entries:
            if entry.get("path") == comp_path:
                entry.setdefault("pass_status", {})[pass_name] = status
                if status == "failed":
                    entry.setdefault("pass_fail_reason", {})[pass_name] = reason
                else:
                    fail = entry.get("pass_fail_reason")
                    if isinstance(fail, dict):
                        fail.pop(pass_name, None)
                entry["updated_at"] = _now_iso()
                found = True
                break
        if not found:
            raise ValueError(f"No manifest entry with path={comp_path!r}")
        _atomic_write_json(manifest_path, entries)
    finally:
        unlock_file(lock_fd)
        lock_fd.close()
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass
