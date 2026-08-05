"""Guard script: fail if any claude/skills/** file contains a hardcoded
docs/system|features|generated|flows|screens path without a layout-exempt annotation.

Exit 0  — all clear.
Exit 1  — one or more un-exempt hardcoded paths found (prints each offending
           file:line to stdout).

Usage:
    python3 check_layout_paths.py [--root <skills-root>]

    --root  Path to the skills directory to scan (default: <repo>/claude/skills).
            The script resolves the repo root as the grandparent of this file's
            directory (scripts/ → rebuild-spec/ → skills/).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that flag a hardcoded docs-namespace path. These are exactly the
# generated/promoted language layers that migrate_docs_layout.py relocates on a
# per-lang flip (LANGUAGE_LAYERS) — they must agree, so `screens` and `components`
# are covered too (v15.0.0 adds components as a first-class language layer).
_HARDCODED = re.compile(
    r"\bdocs/(system|features|generated|flows|screens|components)\b"
)

# Annotation that marks a line (or the line immediately preceding it) as exempt.
_EXEMPT_INLINE = re.compile(r"layout-exempt")

# File extensions to scan.
_SCAN_EXTS = {".md", ".py", ".sh", ".txt", ".yaml", ".yml", ".json"}

# Directories to skip during traversal.
_PRUNE = frozenset({
    "__pycache__", ".venv", "venv", ".git", "node_modules",
    "dist", "build", ".pytest_cache", ".tox",
})


def _default_root() -> Path:
    """Resolve <repo>/claude/skills from this script's location."""
    # This file lives at <repo>/.claude/skills/rebuild-spec/scripts/
    # Claude's canonical source tree is <repo>/claude/ (no dot prefix).
    # Walk up: scripts/ → rebuild-spec/ → skills/ → .claude/ → repo-root
    here = Path(__file__).resolve()
    # scripts/ → rebuild-spec/ → skills/ → .claude/
    claude_skills = here.parent.parent.parent  # .claude/skills/
    repo_root = claude_skills.parent.parent     # repo root
    candidate = repo_root / "claude" / "skills"
    if candidate.is_dir():
        return candidate
    # Fallback: try the .claude shadow (e.g. running from the shadow tree).
    return claude_skills


def scan(root: Path) -> list[tuple[Path, int, str]]:
    """Return a list of (file, line_number, line_text) for offending lines."""
    offences: list[tuple[Path, int, str]] = []
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            entries = list(cur.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in _PRUNE:
                    stack.append(entry)
            elif entry.is_file() and entry.suffix.lower() in _SCAN_EXTS:
                _check_file(entry, offences)
    return offences


def _check_file(path: Path, offences: list[tuple[Path, int, str]]) -> None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return

    # File-level exemption: if a layout-exempt annotation appears within the first
    # 20 lines of the file, the entire file is exempt. This covers ownership-level
    # annotations like "# layout-exempt: rebuild-spec script — all paths are this
    # skill's own managed targets" placed at the top of a file or just after a
    # module docstring.
    for fl in lines[:50]:
        if _EXEMPT_INLINE.search(fl):
            return  # Entire file is exempt.

    # Build a set of exempt line indices (0-based) by scanning for block-level
    # exemptions: a layout-exempt annotation covers all subsequent lines until
    # a blank line or a non-table, non-code line breaks the block (up to 50 lines).
    exempt_set: set[int] = set()
    i = 0
    while i < len(lines):
        if _EXEMPT_INLINE.search(lines[i]):
            # Propagate forward while lines look like they are in the same block
            # (table rows, code fence lines, or non-blank continuation lines).
            j = i + 1
            while j < len(lines) and j - i <= 50:
                l = lines[j]
                # Stop propagating on an empty line that precedes a non-table line.
                if not l.strip():
                    # Peek: if next non-empty line is not a table row, stop.
                    k = j + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k >= len(lines) or not lines[k].startswith("|"):
                        break
                exempt_set.add(j)
                j += 1
        i += 1

    for i, line in enumerate(lines, start=1):
        if not _HARDCODED.search(line):
            continue
        # Check current line for an inline exemption annotation.
        if _EXEMPT_INLINE.search(line):
            continue
        # Check the immediately preceding line for a "near-line" exemption.
        if i >= 2 and _EXEMPT_INLINE.search(lines[i - 2]):
            continue
        # Check block-level exemption (propagated from a preceding exempt annotation).
        if (i - 1) in exempt_set:
            continue
        offences.append((path, i, line.rstrip()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for un-exempt hardcoded docs/system|features|generated|flows|screens paths."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Skills root directory to scan (default: <repo>/claude/skills).",
    )
    args = parser.parse_args()

    root = (args.root or _default_root()).resolve()
    if not root.is_dir():
        print(f"ERROR: root directory does not exist: {root}", file=sys.stderr)
        return 1

    offences = scan(root)
    if not offences:
        print("check_layout_paths: OK — no un-exempt hardcoded docs layout paths found.")
        return 0

    print("check_layout_paths: FAIL — un-exempt hardcoded docs layout paths detected:")
    for path, lineno, text in sorted(offences, key=lambda t: (str(t[0]), t[1])):
        print(f"  {path}:{lineno}: {text}")
    print(
        "\nFix: add '# layout-exempt' (or '<!-- layout-exempt -->') on or before the offending line,"
        "\nor add a docs-root pointer to _shared/docs-canonical-mapping.md § Language Layout."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
