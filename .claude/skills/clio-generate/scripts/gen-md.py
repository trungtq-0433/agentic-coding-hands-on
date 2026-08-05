#!/usr/bin/env python3
"""gen-md: emit a project_content_{id}.md from JSON input.

Reads a JSON document matching `ProjectProfile.to_dict()` (from stdin or file)
and writes a domain-organized markdown profile to:
  {output_dir}/project_content_{project_id}.md

Fixed filename (no timestamp) so each project has exactly one canonical
markdown file — uploading it to Clio replaces the previous version.

The skill agent populates the JSON by querying Clio KG; this script is a
pure formatter and has no Clio/MCP dependency.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from lib.profile_schema import ProjectProfile, section_has_content


# ---------------------------------------------------------------------------
# Markdown primitives
# ---------------------------------------------------------------------------

def _esc(cell: str) -> str:
    """Escape a single table cell — replace pipes with HTML entity."""
    return str(cell).replace('|', '&#124;').replace('\n', ' ')


def _emit_table(rows: list[dict]) -> str:
    """Emit a markdown pipe table from list[dict]. Returns empty string if rows empty."""
    if not rows:
        return ''
    headers = list(rows[0].keys())
    lines = [
        '| ' + ' | '.join(headers) + ' |',
        '|' + '|'.join(['---'] * len(headers)) + '|',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(_esc(row.get(h, '')) for h in headers) + ' |')
    return '\n'.join(lines)


def _emit_list(items: list[str]) -> str:
    """Emit bulleted list. Empty list → empty string."""
    return '\n'.join(f'- {item}' for item in items)


def _emit_image_ref(path: str) -> str:
    """Emit `Image: path` line if path non-empty."""
    return f'Image: {path}' if path else ''


def _nonempty(parts: list[str]) -> str:
    """Join non-empty parts with blank lines between."""
    return '\n\n'.join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Section emitters — one per top-level section
# ---------------------------------------------------------------------------

def _emit_background(p: ProjectProfile) -> str:
    bg = p.project_background
    if not section_has_content(p, 'project_background'):
        return ''
    parts = ['## Project Background']
    if bg.current_issues:
        parts.append(f'### Current Issues\n{bg.current_issues}')
    if bg.objectives:
        parts.append(f'### Objectives\n{bg.objectives}')
    return _nonempty(parts)


def _emit_features(p: ProjectProfile) -> str:
    f = p.features
    if not section_has_content(p, 'features'):
        return ''
    parts = ['## Features']
    if f.description:
        parts.append(f'### Description\n{f.description}')
    if f.table:
        parts.append(f'### Feature Table\n{_emit_table(f.table)}')
    return _nonempty(parts)


def _emit_nfr_overview(p: ProjectProfile) -> str:
    n = p.nfr_overview
    if not section_has_content(p, 'nfr_overview'):
        return ''
    parts = ['## Non-Functional Requirements (Overview)']
    if n.description:
        parts.append(f'### Description\n{n.description}')
    if n.table:
        parts.append(f'### Requirements Table\n{_emit_table(n.table)}')
    return _nonempty(parts)


def _emit_screen_flow(p: ProjectProfile) -> str:
    if not section_has_content(p, 'screen_flow'):
        return ''
    return f'## Screen Flow\n\n{_emit_image_ref(p.screen_flow.image_path)}'


def _emit_business_process(p: ProjectProfile) -> str:
    bp = p.business_process
    if not section_has_content(p, 'business_process'):
        return ''
    parts = ['## Business Process']
    if bp.categories:
        parts.append(f'### Categories\n{_emit_list(bp.categories)}')
    if bp.before_steps:
        parts.append(f'### Before (Current Process)\n{_emit_list(bp.before_steps)}')
    if bp.after_blocks:
        after = ['### After (Post-Introduction)']
        for blk in bp.after_blocks:
            after.append(f'#### {blk.title}\n{blk.body}')
        parts.append('\n\n'.join(after))
    return _nonempty(parts)


def _emit_benefits(p: ProjectProfile) -> str:
    if not section_has_content(p, 'benefits'):
        return ''
    parts = ['## Benefits']
    for b in p.benefits:
        parts.append(f'### {b.title}\n{b.content}')
    return _nonempty(parts)


def _emit_approach_comparison(p: ProjectProfile) -> str:
    if not section_has_content(p, 'approach_comparison'):
        return ''
    return f'## Approach Comparison\n\n{_emit_table(p.approach_comparison)}'


def _emit_assumptions(p: ProjectProfile) -> str:
    if not section_has_content(p, 'assumptions'):
        return ''
    parts = ['## Assumptions']
    for a in p.assumptions:
        parts.append(f'### {a.label}\n{a.content}')
    return _nonempty(parts)


def _emit_infrastructure(p: ProjectProfile) -> str:
    if not section_has_content(p, 'infrastructure'):
        return ''
    return f'## Infrastructure\n\n{_emit_table(p.infrastructure)}'


def _emit_software_stack(p: ProjectProfile) -> str:
    if not section_has_content(p, 'software_stack'):
        return ''
    return f'## Software Stack\n\n{_emit_table(p.software_stack)}'


def _emit_nfr_sections(p: ProjectProfile) -> str:
    if not section_has_content(p, 'nfr_sections'):
        return ''
    parts = ['## NFR Sections']
    for s in p.nfr_sections:
        parts.append(f'### {s.title}\n{s.body}')
    return _nonempty(parts)


def _emit_nfr_detailed(p: ProjectProfile) -> str:
    if not section_has_content(p, 'nfr_detailed'):
        return ''
    return f'## NFR Detailed\n\n{_emit_table(p.nfr_detailed)}'


def _emit_schedule(p: ProjectProfile) -> str:
    s = p.schedule
    if not section_has_content(p, 'schedule'):
        return ''
    parts = ['## Schedule']
    if s.description:
        parts.append(f'### Description\n{s.description}')
    if s.image_path:
        parts.append(f'### Chart\n{_emit_image_ref(s.image_path)}')
    return _nonempty(parts)


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

_EMITTERS = [
    _emit_background, _emit_features, _emit_nfr_overview, _emit_screen_flow,
    _emit_business_process, _emit_benefits, _emit_approach_comparison,
    _emit_assumptions, _emit_infrastructure, _emit_software_stack,
    _emit_nfr_sections, _emit_nfr_detailed, _emit_schedule,
]


def render_profile_md(profile: ProjectProfile) -> str:
    """Render a ProjectProfile to its markdown form."""
    header = f'# Project Profile: {profile.project_id}\nGenerated: {profile.timestamp}'
    body = _nonempty([emit(profile) for emit in _EMITTERS])
    return f'{header}\n\n{body}\n' if body else f'{header}\n'


def _resolve_output_dir(arg: Optional[str]) -> Path:
    if arg:
        return Path(arg)
    env = os.getenv('SLIDE_GENERATOR__OUTPUTS_PATH')
    if env:
        return Path(env).expanduser()
    return Path.cwd() / 'outputs'


def main():
    ap = argparse.ArgumentParser(description='Emit a project_profile markdown from JSON input')
    ap.add_argument('--project-id', required=True, help='Project identifier')
    ap.add_argument('--input', help='Input JSON file (default: stdin)')
    ap.add_argument('--output-dir', help='Output directory (default: env SLIDE_GENERATOR__OUTPUTS_PATH or ./outputs)')
    ap.add_argument('--timestamp', help='Timestamp string (default: now as YYYYMMDD_HHMMSS)')
    args = ap.parse_args()

    # Load input JSON
    if args.input:
        data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    else:
        data = json.loads(sys.stdin.read())

    timestamp = args.timestamp or datetime.now().strftime('%Y%m%d_%H%M%S')
    data['project_id'] = args.project_id
    data['timestamp'] = timestamp

    profile = ProjectProfile.from_dict(data)
    md = render_profile_md(profile)

    out_dir = _resolve_output_dir(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'project_content_{args.project_id}.md'
    out_file.write_text(md, encoding='utf-8')

    # Count emitted sections
    count = sum(1 for emit in _EMITTERS if emit(profile))
    print(f'Wrote {out_file} ({count}/{len(_EMITTERS)} sections, {len(md)} chars)')


if __name__ == '__main__':
    main()
