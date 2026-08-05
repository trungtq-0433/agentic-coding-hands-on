#!/usr/bin/env python3
"""
convert.py - Convert PDF/DOCX/EPUB to Markdown chunks via Calibre HTMLZ
Combines the original steps 1-2 into a single script.
"""

import os
import sys
import subprocess
import zipfile
import shutil
import tempfile
import argparse
import bisect
import glob
import re

from manifest import create_manifest


def _calibre_env():
    """Build environment for running calibre headless (no display required).

    Injects QT_QPA_PLATFORM=offscreen so ebook-convert works on servers and
    CI environments without an X11 display.  Also adds ~/calibre-libs to
    LD_LIBRARY_PATH so isolated calibre installs can find libxcb-cursor.so.0
    if the user extracted it manually.
    """
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    home = os.path.expanduser("~")
    extra_lib = os.path.join(home, "calibre-libs", "usr", "lib", "x86_64-linux-gnu")
    if os.path.isdir(extra_lib):
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = f"{extra_lib}:{existing}" if existing else extra_lib

    return env


def find_calibre_convert():
    """Find ebook-convert command from Calibre installation.

    Returns the path string on success, or None if not found.
    Also ensures the process environment is set up for headless operation
    (QT_QPA_PLATFORM=offscreen + optional LD_LIBRARY_PATH for libxcb-cursor).
    """
    home = os.path.expanduser("~")
    possible_paths = [
        "/Applications/calibre.app/Contents/MacOS/ebook-convert",
        "/usr/bin/ebook-convert",
        "/usr/local/bin/ebook-convert",
        f"{home}/calibre-bin/calibre/ebook-convert",   # calibre isolated installer (new layout)
        f"{home}/calibre-bin/ebook-convert",           # calibre isolated installer (old layout)
        f"{home}/.local/bin/ebook-convert",
        f"{home}/bin/ebook-convert",
        "ebook-convert",                                # If in PATH
    ]

    env = _calibre_env()
    # Propagate the headless env to our own process so subprocesses inherit it
    os.environ.update({k: v for k, v in env.items() if k in ("QT_QPA_PLATFORM", "LD_LIBRARY_PATH")})

    for path in possible_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10, env=env)
            if result.returncode == 0:
                print(f"Found Calibre ebook-convert: {path}")
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def convert_pdf_to_html_pdftohtml(pdf_file, temp_dir):
    """Fallback: convert PDF to HTML using pdftohtml (poppler-utils).

    Returns (html_path, images_dir, metadata) on success, or (None, None, {}).
    """
    pdftohtml_bin = shutil.which("pdftohtml")
    if not pdftohtml_bin:
        return None, None, {}

    out_prefix = os.path.join(temp_dir, "pdftohtml_out")
    cmd = [pdftohtml_bin, "-s", "-noframes", "-enc", "UTF-8", "-q", pdf_file, out_prefix]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"pdftohtml failed: {result.stderr}")
            return None, None, {}
    except subprocess.TimeoutExpired:
        print("pdftohtml timed out")
        return None, None, {}

    html_file = out_prefix + ".html"
    if not os.path.exists(html_file):
        # pdftohtml sometimes uses just basename
        for f in os.listdir(temp_dir):
            if f.endswith(".html"):
                html_file = os.path.join(temp_dir, f)
                break
        else:
            print("pdftohtml: output HTML not found")
            return None, None, {}

    images_dir = None
    files_dir = out_prefix + "_files"
    if os.path.isdir(files_dir):
        images_dir = files_dir

    metadata = {}
    try:
        import subprocess as _sp
        info = _sp.run(["pdfinfo", pdf_file], capture_output=True, text=True, timeout=10)
        for line in info.stdout.splitlines():
            if line.startswith("Title:"):
                metadata["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("Author:"):
                metadata["creator"] = line.split(":", 1)[1].strip()
    except Exception:
        pass

    print(f"pdftohtml fallback: converted {pdf_file} → {html_file}")
    return html_file, images_dir, metadata


def convert_pdf_to_html_pymupdf(pdf_file, temp_dir):
    """Fallback: convert PDF to HTML using PyMuPDF (fitz).

    Returns (html_path, images_dir, metadata) on success, or (None, None, {}).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, None, {}

    try:
        doc = fitz.open(pdf_file)
        meta = doc.metadata or {}
        metadata = {}
        if meta.get("title"):
            metadata["title"] = meta["title"]
        if meta.get("author"):
            metadata["creator"] = meta["author"]

        html_parts = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body>"
        ]
        images_dir = os.path.join(temp_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        for page_num in range(len(doc)):
            page = doc[page_num]
            html_parts.append(page.get_text("html"))

        html_parts.append("</body></html>")
        doc.close()

        # Clean up empty images dir
        if not os.listdir(images_dir):
            shutil.rmtree(images_dir)
            images_dir = None

        html_content = "\n".join(html_parts)
        html_file = os.path.join(temp_dir, "pymupdf_out.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"PyMuPDF fallback: converted {pdf_file} → {html_file}")
        return html_file, images_dir, metadata

    except Exception as e:
        print(f"PyMuPDF fallback failed: {e}")
        return None, None, {}


def convert_to_htmlz(input_file, htmlz_file, calibre_path):
    """Convert input file to HTMLZ using Calibre"""
    try:
        print(f"Converting {input_file} to HTMLZ...")
        cmd = [calibre_path, input_file, htmlz_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            file_size = os.path.getsize(htmlz_file)
            print(f"HTMLZ conversion successful: {htmlz_file} ({file_size} bytes)")
            return True
        else:
            print(f"HTMLZ conversion failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("HTMLZ conversion timed out")
        return False
    except Exception as e:
        print(f"HTMLZ conversion error: {e}")
        return False


def extract_metadata_from_htmlz(extract_dir):
    """Extract metadata from metadata.opf file in HTMLZ"""
    try:
        import xml.etree.ElementTree as ET

        metadata_file = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() == 'metadata.opf':
                    metadata_file = os.path.join(root, file)
                    break
            if metadata_file:
                break

        if not metadata_file:
            return {}

        tree = ET.parse(metadata_file)
        root = tree.getroot()

        namespaces = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        metadata = {}

        title_elem = root.find('.//dc:title', namespaces)
        if title_elem is not None and title_elem.text:
            metadata['title'] = title_elem.text.strip()

        creator_elem = root.find('.//dc:creator', namespaces)
        if creator_elem is not None and creator_elem.text:
            metadata['creator'] = creator_elem.text.strip()

        publisher_elem = root.find('.//dc:publisher', namespaces)
        if publisher_elem is not None and publisher_elem.text:
            metadata['publisher'] = publisher_elem.text.strip()

        language_elem = root.find('.//dc:language', namespaces)
        if language_elem is not None and language_elem.text:
            metadata['language'] = language_elem.text.strip()

        return metadata

    except Exception as e:
        print(f"Warning: Error extracting metadata: {e}")
        return {}


def extract_htmlz(htmlz_file, temp_dir):
    """Extract HTMLZ file and return paths to HTML and images"""
    try:
        with zipfile.ZipFile(htmlz_file, 'r') as zip_file:
            zip_file.extractall(temp_dir)

        html_file = None
        images_dir = None

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower() in ['index.html', 'index.htm']:
                    html_file = os.path.join(root, file)
                    break
            for dir_name in dirs:
                if dir_name.lower() in ['images', 'image', 'pics', 'pictures']:
                    images_dir = os.path.join(root, dir_name)
                    break

        if not html_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.html', '.htm')):
                        html_file = os.path.join(root, file)
                        break
                if html_file:
                    break

        return html_file, images_dir

    except Exception as e:
        print(f"Error extracting HTMLZ: {e}")
        return None, None


def build_temp_dir(input_file, temp_root=None):
    """Return the working directory path for an input file.

    Default: place {book_name}_temp/ next to the input file (same directory).
    When temp_root is provided, only the parent changes; the leaf stays compatible.
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    leaf = f"{base_name}_temp"
    if temp_root is None:
        # Default to the directory containing the input file so the temp folder
        # appears next to the file (e.g. at repo root) rather than wherever the
        # Python process happens to be running from.
        temp_root = os.path.dirname(os.path.abspath(input_file))
    return os.path.join(temp_root, leaf)

def _fix_image_orientation_from_css(html_dir, images_dir, html_file):
    """Parse Calibre CSS to detect transform rotations and bake them into image files.

    Calibre sometimes stores PDF images in a flipped/rotated orientation (due to
    PDF coordinate system differences) and compensates with CSS transform rules in
    style.css. This function detects those CSS transforms and applies them physically
    to the image files so they render correctly without requiring CSS support.

    Example: `.calibre22 { transform: rotate(180deg); }` → rotates matching images 180°.
    """
    css_path = os.path.join(html_dir, "style.css")
    if not os.path.exists(css_path):
        return

    try:
        with open(css_path, 'r', encoding='utf-8', errors='ignore') as f:
            css_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read CSS for orientation fix: {e}")
        return

    # Parse CSS: find .calibreXX { ... transform: rotate(Ndeg) ... }
    class_transforms = {}
    for rule_match in re.finditer(r'\.(calibre\w+)\s*\{([^}]*)\}', css_content, re.DOTALL):
        class_name = rule_match.group(1)
        rule_body = rule_match.group(2)
        rot_match = re.search(r'(?:-webkit-)?transform\s*:\s*rotate\((-?\d+)deg\)', rule_body)
        if rot_match:
            angle = int(rot_match.group(1))
            if angle != 0:
                class_transforms[class_name] = angle

    if not class_transforms:
        return

    # Parse HTML to map image filename → CSS class → rotation angle
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read HTML for orientation fix: {e}")
        return

    img_rotations = {}
    for img_match in re.finditer(r'<img[^>]+>', html_content, re.IGNORECASE):
        tag = img_match.group(0)
        src_m = re.search(r'src=["\']([^"\']+)["\']', tag)
        cls_m = re.search(r'class=["\']([^"\']+)["\']', tag)
        if src_m and cls_m:
            img_basename = os.path.basename(src_m.group(1))
            for cls in cls_m.group(1).split():
                if cls in class_transforms:
                    img_rotations[img_basename] = class_transforms[cls]
                    break

    if not img_rotations:
        return

    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow not available, skipping CSS-based image orientation fix")
        return

    fixed_count = 0
    for img_name, angle in img_rotations.items():
        img_path = os.path.join(images_dir, img_name)
        if not os.path.exists(img_path):
            continue
        try:
            img = Image.open(img_path)
            # CSS rotate(Ndeg) is clockwise; PIL rotate() is counter-clockwise
            rotated = img.rotate(-angle, expand=True)
            # Preserve format (JPEG quality, PNG lossless)
            ext = os.path.splitext(img_path)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                rotated.save(img_path, format='JPEG', quality=92)
            else:
                rotated.save(img_path)
            fixed_count += 1
        except Exception as e:
            print(f"Warning: Could not rotate {img_name}: {e}")

    if fixed_count > 0:
        print(f"Fixed orientation for {fixed_count} image(s) based on CSS transforms")


def setup_temp_directory(input_file, html_file, images_dir, temp_root=None):
    """Setup temp directory with HTML and images"""
    try:
        temp_dir = build_temp_dir(input_file, temp_root)
        os.makedirs(temp_dir, exist_ok=True)

        input_html = os.path.join(temp_dir, "input.html")
        if os.path.exists(input_html):
            print(f"Skipping HTML copy - input.html already exists")
        else:
            shutil.copy2(html_file, input_html)
            print(f"Copied HTML to: {input_html}")

        # Copy CSS files alongside the HTML (Calibre HTML references style.css)
        html_dir = os.path.dirname(html_file)
        for css_file in glob.glob(os.path.join(html_dir, "*.css")):
            dest_css = os.path.join(temp_dir, os.path.basename(css_file))
            if not os.path.exists(dest_css):
                shutil.copy2(css_file, dest_css)
                print(f"Copied CSS to: {dest_css}")

        if images_dir and os.path.exists(images_dir):
            target_images_dir = os.path.join(temp_dir, "images")
            if os.path.exists(target_images_dir):
                print(f"Skipping images copy - images directory already exists")
            else:
                shutil.copytree(images_dir, target_images_dir)
                print(f"Copied images to: {target_images_dir}")
                # Bake CSS transform rotations into image pixels so output is
                # orientation-correct even when CSS is not applied (e.g. Calibre publishing)
                _fix_image_orientation_from_css(html_dir, target_images_dir, input_html)

        return temp_dir
    except Exception as e:
        print(f"Error setting up temp directory: {e}")
        return None


def convert_html_to_markdown(html_file, md_file, strip_page_numbers=False):
    """Convert HTML to Markdown using pandoc"""
    try:
        import pypandoc

        pypandoc.convert_file(
            html_file,
            'markdown',
            outputfile=md_file,
            extra_args=['--wrap=none']
        )

        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            content = content.replace('\ufeff', '')
            content = content.replace('\u00a0', ' ')
            content = clean_calibre_markers(content, strip_page_numbers=strip_page_numbers)

            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Markdown conversion successful: {md_file}")
            return True
        else:
            print("Markdown file was not created")
            return False
    except ImportError:
        print("pypandoc not found. Install with: pip install pypandoc")
        return False
    except Exception as e:
        print(f"HTML to Markdown conversion failed: {e}")
        return False


_PAGE_SEQUENCE_MIN_LENGTH = 4
_PAGE_SEQUENCE_MIN_RATIO = 0.5


def _detect_page_number_lines(lines):
    """Detect standalone-digit lines that form a monotonic page-number sequence.

    Returns a set of line indices that should be dropped as page numbers.

    Algorithm: collect every standalone-digit line in document order, find the
    Longest Non-Decreasing Subsequence (LNDS) of their integer values via
    bisect_right with parent-pointer reconstruction. If the LNDS is long enough
    and covers a large enough fraction of all standalone digits, treat those
    elements as page numbers. Outliers (years like 1984, chapter numbers,
    citation indices) sit off the monotonic spine and stay preserved.
    """
    digit_indices = []
    digit_values = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s.isdigit():
            digit_indices.append(i)
            digit_values.append(int(s))

    n = len(digit_values)
    if n < _PAGE_SEQUENCE_MIN_LENGTH:
        return set()

    tails = []
    tails_idx = []
    parents = [-1] * n

    for i, v in enumerate(digit_values):
        pos = bisect.bisect_right(tails, v)
        if pos > 0:
            parents[i] = tails_idx[pos - 1]
        if pos == len(tails):
            tails.append(v)
            tails_idx.append(i)
        else:
            tails[pos] = v
            tails_idx[pos] = i

    lnds = []
    cur = tails_idx[-1]
    while cur != -1:
        lnds.append(cur)
        cur = parents[cur]
    lnds.reverse()

    if len(lnds) < _PAGE_SEQUENCE_MIN_LENGTH:
        return set()
    if len(lnds) / n < _PAGE_SEQUENCE_MIN_RATIO:
        return set()

    return {digit_indices[i] for i in lnds}


def clean_calibre_markers(content, strip_page_numbers=False):
    """Clean up Calibre-specific markers from markdown content.

    Standalone digit lines are handled in two layers:
      1. If a line is adjacent to Calibre noise (::: fence, .ct}/.cn} marker),
         drop it — clearly leftover.
      2. Otherwise, run LNDS over all standalone digits to detect a monotonic
         page-number sequence and drop those. Outliers like years (1984),
         chapter numbers, and citation indices stay preserved.

    Pass strip_page_numbers=True to bypass both layers and aggressively delete
    every standalone-digit line (legacy behavior).
    """
    content = re.sub(r'\{\.calibre[^}]*\}', '', content)
    content = re.sub(r'\(#calibre_link-\d+\)', '', content)

    # Clean heading calibre attribute blocks: {#calibre_link-N .calibreN}
    content = re.sub(r'\s*\{#calibre_link-\d+[^}]*\}', '', content)

    # Clean [**text**] format to **text**
    content = re.sub(r'\[\*\*([^*]+)\*\*\]', r'**\1**', content)

    lines = content.split('\n')

    page_number_lines = set() if strip_page_numbers else _detect_page_number_lines(lines)

    def is_calibre_noise(line):
        s = line.strip()
        if not s:
            return False
        if s.startswith(':::'):
            return True
        if s.endswith('.ct}') or s.endswith('.cn}'):
            return True
        return False

    def prev_nonblank(idx):
        for j in range(idx - 1, -1, -1):
            if lines[j].strip():
                return lines[j]
        return None

    def next_nonblank(idx):
        for j in range(idx + 1, len(lines)):
            if lines[j].strip():
                return lines[j]
        return None

    cleaned_lines = []
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        if stripped_line.startswith(':::'):
            continue
        if stripped_line.endswith('.ct}') or stripped_line.endswith('.cn}'):
            continue

        if re.match(r'^\s*\d+\s*$', line):
            if strip_page_numbers:
                continue
            if i in page_number_lines:
                continue
            prev = prev_nonblank(i)
            nxt = next_nonblank(i)
            if (prev is not None and is_calibre_noise(prev)) or \
               (nxt is not None and is_calibre_noise(nxt)):
                continue
            # else: preserve as real content

        cleaned_lines.append(line)

    content = '\n'.join(cleaned_lines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content


# =============================================================================
# Structural block parsing and chunk splitting (Step 3)
# =============================================================================

def parse_structural_blocks(content):
    """Parse markdown into structural blocks that should not be split.

    Returns list of (text, block_type) tuples where block_type is one of:
    'heading', 'code_block', 'table', 'list', 'blockquote', 'image', 'paragraph'
    """
    blocks = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code block (fenced)
        if stripped.startswith('```'):
            block_lines = [line]
            i += 1
            while i < len(lines):
                block_lines.append(lines[i])
                if lines[i].strip().startswith('```') and len(block_lines) > 1:
                    i += 1
                    break
                i += 1
            blocks.append(('\n'.join(block_lines), 'code_block'))
            continue

        # Heading
        if re.match(r'^#{1,6}\s', stripped):
            blocks.append((line, 'heading'))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            block_lines = [line]
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('>') or
                                       (lines[i].strip() and not re.match(r'^#{1,6}\s', lines[i].strip())
                                        and not lines[i].strip().startswith('```')
                                        and not lines[i].strip().startswith('|')
                                        and not re.match(r'^[-*+]\s', lines[i].strip())
                                        and not re.match(r'^\d+\.\s', lines[i].strip())
                                        and block_lines[-1].strip().startswith('>'))):
                block_lines.append(lines[i])
                i += 1
            blocks.append(('\n'.join(block_lines), 'blockquote'))
            continue

        # Table (lines starting with |)
        if stripped.startswith('|'):
            block_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('|'):
                block_lines.append(lines[i])
                i += 1
            blocks.append(('\n'.join(block_lines), 'table'))
            continue

        # List (unordered or ordered)
        if re.match(r'^[-*+]\s', stripped) or re.match(r'^\d+\.\s', stripped):
            block_lines = [line]
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                # Continue list: list items, indented continuation, or blank lines within list
                if (re.match(r'^[-*+]\s', s) or re.match(r'^\d+\.\s', s) or
                        (lines[i].startswith('  ') and s) or
                        (s == '' and i + 1 < len(lines) and
                         (re.match(r'^[-*+]\s', lines[i+1].strip()) or
                          re.match(r'^\d+\.\s', lines[i+1].strip()) or
                          lines[i+1].startswith('  ')))):
                    block_lines.append(lines[i])
                    i += 1
                else:
                    break
            blocks.append(('\n'.join(block_lines), 'list'))
            continue

        # Image line (standalone or with surrounding caption)
        if re.match(r'!\[', stripped):
            blocks.append((line, 'image'))
            i += 1
            continue

        # Empty line — just a paragraph separator
        if stripped == '':
            blocks.append((line, 'paragraph'))
            i += 1
            continue

        # Regular paragraph — collect contiguous non-empty, non-special lines
        block_lines = [line]
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if (s == '' or s.startswith('```') or re.match(r'^#{1,6}\s', s) or
                    s.startswith('>') or s.startswith('|') or
                    re.match(r'^[-*+]\s', s) or re.match(r'^\d+\.\s', s) or
                    re.match(r'!\[', s)):
                break
            block_lines.append(lines[i])
            i += 1
        blocks.append(('\n'.join(block_lines), 'paragraph'))
        continue

    return blocks


def merge_blocks_to_chunks(blocks, target_size=6000):
    """Merge structural blocks into chunks respecting target_size.

    Prefers to split at heading boundaries. Never splits within a single
    structural block unless the block itself exceeds target_size * 2.
    """
    chunks = []
    current_parts = []
    current_size = 0

    def flush():
        nonlocal current_parts, current_size
        if current_parts:
            chunks.append('\n'.join(current_parts))
            current_parts = []
            current_size = 0

    for text, btype in blocks:
        block_size = len(text)

        # If a single block is oversized, handle degradation
        if block_size > target_size * 2:
            flush()
            print(f"  WARNING: Oversized {btype} block ({block_size} chars), force-splitting")
            sub_chunks = _force_split_block(text, target_size)
            chunks.extend(sub_chunks)
            continue

        # Prefer to split at heading boundaries
        if btype == 'heading' and current_size > 0:
            flush()

        # Would adding this block exceed target?
        if current_size + block_size > target_size and current_parts:
            flush()

        current_parts.append(text)
        current_size += block_size

    flush()
    return chunks


def _force_split_block(text, target_size):
    """Force-split an oversized block by paragraph (empty lines), then by lines.

    For fenced code blocks, each resulting chunk gets proper opening/closing fences
    so it remains valid Markdown.
    """
    stripped = text.strip()
    is_fenced_code = stripped.startswith('```')

    # Extract fence info for code blocks
    fence_opener = ''
    if is_fenced_code:
        first_line = stripped.split('\n', 1)[0]
        fence_opener = first_line  # e.g. "```python"

    # Try splitting by empty lines first (not applicable for code blocks — no empty lines expected)
    if not is_fenced_code:
        paragraphs = re.split(r'\n\n+', text)
        if len(paragraphs) > 1:
            chunks = []
            current = []
            current_size = 0
            for para in paragraphs:
                para_size = len(para)
                if current_size + para_size > target_size and current:
                    chunks.append('\n\n'.join(current))
                    current = [para]
                    current_size = para_size
                else:
                    current.append(para)
                    current_size += para_size
            if current:
                chunks.append('\n\n'.join(current))
            return chunks

    # Split by lines
    lines = text.split('\n')

    # For code blocks, strip the opening and closing fences before splitting content
    if is_fenced_code:
        # Remove opening fence line
        content_lines = lines[1:]
        # Remove closing fence line if present
        if content_lines and content_lines[-1].strip().startswith('```'):
            content_lines = content_lines[:-1]
        lines = content_lines

    chunks = []
    current = []
    current_size = 0
    for line in lines:
        line_size = len(line) + 1
        if current_size + line_size > target_size and current:
            chunks.append('\n'.join(current))
            current = [line]
            current_size = line_size
        else:
            current.append(line)
            current_size += line_size
    if current:
        chunks.append('\n'.join(current))

    # Re-wrap each chunk in fences for code blocks
    if is_fenced_code:
        chunks = [f"{fence_opener}\n{chunk}\n```" for chunk in chunks]

    return chunks


def split_markdown_structured(md_file, temp_dir, target_size=6000):
    """Split markdown into structural chunks.

    Returns list of chunk filenames (e.g. ['chunk0001.md', ...]).
    """
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = parse_structural_blocks(content)
        chunk_texts = merge_blocks_to_chunks(blocks, target_size)

        chunk_files = []
        for i, chunk_text in enumerate(chunk_texts, 1):
            filename = f"chunk{i:04d}.md"
            chunk_file = os.path.join(temp_dir, filename)
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            chunk_files.append(filename)

        print(f"Split into {len(chunk_files)} chunks")
        for filename in chunk_files:
            filepath = os.path.join(temp_dir, filename)
            size = os.path.getsize(filepath)
            print(f"  {filename}: {size} characters")

        return chunk_files
    except Exception as e:
        print(f"Error splitting markdown: {e}")
        return []


def _find_existing_chunk_files(temp_dir):
    """Find existing chunk source files (excluding output_ prefixed).

    Returns (filenames_list, is_legacy=False).
    """
    chunk_files = glob.glob(os.path.join(temp_dir, 'chunk*.md'))
    chunk_files = [os.path.basename(f) for f in chunk_files if not os.path.basename(f).startswith('output_')]

    if chunk_files:
        return sorted(chunk_files), False
    return [], False


def create_config_file(temp_dir, input_file, input_lang, output_lang, metadata=None, conversion_method=None):
    """Create config.txt file for the pipeline"""
    try:
        config_file = os.path.join(temp_dir, "config.txt")

        method = conversion_method or "calibre_htmlz"
        config_content = f"""# Translation Configuration
input_file={input_file}
input_lang={input_lang}
output_lang={output_lang}
conversion_method={method}
"""
        if metadata:
            config_content += f"\n# Book Metadata\n"
            if 'title' in metadata:
                config_content += f"original_title={metadata['title']}\n"
            if 'creator' in metadata:
                config_content += f"creator={metadata['creator']}\n"
            if 'publisher' in metadata:
                config_content += f"publisher={metadata['publisher']}\n"
            if 'language' in metadata:
                config_content += f"source_language={metadata['language']}\n"

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)

        print(f"Created config file: {config_file}")
        return True
    except Exception as e:
        print(f"Error creating config file: {e}")
        return False


