"""PDF table extraction using pdfplumber."""

from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from ..parser_base_classes_and_data_models import (
    ParseFailedError,
    Table,
)


class PDFTableExtractor:
    """
    PDF table extractor using pdfplumber.

    Best for: Accurate table extraction
    Use alongside PyMuPDFTextParser for complete PDF parsing.
    """

    def __init__(self, min_rows: int = 2, min_cols: int = 2):
        """
        Initialize table extractor.

        Args:
            min_rows: Minimum rows for valid table
            min_cols: Minimum columns for valid table
        """
        if pdfplumber is None:
            raise ImportError("pdfplumber not installed. Run: pip install pdfplumber")
        self.min_rows = min_rows
        self.min_cols = min_cols

    def extract_tables(self, source: str) -> list[Table]:
        """
        Extract all tables from a PDF.

        Args:
            source: Path to PDF file

        Returns:
            List of Table objects
        """
        path = Path(source)
        if not path.exists():
            raise ParseFailedError(f"File not found: {source}", source)

        tables = []

        try:
            with pdfplumber.open(source) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = self._extract_page_tables(page, page_num)
                    tables.extend(page_tables)
        except Exception as e:
            raise ParseFailedError(f"Failed to extract tables: {e}", source, e)

        return tables

    def _extract_page_tables(self, page, page_num: int) -> list[Table]:
        """Extract tables from a single page."""
        tables = []

        try:
            extracted = page.extract_tables()
        except Exception:
            return tables

        for table_idx, table_data in enumerate(extracted):
            if not table_data:
                continue

            # Filter out invalid tables
            if len(table_data) < self.min_rows:
                continue
            if any(len(row) < self.min_cols for row in table_data[:2]):
                continue

            # Clean table data
            cleaned = self._clean_table_data(table_data)
            if not cleaned:
                continue

            # First row as headers
            headers = cleaned[0]
            rows = cleaned[1:]

            table = Table(
                headers=headers,
                rows=rows,
                caption=f"Page {page_num}, Table {table_idx + 1}",
            )
            tables.append(table)

        return tables

    def _clean_table_data(self, table_data: list[list]) -> list[list[str]]:
        """Clean and normalize table data."""
        cleaned = []

        for row in table_data:
            cleaned_row = []
            for cell in row:
                # Convert to string and clean
                if cell is None:
                    cell_str = ""
                else:
                    cell_str = str(cell).strip()
                    # Remove excessive newlines
                    cell_str = " ".join(cell_str.split())
                cleaned_row.append(cell_str)
            cleaned.append(cleaned_row)

        # Remove empty rows
        cleaned = [row for row in cleaned if any(cell for cell in row)]

        return cleaned

    def extract_tables_with_settings(
        self,
        source: str,
        table_settings: dict | None = None,
    ) -> list[Table]:
        """
        Extract tables with custom pdfplumber settings.

        Args:
            source: Path to PDF file
            table_settings: pdfplumber table extraction settings

        Returns:
            List of Table objects
        """
        if table_settings is None:
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
                "join_tolerance": 3,
            }

        tables = []

        try:
            with pdfplumber.open(source) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        extracted = page.extract_tables(table_settings)
                        for table_idx, table_data in enumerate(extracted):
                            if not table_data or len(table_data) < self.min_rows:
                                continue

                            cleaned = self._clean_table_data(table_data)
                            if not cleaned:
                                continue

                            table = Table(
                                headers=cleaned[0],
                                rows=cleaned[1:],
                                caption=f"Page {page_num}, Table {table_idx + 1}",
                            )
                            tables.append(table)
                    except Exception:
                        continue
        except Exception as e:
            raise ParseFailedError(f"Failed to extract tables: {e}", source, e)

        return tables
