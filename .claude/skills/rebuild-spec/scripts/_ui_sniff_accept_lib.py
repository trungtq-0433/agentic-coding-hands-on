#!/usr/bin/env python3
"""Tier-2 ui-sniff ACCEPT-path helpers (Phase 09, Track D) -- stdlib-only.

[Red-team fix 3] The accept-path REUSES the existing `dfm-form`/`cobol-screen`
screen-production mechanism -- it invents no new pipeline, template, or
validator code. Two responsibilities live here, kept out of Phase 07's
`_content_sniff_lib.py` so that module stays a pure detector:

  (a) Sparse digest builder -- `build_sparse_screen_recs` / `write_ui_sniff_digest`
      convert user-ACCEPTED Tier-2 sniff signals (see `_content_sniff_lib.sniff_ui`)
      into a minimal `_digest_extract_ui_sniff.json`, using the SAME `ScreenRec`
      shape every other screen extractor emits (Phase 01/02):
      `{screen, kind, reachable, entry_citation, flow_edges, unverified, raw}`.
      EVERY entry is `unverified: True` -- a content sniff can never back a
      verified claim, only a cited lead.

  (b) Session profile-override helper -- `override_profile_for_ui_sniff` returns
      a NEW in-memory profile dict with `screen_source: "ui-sniff"` and the
      `screen-list`/`screen-flow` `artifact_map` actions flipped to `"produce"`
      (the self-consistency rule, `_schema.md:85-89`), so the existing
      `produce()` gate (`pipeline-dispatch-and-gates.md:29-33`) picks it up
      unchanged. `write_profile_override_sidecar` persists that dict to a
      plan-dir sidecar (`<plan-dir>/.ui-sniff-profile-override.json`) so it
      survives across the orchestrator's separate script invocations.

[RT-F5 trust boundary] Neither responsibility EVER writes to
`references/stack-profiles/*.json` -- profiles are loaded ONLY from that kit
directory (`_schema.md` Hard Rule 1) and a project condition (an unrecognized
repo happening to contain UI leads) must never be able to mutate a kit file.
The override is pure in-memory / plan-dir-sidecar only.

Stdlib only.
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _extractor_lib import write_digest_atomic

EXTRACTOR_NAME = "extract_ui_sniff"
SCREEN_KIND = "ui-sniff"
SIDECAR_FILENAME = ".ui-sniff-profile-override.json"

_MAX_SCREEN_NAME_LEN = 80
_MAX_CITATION_LEN = 200  # matches SKILL.md's RT-F10-independent prompt-body cap
_SCREEN_ARTIFACTS = ("screen-list", "screen-flow")


# ---------------------------------------------------------------------------
# (a) Sparse digest builder
# ---------------------------------------------------------------------------

def _sanitize_screen_name(text: str) -> str:
    """Markdown-hostile-char strip + length cap, mirroring the sanitize_identifier
    convention used by every other screen/digest extractor (RT-F10 spirit)."""
    cleaned = text.replace("|", "").replace("`", "").replace("\n", " ").replace("\r", " ").strip()
    return cleaned[:_MAX_SCREEN_NAME_LEN] or "unnamed"


def _sanitize_citation(text: str) -> str:
    """Markdown/prompt-hostile-char strip + length cap for `entry_citation`.

    [fix 10 follow-up] The citation is untrusted content from an unrecognized repo that
    both this digest's `entry_citation` field AND SKILL.md's Tier-2 AskUserQuestion prose
    surface verbatim. SKILL.md wraps it in a single backtick span, but an unsanitized
    backtick in the source text can break out of that delimiter -- strip the same
    Markdown-hostile chars `_sanitize_screen_name` already strips from the `screen` field,
    so `entry_citation` gets the identical treatment rather than being the one unsanitized
    field in this ScreenRec."""
    cleaned = text.replace("|", "").replace("`", "").replace("\n", " ").replace("\r", " ").strip()
    return cleaned[:_MAX_CITATION_LEN]


def _screen_name_from_signal(signal: dict[str, Any], index: int) -> str:
    """Derive a stable, unique, Markdown-safe screen name from a sniff signal.

    One accepted signal == one sparse ScreenRec ("lead"), never merged --
    merging leads would be inventing structure a sniff can't back."""
    citation = str(signal.get("citation", ""))
    relpath = citation.split(":", 1)[0] if citation else "unknown"
    stem = Path(relpath).stem or relpath
    family = str(signal.get("family", "signal"))
    return _sanitize_screen_name(f"{stem}_{family}_{index}")


