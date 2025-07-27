"""Template selection menu for map preview tool."""

from typing import List
from systems.menu import BaseMenu


class TemplateSelectionMenu(BaseMenu):
    """Menu for selecting templates in the map preview tool."""
    
    def __init__(self, world, available_templates):
        super().__init__(world)
        self.available_templates = available_templates
    
    def get_title(self) -> str:
        return "--- Select map template ---"
    
    def get_subtitle(self) -> str:
        return ""
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build template selection items."""
        return self.available_templates
    
    def get_selected_template(self) -> str:
        """Get the currently selected template name."""
        if self.selected_index >= 0 and self.selected_index < len(self.available_templates):
            return self.available_templates[self.selected_index]
        return None
    
    def get_menu_line(self, line_num: int, player_entity: int) -> tuple:
        """Override to provide template-specific display with highlighting."""
        if line_num == 0:
            return self.get_title(), False
        elif line_num == 1:
            return self.get_subtitle(), False
        
        # Build menu items if needed
        if self._items_dirty:
            self._menu_items = self.build_menu_items(player_entity)
            self._items_dirty = False
        
        item_line = line_num - 2
        if item_line >= 0 and item_line < len(self._menu_items):
            template_name = self._menu_items[item_line]
            is_highlighted = item_line == self.selected_index
            prefix = "> " if is_highlighted else "  "
            return f"{prefix}{template_name}", is_highlighted
        
        return "", False
