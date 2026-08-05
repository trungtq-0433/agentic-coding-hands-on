"""Load, validate, and manage historical calibration entries."""

import fnmatch
import functools
import logging
import re
from pathlib import Path

import yaml

from agentic_estimate.utils.knowledge_base_loader_yaml_config import (
    _get_project_root,
    _load_yaml,
)
from agentic_estimate.utils.schema_validator_jsonschema import validate_against_schema

logger = logging.getLogger(__name__)

HISTORICAL_DIR = "knowledge-base/historical"
SCHEMA_PATH = "knowledge-base/historical/_schema.yaml"
CONFIG_PATH = "knowledge-base/historical/calibration-config.yaml"
ENTRY_SCHEMA_PATH = "schemas/historical-entry-schema.json"


@functools.lru_cache(maxsize=1)
def _load_schema_config() -> dict:
    return _load_yaml(SCHEMA_PATH)


@functools.lru_cache(maxsize=1)
def _load_calibration_config() -> dict:
    return _load_yaml(CONFIG_PATH)


def clear_caches():
    """Clear all LRU caches. Call in tests to avoid cross-test contamination."""
    _load_schema_config.cache_clear()
    _load_calibration_config.cache_clear()
    _load_yaml.cache_clear()


def get_task_type_aliases() -> dict:
    return _load_schema_config().get("task_type_aliases", {})


def classify_task_type(task_name: str, aliases: dict | None = None) -> str | None:
    """Match a free-text task name to a KB category key.

    Uses case-insensitive matching with glob-style wildcards.
    Returns the category key or None if no match.
    """
    if not task_name:
        return None

    if aliases is None:
        aliases = get_task_type_aliases()

    name_lower = task_name.lower().strip()

    # Exact category key match
    if name_lower in aliases:
        return name_lower

    for category, patterns in aliases.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if fnmatch.fnmatch(name_lower, pattern_lower):
                return category
            if pattern_lower in name_lower:
                return category

    return None


def sanitize_entry(data: dict) -> dict:
    """Remove client-identifiable fields per sanitization rules."""
    schema_config = _load_schema_config()
    stripped = schema_config.get("sanitization", {}).get("stripped_fields", [])

    sanitized = {}
    for key, value in data.items():
        if key in stripped:
            continue
        if isinstance(value, dict):
            sanitized[key] = {k: v for k, v in value.items() if k not in stripped}
        else:
            sanitized[key] = value

    return sanitized


def _generate_slug(existing_dir: Path) -> str:
    """Auto-increment project-NNN slug based on existing entries."""
    max_n = 0
    for subdir in [existing_dir.parent / "accepted", existing_dir.parent / "actuals"]:
        if not subdir.exists():
            continue
        for f in subdir.glob("project-*.yaml"):
            match = re.match(r"project-(\d+)", f.stem)
            if match:
                max_n = max(max_n, int(match.group(1)))
    return f"project-{max_n + 1:03d}"


