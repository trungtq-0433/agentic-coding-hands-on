#!/usr/bin/env python3
"""Rebuild a PDF with translated text inserted in-place (text-only redaction + HTML re-insertion)."""
import html
import io
import multiprocessing as mp
import os
import shutil
import tempfile

import pymupdf
from pymupdf import sRGB_to_rgb

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

CSS_TEMPLATE = (
    "@font-face {font-family: 'Noto Sans'; src: url(NotoSans-Regular.ttf);}\n"
    "@font-face {font-family: 'Noto Sans'; font-weight: bold; src: url(NotoSans-Bold.ttf);}\n"
    "@font-face {font-family: 'Noto Sans'; font-style: italic; src: url(NotoSans-Italic.ttf);}\n"
    "@font-face {font-family: 'Noto Sans'; font-weight: bold; font-style: italic;"
    " src: url(NotoSans-BoldItalic.ttf);}\n"
    "@font-face {font-family: 'Noto Sans JP'; src: url(NotoSansJP-Regular.ttf);}\n"
    "* {font-family: 'Noto Sans', 'Noto Sans JP', sans-serif;}\n"
)

TOTAL_ELEMENTS_BUDGET = 800  # ~5 GB peak memory across workers

_BUSY_COUNT = None


def _init_pool(counter):
    global _BUSY_COUNT
    _BUSY_COUNT = counter


def _color_to_rgb(color_int):
    try:
        return sRGB_to_rgb(color_int)
    except Exception:
        return (0, 0, 0)


def _is_overflow(ret):
    """True if insert_htmlbox spare_height < 0 (text did not fit into bbox)."""
    return isinstance(ret, (tuple, list)) and ret[0] < 0


def _create_html(translated_text, spans, type_="normal", ocr_attrs=None):
    """Build HTML snippet for insert_htmlbox."""
    safe = html.escape(translated_text)
    if type_ == "ocr" and ocr_attrs:
        bg = ocr_attrs.get("background_color", (255, 255, 255))
        fg = ocr_attrs.get("text_color", (0, 0, 0))
        return f'<div style="background-color: rgb{bg};"><span style="color: rgb{fg};">{safe}</span></div>'
    if not spans:
        return f"<span>{safe}</span>"
    s = spans[0]
    r, g, b = _color_to_rgb(s["font_color"])
    styles = [f"font-size: {s['font_size']}px;", f"color: rgb({r},{g},{b});"]
    if s.get("bold"):
        styles.append("font-weight: bold;")
    if s.get("italic"):
        styles.append("font-style: italic;")
    return f'<span style="{" ".join(styles)}">{safe}</span>'


def _temp_save(doc, page_path):
    """Incremental garbage-collecting save; reopen to free memory."""
    tmp = page_path + ".tmp"
    doc.ez_save(tmp, garbage=4)
    doc.close()
    os.replace(tmp, page_path)
    return pymupdf.open(page_path)


def _process_page(page_path, page_elements, structure, fonts_dir, css, autofit=False):
    """Multiprocessing worker: insert translated HTML into a single-page temp PDF.

    Returns dict {elem_id: insert_htmlbox_return} for fit validation.
    """
    global _BUSY_COUNT
    if not page_elements:
        return {}

    if _BUSY_COUNT is not None:
        with _BUSY_COUNT.get_lock():
            _BUSY_COUNT.value += 1

    fit_results = {}
    try:
        doc = pymupdf.open(page_path)
        count = 0
        for elem in page_elements:
            elem_id = elem["id"]
            info = structure.get(elem_id, {})
            bbox = info.get("bbox")
            if bbox is None:
                continue
            ocr_attrs = info.get("ocr_attrs")
            type_ = "ocr" if ocr_attrs else "normal"
            html = _create_html(
                elem["translated_text"], info.get("spans", []), type_, ocr_attrs
            )
            font_size = info.get("spans", [{}])[0].get("font_size", 10) if info.get("spans") else 10

            if autofit:
                floor_size = max(4, font_size - 6)
                ret = doc[0].insert_htmlbox(rect=bbox, text=html, css=css, archive=fonts_dir)
                while _is_overflow(ret) and font_size > floor_size:
                    font_size -= 1
                    html = _create_html(elem["translated_text"],
                                        [{**s, "font_size": font_size} for s in info.get("spans", [{}])],
                                        type_, ocr_attrs)
                    ret = doc[0].insert_htmlbox(rect=bbox, text=html, css=css, archive=fonts_dir)
            else:
                ret = doc[0].insert_htmlbox(rect=bbox, text=html, css=css, archive=fonts_dir)

            fit_results[elem_id] = ret
            count += 1

            busy_now = max(1, _BUSY_COUNT.value if _BUSY_COUNT is not None else 1)
            if count >= max(1, TOTAL_ELEMENTS_BUDGET // busy_now):
                doc = _temp_save(doc, page_path)
                count = 0

        _temp_save(doc, page_path)
    finally:
        if _BUSY_COUNT is not None:
            with _BUSY_COUNT.get_lock():
                _BUSY_COUNT.value -= 1

    return fit_results


def rebuild(pdf_path, translated_elements, structure, out_path, fonts_dir=None, css=None, autofit=False):
    """Rebuild PDF with translated text in original bboxes. Returns {elem_id: insert_htmlbox ret}."""
    if fonts_dir is None:
        fonts_dir = FONTS_DIR
    if css is None:
        css = CSS_TEMPLATE

    doc = pymupdf.open(pdf_path)
    num_pages = doc.page_count

    # Redact only text glyphs — keep images and vector graphics intact
    for page in doc:
        page.add_redact_annot(page.rect)
        page.apply_redactions(images=0, graphics=0)

    # AcroForm workaround: PyMuPDF 1.25.4 do_widgets bug crashes for page > 0
    _buf = io.BytesIO(doc.tobytes(garbage=4, deflate=True))
    doc.close()
    doc = pymupdf.open(stream=_buf, filetype="pdf")
    if doc.is_form_pdf:
        doc.xref_set_key(doc.pdf_catalog(), "AcroForm", "null")

    page_groups = {i: [] for i in range(num_pages)}
    for elem in translated_elements:
        parts = elem["id"].split("_")
        page_id = int(parts[1]) if parts[0] == "ocr" else int(parts[0])
        if page_id in page_groups:
            page_groups[page_id].append(elem)

    tmp_dir = tempfile.mkdtemp(prefix="pdf_inplace_")
    try:
        temp_paths = []
        for i in range(num_pages):
            tp = os.path.join(tmp_dir, f"page_{i}.pdf")
            pg = pymupdf.open()
            pg.insert_pdf(doc, from_page=i, to_page=i)
            pg.ez_save(tp, garbage=4)
            pg.close()
            temp_paths.append(tp)
        doc.close()

        args = [(temp_paths[i], page_groups[i], structure, fonts_dir, css, autofit) for i in range(num_pages)]
        busy_count = mp.Value("i", 0)
        with mp.Pool(mp.cpu_count(), initializer=_init_pool, initargs=(busy_count,)) as pool:
            results = pool.starmap(_process_page, args)
            pool.close()
            pool.join()

        all_fit = {}
        for r in results:
            all_fit.update(r)

        final_doc = pymupdf.open()
        for tp in temp_paths:
            final_doc.insert_pdf(pymupdf.open(tp), from_page=0, to_page=0)
        final_doc.subset_fonts(verbose=False)
        final_doc.ez_save(out_path, garbage=4)
        final_doc.close()

        return all_fit

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