def _do_split_and_manifest(temp_dir, input_md, chunk_size):
    """Split markdown and create manifest. Returns chunk count or 0 on failure."""
    existing, is_legacy = _find_existing_chunk_files(temp_dir)
    if existing:
        print(f"Skipping markdown splitting - found {len(existing)} existing {'page' if is_legacy else 'chunk'} files")
        # Create/update manifest for existing files
        create_manifest(temp_dir, existing, input_md)
        return len(existing)

    chunk_files = split_markdown_structured(input_md, temp_dir, chunk_size)
    if not chunk_files:
        return 0
    create_manifest(temp_dir, chunk_files, input_md)
    return len(chunk_files)


def _check_strip_page_numbers_cache_conflict(strip_flag, temp_dir, input_md):
    """Return list of cached files that would silently neutralize --strip-page-numbers.

    The flag only takes effect inside clean_calibre_markers, which runs during
    HTML→Markdown conversion. If input.md or chunk*.md already exist from a
    prior run, both are reused as-is and the flag becomes a no-op. Surface
    that conflict so the user knows to clean up.
    """
    if not strip_flag:
        return []
    if not os.path.isdir(temp_dir):
        return []

    blockers = []
    if os.path.exists(input_md):
        blockers.append(input_md)

    existing_chunks = [
        f for f in glob.glob(os.path.join(temp_dir, 'chunk*.md'))
        if not os.path.basename(f).startswith('output_')
    ]
    if existing_chunks:
        blockers.append(f"{len(existing_chunks)} chunk file(s) under {temp_dir}/")

    return blockers


