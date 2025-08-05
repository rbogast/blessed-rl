"""
Examine menu for displaying examination results.
"""

from systems.menu import BaseMenu
from components.examine import ExamineCursor
from typing import List


class ExamineMenu(BaseMenu):
    """Menu for displaying examine mode results."""
    
    def __init__(self, world, examine_system):
        super().__init__(world)
        self.examine_system = examine_system
        self.entities_at_cursor = []
        self.selected_entity_id = None
        self.show_entity_list = True
    
    def get_title(self) -> str:
        """Get the menu title."""
        return "You see:"
    
    def get_subtitle(self) -> str:
        """Get the menu subtitle."""
        return ""
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build the list of menu items for examination."""
        cursor = self.world.get_component(player_entity, ExamineCursor)
        if not cursor:
            return ["Nothing to examine"]
        
        # Get entities at cursor position
        self.entities_at_cursor = self.examine_system.get_entities_at_cursor(player_entity)
        
        if not self.entities_at_cursor:
            # No entities, show terrain description
            terrain_desc = self.examine_system.get_terrain_description(cursor.cursor_x, cursor.cursor_y)
            return [terrain_desc]
        
        if self.selected_entity_id is not None and not self.show_entity_list:
            # Show detailed description of selected entity
            description = self.examine_system.get_entity_description(self.selected_entity_id)
            return description.split('\n')  # Split multi-line descriptions
        
        if len(self.entities_at_cursor) == 1:
            # Single entity, show detailed description
            entity_id = self.entities_at_cursor[0]
            description = self.examine_system.get_entity_description(entity_id)
            return description.split('\n')
        
        # Multiple entities, show list
        items = []
        for entity_id in self.entities_at_cursor:
            description = self.examine_system.get_entity_description(entity_id)
            # Use first line of description for list
            first_line = description.split('\n')[0]
            items.append(first_line)
        
        return items
    
    def select_entity(self, index: int) -> bool:
        """Select an entity from the list for detailed examination."""
        if 0 <= index < len(self.entities_at_cursor):
            self.selected_entity_id = self.entities_at_cursor[index]
            self.show_entity_list = False
            self.invalidate()  # Force menu rebuild
            return True
        return False
    
    def return_to_list(self) -> None:
        """Return to the entity list view."""
        self.selected_entity_id = None
        self.show_entity_list = True
        self.invalidate()  # Force menu rebuild
    
    def reset(self) -> None:
        """Reset menu state."""
        super().reset()
        self.selected_entity_id = None
        self.show_entity_list = True
        self.entities_at_cursor = []
    
    def can_select_items(self) -> bool:
        """Check if there are multiple items that can be selected."""
        return len(self.entities_at_cursor) > 1 and self.show_entity_list
    
    def is_showing_detail(self) -> bool:
        """Check if currently showing detailed view of an entity."""
        return self.selected_entity_id is not None and not self.show_entity_list
