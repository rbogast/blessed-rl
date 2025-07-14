"""
Input handling system for numpad movement.
"""

from ecs.system import System
from components.core import Position, Player
from components.combat import Health
from game.game_state import GameStateManager
from game.config import GameConfig
from typing import Optional


class InputSystem(System):
    """Handles player input and queues movement actions."""
    
    # Numpad movement mapping (using actual numpad digit characters)
    MOVEMENT_KEYS = {
        '7': (-1, -1),   # Northwest (numpad 7)
        '8': (0, -1),    # North (numpad 8)
        '9': (1, -1),    # Northeast (numpad 9)
        '4': (-1, 0),    # West (numpad 4)
        '6': (1, 0),     # East (numpad 6)
        '1': (-1, 1),    # Southwest (numpad 1)
        '2': (0, 1),     # South (numpad 2)
        '3': (1, 1),     # Southeast (numpad 3)
    }
    
    def __init__(self, world, game_state: GameStateManager, message_log, render_system=None):
        super().__init__(world)
        self.game_state = game_state
        self.message_log = message_log
        self.render_system = render_system
        self.pending_action = None  # (action_type, dx, dy)
    
    def update(self, dt: float = 0.0) -> None:
        """Process any pending input actions."""
        # This system doesn't update automatically - it responds to input events
        pass
    
    def handle_input(self, key) -> bool:
        """Handle a key press and return True if an action was queued."""
        if not self.game_state.is_playing():
            return False
        
        # Convert blessed key to string representation
        key_str = str(key)
        key_name = key.name if hasattr(key, 'name') else key_str
        
        # Check if a menu is active first
        if self.render_system and self._is_menu_active():
            # In menu mode - handle navigation and selection
            if key_str == '8':  # Numpad 8 - navigate up
                self._navigate_menu_up()
                return True
            elif key_str == '2':  # Numpad 2 - navigate down
                self._navigate_menu_down()
                return True
            elif key_name == 'KEY_ENTER':  # Numpad Enter - select highlighted item
                self._select_highlighted_item()
                return True
            elif key_str.isdigit() and key_str != '0':
                # Direct number selection still works
                self._select_item(int(key_str))
                return True
        else:
            # Not in menu mode - handle movement keys
            if key_str in self.MOVEMENT_KEYS:
                dx, dy = self.MOVEMENT_KEYS[key_str]
                return self._queue_movement(dx, dy)
        
        # Handle other keys
        if key == 'q':
            self._quit_game()
            return True
        elif key == '5':  # Numpad 5 for wait
            self._wait()
            return True
        elif key.lower() == 'r':
            self._restart_game()
            return True
        elif key.lower() == 'i':
            self._toggle_inventory()
            return True
        elif key.lower() == 'g':
            self._pickup_items()
            return True
        elif key.lower() == 'e':
            self._equip_menu()
            return True
        elif key.lower() == 'u':
            self._use_menu()
            return True
        elif key.lower() == 'd':
            self._drop_menu()
            return True
        elif key == 'KEY_ESCAPE' or key == '\x1b':  # Escape key
            if self.render_system and self._is_menu_active():
                self._close_menus()
                return True
            else:
                return False
        
        return False
    
    def _queue_movement(self, dx: int, dy: int) -> bool:
        """Queue a movement action for the player."""
        player_entity = self.game_state.get_player_entity()
        if not player_entity:
            return False
        
        position = self.world.get_component(player_entity, Position)
        if not position:
            return False
        
        new_x = position.x + dx
        new_y = position.y + dy
        
        # Prevent moving west past x=0
        if new_x < 0:
            self.message_log.add_warning("You cannot go further west!")
            return False
        
        # Prevent moving outside Y bounds
        if not GameConfig.is_valid_y(new_y):
            self.message_log.add_warning("You cannot go that way!")
            return False
        
        # Queue the movement action
        self.pending_action = ('move', dx, dy)
        return True
    
    def _wait(self) -> None:
        """Player waits/skips turn."""
        self.pending_action = ('wait',)
        self.message_log.add_info("You wait...")
    
    def _quit_game(self) -> None:
        """Quit the game."""
        player_entity = self.game_state.get_player_entity()
        if player_entity:
            position = self.world.get_component(player_entity, Position)
            final_x = position.x if position else 0
            self.game_state.game_over("Player quit", final_x)
        else:
            self.game_state.game_over("Player quit", 0)
    
    def _restart_game(self) -> None:
        """Restart the game with a new map."""
        self.pending_action = ('restart',)
        self.message_log.add_info("Restarting game...")
    
    def get_pending_action(self) -> Optional[tuple]:
        """Get and clear the pending action."""
        action = self.pending_action
        self.pending_action = None
        return action
    
    def _toggle_inventory(self) -> None:
        """Toggle inventory display in the sidebar."""
        self.pending_action = ('toggle_inventory',)
        self.message_log.add_info("Toggling inventory display...")
    
    def _pickup_items(self) -> None:
        """Pick up items at current position."""
        self.pending_action = ('pickup',)
    
    def _equip_menu(self) -> None:
        """Show equip/unequip menu."""
        self.pending_action = ('equip_menu',)
    
    def _use_menu(self) -> None:
        """Show use item menu."""
        self.pending_action = ('use_menu',)
    
    def _drop_menu(self) -> None:
        """Show drop item menu."""
        self.pending_action = ('drop_menu',)
    
    def _select_item(self, item_number: int) -> None:
        """Select an item from the current menu."""
        self.pending_action = ('select_item', item_number)
    
    def has_pending_action(self) -> bool:
        """Check if there's a pending action."""
        return self.pending_action is not None
    
    def _close_menus(self) -> None:
        """Close all active menus."""
        self.pending_action = ('close_menus',)
    
    def _is_menu_active(self) -> bool:
        """Check if any menu is currently active."""
        return (self.render_system.menu_manager.is_menu_active() or 
                self.render_system.menu_manager.is_inventory_shown())
    
    def _navigate_menu_up(self) -> None:
        """Navigate up in the current menu."""
        if self.render_system:
            self.render_system.navigate_menu_up()
            self.game_state.request_render()
    
    def _navigate_menu_down(self) -> None:
        """Navigate down in the current menu."""
        if self.render_system:
            self.render_system.navigate_menu_down()
            self.game_state.request_render()
    
    def _select_highlighted_item(self) -> None:
        """Select the currently highlighted menu item."""
        if self.render_system:
            selected_item = self.render_system.get_selected_menu_item()
            if selected_item > 0:
                self._select_item(selected_item)
