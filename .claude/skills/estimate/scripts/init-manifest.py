#!/usr/bin/env python3
"""Scan output directories and build/update manifest.json from existing files.

Usage:
    python3 scripts/init-manifest.py output/mhc-digital-solution/
    python3 scripts/init-manifest.py output/  # all subdirectories
    python3 scripts/init-manifest.py output/ --check  # read-only, show missing
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agentic_estimate.utils.manifest_manager import (  # noqa: E402
    get_missing,
    save_manifest,
    scan_and_build,
)


def main():
    parser = argparse.ArgumentParser(description="Build manifest.json from existing output files")
    parser.add_argument("path", type=Path, help="Output directory or parent of output directories")
    parser.add_argument("--check", action="store_true", help="Show missing outputs without writing")
    args = parser.parse_args()

    target = args.path.resolve()
    dirs_to_process: list[Path] = []

    if list(target.glob("*-estimate-*.json")):
        dirs_to_process.append(target)
    else:
        for child in sorted(target.iterdir()):
            if child.is_dir() and list(child.glob("*-estimate-*.json")):
                dirs_to_process.append(child)

    if not dirs_to_process:
        print("No estimate JSON files found.", file=sys.stderr)
        sys.exit(1)

    for d in dirs_to_process:
        manifest = scan_and_build(d)
        if not manifest["estimates"]:
            continue

        if not args.check:
            save_manifest(d, manifest)

        est_count = len(manifest["estimates"])
        print(f"{d.name}/: {est_count} estimate(s)")

        if args.check:
            missing = get_missing(manifest)
            if missing:
                for est_id, info in missing.items():
                    if info["required"]:
                        print(f"  [{est_id}] MISSING required: {', '.join(info['required'])}")
                    if info["optional"]:
                        print(f"  [{est_id}] available optional: {', '.join(info['optional'])}")
            else:
                print("  All outputs generated.")
        else:
            print(f"  -> {d / 'manifest.json'}")


if __name__ == "__main__":
    main()
