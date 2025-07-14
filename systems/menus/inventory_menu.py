"""Inventory menu implementation."""

from typing import List
from systems.menu import BaseMenu


class InventoryMenu(BaseMenu):
    """Menu for displaying inventory items (non-navigable display)."""
    
    def get_title(self) -> str:
        return "--- Inventory ---"
    
    def get_subtitle(self) -> str:
        return "[E]quip [U]se [I]nv"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build inventory display items."""
        from components.items import Inventory, Item
        
        items = []
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not inventory:
            items.append("No inventory")
            return items
        
        # Add capacity info
        items.append(f"Items: {len(inventory.items)}/{inventory.capacity}")
        
        # Add inventory items
        for i, item_entity_id in enumerate(inventory.items):
            item = self.world.get_component(item_entity_id, Item)
            if item:
                name = item.name[:18]
                items.append(f"{i + 1:2d}. {name}")
        
        return items
    
    def get_menu_line(self, line_num: int, player_entity: int) -> tuple:
        """Override to provide inventory-specific display without highlighting."""
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
            return self._menu_items[item_line], False
        
        return "", False
