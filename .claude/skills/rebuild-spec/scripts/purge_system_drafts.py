"""CLI: purge aggregate *.draft.md files after a successful system-synthesis promote.

Usage
-----
    python3 purge_system_drafts.py --system-dir docs/<lang>/system --docs-root docs/<lang>

Deletes each ``<name>.draft.md`` in ``--system-dir`` ONLY when its promoted sibling
``<name>.md`` exists on disk (safety invariant: no sibling → promote did not happen
→ draft is preserved).

Exit codes
----------
0  — success (0 or more files deleted)
1  — argument / filesystem error

Stdlib only.  Python 3.9+.
"""
from __future__ import annotations

import argparse
import os
import sys

# Ensure the scripts directory is on the path so the lib import works whether
# this script is run from the scripts/ dir or from the repo root.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _promote_shadow_purge_lib import purge_system_drafts  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Purge aggregate *.draft.md files whose promoted sibling exists. "
            "Run after the promote gate completes (failed==0) to remove stale drafts."
        )
    )
    parser.add_argument(
        "--system-dir",
        required=True,
        help="Absolute or relative path to the docs/<lang>/system/ directory.",
    )
    parser.add_argument(
        "--docs-root",
        required=True,
        help=(
            "Absolute or relative path used as the path-traversal guard boundary "
            "(typically the parent of --system-dir, e.g. docs/<lang>/)."
        ),
    )
    args = parser.parse_args(argv)

    system_dir = os.path.abspath(args.system_dir)
    docs_root = os.path.abspath(args.docs_root)

    if not os.path.isdir(system_dir):
        print(
            f"[ERROR] purge_system_drafts: --system-dir does not exist: {system_dir}",
            file=sys.stderr,
        )
        return 1

    deleted = purge_system_drafts(system_dir, docs_root)
    print(f"[INFO] purge_system_drafts: deleted {len(deleted)} draft(s)")
    for path in deleted:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