def _abort_on_strip_cache_conflict(blockers, temp_dir):
    if not blockers:
        return
    print("Error: --strip-page-numbers cannot take effect because cached files exist:")
    for b in blockers:
        print(f"  - {b}")
    print(f"Delete the cached files (or remove the entire {temp_dir}/ directory) and re-run.")
    sys.exit(1)


# =============================================================================
# Native DOCX / PDF pipelines (Idea A + B)
# =============================================================================

def _convert_docx_native(input_file, temp_dir, chunk_size, ilang, olang):
    """Extract DOCX natively via raw-XML engine (Idea A). Returns True on success."""
    try:
        import sys as _sys
        _docx_dir = os.path.join(os.path.dirname(__file__), "docx")
        if _docx_dir not in _sys.path:
            _sys.path.insert(0, _docx_dir)
        from extract_docx import extract_docx_to_chunks
    except ImportError as e:
        print(f"extract_docx not available: {e}")
        return False
    try:
        os.makedirs(temp_dir, exist_ok=True)
        count = extract_docx_to_chunks(input_file, temp_dir, chunk_size)
        if count == 0:
            return False
        create_config_file(temp_dir, input_file, ilang, olang, {}, "docx_native")
        return True
    except Exception as e:
        print(f"DOCX native extraction failed: {e}")
        return False


