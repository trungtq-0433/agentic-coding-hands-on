from typing import List, Dict, Any

from lib.schemas import (
    SlideContent,
    ContentItem,
    LayoutType,
    ContentType,
    Position
)



class SpecGenerator:
    """Generate slide specifications from parsed content"""
    
    def generate(
        self,
        parsed_content: List[Dict[str, Any]]
    ) -> List[SlideContent]:
        """
        Generate slide content list from parsed markdown
        
        Args:
            parsed_content: Parsed markdown content
        
        Returns:
            List of SlideContent objects
        """
        print(f"Generating spec for {len(parsed_content)} slides")
        
        slides = []
        
        for slide_data in parsed_content:
            slide_content = self._create_slide_content(slide_data)
            slides.append(slide_content)
        
        print(f"Generated {len(slides)} slides")
        return slides
    
    def _create_slide_content(self, slide_data: Dict[str, Any]) -> SlideContent:
        """
        Create SlideContent object from parsed data
        
        Args:
            slide_data: Parsed slide data
        
        Returns:
            SlideContent object
        """
        # Map layout string to LayoutType enum
        layout = self._map_layout(slide_data.get('layout', 'content'))
        
        # Convert content items
        content_items = []
        for item in slide_data.get('content', []):
            content_item = self._create_content_item(item)
            content_items.append(content_item)
        
        # Create slide content
        slide_content = SlideContent(
            slide_number=slide_data.get('slide_number', 1),
            layout=layout,
            title=slide_data.get('title'),
            subtitle=slide_data.get('subtitle'),
            content=content_items
        )
        
        # Pass through shape_contents if exists (for shape targeting)
        if 'shape_contents' in slide_data:
            slide_content.shape_contents = slide_data['shape_contents']
            print(f"  - Passed through shape_contents: {list(slide_data['shape_contents'].keys())}")
        
        return slide_content
    
    def _create_content_item(self, item_data: Dict[str, Any]) -> ContentItem:
        """
        Create ContentItem from parsed data
        
        Args:
            item_data: Parsed content item data
        
        Returns:
            ContentItem object
        """
        # Map type string to ContentType enum
        content_type = self._map_content_type(item_data.get('type', 'text'))
        
        # Map position string to Position enum
        position = self._map_position(item_data.get('position', 'main'))
        
        return ContentItem(
            type=content_type,
            data=item_data.get('data'),
            position=position,
            style=item_data.get('style')
        )
    
    def _map_layout(self, layout_str: str) -> LayoutType:
        """Map layout string to LayoutType enum"""
        layout_map = {
            'title': LayoutType.TITLE,
            'section_header': LayoutType.SECTION_HEADER,
            'content': LayoutType.CONTENT,
            'two_column': LayoutType.TWO_COLUMN,
            'image': LayoutType.IMAGE,
            'table': LayoutType.TABLE,
        }
        return layout_map.get(layout_str.lower(), LayoutType.CONTENT)
    
    def _map_content_type(self, type_str: str) -> ContentType:
        """Map content type string to ContentType enum"""
        type_map = {
            'text': ContentType.TEXT,
            'list': ContentType.LIST,
            'table': ContentType.TABLE,
            'image': ContentType.IMAGE,
            'code': ContentType.CODE,
        }
        return type_map.get(type_str.lower(), ContentType.TEXT)
    
    def _map_position(self, position_str: str) -> Position:
        """Map position string to Position enum"""
        position_map = {
            'main': Position.MAIN,
            'left': Position.LEFT,
            'right': Position.RIGHT,
            'full': Position.FULL,
        }
        return position_map.get(position_str.lower(), Position.MAIN)
