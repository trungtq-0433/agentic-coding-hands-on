#!/usr/bin/env python3
"""
docx_containers.py - Raw-XML extraction + write-back for DOCX containers.

Covers:
  - Text boxes (w:txbxContent in word/document.xml)
  - Comments (word/comments.xml)

Also provides track-changes normalization: w:del removed, w:ins unwrapped.
Container paragraphs share the [P:N] index namespace with body elements.
"""

import os
import re
import zipfile
from io import BytesIO

try:
    from lxml import etree
except ImportError:
    etree = None

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_XML_NS = "http://www.w3.org/XML/1998/namespace"
_WNS = {"w": _W}
_INLINE_MD_RE = re.compile(r"\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*", re.DOTALL)


def _qn(local):
    return f"{{{_W}}}{local}"


# ---------------------------------------------------------------------------
# Track-changes normalization
# ---------------------------------------------------------------------------

def remove_track_changes(root):
    """Remove w:del; unwrap w:ins children in an lxml tree in-place."""
    for elem in root.xpath("//w:del", namespaces=_WNS):
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
    for elem in list(root.xpath("//w:ins", namespaces=_WNS)):
        parent = elem.getparent()
        if parent is None:
            continue
        pos = list(parent).index(elem)
        for i, child in enumerate(list(elem)):
            parent.insert(pos + i, child)
        parent.remove(elem)


# ---------------------------------------------------------------------------
# Run metadata helpers
# ---------------------------------------------------------------------------

def _xml_run_meta(run_elem):
    """Extract metadata dict from a raw w:r lxml element."""
    texts = []
    for child in run_elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "t":
            texts.append(child.text or "")
        elif tag == "br" and child.get(_qn("type"), "") in ("", "textWrapping"):
            texts.append("\n")
        elif tag == "tab":
            texts.append("\t")

    meta = {"text": "".join(texts), "bold": None, "italic": None, "underline": None,
            "font_name": None, "font_size_pt": None, "color_rgb": None}

    rpr = run_elem.find(_qn("rPr"))
    if rpr is None:
        return meta
    b_elem = rpr.find(_qn("b"))
    meta["bold"] = b_elem is not None and b_elem.get(_qn("val"), "1") != "0"
    i_elem = rpr.find(_qn("i"))
    meta["italic"] = i_elem is not None and i_elem.get(_qn("val"), "1") != "0"
    u = rpr.find(_qn("u"))
    if u is not None:
        meta["underline"] = u.get(_qn("val"), "single") != "none"
    sz = rpr.find(_qn("sz"))
    if sz is not None:
        try:
            meta["font_size_pt"] = float(sz.get(_qn("val"), 0)) / 2.0
        except (TypeError, ValueError):
            pass
    clr = rpr.find(_qn("color"))
    if clr is not None:
        val = clr.get(_qn("val"))
        if val and val.upper() not in ("AUTO",):
            meta["color_rgb"] = val
    fonts = rpr.find(_qn("rFonts"))
    if fonts is not None:
        meta["font_name"] = fonts.get(_qn("ascii"))
    return meta


def _runs_meta_to_md(runs_meta):
    """Convert run metadata list to inline-markdown text (bold/italic only)."""
    parts = []
    for r in runs_meta:
        t = r.get("text", "")
        if not t:
            continue
        if r.get("bold") and r.get("italic"):
            parts.append(f"***{t}***")
        elif r.get("bold"):
            parts.append(f"**{t}**")
        elif r.get("italic"):
            parts.append(f"*{t}*")
        else:
            parts.append(t)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_containers(docx_path, base_idx, profile=None):
    """Extract container paragraphs (textboxes + comments) from DOCX zip.

    Returns (items, all_elements, next_idx).
    items: list of (md_text, meta_dict) for translatable content.
    all_elements: all elements including empty paragraphs.
    """
    if etree is None:
        return [], [], base_idx

    items, all_elements = [], []
    idx = base_idx
    translate_comments = True if profile is None else profile.get("translate_comments", True)

    with zipfile.ZipFile(docx_path, "r") as zf:
        names = set(zf.namelist())

        # Text boxes from document.xml
        if "word/document.xml" in names:
            root = etree.parse(BytesIO(zf.read("word/document.xml"))).getroot()
            remove_track_changes(root)

            for tb_idx, txbx in enumerate(root.iter(_qn("txbxContent"))):
                for p_idx, p_elem in enumerate(txbx.findall(_qn("p"))):
                    runs_meta = [_xml_run_meta(r) for r in p_elem.iter(_qn("r"))]
                    text = _runs_meta_to_md(runs_meta).strip()
                    meta = {
                        "elem_idx": idx, "type": "textbox_paragraph",
                        "part": "word/document.xml",
                        "container_idx": tb_idx, "para_idx": p_idx,
                        "runs": runs_meta,
                    }
                    all_elements.append(meta)
                    if text:
                        items.append((f"[P:{idx}] {text}", meta))
                    idx += 1

        # Comments from word/comments.xml
        if translate_comments and "word/comments.xml" in names:
            root = etree.parse(BytesIO(zf.read("word/comments.xml"))).getroot()
            remove_track_changes(root)

            for comment_elem in root.findall(_qn("comment")):
                comment_id = comment_elem.get(_qn("id"), "")
                for p_idx, p_elem in enumerate(comment_elem.findall(_qn("p"))):
                    runs_meta = [_xml_run_meta(r) for r in p_elem.iter(_qn("r"))]
                    text = _runs_meta_to_md(runs_meta).strip()
                    meta = {
                        "elem_idx": idx, "type": "comment_paragraph",
                        "part": "word/comments.xml",
                        "comment_id": comment_id, "para_idx": p_idx,
                        "runs": runs_meta,
                    }
                    all_elements.append(meta)
                    if text:
                        items.append((f"[P:{idx}] {text}", meta))
                    idx += 1

    return items, all_elements, idx


