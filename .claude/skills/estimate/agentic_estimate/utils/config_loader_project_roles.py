"""Project role configuration loader with user overrides."""

import sys
from pathlib import Path

import yaml

from agentic_estimate.utils.knowledge_base_loader_yaml_config import _get_project_root

DEFAULT_ROLES_CONFIG_PATH = "knowledge-base/roles-config-defaults.yaml"
USER_CONFIG_FILENAME = "estimate-config.yaml"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_project_config(input_dir: Path) -> dict:
    """
    Load project configuration with role definitions and optional overrides.

    Loads defaults from knowledge-base/roles-config-defaults.yaml,
    then merges with user's estimate-config.yaml from input_dir if present.

    Args:
        input_dir: Directory containing input documents (may contain estimate-config.yaml)

    Returns:
        Dictionary with keys:
        - roles: dict[str, dict] — role definitions with active status
        - cost_per_md: dict[str, float] — per-role cost overrides (optional)
        - team: dict[str, int] — per-role headcount (optional)

    Raises:
        ValueError: If no roles are active after merging configs
    """
    # Load defaults from project knowledge base
    project_root = _get_project_root()
    defaults_path = project_root / DEFAULT_ROLES_CONFIG_PATH
    defaults = _load_yaml(defaults_path)

    if not defaults or "roles" not in defaults:
        raise ValueError(f"Invalid defaults file: {defaults_path}")

    roles = defaults["roles"]

    # Try to load user config from input directory
    user_config_path = Path(input_dir) / USER_CONFIG_FILENAME
    user_config = _load_yaml(user_config_path)

    # Merge user role overrides (only active status)
    if user_config and "roles" in user_config:
        user_roles = user_config["roles"]
        for slug, active in user_roles.items():
            if slug in roles:
                roles[slug]["active"] = bool(active)
            else:
                # Warn about unknown slugs but don't crash
                print(
                    f"Warning: Unknown role '{slug}' in {USER_CONFIG_FILENAME}, ignoring",
                    file=sys.stderr,
                )

    # Validate at least one role is active
    active_count = sum(1 for r in roles.values() if r.get("active", False))
    if active_count == 0:
        raise ValueError("At least one role must be active")

    # Build final config
    config = {
        "roles": roles,
        "cost_per_md": user_config.get("cost_per_md", {}),
        "team": user_config.get("team", {}),
    }

    return config


def get_active_roles(config: dict) -> list[str]:
    """
    Get list of active role slugs in definition order.

    Args:
        config: Config dict from load_project_config()

    Returns:
        List of role slugs where active=True
    """
    roles = config.get("roles", {})
    return [slug for slug, data in roles.items() if data.get("active", False)]


def get_role_display_name(slug: str, config: dict) -> str:
    """
    Get display name for a role slug.

    Args:
        slug: Role slug (e.g., 'fe', 'qa_manual')
        config: Config dict from load_project_config()

    Returns:
        Display name from config, or slug.upper() if not found
    """
    roles = config.get("roles", {})
    role_data = roles.get(slug)
    if role_data and "name" in role_data:
        return role_data["name"]
    return slug.upper()


def get_role_cost(slug: str, config: dict, default_cost: float) -> float:
    """
    Get cost per man-day for a role.

    Args:
        slug: Role slug
        config: Config dict from load_project_config()
        default_cost: Default cost if no override specified

    Returns:
        Cost per man-day for the role
    """
    cost_overrides = config.get("cost_per_md", {})
    return cost_overrides.get(slug, default_cost)


def get_team_headcount(slug: str, config: dict) -> int | None:
    """
    Get team headcount for a role.

    Args:
        slug: Role slug
        config: Config dict from load_project_config()

    Returns:
        Headcount for the role, or None if not specified
    """
    team_config = config.get("team", {})
    return team_config.get(slug)
