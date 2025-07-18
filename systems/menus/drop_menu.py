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
        from components.corpse import Corpse
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return items
        
        # Add all items from inventory
        for item_entity_id in inventory.items:
            # Check if it's a regular item
            item = self.world.get_component(item_entity_id, Item)
            if item:
                name = item.name[:18]
                items.append(name)
            else:
                # Check if it's a corpse
                corpse = self.world.get_component(item_entity_id, Corpse)
                if corpse:
                    name = f"{corpse.original_entity_type} corpse"[:18]
                    items.append(name)
                else:
                    # Unknown item type
                    items.append("Unknown item")
        
        return items
