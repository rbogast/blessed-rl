"""
Components for the examine system.
"""

from ecs.component import Component


class ExamineCursor(Component):
    """Component for tracking examine cursor state."""
    
    def __init__(self, cursor_x: int, cursor_y: int):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        self.is_active = True
    
    def move_cursor(self, new_x: int, new_y: int) -> None:
        """Move the cursor to a new position."""
        self.cursor_x = new_x
        self.cursor_y = new_y
    
    def deactivate(self) -> None:
        """Deactivate the cursor."""
        self.is_active = False
