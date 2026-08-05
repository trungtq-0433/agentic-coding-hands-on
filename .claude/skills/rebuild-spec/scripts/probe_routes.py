#!/usr/bin/env python3
"""Tier-1 CLI route probe — runs framework-native route listers and writes a route manifest.

Exit code: always 0 (advisory — never halts the pipeline).
Stdout: JSON status object.

Stdlib only. Parsers and manifest writer live in _probe_routes_lib.py.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any  # used in _binary_present / probe return type

from _probe_routes_lib import LISTERS, parse_json_output, parse_text_output, write_manifest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROBE_TIMEOUT_S = 60
# Hard ceiling on child stdout bytes.  A hostile or runaway route-lister (e.g. a
# debug build that emits unbounded JSON) would otherwise buffer multi-GB before the
# 60-second wall-clock timeout fires.  Hitting this cap kills the process immediately
# and returns tier1_failed — the manifest is advisory, so truncation beats OOM.
MAX_PROBE_OUTPUT_BYTES = 10_000_000  # 10 MB


# ---------------------------------------------------------------------------
# Bootability classification
# ---------------------------------------------------------------------------

def _detect_file_present(root: Path, detect_file: object) -> bool:
    """Check if detect_file condition is met.

    Supports three forms:
    - str: simple file existence check (root / detect_file).is_file()
    - tuple (primary, alternatives): primary file must exist AND at least one
      alternative from the alternatives tuple must exist. Used by Django:
      manage.py is not a bootability signal on its own; a dep manifest is required.
    """
    if isinstance(detect_file, str):
        return (root / detect_file).is_file()
    if isinstance(detect_file, tuple):
        primary, alternatives = detect_file[0], detect_file[1]
        if not (root / primary).is_file():
            return False
        if isinstance(alternatives, str):
            return (root / alternatives).is_file()
        # alternatives is a tuple of filenames — require at least one
        return any((root / alt).is_file() for alt in alternatives)
    return False


def classify_bootable(root: Path) -> list[str]:
    """Return stack keys that are bootable-first-class (own lockfile/manifest present).

    Embedded-no-boot stacks (ColdFusion etc.) are never in LISTERS.
    Deduplicates while preserving order (laravel+symfony share composer.lock;
    disambiguation by entrypoint presence happens in _probe_stack).
    Django requires manage.py AND a dep manifest (see _detect_file_present).
    """
    seen: set[str] = set()
    result: list[str] = []
    for stack, defn in LISTERS.items():
        detect_file = defn.get("detect_file")
        if detect_file and _detect_file_present(root, detect_file) and stack not in seen:
            seen.add(stack)
            result.append(stack)
    return result


# ---------------------------------------------------------------------------
# Binary presence check
# ---------------------------------------------------------------------------

def _binary_present(defn: dict[str, Any], root: Path) -> bool:
    if defn.get("detect_binary"):
        local = root / defn["detect_binary"]
        if local.exists():
            return True
        if shutil.which(defn["detect_binary"]):
            return True
        return False
    if defn.get("detect_which"):
        return bool(shutil.which(defn["detect_which"]))
    return True


# ---------------------------------------------------------------------------
# Per-stack probe runner
# ---------------------------------------------------------------------------

def _probe_stack(stack: str, root: Path) -> tuple[str, list[dict[str, str]]]:
    """Run the lister for one stack. Returns (status, routes).

    status: "tier1_ok" | "tier1_failed"
    Never raises — all errors map to tier1_failed.

    Stdout is read incrementally via Popen and capped at MAX_PROBE_OUTPUT_BYTES.
    A runaway child that emits unbounded output is killed before the cap is exhausted,
    avoiding OOM on hostile or pathological route-lister binaries.
    """
    defn = LISTERS[stack]
    if not _binary_present(defn, root):
        return "tier1_failed", []

    try:
        proc = subprocess.Popen(
            defn["cmd"],
            cwd=str(root),
            stdout=subprocess.PIPE,
            # DEVNULL, not PIPE: stderr is never read, and an undrained pipe
            # deadlocks the child once its 64KB buffer fills (probe is advisory).
            stderr=subprocess.DEVNULL,
            shell=False,  # SECURITY: fixed argv from LISTERS, no shell interpolation
        )
    except (FileNotFoundError, OSError):
        return "tier1_failed", []

    chunks: list[bytes] = []
    total = 0
    cap_hit = False
    try:
        assert proc.stdout is not None  # guaranteed by stdout=PIPE
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_PROBE_OUTPUT_BYTES:
                # Output exceeds hard ceiling — kill immediately and bail.
                proc.kill()
                cap_hit = True
                break
            chunks.append(chunk)
        try:
            proc.wait(timeout=PROBE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            return "tier1_failed", []
    except OSError:
        proc.kill()
        return "tier1_failed", []

    if cap_hit:
        return "tier1_failed", []

    if proc.returncode != 0:
        return "tier1_failed", []

    stdout_text = b"".join(chunks).decode("utf-8", errors="replace")
    fmt = defn.get("format", "text")
    routes = (
        parse_json_output(stdout_text, stack)
        if fmt == "json"
        else parse_text_output(stdout_text, stack)
    )
    return ("tier1_ok", routes) if routes else ("tier1_failed", [])


# ---------------------------------------------------------------------------
# Main probe orchestrator
# ---------------------------------------------------------------------------

def probe(
    project_root: Path,
    plan_dir: Path,
    stacks: list[str] | None = None,
) -> dict[str, Any]:
    """Run the Tier-1 probe and return a status dict (exit 0 always)."""
    bootable = classify_bootable(project_root)

    if stacks:
        requested = [s.strip().lower() for s in stacks if s.strip()]
        to_probe = [s for s in requested if s in LISTERS and s in bootable]
        skipped_unknown = [s for s in requested if s not in LISTERS]
    else:
        to_probe = bootable
        skipped_unknown = []

    if not to_probe:
        return {
            "status": "skipped",
            "manifest_path": None,
            "stacks_probed": [],
            "per_stack": {},
            "note": (
                "No bootable stacks with known listers detected."
                if not stacks
                else f"Requested stacks {stacks!r} not in bootable set {bootable!r}."
            ),
        }

    all_routes: list[dict[str, str]] = []
    per_stack: dict[str, Any] = {}

    for stack in to_probe:
        status, routes = _probe_stack(stack, project_root)
        per_stack[stack] = {"status": status, "route_count": len(routes)}
        if status == "tier1_ok":
            all_routes.extend(routes)

    for s in skipped_unknown:
        per_stack[s] = {"status": "skipped", "route_count": 0, "note": "stack not in LISTERS"}

    any_ok = any(v["status"] == "tier1_ok" for v in per_stack.values())
    overall_status = "tier1_ok" if any_ok else "tier1_failed"

    manifest_path: Path | None = None
    if all_routes:
        manifest_path = write_manifest(all_routes, plan_dir)

    return {
        "status": overall_status,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "stacks_probed": list(per_stack.keys()),
        "per_stack": per_stack,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tier-1 CLI route probe — runs framework listers, writes route-manifest.",
    )
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--stacks", default="", help="Comma-separated stack list from scout.")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    plan = Path(args.plan_dir).resolve()
    stacks = [s.strip() for s in args.stacks.split(",") if s.strip()] if args.stacks else []

    result = probe(root, plan, stacks or None)
    print(json.dumps(result))
    return 0  # Always exit 0 — advisory, never halts pipeline


if __name__ == "__main__":
    sys.exit(main())