def _convert_pptx_native(input_file, temp_dir, chunk_size, ilang, olang):
    """Extract PPTX natively via python-pptx (per-run components). Returns True on success."""
    try:
        import sys as _sys
        _pptx_dir = os.path.join(os.path.dirname(__file__), "pptx")
        if _pptx_dir not in _sys.path:
            _sys.path.insert(0, _pptx_dir)
        from extract_pptx import extract_pptx_to_chunks
    except ImportError as e:
        print(f"extract_pptx not available: {e}")
        return False
    try:
        os.makedirs(temp_dir, exist_ok=True)
        count = extract_pptx_to_chunks(input_file, temp_dir, chunk_size)
        if count == 0:
            return False
        create_config_file(temp_dir, input_file, ilang, olang, {}, "pptx_native")
        return True
    except Exception as e:
        print(f"PPTX native extraction failed: {e}")
        return False


def _convert_xlsx_native(input_file, temp_dir, chunk_size, ilang, olang):
    """Extract XLSX natively with openpyxl. Returns True on success."""
    try:
        import sys as _sys
        _xlsx_dir = os.path.join(os.path.dirname(__file__), "xlsx")
        if _xlsx_dir not in _sys.path:
            _sys.path.insert(0, _xlsx_dir)
        from extract_xlsx import extract_xlsx_to_chunks
    except ImportError as e:
        print(f"extract_xlsx not available: {e}")
        return False
    try:
        os.makedirs(temp_dir, exist_ok=True)
        count = extract_xlsx_to_chunks(input_file, temp_dir, chunk_size)
        if count == 0:
            return False
        create_config_file(temp_dir, input_file, ilang, olang, {}, "xlsx_native")
        return True
    except Exception as e:
        print(f"XLSX extraction failed: {e}")
        return False


