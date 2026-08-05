"""Raw-XML DOCX extraction engine — port of file-trans-poc docx_parser.py."""
from __future__ import annotations

import re
import zipfile
from io import BytesIO

from lxml import etree

from docx_xml_model import TextAttr, TranslateElement

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def QN(tag: str) -> str:
    return f'{{{NS["w"]}}}{tag}'


# Locked part ordering — extract and rebuild MUST use this same sequence.
_HEADER_RE = re.compile(r"^word/header\d*\.xml$")
_FOOTER_RE = re.compile(r"^word/footer\d*\.xml$")

_FIXED_EXTRAS = (
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
)


def _build_part_order(names: set) -> list[str]:
    """Return ordered list of XML parts that contain translatable w:r runs."""
    order: list[str] = []
    if "word/document.xml" in names:
        order.append("word/document.xml")
    order.extend(sorted(n for n in names if _HEADER_RE.match(n)))
    order.extend(sorted(n for n in names if _FOOTER_RE.match(n)))
    for extra in _FIXED_EXTRAS:
        if extra in names and extra not in order:
            order.append(extra)
    return order


def _remove_track_changes(root: etree._Element) -> None:
    """Remove w:del; unwrap w:ins (move children into parent)."""
    for del_elem in root.xpath("//w:del", namespaces=NS):
        parent = del_elem.getparent()
        if parent is not None:
            parent.remove(del_elem)
    for ins_elem in root.xpath("//w:ins", namespaces=NS):
        parent = ins_elem.getparent()
        if parent is None:
            continue
        idx = list(parent).index(ins_elem)
        for child in reversed(list(ins_elem)):
            parent.insert(idx, child)
        parent.remove(ins_elem)


def _extract_elements(root: etree._Element, part: str, start_idx: int) -> tuple[list[TranslateElement], int]:
    """Walk //*[w:r] in root; accumulate run stacks into TranslateElements.

    A w:r without w:t closes the current run stack (line-break run).
    Returns (elements, next_global_idx).
    """
    elements: list[TranslateElement] = []
    idx = start_idx

    run_parents = root.xpath("//*[w:r]", namespaces=NS)
    for parent in run_parents:
        current_stack: list[TextAttr] = []

        for run in parent.xpath("./w:r", namespaces=NS):
            wt = run.find("./w:t", namespaces=NS)
            if wt is None:
                # break run — flush current stack as one element
                if not current_stack:
                    continue
                elements.append(TranslateElement(
                    id=str(idx),
                    general_text="".join(a.text for a in current_stack),
                    components=list(current_stack),
                    part=part,
                ))
                current_stack.clear()
                idx += 1
            else:
                attr = TextAttr(text=wt.text or "")
                rPr = run.find("./w:rPr", namespaces=NS)
                if rPr is not None:
                    attr.bold = rPr.find("./w:b", namespaces=NS) is not None
                    attr.italic = rPr.find("./w:i", namespaces=NS) is not None
                    attr.underline = rPr.find("./w:u", namespaces=NS) is not None
                    sz = rPr.find("./w:sz", namespaces=NS)
                    if sz is not None:
                        val = sz.get(QN("val"))
                        if val:
                            try:
                                attr.font_size = float(val) / 2.0
                            except (TypeError, ValueError):
                                pass
                    color = rPr.find("./w:color", namespaces=NS)
                    if color is not None:
                        attr.font_color = color.get(QN("val")) or None
                    fonts = rPr.find("./w:rFonts", namespaces=NS)
                    if fonts is not None:
                        attr.font_name = fonts.get(QN("ascii")) or None
                current_stack.append(attr)

        if current_stack:
            elements.append(TranslateElement(
                id=str(idx),
                general_text="".join(a.text for a in current_stack),
                components=list(current_stack),
                part=part,
            ))
            idx += 1

    return elements, idx


def extract(docx_path: str) -> tuple[list[TranslateElement], list[str]]:
    """Open docx_path, extract all TranslateElements from translatable XML parts.

    Returns (elements, parts_used) where parts_used is the ordered list of
    part names actually processed (subset of the locked part order).
    Both extract() and rebuild() MUST iterate parts_used in this same order.
    """
    with zipfile.ZipFile(docx_path, "r") as zf:
        names = set(zf.namelist())
        part_order = _build_part_order(names)

        elements: list[TranslateElement] = []
        parts_used: list[str] = []
        global_idx = 0

        for part in part_order:
            xml_bytes = zf.read(part)
            root = etree.parse(BytesIO(xml_bytes)).getroot()
            _remove_track_changes(root)
            part_elems, global_idx = _extract_elements(root, part, global_idx)
            if part_elems:
                parts_used.append(part)
                elements.extend(part_elems)

    return elements, parts_used
