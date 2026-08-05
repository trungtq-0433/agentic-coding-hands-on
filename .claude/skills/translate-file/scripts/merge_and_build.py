#!/usr/bin/env python3
"""
merge_and_build.py - Merge translated pages and build final outputs
Combines original steps 4-7: merge -> HTML -> TOC -> DOCX/EPUB/PDF

Usage: merge_and_build.py --temp-dir <path> [--title <title>] [--author <author>] [--lang <lang>]
"""

import os
import sys
import re
import glob
import shutil
import subprocess
import argparse
import html as _html_lib
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from manifest import validate_for_merge


# =============================================================================
# Image structure validation helpers
# =============================================================================

# Markdown image: `![alt](url)` or `![alt](url "title")`.
# - Negative lookbehind on `\` skips escaped `\![...]` (renders as literal text).
# - Closing `)` is required — a missing `)` means the image won't render, so
#   such a fragment must NOT count as a preserved image reference.
_MD_IMG_RE = re.compile(r'(?<!\\)!\[[^\]]*\]\(\s*([^)\s]+)[^)]*\)')
_VALID_ATTR_NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_:.\-]*$')


class _ImgTagCollector(HTMLParser):
    """Collects every <img> tag found in fed text. Uses stdlib HTMLParser, which
    correctly handles `>` inside quoted attribute values — unlike a plain
    `<img\\b[^>]*>` regex, which would truncate at the first `>`."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.records = []  # list of (raw_tag_text, attrs_list)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.records.append((self.get_starttag_text(), list(attrs)))

    handle_startendtag = handle_starttag


def _scan_img_tags(text):
    """Return (Counter of <img> srcs, list of (raw_tag, bad_attr_name) tuples).

    Feeds the entire text to HTMLParser rather than pre-extracting tags via regex,
    so quoted attribute values containing `>` are handled correctly."""
    src_counts = Counter()
    bad_attrs = []
    parser = _ImgTagCollector()
    try:
        parser.feed(text)
        parser.close()
    except Exception as e:
        bad_attrs.append(('<unparseable input>', f'<parser error: {e}>'))
        return src_counts, bad_attrs
    for raw_tag, attrs in parser.records:
        for name, _ in attrs:
            if not _VALID_ATTR_NAME_RE.match(name):
                bad_attrs.append((raw_tag, name))
        for name, val in attrs:
            if name == 'src' and val:
                src_counts[val] += 1
    return src_counts, bad_attrs


def _scan_image_refs(text):
    """Return (Counter html_srcs, Counter md_srcs, list bad_attrs)."""
    html_srcs, bad_attrs = _scan_img_tags(text)
    md_srcs = Counter(_MD_IMG_RE.findall(text))
    return html_srcs, md_srcs, bad_attrs


def _validate_chunk_images(temp_dir):
    """Verify each output_chunk*.md preserves the image structure of its chunk*.md.

    Bad-attribute detection uses a per-chunk DELTA: a malformed <img> attribute
    is flagged only if it appears in the output chunk but not in the source
    chunk. This avoids false positives on code blocks that legitimately contain
    deliberately-broken <img> examples — both chunks carry the same example, so
    the delta is empty.

    Returns False on any divergence; collects all errors and prints them
    together so an agent can fix many chunks in one pass.
    """
    temp_path = Path(temp_dir)
    errors = []
    for src_chunk in sorted(temp_path.glob('chunk*.md')):
        if src_chunk.name.startswith('output_'):
            continue
        out_chunk = temp_path / f'output_{src_chunk.name}'
        if not out_chunk.exists():
            continue  # missing-output is the manifest validator's job
        src_html, src_md, src_bad = _scan_image_refs(src_chunk.read_text(encoding='utf-8'))
        out_html, out_md, out_bad = _scan_image_refs(out_chunk.read_text(encoding='utf-8'))

        src_bad_counts = Counter(name for _, name in src_bad)
        out_bad_counts = Counter(name for _, name in out_bad)
        new_bad_counts = out_bad_counts - src_bad_counts
        if new_bad_counts:
            new_bad_examples = [
                (raw_tag, attr_name)
                for raw_tag, attr_name in out_bad
                if new_bad_counts.get(attr_name, 0) > 0
            ]
            for raw_tag, attr_name in new_bad_examples:
                errors.append(
                    f"ERROR: {out_chunk.name} introduced malformed <img> tag (not present in source)\n"
                    f"  tag: {raw_tag}\n"
                    f"  problem: attribute name '{attr_name}' is not a valid HTML identifier\n"
                    f"  likely cause: an unescaped quote inside alt=\"...\" or title=\"...\" closed the attribute early\n"
                    f"  fix: in {out_chunk.name}, replace the inner quote with a curly quote in the target language or with &quot; / &#39;\n"
                    f"  source chunk for reference: {src_chunk.name}"
                )

        if src_html != out_html or src_md != out_md:
            errors.append(
                f"ERROR: {out_chunk.name} image references diverge from {src_chunk.name}\n"
                f"  missing <img src> (count): {sorted((src_html - out_html).items()) or 'none'}\n"
                f"  extra   <img src> (count): {sorted((out_html - src_html).items()) or 'none'}\n"
                f"  missing ![](path) (count): {sorted((src_md - out_md).items()) or 'none'}\n"
                f"  extra   ![](path) (count): {sorted((out_md - src_md).items()) or 'none'}\n"
                f"  fix: restore the missing image refs in {out_chunk.name} from {src_chunk.name}"
            )

    if errors:
        print("\n=== Image validation failed ===")
        for e in errors:
            print(e)
            print()
        return False
    return True


def _check_generated_html_sanity(html_path):
    """Sanity-check generated HTML for malformed <img> tags. Returns False on problems.

    Note: we deliberately do NOT flag `&lt;img` in the rendered HTML — books that
    discuss HTML in prose or code blocks legitimately render escaped `<img>` text,
    and that's not a corruption signal. Real corruption produces a malformed
    actual `<img>` tag, which the attribute-name check catches."""
    try:
        text = Path(html_path).read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: cannot read {html_path}: {e}")
        return False

    _, bad_attrs = _scan_img_tags(text)
    if not bad_attrs:
        return True

    print(f"ERROR: image sanity check failed on {Path(html_path).name}")
    for raw_tag, attr_name in bad_attrs:
        print(f"  - malformed <img>: {raw_tag}")
        print(f"    bad attribute name: '{attr_name}'")
    print(
        "  fix: inspect output.md and the corresponding output_chunk*.md;\n"
        "       if alt text contains literal quotes, replace with curly quotes or HTML entity"
    )
    return False

# Try to import BeautifulSoup for TOC generation
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Try to import markdown
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# Language configuration — single source of truth for lang-dependent values
# =============================================================================

LANG_CONFIG = {
    'zh': {
        'lang_attr': 'zh-CN',
        'font_family': "'FangSong', '仿宋', 'STFangSong', '华文仿宋', serif",
        'font_family_ebook': '"FangSong", "FangSong_GB2312", "仿宋", "仿宋_GB2312", "STFangSong", "SimSun", serif',
        'toc_label': '目录',
        'pdf_font': 'FangSong',
    },
    'en': {
        'lang_attr': 'en',
        'font_family': "Georgia, 'Times New Roman', Times, serif",
        'font_family_ebook': 'Georgia, "Times New Roman", Times, serif',
        'toc_label': 'Contents',
        'pdf_font': 'Georgia',
    },
    'ja': {
        'lang_attr': 'ja',
        'font_family': "'Hiragino Mincho ProN', 'Yu Mincho', 'MS Mincho', serif",
        'font_family_ebook': '"Hiragino Mincho ProN", "Yu Mincho", "MS Mincho", serif',
        'toc_label': '目次',
        'pdf_font': 'Hiragino Mincho ProN',
    },
    'ko': {
        'lang_attr': 'ko',
        'font_family': "'Nanum Myeongjo', 'Batang', serif",
        'font_family_ebook': '"Nanum Myeongjo", "Batang", serif',
        'toc_label': '목차',
        'pdf_font': 'Nanum Myeongjo',
    },
    'fr': {
        'lang_attr': 'fr',
        'font_family': "Georgia, 'Times New Roman', Times, serif",
        'font_family_ebook': 'Georgia, "Times New Roman", Times, serif',
        'toc_label': 'Table des matières',
        'pdf_font': 'Georgia',
    },
    'de': {
        'lang_attr': 'de',
        'font_family': "Georgia, 'Times New Roman', Times, serif",
        'font_family_ebook': 'Georgia, "Times New Roman", Times, serif',
        'toc_label': 'Inhaltsverzeichnis',
        'pdf_font': 'Georgia',
    },
    'es': {
        'lang_attr': 'es',
        'font_family': "Georgia, 'Times New Roman', Times, serif",
        'font_family_ebook': 'Georgia, "Times New Roman", Times, serif',
        'toc_label': 'Índice',
        'pdf_font': 'Georgia',
    },
}

# Default fallback for unknown languages
_DEFAULT_LANG_CONFIG = {
    'lang_attr': 'en',
    'font_family': "Georgia, 'Times New Roman', Times, serif",
    'font_family_ebook': 'Georgia, "Times New Roman", Times, serif',
    'toc_label': 'Contents',
    'pdf_font': 'Georgia',
}


def get_lang_config(lang_code):
    """Get language config, falling back to defaults for unknown languages."""
    return LANG_CONFIG.get(lang_code, _DEFAULT_LANG_CONFIG)


def load_config(temp_dir):
    """Load configuration from config.txt"""
    config_file = os.path.join(temp_dir, 'config.txt')
    if not os.path.exists(config_file):
        print("Error: config.txt not found in temp directory.")
        sys.exit(1)

    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config


def natural_sort_key(text):
    """Natural sorting key for filenames with numbers"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', text)]


