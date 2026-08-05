#!/usr/bin/env python3
"""gen-slide: render a PPTX from a project_profile.md.

Reads a profile markdown (produced by gen-md.py) and renders it into the
SVN proposal PPTX template via the role-based renderer pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Make third-party deps (python-pptx, lxml, Pillow) importable before any lib
# import. No-op on local/venv installs; self-bootstraps on the read-only,
# pip-less Claude Desktop sandbox. MUST run before importing lib.renderer.
from ensure_deps import ensure_deps
ensure_deps()

from lib.profile_parser import parse_profile
from lib.renderer import PPTXRenderer


def main():
    ap = argparse.ArgumentParser(description='Render PPTX from project_profile markdown')
    ap.add_argument('--input', required=True, help='Path to project_content_{id}_{ts}.md')
    ap.add_argument('--output', help='Output file name without .pptx (default: derived from input)')
    ap.add_argument('--output-dir', help='Output directory (default: env SLIDE_GENERATOR__OUTPUTS_PATH or ./outputs)')
    ap.add_argument('--template', default='SVN Proposal Menu.pptx', help='Template PPTX name or path')
    ap.add_argument('--extra-slides', help='Path to JSON file with AI-generated extra slides '
                    '(list of {title, bullets[], anchor_section|anchor_slide}). '
                    'Each slide is cloned from template slide 71 and inserted after its anchor.')
    args = ap.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        sys.exit(f'Input not found: {md_path}')

    md = md_path.read_text(encoding='utf-8')
    profile = parse_profile(md)

    # Resolve template path: absolute > scripts/templates > clio-generate/templates
    tpl = Path(args.template)
    if not tpl.is_absolute():
        candidates = [
            Path(__file__).parent / 'templates' / args.template,
            Path(__file__).parent.parent / 'templates' / args.template,
        ]
        for c in candidates:
            if c.exists():
                tpl = c
                break
        else:
            sys.exit(f'Template not found: {args.template}')

    # Derive output name from project_id+timestamp when not given
    output_name = args.output or f'proposal_{profile.project_id}_{profile.timestamp}'

    # Auto-routed extras from unrecognized `##` headings (see profile_parser.py
    # / extra_slide_classifier.py) always apply; --extra-slides JSON (manual,
    # AI-crafted layouts) is appended on top rather than replacing them.
    extra_slides = list(profile.auto_extra_slides)
    if args.extra_slides:
        extra_path = Path(args.extra_slides)
        if not extra_path.exists():
            sys.exit(f'Extra-slides JSON not found: {extra_path}')
        try:
            manual_extra_slides = json.loads(extra_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            sys.exit(f'Invalid JSON in {extra_path}: {e}')
        if not isinstance(manual_extra_slides, list):
            sys.exit('--extra-slides JSON must be a list of slide entries')
        print(f'Loaded {len(manual_extra_slides)} extra slide(s) from {extra_path}')
        extra_slides.extend(manual_extra_slides)
    if not extra_slides:
        extra_slides = None

    renderer = PPTXRenderer()
    out_file = renderer.render_from_profile(
        profile, str(tpl), output_name, args.output_dir,
        extra_slides=extra_slides,
    )
    print(f'Done: {out_file}')


if __name__ == '__main__':
    main()
