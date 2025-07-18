"""Throwing menu implementation."""

from typing import List
from systems.menu import BaseMenu


class ThrowingMenu(BaseMenu):
    """Menu for selecting items to throw."""
    
    def get_title(self) -> str:
        return "--- Throw Item ---"
    
    def get_subtitle(self) -> str:
        return "Select item to throw:"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build list of throwable items."""
        from components.items import Inventory, Item, Throwable
        from components.corpse import Corpse
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return items
        
        # Add throwable items from inventory
        for item_entity_id in inventory.items:
            # Check if item has throwable component or physics component
            throwable = self.world.get_component(item_entity_id, Throwable)
            from components.effects import Physics
            physics = self.world.get_component(item_entity_id, Physics)
            
            # Items are throwable if they have Throwable component or Physics component
            if throwable or physics:
                item = self.world.get_component(item_entity_id, Item)
                if item:
                    name = item.name[:16]
                    weight_info = ""
                    if throwable:
                        weight_info = f" ({throwable.weight:.1f}lbs)"
                    elif physics:
                        weight_info = f" ({physics.mass:.1f}lbs)"
                    items.append(f"{name}{weight_info}")
                else:
                    # Check if it's a corpse
                    corpse = self.world.get_component(item_entity_id, Corpse)
                    if corpse:
                        name = f"{corpse.original_entity_type} corpse"[:16]
                        weight_info = ""
                        if physics:
                            weight_info = f" ({physics.mass:.1f}lbs)"
                        items.append(f"{name}{weight_info}")
        
        if not items:
            items.append("No throwable items")
        
        return items
    
    def get_throwable_items(self, player_entity: int) -> List[int]:
        """Get list of throwable item entity IDs."""
        from components.items import Inventory, Throwable
        from components.effects import Physics
        
        throwable_items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            return throwable_items
        
        for item_entity_id in inventory.items:
            # Items are throwable if they have Throwable component or Physics component
            throwable = self.world.get_component(item_entity_id, Throwable)
            physics = self.world.get_component(item_entity_id, Physics)
            
            if throwable or physics:
                throwable_items.append(item_entity_id)
        
        return throwable_items
