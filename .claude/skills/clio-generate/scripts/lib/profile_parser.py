"""Profile markdown parser — converts project_content_{id}_{ts}.md into ProjectProfile.

Markdown structure:
  # Project Profile: {id}
  Generated: {ts}

  ## Section Heading
  ### Subsection Heading      (optional)
  free text / bullet list / numbered list / table / `Image: path`
  ...

Tolerant: unknown sections logged + skipped; missing sections leave defaults.
"""
from __future__ import annotations

import re
from typing import Optional

from lib.extra_slide_classifier import build_extra_slide_entry
from lib.markdown_primitives import (
    parse_image_ref as _parse_image_ref,
    parse_list as _parse_list,
    parse_table as _parse_table,
    parse_text as _parse_text,
    split_subsections as _split_subsections,
)
from lib.profile_schema import (
    AfterBlock,
    AssumptionSection,
    BackgroundSection,
    BenefitSection,
    BusinessProcessSection,
    FeaturesSection,
    NFROverviewSection,
    NFRSection,
    ProjectProfile,
    ScheduleSection,
    ScreenFlowSection,
)

# Map normalized section heading -> handler name
_SECTION_MAP = {
    'project background': 'project_background',
    'features': 'features',
    'non-functional requirements (overview)': 'nfr_overview',
    'nfr overview': 'nfr_overview',
    'screen flow': 'screen_flow',
    'business process': 'business_process',
    'benefits': 'benefits',
    'approach comparison': 'approach_comparison',
    'assumptions': 'assumptions',
    'infrastructure': 'infrastructure',
    'software stack': 'software_stack',
    'nfr sections': 'nfr_sections',
    'nfr detailed': 'nfr_detailed',
    'schedule': 'schedule',
}


def parse_profile(markdown: str) -> ProjectProfile:
    """Top-level: parse markdown text into a ProjectProfile.

    Headings outside `_SECTION_MAP`'s fixed vocabulary (hand-written markdown
    that doesn't follow gen-md.py's schema) are never dropped — each is
    classified and shaped into an extra-slide entry (`auto_extra_slides`) so
    gen-slide.py can still place it in the deck via the generic layouts in
    `extra_slide_layouts.py`, anchored after the last recognized section.
    """
    project_id, timestamp = _parse_header(markdown)
    profile = ProjectProfile.empty(project_id=project_id, timestamp=timestamp)

    last_known_key = None
    for heading, content in _split_sections(markdown).items():
        key = _SECTION_MAP.get(heading.lower().strip())
        if not key:
            entry = _route_unmatched_section(heading, content, last_known_key)
            profile.auto_extra_slides.append(entry)
            print(f'[profile-parser] WARNING: unrecognized section "{heading}" — '
                  f'auto-routed to \'{entry["layout"]}\' extra-slide layout '
                  f'(anchor: {last_known_key or "end of deck"}); review the '
                  f'rendered slide before uploading to Clio')
            continue
        handler = globals().get(f'_handle_{key}')
        if handler:
            handler(profile, content)
            if key not in profile.section_order:
                profile.section_order.append(key)
            last_known_key = key
    return profile


def _route_unmatched_section(heading: str, content: str, anchor_section: Optional[str]) -> dict:
    """Classify one unrecognized `## heading` block into an extra-slide entry.

    Parsing (table/list/subsection detection) stays here, reusing the same
    primitives the known-section handlers use; `build_extra_slide_entry` only
    picks a layout and shapes the already-parsed pieces.
    """
    subs = _split_subsections(content)
    table_rows = _parse_table(content) if not subs else []
    list_items = _parse_list(content) if not subs and not table_rows else []
    entry = build_extra_slide_entry(
        heading, subsections=subs, table_rows=table_rows,
        list_items=list_items, raw_text=content,
    )
    entry['anchor_section'] = anchor_section
    return entry


# ---------------------------------------------------------------------------
# Header + section splitting
# ---------------------------------------------------------------------------

