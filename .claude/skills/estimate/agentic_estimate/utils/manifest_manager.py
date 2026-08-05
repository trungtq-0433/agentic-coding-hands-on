"""Manage output manifest.json for tracking generated deliverables."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

REQUIRED_OUTPUTS = ("md", "html", "xlsx")
OPTIONAL_OUTPUTS = (
    "assumptions-docx",
    "wbs",
    "proposal",
    "diagrams",
    "breakdown",
    "infra-cost",
    "infra-diagram",
)


def derive_slug(name: str, max_len: int = 40) -> str:
    return name.lower().replace(" ", "-")[:max_len]


def load_manifest(output_dir: Path) -> dict:
    path = output_dir / "manifest.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return _new_manifest(output_dir.name)


def save_manifest(output_dir: Path, manifest: dict):
    to_write = {**manifest, "updated_at": _now_iso()}
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(to_write, indent=2, ensure_ascii=False) + "\n", "utf-8")


def find_or_create_estimate(manifest: dict, json_filename: str, data: dict, timestamp: str) -> dict:
    for est in manifest["estimates"]:
        if est["json"] == json_filename:
            return est

    est_id = re.sub(r"-estimate(?:-\w+)?-\d{6}-\d{4}\.json$", "", json_filename)
    entry = {
        "id": est_id,
        "name": data.get("project_name", est_id),
        "json": json_filename,
        "timestamp": timestamp,
        "outputs": _init_outputs(),
    }
    manifest["estimates"].append(entry)
    return entry


def mark_output(entry: dict, format_key: str, filename: str):
    if format_key in entry["outputs"]:
        entry["outputs"][format_key]["file"] = filename
        entry["outputs"][format_key]["generated"] = True
    else:
        entry["outputs"][format_key] = {
            "required": format_key in REQUIRED_OUTPUTS,
            "file": filename,
            "generated": True,
        }


def mark_breakdown(entry: dict, dir_name: str):
    entry["outputs"]["breakdown"] = {
        "required": False,
        "dir": dir_name,
        "generated": True,
    }


def get_missing(manifest: dict) -> dict:
    result = {}
    for est in manifest["estimates"]:
        missing_req = []
        missing_opt = []
        for key, info in est["outputs"].items():
            if not info.get("generated", False):
                if info.get("required", False):
                    missing_req.append(key)
                else:
                    missing_opt.append(key)
        if missing_req or missing_opt:
            result[est["id"]] = {
                "name": est["name"],
                "required": missing_req,
                "optional": missing_opt,
            }
    return result


def scan_and_build(output_dir: Path) -> dict:
    """Scan an output directory and build manifest from existing files."""
    manifest = load_manifest(output_dir)

    json_files = sorted(output_dir.glob("*-estimate-*.json"))
    if not json_files:
        return manifest

    project_name = manifest.get("project", output_dir.name)
    breakdown_dirs = [
        d for d in sorted(output_dir.iterdir()) if d.is_dir() and d.name.startswith("breakdown")
    ]

    for jf in json_files:
        try:
            data = json.loads(jf.read_text("utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: skipping malformed JSON: {jf}", file=sys.stderr)
            continue
        project_name = data.get("project_name", project_name)

        m = re.search(r"-(\d{6}-\d{4})\.json$", jf.name)
        ts = m.group(1) if m else datetime.now().strftime("%y%m%d-%H%M")

        entry = find_or_create_estimate(manifest, jf.name, data, ts)
        slug = derive_slug(data.get("project_name", "estimate"))

        _scan_standard_outputs(output_dir, entry, slug, ts)
        _scan_translations(output_dir, entry, slug, ts)
        _scan_diagrams(output_dir, entry, ts)
        _scan_breakdowns(breakdown_dirs, entry, data)
        _scan_infra(output_dir, entry)

    manifest["project"] = project_name
    return manifest


def _scan_standard_outputs(output_dir: Path, entry: dict, slug: str, ts: str):
    patterns = {
        "md": f"{slug}-estimate-{ts}.md",
        "html": f"{slug}-estimate-{ts}.html",
        "xlsx": f"{slug}-estimate-interactive-{ts}.xlsx",
        "assumptions-docx": f"{slug}-assumptions-{ts}.docx",
        "wbs": f"{slug}-wbs-{ts}.xlsx",
        "proposal": f"{slug}-proposal-{ts}.docx",
    }
    for fmt, filename in patterns.items():
        if (output_dir / filename).exists():
            mark_output(entry, fmt, filename)


def _scan_translations(output_dir: Path, entry: dict, slug: str, ts: str):
    pattern = f"{slug}-estimate-{ts}-*.md"
    for f in output_dir.glob(pattern):
        m = re.search(rf"-{re.escape(ts)}-(\w+)\.md$", f.name)
        if m:
            mark_output(entry, f"md-{m.group(1)}", f.name)


def _scan_diagrams(output_dir: Path, entry: dict, ts: str):
    est_id = entry.get("id", "")
    for f in sorted(output_dir.glob(f"*-diagrams-{ts}.md")):
        if est_id and est_id in f.name:
            mark_output(entry, "diagrams", f.name)
            return


def _scan_breakdowns(breakdown_dirs: list[Path], entry: dict, data: dict):
    est_name = data.get("project_name", "").lower()
    sub_systems = [s.lower() for s in data.get("parameters", {}).get("sub_systems", [])]

    for d in breakdown_dirs:
        has_index = (d / "breakdown-index.md").exists() or (d / "breakdown.json").exists()
        slug_part = d.name.replace("breakdown-", "").replace("breakdown", "")

        if has_index and (not slug_part or slug_part in est_name or est_name in slug_part):
            mark_breakdown(entry, d.name + "/")
            return

        if any(ss in slug_part or slug_part in ss for ss in sub_systems):
            mark_breakdown(entry, d.name + "/")
            return


def _scan_infra(output_dir: Path, entry: dict):
    infra_dir = output_dir / "infra"
    if not infra_dir.is_dir():
        return
    cost_file = infra_dir / "cost-estimate.md"
    if cost_file.exists():
        mark_output(entry, "infra-cost", f"infra/{cost_file.name}")
    for ext in ("py", "png", "svg"):
        diag_file = infra_dir / f"architecture-diagram.{ext}"
        if diag_file.exists():
            mark_output(entry, "infra-diagram", f"infra/{diag_file.name}")
            break


def _new_manifest(project_name: str) -> dict:
    now = _now_iso()
    return {
        "version": 1,
        "project": project_name,
        "created_at": now,
        "updated_at": now,
        "estimates": [],
    }


def _init_outputs() -> dict:
    outputs = {}
    for key in REQUIRED_OUTPUTS:
        outputs[key] = {"required": True, "file": None, "generated": False}
    for key in OPTIONAL_OUTPUTS:
        if key == "breakdown":
            outputs[key] = {"required": False, "dir": None, "generated": False}
        else:
            outputs[key] = {"required": False, "file": None, "generated": False}
    return outputs


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
