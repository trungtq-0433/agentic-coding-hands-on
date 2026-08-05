#!/usr/bin/env python3
"""Build a polished, client-facing System Overview .docx from a Markdown source.

Self-contained: depends only on `pandoc` (CLI) + Python stdlib. No reference template
required — all styling (Arial, navy heading palette, bordered tables with shaded header,
cover page, per-section page breaks, table spacing, page-numbered footer + title header)
is applied by post-processing the OOXML that pandoc emits.

Used by the rebuild-spec `--overview` pass (OV.4). Safe to run standalone:

    python3 build_overview_docx.py <input.md> <output.docx> [--header "..."]

(The document title/H1 comes from the Markdown's first heading; only --header is configurable.)

Idempotent: regenerates the .docx from the .md each run.
Stdlib + pandoc only — no pip installs.

Hard gate: after building, the .docx is round-tripped through pandoc (reopened) — a file that
does not reopen cleanly (invalid OOXML) fails the build with exit 2 instead of shipping broken.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

# ── styling constants (the "đẹp dễ nhìn" palette, baked in) ──────────────────
FONT = "Arial"
NAVY_TITLE = "1A365D"   # Title + Heading1
BLUE_H2 = "2C5282"      # Heading2 (also table header fill)
BLUE_H3 = "1F4D78"      # Heading3
HDR_FILL = "2C5282"     # table header row fill
ZEBRA_FILL = "F2F6FB"   # alternating row fill
BORDER = "808080"       # table outer border
BORDER_INNER = "BFBFBF" # table inner gridlines

# half-point sizes
SZ = {"Title": "56", "Heading1": "32", "Heading2": "26", "Heading3": "24"}
COLOR = {"Title": NAVY_TITLE, "Heading1": NAVY_TITLE, "Heading2": BLUE_H2, "Heading3": BLUE_H3}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def pandoc_to_docx(src_md: str, out_docx: str) -> None:
    run(["pandoc", src_md, "--from", "gfm", "-o", out_docx])


# ── styles.xml patches ───────────────────────────────────────────────────────

def set_default_font(styles: str) -> str:
    """Force Arial as the document default font (docDefaults > rPrDefault > rFonts)."""
    def repl(m: re.Match) -> str:
        block = m.group(0)
        if "<w:rFonts" in block:
            block = re.sub(r"<w:rFonts[^/]*/>",
                           f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>',
                           block, count=1)
        else:
            block = block.replace("<w:rPr>",
                                  f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>', 1)
        return block
    m = re.search(r"<w:docDefaults>.*?</w:docDefaults>", styles, re.S)
    if not m:
        return styles
    return styles[:m.start()] + repl(m) + styles[m.end():]


def _ensure_in_rpr(block: str, inner: str, tag_re: str) -> str:
    """Insert `inner` into the style's first <w:rPr>; replace existing tag if present."""
    rpr = re.search(r"<w:rPr>.*?</w:rPr>", block, re.S)
    if rpr:
        body = rpr.group(0)
        body2 = re.sub(tag_re, "", body)               # drop any existing instance
        body2 = body2.replace("<w:rPr>", "<w:rPr>" + inner, 1)
        return block[:rpr.start()] + body2 + block[rpr.end():]
    # no rPr → add one right before </w:style>
    return block.replace("</w:style>", f"<w:rPr>{inner}</w:rPr></w:style>", 1)


