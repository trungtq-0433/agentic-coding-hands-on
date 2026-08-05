#!/usr/bin/env python3
"""Improvement-proposal Step 5c CLI — validation-prep splitter.

Splits combined-initial.md into one per-item payload JSON (carrying ONLY the
proposal item's markdown) + a _manifest.json. The validator self-verifies each
item against the real repo, so there is no evidence / stack-context /
use-context machinery here. The orchestrator calls this script via Bash; stdout
is captured into its log buffer verbatim.

Stdout contract:
  - One `done: step-5c -> <manifest_path>` line OR `skip: step-5c (artifact exists)`.
  - Exactly one trailer: `Status: DONE` | `Status: BLOCKED - <reason>`.

Exit code: 0 for DONE / skip. Non-zero only for BLOCKED.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase_d_prep_lib import (  # noqa: E402
    assert_under_plans,
    compute_sha256,
    parse_items,
    rewrite_h4_to_h2,
    validate_filename_slug,
)


DEDUP_APPLIED_MARKER = "<!-- dedup: applied"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validation-prep splitter (Improvement-proposal Step 5c).",
        allow_abbrev=False,
    )
    p.add_argument("--combined-path", type=Path, required=True)
    p.add_argument("--payloads-dir", type=Path, required=True)
    p.add_argument("--manifest-path", type=Path, required=True)
    p.add_argument("--validation-dir", type=Path, required=True)
    return p.parse_args(argv)


def _print_status(status: str, reason: str = "") -> None:
    if reason:
        print(f"Status: {status} — {reason}")
    else:
        print(f"Status: {status}")


def _atomic_write_json(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
        os.replace(tmp_name, target)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _last_non_blank_line(text: str) -> str:
    for line in reversed(text.splitlines()):
        if line.strip():
            return line
    return ""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    plans_root = Path("plans").resolve()

    # Path-safety on every external path we'll touch.
    for p in [args.combined_path, args.payloads_dir, args.manifest_path, args.validation_dir]:
        try:
            assert_under_plans(p, plans_root)
        except ValueError as exc:
            _print_status("BLOCKED", f"path-safety: {exc}")
            return 2

    # Combined-initial.md presence + dedup-applied marker.
    if not args.combined_path.is_file():
        _print_status("BLOCKED", f"combined missing at {args.combined_path}")
        return 2
    combined_text = args.combined_path.read_text(encoding="utf-8")
    if not _last_non_blank_line(combined_text).startswith(DEDUP_APPLIED_MARKER):
        _print_status("BLOCKED", "combined-initial.md not finalised by step-5b")
        return 2

    current_sha = compute_sha256(combined_text.encode("utf-8"))

    # Idempotency: manifest SHA check.
    if args.manifest_path.exists() and args.manifest_path.stat().st_size > 0:
        try:
            existing = json.loads(args.manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = None
        if isinstance(existing, dict) and existing.get("combined_md_sha256") == current_sha:
            print("skip: step-5c (artifact exists)")
            _print_status("DONE")
            return 0
        # Stale manifest → wipe payloads_dir + manifest, rebuild.
        if args.payloads_dir.is_dir():
            for entry in args.payloads_dir.iterdir():
                if entry.is_file() and (entry.name.startswith("item-") or entry.name == "_manifest.json"):
                    try:
                        entry.unlink()
                    except OSError:
                        pass

    # Parse items. parse_items only emits items under a Technical/Business
    # section, so no track filtering is needed — combine only writes active-track
    # sections. Indices are 1-based doc order as assigned by parse_items.
    items = parse_items(combined_text)

    manifest_items: list[dict] = []
    args.payloads_dir.mkdir(parents=True, exist_ok=True)

    for it in items:
        if not validate_filename_slug(it.slug):
            _print_status("BLOCKED", f"invalid slug for item-{it.index}: {it.slug!r}")
            return 2

        payload_path = args.payloads_dir / f"item-{it.index:02d}-{it.slug}.json"
        output_path = args.validation_dir / f"item-{it.index:02d}-{it.slug}.md"

        # Payload = the proposal item, nothing more. schema_version guards
        # against a future shape the validator wouldn't understand.
        payload = {
            "schema_version": 1,
            "item_markdown": rewrite_h4_to_h2(it.body),
        }
        _atomic_write_json(payload_path, payload)

        manifest_items.append({
            "item_index": it.index,
            "item_slug": it.slug,
            "track": it.track,
            "payload_path": str(payload_path.resolve()),
            "output_path": str(output_path.resolve()),
        })

    # Write manifest LAST (atomic completion marker).
    manifest_payload = {
        "schema_version": 1,
        "combined_md_sha256": current_sha,
        "items": manifest_items,
    }
    _atomic_write_json(args.manifest_path, manifest_payload)

    if not items:
        print(f"done: step-5c (no items) → {args.manifest_path.resolve()}")
    else:
        print(f"done: step-5c → {args.manifest_path.resolve()}")

    _print_status("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
