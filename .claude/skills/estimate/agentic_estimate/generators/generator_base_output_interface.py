"""Base generator interface for output formats."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OutputConfig:
    """Configuration for output generation."""

    output_dir: str = "./output"
    project_name: str = "project"
    include_risks: bool = True
    include_validation: bool = True
    include_api_spec: bool = True
    client_version: bool = False  # Simplified version for clients
    template_dir: str | None = None
    custom_styles: dict = field(default_factory=dict)

    def get_output_path(self, filename: str) -> Path:
        """Get full output path for filename."""
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path / filename


class BaseGenerator(ABC):
    """Base class for output generators."""

    def __init__(self, config: OutputConfig | None = None):
        """
        Initialize generator.

        Args:
            config: Output configuration
        """
        self.config = config or OutputConfig()

    @abstractmethod
    def generate(self, results: dict) -> str:
        """
        Generate output from results.

        Args:
            results: Estimation pipeline results

        Returns:
            Path to generated file
        """
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return file extension for this format."""
        pass

    def get_filename(self, suffix: str = "") -> str:
        """Generate output filename."""
        name = self.config.project_name.lower().replace(" ", "-")
        suffix_part = f"-{suffix}" if suffix else ""
        return f"{name}-estimate{suffix_part}.{self.file_extension}"

    def _safe_get(self, data: dict, *keys, default=""):
        """Safely get nested dictionary value."""
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current if current is not None else default
