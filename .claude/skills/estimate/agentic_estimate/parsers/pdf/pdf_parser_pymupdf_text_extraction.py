"""PDF text extraction using PyMuPDF (fitz)."""

import io
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
    Section,
)


class PyMuPDFTextParser(BaseParser):
    """
    PDF parser using PyMuPDF for fast text extraction.

    Best for: Speed, general text extraction
    Limitations: Table extraction less accurate than pdfplumber
    """

    _VALID_OCR_LANG = re.compile(r"^[a-zA-Z_+]+$")
    _MAX_OCR_PAGES = 50
    _SPARSE_WORDS_PER_PAGE = 50

    def __init__(
        self,
        extract_images: bool = False,
        ocr_fallback: bool = False,
        ocr_lang: str = "eng",
    ):
        if fitz is None:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
        if not self._VALID_OCR_LANG.match(ocr_lang):
            raise ValueError(f"Invalid ocr_lang: {ocr_lang!r}")
        self.extract_images = extract_images
        self.ocr_fallback = ocr_fallback
        self.ocr_lang = ocr_lang

    def parse(self, source: str) -> ParsedDocument:
        """
        Parse PDF and extract text content.

        Args:
            source: Path to PDF file

        Returns:
            ParsedDocument with extracted text and metadata
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        try:
            doc = fitz.open(source)
        except Exception as e:
            raise ParseFailedError(f"Failed to open PDF: {e}", source, e)

        try:
            content_parts = []
            sections = []
            warnings = []
            image_count = 0

            for page_num in range(len(doc)):
                page = doc[page_num]

                text = page.get_text("text")
                if text.strip():
                    content_parts.append(text)

                page_sections = self._extract_sections_from_page(page, page_num + 1)
                sections.extend(page_sections)

                if self.extract_images:
                    image_count += len(page.get_images())

            metadata = self._extract_metadata(doc, image_count)

            if not content_parts:
                warnings.append("No text content extracted - PDF may be image-based (use OCR)")

            content = "\n\n".join(content_parts)

            # Content density metrics
            page_count = len(doc)
            word_count = len(content.split())
            words_per_page = word_count / max(page_count, 1)
            metadata["content_density"] = {
                "words_per_page": round(words_per_page, 1),
                "total_words": word_count,
                "is_sparse": words_per_page < self._SPARSE_WORDS_PER_PAGE,
            }

            # OCR fallback for sparse content
            if self.ocr_fallback and words_per_page < self._SPARSE_WORDS_PER_PAGE:
                ocr_content = self._ocr_pages(doc, warnings)
                if ocr_content:
                    content = self._merge_text_and_ocr(content, ocr_content)
                    metadata["content_density"]["ocr_applied"] = True
                    metadata["content_density"]["ocr_words"] = len(ocr_content.split())
                    warnings.append(
                        f"Sparse text detected ({words_per_page:.0f} words/page). OCR applied."
                    )

            title = metadata.get("title", "")
            if not title and sections:
                title = sections[0].title
            if not title:
                title = path.stem

            return ParsedDocument(
                source_path=source,
                source_type="pdf",
                title=title,
                content=content,
                sections=sections,
                tables=[],
                metadata=metadata,
                parse_warnings=warnings,
            )
        finally:
            doc.close()

    def _extract_sections_from_page(self, page, page_num: int) -> list[Section]:
        """
        Extract sections by analyzing text blocks and font sizes.

        Uses font size heuristics to identify headers.
        """
        sections = []

        try:
            blocks = page.get_text("dict")["blocks"]
        except Exception:
            return sections

        # Collect font sizes to determine header thresholds
        font_sizes = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span.get("size", 12))

        if not font_sizes:
            return sections

        # Calculate thresholds
        avg_size = sum(font_sizes) / len(font_sizes)
        max_size = max(font_sizes)

        # Headers are typically larger than average
        h1_threshold = max_size * 0.9
        h2_threshold = avg_size * 1.3
        h3_threshold = avg_size * 1.1

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = ""
                line_size = 0

                for span in line["spans"]:
                    line_text += span.get("text", "")
                    line_size = max(line_size, span.get("size", 12))

                line_text = line_text.strip()
                if not line_text or len(line_text) > 200:  # Skip very long lines
                    continue

                # Determine header level based on font size
                level = 0
                if line_size >= h1_threshold:
                    level = 1
                elif line_size >= h2_threshold:
                    level = 2
                elif line_size >= h3_threshold:
                    level = 3

                if level > 0:
                    # Clean up header text
                    clean_text = self._clean_header_text(line_text)
                    if clean_text:
                        sections.append(Section(level=level, title=clean_text, content=""))

        return sections

    def _clean_header_text(self, text: str) -> str:
        """Clean header text by removing common artifacts."""
        # Remove page numbers
        text = re.sub(r"^\d+\.\s*", "", text)
        text = re.sub(r"\s*\d+$", "", text)
        # Remove excessive whitespace
        text = " ".join(text.split())
        return text

    def _extract_metadata(self, doc, image_count: int) -> dict:
        """Extract PDF metadata."""
        meta = doc.metadata or {}

        return {
            "pages": len(doc),
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "created": meta.get("creationDate", ""),
            "modified": meta.get("modDate", ""),
            "images": image_count,
            "encrypted": doc.is_encrypted,
        }

    def _ocr_pages(self, doc, warnings: list[str] | None = None) -> str:
        """Render each PDF page to image and run OCR."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return ""

        ocr_parts = []
        failed_pages = 0
        pages_to_ocr = min(len(doc), self._MAX_OCR_PAGES)
        for page_num in range(pages_to_ocr):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            buf = io.BytesIO(pix.tobytes("png"))
            del pix
            img = Image.open(buf)

            try:
                text = pytesseract.image_to_string(img, lang=self.ocr_lang)
                if text.strip():
                    ocr_parts.append(f"--- Page {page_num + 1} ---\n{text.strip()}")
            except Exception:
                failed_pages += 1
                continue
            finally:
                img.close()
                buf.close()

        if failed_pages and warnings is not None:
            warnings.append(f"OCR failed on {failed_pages}/{pages_to_ocr} pages.")

        return "\n\n".join(ocr_parts)

    def _merge_text_and_ocr(self, text_content: str, ocr_content: str) -> str:
        """Merge text-layer content with OCR content."""
        if not text_content.strip():
            return ocr_content
        return f"{text_content}\n\n--- OCR Extracted Content ---\n\n{ocr_content}"

    def supports(self, source: str) -> bool:
        """Check if this parser supports the given source."""
        return source.lower().endswith(".pdf")