def _convert_pdf_native(input_file, temp_dir, chunk_size, ilang, olang):
    """Convert PDF→DOCX (pdf2docx) then extract natively (Idea B). Returns True on success."""
    try:
        import sys as _sys
        _pdf_dir = os.path.join(os.path.dirname(__file__), "pdf")
        _docx_dir = os.path.join(os.path.dirname(__file__), "docx")
        if _pdf_dir not in _sys.path:
            _sys.path.insert(0, _pdf_dir)
        if _docx_dir not in _sys.path:
            _sys.path.insert(0, _docx_dir)
        from pdf_bridge import convert_pdf_to_docx
        from extract_docx import extract_docx_to_chunks
    except ImportError as e:
        print(f"PDF native pipeline not available: {e}")
        return False
    try:
        os.makedirs(temp_dir, exist_ok=True)
        bridge_docx = os.path.join(temp_dir, "_bridge.docx")
        if not convert_pdf_to_docx(input_file, bridge_docx):
            return False
        count = extract_docx_to_chunks(bridge_docx, temp_dir, chunk_size)
        if count == 0:
            return False
        create_config_file(temp_dir, input_file, ilang, olang, {}, "pdf_docx_bridge")
        return True
    except Exception as e:
        print(f"PDF native pipeline failed: {e}")
        return False


