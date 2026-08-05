"""Base template classes — role-based descriptors for dynamic slide rendering.

A SlideRoleConfig declares ROLES (semantic shape groups), not specific shapes.
The renderer combines this with a ShapeDiscovery engine to locate the right
shapes at render time, so the same template can absorb varying amounts of
content without per-shape hardcoding.

Legacy ShapeTarget / SlideConfig kept for backward compatibility with the
old MarkdownParser → SpecGenerator → PPTXRenderer pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# New role-based descriptors (Phase 02)
# ---------------------------------------------------------------------------

class ShapeFindStrategy(str, Enum):
    """How the renderer should locate the shape(s) for a given role."""
    BY_INDEX = 'by_index'              # direct slide.shapes[i] lookup
    BY_NAME = 'by_name'                # recursive name search (handles groups)
    BY_GROUP_CHILDREN = 'by_group'     # iterate children of a named group
    BY_POSITION = 'by_position'        # filter by shape_type, sort by axis


class ContentKind(str, Enum):
    """What kind of content the role's shape(s) accept."""
    TEXT = 'text'
    TABLE = 'table'
    IMAGE = 'image'


@dataclass
class ShapeRole:
    """Semantic descriptor for one or more shapes that share a role.

    Examples:
      ShapeRole(name='before_steps', cardinality=8, kind=TEXT, source_path='business_process.before_steps',
                find_strategy=BY_NAME, find_params={'names': ['Google Shape;529;p78', ...]})

      ShapeRole(name='after_blocks', cardinality=4, kind=TEXT, source_path='business_process.after_blocks',
                sub_roles=[
                    ShapeRole(name='title', cardinality=1, kind=TEXT, source_path='title',
                              find_strategy=BY_NAME, find_params={'names': [...]}),
                    ShapeRole(name='body',  cardinality=1, kind=TEXT, source_path='body',
                              find_strategy=BY_NAME, find_params={'names': [...]}),
                ])
    """
    name: str
    cardinality: int                       # 1 for single, N for variable-length collections
    kind: ContentKind = ContentKind.TEXT
    source_path: str = ''                  # dot-notation into ProjectProfile (supports [start:end] slice)
    find_strategy: ShapeFindStrategy = ShapeFindStrategy.BY_INDEX
    find_params: dict = field(default_factory=dict)
    sub_roles: Optional[List['ShapeRole']] = None  # for compound roles like title+body pairs
    fill_cols: Optional[List[int]] = None  # table-only: restrict writes to specific columns
    fit_to_slide: bool = False             # image-only: scale image to fill slide content area
    description: Optional[str] = None


@dataclass
class SlideRoleConfig:
    """Role-based config for a single slide."""
    slide_number: int
    roles: List[ShapeRole] = field(default_factory=list)
    content_types: List[str] = field(default_factory=lambda: ['text'])
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Legacy shape-target config (kept for the old generate_pptx.py pipeline)
# ---------------------------------------------------------------------------

@dataclass
class ShapeTarget:
    """Legacy: target a specific shape for content filling."""
    shape_name: Optional[str] = None
    shape_index: Optional[int] = None
    content_key: Optional[str] = None
    placeholder: bool = False
    description: Optional[str] = None
    fill_cols: Optional[List[int]] = None


@dataclass
class SlideConfig:
    """Legacy: per-shape config used by old renderer path."""
    slide_number: int
    layout_type: str
    content_types: Optional[List[str]] = None
    max_items: Optional[int] = None
    shape_targets: Optional[List[ShapeTarget]] = None
    placeholder_count: int = 0
    has_title: bool = False
    has_subtitle: bool = False
    custom_handler: Optional[Callable] = None
    protected: bool = False
    description: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if self.content_types is None:
            self.content_types = ['text', 'list']
        if self.shape_targets is None:
            self.shape_targets = []


# ---------------------------------------------------------------------------
# Base template class
# ---------------------------------------------------------------------------

class BaseSlideTemplate(ABC):
    """Base for template-specific configurations.

    Subclasses populate `slide_role_configs` (new) and optionally
    `slide_configs` (legacy) for the 17+ slides they manage.
    """

    def __init__(self):
        self.slide_role_configs: Dict[int, SlideRoleConfig] = {}
        self.slide_configs: Dict[int, SlideConfig] = {}  # legacy
        self.protected_slides: List[int] = []
        self._initialize_configs()

    @abstractmethod
    def _initialize_configs(self):
        """Populate slide_role_configs and (optionally) slide_configs."""
        pass

    def get_slide_role_config(self, slide_number: int) -> Optional[SlideRoleConfig]:
        """Get role-based config for a slide (None if not configured)."""
        return self.slide_role_configs.get(slide_number)

    def get_slide_config(self, slide_number: int) -> Optional[SlideConfig]:
        """Legacy accessor — returns None or a default if not explicitly set."""
        return self.slide_configs.get(slide_number, self._default_config(slide_number))

    def should_fill_slide(self, slide_number: int) -> bool:
        return slide_number not in self.protected_slides

    def configured_slide_numbers(self) -> List[int]:
        return sorted(self.slide_role_configs.keys())

    def _default_config(self, slide_number: int) -> SlideConfig:
        return SlideConfig(
            slide_number=slide_number,
            layout_type='content',
            content_types=['text', 'list', 'table', 'image'],
            description='Default config',
        )
