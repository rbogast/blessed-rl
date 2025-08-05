"""
Base menu system for handling menu display and navigation.
Provides common functionality for all menu types with highlighting support.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional


class BaseMenu(ABC):
    """Base class for all menu types with navigation and highlighting support."""
    
    def __init__(self, world):
        self.world = world
        self.selected_index = -1  # -1 means no item highlighted
        self.navigation_mode = False
        self._menu_items = []
        self._items_dirty = True
    
    @abstractmethod
    def get_title(self) -> str:
        """Get the menu title."""
        pass
    
    @abstractmethod
    def get_subtitle(self) -> str:
        """Get the menu subtitle."""
        pass
    
    @abstractmethod
    def build_menu_items(self, player_entity: int) -> List[str]:
        """Build the list of menu items for the given player."""
        pass
    
    def get_menu_line(self, line_num: int, player_entity: int) -> Tuple[str, bool]:
        """Get a menu line with highlighting information."""
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
            item_info = self._menu_items[item_line]
            line_text = f"{item_line + 1}) {item_info}"
            is_highlighted = item_line == self.selected_index
            return line_text, is_highlighted
        
        return "", False
    
    def navigate_up(self) -> None:
        """Navigate up in the menu."""
        if self._items_dirty:
            return
        
        if not self._menu_items:
            return
        
        if self.selected_index == -1:
            # First navigation - select first item
            self.selected_index = 0
        else:
            # Move up, wrap to bottom if at top
            self.selected_index = (self.selected_index - 1) % len(self._menu_items)
        
        self.navigation_mode = True
    
    def navigate_down(self) -> None:
        """Navigate down in the menu."""
        if self._items_dirty:
            return
        
        if not self._menu_items:
            return
        
        if self.selected_index == -1:
            # First navigation - select first item
            self.selected_index = 0
        else:
            # Move down, wrap to top if at bottom
            self.selected_index = (self.selected_index + 1) % len(self._menu_items)
        
        self.navigation_mode = True
    
    def get_selected_item_number(self) -> int:
        """Get the currently selected item number (1-based) or -1 if none."""
        if self.selected_index == -1:
            return -1
        return self.selected_index + 1
    
    def reset(self) -> None:
        """Reset menu state."""
        self.selected_index = 0
        self.navigation_mode = True
        self._items_dirty = True
    
    def invalidate(self) -> None:
        """Mark menu items as dirty for rebuilding."""
        self._items_dirty = True


class MenuManager:
    """Manages different menu types and their state."""
    
    def __init__(self, world):
        self.world = world
        self.active_menu = None
        self.show_inventory = False
        
        # Import menu types here to avoid circular imports
        from systems.menus.inventory_menu import InventoryMenu
        from systems.menus.equip_menu import EquipMenu
        from systems.menus.use_menu import UseMenu
        from systems.menus.drop_menu import DropMenu
        from systems.menus.throwing_menu import ThrowingMenu
        
        self.menus = {
            'inventory': InventoryMenu(world),
            'equip': EquipMenu(world),
            'use': UseMenu(world),
            'drop': DropMenu(world),
            'throwing': ThrowingMenu(world)
        }
        
        # Examine menu will be set later when examine system is available
        self.examine_menu = None
    
    def show_menu(self, menu_type: str) -> None:
        """Show a specific menu type."""
        if menu_type in self.menus:
            self.active_menu = self.menus[menu_type]
            self.active_menu.reset()
            self.show_inventory = False
    
    def show_inventory_display(self) -> None:
        """Show the inventory display (not a navigable menu)."""
        self.active_menu = None
        self.show_inventory = True
    
    def show_examine_menu(self) -> None:
        """Show the examine menu."""
        if self.examine_menu:
            self.active_menu = self.examine_menu
            self.active_menu.reset()
            self.show_inventory = False
    
    def hide_all(self) -> None:
        """Hide all menus and return to messages."""
        self.active_menu = None
        self.show_inventory = False
    
    def set_examine_menu(self, examine_menu) -> None:
        """Set the examine menu instance."""
        self.examine_menu = examine_menu
    
    def is_examine_active(self) -> bool:
        """Check if examine menu is currently active."""
        return self.active_menu is self.examine_menu and self.examine_menu is not None
    
    def is_menu_active(self) -> bool:
        """Check if any navigable menu is active."""
        return self.active_menu is not None
    
    def is_inventory_shown(self) -> bool:
        """Check if inventory display is shown."""
        return self.show_inventory
    
    def navigate_up(self) -> None:
        """Navigate up in the current menu."""
        if self.active_menu:
            self.active_menu.navigate_up()
    
    def navigate_down(self) -> None:
        """Navigate down in the current menu."""
        if self.active_menu:
            self.active_menu.navigate_down()
    
    def get_selected_item_number(self) -> int:
        """Get the currently selected item number or -1 if none."""
        if self.active_menu:
            return self.active_menu.get_selected_item_number()
        return -1
    
    def get_menu_line(self, line_num: int, player_entity: int) -> Tuple[str, bool]:
        """Get a menu line with highlighting information."""
        if self.active_menu:
            return self.active_menu.get_menu_line(line_num, player_entity)
        elif self.show_inventory:
            return self.menus['inventory'].get_menu_line(line_num, player_entity)
        return "", False
