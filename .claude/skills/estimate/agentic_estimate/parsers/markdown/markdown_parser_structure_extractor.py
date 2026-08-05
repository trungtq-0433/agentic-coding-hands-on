"""Markdown parsing with structure extraction."""

import re
from pathlib import Path

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
    Section,
    Table,
)


class MarkdownParser(BaseParser):
    """
    Markdown parser that preserves document structure.

    Features:
    - Header hierarchy extraction
    - Table parsing
    - List extraction
    - Code block detection
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        Initialize Markdown parser.

        Args:
            encoding: File encoding (default: utf-8)
        """
        self.encoding = encoding

    def parse(self, source: str) -> ParsedDocument:
        """
        Parse Markdown file and extract structure.

        Args:
            source: Path to Markdown file

        Returns:
            ParsedDocument with sections and tables
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        try:
            content = path.read_text(encoding=self.encoding)
        except Exception as e:
            raise ParseFailedError(f"Failed to read file: {e}", source, e)

        # Extract components
        title = self._extract_title(content)
        sections = self._extract_sections(content)
        tables = self._extract_tables(content)

        # Build metadata
        metadata = {
            "char_count": len(content),
            "word_count": len(content.split()),
            "line_count": content.count("\n") + 1,
            "header_count": len(sections),
            "table_count": len(tables),
            "has_code_blocks": "```" in content,
        }

        return ParsedDocument(
            source_path=source,
            source_type="markdown",
            title=title or path.stem,
            content=content,
            sections=sections,
            tables=tables,
            metadata=metadata,
        )

    def _extract_title(self, content: str) -> str | None:
        """Extract document title from first h1 header."""
        # Match first # header
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Check for YAML front matter title
        yaml_match = re.search(
            r"^---\s*\n.*?title:\s*[\"']?(.+?)[\"']?\s*\n.*?---", content, re.DOTALL
        )
        if yaml_match:
            return yaml_match.group(1).strip()

        return None

    def _extract_sections(self, content: str) -> list[Section]:
        """Extract sections from headers."""
        sections = []

        # Pattern for markdown headers
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        # Find all headers with their positions
        headers = []
        for match in header_pattern.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            headers.append(
                {
                    "level": level,
                    "title": title,
                    "start": start,
                }
            )

        # Extract content between headers
        for i, header in enumerate(headers):
            # Find end position (start of next header or end of content)
            if i + 1 < len(headers):
                end = headers[i + 1]["start"] - len(
                    f"{'#' * headers[i + 1]['level']} {headers[i + 1]['title']}"
                )
            else:
                end = len(content)

            # Extract content between this header and next
            section_content = content[header["start"] : end].strip()

            # Remove content that belongs to subsections
            # (content before any lower-level header)
            for j in range(i + 1, len(headers)):
                if headers[j]["level"] > header["level"]:
                    # This is a subsection, trim content
                    sub_header_pos = content.find(
                        f"{'#' * headers[j]['level']} {headers[j]['title']}", header["start"]
                    )
                    if sub_header_pos != -1 and sub_header_pos < end:
                        section_content = content[header["start"] : sub_header_pos].strip()
                        break
                else:
                    break

            sections.append(
                Section(
                    level=header["level"],
                    title=header["title"],
                    content=(
                        section_content[:500] if len(section_content) > 500 else section_content
                    ),
                )
            )

        return sections

    def _extract_tables(self, content: str) -> list[Table]:
        """Extract markdown tables."""
        tables = []

        # Pattern for markdown tables
        # Matches: | header | header |
        #          |--------|--------|
        #          | cell   | cell   |
        table_pattern = re.compile(
            r"(\|[^\n]+\|\n)"  # Header row
            r"(\|[-:\s|]+\|\n)"  # Separator row
            r"((?:\|[^\n]+\|\n?)+)",  # Data rows
            re.MULTILINE,
        )

        for match in table_pattern.finditer(content):
            header_row = match.group(1)
            data_rows = match.group(3)

            # Parse header
            headers = self._parse_table_row(header_row)
            if not headers:
                continue

            # Parse data rows
            rows = []
            for line in data_rows.strip().split("\n"):
                row = self._parse_table_row(line)
                if row:
                    rows.append(row)

            if headers and rows:
                tables.append(
                    Table(
                        headers=headers,
                        rows=rows,
                    )
                )

        return tables

    def _parse_table_row(self, row: str) -> list[str]:
        """Parse a single table row."""
        # Remove leading/trailing pipes and split
        row = row.strip()
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|"):
            row = row[:-1]

        cells = [cell.strip() for cell in row.split("|")]
        return cells

    def supports(self, source: str) -> bool:
        """Check if this parser supports the given source."""
        lower = source.lower()
        return lower.endswith(".md") or lower.endswith(".markdown")

    def parse_string(self, content: str, title: str = "Untitled") -> ParsedDocument:
        """
        Parse Markdown content from string.

        Args:
            content: Markdown content string
            title: Document title

        Returns:
            ParsedDocument with extracted structure
        """
        extracted_title = self._extract_title(content) or title
        sections = self._extract_sections(content)
        tables = self._extract_tables(content)

        metadata = {
            "char_count": len(content),
            "word_count": len(content.split()),
            "line_count": content.count("\n") + 1,
            "header_count": len(sections),
            "table_count": len(tables),
        }

        return ParsedDocument(
            source_path="<string>",
            source_type="markdown",
            title=extracted_title,
            content=content,
            sections=sections,
            tables=tables,
            metadata=metadata,
        )
