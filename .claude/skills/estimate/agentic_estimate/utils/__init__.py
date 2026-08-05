"""Utility modules for agentic-estimate."""

from .calibration_engine import CalibrationEngine
from .config_loader_project_roles import (
    get_active_roles,
    get_role_cost,
    get_role_display_name,
    get_team_headcount,
    load_project_config,
)
from .historical_data_loader import (
    check_duplicate_slug,
    classify_task_type,
    clear_caches,
    load_all_entries,
    load_historical_entry,
    normalize_estimate_json,
    validate_entry,
)
from .knowledge_base_loader_yaml_config import (
    calculate_effort,
    get_complexity_multiplier,
    get_effort,
    get_experience_multiplier,
    get_tech_multiplier,
    load_base_efforts,
    load_complexity_factors,
    load_complexity_matrix,
    load_estimation_thresholds,
    load_experience_factors,
    load_risk_patterns,
    load_tech_multipliers,
)
from .manifest_manager import (
    derive_slug,
    find_or_create_estimate,
    get_missing,
    load_manifest,
    mark_breakdown,
    mark_output,
    save_manifest,
    scan_and_build,
)
from .role_effort_extractor import (
    ExtractionResult,
    TaskEffort,
    extract_role_effort,
)
from .schema_validator_jsonschema import (
    SchemaValidator,
    load_schema,
    validate_against_schema,
    validate_architecture,
    validate_estimate,
    validate_project,
    validate_requirement,
)

__all__ = [
    # Knowledge base
    "load_base_efforts",
    "load_complexity_matrix",
    "load_complexity_factors",
    "load_tech_multipliers",
    "load_risk_patterns",
    "load_estimation_thresholds",
    "load_experience_factors",
    "get_effort",
    "get_complexity_multiplier",
    "get_tech_multiplier",
    "get_experience_multiplier",
    "calculate_effort",
    # Schema validation
    "load_schema",
    "validate_against_schema",
    "validate_requirement",
    "validate_architecture",
    "validate_estimate",
    "validate_project",
    "SchemaValidator",
    # Manifest management
    "derive_slug",
    "load_manifest",
    "save_manifest",
    "find_or_create_estimate",
    "mark_output",
    "mark_breakdown",
    "get_missing",
    "scan_and_build",
    # Calibration
    "CalibrationEngine",
    # Historical data
    "clear_caches",
    "classify_task_type",
    "normalize_estimate_json",
    "load_historical_entry",
    "load_all_entries",
    "validate_entry",
    "check_duplicate_slug",
    # Project role configuration
    "load_project_config",
    "get_active_roles",
    "get_role_display_name",
    "get_role_cost",
    "get_team_headcount",
    # Role effort extraction
    "extract_role_effort",
    "ExtractionResult",
    "TaskEffort",
]