def _convert_pdf_inplace(input_file, temp_dir, chunk_size, ilang, olang, profile=None, user_overrides=None):
    """PDF in-place engine: extract text elements, write element-based chunks.

    Produces chunk*.md with [E:page_line] markers, pdf_structure.json,
    pdf_profile.json (if profile provided), and config.txt.
    Returns True on success; False if extraction yields zero elements (fall through).
    """
    try:
        import sys as _sys
        import json as _json
        _pdf_dir = os.path.join(os.path.dirname(__file__), "pdf")
        if _pdf_dir not in _sys.path:
            _sys.path.insert(0, _pdf_dir)
        from pdf_inplace_extract import extract_elements
        from pdf_chunk_io import write_chunks
        from pdf_profile import profile as _profile_fn
    except ImportError as e:
        print(f"PDF in-place engine not available: {e}")
        return False

    try:
        os.makedirs(temp_dir, exist_ok=True)

        # Run profiler to get column layout, scanned pages, etc.
        if profile is None:
            try:
                print("PDF in-place: profiling...")
                profile = _profile_fn(input_file, user_overrides=user_overrides or {})
                print(
                    f"  columns: {set(profile['columns_per_page'].values())}, "
                    f"scanned: {profile['scanned_pages']}, "
                    f"script: {profile['dominant_script']}"
                )
            except Exception as e:
                print(f"  profiling failed ({e}), continuing without profile")
                profile = None

        print("PDF in-place: extracting elements...")
        elements, structure = extract_elements(input_file, profile=profile)

        # OCR scanned pages if any exist and translate_img is enabled
        scanned_pages = []
        if profile:
            scanned_pages = profile.get("scanned_pages", [])
            translate_img = profile.get("translate_img", False)
        else:
            translate_img = False

        if scanned_pages and translate_img:
            try:
                from pdf_ocr import extract_ocr_elements
                print(f"PDF in-place: OCR-ing {len(scanned_pages)} scanned page(s)...")
                ocr_elems, ocr_struct = extract_ocr_elements(input_file, scanned_pages, ilang)
                elements.extend(ocr_elems)
                structure.update(ocr_struct)
                print(f"  OCR added {len(ocr_elems)} elements")
            except Exception as e:
                print(f"  OCR failed ({e}), continuing without scanned pages")

        if not elements:
            print("PDF in-place: zero text elements extracted (scanned/image-only PDF?)")
            return False

        glyphless = structure.get("glyphless_pages", [])
        print(f"PDF in-place: {len(elements)} elements, glyphless pages: {glyphless}")

        # Write pdf_structure.json
        struct_path = os.path.join(temp_dir, "pdf_structure.json")
        with open(struct_path, "w", encoding="utf-8") as f:
            _json.dump(structure, f, ensure_ascii=False)

        # Write pdf_profile.json if profile was computed
        if profile:
            prof_path = os.path.join(temp_dir, "pdf_profile.json")
            with open(prof_path, "w", encoding="utf-8") as f:
                _json.dump(profile, f, ensure_ascii=False, indent=2)

        # Write chunk*.md with [E:id] markers
        chunk_files = write_chunks(elements, temp_dir, max_chars=chunk_size)
        if not chunk_files:
            return False
        print(f"PDF in-place: wrote {len(chunk_files)} chunk(s)")

        create_manifest(temp_dir, chunk_files, input_file)
        meta = {}
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(input_file)
            m = doc.metadata or {}
            if m.get("title"):
                meta["title"] = m["title"]
            if m.get("author"):
                meta["creator"] = m["author"]
            doc.close()
        except Exception:
            pass
        create_config_file(temp_dir, input_file, ilang, olang, meta, "pdf_inplace")
        return True
    except Exception as e:
        print(f"PDF in-place extraction failed: {e}")
        return False


