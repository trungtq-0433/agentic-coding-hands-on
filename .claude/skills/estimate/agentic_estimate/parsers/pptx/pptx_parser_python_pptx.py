"""PPTX parsing using python-pptx."""

from __future__ import annotations

from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    Presentation = None
    MSO_SHAPE_TYPE = None

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
    Section,
    Table,
)


class PptxParser(BaseParser):
    """
    PPTX parser using python-pptx library.

    Supports: .pptx format
    Features: Slides, text extraction, tables, speaker notes, images
    """

    def __init__(self):
        if Presentation is None:
            raise ImportError("python-pptx not installed. Run: pip install python-pptx")

    def parse(self, source: str) -> ParsedDocument:
        """
        Parse PPTX file and extract content from all slides.

        Args:
            source: Path to PPTX file

        Returns:
            ParsedDocument with slides as sections and extracted tables
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        try:
            prs = Presentation(source)
        except Exception as e:
            raise ParseFailedError(f"Failed to open PPTX file: {e}", source, e)

        sections = []
        tables = []
        content_parts = []
        warnings = []

        title = self._extract_presentation_title(prs)

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_title = self._extract_slide_title(slide, slide_idx)
            slide_content = []
            slide_tables = []

            for shape in slide.shapes:
                if shape.has_text_frame:
                    text = self._extract_text_from_shape(shape)
                    if text and text != slide_title:
                        slide_content.append(text)

                elif shape.has_table:
                    table = self._extract_table(shape.table)
                    if table:
                        slide_tables.append(table)
                        tables.append(table)

                elif hasattr(shape, "shape_type") and shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    slide_content.append(f"[Image: {shape.name}]")

            notes = self._extract_speaker_notes(slide)
            if notes:
                slide_content.append(f"\n**Speaker Notes:** {notes}")

            section = Section(
                level=2,
                title=slide_title,
                content="\n\n".join(slide_content),
            )
            sections.append(section)

            slide_md = [f"## {slide_title}\n"]
            if slide_content:
                slide_md.append("\n\n".join(slide_content))
            for table in slide_tables:
                slide_md.append(f"\n{table.to_markdown()}\n")

            content_parts.append("\n".join(slide_md))

        content = "\n\n---\n\n".join(content_parts)

        metadata = {
            "slides": len(prs.slides),
            "tables": len(tables),
            "sections": len(sections),
        }

        return ParsedDocument(
            source_path=source,
            source_type="pptx",
            title=title,
            content=content,
            sections=sections,
            tables=tables,
            metadata=metadata,
            parse_warnings=warnings,
        )

    def _extract_presentation_title(self, prs) -> str:
        """Extract presentation title from first slide or properties."""
        if hasattr(prs.core_properties, "title") and prs.core_properties.title:
            return prs.core_properties.title

        if prs.slides:
            first_slide = prs.slides[0]
            title = self._extract_slide_title(first_slide, 1)
            if title != "Slide 1":
                return title

        return "Untitled Presentation"

    def _extract_slide_title(self, slide, slide_idx: int) -> str:
        """Extract title from slide."""
        if slide.shapes.title:
            return slide.shapes.title.text.strip() or f"Slide {slide_idx}"
        return f"Slide {slide_idx}"

    def _extract_text_from_shape(self, shape) -> str:
        """Extract formatted text from a shape."""
        if not shape.has_text_frame:
            return ""

        text_parts = []
        for paragraph in shape.text_frame.paragraphs:
            para_text = []
            for run in paragraph.runs:
                text = run.text
                if not text:
                    continue

                if run.font.bold and run.font.italic:
                    text = f"***{text}***"
                elif run.font.bold:
                    text = f"**{text}**"
                elif run.font.italic:
                    text = f"*{text}*"

                para_text.append(text)

            if para_text:
                level = paragraph.level
                if level > 0:
                    text_parts.append(f"{'  ' * level}- {''.join(para_text)}")
                else:
                    text_parts.append("".join(para_text))

        return "\n".join(text_parts)

    def _extract_table(self, table) -> Table | None:
        """Extract table data from PPTX table."""
        if not table.rows or len(table.rows) == 0:
            return None

        headers = [cell.text.strip() for cell in table.rows[0].cells]
        rows = []

        for idx in range(1, len(table.rows)):
            row_data = [cell.text.strip() for cell in table.rows[idx].cells]
            if any(row_data):
                rows.append(row_data)

        if not headers and not rows:
            return None

        return Table(headers=headers if any(headers) else [], rows=rows)

    def _extract_speaker_notes(self, slide) -> str:
        if not slide.has_notes_slide or not slide.notes_slide.notes_text_frame:
            return ""
        return slide.notes_slide.notes_text_frame.text.strip()

    def supports(self, source: str) -> bool:
        return source.lower().endswith(".pptx")
