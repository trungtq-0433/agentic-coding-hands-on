#!/usr/bin/env python3
"""Detect available infrastructure CLI tools.
Output: JSON object with availability, version, and path for each tool.
Exit: always 0 (missing tools is not an error).
"""

import json
import re
import shutil
import subprocess
import sys


def check_tool(name, version_flag="--version"):
    """Check a single tool and return dict with availability info."""
    path = shutil.which(name)
    if not path:
        return {"available": False, "version": None, "path": None}

    version = _extract_version(name, version_flag)
    return {"available": True, "version": version, "path": path}


def _extract_version(name, version_flag):
    """Run tool's version command and extract semver-like string."""
    try:
        result = subprocess.run(
            [name, version_flag],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout or result.stderr
        first_line = output.strip().splitlines()[0] if output.strip() else ""

        # Extract first semver-like pattern
        match = re.search(r"\d+\.\d+(?:\.\d+)?", first_line)
        return match.group(0) if match else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
        return "unknown"


def main():
    tools = {
        "terraform": check_tool("terraform", "version"),
        "infracost": check_tool("infracost", "--version"),
        "oiq": _check_oiq(),
        "tfsec": check_tool("tfsec", "--version"),
        "checkov": check_tool("checkov", "--version"),
    }
    json.dump(tools, sys.stdout, indent=2)
    print()  # trailing newline


def _check_oiq():
    """oiq has no --version flag; just check presence."""
    path = shutil.which("oiq")
    if not path:
        return {"available": False, "version": None, "path": None}
    return {"available": True, "version": None, "path": path}


if __name__ == "__main__":
    main()
