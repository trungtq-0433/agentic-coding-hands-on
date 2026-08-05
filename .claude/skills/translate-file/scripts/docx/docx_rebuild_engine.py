"""Raw-XML DOCX rebuild engine — port of file-trans-poc docx_parser._insert_text."""
from __future__ import annotations

import zipfile
from io import BytesIO

from lxml import etree

from docx_extract_engine import NS, QN, _build_part_order, _remove_track_changes

# Re-use the same walk logic as extraction for order parity.
_WALK_XPATH = "//*[w:r]"
_RUN_XPATH = "./w:r"
_WT_XPATH = "./w:t"


def _create_run(comp: dict) -> etree._Element:
    """Build a w:r element from a mapped_component dict."""
    run = etree.Element(QN("r"))
    rPr = etree.SubElement(run, QN("rPr"))

    if comp.get("bold"):
        etree.SubElement(rPr, QN("b"))
    if comp.get("italic"):
        etree.SubElement(rPr, QN("i"))
    if comp.get("underline"):
        u = etree.SubElement(rPr, QN("u"))
        u.set(QN("val"), "single")
    font_size = comp.get("font_size")
    if font_size:
        try:
            sz = etree.SubElement(rPr, QN("sz"))
            sz.set(QN("val"), str(int(float(font_size) * 2)))
        except (TypeError, ValueError):
            pass
    font_color = comp.get("font_color")
    if font_color:
        color = etree.SubElement(rPr, QN("color"))
        # Normalize: list[int] → hex str
        if isinstance(font_color, list):
            try:
                font_color = "{:02X}{:02X}{:02X}".format(
                    int(font_color[0]), int(font_color[1]), int(font_color[2])
                )
            except Exception:
                font_color = None
        if font_color:
            color.set(QN("val"), str(font_color))
    font_name = comp.get("font_name")
    if font_name:
        rFonts = etree.SubElement(rPr, QN("rFonts"))
        rFonts.set(QN("ascii"), str(font_name))

    t = etree.SubElement(run, QN("t"))
    try:
        t.text = str(comp.get("text", ""))
    except ValueError:
        t.text = ""  # guard against LLM invalid characters
    # Preserve leading/trailing whitespace
    text = t.text or ""
    if text and (text[0] == " " or text[-1] == " "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return run


def _insert_into_part(root: etree._Element, mapped_by_id: dict, start_idx: int) -> int:
    """Replace original w:r stacks with mapped_components in root.

    Walks //*[w:r] identically to extraction — order parity is critical.
    Returns next global_idx after this part.
    """
    idx = start_idx
    run_parents = root.xpath(_WALK_XPATH, namespaces=NS)

    for parent in run_parents:
        current_stack: list = []

        for run in parent.xpath(_RUN_XPATH, namespaces=NS):
            has_text = run.find(_WT_XPATH, namespaces=NS) is not None
            if not has_text:
                if not current_stack:
                    continue
                # Flush: insert new runs, remove old ones
                sid = str(idx)
                if sid in mapped_by_id:
                    anchor = current_stack[0]
                    for comp in mapped_by_id[sid]:
                        anchor.addprevious(_create_run(comp))
                    for old_run in current_stack:
                        parent.remove(old_run)
                # else: leave original runs untouched (no mapping for this id)
                current_stack.clear()
                idx += 1
            else:
                current_stack.append(run)

        if current_stack:
            sid = str(idx)
            if sid in mapped_by_id:
                anchor = current_stack[0]
                for comp in mapped_by_id[sid]:
                    anchor.addprevious(_create_run(comp))
                for old_run in current_stack:
                    parent.remove(old_run)
            idx += 1

    return idx


def _save_docx(source_zip: zipfile.ZipFile, output_path: str, translated_parts: dict) -> None:
    """Write new zip: replace modified XML parts, copy everything else byte-for-byte."""
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        for item in source_zip.infolist():
            if item.filename in translated_parts:
                out_zip.writestr(item, translated_parts[item.filename])
            else:
                out_zip.writestr(item, source_zip.read(item.filename))


def rebuild(source_docx: str, mapped_by_id: dict, parts_used: list[str], output_docx: str) -> None:
    """Rebuild output_docx by injecting mapped_components into source_docx.

    mapped_by_id: {str(id): list[component_dict]}
    parts_used: ordered list from extract phase (locked order for parity)
    """
    with zipfile.ZipFile(source_docx, "r") as zf:
        all_names = set(zf.namelist())
        # Re-derive full part order (same as extraction) but only process parts_used
        full_order = _build_part_order(all_names)
        # Only rebuild parts that were extracted (others have no elements)
        rebuild_set = set(parts_used)

        translated: dict[str, bytes] = {}
        global_idx = 0

        for part in full_order:
            if part not in all_names:
                continue
            xml_bytes = zf.read(part)
            if part not in rebuild_set:
                # Still track idx for parts that were skipped (had no elements)
                # They contribute 0 elements so idx stays the same — skip
                continue
            root = etree.parse(BytesIO(xml_bytes)).getroot()
            _remove_track_changes(root)
            global_idx = _insert_into_part(root, mapped_by_id, global_idx)
            translated[part] = etree.tostring(
                root,
                pretty_print=True,
                encoding="UTF-8",
                xml_declaration=True,
                standalone=True,
            )

        _save_docx(zf, output_docx, translated)