def get_slug(name: str) -> str:
    """Slugify a name for use as filename."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:40] if slug else "unnamed"


def normalize_estimate_json(
    data: dict,
    entry_type: str = "accepted",
    project_meta: dict | None = None,
    slug: str | None = None,
) -> dict:
    """Convert estimate-output-schema JSON to canonical historical entry.

    Args:
        data: Estimate JSON matching estimate-output-schema.json
        entry_type: "accepted" or "actual"
        project_meta: Optional dict with domain, tech_stack, team_size, team_experience
        slug: Anonymous project slug (auto-generated if None)
    """
    project_meta = project_meta or {}
    hist_dir = _get_project_root() / HISTORICAL_DIR

    if not slug:
        slug = _generate_slug(hist_dir)

    project_date = data.get("generated_date", "")

    project = {"name": slug, "date": project_date}
    if project_meta.get("domain"):
        project["domain"] = project_meta["domain"]
    if project_meta.get("tech_stack"):
        project["tech_stack"] = project_meta["tech_stack"]
    if project_meta.get("team_size"):
        project["team_size"] = int(project_meta["team_size"])
    if project_meta.get("team_experience"):
        project["team_experience"] = project_meta["team_experience"]

    tasks = []
    aliases = get_task_type_aliases()

    options = data.get("options", [])
    if options:
        first_option = options[0]
        raw_tasks = _extract_tasks_from_option(first_option)
        for t in raw_tasks:
            task_type = classify_task_type(t["name"], aliases) or "unclassified"
            task_entry = {"task_type": task_type, "total_md": t["total_md"]}
            if t.get("story_points"):
                task_entry["story_points"] = t["story_points"]
            if t.get("effort"):
                task_entry["effort"] = t["effort"]
            tasks.append(task_entry)

    total_md = sum(t["total_md"] for t in tasks)

    estimate = {"total_md": total_md, "tasks": tasks}

    multipliers = data.get("parameters", {}).get("project_multipliers")
    if multipliers:
        estimate["multipliers_used"] = [
            {"name": m["name"], "key": m.get("key", ""), "value": m["value"]} for m in multipliers
        ]

    entry = {
        "version": "1.0",
        "type": entry_type,
        "project": project,
        "estimate": estimate,
    }

    return sanitize_entry(entry)


def _extract_tasks_from_option(option: dict) -> list[dict]:
    """Extract flat task list from either categories[] or tasks[] structure."""
    raw_tasks = []

    categories = option.get("categories", [])
    if categories:
        for cat in categories:
            for t in cat.get("tasks", []):
                raw_tasks.append(_map_task(t))
    else:
        for t in option.get("tasks", []):
            raw_tasks.append(_map_task(t))

    return raw_tasks


def _map_task(task: dict) -> dict:
    """Extract relevant fields from an estimate task."""
    effort_by_role = {}
    for role, role_data in task.get("effort", {}).items():
        if isinstance(role_data, dict):
            md = role_data.get("md", 0)
        else:
            md = role_data
        if md > 0:
            effort_by_role[role] = md

    return {
        "name": task.get("name", ""),
        "total_md": task.get("total_md", 0),
        "story_points": task.get("story_points", 0),
        "effort": effort_by_role,
    }


def load_historical_entry(path: Path) -> dict:
    """Load a single canonical YAML entry."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_all_entries(type_filter: str | None = None) -> list[dict]:
    """Load all historical entries, optionally filtered by type.

    Returns entries sorted by project.date descending.
    Gracefully skips malformed files.
    """
    hist_dir = _get_project_root() / HISTORICAL_DIR
    entries = []

    dirs_to_scan = []
    if type_filter == "accepted":
        dirs_to_scan = [hist_dir / "accepted"]
    elif type_filter == "actual":
        dirs_to_scan = [hist_dir / "actuals"]
    else:
        dirs_to_scan = [hist_dir / "accepted", hist_dir / "actuals"]

    for scan_dir in dirs_to_scan:
        if not scan_dir.exists():
            continue
        for f in scan_dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue
            try:
                entry = load_historical_entry(f)
                if entry and isinstance(entry, dict):
                    entries.append(entry)
            except Exception as exc:
                logger.warning("Skipping malformed entry %s: %s", f.name, exc)
                continue

    entries.sort(
        key=lambda e: e.get("project", {}).get("date", ""),
        reverse=True,
    )
    return entries


def validate_entry(data: dict) -> tuple[bool, list[str]]:
    """Validate a historical entry against the JSON Schema."""
    return validate_against_schema(data, ENTRY_SCHEMA_PATH)


