#!/usr/bin/env python3
"""Generate PPTX from markdown with FILL_SLIDE/SHAPE markers.

Usage:
    python generate_pptx.py --input slides.md [--output name] [--output-dir dir/] [--template "SVN Proposal Menu.pptx"]
    python generate_pptx.py --input slides.md --images images.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.parser import MarkdownParser
from lib.generator import SpecGenerator
from lib.renderer import PPTXRenderer


def load_images(images_path: str) -> list[dict]:
    """Load images array from JSON file.

    Expected format:
    [
        {"slide_number": 8, "shape_name": "screen_flow_image", "data": "data:image/png;base64,..."},
        {"slide_number": 43, "shape_name": "schedule_image", "data": "data:image/png;base64,..."}
    ]
    """
    with open(images_path, 'r') as f:
        return json.load(f)


def inject_images_into_markdown(markdown: str, images: list[dict]) -> str:
    """Inject image data into markdown content at the correct SHAPE positions.

    For each image, finds the matching FILL_SLIDE + SHAPE block and replaces
    the shape content with the image data URI or file path.
    """
    if not images:
        return markdown

    for img in images:
        slide_num = img['slide_number']
        shape_name = img['shape_name']
        image_data = img['data']

        # Find the FILL_SLIDE marker for this slide
        fill_marker = f'<!-- FILL_SLIDE: {slide_num} -->'
        shape_marker = f'<!-- SHAPE: {shape_name} -->'

        if fill_marker not in markdown:
            print(f'[WARN] FILL_SLIDE {slide_num} not found in markdown, skipping image')
            continue

        if shape_marker not in markdown:
            print(f'[WARN] SHAPE {shape_name} not found in markdown, skipping image')
            continue

        # Find the shape marker within this slide's section
        fill_idx = markdown.index(fill_marker)
        # Find next FILL_SLIDE or end of file
        next_fill = markdown.find('<!-- FILL_SLIDE:', fill_idx + len(fill_marker))
        slide_section = markdown[fill_idx:next_fill] if next_fill != -1 else markdown[fill_idx:]

        # Find shape marker within slide section
        shape_idx = slide_section.find(shape_marker)
        if shape_idx == -1:
            continue

        # Find content after shape marker (until next SHAPE or END SHAPE or FILL_SLIDE)
        content_start = shape_idx + len(shape_marker)
        next_shape = slide_section.find('<!-- SHAPE:', content_start)
        next_end_shape = slide_section.find('<!-- END SHAPE', content_start)
        next_fill_in_section = slide_section.find('<!-- FILL_SLIDE:', content_start)

        end_positions = [p for p in [next_shape, next_end_shape, next_fill_in_section, len(slide_section)] if p > content_start]
        content_end = min(end_positions) if end_positions else len(slide_section)

        # Replace the content between shape marker and next marker
        old_content = slide_section[content_start:content_end]
        new_slide_section = slide_section[:content_start] + '\n' + image_data + '\n' + slide_section[content_end:]

        # Rebuild markdown
        new_markdown = markdown[:fill_idx] + new_slide_section
        if next_fill != -1:
            new_markdown += markdown[next_fill:]

        markdown = new_markdown
        print(f'[OK] Injected image for slide {slide_num}, shape {shape_name} ({len(image_data)} chars)')

    return markdown


def main():
    parser = argparse.ArgumentParser(description='Generate PPTX from markdown content')
    parser.add_argument('--input', '-i', required=True, help='Input markdown file path')
    parser.add_argument('--output', '-o', help='Output PPTX file path (default: auto-generated)')
    parser.add_argument('--template', '-t', default='SVN Proposal Menu.pptx', help='Template PPTX file name')
    parser.add_argument('--images', help='JSON file with images array (base64 data URIs)')
    parser.add_argument('--template-dir', help='Template directory (default: ../templates/)')
    parser.add_argument('--output-dir', help='Output directory (default: same as input file)')

    args = parser.parse_args()

    # Resolve paths
    input_path = Path(args.input)
    if not input_path.exists():
        print(f'[ERROR] Input file not found: {input_path}')
        sys.exit(1)

    # Template directory
    if args.template_dir:
        template_dir = Path(args.template_dir)
    else:
        template_dir = Path(__file__).parent / 'templates'
    template_path = template_dir / args.template
    if not template_path.exists():
        # Fallback: try sibling templates/ dir
        alt_template_dir = Path(__file__).parent.parent / 'templates'
        template_path = alt_template_dir / args.template
        if not template_path.exists():
            print(f'[ERROR] Template not found: {args.template}')
            print(f'  Searched: {template_dir} and {alt_template_dir}')
            sys.exit(1)

    # Output path
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.output and Path(args.output).is_absolute():
        output_dir = Path(args.output).parent
    else:
        output_dir = input_path.parent

    if args.output:
        output_name = Path(args.output).stem
    else:
        output_name = input_path.stem.replace('slides_', 'proposal_')
    output_path = output_dir / f'{output_name}.pptx'

    # Read markdown content
    print(f'[1/4] Reading markdown: {input_path}')
    markdown_content = input_path.read_text(encoding='utf-8')

    # Inject images if provided
    if args.images:
        print(f'[2/4] Loading images: {args.images}')
        images = load_images(args.images)
        print(f'       Found {len(images)} image(s)')
        markdown_content = inject_images_into_markdown(markdown_content, images)
    else:
        print('[2/4] No images to inject')

    # Parse markdown
    print(f'[3/4] Parsing markdown content ({len(markdown_content)} chars)')
    md_parser = MarkdownParser()
    parsed_data = md_parser.parse_text(markdown_content)
    fill_slides = parsed_data['fill_slides']
    print(f'       Found {len(fill_slides)} slides to fill')

    # Generate slide content
    spec_gen = SpecGenerator()
    slides = spec_gen.generate(parsed_content=fill_slides)
    print(f'       Generated {len(slides)} slide specs')

    # Render PPTX
    print(f'[4/4] Rendering PPTX with template: {template_path.name}')
    renderer = PPTXRenderer()
    # Override template search to use our templates dir
    output_file = renderer.render(
        slides=slides,
        template=str(template_path),
        output_name=output_path.stem,
        output_dir=str(output_path.parent),
    )

    print(f'\n[DONE] PPTX generated: {output_file}')
    print(f'       Slides filled: {len(slides)}')
    return str(output_file)


if __name__ == '__main__':
    main()
