"""Canonical ProjectProfile dataclass — the contract between gen-md and gen-slide.

The profile is domain-organized (not slide-organized). Each section maps to
one `## Heading` in the project_profile markdown.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Compound sub-blocks
# ---------------------------------------------------------------------------

@dataclass
class AfterBlock:
    """One business_process 'after' block: category benefit title + body."""
    title: str = ''
    body: str = ''


@dataclass
class BenefitSection:
    """One benefit (title + multi-line content). Slides 12+13 fill 2 each."""
    title: str = ''
    content: str = ''


@dataclass
class AssumptionSection:
    """One assumption row: label (fixed in template) + content (filled)."""
    label: str = ''
    content: str = ''


@dataclass
class NFRSection:
    """One non-functional requirement section: title + body (5 bullets)."""
    title: str = ''
    body: str = ''


# ---------------------------------------------------------------------------
# Top-level section wrappers (for sections with multiple subfields)
# ---------------------------------------------------------------------------

@dataclass
class BackgroundSection:
    current_issues: str = ''
    objectives: str = ''


@dataclass
class FeaturesSection:
    description: str = ''
    table: list[dict] = field(default_factory=list)


@dataclass
class NFROverviewSection:
    description: str = ''
    table: list[dict] = field(default_factory=list)


@dataclass
class ScreenFlowSection:
    image_path: str = ''


@dataclass
class BusinessProcessSection:
    categories: list[str] = field(default_factory=list)
    before_steps: list[str] = field(default_factory=list)
    after_blocks: list[AfterBlock] = field(default_factory=list)


@dataclass
class ScheduleSection:
    description: str = ''
    image_path: str = ''


# ---------------------------------------------------------------------------
# Root ProjectProfile
# ---------------------------------------------------------------------------

@dataclass
class ProjectProfile:
    """Root project profile, organized by business domain."""
    project_id: str = ''
    timestamp: str = ''

    project_background: BackgroundSection = field(default_factory=BackgroundSection)
    features: FeaturesSection = field(default_factory=FeaturesSection)
    nfr_overview: NFROverviewSection = field(default_factory=NFROverviewSection)
    screen_flow: ScreenFlowSection = field(default_factory=ScreenFlowSection)
    business_process: BusinessProcessSection = field(default_factory=BusinessProcessSection)

    # Variable-length collections (no fixed structure beyond sub-block)
    benefits: list[BenefitSection] = field(default_factory=list)
    approach_comparison: list[dict] = field(default_factory=list)
    assumptions: list[AssumptionSection] = field(default_factory=list)
    infrastructure: list[dict] = field(default_factory=list)
    software_stack: list[dict] = field(default_factory=list)
    nfr_sections: list[NFRSection] = field(default_factory=list)
    nfr_detailed: list[dict] = field(default_factory=list)

    schedule: ScheduleSection = field(default_factory=ScheduleSection)

    # Parser-internal: order in which `##` section headings were first seen in
    # the source markdown. NOT part of the agent-authored JSON contract — it is
    # derived by `parse_profile` and excluded from `to_dict`/`from_dict`.
    section_order: list[str] = field(default_factory=list)

    # Parser-internal: extra-slide entries auto-routed by
    # `extra_slide_classifier` for `##` headings that didn't match any known
    # section (hand-written markdown with its own heading vocabulary). Same
    # shape as --extra-slides JSON entries. Excluded from `to_dict`/`from_dict`.
    auto_extra_slides: list[dict] = field(default_factory=list)

    @classmethod
    def empty(cls, project_id: str = '', timestamp: str = '') -> 'ProjectProfile':
        """Factory returning an instance with all fields defaulted."""
        return cls(project_id=project_id, timestamp=timestamp)

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectProfile':
        """Build a ProjectProfile from a plain dict (e.g. JSON input from agent).

        Tolerant: unknown keys ignored, missing keys use defaults.
        """
        def _section(cls_, payload):
            if not isinstance(payload, dict):
                return cls_()
            valid = {f for f in cls_.__dataclass_fields__}
            return cls_(**{k: v for k, v in payload.items() if k in valid})

        def _list_of(cls_, payload):
            if not isinstance(payload, list):
                return []
            return [_section(cls_, item) for item in payload]

        return cls(
            project_id=data.get('project_id', ''),
            timestamp=data.get('timestamp', ''),
            project_background=_section(BackgroundSection, data.get('project_background')),
            features=_section(FeaturesSection, data.get('features')),
            nfr_overview=_section(NFROverviewSection, data.get('nfr_overview')),
            screen_flow=_section(ScreenFlowSection, data.get('screen_flow')),
            business_process=BusinessProcessSection(
                categories=data.get('business_process', {}).get('categories', []) or [],
                before_steps=data.get('business_process', {}).get('before_steps', []) or [],
                after_blocks=_list_of(AfterBlock, data.get('business_process', {}).get('after_blocks')),
            ),
            benefits=_list_of(BenefitSection, data.get('benefits')),
            approach_comparison=data.get('approach_comparison', []) or [],
            assumptions=_list_of(AssumptionSection, data.get('assumptions')),
            infrastructure=data.get('infrastructure', []) or [],
            software_stack=data.get('software_stack', []) or [],
            nfr_sections=_list_of(NFRSection, data.get('nfr_sections')),
            nfr_detailed=data.get('nfr_detailed', []) or [],
            schedule=_section(ScheduleSection, data.get('schedule')),
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict (round-trippable through from_dict).

        `section_order` and `auto_extra_slides` are parser-internal (derived
        from source markdown), not part of the agent-authored JSON contract,
        so they're excluded here.
        """
        d = asdict(self)
        d.pop('section_order', None)
        d.pop('auto_extra_slides', None)
        return d


# ---------------------------------------------------------------------------
# Section content predicates — single source of truth for "does this section
# have content", shared by gen-md (`_emit_*` guards) and the renderer's
# prune+reorder pass so the two can never diverge.
# ---------------------------------------------------------------------------

_SECTION_CONTENT_CHECKS = {
    'project_background': lambda p: bool(p.project_background.current_issues or p.project_background.objectives),
    'features':           lambda p: bool(p.features.description or p.features.table),
    'nfr_overview':       lambda p: bool(p.nfr_overview.description or p.nfr_overview.table),
    'screen_flow':        lambda p: bool(p.screen_flow.image_path),
    'business_process':   lambda p: bool(p.business_process.categories or p.business_process.before_steps or p.business_process.after_blocks),
    'benefits':           lambda p: bool(p.benefits),
    'approach_comparison': lambda p: bool(p.approach_comparison),
    'assumptions':        lambda p: bool(p.assumptions),
    'infrastructure':     lambda p: bool(p.infrastructure),
    'software_stack':     lambda p: bool(p.software_stack),
    'nfr_sections':       lambda p: bool(p.nfr_sections),
    'nfr_detailed':       lambda p: bool(p.nfr_detailed),
    'schedule':           lambda p: bool(p.schedule.description or p.schedule.image_path),
}


def section_has_content(profile: 'ProjectProfile', key: str) -> bool:
    """Return True if `profile`'s section `key` has content worth rendering.

    `key` must be one of `SECTION_TO_SLIDES`'s keys (== ProjectProfile field
    names). Unknown keys are treated as empty (False) rather than raising, so
    callers iterating over an untrusted/older `section_order` stay safe.
    """
    check = _SECTION_CONTENT_CHECKS.get(key)
    return bool(check(profile)) if check else False