def main():
    """Main conversion function"""
    parser = argparse.ArgumentParser(description="Convert PDF/DOCX/EPUB to markdown chunks via HTMLZ")
    parser.add_argument("input_file", help="Input file (PDF, DOCX, or EPUB)")
    parser.add_argument("-l", "--ilang", default="auto", help="Input language (default: auto)")
    parser.add_argument("--olang", default="zh", help="Output language (default: zh)")
    parser.add_argument("--chunk-size", type=int, default=6000, help="Target chunk size in characters (default: 6000)")
    parser.add_argument(
        "--temp-root",
        default=None,
        help="Directory under which {book_name}_temp/ will be created (default: current working directory)",
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "native", "markdown"],
        help="Conversion mode: auto (default) tries native first then Calibre/Markdown; "
             "native forces native pipeline (error if unsupported); "
             "markdown forces legacy Calibre→Markdown pipeline.",
    )
    parser.add_argument(
        "--strip-page-numbers",
        action="store_true",
        help="Aggressively delete every standalone-digit line (legacy behavior). "
             "Default is off: standalone digits are preserved unless adjacent to Calibre noise.",
    )
    parser.add_argument(
        "--translate-img",
        action="store_true",
        help="Run vision-OCR on image-only/scanned pages in PDF (requires pdf_ocr support).",
    )
    parser.add_argument(
        "--page-range",
        default=None,
        metavar="N-M",
        help="Translate only pages N through M (1-based, e.g. '1-10'). PDF in-place pipeline only.",
    )

    args = parser.parse_args()
    input_file = args.input_file

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    file_ext = os.path.splitext(input_file)[1].lower()
    if file_ext not in ['.pdf', '.docx', '.epub', '.xlsx', '.pptx']:
        print(f"Error: Unsupported file type: {file_ext}")
        sys.exit(1)

    print("=== File Conversion ===")
    print(f"Input file: {input_file}")
    print(f"Target chunk size: {args.chunk_size} characters")
    if args.temp_root:
        print(f"Temp root: {args.temp_root}")

    # --- Native pipeline routing ---
    if args.mode != 'markdown':
        temp_dir = build_temp_dir(input_file, args.temp_root)
        if file_ext == '.pptx':
            print("Trying PPTX native pipeline (python-pptx)...")
            if _convert_pptx_native(input_file, temp_dir, args.chunk_size, args.ilang, args.olang):
                print("Conversion completed successfully!")
                print(f"Temp directory: {temp_dir}")
                return
            print("Error: PPTX extraction failed")
            sys.exit(1)
        elif file_ext == '.xlsx':
            print("Trying XLSX native pipeline (openpyxl)...")
            if _convert_xlsx_native(input_file, temp_dir, args.chunk_size, args.ilang, args.olang):
                print("Conversion completed successfully!")
                print(f"Temp directory: {temp_dir}")
                return
            print("Error: XLSX extraction failed")
            sys.exit(1)
        elif file_ext == '.docx':
            print("Trying DOCX native pipeline (python-docx)...")
            if _convert_docx_native(input_file, temp_dir, args.chunk_size, args.ilang, args.olang):
                print("Conversion completed successfully!")
                print(f"Temp directory: {temp_dir}")
                return
            if args.mode == 'native':
                print("Error: DOCX native mode failed and --mode=native was set")
                sys.exit(1)
            print("DOCX native extraction failed — falling back to Calibre/Markdown pipeline")
        elif file_ext == '.pdf':
            # Try pdf_inplace engine first (preserves images/layout without rebuilding)
            print("Trying PDF in-place engine (PyMuPDF text-swap)...")
            _pdf_overrides = {}
            if args.translate_img:
                _pdf_overrides["translate_img"] = True
            if args.page_range:
                _pdf_overrides["page_range"] = args.page_range
            if _convert_pdf_inplace(
                input_file, temp_dir, args.chunk_size, args.ilang, args.olang,
                user_overrides=_pdf_overrides,
            ):
                print("Conversion completed successfully!")
                print(f"Temp directory: {temp_dir}")
                return
            print("PDF in-place engine failed — trying pdf2docx bridge...")
            if _convert_pdf_native(input_file, temp_dir, args.chunk_size, args.ilang, args.olang):
                print("Conversion completed successfully!")
                print(f"Temp directory: {temp_dir}")
                return
            if args.mode == 'native':
                print("Error: PDF native mode failed and --mode=native was set")
                sys.exit(1)
            print("PDF native pipeline failed — falling back to Calibre/Markdown pipeline")

    calibre_path = find_calibre_convert()
    if calibre_path:
        print(f"Converter: Calibre ({calibre_path})")
    else:
        print("Calibre not found — will try pdftohtml / PyMuPDF fallback (PDF only)")

    htmlz_file = f"{os.path.splitext(input_file)[0]}.htmlz"

    try:
        temp_dir = build_temp_dir(input_file, args.temp_root)
        input_html_path = os.path.join(temp_dir, "input.html")

        if os.path.exists(input_html_path):
            print(f"Skipping HTMLZ conversion - input.html already exists")

            metadata = {}
            config_file = os.path.join(temp_dir, "config.txt")
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                if key == 'original_title':
                                    metadata['title'] = value
                                elif key == 'creator':
                                    metadata['creator'] = value
                                elif key == 'publisher':
                                    metadata['publisher'] = value
                                elif key == 'source_language':
                                    metadata['language'] = value
                except Exception as e:
                    print(f"Warning: Could not read metadata from config: {e}")

            input_md = os.path.join(temp_dir, "input.md")
            _abort_on_strip_cache_conflict(
                _check_strip_page_numbers_cache_conflict(args.strip_page_numbers, temp_dir, input_md),
                temp_dir,
            )
            if os.path.exists(input_md):
                print(f"Skipping HTML to Markdown conversion - input.md already exists")
            else:
                if not convert_html_to_markdown(input_html_path, input_md, strip_page_numbers=args.strip_page_numbers):
                    sys.exit(1)

            chunk_count = _do_split_and_manifest(temp_dir, input_md, args.chunk_size)
            if chunk_count == 0:
                sys.exit(1)

            create_config_file(temp_dir, input_file, args.ilang, args.olang, metadata)
            print("Conversion completed successfully!")
            print(f"Temp directory: {temp_dir}")
            return

        # --- Try calibre first, then fallbacks for PDF ---
        html_file = None
        images_dir = None
        metadata = {}

        if calibre_path:
            conversion_method = "calibre_htmlz"
            if not convert_to_htmlz(input_file, htmlz_file, calibre_path):
                sys.exit(1)

            with tempfile.TemporaryDirectory() as extract_dir:
                html_file, images_dir = extract_htmlz(htmlz_file, extract_dir)
                if not html_file:
                    sys.exit(1)

                metadata = extract_metadata_from_htmlz(extract_dir)

                temp_dir = setup_temp_directory(input_file, html_file, images_dir, temp_root=args.temp_root)
                if not temp_dir:
                    sys.exit(1)

                if os.path.exists(htmlz_file):
                    os.remove(htmlz_file)

                html_file = None  # already copied into temp_dir by setup_temp_directory

        else:
            print(f"Error: Calibre ebook-convert is required for {file_ext} files.")
            print("Install Calibre: https://calibre-ebook.com/")
            sys.exit(1)

        input_html = os.path.join(temp_dir, "input.html")
        input_md = os.path.join(temp_dir, "input.md")

        _abort_on_strip_cache_conflict(
            _check_strip_page_numbers_cache_conflict(args.strip_page_numbers, temp_dir, input_md),
            temp_dir,
        )
        if os.path.exists(input_md):
            print(f"Skipping HTML to Markdown conversion - input.md already exists")
        else:
            if not convert_html_to_markdown(input_html, input_md, strip_page_numbers=args.strip_page_numbers):
                sys.exit(1)

        chunk_count = _do_split_and_manifest(temp_dir, input_md, args.chunk_size)
        if chunk_count == 0:
            sys.exit(1)

        create_config_file(temp_dir, input_file, args.ilang, args.olang, metadata, conversion_method)

        print("Conversion completed successfully!")
        print(f"Temp directory: {temp_dir}")
        print(f"Markdown chunks: {chunk_count} files")

    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
