"""
Clean menu state management system to fix navigation inconsistencies.
"""

from enum import Enum
from typing import Optional, List


class MenuState(Enum):
    """Menu states for the state machine."""
    CLOSED = "closed"
    INVENTORY_DISPLAY = "inventory_display"
    EQUIP_MENU = "equip_menu"
    USE_MENU = "use_menu"
    DROP_MENU = "drop_menu"
    THROWING_MENU = "throwing_menu"
    INTERACTIVE_INVENTORY = "interactive_inventory"
    ITEM_EXAMINATION = "item_examination"
    EXAMINE_MODE = "examine_mode"


class MenuStateMachine:
    """Clean state machine for menu navigation and input handling."""
    
    def __init__(self):
        self.state = MenuState.CLOSED
        self.selected_index = 0
        self.menu_items = []
        self.direct_selection_enabled = True
        self.navigation_active = False
        
        # Context data for specific menu states
        self.context = {}
    
    def transition_to(self, new_state: MenuState, context: dict = None) -> None:
        """Transition to a new menu state."""
        self.state = new_state
        self.selected_index = 0
        self.navigation_active = False
        self.direct_selection_enabled = True
        self.context = context or {}
        
        # State-specific initialization
        if new_state == MenuState.CLOSED:
            self.menu_items = []
        elif new_state == MenuState.INVENTORY_DISPLAY:
            self.direct_selection_enabled = False  # Inventory display is read-only
    
    def handle_input(self, key: str) -> Optional[dict]:
        """
        Handle input for the current menu state.
        Returns action dict if an action should be taken, None otherwise.
        """
        if self.state == MenuState.CLOSED:
            return None
        
        # Handle navigation keys
        if key in ['8', 'KEY_UP']:  # Up
            return self._navigate_up()
        elif key in ['2', 'KEY_DOWN']:  # Down
            return self._navigate_down()
        elif key == 'KEY_ENTER':  # Enter
            return self._confirm_selection()
        elif key == 'KEY_ESCAPE':  # Escape
            return {'action': 'close_menu'}
        elif key.isdigit() and self.direct_selection_enabled:
            # Direct number selection
            item_number = int(key)
            if 1 <= item_number <= len(self.menu_items):
                return {'action': 'select_item', 'item_number': item_number}
            else:
                return {'action': 'invalid_selection'}
        
        return None
    
    def _navigate_up(self) -> dict:
        """Navigate up in the menu."""
        if not self.menu_items:
            return {'action': 'no_items'}
        
        self.navigation_active = True
        self.selected_index = (self.selected_index - 1) % len(self.menu_items)
        return {'action': 'navigate', 'direction': 'up', 'selected_index': self.selected_index}
    
    def _navigate_down(self) -> dict:
        """Navigate down in the menu."""
        if not self.menu_items:
            return {'action': 'no_items'}
        
        self.navigation_active = True
        self.selected_index = (self.selected_index + 1) % len(self.menu_items)
        return {'action': 'navigate', 'direction': 'down', 'selected_index': self.selected_index}
    
    def _confirm_selection(self) -> dict:
        """Confirm the currently selected item."""
        if not self.menu_items or not self.navigation_active:
            return {'action': 'no_selection'}
        
        item_number = self.selected_index + 1
        return {'action': 'select_item', 'item_number': item_number}
    
    def set_menu_items(self, items: List[str]) -> None:
        """Set the current menu items."""
        self.menu_items = items
        # Reset selection if it's out of bounds
        if self.selected_index >= len(items):
            self.selected_index = 0
    
    def get_selected_index(self) -> int:
        """Get the currently selected index (0-based)."""
        return self.selected_index if self.navigation_active else -1
    
    def get_selected_item_number(self) -> int:
        """Get the currently selected item number (1-based) or -1 if none."""
        if self.navigation_active and self.menu_items:
            return self.selected_index + 1
        return -1
    
    def is_navigation_active(self) -> bool:
        """Check if navigation mode is active."""
        return self.navigation_active
    
    def is_menu_open(self) -> bool:
        """Check if any menu is currently open."""
        return self.state != MenuState.CLOSED
    
    def get_current_state(self) -> MenuState:
        """Get the current menu state."""
        return self.state
    
    def reset(self) -> None:
        """Reset the menu state machine."""
        self.transition_to(MenuState.CLOSED)


class MenuInputHandler:
    """Handles menu input using the state machine."""
    
    def __init__(self, menu_state_machine: MenuStateMachine):
        self.state_machine = menu_state_machine
    
    def handle_menu_input(self, key: str) -> Optional[dict]:
        """
        Handle input for menus using the state machine.
        Returns action dict if an action should be taken, None otherwise.
        """
        return self.state_machine.handle_input(key)
    
    def is_menu_active(self) -> bool:
        """Check if any menu is currently active."""
        return self.state_machine.is_menu_open()
    
    def get_highlighted_item(self) -> int:
        """Get the currently highlighted item number (1-based) or -1 if none."""
        return self.state_machine.get_selected_item_number()
