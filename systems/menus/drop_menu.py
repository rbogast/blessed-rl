"""Drop item menu implementation."""

from typing import List
from systems.menu import BaseMenu


class DropMenu(BaseMenu):
    """Menu for dropping items from inventory."""
    
    def get_title(self) -> str:
        return "--- Drop Item ---"
    
    def get_subtitle(self) -> str:
        return "Select item number:"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build list of droppable items."""
        from components.items import Inventory, Item
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return items
        
        # Add all items from inventory
        for item_entity_id in inventory.items:
            item = self.world.get_component(item_entity_id, Item)
            if item:
                name = item.name[:18]
                items.append(name)
        
        return items
