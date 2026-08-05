#!/usr/bin/env python3
"""parse_speckit_specs.py — W0' spec-reading front-end for migrate-aidd.

Reads a Spec-Kit / SDD project tree and emits:
  <plan-dir>/artifacts/spec-summary.md   — human + researcher evidence
  <plan-dir>/artifacts/_speckit-index.json — machine index for P5 F### mapping

Stdout contract:
  done: parse-speckit -> <abs-path>
  Status: DONE | Status: BLOCKED - <reason>

Exit codes: 0 = success, 2 = arg/IO error.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Allow direct invocation without package install.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from speckit_parse_lib import enumerate_features, find_constitution, parse_spec_md  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_guarded(path: str, base: str) -> str:
    resolved = os.path.realpath(os.path.abspath(path))
    base_resolved = os.path.realpath(os.path.abspath(base))
    if os.path.commonpath([resolved, base_resolved]) != base_resolved:
        raise ValueError(f"Path traversal detected: {path!r} escapes {base!r}")
    return resolved


def _atomic_write(path: str, content: str) -> None:
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".ps_tmp_")
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


def _atomic_write_json(path: str, payload: object) -> None:
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".pj_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        os.rename(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _detect_stack(repo_root: str) -> str:
    """Derive stack from repo manifests. Returns e.g. 'JS/TS', 'PHP', 'Python', etc."""
    manifests = [
        ("package.json", "JS/TS"),
        ("composer.json", "PHP"),
        ("pyproject.toml", "Python"),
        ("requirements.txt", "Python"),
        ("go.mod", "Go"),
        ("pom.xml", "Java"),
        ("Cargo.toml", "Rust"),
    ]
    for filename, stack in manifests:
        if os.path.isfile(os.path.join(repo_root, filename)):
            return stack
    return "UNKNOWN"


def _bool_flag(val: bool) -> str:
    return "yes" if val else "no"


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Parse Spec-Kit specs tree and emit spec-summary.md + _speckit-index.json.",
        allow_abbrev=False,
    )
    p.add_argument("--spec-folder", default=None, help="Informational: original spec folder path.")
    p.add_argument("--plan-dir", required=True, help="Active plan directory path.")
    p.add_argument("--specs-root", default=None, help="Explicit specs root path (overrides --detection-json).")
    p.add_argument("--detection-json", default=None, help="Path to sdd-detection.json to read specsRoot from.")
    p.add_argument("--repo-root", default=None, help="Repo root for stack detection (default: CWD).")
    return p.parse_args(argv)


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    cwd = os.getcwd()
    repo_root = os.path.realpath(args.repo_root) if args.repo_root else cwd

    # Resolve specs_root.
    # NOTE: specs_root is intentionally NOT guarded under repo_root — it is the
    # user's spec folder and is validated upstream by detect_sdd.py
    # (verify_spec_folder: in-repo, no `..`, no null byte) for the --spec-folder
    # path. Reads are read-only and confined to specs_root/NNN-*/. The write
    # boundary (plan_dir below) IS guarded under cwd.
    if args.specs_root:
        specs_root = os.path.realpath(args.specs_root)
    elif args.detection_json:
        try:
            with open(args.detection_json, encoding="utf-8") as f:
                det = json.load(f)
            specs_root_raw = det.get("specsRoot", "")
            if not specs_root_raw:
                print("Status: BLOCKED - detection-json has empty specsRoot", flush=True)
                return 2
            # specsRoot may be relative to repo_root
            if not os.path.isabs(specs_root_raw):
                specs_root = os.path.realpath(os.path.join(repo_root, specs_root_raw))
            else:
                specs_root = os.path.realpath(specs_root_raw)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Status: BLOCKED - cannot read detection-json: {e}", flush=True)
            return 2
    else:
        print("Status: BLOCKED - must supply --specs-root or --detection-json", flush=True)
        return 2

    if not os.path.isdir(specs_root):
        print(f"Status: BLOCKED - specsRoot is not a directory: {specs_root}", flush=True)
        return 2

    # Resolve plan_dir (guarded under cwd)
    try:
        plan_dir = _resolve_guarded(args.plan_dir, cwd)
    except ValueError as e:
        print(f"Status: BLOCKED - {e}", flush=True)
        return 2

    artifacts_dir = os.path.join(plan_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # Enumerate features
    features = enumerate_features(specs_root)

    # Parse each spec.md
    enriched: list[dict] = []
    for feat in features:
        spec_path = os.path.join(specs_root, feat["raw_name"], "spec.md")
        parsed = parse_spec_md(spec_path) if feat["has_spec"] else {"title": "", "us_count": 0, "fr_count": 0}
        enriched.append({**feat, **parsed})

    # Constitution
    constitution_path = find_constitution(repo_root, specs_root)

    # Stack detection
    detected_stack = _detect_stack(repo_root)

    # Build spec-summary.md
    lines: list[str] = [
        "# Spec Summary — migrate-aidd W0'",
        "",
        f"## Detected Language",
        f"{detected_stack}",
        "",
        f"## Source",
        f"- specsRoot: `{specs_root}`",
        f"- constitution: `{constitution_path}`" if constitution_path else "- constitution: not found",
        f"- feature count: {len(enriched)}",
        "",
        "## Features",
        "",
    ]

    for feat in enriched:
        lines.append(f"### {feat['nnn']} — {feat['slug']}")
        lines.append(f"- raw_name: `{feat['raw_name']}`")
        lines.append(f"- has_spec: {_bool_flag(feat['has_spec'])}")
        lines.append(f"- has_plan: {_bool_flag(feat['has_plan'])}")
        lines.append(f"- has_tasks: {_bool_flag(feat['has_tasks'])}")
        lines.append(f"- has_data_model: {_bool_flag(feat['has_data_model'])}")
        lines.append(f"- has_contracts: {_bool_flag(feat['has_contracts'])}")
        if feat.get("contracts_src"):
            lines.append(f"- contracts_src: `{feat['contracts_src']}`")
        lines.append(f"- has_research: {_bool_flag(feat.get('has_research', False))}")
        if feat.get("research_src"):
            lines.append(f"- research_src: `{feat['research_src']}`")
        if feat.get("research_sections"):
            sections_str = ", ".join(feat["research_sections"])
            lines.append(f"- research_sections: {sections_str}")
        if feat["has_spec"]:
            lines.append(f"- title: {feat['title'] or '(none)'}")
            lines.append(f"- us_count: {feat['us_count']}")
            lines.append(f"- fr_count: {feat['fr_count']}")
        lines.append("")

    summary_md = "\n".join(lines)

    # Build _speckit-index.json
    index = {
        "specsRoot": specs_root,
        "detectedStack": detected_stack,
        "features": [
            {
                "nnn": f["nnn"],
                "slug": f["slug"],
                "raw_name": f["raw_name"],
                "has_spec": f["has_spec"],
                "has_plan": f["has_plan"],
                "has_tasks": f["has_tasks"],
                "has_data_model": f["has_data_model"],
                "has_contracts": f["has_contracts"],
                # contracts_src: absolute path to contracts/ dir if present, else null.
                # Used by W0'/W6 researcher to copy contracts verbatim to
                # artifacts/features/{slug}/contracts/ (auto-promoted by promote_drafts).
                "contracts_src": f.get("contracts_src"),
                # research.md presence + sections for spec-URI anchors (spec://NNN/research.md#section)
                "has_research": f.get("has_research", False),
                "research_src": f.get("research_src"),
                "research_sections": f.get("research_sections", []),
            }
            for f in enriched
        ],
    }

    # Write outputs
    summary_path = os.path.join(artifacts_dir, "spec-summary.md")
    index_path = os.path.join(artifacts_dir, "_speckit-index.json")

    try:
        _atomic_write(summary_path, summary_md)
        _atomic_write_json(index_path, index)
    except OSError as e:
        print(f"Status: BLOCKED - write error: {e}", flush=True)
        return 2

    print(f"done: parse-speckit -> {os.path.abspath(summary_path)}", flush=True)
    print("Status: DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run())