def _parse_header(md: str) -> tuple[str, str]:
    """Extract project_id from `# Project Profile: X` and timestamp from `Generated: X`."""
    pid_match = re.search(r'^#\s*Project Profile:\s*(\S+)', md, re.MULTILINE)
    ts_match = re.search(r'^Generated:\s*(\S+)', md, re.MULTILINE)
    return (pid_match.group(1) if pid_match else '',
            ts_match.group(1) if ts_match else '')


def _split_sections(md: str) -> dict[str, str]:
    """Split markdown by `^## ` headings. Returns {heading_text: content}."""
    parts: dict[str, str] = {}
    current_heading = None
    current_lines: list[str] = []
    for line in md.splitlines():
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m and not line.startswith('###'):
            if current_heading is not None:
                parts[current_heading] = '\n'.join(current_lines).strip()
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)
    if current_heading is not None:
        parts[current_heading] = '\n'.join(current_lines).strip()
    return parts


# ---------------------------------------------------------------------------
# Section handlers — one per top-level section
# ---------------------------------------------------------------------------

def _handle_project_background(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.project_background = BackgroundSection(
        current_issues=_parse_text(subs.get('Current Issues', '')),
        objectives=_parse_text(subs.get('Objectives', '')),
    )


def _handle_features(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.features = FeaturesSection(
        description=_parse_text(subs.get('Description', '')),
        table=_parse_table(subs.get('Feature Table', '')),
    )


def _handle_nfr_overview(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.nfr_overview = NFROverviewSection(
        description=_parse_text(subs.get('Description', '')),
        table=_parse_table(subs.get('Requirements Table', '')),
    )


def _handle_screen_flow(profile: ProjectProfile, content: str):
    profile.screen_flow = ScreenFlowSection(image_path=_parse_image_ref(content))


def _handle_business_process(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    after_blocks = []
    after_content = subs.get('After (Post-Introduction)') or subs.get('After', '')
    # Each `#### title` followed by body
    for m in re.finditer(r'^####\s+(.+?)\s*$\n(.*?)(?=^####\s|\Z)', after_content, re.MULTILINE | re.DOTALL):
        after_blocks.append(AfterBlock(title=m.group(1).strip(), body=m.group(2).strip()))
    profile.business_process = BusinessProcessSection(
        categories=_parse_list(subs.get('Categories', '')),
        before_steps=_parse_list(subs.get('Before (Current Process)') or subs.get('Before', '')),
        after_blocks=after_blocks,
    )


def _handle_benefits(profile: ProjectProfile, content: str):
    benefits = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        benefits.append(BenefitSection(title=m.group(1).strip(), content=m.group(2).strip()))
    profile.benefits = benefits


def _handle_approach_comparison(profile: ProjectProfile, content: str):
    profile.approach_comparison = _parse_table(content)


def _handle_assumptions(profile: ProjectProfile, content: str):
    assumptions = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        assumptions.append(AssumptionSection(label=m.group(1).strip(), content=m.group(2).strip()))
    profile.assumptions = assumptions


def _handle_infrastructure(profile: ProjectProfile, content: str):
    profile.infrastructure = _parse_table(content)


def _handle_software_stack(profile: ProjectProfile, content: str):
    profile.software_stack = _parse_table(content)


def _handle_nfr_sections(profile: ProjectProfile, content: str):
    sections = []
    for m in re.finditer(r'^###\s+(.+?)\s*$\n(.*?)(?=^###\s|\Z)', content, re.MULTILINE | re.DOTALL):
        sections.append(NFRSection(title=m.group(1).strip(), body=m.group(2).strip()))
    profile.nfr_sections = sections


def _handle_nfr_detailed(profile: ProjectProfile, content: str):
    profile.nfr_detailed = _parse_table(content)


def _handle_schedule(profile: ProjectProfile, content: str):
    subs = _split_subsections(content)
    profile.schedule = ScheduleSection(
        description=_parse_text(subs.get('Description', '')),
        image_path=_parse_image_ref(subs.get('Chart', '')),
    )