def style_heading(styles: str, style_id: str, page_break: bool = False) -> str:
    """Apply Arial + size + color (+ bold) to a heading/title style; optional pageBreakBefore."""
    m = re.search(rf'<w:style [^>]*w:styleId="{style_id}"[^>]*>.*?</w:style>', styles, re.S)
    if not m:
        return styles
    block = m.group(0)
    # rPr: font, size, color, bold
    block = _ensure_in_rpr(block, f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/>', r"<w:rFonts[^/]*/>")
    block = _ensure_in_rpr(block, f'<w:sz w:val="{SZ[style_id]}"/>', r'<w:sz w:val="\d+"/>')
    block = _ensure_in_rpr(block, f'<w:color w:val="{COLOR[style_id]}"/>', r'<w:color w:val="[0-9A-Fa-f]+"/>')
    if "<w:b/>" not in block and "<w:b " not in block:
        block = _ensure_in_rpr(block, "<w:b/>", r"(?!)")  # no-op tag_re → just prepend
    # pPr: pageBreakBefore on/off
    if page_break:
        if "<w:pageBreakBefore" in block:
            block = re.sub(r'<w:pageBreakBefore[^/]*/>', '<w:pageBreakBefore w:val="1"/>', block, count=1)
        elif "<w:pPr>" in block:
            block = block.replace("<w:pPr>", "<w:pPr><w:pageBreakBefore w:val=\"1\"/>", 1)
        else:
            block = re.sub(r'(<w:style [^>]*>)', r'\1<w:pPr><w:pageBreakBefore w:val="1"/></w:pPr>', block, count=1)
    return styles[:m.start()] + block + styles[m.end():]


def add_table_style(styles: str) -> str:
    based_on = '<w:basedOn w:val="TableNormal"/>' if 'w:styleId="TableNormal"' in styles else ''
    ts = (
        '<w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/>' + based_on +
        '<w:tblPr><w:tblBorders>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{BORDER_INNER}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{BORDER_INNER}"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        '<w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:color w:val="FFFFFF"/></w:rPr>'
        f'<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{HDR_FILL}"/></w:tcPr></w:tblStylePr>'
        '<w:tblStylePr w:type="band1Horz"><w:tcPr>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{ZEBRA_FILL}"/></w:tcPr></w:tblStylePr></w:style>'
    )
    pat = re.compile(r'<w:style w:type="table" w:styleId="Table">.*?</w:style>', re.S)
    return pat.sub(ts, styles) if pat.search(styles) else styles.replace("</w:styles>", ts + "</w:styles>")


# ── document.xml patches ───────────────────────────────────────────────────────

def patch_document(doc: str) -> str:
    # cover: first heading (the lone "# Title") → Title style
    doc = doc.replace('<w:pStyle w:val="Heading1" />', '<w:pStyle w:val="Title" />', 1)
    doc = doc.replace('<w:pStyle w:val="Heading1"/>', '<w:pStyle w:val="Title"/>', 1)
    # zebra banding: enable horizontal bands in every table's tblLook
    doc = doc.replace('w:noHBand="0" w:noVBand="0" w:val="0020"', 'w:noHBand="0" w:noVBand="1" w:val="0420"')
    # table spacing: blank paragraph before + after every table
    doc = doc.replace("<w:tbl>", "<w:p/><w:tbl>")
    doc = doc.replace("</w:tbl>", "</w:tbl><w:p/>")
    return doc


# ── header / footer parts (created from scratch — self-contained) ─────────────

HEADER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:p><w:pPr><w:jc w:val="right"/><w:rPr><w:color w:val="808080"/><w:sz w:val="16"/>'
    f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr></w:pPr>'
    '<w:r><w:rPr><w:color w:val="808080"/><w:sz w:val="16"/>'
    f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr><w:t xml:space="preserve">{{HEADER_TEXT}}</w:t></w:r></w:p></w:hdr>'
)

FOOTER_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:p><w:pPr><w:jc w:val="center"/><w:rPr><w:color w:val="808080"/><w:sz w:val="16"/>'
    f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr></w:pPr>'
    '<w:r><w:rPr><w:color w:val="808080"/><w:sz w:val="16"/>'
    f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr><w:t xml:space="preserve">Page </w:t></w:r>'
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
    '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>'
)


