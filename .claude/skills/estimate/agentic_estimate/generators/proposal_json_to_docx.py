"""Render estimate JSON to professional proposal DOCX."""

from pathlib import Path


def render(data: dict, output_path: Path | str, config: dict | None = None) -> None:
    """Render estimate JSON to professional proposal DOCX.

    Args:
        data: Estimate JSON dictionary
        output_path: Path to save DOCX file
        config: Optional config dict (description, date, etc.)
    """
    from docx import Document

    from .proposal_docx_section_builders import (
        add_assumptions,
        add_cover_page,
        add_estimate_tables,
        add_executive_summary,
        add_option_comparison,
        add_risks,
        add_scope,
        add_team_composition,
        add_toc,
    )

    doc = Document()
    _setup_styles(doc)

    config = config or {}

    add_cover_page(doc, data, config)
    add_toc(doc)
    add_executive_summary(doc, data)
    add_scope(doc, data)
    add_estimate_tables(doc, data)

    if len(data.get("options", [])) > 1:
        add_option_comparison(doc, data)

    add_team_composition(doc, data)
    add_risks(doc, data)
    add_assumptions(doc, data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


def _setup_styles(doc):
    """Configure document styles for professional appearance."""
    from docx.enum.style import WD_STYLE_TYPE
    from docx.shared import Pt, RGBColor

    styles = doc.styles

    if "Heading 1" in styles:
        h1 = styles["Heading 1"]
        h1.font.name = "Calibri"
        h1.font.size = Pt(18)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(0, 70, 127)

    if "Heading 2" in styles:
        h2 = styles["Heading 2"]
        h2.font.name = "Calibri"
        h2.font.size = Pt(14)
        h2.font.bold = True
        h2.font.color.rgb = RGBColor(0, 70, 127)

    if "Normal" in styles:
        normal = styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)

    try:
        if "List Bullet 2" not in styles:
            bullet2 = styles.add_style("List Bullet 2", WD_STYLE_TYPE.PARAGRAPH)
            bullet2.base_style = styles["List Bullet"]
    except (ValueError, KeyError):
        pass
