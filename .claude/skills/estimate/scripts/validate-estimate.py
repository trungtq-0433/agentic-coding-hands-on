#!/usr/bin/env python3
"""Validate estimation JSON against knowledge base rules.

Checks:
  - All requirements have estimates
  - No task exceeds 13 SP (suggests splits)
  - Buffer >= 10%
  - SP/Man-Days ratio ~0.5 (±30%)
  - Total SP reasonable (< 500)
  - Assumptions documented

Usage:
    python skills/estimate/scripts/validate-estimate.py estimate.json
    python skills/estimate/scripts/validate-estimate.py estimate.json --strict
"""

import argparse
import json
import sys
from pathlib import Path

from validate_checks import validate


def load_estimate(path: str) -> dict:
    """Load and parse estimation JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Validate estimation JSON against knowledge base rules",
    )
    parser.add_argument("file", help="Path to estimation JSON file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings too (default: fail on errors only)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    try:
        data = load_estimate(args.file)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    result = validate(data, strict=args.strict)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASSED" if result["passed"] else "FAILED"
        print(f"Validation: {status} ({result['errors']} errors, {result['warnings']} warnings)")
        for issue in result["issues"]:
            icon = "✗" if issue["severity"] == "error" else "⚠"
            prefix = (
                f"[{issue.get('id', issue['check'])}]" if "id" in issue else f"[{issue['check']}]"
            )
            print(f"  {icon} {prefix} {issue['message']}")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
