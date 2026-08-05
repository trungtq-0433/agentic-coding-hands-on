#!/usr/bin/env python3
"""Convert a PDF to DOCX via pdf2docx as a bridge for the native DOCX pipeline."""
import os


def convert_pdf_to_docx(input_pdf, output_docx):
    """Convert a PDF file to DOCX using pdf2docx. Returns True on success."""
    try:
        from pdf2docx import Converter
    except ImportError:
        print("pdf2docx not installed. Install with: pip install pdf2docx")
        return False
    try:
        cv = Converter(input_pdf)
        cv.convert(output_docx)
        cv.close()
    except Exception as e:
        print(f"pdf2docx conversion failed: {e}")
        return False
    if not os.path.exists(output_docx) or os.path.getsize(output_docx) == 0:
        print("pdf2docx: output DOCX not created")
        return False
    print(f"pdf2docx: {input_pdf} → {output_docx} ({os.path.getsize(output_docx):,} bytes)")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: pdf_bridge.py <input.pdf> <output.docx>")
        sys.exit(1)
    ok = convert_pdf_to_docx(sys.argv[1], sys.argv[2])
    sys.exit(0 if ok else 1)
