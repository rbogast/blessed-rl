"""Biome selection menu for map preview tool."""

from typing import List
from systems.menu import BaseMenu


class BiomeSelectionMenu(BaseMenu):
    """Menu for selecting biomes in the map preview tool."""
    
    def __init__(self, world, available_biomes):
        super().__init__(world)
        self.available_biomes = available_biomes
    
    def get_title(self) -> str:
        return "--- Select Biome ---"
    
    def get_subtitle(self) -> str:
        return "↑↓: Navigate, Enter: Select, Esc: Cancel"
    
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build biome selection items."""
        return self.available_biomes
    
    def get_selected_biome(self) -> str:
        """Get the currently selected biome name."""
        if self.selected_index >= 0 and self.selected_index < len(self.available_biomes):
            return self.available_biomes[self.selected_index]
        return None
    
    def get_menu_line(self, line_num: int, player_entity: int) -> tuple:
        """Override to provide biome-specific display with highlighting."""
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
            biome_name = self._menu_items[item_line]
            is_highlighted = item_line == self.selected_index
            prefix = "> " if is_highlighted else "  "
            return f"{prefix}{biome_name}", is_highlighted
        
        return "", False