# =============================================================================
# Step 4: Merge translated markdown files
# =============================================================================

def merge_markdown_files(temp_dir):
    """Merge all translated output files into output.md"""
    print("=== Merging translated markdown files ===")

    output_md = os.path.join(temp_dir, 'output.md')

    # Always validate manifest, even if output.md exists (catch stale/corrupt outputs)
    ok, ordered_files, warnings = validate_for_merge(temp_dir)

    # Image structure validation runs unconditionally — bad chunks invalidate any cached output.md
    if not _validate_chunk_images(temp_dir):
        if os.path.exists(output_md):
            print("Removing stale output.md (built from chunks that failed image validation)")
            os.remove(output_md)
        return False

    if os.path.exists(output_md):
        if not ok:
            output_size = os.path.getsize(output_md)
            if output_size > 0:
                # Source chunks may have been cleaned up after a successful merge.
                # If output.md is non-empty, trust it — deleting it would lose the translation.
                print(f"WARNING: manifest validation failed but output.md is non-empty ({output_size:,} bytes) — using existing output.md (source chunks may have been cleaned up)")
                return True
            print(f"WARNING: output.md exists but is empty and manifest validation failed — deleting stale output.md")
            os.remove(output_md)
        else:
            # Check if any output_chunk is newer than output.md (re-translated chunks)
            output_md_mtime = os.path.getmtime(output_md)
            newer_chunks = []
            if ordered_files:
                newer_chunks = [
                    os.path.basename(f) for f in ordered_files
                    if os.path.getmtime(f) > output_md_mtime
                ]
            if newer_chunks:
                print(f"Re-merging — {len(newer_chunks)} chunk(s) newer than output.md: {', '.join(newer_chunks[:5])}{'...' if len(newer_chunks) > 5 else ''}")
                os.remove(output_md)
            else:
                print(f"Skipping merge - output.md already exists and is up to date")
                return True

    if not ok:
        print("ERROR: Merge validation failed. Fix the issues above before merging.")
        return False

    if ordered_files is not None:
        # Manifest-based merge
        print(f"Merging {len(ordered_files)} translated files (manifest-ordered)")
        merged_content = ""
        for file_path in ordered_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    merged_content += content + "\n\n"
            except Exception as e:
                print(f"Error reading {os.path.basename(file_path)}: {e}")
    else:
        # Legacy fallback: glob-based merge (no manifest)
        print("WARNING: No manifest.json found — using legacy glob-based merge.")
        print("  For hash validation, re-run convert.py to generate manifest.json")

        # Match chunk output files
        output_files = glob.glob(os.path.join(temp_dir, 'output_chunk*.md'))

        # Count original source files
        original_files = glob.glob(os.path.join(temp_dir, 'chunk*.md'))
        original_files = [f for f in original_files if not os.path.basename(f).startswith('output_')]

        if not output_files:
            print("Error: No translated markdown files found.")
            return False

        # Build expected output filename for each source file and verify 1:1 match
        source_basenames = sorted(
            [os.path.basename(f) for f in original_files],
            key=natural_sort_key
        )
        expected_outputs = set(f"output_{name}" for name in source_basenames)
        actual_outputs = set(os.path.basename(f) for f in output_files)

        missing = expected_outputs - actual_outputs
        orphaned = actual_outputs - expected_outputs

        if missing or orphaned:
            if missing:
                print(f"ERROR: Missing translations for: {', '.join(sorted(missing, key=natural_sort_key))}")
            if orphaned:
                print(f"ERROR: Orphaned outputs (no matching source): {', '.join(sorted(orphaned, key=natural_sort_key))}")
            return False

        # Verify no empty output files
        for fp in output_files:
            if os.path.getsize(fp) == 0:
                print(f"ERROR: Empty output file: {os.path.basename(fp)}")
                return False

        # Use source order to determine merge order (via expected output names)
        output_files = [
            os.path.join(temp_dir, f"output_{name}")
            for name in source_basenames
        ]
        print(f"Merging {len(output_files)} translated files (legacy glob)")

        merged_content = ""
        for file_path in output_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    merged_content += content + "\n\n"
            except Exception as e:
                print(f"Error reading {os.path.basename(file_path)}: {e}")

    try:
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        file_size = os.path.getsize(output_md)
        print(f"Merged into output.md ({file_size:,} bytes)")
        return True
    except Exception as e:
        print(f"Error saving merged file: {e}")
        return False


