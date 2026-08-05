from __future__ import annotations

import re
from typing import Any
from typing import Dict
from typing import List




class MarkdownParser:
    """Parser for FILL_SLIDE markers - fill content into existing template slides"""

    def __init__(self):
        # FILL_SLIDE marker for filling existing slides
        self.fill_marker_pattern = re.compile(
            r'<!--\s*FILL_SLIDE:\s*(\d+)(?:,\s*LAYOUT:\s*(\w+))?\s*-->',
        )
        # SHAPE marker for targeting specific shapes
        self.shape_marker_pattern = re.compile(
            r'<!--\s*SHAPE:\s*(\w+)\s*-->',
        )
        # Optional END SHAPE marker (used only in authoring; must NOT appear in final content)
        # Example: <!-- END SHAPE -->
        self.end_shape_pattern = re.compile(
            r'<!--\s*END SHAPE\s*-->',
        )
        self.image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        self.table_pattern = re.compile(r'^\|(.+)\|$')

    def parse_text(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse markdown text with FILL_SLIDE markers

        Args:
            content: Raw markdown text (may contain escape sequences like \\n from JSON)

        Returns:
            {
                'fill_slides': [list of slides to fill into existing]
            }
        """
        # Normalize line endings: convert \r\n (Windows) and \r (old Mac) to \n (Unix)
        # This ensures consistent parsing regardless of source format
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        fill_slides = []

        # Find all FILL_SLIDE markers
        all_markers = []
        for match in self.fill_marker_pattern.finditer(content):
            all_markers.append({
                'pos': match.start(),
                'slide_num': int(match.group(1)),
                'layout': match.group(2) or 'content',
                'end': match.end(),
            })

        # Sort by position
        all_markers.sort(key=lambda x: x['pos'])

        # Process each marker
        for i, marker in enumerate(all_markers):
            # Get content until next marker or end
            start = marker['end']
            end = all_markers[i + 1]['pos'] if i + 1 < len(all_markers) else len(content)
            slide_content = content[start:end].strip()

            if slide_content:
                # Parse content (automatically detects SHAPE markers)
                slide_data = self._parse_slide_content(slide_content, marker['layout'])
                slide_data['slide_number'] = marker['slide_num']
                slide_data['layout'] = marker['layout']
                fill_slides.append(slide_data)

        return {
            'fill_slides': fill_slides,
        }

    def _parse_slide_content(self, content: str, layout: str) -> Dict[str, Any]:
        """
        Parse content of a single slide

        Automatically detects and handles SHAPE markers:
            <!-- SHAPE: current_issues -->
            Content for current issues...

            <!-- SHAPE: objectives -->
            Content for objectives...

        Returns:
            {
                'title': ...,
                'subtitle': ...,
                'content': [...],              # Regular content items
                'shape_contents': {...}         # Dict of shape_key → content (if SHAPE markers found)
            }
        """
        # Check if content has SHAPE markers
        shape_markers = list(self.shape_marker_pattern.finditer(content))

        if shape_markers:
            # Parse with SHAPE markers
            return self._parse_with_shape_markers(content, layout, shape_markers)

        # Regular parsing (no SHAPE markers)
        lines = content.split('\n')

        title = None
        subtitle = None
        content_items: list[dict[str, Any]] = []
        current_list: list[str] = []
        current_table: list[str] = []

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                if current_list:
                    content_items.append({
                        'type': 'list',
                        'data': current_list,
                        'position': self._detect_position(layout, len(content_items)),
                    })
                    current_list = []
                if current_table:
                    content_items.append({
                        'type': 'table',
                        'data': self._parse_table(current_table),
                        'position': 'main',
                    })
                    current_table = []
                continue

            # Title (H1)
            if line.startswith('# '):
                title = line[2:].strip()

            # Subtitle or section (H2)
            elif line.startswith('## '):
                section_title = line[3:].strip()
                if not title:
                    title = section_title
                else:
                    subtitle = section_title

            # List items
            elif line.startswith('- ') or line.startswith('* '):
                item = line[2:].strip()
                current_list.append(item)

            # Images
            elif '![' in line:
                img_match = self.image_pattern.search(line)
                if img_match:
                    caption = img_match.group(1)
                    path = img_match.group(2)

                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('*'):
                        caption = lines[i + 1].strip().strip('*')

                    content_items.append({
                        'type': 'image',
                        'data': {
                            'path': path,
                            'caption': caption if caption else None,
                        },
                        'position': self._detect_position(layout, len(content_items)),
                    })

            # Tables
            elif '|' in line:
                current_table.append(line)

            # Regular text
            elif line and not line.startswith('#'):
                if line.startswith('*') and line.endswith('*'):
                    continue

                content_items.append({
                    'type': 'text',
                    'data': line,
                    'position': self._detect_position(layout, len(content_items)),
                })

        # Finalize remaining content
        if current_list:
            content_items.append({
                'type': 'list',
                'data': current_list,
                'position': self._detect_position(layout, len(content_items)),
            })

        if current_table:
            content_items.append({
                'type': 'table',
                'data': self._parse_table(current_table),
                'position': 'main',
            })

        return {
            'title': title,
            'subtitle': subtitle,
            'content': content_items,
        }

    def _parse_table(self, table_lines: List[str]) -> Dict[str, Any]:
        """Parse markdown table"""
        if len(table_lines) < 2:
            return {'headers': [], 'rows': []}

        headers = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

        rows = []
        for line in table_lines[2:]:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells:
                rows.append(cells)

        return {
            'headers': headers,
            'rows': rows,
        }

    def _detect_position(self, layout: str, content_index: int) -> str:
        """Detect content position based on layout"""
        if layout == 'two_column':
            return 'left' if content_index % 2 == 0 else 'right'
        else:
            return 'main'

    def _parse_with_shape_markers(self, content: str, layout: str, shape_markers: List) -> Dict[str, Any]:
        """
        Parse slide content that contains SHAPE markers

        Example:
            <!-- SHAPE: current_issues -->
            Content for current issues...

            <!-- SHAPE: objectives -->
            Content for objectives...

        Returns:
            {
                'title': ...,
                'subtitle': ...,
                'content': [],
                'shape_contents': {
                    'current_issues': 'Content for current issues...',
                    'objectives': 'Content for objectives...'
                }
            }
        """
        result: dict[str, Any] = {
            'title': None,
            'subtitle': None,
            'content': [],
            'shape_contents': {},  # Map of shape_key → content
        }

        # Extract title (before first SHAPE marker)
        first_marker_pos = shape_markers[0].start()
        pre_content = content[:first_marker_pos].strip()

        if pre_content:
            lines = pre_content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('# '):
                    result['title'] = line[2:].strip()
                elif line.startswith('## '):
                    result['subtitle'] = line[3:].strip()

        # Parse each SHAPE section
        for i, marker in enumerate(shape_markers):
            shape_key = marker.group(1)  # Extract key (e.g., 'current_issues')

            # Get content for this shape
            start = marker.end()
            end = shape_markers[i + 1].start() if i + 1 < len(shape_markers) else len(content)
            shape_content = content[start:end].strip()

            # Strip optional END SHAPE marker from within this shape block.
            # Many authoring prompts append <!-- END SHAPE --> after each section
            # for validation, but this marker should never be rendered into PPTX.
            if shape_content:
                end_match = self.end_shape_pattern.search(shape_content)
                if end_match:
                    # Keep everything before the END SHAPE marker
                    shape_content = shape_content[:end_match.start()].rstrip()

            if shape_content:
                result['shape_contents'][shape_key] = shape_content
                print(f"  - Found SHAPE '{shape_key}': {len(shape_content)} chars")

        return result
