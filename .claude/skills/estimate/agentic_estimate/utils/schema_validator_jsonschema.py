"""JSON Schema validation utility."""

import json

from agentic_estimate.utils.knowledge_base_loader_yaml_config import _get_project_root

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    jsonschema = None

_default_validator = None


def _get_default_validator() -> "SchemaValidator":
    global _default_validator
    if _default_validator is None:
        _default_validator = SchemaValidator()
    return _default_validator


def load_schema(schema_path: str) -> dict:
    full_path = _get_project_root() / schema_path
    if not full_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(full_path, encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(
    data: dict,
    schema_path: str,
) -> tuple[bool, list[str]]:
    return _get_default_validator().validate(data, schema_path)


def validate_requirement(data: dict) -> tuple[bool, list[str]]:
    """Validate requirement data against schema."""
    return validate_against_schema(data, "schemas/requirement-item-schema.json")


def validate_architecture(data: dict) -> tuple[bool, list[str]]:
    """Validate architecture data against schema."""
    return validate_against_schema(data, "schemas/architecture-design-schema.json")


def validate_estimate(data: dict) -> tuple[bool, list[str]]:
    """Validate estimate data against schema."""
    return validate_against_schema(data, "schemas/estimate-output-schema.json")


def validate_project(data: dict) -> tuple[bool, list[str]]:
    """Validate project data against schema."""
    return validate_against_schema(data, "schemas/project-metadata-schema.json")


class SchemaValidator:
    """Schema validator with caching."""

    def __init__(self):
        self._schema_cache: dict[str, dict] = {}

    def _get_schema(self, schema_path: str) -> dict:
        """Get schema with caching."""
        if schema_path not in self._schema_cache:
            self._schema_cache[schema_path] = load_schema(schema_path)
        return self._schema_cache[schema_path]

    def validate(self, data: dict, schema_path: str) -> tuple[bool, list[str]]:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema_path: Path to schema file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if jsonschema is None:
            return True, []

        try:
            schema = self._get_schema(schema_path)
        except FileNotFoundError as e:
            return False, [str(e)]

        validator = Draft202012Validator(schema)
        errors = []

        for error in validator.iter_errors(data):
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return len(errors) == 0, errors

    def clear_cache(self) -> None:
        """Clear schema cache."""
        self._schema_cache.clear()
