"""DOCX parsing using python-docx."""

from __future__ import annotations

from pathlib import Path

try:
    from docx import Document
except ImportError:
    Document = None

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
    Section,
    Table,
)


class DocxParser(BaseParser):
    """
    DOCX parser using python-docx library.

    Supports: .docx format
    Features: Headings, paragraphs, tables, lists, inline formatting
    """

    def __init__(self):
        if Document is None:
            raise ImportError("python-docx not installed. Run: pip install python-docx")

    def parse(self, source: str) -> ParsedDocument:
        """
        Parse DOCX file and extract structured content.

        Args:
            source: Path to DOCX file

        Returns:
            ParsedDocument with sections, tables, and formatted text
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        try:
            doc = Document(source)
        except Exception as e:
            raise ParseFailedError(f"Failed to open DOCX file: {e}", source, e)

        sections = []
        tables = []
        content_parts = []
        warnings = []
        current_section_stack = []

        para_lookup = {p._element: p for p in doc.paragraphs}
        table_lookup = {t._element: t for t in doc.tables}

        for element in doc.element.body:
            if element.tag.endswith("p"):
                para = para_lookup.get(element)
                if para:
                    self._process_paragraph(
                        para, sections, content_parts, current_section_stack, warnings
                    )
            elif element.tag.endswith("tbl"):
                tbl = table_lookup.get(element)
                if tbl:
                    table = self._extract_table(tbl)
                    if table:
                        tables.append(table)
                        content_parts.append(f"\n{table.to_markdown()}\n")

        title = self._extract_title(doc, sections)
        content = "".join(content_parts).strip()

        metadata = {
            "paragraphs": len(doc.paragraphs),
            "tables": len(tables),
            "sections": len(sections),
        }

        return ParsedDocument(
            source_path=source,
            source_type="docx",
            title=title,
            content=content,
            sections=sections,
            tables=tables,
            metadata=metadata,
            parse_warnings=warnings,
        )

    def _process_paragraph(self, para, sections, content_parts, current_section_stack, warnings):
        """Process a paragraph and determine its type."""
        style_name = para.style.name if para.style else "Normal"
        text = self._format_paragraph_text(para)

        if not text.strip():
            return

        if style_name.startswith("Heading"):
            level = self._extract_heading_level(style_name)
            section = Section(level=level, title=text, content="")

            while current_section_stack and current_section_stack[-1].level >= level:
                current_section_stack.pop()

            sections.append(section)
            current_section_stack.append(section)
            content_parts.append(f"\n{'#' * level} {text}\n\n")

        elif "List Bullet" in style_name or "List" in style_name:
            formatted_text = f"- {text}\n"
            content_parts.append(formatted_text)
            if current_section_stack:
                current_section_stack[-1].content += formatted_text

        else:
            content_parts.append(f"{text}\n\n")
            if current_section_stack:
                current_section_stack[-1].content += f"{text}\n\n"

    def _format_paragraph_text(self, para) -> str:
        """Extract text with inline formatting."""
        result = []
        for run in para.runs:
            text = run.text
            if not text:
                continue

            if run.bold and run.italic:
                text = f"***{text}***"
            elif run.bold:
                text = f"**{text}**"
            elif run.italic:
                text = f"*{text}*"

            result.append(text)

        return "".join(result)

    def _extract_heading_level(self, style_name: str) -> int:
        """Extract heading level from style name."""
        import re

        match = re.search(r"\d+", style_name)
        if match:
            return min(max(int(match.group()), 1), 6)
        return 1

    def _extract_table(self, table) -> Table | None:
        """Extract table data from DOCX table."""
        if not table.rows:
            return None

        headers = [cell.text.strip() for cell in table.rows[0].cells]
        rows = []

        for row in table.rows[1:]:
            row_data = [cell.text.strip() for cell in row.cells]
            if any(row_data):
                rows.append(row_data)

        if not headers and not rows:
            return None

        return Table(headers=headers if any(headers) else [], rows=rows)

    def _extract_title(self, doc, sections) -> str:
        """Extract document title from first heading or properties."""
        if sections:
            return sections[0].title

        if hasattr(doc.core_properties, "title") and doc.core_properties.title:
            return doc.core_properties.title

        for para in doc.paragraphs[:5]:
            if para.text.strip():
                return para.text.strip()

        return "Untitled Document"

    def supports(self, source: str) -> bool:
        """Check if this parser supports the given source."""
        return source.lower().endswith(".docx")