def build_sparse_screen_recs(signals: list[dict[str, Any]], summary: str = "") -> list[dict[str, Any]]:
    """Convert accepted Tier-2 signals (`{family, token, citation, structural}`,
    `_content_sniff_lib.sniff_ui` shape) into ScreenRec-shaped sparse entries.

    Every entry is `unverified: True` -- a sniff signal is a lead, never a
    verified claim. `reachable` is True only for a `structural` signal
    (menu-loop corroboration is stronger evidence of a real interactive
    surface); every other signal defaults to `reachable: False` (a bare
    keyword hit does not establish reachability)."""
    recs: list[dict[str, Any]] = []
    for idx, signal in enumerate(signals):
        family = signal.get("family", "unknown")
        token = signal.get("token", "")
        structural = bool(signal.get("structural", False))
        recs.append({
            "screen": _screen_name_from_signal(signal, idx),
            "kind": SCREEN_KIND,
            "reachable": structural,
            "entry_citation": _sanitize_citation(str(signal.get("citation", ""))),
            "flow_edges": [],
            "unverified": True,
            "raw": {"family": family, "token": token, "summary": summary},
        })
    return recs


def write_ui_sniff_digest(
    plan_dir: str | Path,
    signals: list[dict[str, Any]],
    summary: str = "",
) -> Path:
    """Build the sparse ScreenRec list + write it atomically as
    `_digest_extract_ui_sniff.json` (same atomic-write contract as every other
    extractor -- `write_digest_atomic`). Returns the written path."""
    screens = build_sparse_screen_recs(signals, summary=summary)
    digest: dict[str, Any] = {
        "extractor": EXTRACTOR_NAME,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "screens": screens,
        "warnings": [] if signals else ["no_accepted_signals"],
    }
    return write_digest_atomic(plan_dir, EXTRACTOR_NAME, digest, shard_name=EXTRACTOR_NAME)


# ---------------------------------------------------------------------------
# (b) Session profile-override helper
# ---------------------------------------------------------------------------

def override_profile_for_ui_sniff(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a NEW profile dict (the input is never mutated) with
    `screen_source: "ui-sniff"` and `screen-list`/`screen-flow` `artifact_map`
    actions flipped to `"produce"` (self-consistency rule, `_schema.md:85-89`).

    Pure in-memory transform -- performs ZERO filesystem I/O. This is what
    keeps the RT-F5 trust boundary intact: nothing here can reach
    `references/stack-profiles/*.json`, on-disk or otherwise."""
    overridden = copy.deepcopy(profile)
    overridden["screen_source"] = "ui-sniff"
    artifact_map = overridden.setdefault("artifact_map", {})
    for artifact in _SCREEN_ARTIFACTS:
        entry = artifact_map.get(artifact)
        if not isinstance(entry, dict):
            entry = {"class": "web"}
        entry["action"] = "produce"
        artifact_map[artifact] = entry
    return overridden


def write_profile_override_sidecar(plan_dir: str | Path, overridden_profile: dict[str, Any]) -> Path:
    """Persist the overridden profile to a PLAN-DIR sidecar
    (`<plan-dir>/.ui-sniff-profile-override.json`) -- never the kit's
    `references/stack-profiles/` directory. Atomic tmp-file + `os.replace`,
    mirroring `write_digest_atomic`'s contract."""
    plan_path = Path(plan_dir)
    plan_path.mkdir(parents=True, exist_ok=True)
    target = plan_path / SIDECAR_FILENAME
    payload = json.dumps(overridden_profile, indent=2, ensure_ascii=False)

    fd, tmp_path = tempfile.mkstemp(
        prefix=".ui-sniff-profile-override_",
        suffix=".json.tmp",
        dir=str(plan_path),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target
