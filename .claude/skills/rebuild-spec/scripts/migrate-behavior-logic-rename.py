#!/usr/bin/env python3
"""Idempotent migration: rename background-logic.md → behavior-logic.md in spec dirs."""
import argparse
import json
import re
import sys
from pathlib import Path


def migrate(spec_root: Path) -> int:
    if not spec_root.is_dir():
        print(f"ERROR: {spec_root} is not a directory", file=sys.stderr)
        return 1

    migrated = 0
    already_done = 0

    for old_path in spec_root.rglob("background-logic.md"):
        new_path = old_path.parent / "behavior-logic.md"
        if new_path.exists():
            print(f"already migrated: {old_path.parent}")
            already_done += 1
            continue
        old_path.rename(new_path)
        print(f"renamed: {old_path} → {new_path}")
        migrated += 1

    # Update internal links in all .md files under spec_root
    pattern = re.compile(r'\bbackground-logic\.md\b')
    write_errors = 0
    for md_file in spec_root.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        new_text = pattern.sub("behavior-logic.md", text)
        if new_text != text:
            try:
                md_file.write_text(new_text, encoding="utf-8")
                print(f"updated links in: {md_file}")
            except OSError as e:
                print(f"warning: cannot update links in {md_file}: {e}", file=sys.stderr)
                write_errors += 1

    # Patch .rebuild-state.json doc_shas key to avoid silent OOB-detection miss
    state_path = spec_root.parent / ".rebuild-state.json"
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            doc_shas = state.get("doc_shas", {})
            if "background-logic.md" in doc_shas:
                doc_shas["behavior-logic.md"] = doc_shas.pop("background-logic.md")
                state["doc_shas"] = doc_shas
                state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print("updated .rebuild-state.json doc_shas key: background-logic.md → behavior-logic.md")
            else:
                print(".rebuild-state.json doc_shas: key already migrated or absent — no change.")
        except OSError as e:
            print(f"warning: cannot update .rebuild-state.json: {e}", file=sys.stderr)
            write_errors += 1

    if already_done > 0 and migrated == 0:
        print("already migrated — no changes needed.")
    else:
        print(f"migrated {migrated} file(s).")
    return 1 if write_errors else 0


def main():
    parser = argparse.ArgumentParser(description="Migrate background-logic.md → behavior-logic.md")
    parser.add_argument("--spec-root", default="./docs/specs", type=Path,
                        help="Root of spec directory (default: ./docs/specs)")
    args = parser.parse_args()
    sys.exit(migrate(args.spec_root))


if __name__ == "__main__":
    main()
