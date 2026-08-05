"""Generic web URL parser.

For URLs not handled by specific parsers (GitHub, etc.), this parser
either uses requests+html2text (if available) or returns a stub
indicating Claude should use WebFetch tool.
"""

import re

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
)


class WebURLParser(BaseParser):
    """Parser for generic web URLs."""

    URL_PATTERN = re.compile(r"^https?://")

    # URLs handled by other parsers (GitHub, etc.)
    EXCLUDED_PATTERNS = [
        re.compile(r"github\.com/[^/]+/[^/]+/(issues|discussions|pull)/\d+"),
    ]

    def __init__(self, use_requests: bool = True):
        """
        Initialize web URL parser.

        Args:
            use_requests: If True and requests/html2text available,
                         fetch content directly. Otherwise return stub.
        """
        self.use_requests = use_requests
        self._requests_available = self._check_requests()

    def _check_requests(self) -> bool:
        """Check if requests and html2text are available."""
        try:
            import html2text  # noqa: F401
            import requests  # noqa: F401

            return True
        except ImportError:
            return False

    def supports(self, source: str) -> bool:
        """Check if source is a generic web URL (not handled by other parsers)."""
        if not self.URL_PATTERN.match(source):
            return False

        # Exclude URLs handled by specific parsers
        for pattern in self.EXCLUDED_PATTERNS:
            if pattern.search(source):
                return False

        return True

    def parse(self, source: str) -> ParsedDocument:
        """Parse web URL and return content."""
        if self.use_requests and self._requests_available:
            return self._fetch_with_requests(source)
        else:
            return self._create_stub(source)

    def _fetch_with_requests(self, source: str) -> ParsedDocument:
        """Fetch URL content using requests and convert HTML to markdown."""
        import html2text
        import requests

        try:
            response = requests.get(
                source,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AgenticEstimate/1.0)"},
            )
            response.raise_for_status()

            # Convert HTML to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.ignore_emphasis = False
            h.body_width = 0  # No wrapping

            content = h.handle(response.text)

            # Extract title from content or URL
            title = self._extract_title(response.text) or source

            return ParsedDocument(
                source_path=source,
                source_type="web-url",
                title=title,
                content=content,
                metadata={
                    "url": source,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(response.text),
                },
            )

        except requests.RequestException as e:
            raise ParseFailedError(f"Failed to fetch URL: {e}", source)

    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML."""
        import re

        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _create_stub(self, source: str) -> ParsedDocument:
        """Create a stub document indicating Claude should use WebFetch."""
        content = f"""# Web URL Content Required

**URL:** {source}

This URL requires fetching. Claude should use the **WebFetch** tool to retrieve the content.

## Instructions for Claude

Use the WebFetch tool with this URL:
```
WebFetch: {source}
```

Then process the returned content for estimation.

## Why This Stub?

The `requests` or `html2text` Python packages are not installed.
To enable direct fetching, install:

```bash
pip install requests html2text
```
"""

        return ParsedDocument(
            source_path=source,
            source_type="web-url-stub",
            title=f"Fetch Required: {source}",
            content=content,
            metadata={
                "url": source,
                "requires_fetch": True,
                "fetch_tool": "WebFetch",
            },
            parse_warnings=[
                "Content not fetched. Use WebFetch tool or install: pip install requests html2text"
            ],
        )
