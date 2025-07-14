"""Use item menu implementation."""

from typing import List
from systems.menu import BaseMenu


class UseMenu(BaseMenu):
    """Menu for using consumable items."""
    
    def get_title(self) -> str:
        return "--- Use Item ---"
    
    def get_subtitle(self) -> str:
        return "Select item number:"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build list of usable items."""
        from components.items import Inventory, Item, Consumable
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return items
        
        # Add consumable items from inventory
        for item_entity_id in inventory.items:
            consumable = self.world.get_component(item_entity_id, Consumable)
            if consumable:
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    name = item.name[:16]
                    uses_text = f"({consumable.uses})" if consumable.uses > 1 else ""
                    items.append(f"{name} {uses_text}")
        
        return items
