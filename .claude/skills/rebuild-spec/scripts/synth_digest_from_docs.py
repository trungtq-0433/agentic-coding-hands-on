#!/usr/bin/env python3
"""synth_digest_from_docs.py — Phase 07 (Reuse≠Exclude).

Build a schema-valid neutral _service-digest.json from a reused component's existing docs,
so the synthesis pass treats it like any other component.

Usage:
  python3 synth_digest_from_docs.py \\
      --docs-root <path>         \\  # e.g. employee/docs  (abs or relative to CWD)
      --name <component>         \\  # e.g. employee
      --role <role>              \\  # e.g. service  (from manifest)
      --source-sha <sha>         \\  # from manifest entry source_sha
      --generated-at <iso>       \\  # ISO-8601 UTC (e.g. 2026-06-24T12:00:00Z)
      --out <path>               \\  # output path for _service-digest.json
      [--primary-lang <lang>]       # override primary_lang (default: read from .rebuild-state.json)

The docs root is resolved via the component's .rebuild-state.json primary_lang:
  - primary_lang absent or "en" → docs-root directly (flat)
  - primary_lang "vi"/"jp"/etc  → docs-root/<lang>/

Output MUST pass _system_synthesis_lib._check_caps (self-check; fails loud on violation).
Writes atomically via tmp → os.replace.  Path-guarded.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

# ---------------------------------------------------------------------------
# Ensure scripts/ is importable when run directly
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _reused_digest_parse_lib import parse_route_list, parse_entities, parse_architecture, SIGNAL_INFERRED
from _path_lib import _resolve_guarded
from _system_synthesis_lib import _check_caps


# ---------------------------------------------------------------------------
# Lang-mapped docs root resolution
# ---------------------------------------------------------------------------

def resolve_lang_root(docs_root: str, primary_lang: str | None) -> str:
    """Return the effective docs directory.

    Mirrors the v13.0.0 lang-mapping convention:
    - If docs_root directly contains generated/ or system/ → flat layout → return docs_root.
    - Otherwise check docs_root/<lang>/ and return it if present.
    - For "en", first try flat (legacy), then docs_root/en/ (v13+ per-lang).
    """
    # Flat layout: generated/ or system/ directly under docs_root → no subdir needed
    if (os.path.isdir(os.path.join(docs_root, "generated")) or
            os.path.isdir(os.path.join(docs_root, "system"))):
        return docs_root

    if not primary_lang:
        return docs_root

    lang = primary_lang.lower()

    # Normalise jp → try jp first, then ja
    if lang == "jp":
        jp_dir = os.path.join(docs_root, "jp")
        if os.path.isdir(jp_dir):
            return jp_dir
        alt = os.path.join(docs_root, "ja")
        if os.path.isdir(alt):
            return alt
        return docs_root

    candidate = os.path.join(docs_root, primary_lang)
    if os.path.isdir(candidate):
        return candidate

    return docs_root


def read_primary_lang(docs_root: str) -> str | None:
    """Best-effort read of primary_lang from docs/.rebuild-state.json."""
    state = os.path.join(docs_root, ".rebuild-state.json")
    try:
        with open(state, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            lang = data.get("primary_lang")
            return str(lang) if lang else None
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return None


# ---------------------------------------------------------------------------
# Doc file readers
# ---------------------------------------------------------------------------

def _read_file(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Digest assembly
# ---------------------------------------------------------------------------

def build_digest(
    docs_root: str,
    name: str,
    role: str,
    source_sha: str,
    generated_at: str,
    primary_lang: str | None = None,
) -> dict:
    """Build the neutral digest dict from a reused component's docs.

    Returns a dict matching the neutral-digest schema.  Sections that cannot
    be parsed are represented with empty arrays + a note carrying SIGNAL_INFERRED.
    """
    lang = primary_lang or read_primary_lang(docs_root)
    lang_root = resolve_lang_root(docs_root, lang)

    route_list_text = _read_file(os.path.join(lang_root, "generated", "route-list.md"))
    entities_text = _read_file(os.path.join(lang_root, "generated", "entities.md"))
    arch_text = _read_file(os.path.join(lang_root, "system", "architecture.md"))

    # Parse rpc from route-list (inbound)
    if route_list_text is not None:
        rpc_inbound, rpc_signal = parse_route_list(route_list_text)
    else:
        rpc_inbound, rpc_signal = [], SIGNAL_INFERRED

    # Parse entities
    if entities_text is not None:
        entities, ent_signal = parse_entities(entities_text)
    else:
        entities, ent_signal = [], SIGNAL_INFERRED

    # Parse rpc outbound + topics from architecture (best-effort)
    if arch_text is not None:
        rpc_outbound, topics, arch_signal = parse_architecture(arch_text)
    else:
        rpc_outbound, topics, arch_signal = [], [], SIGNAL_INFERRED

    rpc = rpc_inbound + rpc_outbound

    # Assemble
    digest: dict = {
        "service": name,
        "role": role,
        "generated_at": generated_at,
        "source_sha": source_sha,
        "provenance": "docs-derived",   # Phase 10: signals reused node to renderers
        "rpc": rpc,
        "topic": topics,
        "entity": entities,
    }

    # Attach signal notes (non-schema; stripped by synthesis but useful for humans)
    signals: list[str] = []
    if rpc_signal == SIGNAL_INFERRED:
        signals.append("rpc: " + SIGNAL_INFERRED + " (route-list unparseable or absent)")
    if ent_signal == SIGNAL_INFERRED:
        signals.append("entity: " + SIGNAL_INFERRED + " (entities.md unparseable or absent)")
    if arch_signal == SIGNAL_INFERRED:
        signals.append("arch: " + SIGNAL_INFERRED + " (architecture.md unparseable or absent)")
    if signals:
        digest["_signals"] = signals

    return digest


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def self_check(digest: dict, out_path: str) -> None:
    """Run _check_caps on the assembled digest; raise on violation (fail loud)."""
    _check_caps(digest, out_path)
    # load_digests additionally requires non-empty source_sha and generated_at
    if not digest.get("source_sha"):
        raise ValueError(
            f"synth_digest_from_docs: 'source_sha' is empty — pass a real sha via --source-sha"
        )
    if not digest.get("generated_at"):
        raise ValueError(
            f"synth_digest_from_docs: 'generated_at' is empty — pass an ISO timestamp via --generated-at"
        )


# ---------------------------------------------------------------------------
# Atomic write + path guard
# ---------------------------------------------------------------------------

def write_digest(out_path: str, digest: dict, project_root: str | None = None) -> None:
    """Atomically write digest JSON; path-guarded when project_root provided."""
    abs_out = os.path.realpath(os.path.abspath(out_path))
    if project_root:
        _resolve_guarded(abs_out, project_root)
    dir_ = os.path.dirname(abs_out) or "."
    os.makedirs(dir_, exist_ok=True)
    payload = json.dumps(digest, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix="_synth_digest_tmp_", suffix=".json", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, abs_out)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    import datetime
    p = argparse.ArgumentParser(
        description="Synthesise a neutral _service-digest.json from a reused component's docs."
    )
    p.add_argument("--docs-root", required=True,
                   help="Path to the component's docs/ directory")
    p.add_argument("--name", required=True,
                   help="Component service name (e.g. employee)")
    p.add_argument("--role", default="service",
                   help="Component role (e.g. service / backend / fullstack)")
    p.add_argument("--source-sha", default="",
                   help="Source SHA from manifest entry source_sha")
    p.add_argument("--generated-at", default="",
                   help="ISO-8601 UTC timestamp (default: wall-clock — for manual use only)")
    p.add_argument("--out", required=True,
                   help="Output path for _service-digest.json")
    p.add_argument("--primary-lang", default=None,
                   help="Override primary_lang (default: read from docs/.rebuild-state.json)")
    p.add_argument("--project-root", default=None,
                   help="Project root for path guard (optional)")
    args = p.parse_args(argv)

    # Wall-clock default for manual use only (not used in tests — tests pass --generated-at).
    generated_at = args.generated_at or (
        datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    docs_root = os.path.realpath(os.path.abspath(args.docs_root))
    if not os.path.isdir(docs_root):
        print(f"[ERROR] docs-root does not exist: {docs_root!r}", file=sys.stderr)
        sys.exit(1)

    digest = build_digest(
        docs_root=docs_root,
        name=args.name,
        role=args.role,
        source_sha=args.source_sha,
        generated_at=generated_at,
        primary_lang=args.primary_lang,
    )

    try:
        self_check(digest, args.out)
    except ValueError as exc:
        print(f"[ERROR] digest self-check failed: {exc}", file=sys.stderr)
        sys.exit(1)

    write_digest(args.out, digest, project_root=args.project_root)
    print(json.dumps({
        "status": "ok",
        "out": args.out,
        "service": args.name,
        "rpc_count": len(digest.get("rpc", [])),
        "entity_count": len(digest.get("entity", [])),
        "topic_count": len(digest.get("topic", [])),
        "signals": digest.get("_signals", []),
    }, indent=2))


if __name__ == "__main__":
    main()