def detect_column_mapping(headers: list[str], sample_rows: list[list]) -> dict:
    """Heuristically detect column mapping from Excel/CSV headers.

    Returns dict with task_name, total_md, story_points, roles, confidence.
    """
    h_lower = [str(h).lower().strip() for h in headers]

    name_keywords = ["task", "feature", "item", "name", "description", "function"]
    md_keywords = ["md", "man-day", "man day", "effort", "days", "estimate", "total"]
    sp_keywords = ["sp", "story point", "point", "story"]
    role_keywords = {
        "be": ["be", "backend", "back-end", "server"],
        "fe": ["fe", "frontend", "front-end", "client"],
        "qa_manual": ["qa", "test", "quality"],
        "design": ["design", "ui/ux", "ux"],
        "infra": ["infra", "devops", "ops"],
        "pm": ["pm", "project manager"],
        "brse": ["brse", "bridge"],
    }

    mapping: dict = {
        "task_name": None,
        "total_md": None,
        "story_points": None,
        "roles": {},
        "confidence": "low",
    }

    matches = 0

    for i, h in enumerate(h_lower):
        if mapping["task_name"] is None:
            if any(kw in h for kw in name_keywords):
                mapping["task_name"] = headers[i]
                matches += 1

        if mapping["total_md"] is None:
            if any(kw in h for kw in md_keywords):
                mapping["total_md"] = headers[i]
                matches += 1

        if mapping["story_points"] is None:
            if any(kw in h for kw in sp_keywords):
                mapping["story_points"] = headers[i]
                matches += 1

        for role, keywords in role_keywords.items():
            if role not in mapping["roles"]:
                if any(kw in h for kw in keywords):
                    mapping["roles"][role] = headers[i]
                    matches += 1

    if matches >= 3:
        mapping["confidence"] = "high"
    elif matches >= 2:
        mapping["confidence"] = "medium"

    # Fallback: if no task_name found, use first string-heavy column
    if mapping["task_name"] is None and sample_rows:
        for i, h in enumerate(headers):
            col_vals = [row[i] for row in sample_rows if i < len(row)]
            str_count = sum(1 for v in col_vals if isinstance(v, str) and len(str(v)) > 3)
            if str_count >= len(col_vals) * 0.5:
                mapping["task_name"] = headers[i]
                break

    return mapping


def normalize_excel_data(
    rows: list[dict],
    mapping: dict,
    entry_type: str = "accepted",
    project_meta: dict | None = None,
    slug: str | None = None,
) -> dict:
    """Convert mapped Excel rows to canonical historical entry."""
    project_meta = project_meta or {}
    hist_dir = _get_project_root() / HISTORICAL_DIR

    if not slug:
        slug = _generate_slug(hist_dir)

    from datetime import date

    project = {"name": slug, "date": date.today().isoformat()}
    if project_meta.get("domain"):
        project["domain"] = project_meta["domain"]
    if project_meta.get("tech_stack"):
        project["tech_stack"] = project_meta["tech_stack"]
    if project_meta.get("team_size"):
        project["team_size"] = int(project_meta["team_size"])
    if project_meta.get("team_experience"):
        project["team_experience"] = project_meta["team_experience"]

    aliases = get_task_type_aliases()
    tasks = []
    name_col = mapping.get("task_name")
    md_col = mapping.get("total_md")
    sp_col = mapping.get("story_points")
    role_cols = mapping.get("roles", {})

    for row in rows:
        task_name = str(row.get(name_col, "")).strip() if name_col else ""
        if not task_name:
            continue

        total_md = _safe_float(row.get(md_col)) if md_col else 0
        if total_md <= 0:
            continue

        task_type = classify_task_type(task_name, aliases) or "unclassified"
        task_entry: dict = {"task_type": task_type, "total_md": total_md}

        if sp_col:
            sp = _safe_int(row.get(sp_col))
            if sp > 0:
                task_entry["story_points"] = sp

        effort = {}
        for role, col in role_cols.items():
            val = _safe_float(row.get(col))
            if val > 0:
                effort[role] = val
        if effort:
            task_entry["effort"] = effort

        tasks.append(task_entry)

    total_md = sum(t["total_md"] for t in tasks)
    estimate = {"total_md": total_md, "tasks": tasks}

    entry = {
        "version": "1.0",
        "type": entry_type,
        "project": project,
        "estimate": estimate,
    }

    return sanitize_entry(entry)


def _safe_float(val) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val) -> int:
    try:
        return int(float(val)) if val is not None else 0
    except (ValueError, TypeError):
        return 0


def check_duplicate_slug(slug: str, entry_type: str) -> Path | None:
    """Check if a slug already exists. Returns path if duplicate, None otherwise."""
    hist_dir = _get_project_root() / HISTORICAL_DIR
    subdir = "accepted" if entry_type == "accepted" else "actuals"
    target = hist_dir / subdir / f"{slug}.yaml"
    return target if target.exists() else None
