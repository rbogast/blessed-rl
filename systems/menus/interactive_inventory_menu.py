"""Interactive inventory menu implementation."""

from typing import List
from systems.menu import BaseMenu


class InteractiveInventoryMenu(BaseMenu):
    """Menu for navigating and selecting inventory items."""
    
    def get_title(self) -> str:
        return "--- Inventory ---"
    
    def get_subtitle(self) -> str:
        return "Select item to examine:"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build list of inventory items for navigation."""
        from components.items import Inventory, Item
        from components.corpse import Corpse
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return ["No inventory"]
        
        if not inventory.items:
            return ["Inventory is empty"]
        
        # Add inventory items
        for item_entity_id in inventory.items:
            # Check if it's a regular item
            item = self.world.get_component(item_entity_id, Item)
            if item:
                name = item.name
                items.append(name)
            else:
                # Check if it's a corpse
                corpse = self.world.get_component(item_entity_id, Corpse)
                if corpse:
                    name = f"{corpse.original_entity_type} corpse"
                    items.append(name)
                else:
                    # Unknown item type
                    items.append("Unknown item")
        
        return items
    
    def get_selected_item_entity_id(self, player_entity: int) -> int:
        """Get the entity ID of the currently selected item."""
        from components.items import Inventory
        
        inventory = self.world.get_component(player_entity, Inventory)
        if not inventory or self.selected_index < 0 or self.selected_index >= len(inventory.items):
            return None
        
        return inventory.items[self.selected_index]
