"""Knowledge base loader for YAML configuration files."""

import functools
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


DEFAULT_BASE_EFFORTS_PATH = "knowledge-base/base-efforts-man-days-per-task-type.yaml"
DEFAULT_COMPLEXITY_PATH = "knowledge-base/complexity-multipliers-and-factors.yaml"
DEFAULT_TECH_MULTIPLIERS_PATH = "knowledge-base/tech-stack-multipliers-by-framework.yaml"
DEFAULT_RISK_PATTERNS_PATH = "knowledge-base/risk-patterns-indicators-mitigations.yaml"
DEFAULT_ESTIMATION_THRESHOLDS_PATH = "knowledge-base/estimation-thresholds-validation.yaml"
DEFAULT_EXPERIENCE_FACTORS_PATH = "knowledge-base/experience-factors-team-profile.yaml"

MAX_TEAM_SIZE = 999


@functools.lru_cache(maxsize=1)
def _get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        # Skill root: has both SKILL.md and knowledge-base/ directory
        if (parent / "SKILL.md").exists() and (parent / "knowledge-base").is_dir():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: 3 levels up from this file → agentic_estimate/utils/ → agentic_estimate/ → estimate/
    return Path(__file__).resolve().parent.parent.parent


@functools.lru_cache(maxsize=16)
def _load_yaml(path: str) -> dict:
    full_path = _get_project_root() / path
    if not full_path.exists():
        logger.warning(f"Config file not found: {path}, using defaults")
        return {}

    with open(full_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_base_efforts(path: str | None = None) -> dict:
    path = path or DEFAULT_BASE_EFFORTS_PATH
    data = _load_yaml(path)

    # Flatten nested structure for easier access
    efforts = {}

    for category, items in data.items():
        if isinstance(items, dict):
            for key, value in items.items():
                efforts[f"{category}_{key}"] = value
        else:
            efforts[category] = items

    return efforts


def load_complexity_matrix(path: str | None = None) -> dict:
    path = path or DEFAULT_COMPLEXITY_PATH
    data = _load_yaml(path)

    # Extract complexity levels
    levels = data.get("complexity_levels", {})

    # Add default if not present
    if not levels:
        levels = {
            "simple": 1.0,
            "medium": 1.5,
            "complex": 2.5,
            "very_complex": 4.0,
        }

    return levels


def load_complexity_factors(path: str | None = None) -> dict:
    path = path or DEFAULT_COMPLEXITY_PATH
    data = _load_yaml(path)
    return data.get("factors", {})


def load_tech_multipliers(path: str | None = None) -> dict:
    path = path or DEFAULT_TECH_MULTIPLIERS_PATH
    data = _load_yaml(path)

    # Flatten for easier access
    multipliers = {}

    # Familiarity levels
    multipliers["familiarity"] = data.get("familiarity", {})

    # Frontend frameworks
    frontend = data.get("frontend", {})
    for framework, config in frontend.items():
        if isinstance(config, dict):
            multipliers[f"frontend_{framework}"] = config.get("base", 1.0)
        else:
            multipliers[f"frontend_{framework}"] = config

    # Backend frameworks
    backend = data.get("backend", {})
    for framework, config in backend.items():
        if isinstance(config, dict):
            multipliers[f"backend_{framework}"] = config.get("base", 1.0)
        else:
            multipliers[f"backend_{framework}"] = config

    # Databases
    databases = data.get("databases", {})
    for db, config in databases.items():
        if isinstance(config, dict):
            multipliers[f"database_{db}"] = config.get("base", 1.0)
        else:
            multipliers[f"database_{db}"] = config

    return multipliers


def get_effort(task_type: str, default: float = 1.0) -> float:
    efforts = load_base_efforts()
    return efforts.get(task_type, default)


def get_complexity_multiplier(complexity: str, default: float = 1.5) -> float:
    matrix = load_complexity_matrix()
    # Handle both underscore and hyphen formats
    normalized = complexity.lower().replace("-", "_")
    return matrix.get(normalized, default)


def get_tech_multiplier(tech: str, default: float = 1.0) -> float:
    multipliers = load_tech_multipliers()

    # Try exact match first
    if tech in multipliers:
        return multipliers[tech]

    # Try with category prefixes
    for prefix in ["frontend_", "backend_", "database_"]:
        key = f"{prefix}{tech.lower()}"
        if key in multipliers:
            return multipliers[key]

    return default


def calculate_effort(
    base_task: str,
    complexity: str = "medium",
    tech_stack: list[str] | None = None,
    factors: list[str] | None = None,
) -> float:
    base = get_effort(base_task)
    complexity_mult = get_complexity_multiplier(complexity)
    effort = base * complexity_mult

    if tech_stack:
        tech_mult = 1.0
        for tech in tech_stack:
            tech_mult *= get_tech_multiplier(tech)
        effort *= tech_mult

    if factors:
        factor_data = load_complexity_factors()
        for factor in factors:
            for category, values in factor_data.items():
                if factor in values:
                    effort *= values[factor]

    return round(effort, 2)


def load_risk_patterns(path: str | None = None) -> dict:
    path = path or DEFAULT_RISK_PATTERNS_PATH
    return _load_yaml(path)


def load_estimation_thresholds(path: str | None = None) -> dict:
    path = path or DEFAULT_ESTIMATION_THRESHOLDS_PATH
    return _load_yaml(path)


def load_experience_factors(path: str | None = None) -> dict:
    path = path or DEFAULT_EXPERIENCE_FACTORS_PATH
    data = _load_yaml(path)

    # Provide defaults if file not found or empty
    if not data:
        data = {
            "experience_levels": {
                "junior": {"multiplier": 1.3},
                "mid": {"multiplier": 1.0},
                "senior": {"multiplier": 0.8},
            },
            "domain_familiarity": {
                "new": {"multiplier": 1.25},
                "familiar": {"multiplier": 1.0},
                "expert": {"multiplier": 0.85},
            },
            "team_size_factors": {
                "solo": {"multiplier": 1.0, "min_size": 1, "max_size": 1},
                "small": {"multiplier": 0.95, "min_size": 2, "max_size": 3},
                "medium": {"multiplier": 1.1, "min_size": 4, "max_size": 6},
                "large": {"multiplier": 1.25, "min_size": 7, "max_size": 999},
            },
        }

    return data


def get_experience_multiplier(
    experience_level: str = "mid",
    domain_familiarity: str = "familiar",
    team_size: int = 1,
) -> float:
    factors = load_experience_factors()

    exp_data = factors.get("experience_levels", {}).get(experience_level, {})
    exp_mult = exp_data.get("multiplier", 1.0)

    domain_data = factors.get("domain_familiarity", {}).get(domain_familiarity, {})
    domain_mult = domain_data.get("multiplier", 1.0)

    size_factors = factors.get("team_size_factors", {})
    size_mult = 1.0

    for _, size_data in size_factors.items():
        min_size = size_data.get("min_size", 1)
        max_size = size_data.get("max_size", MAX_TEAM_SIZE)
        if min_size <= team_size <= max_size:
            size_mult = size_data.get("multiplier", 1.0)
            break

    return exp_mult * domain_mult * size_mult
