"""Utility functions for proposal DOCX generation."""

from .estimate_render_helpers import all_tasks_from_option, task_total_md


def add_styled_table(doc, headers: list[str], rows: list[list], style: str = "Light Grid Accent 1"):
    """Add a styled table to document."""
    table = doc.add_table(rows=1, cols=len(headers), style=style)
    table.autofit = False
    table.allow_autofit = False

    header_row = table.rows[0]
    for i, header in enumerate(headers):
        cell = header_row.cells[i]
        cell.text = str(header)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True

    for row_data in rows:
        row = table.add_row()
        for i, val in enumerate(row_data):
            row.cells[i].text = str(val) if val else ""

    return table


def flatten_tasks(option: dict) -> list[dict]:
    """Extract all tasks from option (categories or flat tasks)."""
    return all_tasks_from_option(option)


def sum_option_md(option: dict) -> float:
    """Calculate total MD for an option."""
    return sum(task_total_md(t) for t in all_tasks_from_option(option))