# ---------------------------------------------------------------------------
# Write-back helpers
# ---------------------------------------------------------------------------

def _parse_inline_md(text):
    """Parse ***bold+italic***, **bold**, *italic* → (text, bold, italic) tuples."""
    segments, last_end = [], 0
    for m in _INLINE_MD_RE.finditer(text):
        if m.start() > last_end:
            segments.append((text[last_end:m.start()], None, None))
        g1, g2, g3 = m.group(1), m.group(2), m.group(3)
        if g1 is not None:
            segments.append((g1, True, True))
        elif g2 is not None:
            segments.append((g2, True, None))
        else:
            segments.append((g3, None, True))
        last_end = m.end()
    if last_end < len(text):
        segments.append((text[last_end:], None, None))
    return segments or [(text, None, None)]


def _build_rpr(rpr, meta, bold_override=None, italic_override=None):
    """Populate a w:rPr lxml element from meta dict + optional overrides."""
    b = bold_override if bold_override is not None else meta.get("bold")
    i = italic_override if italic_override is not None else meta.get("italic")
    if b:
        etree.SubElement(rpr, _qn("b"))
    if i:
        etree.SubElement(rpr, _qn("i"))
    if meta.get("underline"):
        u = etree.SubElement(rpr, _qn("u"))
        u.set(_qn("val"), "single")
    if meta.get("font_size_pt"):
        sz = etree.SubElement(rpr, _qn("sz"))
        sz.set(_qn("val"), str(int(meta["font_size_pt"] * 2)))
    if meta.get("color_rgb"):
        clr = etree.SubElement(rpr, _qn("color"))
        clr.set(_qn("val"), meta["color_rgb"].lstrip("#"))
    if meta.get("font_name"):
        rf = etree.SubElement(rpr, _qn("rFonts"))
        rf.set(_qn("ascii"), meta["font_name"])
        rf.set(_qn("hAnsi"), meta["font_name"])


def _set_xml_para_text(p_elem, text, runs_meta):
    """Replace w:r children in p_elem with new runs for translated text."""
    # Always clear existing runs — even empty translation must not leave source text
    for r in list(p_elem.findall(_qn("r"))):
        p_elem.remove(r)
    if not text:
        return

    base_meta = runs_meta[0] if runs_meta else {}
    for seg_text, bold, italic in _parse_inline_md(text):
        if not seg_text:
            continue
        r_elem = etree.SubElement(p_elem, _qn("r"))
        rpr = etree.SubElement(r_elem, _qn("rPr"))
        _build_rpr(rpr, base_meta, bold, italic)
        t_elem = etree.SubElement(r_elem, _qn("t"))
        t_elem.text = seg_text
        if seg_text[0] == " " or seg_text[-1] == " ":
            t_elem.set(f"{{{_XML_NS}}}space", "preserve")


def _modify_xml_part(xml_bytes, part_metas, translations):
    """Modify an XML part's bytes by injecting container translations."""
    root = etree.parse(BytesIO(xml_bytes)).getroot()

    tb_map = {}   # (container_idx, para_idx) -> p_elem
    cm_map = {}   # (comment_id, para_idx)    -> p_elem

    for tb_idx, txbx in enumerate(root.iter(_qn("txbxContent"))):
        for p_idx, p_elem in enumerate(txbx.findall(_qn("p"))):
            tb_map[(tb_idx, p_idx)] = p_elem

    for comment in root.findall(_qn("comment")):
        cid = comment.get(_qn("id"), "")
        for p_idx, p_elem in enumerate(comment.findall(_qn("p"))):
            cm_map[(cid, p_idx)] = p_elem

    for meta in part_metas:
        text = translations.get(meta["elem_idx"])
        if text is None:
            continue
        if meta["type"] == "textbox_paragraph":
            p_elem = tb_map.get((meta["container_idx"], meta["para_idx"]))
        elif meta["type"] == "comment_paragraph":
            p_elem = cm_map.get((meta["comment_id"], meta["para_idx"]))
        else:
            continue
        if p_elem is not None:
            _set_xml_para_text(p_elem, text, meta.get("runs", []))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def write_back_containers(output_docx, elem_index, translations):
    """Inject container translations into output_docx via in-place zip replacement."""
    if etree is None:
        return

    # Group container elements by their XML part
    part_to_metas = {}
    for idx, meta in elem_index.items():
        if meta.get("type") not in ("textbox_paragraph", "comment_paragraph"):
            continue
        if idx not in translations:
            continue
        part = meta.get("part", "")
        if part not in part_to_metas:
            part_to_metas[part] = []
        part_to_metas[part].append(meta)

    if not part_to_metas:
        return

    tmp = output_docx + ".ctmp"
    with zipfile.ZipFile(output_docx, "r") as zin, \
         zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in part_to_metas:
                data = _modify_xml_part(data, part_to_metas[item.filename], translations)
            zout.writestr(item, data)

    os.replace(tmp, output_docx)
