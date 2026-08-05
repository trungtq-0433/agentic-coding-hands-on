"""Output generators for estimation results.

Generators:
- estimate_json_to_markdown: JSON → markdown report (deterministic rendering)
- estimate_json_to_interactive_excel: JSON → Excel workbook with live formulas
- estimate_json_to_html: JSON → self-contained HTML report (opens in browser)
- breakdown_json_to_overview_markdown: breakdown JSON → overview markdown (L1+L2)
- breakdown_json_to_per_team_markdown: breakdown JSON → per-team task files (L3)
- qa_log_json_to_xlsx: Q&A log JSON → categorized Excel workbook
- assumptions_json_to_docx: JSON → Word document with assumptions/TBD items
- wbs_json_to_standalone_xlsx: JSON → standalone WBS Excel workbook
- proposal_json_to_docx: JSON → professional proposal DOCX with all sections
- ExcelGenerator: Legacy Excel spreadsheet via openpyxl
- PDFGenerator: PDF documents via HTML/weasyprint

Usage (new JSON-based pipeline):
    from agentic_estimate.generators.estimate_json_to_markdown import render as render_md
    from agentic_estimate.generators.estimate_json_to_interactive_excel import render as render_xlsx
    from agentic_estimate.generators.estimate_json_to_html import render as render_html
    from agentic_estimate.generators.proposal_json_to_docx import render as render_proposal

Usage (breakdown pipeline):
    from agentic_estimate.generators.breakdown_json_to_overview_markdown import render as render_overview
    from agentic_estimate.generators.breakdown_json_to_per_team_markdown import render as render_per_team

Usage (legacy):
    from agentic_estimate.generators import ExcelGenerator, PDFGenerator, OutputConfig
"""

from .generator_base_output_interface import BaseGenerator, OutputConfig
from .generator_excel_spreadsheet_openpyxl import ExcelGenerator
from .generator_pdf_html_weasyprint import PDFGenerator

__all__ = [
    "BaseGenerator",
    "OutputConfig",
    "ExcelGenerator",
    "PDFGenerator",
]