def add_header_footer(unpacked: str, header_text: str) -> None:
    word = os.path.join(unpacked, "word")
    with open(os.path.join(word, "header1.xml"), "w", encoding="utf-8") as f:
        f.write(HEADER_XML.replace("{HEADER_TEXT}", html.escape(header_text, quote=True)))
    with open(os.path.join(word, "footer1.xml"), "w", encoding="utf-8") as f:
        f.write(FOOTER_XML)
    # content types
    ctp = os.path.join(unpacked, "[Content_Types].xml")
    ct = open(ctp, encoding="utf-8").read()
    for part, ctype in (("header1", "header"), ("footer1", "footer")):
        ov = (f'<Override PartName="/word/{part}.xml" '
              f'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{ctype}+xml"/>')
        if part not in ct:
            ct = ct.replace("</Types>", ov + "</Types>")
    open(ctp, "w", encoding="utf-8").write(ct)
    # relationships
    relp = os.path.join(word, "_rels", "document.xml.rels")
    rels = open(relp, encoding="utf-8").read()
    ids = [int(x) for x in re.findall(r'Id="rId(\d+)"', rels)] or [0]
    hid, fid = f"rId{max(ids)+1}", f"rId{max(ids)+2}"
    add = (f'<Relationship Id="{hid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
           f'<Relationship Id="{fid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>')
    rels = rels.replace("</Relationships>", add + "</Relationships>")
    open(relp, "w", encoding="utf-8").write(rels)
    # sectPr references
    dp = os.path.join(word, "document.xml")
    d = open(dp, encoding="utf-8").read()
    refs = f'<w:headerReference r:id="{hid}" w:type="default"/><w:footerReference r:id="{fid}" w:type="default"/>'
    if "<w:sectPr" in d:
        d = re.sub(r"(<w:sectPr[^>]*>)", r"\1" + refs, d, count=1)
    else:
        d = d.replace("</w:body>", f"<w:sectPr>{refs}</w:sectPr></w:body>")
    # ensure r: namespace present on document root
    # NOTE: inspect the <w:document> tag itself, not d.split(">",1)[0] (which is the
    # <?xml ...?> declaration). pandoc already declares xmlns:r on <w:document>, so the
    # old check always fired and injected a DUPLICATE xmlns:r → invalid OOXML (Word refuses).
    _doc_tag = re.search(r"<w:document\b[^>]*>", d)
    if _doc_tag and 'xmlns:r=' not in _doc_tag.group(0):
        d = d.replace("<w:document ", '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
    open(dp, "w", encoding="utf-8").write(d)


def repack(unpacked: str, out_docx: str) -> None:
    if os.path.exists(out_docx):
        os.remove(out_docx)
    with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as z:
        ct = os.path.join(unpacked, "[Content_Types].xml")
        z.write(ct, "[Content_Types].xml")
        for dp, _, files in os.walk(unpacked):
            for fn in files:
                full = os.path.join(dp, fn)
                arc = os.path.relpath(full, unpacked)
                if arc != "[Content_Types].xml":
                    z.write(full, arc)


def roundtrip_check(out_docx: str) -> None:
    """Self-gate (OV.4): the built .docx MUST reopen cleanly via pandoc.

    Catches invalid OOXML (e.g. a duplicate xmlns:r, an unbalanced part) before the file
    ever reaches Word. Folds the formerly-manual OV.4 step into the builder so a broken
    deliverable can never pass silently. Raises SystemExit(2) on failure.
    """
    r = subprocess.run(["pandoc", out_docx, "-t", "plain", "-o", os.devnull],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"[OV.4] ROUND-TRIP FAILED — pandoc cannot reopen {out_docx}:\n{r.stderr}\n")
        raise SystemExit(2)
    print(f"[OV.4] round-trip OK — {out_docx} reopens cleanly")


def style_presence_check(out_docx: str) -> None:
    """Self-gate (OV.4): confirm the styling actually LANDED in the .docx.

    roundtrip_check proves the file OPENS; this proves it is STYLED. The styling is applied by
    regex-patching the OOXML pandoc emits — if a future pandoc version changes that XML shape, the
    patches silently no-op and you'd ship a valid-but-unstyled (plain-pandoc) doc that still passes
    round-trip. This asserts the key style markers are present; raises SystemExit(2) on any miss.
    """
    with zipfile.ZipFile(out_docx) as z:
        names = set(z.namelist())
        styles = z.read("word/styles.xml").decode("utf-8") if "word/styles.xml" in names else ""
    checks = {
        "Arial default font": FONT in styles,
        "heading navy palette": NAVY_TITLE in styles and BLUE_H2 in styles,
        "bordered Table style": 'w:styleId="Table"' in styles and HDR_FILL in styles,
        "per-section page breaks": "pageBreakBefore" in styles,
        "running header part": "word/header1.xml" in names,
        "page-number footer part": "word/footer1.xml" in names,
    }
    missing = [k for k, ok in checks.items() if not ok]
    if missing:
        sys.stderr.write(
            f"[OV.4] STYLE CHECK FAILED — {out_docx} opens but styling did not apply: "
            f"{', '.join(missing)}.\n  Likely a pandoc version whose OOXML shape changed so the "
            f"style patches no-op'd. Pin/verify pandoc, then rebuild.\n")
        raise SystemExit(2)
    print("[OV.4] style check OK — font/colors/table/page-breaks/header/footer all present")


def build(src_md: str, out_docx: str, header_text: str) -> None:
    tmp = tempfile.mkdtemp(prefix="ov_docx_")
    try:
        base = os.path.join(tmp, "base.docx")
        pandoc_to_docx(src_md, base)
        unpacked = os.path.join(tmp, "unpacked")
        with zipfile.ZipFile(base) as z:
            z.extractall(unpacked)
        # styles
        sp = os.path.join(unpacked, "word", "styles.xml")
        st = open(sp, encoding="utf-8").read()
        st = set_default_font(st)
        st = style_heading(st, "Title")
        st = style_heading(st, "Heading1")
        st = style_heading(st, "Heading2", page_break=True)  # each section → new page
        st = style_heading(st, "Heading3")
        st = add_table_style(st)
        open(sp, "w", encoding="utf-8").write(st)
        # document body
        dp = os.path.join(unpacked, "word", "document.xml")
        d = open(dp, encoding="utf-8").read()
        d = patch_document(d)
        open(dp, "w", encoding="utf-8").write(d)
        # header/footer
        add_header_footer(unpacked, header_text)
        repack(unpacked, out_docx)
        print(f"[OV.4] built {out_docx} ({os.path.getsize(out_docx)} bytes)")
        roundtrip_check(out_docx)          # hard gate 1: reject invalid OOXML before it reaches Word
        style_presence_check(out_docx)     # hard gate 2: reject valid-but-unstyled (pandoc drift)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Build styled System Overview .docx from Markdown")
    p.add_argument("input_md")
    p.add_argument("output_docx")
    p.add_argument("--header", default="System Overview",
                   help="right-aligned running header text (caller passes '<ProjectName> — System Overview')")
    args = p.parse_args(argv)
    if shutil.which("pandoc") is None:
        print("[ERROR] pandoc not found on PATH — install pandoc to build the .docx", file=sys.stderr)
        return 2
    if not os.path.isfile(args.input_md):
        print(f"[ERROR] input not found: {args.input_md}", file=sys.stderr)
        return 2
    build(args.input_md, args.output_docx, args.header)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
