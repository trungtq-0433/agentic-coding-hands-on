"""OCR parsing using Tesseract."""

from pathlib import Path

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
)


class TesseractOCRParser(BaseParser):
    """
    OCR parser using Tesseract for image-to-text extraction.

    Supports: PNG, JPG, JPEG, TIFF, BMP, GIF
    Requirements: Tesseract-OCR installed on system
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"}

    def __init__(
        self,
        lang: str = "eng",
        confidence_threshold: int = 60,
        tesseract_cmd: str | None = None,
    ):
        """
        Initialize Tesseract OCR parser.

        Args:
            lang: OCR language (e.g., 'eng', 'vie', 'eng+vie')
            confidence_threshold: Minimum confidence to include text (0-100)
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        if pytesseract is None or Image is None:
            raise ImportError(
                "pytesseract and Pillow not installed. Run: pip install pytesseract pillow"
            )

        self.lang = lang
        self.confidence_threshold = confidence_threshold

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def parse(self, source: str) -> ParsedDocument:
        """
        Parse image file using OCR.

        Args:
            source: Path to image file

        Returns:
            ParsedDocument with extracted text
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        try:
            image = Image.open(source)
        except Exception as e:
            raise ParseFailedError(f"Failed to open image: {e}", source, e)

        warnings = []

        # Get image info
        image_size = image.size
        image_mode = image.mode

        # Convert to RGB if necessary
        if image_mode not in ("L", "RGB"):
            image = image.convert("RGB")

        # Perform OCR with detailed output
        try:
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as e:
            raise ParseFailedError(f"OCR failed: {e}", source, e)

        # Extract text with confidence filtering
        text_parts = []
        confidences = []
        word_count = 0

        for i, conf in enumerate(ocr_data["conf"]):
            try:
                conf_int = int(conf)
            except (ValueError, TypeError):
                continue

            if conf_int >= self.confidence_threshold:
                word = ocr_data["text"][i]
                if word and word.strip():
                    text_parts.append(word)
                    confidences.append(conf_int)
                    word_count += 1

        content = " ".join(text_parts)

        # Clean up content
        content = self._clean_ocr_text(content)

        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Add warnings for low quality
        if avg_confidence < 70:
            warnings.append(f"Low OCR confidence ({avg_confidence:.1f}%). Consider manual review.")
        if word_count < 10:
            warnings.append("Very few words extracted. Image may be low quality or non-text.")

        # Build metadata
        metadata = {
            "image_size": image_size,
            "image_width": image_size[0],
            "image_height": image_size[1],
            "image_mode": image_mode,
            "ocr_language": self.lang,
            "avg_confidence": round(avg_confidence, 2),
            "word_count": word_count,
            "confidence_threshold": self.confidence_threshold,
        }

        image.close()

        return ParsedDocument(
            source_path=source,
            source_type="image-ocr",
            title=path.stem,
            content=content,
            sections=[],
            tables=[],
            metadata=metadata,
            parse_warnings=warnings,
        )

    def _clean_ocr_text(self, text: str) -> str:
        """Clean common OCR artifacts."""
        # Normalize whitespace
        text = " ".join(text.split())

        # Common OCR error corrections
        replacements = [
            ("  ", " "),
            (" ,", ","),
            (" .", "."),
            (" :", ":"),
            ("( ", "("),
            (" )", ")"),
        ]

        for old, new in replacements:
            text = text.replace(old, new)

        return text.strip()

    def supports(self, source: str) -> bool:
        """Check if this parser supports the given source."""
        suffix = Path(source).suffix.lower()
        return suffix in self.SUPPORTED_EXTENSIONS

    def get_available_languages(self) -> list[str]:
        """Get list of available OCR languages."""
        try:
            languages = pytesseract.get_languages()
            return [lang for lang in languages if lang != "osd"]
        except Exception:
            return ["eng"]

    def parse_with_preprocessing(
        self,
        source: str,
        grayscale: bool = True,
        threshold: bool = False,
        denoise: bool = False,
    ) -> ParsedDocument:
        """
        Parse image with preprocessing for better OCR results.

        Args:
            source: Path to image file
            grayscale: Convert to grayscale
            threshold: Apply binary threshold
            denoise: Apply denoising (requires opencv)

        Returns:
            ParsedDocument with extracted text
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        image = Image.open(source)

        # Preprocessing
        if grayscale:
            image = image.convert("L")

        if threshold:
            # Simple threshold
            image = image.point(lambda x: 255 if x > 128 else 0, mode="1")

        # Continue with standard parsing
        try:
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.lang,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as e:
            raise ParseFailedError(f"OCR failed: {e}", source, e)

        text_parts = []
        confidences = []

        for i, conf in enumerate(ocr_data["conf"]):
            try:
                conf_int = int(conf)
            except (ValueError, TypeError):
                continue

            if conf_int >= self.confidence_threshold:
                word = ocr_data["text"][i]
                if word and word.strip():
                    text_parts.append(word)
                    confidences.append(conf_int)

        content = self._clean_ocr_text(" ".join(text_parts))
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        image.close()

        return ParsedDocument(
            source_path=source,
            source_type="image-ocr",
            title=path.stem,
            content=content,
            metadata={
                "ocr_language": self.lang,
                "avg_confidence": round(avg_confidence, 2),
                "preprocessing": {
                    "grayscale": grayscale,
                    "threshold": threshold,
                    "denoise": denoise,
                },
            },
        )
