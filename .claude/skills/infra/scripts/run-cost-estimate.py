#!/usr/bin/env python3
"""Run cost estimation on a Terraform directory.
Usage: run-cost-estimate.py [terraform-dir]
Output: Markdown cost table to stdout.
Tool priority: infracost -> oiq -> heuristic.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
HEURISTIC_FILE = Path(
    os.environ.get("INFRA_HEURISTIC_FILE", SKILL_DIR / "assets" / "pricing-heuristic.json")
)
OIQ_PRICES_FILE = Path(
    os.environ.get("OIQ_PRICES_FILE", Path.home() / ".oiq" / "prices.csv")
)


def main():
    tf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    if not tf_dir.is_dir():
        die(f"Directory not found: {tf_dir}")
    if not list(tf_dir.glob("*.tf")):
        die(f"No .tf files found in: {tf_dir}")

    tool = detect_best_tool()

    if tool == "infracost":
        run_infracost(tf_dir)
    elif tool == "oiq":
        run_oiq(tf_dir)
    else:
        run_heuristic(tf_dir)


# -- Tool detection -----------------------------------------------------------

def detect_best_tool():
    """Detect best available cost estimation tool."""
    tools = _load_tools_json()

    if tools.get("infracost", {}).get("available"):
        return "infracost"
    if tools.get("oiq", {}).get("available") and OIQ_PRICES_FILE.is_file():
        return "oiq"
    return "heuristic"


def _load_tools_json():
    """Run detect-tools.py and parse its JSON output."""
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "detect-tools.py")],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return {}


# -- Infracost ----------------------------------------------------------------

def run_infracost(tf_dir):
    """Run infracost breakdown and output markdown table."""
    version = _get_tool_version("infracost", "--version")

    # Auto-detect tfvars files
    cmd = ["infracost", "breakdown", "--path", str(tf_dir), "--format", "json"]
    for f in list(tf_dir.glob("*.tfvars")) + list(tf_dir.glob("*.tfvars.json")):
        cmd.extend(["--terraform-var-file", str(f)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        die(f"infracost breakdown failed: {e}\nEnsure INFRACOST_API_KEY is set or run: infracost auth login")

    total = float(data.get("totalMonthlyCost") or 0)

    print_table_header()

    # Walk projects -> resources for per-resource rows
    for project in data.get("projects", []):
        for resource in project.get("breakdown", {}).get("resources", []):
            name = resource.get("name", "unknown")
            rtype = resource.get("resourceType", "unknown")
            cost = float(resource.get("monthlyCost") or 0)
            print(f"| {name} | {rtype} | ${cost:.2f} | |")

    print_footer(total, "infracost", version)


# -- OIQ ----------------------------------------------------------------------

def run_oiq(tf_dir):
    """Run oiq match+price pipeline and output markdown table."""
    try:
        match_result = subprocess.run(
            ["oiq", "match", "--tf-dir", str(tf_dir)],
            capture_output=True, text=True, timeout=60
        )
        price_result = subprocess.run(
            ["oiq", "price", "--prices-file", str(OIQ_PRICES_FILE)],
            input=match_result.stdout,
            capture_output=True, text=True, timeout=60
        )
        output = price_result.stdout.strip()
    except subprocess.TimeoutExpired:
        output = ""

    print_table_header()
    total = 0.0

    if not output:
        print("| (oiq produced no output) | — | $0.00 | — |")
    else:
        for line in output.splitlines():
            if not line.strip() or re.match(r"^\s*(Resource|Total|---|\+)", line):
                continue
            parts = line.split()
            if len(parts) < 3 or parts[0] == "UNKNOWN":
                continue
            name, rtype = parts[0], parts[1]
            # Extract last number as cost
            costs = re.findall(r"\d+(?:\.\d+)?", line)
            cost = float(costs[-1]) if costs else 0.0
            total += cost
            print(f"| {name} | {rtype} | ${cost:.2f} | |")

    print_footer(total, "oiq")


# -- Heuristic ----------------------------------------------------------------

def run_heuristic(tf_dir):
    """Estimate costs from pricing-heuristic.json lookup."""
    if not HEURISTIC_FILE.is_file():
        die(f"Heuristic pricing file not found: {HEURISTIC_FILE}")

    heuristics = json.loads(HEURISTIC_FILE.read_text())

    # Collect all resource declarations from .tf files
    resources = []
    for tf_file in tf_dir.glob("*.tf"):
        content = tf_file.read_text()
        for match in re.finditer(r'resource\s+"(aws_[\w-]+)"\s+"([\w-]+)"', content):
            rtype, name = match.group(1), match.group(2)
            # Try to find instance_type in the block
            block_match = re.search(
                rf'resource\s+"{rtype}"\s+"{name}"\s*\{{([^}}]{{0,500}})',
                content, re.DOTALL
            )
            instance_type = None
            if block_match:
                it_match = re.search(
                    r'(?:instance_type|instance_class)\s*=\s*"([^"]+)"',
                    block_match.group(1)
                )
                if it_match:
                    instance_type = it_match.group(1)
            resources.append((rtype, name, instance_type, tf_file))

    print_table_header()
    total = 0.0

    for rtype, name, instance_type, _ in resources:
        entry = heuristics.get(rtype, {})
        cost = float(entry.get("base_monthly", 0))
        note = ""

        if instance_type:
            variant_cost = entry.get("variants", {}).get(instance_type)
            if variant_cost is not None:
                cost = float(variant_cost)
            note = instance_type
        else:
            note = entry.get("note", "")

        total += cost
        print(f"| {name} | {rtype} | ${cost:.2f} | {note} |")

    print()
    print("> **ESTIMATE ONLY — verify with infracost for accurate pricing.**")
    print_footer(total, "heuristic")


# -- Shared output helpers ----------------------------------------------------

def print_table_header():
    print("## Cost Estimate (Monthly USD)\n")
    print("| Resource | Type | Monthly Cost | Notes |")
    print("|----------|------|-------------|-------|")


def print_footer(total, tool, version=None):
    tool_label = f"{tool} {version}" if version else tool
    print(f"\n**Total Estimated:** ${total:.2f}/month")
    print(f"**Tool Used:** {tool_label}")
    print("**Disclaimer:** Estimates only. Actual costs vary by usage, region, and configuration.")


def _get_tool_version(name, flag):
    """Extract version string from a CLI tool."""
    try:
        result = subprocess.run([name, flag], capture_output=True, text=True, timeout=10)
        output = result.stdout or result.stderr
        match = re.search(r"\d+\.\d+\.\d+", output)
        return match.group(0) if match else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
