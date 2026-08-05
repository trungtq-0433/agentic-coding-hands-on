#!/usr/bin/env python3
"""CLI wrapper for document parsing.

Exposes existing parsers (PDF, Excel, Markdown, OCR) to Claude via Bash tool.
Outputs JSON for easy processing.

Usage:
    python skills/estimate/scripts/parse-document.py spec.pdf
    python skills/estimate/scripts/parse-document.py *.pdf *.xlsx --merge
    python skills/estimate/scripts/parse-document.py image.png --ocr
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from agentic_estimate.parsers import (
        ParsedDocument,
        UnsupportedFormatError,
        create_default_registry,
    )
except ImportError:
    # Skill root is 2 levels up: scripts/ → estimate/
    PROJECT_ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from agentic_estimate.parsers import (
        ParsedDocument,
        UnsupportedFormatError,
        create_default_registry,
    )

# URL pattern for detecting URLs vs file paths
URL_PATTERN = re.compile(r"^https?://|^github\.com/")


def document_to_dict(doc: ParsedDocument) -> dict:
    """Convert ParsedDocument to JSON-serializable dict."""
    result = {
        "path": doc.source_path,
        "type": doc.source_type,
        "title": doc.title,
        "content": doc.content,
        "metadata": {
            "word_count": doc.get_word_count(),
            "has_tables": len(doc.tables) > 0,
            "section_count": len(doc.sections),
            **doc.metadata,
        },
    }

    if doc.sections:
        result["sections"] = [
            {"title": s.title, "level": s.level, "content": s.content[:500]} for s in doc.sections
        ]

    if doc.tables:
        result["tables"] = [{"headers": t.headers, "row_count": len(t.rows)} for t in doc.tables]

    if doc.parse_warnings:
        result["warnings"] = doc.parse_warnings

    return result


def is_url(source: str) -> bool:
    """Check if source is a URL (not a file path)."""
    return bool(URL_PATTERN.match(source))


def get_cache_path(source: str) -> Path:
    """Get .parsed.md cache path for a source file."""
    return Path(f"{source}.parsed.md")


def save_cache(source: str, content: str) -> Path:
    """Save parsed content as .parsed.md next to source file."""
    cache_path = get_cache_path(source)
    cache_path.write_text(content, encoding="utf-8")
    return cache_path


def parse_files(
    file_paths: list[str],
    merge: bool = False,
    output_format: str = "json",
    include_ocr: bool = True,
    include_url: bool = True,
    cache: bool = False,
    sheets: list[str] | None = None,
    pdf_ocr: bool = False,
    ocr_lang: str = "eng",
) -> dict:
    """Parse multiple files/URLs and return results."""
    registry = create_default_registry(
        include_ocr=include_ocr,
        include_url=include_url,
        pdf_ocr_fallback=pdf_ocr,
        pdf_ocr_lang=ocr_lang,
    )

    if sheets:
        for parser in registry._parsers:
            if hasattr(parser, "sheets"):
                parser.sheets = sheets

    supported_formats = list(registry.get_supported_extensions())
    results = {
        "files": [],
        "errors": [],
        "supported_formats": supported_formats,
    }

    merged_content = []

    for source in file_paths:
        if not is_url(source) and not Path(source).exists():
            results["errors"].append({"path": source, "error": "File not found"})
            continue

        try:
            doc = registry.parse(source)
            doc_dict = document_to_dict(doc)
            if cache and not is_url(source):
                cp = save_cache(source, doc.content)
                doc_dict["cache_path"] = str(cp)
            results["files"].append(doc_dict)
            if merge:
                label = doc.title or Path(source).name
                merged_content.append(f"## {label}\n\n{doc.content}")
        except UnsupportedFormatError:
            fmt = (
                "Unsupported URL pattern"
                if is_url(source)
                else f"Unsupported format: {Path(source).suffix}"
            )
            results["errors"].append({"path": source, "error": fmt, "supported": supported_formats})
        except Exception as e:
            results["errors"].append({"path": source, "error": str(e)})

    if merge and merged_content:
        results["merged_content"] = "\n\n---\n\n".join(merged_content)

    # Summary
    results["summary"] = {
        "total_files": len(file_paths),
        "parsed_successfully": len(results["files"]),
        "errors": len(results["errors"]),
        "total_content_length": sum(len(f.get("content", "")) for f in results["files"]),
    }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse documents (PDF, Excel, Markdown, images, URLs) to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s spec.pdf
  %(prog)s *.pdf *.xlsx --merge
  %(prog)s wireframe.png --ocr
  %(prog)s document.pdf --output text
  %(prog)s https://github.com/owner/repo/issues/123
  %(prog)s github.com/owner/repo/discussions/456
  %(prog)s https://example.com/spec.html
        """,
    )

    parser.add_argument(
        "files", nargs="+", help="Files or URLs to parse (GitHub issues/discussions/PRs, web URLs)"
    )
    parser.add_argument(
        "--merge", "-m", action="store_true", help="Merge content from all files into single output"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--ocr", action="store_true", default=True, help="Enable OCR for images (default: enabled)"
    )
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR parsing")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Save parsed content as <file>.parsed.md for future cache reads",
    )
    parser.add_argument(
        "--sheets",
        nargs="+",
        help="Specific Excel sheet names to parse (default: visible sheets only)",
    )
    parser.add_argument(
        "--pdf-ocr",
        action="store_true",
        help="Enable OCR fallback for PDFs with sparse text content",
    )
    parser.add_argument(
        "--ocr-lang",
        default="eng",
        help="OCR language (e.g., 'eng', 'jpn', 'eng+jpn'). Default: eng",
    )

    args = parser.parse_args()

    include_ocr = args.ocr and not args.no_ocr

    try:
        results = parse_files(
            args.files,
            merge=args.merge,
            output_format=args.output,
            include_ocr=include_ocr,
            cache=args.cache,
            sheets=args.sheets,
            pdf_ocr=args.pdf_ocr,
            ocr_lang=args.ocr_lang,
        )

        if args.output == "text":
            # Output plain text content only
            if args.merge and "merged_content" in results:
                print(results["merged_content"])
            else:
                for doc in results["files"]:
                    print(f"=== {doc['path']} ===\n")
                    print(doc["content"])
                    print()
        else:
            # Output JSON
            indent = 2 if args.pretty else None
            print(json.dumps(results, indent=indent, ensure_ascii=False))

    except Exception as e:
        error_result = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
