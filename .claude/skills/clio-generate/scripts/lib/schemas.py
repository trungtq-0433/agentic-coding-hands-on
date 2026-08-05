from __future__ import annotations

from dataclasses import field
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class LayoutType(str, Enum):
    TITLE = 'title'
    SECTION_HEADER = 'section_header'
    CONTENT = 'content'
    TWO_COLUMN = 'two_column'
    IMAGE = 'image'
    TABLE = 'table'


class ContentType(str, Enum):
    TEXT = 'text'
    LIST = 'list'
    TABLE = 'table'
    IMAGE = 'image'
    CODE = 'code'


class Position(str, Enum):
    MAIN = 'main'
    LEFT = 'left'
    RIGHT = 'right'
    FULL = 'full'


class ContentItem:
    def __init__(
        self,
        type: ContentType,
        data: Any,
        position: Position = Position.MAIN,
        style: Optional[Dict[str, Any]] = None,
    ):
        self.type = type
        self.data = data
        self.position = position
        self.style = style


class SlideContent:
    def __init__(
        self,
        slide_number: int,
        layout: LayoutType,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: Optional[List[ContentItem]] = None,
        shape_contents: Optional[Dict[str, str]] = None,
    ):
        self.slide_number = slide_number
        self.layout = layout
        self.title = title
        self.subtitle = subtitle
        self.content = content if content is not None else []
        self.shape_contents = shape_contents
