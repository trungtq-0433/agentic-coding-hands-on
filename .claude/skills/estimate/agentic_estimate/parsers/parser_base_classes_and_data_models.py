"""Base classes and data models for document parsers."""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class Table:
    """Represents a table extracted from a document."""

    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None

    def to_markdown(self) -> str:
        """Convert table to markdown format."""
        if not self.headers:
            return ""

        lines = []
        if self.caption:
            lines.append(f"**{self.caption}**\n")

        # Header row
        lines.append("| " + " | ".join(str(h) for h in self.headers) + " |")
        # Separator
        lines.append("| " + " | ".join("---" for _ in self.headers) + " |")
        # Data rows
        for row in self.rows:
            # Ensure row has same length as headers
            padded_row = row + [""] * (len(self.headers) - len(row))
            lines.append("| " + " | ".join(str(c) for c in padded_row[: len(self.headers)]) + " |")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Section:
    """Represents a document section with hierarchy."""

    level: int  # 1-6 for h1-h6
    title: str
    content: str
    subsections: list["Section"] = field(default_factory=list)

    def to_markdown(self, include_subsections: bool = True) -> str:
        """Convert section to markdown format."""
        lines = []
        lines.append(f"{'#' * self.level} {self.title}")
        if self.content:
            lines.append(f"\n{self.content}")

        if include_subsections:
            for sub in self.subsections:
                lines.append(f"\n{sub.to_markdown()}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary with nested subsections."""
        return {
            "level": self.level,
            "title": self.title,
            "content": self.content,
            "subsections": [s.to_dict() for s in self.subsections],
        }


@dataclass
class ParsedDocument:
    """Unified output format for all document parsers."""

    source_path: str
    source_type: str  # pdf, excel, markdown, image-ocr, google-sheet, google-doc
    title: str
    content: str
    sections: list[Section] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    parse_warnings: list[str] = field(default_factory=list)
    parsed_at: datetime = field(default_factory=datetime.now)

    def to_text(self) -> str:
        """Convert to plain text for agent consumption."""
        parts = []

        # Title
        if self.title:
            parts.append(f"# {self.title}\n")

        # Main content
        if self.content:
            parts.append(self.content)

        # Tables
        if self.tables:
            parts.append("\n## Tables\n")
            for i, table in enumerate(self.tables, 1):
                parts.append(f"\n### Table {i}")
                if table.caption:
                    parts.append(f": {table.caption}")
                parts.append(f"\n{table.to_markdown()}\n")

        return "\n".join(parts)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_path": self.source_path,
            "source_type": self.source_type,
            "title": self.title,
            "content": self.content,
            "sections": [s.to_dict() for s in self.sections],
            "tables": [t.to_dict() for t in self.tables],
            "metadata": self.metadata,
            "parse_warnings": self.parse_warnings,
            "parsed_at": self.parsed_at.isoformat(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_word_count(self) -> int:
        """Get total word count of content."""
        return len(self.content.split())

    def has_warnings(self) -> bool:
        """Check if there are any parse warnings."""
        return len(self.parse_warnings) > 0


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    @abstractmethod
    def parse(self, source: str) -> ParsedDocument:
        """
        Parse a document and return structured data.

        Args:
            source: Path to file or URL/ID for remote documents

        Returns:
            ParsedDocument with extracted content
        """
        pass

    @abstractmethod
    def supports(self, source: str) -> bool:
        """
        Check if this parser supports the given source.

        Args:
            source: Path to file or URL/ID

        Returns:
            True if this parser can handle the source
        """
        pass

    def _add_warning(self, doc: ParsedDocument, warning: str) -> None:
        """Add a warning to the parsed document."""
        doc.parse_warnings.append(warning)


class ParserError(Exception):
    """Base exception for parser errors."""

    def __init__(self, message: str, source: str, cause: Exception | None = None):
        self.message = message
        self.source = source
        self.cause = cause
        super().__init__(f"{message} (source: {source})")


class UnsupportedFormatError(ParserError):
    """Raised when a document format is not supported."""

    pass


class ParseFailedError(ParserError):
    """Raised when parsing fails."""

    pass
