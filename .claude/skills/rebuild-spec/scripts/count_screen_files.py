#!/usr/bin/env python3
"""Count screen-tagged lines in scout-report's File Inventory section.

Counts File Inventory entries whose type token is EXACTLY `screen` (tab-delimited).
The match is anchored to a tab + `screen` + (tab | end-of-line) so the sibling tags
`screen-embedded` (TFrame) and `datamodule` (TDataModule) introduced for the Delphi
profile do NOT inflate the visual-screen count and falsely trip the W2 merge threshold.
Prints the integer count to stdout.

Exit codes: 0 = success, 2 = file missing or path traversal.
Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import sys


def main() -> None:
    p = argparse.ArgumentParser(
        description="Count screen-tagged lines in scout-report File Inventory."
    )
    p.add_argument("--scout-report", required=True, help="Path to scout-report.md")
    args = p.parse_args()

    cwd = os.getcwd()
    resolved = os.path.realpath(os.path.abspath(args.scout_report))
    base = os.path.realpath(os.path.abspath(cwd))
    if os.path.commonpath([resolved, base]) != base:
        print(f"error: path traversal detected: {args.scout_report!r}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(resolved, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"error: cannot read scout-report: {e}", file=sys.stderr)
        sys.exit(2)

    # Exact tab-delimited token match: `\tscreen` NOT followed by `-` or a word char.
    # Matches `screen`, `screen\t...`, and `screen [UNVERIFIED]` (binary-.dfm marker).
    # Excludes the sibling tags `screen-embedded` (TFrame) and `datamodule` (TDataModule)
    # so they cannot inflate the visual-screen count.
    count = sum(
        1 for line in content.splitlines() if re.search(r"\tscreen(?![-\w])", line)
    )
    print(count)


if __name__ == "__main__":
    main()
