#!/usr/bin/env python3
"""Extract a named H2 section from scout-report.md and write it to a file.

Exit codes: 0 = success, 2 = arg/IO error (file missing or section not found).
Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile


def _resolve_guarded(path: str, base: str) -> str:
    """Resolve path and verify it stays under base. Raises ValueError if not."""
    resolved = os.path.realpath(os.path.abspath(path))
    base_resolved = os.path.realpath(os.path.abspath(base))
    if os.path.commonpath([resolved, base_resolved]) != base_resolved:
        raise ValueError(f"Path traversal detected: {path!r} escapes {base!r}")
    return resolved


def _atomic_write(path: str, content: str) -> None:
    dir_ = os.path.dirname(path) or "."
    os.makedirs(dir_, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".ess_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def extract(scout_path: str, section: str, out_path: str) -> None:
    try:
        with open(scout_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"error: cannot read scout-report: {e}", file=sys.stderr)
        sys.exit(2)

    heading = f"## {section}"
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == heading:
            start = i
            break

    if start is None:
        print(f"error: section {section!r} not found in {scout_path!r}", file=sys.stderr)
        sys.exit(2)

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    content = "".join(lines[start:end])

    try:
        _atomic_write(out_path, content)
    except OSError as e:
        print(f"error: cannot write output: {e}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Extract a named H2 section from scout-report.md."
    )
    p.add_argument("--scout-report", required=True, help="Path to scout-report.md")
    p.add_argument("--section", required=True, help='Section name, e.g. "Background Logic Source Inventory"')
    p.add_argument("--out", default=None, help="Output path (default: <scout-report-dir>/_scout-bl-inventory.md)")
    args = p.parse_args()

    cwd = os.getcwd()

    try:
        scout_path = _resolve_guarded(args.scout_report, cwd)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)

    if args.out:
        try:
            out_path = _resolve_guarded(args.out, cwd)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        scout_dir = os.path.dirname(scout_path)
        out_path = os.path.join(scout_dir, "_scout-bl-inventory.md")

    extract(scout_path, args.section, out_path)


if __name__ == "__main__":
    main()
