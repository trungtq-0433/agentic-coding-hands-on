#!/usr/bin/env python3
"""Per-component service topology extractor (Phase D).

Reads a component source tree → emits stack-neutral `_service-digest.json`
under <plan-dir>/artifacts/.

Usage:
  extract_service_topology.py --root <component-root> --plan-dir <plan-dir>
      [--profile <id>] [--encoding <enc>]

Adapter dispatch (RT2-F8):
  spring*  → _topology_adapter_spring
  nestjs*  → _topology_adapter_nestjs
  go*      → _topology_adapter_go
  unknown  → topic=[], rpc=[], _signals_note="[SIGNAL_INFERRED]"

Security (RT2-F12): credential-scrub is a SEPARATE pass (see _credential_scrub_lib).
Field-length caps (RT2-F7): service ≤128; rpc/topic/entity name ≤256; array ≤1000.
  Violation → hard reject (no digest written). Exit 0 advisory otherwise.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _extractor_lib import source_tree_hash          # noqa: E402
from _path_lib import component_name                 # noqa: E402
from _credential_scrub_lib import (                  # noqa: E402
    assert_no_secrets,
    scrub_line,
)

# Re-export scrub_line so tests can import it from this module directly.
_scrub_config_line = scrub_line

_SIGNAL_INFERRED = "[SIGNAL_INFERRED]"
_CAP_SERVICE = 128
_CAP_NAME    = 256
_CAP_ARRAY   = 1000

# ---------------------------------------------------------------------------
# Field-length caps (RT2-F7)
# ---------------------------------------------------------------------------

def _check_caps(digest: dict) -> list[str]:
    """Return violation messages (empty = OK). Does NOT truncate silently."""
    errors: list[str] = []
    if len(digest.get("service", "")) > _CAP_SERVICE:
        errors.append(f"service name exceeds {_CAP_SERVICE} chars (RT2-F7)")
    for field in ("rpc", "topic", "entity"):
        arr = digest.get(field, [])
        if len(arr) > _CAP_ARRAY:
            errors.append(f"{field} array exceeds {_CAP_ARRAY} entries (RT2-F7)")
        for item in arr:
            if len(item.get("name", "")) > _CAP_NAME:
                errors.append(f"{field}[].name exceeds {_CAP_NAME} chars (RT2-F7)")
    return errors

# ---------------------------------------------------------------------------
# Adapter dispatch
# ---------------------------------------------------------------------------

def _dispatch_adapter(profile: str, component_root: str) -> dict:
    """Return {"topic":[…],"rpc":[…]} from the matching stack adapter.

    Unknown profile → empty lists + "_inferred": True.
    """
    p = profile.lower()
    if p.startswith("spring"):
        import _topology_adapter_spring as adp
        return adp.extract(component_root)
    if p.startswith("nestjs") or p.startswith("nest"):
        import _topology_adapter_nestjs as adp  # type: ignore[no-redef]
        return adp.extract(component_root)
    if p.startswith("go"):
        import _topology_adapter_go as adp  # type: ignore[no-redef]
        return adp.extract(component_root)
    return {"topic": [], "rpc": [], "_inferred": True}

# ---------------------------------------------------------------------------
# Atomic digest writer
# ---------------------------------------------------------------------------

def _write_digest_atomic(out_path: str, digest: dict) -> None:
    payload = json.dumps(digest, indent=2, ensure_ascii=False)
    dir_ = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(dir_, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="_svc_digest_", suffix=".json.tmp", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, out_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_topology(
    component_root: str,
    plan_dir: str,
    profile: str = "",
    encoding: str = "utf-8",  # noqa: ARG001 — reserved for future adapter use
) -> tuple[int, list[str]]:
    """Extract topology, scrub credentials, validate caps, write digest.

    Returns (exit_code, warnings). exit_code always 0 (advisory).
    """
    warnings: list[str] = []
    root = Path(component_root).resolve()
    if not root.is_dir():
        warnings.append(f"component_root not a directory: {component_root!r}")
        return 0, warnings

    source_sha = source_tree_hash(
        str(root),
        globs=["*.java", "*.kt", "*.go", "*.ts", "*.js", "*.proto",
               "*.yml", "*.yaml", "*.properties", ".env"],
    )

    adapter_result = _dispatch_adapter(profile, str(root))
    inferred = adapter_result.pop("_inferred", False)

    service_name = component_name(
        os.path.relpath(str(root), str(root.parent))
    ) or root.name

    digest: dict = {
        "service": service_name,
        "role": profile or "unknown",
        "generated_at": _now_iso(),
        "source_sha": source_sha,
        "rpc": adapter_result.get("rpc", []),
        "topic": adapter_result.get("topic", []),
        "entity": [],
    }
    if inferred:
        digest["_signals_note"] = _SIGNAL_INFERRED

    # Credential leak guard (RT2-F12): the digest carries only extracted rpc/topic/entity
    # names — assert none of them embed an unredacted credential pattern. (The config-file
    # scrub utilities in _credential_scrub_lib are library-only; no config text is folded
    # into the digest, so there is nothing to scrub-collect here.)
    secret_warns = assert_no_secrets(json.dumps(digest, ensure_ascii=False))
    warnings.extend(secret_warns)

    # Field-length cap check (RT2-F7) — hard reject on violation
    cap_errors = _check_caps(digest)
    if cap_errors:
        for err in cap_errors:
            print(f"[ERROR] {err}", file=sys.stderr)
        warnings.extend(cap_errors)
        return 0, warnings   # no digest written

    artifacts_dir = Path(plan_dir) / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    _write_digest_atomic(str(artifacts_dir / "_service-digest.json"), digest)

    for w in warnings:
        print(f"[WARN] {w}", file=sys.stderr)
    return 0, warnings

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Extract service topology → _service-digest.json (Phase D)"
    )
    p.add_argument("--root",     required=True)
    p.add_argument("--plan-dir", required=True)
    p.add_argument("--profile",  default="")
    p.add_argument("--encoding", default="utf-8")
    args = p.parse_args(argv)
    code, _ = extract_topology(args.root, args.plan_dir, args.profile, args.encoding)
    return code


if __name__ == "__main__":
    sys.exit(main())
