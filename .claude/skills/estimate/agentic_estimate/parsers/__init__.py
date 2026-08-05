"""Document parsers for agentic-estimate.

This package provides parsers for extracting text and structure from various
document formats including PDF, Excel, Markdown, DOCX, PPTX, and images (via OCR).

Usage:
    from agentic_estimate.parsers import parse_file, create_default_registry

    # Simple usage
    doc = parse_file("document.pdf")
    print(doc.content)

    # With registry
    registry = create_default_registry()
    doc = registry.parse("spreadsheet.xlsx")

Supported formats:
    - PDF (.pdf) - via PyMuPDF and pdfplumber
    - Excel (.xlsx, .xls) - via Pandas and OpenPyXL
    - Markdown (.md, .markdown) - native parsing
    - DOCX (.docx) - via python-docx
    - PPTX (.pptx) - via python-pptx
    - Images (.png, .jpg, .tiff, etc.) - via Tesseract OCR
"""

from .parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
    ParserError,
    Section,
    Table,
    UnsupportedFormatError,
)
from .parser_registry_factory import (
    ParserRegistry,
    create_default_registry,
    parse_file,
    parse_files,
)

try:
    from .docx import DocxParser
except ImportError:
    DocxParser = None

try:
    from .pptx import PptxParser
except ImportError:
    PptxParser = None

__all__ = [
    # Base classes
    "BaseParser",
    "ParsedDocument",
    "Section",
    "Table",
    # Exceptions
    "ParserError",
    "ParseFailedError",
    "UnsupportedFormatError",
    # Registry
    "ParserRegistry",
    "create_default_registry",
    # Convenience functions
    "parse_file",
    "parse_files",
    # Parsers
    "DocxParser",
    "PptxParser",
]

__version__ = "0.1.0"
