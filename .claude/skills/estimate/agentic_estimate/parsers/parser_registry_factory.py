"""Parser registry and factory for document parsing."""

from pathlib import Path

from .parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    UnsupportedFormatError,
)


class ParserRegistry:
    """
    Registry for document parsers with automatic format detection.

    Usage:
        registry = create_default_registry()
        doc = registry.parse("document.pdf")
    """

    def __init__(self):
        self._parsers: list[BaseParser] = []

    def register(self, parser: BaseParser) -> None:
        self._parsers.append(parser)

    def get_parser(self, source: str) -> BaseParser:
        for parser in self._parsers:
            if parser.supports(source):
                return parser

        raise UnsupportedFormatError(
            "No parser found for format",
            source,
        )

    def parse(self, source: str) -> ParsedDocument:
        parser = self.get_parser(source)
        return parser.parse(source)

    def can_parse(self, source: str) -> bool:
        return any(parser.supports(source) for parser in self._parsers)

    _PARSER_EXTENSIONS: dict[str, set[str]] = {
        "PyMuPDFTextParser": {".pdf"},
        "ExcelParser": {".xlsx", ".xls"},
        "MarkdownParser": {".md", ".markdown"},
        "TesseractOCRParser": {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"},
        "DocxParser": {".docx"},
        "PptxParser": {".pptx"},
        "GitHubURLParser": {
            "github.com/*/issues/*",
            "github.com/*/discussions/*",
            "github.com/*/pull/*",
        },
        "WebURLParser": {"http://*", "https://*"},
    }

    def get_supported_extensions(self) -> set[str]:
        extensions = set()
        for parser in self._parsers:
            parser_name = parser.__class__.__name__
            if parser_name in self._PARSER_EXTENSIONS:
                extensions.update(self._PARSER_EXTENSIONS[parser_name])
        return extensions

    def list_parsers(self) -> list[str]:
        return [parser.__class__.__name__ for parser in self._parsers]


def create_default_registry(
    include_pdf: bool = True,
    include_excel: bool = True,
    include_markdown: bool = True,
    include_ocr: bool = True,
    include_url: bool = True,
    include_docx: bool = True,
    include_pptx: bool = True,
    pdf_ocr_fallback: bool = False,
    pdf_ocr_lang: str = "eng",
) -> ParserRegistry:
    registry = ParserRegistry()

    if include_url:
        try:
            from .url import GitHubURLParser, WebURLParser

            registry.register(GitHubURLParser())
            registry.register(WebURLParser())
        except ImportError:
            pass  # URL dependencies not installed

    if include_pdf:
        try:
            from .pdf import PyMuPDFTextParser

            registry.register(
                PyMuPDFTextParser(
                    ocr_fallback=pdf_ocr_fallback,
                    ocr_lang=pdf_ocr_lang,
                )
            )
        except ImportError:
            pass  # PDF dependencies not installed

    if include_excel:
        try:
            from .excel import ExcelParser

            registry.register(ExcelParser())
        except ImportError:
            pass  # Excel dependencies not installed

    if include_markdown:
        try:
            from .markdown import MarkdownParser

            registry.register(MarkdownParser())
        except ImportError:
            pass  # Should not fail, no external deps

    if include_ocr:
        try:
            from .image_ocr import TesseractOCRParser

            registry.register(TesseractOCRParser())
        except ImportError:
            pass  # OCR dependencies not installed

    if include_docx:
        try:
            from .docx import DocxParser

            registry.register(DocxParser())
        except ImportError:
            pass  # DOCX dependencies not installed

    if include_pptx:
        try:
            from .pptx import PptxParser

            registry.register(PptxParser())
        except ImportError:
            pass  # PPTX dependencies not installed

    return registry


def parse_file(source: str) -> ParsedDocument:
    registry = create_default_registry()
    return registry.parse(source)


def parse_files(sources: list[str]) -> list[ParsedDocument]:
    registry = create_default_registry()
    documents = []

    for source in sources:
        try:
            doc = registry.parse(source)
            documents.append(doc)
        except Exception as e:
            # Create a document with error info
            documents.append(
                ParsedDocument(
                    source_path=source,
                    source_type="error",
                    title=Path(source).name,
                    content="",
                    parse_warnings=[f"Failed to parse: {e}"],
                )
            )

    return documents
