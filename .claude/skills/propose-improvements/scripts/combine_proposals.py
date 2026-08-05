#!/usr/bin/env python3
"""Improvement-proposal Step 5a CLI - combine technical + business proposals.

Authoritative implementation of `claude/skills/propose-improvements/references/combine-proposals.md`.
Replaces the previous `researcher` subagent invocation. The orchestrator calls
this script via Bash; stdout is captured into its log buffer verbatim.

Stdout contract (matches subagent return format):
  - Zero or more `warn:` lines (use-context divergence / marker disagreements).
  - One `done: step-5a -> <abs path>` OR `skip: step-5a (artifact exists at <path>)` line.
  - Exactly one trailer: `Status: DONE` | `Status: DONE_WITH_CONCERNS - <reason>`
    | `Status: BLOCKED - <reason>`.

Exit code: 0 for DONE / DONE_WITH_CONCERNS / skip. Non-zero only for BLOCKED.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import tempfile
from pathlib import Path

# Allow `python combine_proposals.py` invocation without package install.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from combine_lib import (  # noqa: E402
    VALID_USE_CONTEXTS,
    build_combined,
    parse_use_context_marker,
    prepare_track_body,
    validate_paths,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Combine technical + business proposals (Step 5a).",
        allow_abbrev=False,
    )
    p.add_argument("--technical-path", type=Path, default=None,
                   help="Path to plans/improvement-proposal/technical/03-technical-proposal.md.")
    p.add_argument("--business-path", type=Path, default=None,
                   help="Path to plans/improvement-proposal/business/04-business-proposal.md.")
    p.add_argument("--use-context-json", type=Path, default=Path("plans/improvement-proposal/use-context.json"),
                   help="Path to plans/improvement-proposal/use-context.json.")
    p.add_argument("--output", type=Path, default=Path("plans/improvement-proposal/combined-initial.md"),
                   help="Output path for combined-initial.md.")
    p.add_argument("--project-name", type=str, default=None,
                   help="Project name; defaults to CWD basename when omitted.")
    return p.parse_args(argv)


def _print_status(status: str, reason: str = "") -> None:
    if reason:
        print(f"Status: {status} — {reason}")
    else:
        print(f"Status: {status}")


def _read_or_none(path: Path | None) -> str | None:
    if path is None:
        return None
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_use_context_json(path: Path) -> str | None:
    """Return useContext value when JSON parses & validates; None otherwise."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    val = data.get("useContext") if isinstance(data, dict) else None
    if isinstance(val, str) and val.lower() in VALID_USE_CONTEXTS:
        return val.lower()
    return None


def _atomic_write(target: Path, content: str) -> None:
    """Write `content` to `target` atomically via tempfile + os.replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, target)
    except Exception:
        # Best-effort cleanup; replace would have failed before unlink-safe state.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    technical_path: Path | None = args.technical_path
    business_path: Path | None = args.business_path
    output_path: Path = args.output

    # Procedure step 1 (a) - at least one track required.
    if technical_path is None and business_path is None:
        _print_status("BLOCKED", "no track proposal provided")
        return 2

    # Path-safety - reject null bytes + traversal.
    inputs: list[Path] = []
    if technical_path is not None:
        inputs.append(technical_path)
    if business_path is not None:
        inputs.append(business_path)
    inputs.append(args.use_context_json)
    try:
        validate_paths(
            plans_root=Path("plans"),
            output_path=output_path,
            input_paths=inputs,
        )
    except ValueError as exc:
        _print_status("BLOCKED", f"path-safety violation: {exc}")
        return 2

    # Idempotency - skip when output already non-empty.
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"skip: step-5a (artifact exists at {output_path})")
        _print_status("DONE")
        return 0

    # Read each provided track.
    tech_raw = _read_or_none(technical_path)
    biz_raw = _read_or_none(business_path)

    # Procedure step 1 (b) - all provided paths empty/missing -> BLOCKED.
    provided = [(name, raw) for name, raw in (("technical", tech_raw), ("business", biz_raw)) if raw is not None]
    non_empty = [(name, raw) for name, raw in provided if raw is not None and raw.strip()]
    if not non_empty:
        _print_status("BLOCKED", "provided track proposal(s) missing/empty")
        return 2

    # Procedure step 3 - use-context.json (optional source of truth).
    json_use_ctx = _read_use_context_json(args.use_context_json)

    # Procedure step 4 - parse + cross-check markers.
    warns: list[str] = []
    track_markers: dict[str, str | None] = {}
    for name, raw in non_empty:
        track_markers[name] = parse_use_context_marker(raw)

    if "technical" in track_markers and "business" in track_markers:
        t_m, b_m = track_markers["technical"], track_markers["business"]
        if t_m and b_m and t_m != b_m:
            warns.append(
                f"warn: step-5a use-context divergence — technical={t_m}, business={b_m}"
            )

    if json_use_ctx is not None:
        for name, marker in track_markers.items():
            if marker and marker != json_use_ctx:
                warns.append(
                    f"warn: step-5a {name} marker disagrees with use-context.json — {name}={marker}, json={json_use_ctx}"
                )

    # Resolve effective use_context for the header badge.
    if json_use_ctx is not None:
        use_context = json_use_ctx
    else:
        # Fall back to a consistent marker among provided tracks.
        markers = [m for m in track_markers.values() if m]
        use_context = markers[0] if markers and len(set(markers)) == 1 else None

    # Procedure step 5 - per-track: strip H1 + use-context, demote headings.
    tech_body = prepare_track_body(tech_raw) if tech_raw and tech_raw.strip() else None
    biz_body = prepare_track_body(biz_raw) if biz_raw and biz_raw.strip() else None

    # Procedure step 6 - build template.
    project_name = args.project_name or Path.cwd().name
    iso_date = _dt.date.today().isoformat()
    combined = build_combined(
        project_name=project_name,
        iso_date=iso_date,
        use_context=use_context,
        tech_body=tech_body,
        biz_body=biz_body,
    )

    # Procedure step 7 - atomic write.
    _atomic_write(output_path, combined)

    # Emit warns, done, status (in spec order).
    for w in warns:
        print(w)
    print(f"done: step-5a → {output_path.resolve()}")
    if warns:
        _print_status("DONE_WITH_CONCERNS", "; ".join(w[len("warn: "):] for w in warns))
    else:
        _print_status("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