# =============================================================================
# Step 5: Convert markdown to HTML
# =============================================================================

def check_pandoc_available():
    """Check if pandoc is available"""
    try:
        subprocess.run(['pandoc', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_with_pandoc(md_file, html_file, title, lang_attr):
    """Convert markdown to HTML using pandoc"""
    cmd = [
        'pandoc', md_file, '-o', html_file,
        '--standalone',
        '--metadata', f'title={title}',
        '--metadata', f'lang={lang_attr}',
        '--from', 'markdown+smart+east_asian_line_breaks',
        '--to', 'html5'
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Converted with pandoc")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Pandoc conversion failed: {e.stderr}")
        return False


def convert_with_python_markdown(md_file, html_file, title):
    """Convert markdown to HTML using python-markdown (fallback 1)"""
    if not MARKDOWN_AVAILABLE:
        return False

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        extensions = ['toc', 'tables', 'fenced_code', 'codehilite', 'nl2br']
        md = markdown.Markdown(extensions=extensions)
        html_content = md.convert(md_content)

        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body>
{html_content}
</body>
</html>"""

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)

        print("Converted with python-markdown (fallback)")
        return True
    except Exception as e:
        print(f"python-markdown conversion failed: {e}")
        return False


def convert_with_basic_regex(md_file, html_file, title):
    """Convert markdown to HTML using basic regex (fallback 2)"""
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = md_content

        # Headers
        html_content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)

        # Bold and italic
        html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
        html_content = re.sub(r'_(.*?)_', r'<em>\1</em>', html_content)

        # Images — escape alt and src so quotes in alt text don't break the tag
        def _md_img_to_html(m):
            alt = _html_lib.escape(m.group(1), quote=True)
            src = _html_lib.escape(m.group(2), quote=True)
            return f'<img src="{src}" alt="{alt}">'
        html_content = re.sub(r'!\[([^\]]*)\]\(([^)]*)\)', _md_img_to_html, html_content)

        # Links
        html_content = re.sub(r'\[([^\]]*)\]\(([^)]*)\)', r'<a href="\2">\1</a>', html_content)

        # Lists and paragraphs
        lines = html_content.split('\n')
        result_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = 'ul'
                item = stripped[2:]
                result_lines.append(f'<li>{item}</li>')
            elif re.match(r'^\d+\. ', stripped):
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = 'ol'
                item = re.sub(r'^\d+\. ', '', stripped)
                result_lines.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result_lines.append(f'</{in_list}>')
                    in_list = False
                if stripped and not stripped.startswith('<'):
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append(line)

        if in_list:
            result_lines.append(f'</{in_list}>')

        html_content = '\n'.join(result_lines)

        # Page separators
        html_content = re.sub(r'<p>---</p>', '<div class="page-separator"></div>', html_content)

        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body>
{html_content}
</body>
</html>"""

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)

        print("Converted with basic regex (fallback 2)")
        return True
    except Exception as e:
        print(f"Basic regex conversion failed: {e}")
        return False


def apply_template_to_html(html_content, template_file, output_file, title, lang_cfg, author=None, style_hints=None):
    """Apply a template to HTML content with language-aware substitutions"""
    if not template_file or not os.path.exists(template_file):
        print(f"Warning: Template {template_file} not found")
        return False

    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        if '$body$' in template_content:
            full_html = template_content.replace('$body$', html_content)
        elif '{{content}}' in template_content:
            full_html = template_content.replace('{{content}}', html_content)
        else:
            if '</body>' in template_content:
                full_html = template_content.replace('</body>', f'{html_content}\n</body>')
            else:
                full_html = template_content + html_content

        # Replace all template placeholders
        full_html = full_html.replace('$title$', title)
        full_html = full_html.replace('$lang$', lang_cfg['lang_attr'])
        full_html = full_html.replace('$body_font$', lang_cfg['font_family'])
        full_html = full_html.replace('$toc_label$', lang_cfg['toc_label'])

        # Inject author meta tag into <head> so calibre_html_publish.py can extract it
        if author:
            author_meta = f'<meta name="author" content="{author}">'
            if '<head>' in full_html or '<head ' in full_html:
                full_html = re.sub(
                    r'(<head[^>]*>)',
                    r'\1\n    ' + author_meta,
                    full_html,
                    count=1,
                    flags=re.IGNORECASE
                )

        # Idea C: inject original document font hints to improve visual fidelity
        if style_hints:
            ff = style_hints.get('font_family')
            fs = style_hints.get('font_size')
            if ff or fs:
                parts = []
                if ff:
                    parts.append(f"font-family: {ff}")
                if fs:
                    parts.append(f"font-size: {fs}")
                extra = f'<style class="doc-hints">body {{ {"; ".join(parts)}; }}</style>'
                full_html = re.sub(r'(</head>)', extra + r'\n\1', full_html, count=1, flags=re.IGNORECASE)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        return True
    except Exception as e:
        print(f"Error applying template: {e}")
        return False


def process_html_separators(html_file):
    """Process page separators in HTML"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        content = re.sub(r'<hr\s*/?>', '<div class="page-separator"></div>', content)
        content = re.sub(r'<p>\s*---\s*</p>', '<div class="page-separator"></div>', content)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error processing separators: {e}")


_PARA_MARKER_RE = re.compile(r'^\[P:\d+\]\s*', re.MULTILINE)


def _write_clean_md(md_file, clean_file):
    """Write a copy of md_file with [P:N] paragraph markers stripped.

    output.md keeps its markers so build_docx.py can map translations back to
    the source DOCX paragraphs. The clean copy is used only for HTML/PDF output
    where the markers must not appear in the rendered text.
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = _PARA_MARKER_RE.sub('', content)
    with open(clean_file, 'w', encoding='utf-8') as f:
        f.write(cleaned)


def convert_md_to_html(temp_dir, title, lang_cfg, author=None):
    """Convert output.md to HTML with templates"""
    print("=== Converting markdown to HTML ===")

    md_file = os.path.join(temp_dir, 'output.md')
    if not os.path.exists(md_file):
        print("Error: output.md not found.")
        return False

    book_doc_file = os.path.join(temp_dir, 'output_doc.html')

    # Skip HTML generation if output_doc.html exists and is newer than output.md
    if os.path.exists(book_doc_file):
        if os.path.getmtime(book_doc_file) > os.path.getmtime(md_file):
            if _check_generated_html_sanity(book_doc_file):
                print("Skipping HTML generation - output_doc.html is up to date")
                return True
            print("Stale output_doc.html failed image sanity — regenerating")
            os.remove(book_doc_file)
        else:
            print("Re-generating HTML - output.md is newer")

    temp_html_file = os.path.join(temp_dir, 'output.html')

    # Strip [P:N] markers for HTML/PDF rendering (output.md keeps them for build_docx.py)
    clean_md_file = os.path.join(temp_dir, 'output_clean.md')
    _write_clean_md(md_file, clean_md_file)

    # Try pandoc -> python-markdown -> basic regex
    success = False
    if check_pandoc_available():
        success = convert_with_pandoc(clean_md_file, temp_html_file, title, lang_cfg['lang_attr'])

    if not success:
        success = convert_with_python_markdown(clean_md_file, temp_html_file, title)

    if not success:
        success = convert_with_basic_regex(clean_md_file, temp_html_file, title)

    if not success:
        print("Error: All markdown-to-HTML converters failed")
        return False

    process_html_separators(temp_html_file)

    # Extract body content
    try:
        with open(temp_html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False

    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    body_content = body_match.group(1).strip() if body_match else html_content

    # Idea C: extract original document style hints for visual fidelity
    style_hints = _extract_doc_style_hints(temp_dir)

    # Generate output_doc.html with ebook template
    template_ebook = os.path.join(SCRIPT_DIR, 'templates', 'template_doc.html')
    book_doc_file = os.path.join(temp_dir, 'output_doc.html')
    apply_template_to_html(body_content, template_ebook, book_doc_file, title, lang_cfg, author, style_hints)

    # Generate output_web.html with web template
    template_web = os.path.join(SCRIPT_DIR, 'templates', 'template.html')
    book_file = os.path.join(temp_dir, 'output_web.html')
    apply_template_to_html(body_content, template_web, book_file, title, lang_cfg, author, style_hints)

    if not _check_generated_html_sanity(book_doc_file):
        return False
    if not _check_generated_html_sanity(book_file):
        return False

    print(f"Generated: output.html, output_doc.html, output_web.html")
    return True


# =============================================================================
# Step 6: Add TOC
# =============================================================================

def generate_heading_id(text, existing_ids):
    """Generate unique ID for heading"""
    base_id = re.sub(r'[^\w\s-]', '', text.lower())
    base_id = re.sub(r'[-\s]+', '-', base_id)
    base_id = base_id.strip('-')

    if not base_id:
        base_id = 'heading'

    heading_id = base_id
    counter = 1
    while heading_id in existing_ids:
        heading_id = f"{base_id}-{counter}"
        counter += 1

    return heading_id


def generate_simple_toc_html(toc_data):
    """Generate simple HTML for table of contents"""
    if not toc_data:
        return ""

    toc_html = '<ul>\n'
    current_level = 1

    for item in toc_data:
        level = item['level']
        text = item['text']
        heading_id = item['id']

        if level > current_level:
            while current_level < level:
                toc_html += '<li><ul>\n'
                current_level += 1
        elif level < current_level:
            while current_level > level:
                toc_html += '</ul></li>\n'
                current_level -= 1

        toc_html += f'<li><a href="#{heading_id}">{text}</a></li>\n'

    while current_level > 1:
        toc_html += '</ul></li>\n'
        current_level -= 1

    toc_html += '</ul>\n'
    return toc_html


def insert_toc_with_bs4(html_file):
    """Insert TOC using BeautifulSoup"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False

    soup = BeautifulSoup(html_content, 'html.parser')

    toc_data = []
    existing_ids = []

    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(heading.name[1])
        text = heading.get_text().strip()
        if not text:
            continue

        heading_id = generate_heading_id(text, existing_ids)
        existing_ids.append(heading_id)
        heading['id'] = heading_id
        toc_data.append({'level': level, 'text': text, 'id': heading_id})

    if not toc_data:
        print("No headings found for TOC")
        return False

    toc_html = generate_simple_toc_html(toc_data)

    toc_content_div = soup.find('div', class_='toc-content')
    if toc_content_div:
        toc_content_div.clear()
        toc_soup = BeautifulSoup(toc_html, 'html.parser')
        toc_content_div.append(toc_soup)
        print(f"TOC inserted ({len(toc_data)} headings)")
    else:
        print("Warning: .toc-content div not found, TOC not inserted")
        return False

    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False


def insert_toc_with_regex(html_file):
    """Insert TOC using regex (fallback)"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return False

    heading_pattern = r'<(h[1-6])(?:[^>]*)>(.*?)</\1>'
    headings = re.findall(heading_pattern, html_content, re.IGNORECASE | re.DOTALL)

    if not headings:
        print("No headings found for TOC")
        return False

    toc_html = '<ul>\n'
    for i, (tag, text) in enumerate(headings):
        level = int(tag[1])
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        heading_id = f"heading-{i+1}"

        old_heading = f'<{tag}>{text}</{tag}>'
        new_heading = f'<{tag} id="{heading_id}">{text}</{tag}>'
        html_content = html_content.replace(old_heading, new_heading, 1)

        if level > 1:
            for _ in range(level - 1):
                toc_html += '  '
        toc_html += f'<li><a href="#{heading_id}">{clean_text}</a></li>\n'

    toc_html += '</ul>\n'

    toc_content_pattern = r'(<div[^>]*class="toc-content[^"]*"[^>]*>).*?(</div>)'
    if re.search(toc_content_pattern, html_content, re.DOTALL):
        html_content = re.sub(
            toc_content_pattern,
            r'\1' + toc_html + r'\2',
            html_content,
            flags=re.DOTALL
        )
        print(f"TOC inserted ({len(headings)} headings)")
    else:
        print("Warning: .toc-content div not found")
        return False

    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return True
    except Exception as e:
        print(f"Error saving HTML file: {e}")
        return False


def add_toc(temp_dir):
    """Add TOC to output_web.html"""
    print("=== Adding Table of Contents ===")

    book_file = os.path.join(temp_dir, 'output_web.html')
    if not os.path.exists(book_file):
        print("Warning: output_web.html not found, skipping TOC")
        return False

    if BS4_AVAILABLE:
        return insert_toc_with_bs4(book_file)
    else:
        return insert_toc_with_regex(book_file)


# =============================================================================
# Step 7: Generate DOCX/EPUB/PDF with error transparency
# =============================================================================

def generate_format(html_file, temp_dir, output_ext, lang_attr):
    """Generate a specific format using calibre_html_publish.py"""
    output_file = os.path.join(temp_dir, f"output{output_ext}")

    if os.path.exists(output_file):
        output_mtime = os.path.getmtime(output_file)

        # Check if source HTML is newer
        html_newer = os.path.getmtime(html_file) > output_mtime

        # Check if any image asset is newer (Calibre embeds these)
        images_newer = False
        images_dir = os.path.join(temp_dir, 'images')
        if os.path.isdir(images_dir):
            for img in os.listdir(images_dir):
                img_path = os.path.join(images_dir, img)
                if os.path.isfile(img_path) and os.path.getmtime(img_path) > output_mtime:
                    images_newer = True
                    break

        if not html_newer and not images_newer:
            file_size = os.path.getsize(output_file)
            print(f"Skipping {output_ext} - already exists and up to date ({file_size:,} bytes)")
            return output_file
        else:
            reasons = []
            if html_newer:
                reasons.append("source HTML changed")
            if images_newer:
                reasons.append("image assets changed")
            print(f"Rebuilding {output_ext} - {', '.join(reasons)}")

    publish_script = os.path.join(SCRIPT_DIR, "calibre_html_publish.py")
    if not os.path.exists(publish_script):
        print(f"calibre_html_publish.py not found at: {publish_script}")
        return None

    try:
        cmd = ["python3", publish_script, html_file, "-o", output_file, "--lang", lang_attr]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            return output_file
        else:
            print(f"Failed to generate {output_ext}")
            if result.stdout:
                print(f"  stdout: {result.stdout[-500:]}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate {output_ext}")
        if e.stdout:
            print(f"  stdout: {e.stdout[-500:]}")
        if e.stderr:
            print(f"  stderr: {e.stderr[-500:]}")
        return None
    except Exception as e:
        print(f"Error generating {output_ext}: {e}")
        return None


def generate_formats(temp_dir, lang_attr, skip_docx=False, skip_pdf=False):
    """Generate DOCX and PDF with result summary.

    skip_docx=True when native DOCX was already built by _build_docx_native().
    skip_pdf=True when PDF was already built by _build_pdf_from_docx().
    """
    print("=== Generating output formats ===")

    html_file = os.path.join(temp_dir, "output_doc.html")
    if not os.path.exists(html_file):
        html_files = glob.glob(os.path.join(temp_dir, "*.html"))
        if html_files:
            html_file = max(html_files, key=os.path.getmtime)
        else:
            print("No HTML files found for format generation")
            return

    results = {}
    for ext in ['.docx', '.pdf']:
        if ext == '.docx' and skip_docx:
            docx_path = os.path.join(temp_dir, "output.docx")
            if os.path.exists(docx_path):
                results[ext] = ('OK', f"{os.path.getsize(docx_path):,} bytes (native)")
            continue
        if ext == '.pdf' and skip_pdf:
            pdf_path = os.path.join(temp_dir, "output.pdf")
            if os.path.exists(pdf_path):
                results[ext] = ('OK', f"{os.path.getsize(pdf_path):,} bytes (from native DOCX)")
            continue
        result = generate_format(html_file, temp_dir, ext, lang_attr)
        if result:
            file_size = os.path.getsize(result)
            results[ext] = ('OK', f"{file_size:,} bytes")
        else:
            results[ext] = ('FAILED', '')

    # Print summary table
    print("\nFormat results:")
    has_failures = False
    for ext, (status, detail) in results.items():
        if status == 'OK':
            print(f"  {ext}: {status} ({detail})")
        else:
            print(f"  {ext}: {status}")
            has_failures = True

    return not has_failures


def _validate_export_name(name):
    """Validate an export filename stem. Keep aliases inside temp_dir."""
    if not name or not name.strip():
        raise ValueError("--export-name must not be empty")
    if '\x00' in name or '/' in name or '\\' in name:
        raise ValueError("--export-name must be a filename stem, not a path")
    return name.strip()


def export_named_aliases(temp_dir, export_name):
    """Copy canonical outputs to optional user-facing filenames.

    Canonical artifacts remain untouched. The alias names use export_name as a
    filename stem, with book_doc.html receiving a _doc suffix to avoid colliding
    with the web HTML alias.
    """
    stem = _validate_export_name(export_name)
    mappings = {
        "output_web.html": f"{stem}.html",
        "output_doc.html": f"{stem}_doc.html",
        "output.docx": f"{stem}.docx",
        "output.pdf": f"{stem}.pdf",
    }
    copied = []
    for src_name, dst_name in mappings.items():
        src = os.path.join(temp_dir, src_name)
        if not os.path.exists(src):
            continue
        dst = os.path.join(temp_dir, dst_name)
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        shutil.copy2(src, dst)
        copied.append(dst_name)
    return copied


# =============================================================================
# Idea B+C: Native DOCX build + original-document style hints
# =============================================================================

def _extract_doc_style_hints(temp_dir):
    """Idea C: extract font/size hints from Calibre's input.html for output enrichment."""
    input_html = os.path.join(temp_dir, "input.html")
    if not os.path.exists(input_html):
        return {}
    try:
        with open(input_html, 'r', encoding='utf-8') as f:
            content = f.read()
        hints = {}
        m = re.search(r'font-family\s*:\s*([^;}\n]{3,80})', content, re.IGNORECASE)
        if m:
            hints['font_family'] = m.group(1).strip().strip('"\'')
        m = re.search(r'font-size\s*:\s*([\d.]+(?:pt|px|em|rem))', content, re.IGNORECASE)
        if m:
            hints['font_size'] = m.group(1).strip()
        return hints
    except Exception:
        return {}


def _build_pdf_from_docx(temp_dir):
    """Convert output.docx to output.pdf using LibreOffice (better than HTML→Calibre for native DOCX).

    Returns True on success. Falls back silently so caller can use Calibre route.
    """
    docx_path = os.path.join(temp_dir, "output.docx")
    if not os.path.exists(docx_path):
        return False

    pdf_path = os.path.join(temp_dir, "output.pdf")

    # Check if PDF is already up to date
    if os.path.exists(pdf_path) and os.path.getmtime(pdf_path) >= os.path.getmtime(docx_path):
        print(f"Skipping PDF — already up to date ({os.path.getsize(pdf_path):,} bytes)")
        return True

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False

    try:
        cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", temp_dir, docx_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(pdf_path):
            print(f"PDF built from native DOCX via LibreOffice ({os.path.getsize(pdf_path):,} bytes)")
            return True
        print(f"LibreOffice PDF failed: {result.stderr[-300:]}")
    except Exception as e:
        print(f"LibreOffice PDF error: {e}")
    return False


def _build_pdf_inplace(temp_dir):
    """Rebuild PDF from translated [E:id] chunks + pdf_structure.json (pdf_inplace mode).

    Reads all output_chunk*.md, parses [E:id] markers, calls pdf_inplace_build.rebuild,
    then runs validation and remediation if available. Exits with non-zero on failure.
    """
    import json as _json
    import sys as _sys
    _pdf_dir = os.path.join(SCRIPT_DIR, "pdf")
    if _pdf_dir not in _sys.path:
        _sys.path.insert(0, _pdf_dir)

    try:
        from pdf_chunk_io import read_outputs
        from pdf_inplace_build import rebuild
    except ImportError as e:
        print(f"PDF in-place build not available: {e}")
        sys.exit(1)

    struct_path = os.path.join(temp_dir, "pdf_structure.json")
    if not os.path.exists(struct_path):
        print(f"Error: pdf_structure.json not found in {temp_dir}")
        sys.exit(1)

    config = load_config(temp_dir)
    input_file = config.get("input_file", "")
    if not os.path.exists(input_file):
        print(f"Error: original PDF not found: {input_file}")
        sys.exit(1)

    with open(struct_path, encoding="utf-8") as f:
        structure = _json.load(f)

    # Collect source element ids from chunks (to validate outputs)
    import glob as _glob, re as _re
    _E_RE = _re.compile(r"^\[E:([\w]+_\d+)\]", _re.MULTILINE)
    source_ids = []
    for fname in sorted(_glob.glob(os.path.join(temp_dir, "chunk*.md"))):
        if os.path.basename(fname).startswith("output_"):
            continue
        with open(fname, encoding="utf-8") as f:
            for m in _E_RE.finditer(f.read()):
                source_ids.append(m.group(1))

    if not source_ids:
        print("Error: no source element ids found in chunk*.md")
        sys.exit(1)

    try:
        id_to_text = read_outputs(temp_dir, source_ids)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error reading translated outputs: {e}")
        sys.exit(1)

    # Build translated_elements preserving original order
    translated_elements = [
        {"id": eid, "translated_text": id_to_text[eid]} for eid in source_ids
    ]

    out_path = os.path.join(temp_dir, "output.pdf")
    print(f"=== PDF in-place rebuild ({len(translated_elements)} elements) ===")
    fit_results = rebuild(input_file, translated_elements, structure, out_path)

    # Write validation JSON for Phase 04
    val_data = _build_pdf_validation(fit_results, structure)
    val_path = os.path.join(temp_dir, "pdf_validation.json")
    with open(val_path, "w", encoding="utf-8") as f:
        _json.dump(val_data, f, ensure_ascii=False, indent=2)

    overflow_count = sum(1 for v in val_data.values() if v.get("overflow_ids"))
    print(f"Validation: {len(val_data)} pages • overflow pages: {overflow_count}")

    # Run image-region diff validation if available
    try:
        from pdf_validate import validate_image_regions
        img_ok = validate_image_regions(input_file, out_path, structure, val_path)
        if img_ok:
            print("Image-region integrity: OK")
        else:
            print("WARNING: image-region diff detected — check pdf_validation.json")
    except ImportError:
        pass

    # Run remediation if any overflow pages
    if overflow_count > 0:
        try:
            from pdf_remediate import remediate
            prof_path = os.path.join(temp_dir, "pdf_profile.json")
            profile = None
            if os.path.exists(prof_path):
                with open(prof_path, encoding="utf-8") as f:
                    profile = _json.load(f)
            remediate(input_file, translated_elements, structure, out_path, val_path, profile)
        except ImportError:
            pass

    if os.path.exists(out_path):
        print(f"  output.pdf: {os.path.getsize(out_path):,} bytes")
    else:
        print("Error: output.pdf was not created")
        sys.exit(1)

    print(f"\n=== Build Complete ===")
    print(f"All outputs saved to: {temp_dir}")


def _build_pdf_validation(fit_results, structure):
    """Aggregate insert_htmlbox fit results into per-page validation report.

    Handles both normal ids ("page_line") and OCR ids ("ocr_page_line").
    """
    page_data = {}
    for elem_id, ret in fit_results.items():
        parts = elem_id.split("_")
        # ocr_0_5 → page 0; 0_5 → page 0
        page_id = parts[1] if parts[0] == "ocr" else parts[0]
        if page_id not in page_data:
            page_data[page_id] = {"overflow_ids": [], "empty_ids": [], "fit_count": 0}
        # ret = (spare_height, scale); spare_height < 0 means failed to fit
        if isinstance(ret, (tuple, list)) and ret[0] < 0:
            page_data[page_id]["overflow_ids"].append(elem_id)
        else:
            page_data[page_id]["fit_count"] += 1
    return page_data


def _build_xlsx_native(temp_dir):
    """Rebuild XLSX from translated chunks via build_xlsx.py. Returns True on success."""
    build_script = os.path.join(SCRIPT_DIR, "xlsx", "build_xlsx.py")
    if not os.path.exists(build_script):
        print(f"build_xlsx.py not found at: {build_script}")
        return False
    output_xlsx = os.path.join(temp_dir, "output.xlsx")
    try:
        cmd = ["python3", build_script, "--temp-dir", temp_dir, "--output", output_xlsx]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        return os.path.exists(output_xlsx)
    except subprocess.CalledProcessError as e:
        print(f"build_xlsx.py failed: {e.stderr[-400:] if e.stderr else '(no stderr)'}")
        return False


def _build_pptx_native(temp_dir):
    """Reconstruct PPTX from pptx_mapped.json + run cross-check. Exits on failure."""
    import json as _json
    import sys as _sys

    _pptx_dir = os.path.join(SCRIPT_DIR, "pptx")
    if _pptx_dir not in _sys.path:
        _sys.path.insert(0, _pptx_dir)

    mapped_path = os.path.join(temp_dir, "pptx_mapped.json")
    if not os.path.exists(mapped_path):
        print(f"Error: pptx_mapped.json not found — run the MAP pass (pptx_mapping.py finalize) first")
        _sys.exit(1)

    try:
        from build_pptx import build_pptx
    except ImportError as e:
        print(f"build_pptx not available: {e}")
        _sys.exit(1)

    config = load_config(temp_dir)
    source_pptx = config.get("input_file", "")

    print("=== Building PPTX (run reconstruction) ===")
    if not build_pptx(temp_dir):
        _sys.exit(1)

    output_pptx = os.path.join(temp_dir, "output.pptx")

    # Cross-check
    try:
        from pptx_cross_check import check as pptx_check
        report = pptx_check(temp_dir, source_pptx, output_pptx)
        n = report["elements"]
        missing = len(report["missing_map"])
        residue = len(report["residue"])
        concat_broken = len(report["concat_broken"])
        slides_ok = "OK" if report["slide_parity_ok"] else "MISMATCH"
        print(
            f"Cross-check: {n} elements • missing-map: {missing} • "
            f"residue: {residue} • concat-broken: {concat_broken} • slides: {slides_ok}"
        )
        if not report["ok"]:
            print("WARNING: cross-check found issues — see pptx_crosscheck.json")
    except ImportError:
        pass

    print(f"\n=== Build Complete ===")
    print(f"All outputs saved to: {temp_dir}")
    if os.path.exists(output_pptx):
        print(f"  output.pptx: {os.path.getsize(output_pptx):,} bytes")


def _build_docx_native(temp_dir):
    """Rebuild DOCX from docx_mapped.json + docx_structure.json via raw-XML engine.

    Requires the MAP pass (step 6.5) to have produced docx_mapped.json first.
    Returns True on success.
    """
    import json as _json

    struct_path = os.path.join(temp_dir, "docx_structure.json")
    mapped_path = os.path.join(temp_dir, "docx_mapped.json")

    if not os.path.exists(struct_path):
        return False

    if not os.path.exists(mapped_path):
        print("Skipping native DOCX build — docx_mapped.json not found. "
              "Run the MAP pass (step 6.5) before building.")
        return False

    try:
        with open(struct_path, 'r', encoding='utf-8') as f:
            structure = _json.load(f)
        source_docx = structure.get("source_docx", "")
    except Exception as e:
        print(f"Cannot read docx_structure.json: {e}")
        return False

    if not source_docx or not os.path.exists(source_docx):
        print(f"Source DOCX not found: {source_docx}")
        return False

    build_script = os.path.join(SCRIPT_DIR, "docx", "build_docx.py")
    if not os.path.exists(build_script):
        print(f"build_docx.py not found at: {build_script}")
        return False

    output_docx = os.path.join(temp_dir, "output.docx")
    try:
        cmd = ["python3", build_script, "--temp-dir", temp_dir, "--output", output_docx]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"build_docx.py failed: {e.stderr[-400:] if e.stderr else '(no stderr)'}")
        return False

    if not os.path.exists(output_docx):
        return False

    _run_docx_validation_and_remediation(temp_dir, output_docx, source_docx, structure)
    return True


def _run_docx_validation_and_remediation(temp_dir, output_docx, source_docx, structure):
    """Run docx_validate + docx_remediate after a native DOCX build."""
    docx_scripts_dir = os.path.join(SCRIPT_DIR, "docx")
    import sys as _sys
    if docx_scripts_dir not in _sys.path:
        _sys.path.insert(0, docx_scripts_dir)

    try:
        from docx_validate import validate
    except ImportError:
        return

    validate(temp_dir, output_docx)

    # Phase 5: remediation for marker-leak + run-mismatch
    try:
        import json as _json
        val_path = os.path.join(temp_dir, "docx_validation.json")
        if not os.path.exists(val_path):
            return
        with open(val_path, "r", encoding="utf-8") as f:
            val = _json.load(f)
        if val.get("ok") or val.get("skipped"):
            return
        has_fixable = val.get("marker_leak") or val.get("run_mismatch")
        if not has_fixable:
            return

        from docx_remediate import remediate
        # Build elem_index from structure
        elem_index = {}
        for elem in structure.get("elements", []):
            etype = elem.get("type")
            if etype in ("paragraph", "cell_paragraph", "hf_paragraph",
                         "footnote_paragraph", "endnote_paragraph",
                         "textbox_paragraph", "comment_paragraph"):
                elem_index[elem["elem_idx"]] = elem
            elif etype == "table":
                for cell in elem.get("cells", []):
                    for para in cell.get("paragraphs", []):
                        elem_index[para["elem_idx"]] = para
        remediate(temp_dir, output_docx, source_docx, elem_index)
    except Exception as e:
        print(f"DOCX remediation error (non-fatal): {e}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Merge translated pages and build final outputs')
    parser.add_argument('--temp-dir', required=True, help='Temp directory path')
    parser.add_argument('--title', default=None, help='Translated book title (override config)')
    parser.add_argument('--author', default=None, help='Author name (override config)')
    parser.add_argument('--lang', default=None, help='Output language code (override config)')
    parser.add_argument('--export-name', default=None, help='Optional filename stem for exported alias copies')
    parser.add_argument('--cleanup', action='store_true', help='Remove intermediate artifacts after successful build')
    parser.add_argument('--merge-only', action='store_true', help='Run only the merge step (produce output.md) then exit')

    args = parser.parse_args()
    temp_dir = args.temp_dir

    if not os.path.isdir(temp_dir):
        print(f"Error: Temp directory not found: {temp_dir}")
        sys.exit(1)

    export_name = None
    if args.export_name:
        try:
            export_name = _validate_export_name(args.export_name)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Load config as base, CLI args override
    config = load_config(temp_dir)

    lang_code = args.lang or config.get('output_lang', 'zh')
    lang_cfg = get_lang_config(lang_code)

    title = args.title or config.get('original_title', 'Translated Book')
    author = args.author or config.get('creator', 'Unknown Author')

    print(f"=== Merge and Build ===")
    print(f"Temp directory: {temp_dir}")
    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Language: {lang_code} (attr: {lang_cfg['lang_attr']})")

    # --merge-only: produce output.md then exit (used by MAP pass step 6.5)
    if args.merge_only:
        if not merge_markdown_files(temp_dir):
            sys.exit(1)
        print("Merge complete.")
        return

    # XLSX native: short-circuit — no HTML/DOCX/PDF pipeline needed
    conversion_method = config.get('conversion_method', 'calibre_htmlz')

    # PDF in-place: short-circuit — rebuild from structure JSON, skip HTML/Calibre
    if conversion_method == 'pdf_inplace':
        _build_pdf_inplace(temp_dir)
        return

    # PPTX native: short-circuit — reconstruct runs from pptx_mapped.json
    if conversion_method == 'pptx_native':
        _build_pptx_native(temp_dir)
        return

    if conversion_method == 'xlsx_native':
        if not _build_xlsx_native(temp_dir):
            sys.exit(1)
        output_xlsx = os.path.join(temp_dir, "output.xlsx")
        print(f"\n=== Build Complete ===")
        print(f"All outputs saved to: {temp_dir}")
        if os.path.exists(output_xlsx):
            print(f"  output.xlsx: {os.path.getsize(output_xlsx):,} bytes")
        if export_name:
            xlsx_src = output_xlsx
            if os.path.exists(xlsx_src):
                dst = os.path.join(temp_dir, f"{export_name}.xlsx")
                shutil.copy2(xlsx_src, dst)
                print(f"\nExport alias: {export_name}.xlsx")
        return

    # Step 4: Merge
    if not merge_markdown_files(temp_dir):
        sys.exit(1)

    # Step 5: Convert to HTML
    if not convert_md_to_html(temp_dir, title, lang_cfg, author):
        sys.exit(1)

    # Step 6: Add TOC
    add_toc(temp_dir)

    # Step 7: Generate formats (native DOCX if applicable, then PDF)
    skip_docx = False
    skip_pdf = False
    if conversion_method in ('docx_native', 'pdf_docx_bridge'):
        print("=== Building native DOCX ===")
        if _build_docx_native(temp_dir):
            print("Native DOCX build succeeded")
            skip_docx = True
            # Prefer LibreOffice for PDF when native DOCX is available (better layout fidelity)
            if _build_pdf_from_docx(temp_dir):
                skip_pdf = True
            else:
                print("LibreOffice PDF failed — will fall back to HTML→Calibre")
        else:
            print("Native DOCX build failed — will regenerate via HTML→Calibre fallback")

    all_formats_ok = generate_formats(temp_dir, lang_cfg['lang_attr'], skip_docx=skip_docx, skip_pdf=skip_pdf)

    if export_name:
        if all_formats_ok:
            aliases = export_named_aliases(temp_dir, export_name)
            if aliases:
                print("\nExport aliases:")
                for name in aliases:
                    print(f"  {name}")
        else:
            print("\nSkipping export aliases — some formats failed.")

    print("\n=== Build Complete ===")
    print(f"All outputs saved to: {temp_dir}")

    # List generated files
    for ext in ['output_web.html', 'output_doc.html', 'output.docx', 'output.pdf']:
        filepath = os.path.join(temp_dir, ext)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {ext}: {size:,} bytes")

    # Cleanup intermediate artifacts if requested (skip if any format failed)
    if args.cleanup:
        if all_formats_ok:
            cleanup_intermediate_files(temp_dir)
        else:
            print("\nSkipping cleanup — some formats failed. Intermediate files kept for diagnosis/retry.")


def cleanup_intermediate_files(temp_dir):
    """Remove intermediate artifacts, keeping only final outputs."""
    print("\n=== Cleaning up intermediate files ===")

    removed = []

    # Remove chunk*.md and output_chunk*.md
    for pattern in ['chunk*.md', 'output_chunk*.md']:
        for filepath in glob.glob(os.path.join(temp_dir, pattern)):
            os.remove(filepath)
            removed.append(os.path.basename(filepath))

    # Remove specific intermediate files
    for name in ['input.html', 'input.md', 'output.html', 'output_clean.md']:
        filepath = os.path.join(temp_dir, name)
        if os.path.exists(filepath):
            os.remove(filepath)
            removed.append(name)

    if removed:
        print(f"Removed {len(removed)} intermediate file(s):")
        # Summarize chunk files instead of listing each one
        chunk_files = [f for f in removed if 'chunk' in f]
        other_files = [f for f in removed if 'chunk' not in f]
        if chunk_files:
            print(f"  {len(chunk_files)} chunk files (chunk*.md, output_chunk*.md)")
        for f in other_files:
            print(f"  {f}")
    else:
        print("No intermediate files to remove.")


if __name__ == "__main__":
    main()
