#!/usr/bin/env python3
# layout-exempt: rebuild-spec navigation script — all docs/components paths here are this skill's own output targets
"""Phase C — Navigation layer for rebuild-spec docs output.

Walks the resolved docs root and emits:
  - README.md per docs/ subdir (2-zone: generated block + preserved user content)
  - docs/README.md (top-level reading-order index)
  - docs/components/README.md (when components/ exists with ≥1 state file)

RT-F14: write-safety — all writes through _path_lib._resolve_guarded().

Deterministic, stdlib only. Exit 0 always (advisory).
Heavy helpers live in _nav_lib.py to keep this file under 200 lines.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lang_lib import detect_layout_mode, resolve_docs_root  # noqa: E402
from _nav_components_io import (  # noqa: E402
    _atomic_write, load_component_meta, write_components_index,
)
from _nav_aggregate_lib import build_aggregate_system_readme  # noqa: E402
from _nav_index import (  # noqa: E402
    _is_aggregate_root, build_index_readme, is_bare_docs_root,
    read_primary_lang_from_state, resolve_root_readme_removal,
)
from _nav_lib import (  # noqa: E402
    GEN_END, GEN_START, META_FILES,
    file_description, read_user_tail, subdir_blurb,
)
from _path_lib import _resolve_guarded  # noqa: E402


def _build_readme_content(subdir: Path, docs_root: str, timestamp: str,
                           existing_content: str = "") -> str:
    """Build the generated zone for a subdir README.md (RT-F14 2-zone pattern)."""
    rel = os.path.relpath(str(subdir), docs_root)
    files = sorted(
        f for f in os.listdir(str(subdir))
        if f.endswith(".md") and f not in META_FILES
        and os.path.isfile(str(subdir / f))
    )
    blurb = subdir_blurb(rel)
    lines = [f"# {rel}", ""]
    if blurb:
        lines += [blurb, ""]
    lines += [
        GEN_START,
        f"<!-- rebuild-spec navigation — generated {timestamp} -->",
        "", "## Files", "",
    ]
    if files:
        for fname in files:
            lines.append(f"- [{fname}]({fname}) — {file_description(fname)}")
    else:
        lines.append("_(no markdown files in this directory)_")
    lines += ["", GEN_END]

    user_tail = read_user_tail(existing_content)
    if user_tail and not user_tail.startswith("\n"):
        user_tail = "\n" + user_tail
    content = "\n".join(lines) + user_tail
    return content if content.endswith("\n") else content + "\n"


def _write_index_readme(docs_root: str, lang: str | None, timestamp: str) -> None:
    """Write the top-level reading-order README.md (2-zone, guarded).

    In per-lang mode when docs_root is the bare docs/ root → writes a pointer to
    docs/<primary_lang>/ instead of the full index. In single-lang mode or when
    docs_root is already a lang-scoped root → writes the full index unchanged.
    """
    raw = os.path.join(docs_root, "README.md")
    try:
        guarded = _resolve_guarded(raw, docs_root)
    except ValueError as e:
        print(f"[ERROR] write-safety violation for index README: {e}", file=sys.stderr)
        return
    existing = ""
    if os.path.isfile(guarded):
        try:
            with open(guarded, encoding="utf-8") as f:
                existing = f.read()
        except OSError:
            pass

    # Per-lang mode: the bare docs/ root carries NO README (v18 — was a ~3-line pointer in
    # v15-v17). The single entry point is docs/<primary_lang>/README.md. Remove the generated
    # root index here, but never destroy a hand-written root README.
    primary_lang = read_primary_lang_from_state(docs_root)
    if is_bare_docs_root(docs_root, primary_lang):
        # Read state from this bare root for detect_layout_mode.
        state: dict = {}
        try:
            state = json.loads(
                Path(os.path.join(docs_root, ".rebuild-state.json")).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError, ValueError):
            pass
        mode = detect_layout_mode(primary_lang, docs_base=docs_root, state=state)
        if mode == "per-lang":
            action, body = resolve_root_readme_removal(existing)
            if action == "delete":
                if os.path.isfile(guarded):
                    try:
                        os.remove(guarded)
                    except OSError as e:
                        print(f"[ERROR] cannot remove root README: {e}", file=sys.stderr)
            elif action == "preserve":
                try:
                    _atomic_write(guarded, body)
                except OSError as e:
                    print(f"[ERROR] cannot rewrite root README user tail: {e}", file=sys.stderr)
            # action == "skip" → leave the hand-written file untouched
            return

    # lang may be None — build_index_readme → get_strings → normalize_lang defaults to "en"
    content = build_index_readme(docs_root, lang, timestamp, existing)
    try:
        _atomic_write(guarded, content)
    except OSError as e:
        print(f"[ERROR] cannot write index README: {e}", file=sys.stderr)


def run(docs_root_arg: str | None, pass_complete: bool, lang: str | None = None,
        components_index: bool = False) -> int:
    """Walk docs root, write per-subdir READMEs, the index README, and components index.

    pass_complete is accepted for back-compatibility but is a no-op (DOCUMENT-MAP
    generation was removed in v15.0.0; stale copies are deleted by migration).
    """
    if docs_root_arg:
        docs_root = os.path.realpath(os.path.abspath(docs_root_arg))
    else:
        docs_root = os.path.realpath(os.path.abspath(resolve_docs_root(None)))

    if not os.path.isdir(docs_root):
        print(f"[WARN] docs root not found: {docs_root}", file=sys.stderr)
        return 0

    # Purge stale DOCUMENT-MAP* files from any tier (migration sweep, idempotent).
    from migrate_docs_layout import purge_document_maps  # local import — avoid cycle
    purge_document_maps(Path(docs_root))

    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Write README.md for each immediate subdir (RT-F14 guard on every write)
    try:
        subdirs = sorted(d for d in os.listdir(docs_root)
                         if os.path.isdir(os.path.join(docs_root, d)))
    except OSError as e:
        print(f"[ERROR] cannot list docs root: {e}", file=sys.stderr)
        return 0

    for name in subdirs:
        subdir_path = Path(docs_root) / name
        # Skip README generation for empty subdirs (zero non-meta .md files).
        # Never delete an existing README — only skip writing.
        try:
            md_count = sum(
                1 for f in os.listdir(str(subdir_path))
                if f.endswith(".md") and f not in META_FILES
                and os.path.isfile(str(subdir_path / f))
            )
        except OSError:
            md_count = 0
        if md_count == 0:
            continue
        readme_raw = str(subdir_path / "README.md")
        try:
            guarded = _resolve_guarded(readme_raw, docs_root)
        except ValueError as e:
            print(f"[ERROR] write-safety violation: {e}", file=sys.stderr)
            continue
        existing = ""
        if os.path.isfile(guarded):
            try:
                with open(guarded, encoding="utf-8") as f:
                    existing = f.read()
            except OSError:
                pass
        # Fix 5: aggregate system/ — render in SoS reading order, not alphabetical.
        if (name == "system" and _is_aggregate_root(docs_root)):
            content = build_aggregate_system_readme(str(subdir_path), lang, timestamp, existing)
        else:
            content = _build_readme_content(subdir_path, docs_root, timestamp, existing)
        try:
            _atomic_write(guarded, content)
        except OSError as e:
            print(f"[ERROR] cannot write README for {name}: {e}", file=sys.stderr)

    # Per-feature READMEs + features index (A4/A5) — scoped to docs/features/*/ only,
    # never general recursion. Logic lives in _nav_feature_lib (keeps this file lean).
    from _nav_feature_lib import write_feature_pass  # local import — avoid cycle
    write_feature_pass(docs_root, lang, timestamp)

    # Top-level reading-order index README (always regenerated; 2-zone preserved)
    _write_index_readme(docs_root, lang, timestamp)

    # Components index: explicit flag OR auto-detect (docs/components/ with ≥1 state file)
    comps_root = os.path.join(docs_root, "components")
    if components_index or (os.path.isdir(comps_root) and bool(load_component_meta(comps_root))):
        write_components_index(docs_root, lang, timestamp)

    return 0


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build navigation READMEs for rebuild-spec docs output."
    )
    p.add_argument("--docs-root", default=None,
                   help="Path to docs root (default: resolved via _lang_lib)")
    p.add_argument("--pass-complete", action="store_true",
                   help="[vestigial — no-op since v15.0.0] formerly wrote DOCUMENT-MAP.md")
    p.add_argument("--lang", default=None,
                   help="Language code for the index README labels (default: en). "
                        "Pass with --docs-root docs/<lang> to render a mirror.")
    p.add_argument("--components-index", action="store_true",
                   help="Generate docs/components/README.md + per-component system/README.md "
                        "(auto-detected when docs/components/ exists with ≥1 .rebuild-state.json).")
    args = p.parse_args()
    sys.exit(run(args.docs_root, args.pass_complete, args.lang,
                 components_index=args.components_index))


if __name__ == "__main__":
    main()
