#!/usr/bin/env python3
"""pptx_runs.py - Per-run helpers shared by extract_pptx and build_pptx."""
from __future__ import annotations

import os
import sys

_DOCX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docx")
if _DOCX_DIR not in sys.path:
    sys.path.insert(0, _DOCX_DIR)

_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def extract_run_attrs(run) -> dict:
    """Extract TextAttr-shaped dict from a python-pptx run.

    Returns all formatting fields; None means 'inherit from theme/placeholder'.
    """
    from docx_xml_model import TextAttr

    font = run.font
    font_size = None
    try:
        if font.size:
            font_size = font.size.pt
    except Exception:
        pass

    font_color = None
    try:
        if font.color and font.color.type == 1:
            rgb = font.color.rgb
            if rgb:
                font_color = "{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2])
    except Exception:
        pass

    underline = None
    try:
        if font.underline is not None:
            underline = bool(font.underline)
    except Exception:
        pass

    hyperlink = None
    try:
        hyperlink = run.hyperlink.address
    except Exception:
        pass

    return TextAttr(
        text=run.text,
        font_size=font_size,
        bold=font.bold,
        italic=font.italic,
        underline=underline,
        font_name=font.name or None,
        font_color=font_color,
        hyperlink=hyperlink,
    ).to_dict()


def apply_components_to_paragraph(para, components: list[dict]) -> None:
    """Rebuild paragraph runs from mapped_components.

    Clears existing a:r elements, then adds one run per component preserving
    formatting. None attrs are left unset so they inherit from theme/placeholder.
    """
    if not components:
        return

    # Remove all existing a:r elements (preserve a:pPr, a:br, etc.)
    p_elem = para._p
    for r in list(p_elem.findall(f"{{{_NS_A}}}r")):
        p_elem.remove(r)

    for comp in components:
        raw_text = comp.get("text", "")
        # Guard invalid surrogate chars from LLM
        try:
            raw_text.encode("utf-16", "surrogatepass")
        except Exception:
            raw_text = raw_text.encode("utf-16", "replace").decode("utf-16", "replace")

        run = para.add_run()
        try:
            run.text = raw_text
        except Exception:
            run.text = ""

        _apply_font(run.font, comp)

        # Best-effort hyperlink (python-pptx support is limited)
        url = comp.get("hyperlink")
        if url:
            try:
                run.hyperlink.address = url
            except Exception:
                pass


def _apply_font(font, comp: dict) -> None:
    """Apply non-None formatting attrs from comp to a python-pptx font object."""
    from pptx.util import Pt
    from pptx.dml.color import RGBColor

    bold = comp.get("bold")
    if bold is not None:
        font.bold = bold

    italic = comp.get("italic")
    if italic is not None:
        font.italic = italic

    underline = comp.get("underline")
    if underline is not None:
        font.underline = underline

    font_size = comp.get("font_size")
    if font_size is not None:
        try:
            font.size = Pt(float(font_size))
        except Exception:
            pass

    font_name = comp.get("font_name")
    if font_name:
        font.name = font_name

    font_color = comp.get("font_color")
    if font_color:
        try:
            fc = str(font_color).lstrip("#")
            if len(fc) == 6:
                font.color.rgb = RGBColor(int(fc[:2], 16), int(fc[2:4], 16), int(fc[4:], 16))
        except Exception:
            pass
