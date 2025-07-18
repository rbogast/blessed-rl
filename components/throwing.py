"""
Components for the throwing system.
"""

from ecs.component import Component
from typing import Optional


class ThrowingCursor(Component):
    """Component for tracking throwing cursor state."""
    
    def __init__(self, cursor_x: int, cursor_y: int, selected_item: int):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        self.selected_item = selected_item  # Entity ID of item being thrown
        self.is_active = True
    
    def move_cursor(self, new_x: int, new_y: int) -> None:
        """Move the cursor to a new position."""
        self.cursor_x = new_x
        self.cursor_y = new_y
    
    def deactivate(self) -> None:
        """Deactivate the cursor."""
        self.is_active = False


class ThrownObject(Component):
    """Component for objects that are currently being thrown."""
    
    def __init__(self, target_x: int, target_y: int, thrower_id: int, 
                 throwing_skill: int, strength: int):
        self.target_x = target_x
        self.target_y = target_y
        self.thrower_id = thrower_id
        self.throwing_skill = throwing_skill
        self.strength = strength
        self.has_landed = False
