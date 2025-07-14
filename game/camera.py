"""
Camera system for viewport management.
"""

from typing import Tuple


class Camera:
    """Manages the viewport for the horizontal scrolling world."""
    
    def __init__(self, viewport_width: int = 55, viewport_height: int = 23):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.x = 0  # Camera's global X position
        self.y = 0  # Camera's Y position (always 0 for this game)
    
    def follow_entity(self, entity_x: int, entity_y: int) -> None:
        """Update camera to follow an entity (usually the player)."""
        # Center the camera on the entity horizontally
        self.x = max(0, entity_x - self.viewport_width // 2)
        
        # Y is always 0 since we don't scroll vertically
        self.y = 0
    
    def get_viewport_bounds(self) -> Tuple[int, int, int, int]:
        """Get the bounds of the current viewport in global coordinates."""
        left = self.x
        right = self.x + self.viewport_width
        top = self.y
        bottom = self.y + self.viewport_height
        return left, top, right, bottom
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = world_x - self.x
        screen_y = world_y - self.y
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates."""
        world_x = screen_x + self.x
        world_y = screen_y + self.y
        return world_x, world_y
    
    def is_in_viewport(self, world_x: int, world_y: int) -> bool:
        """Check if a world position is visible in the current viewport."""
        left, top, right, bottom = self.get_viewport_bounds()
        return left <= world_x < right and top <= world_y < bottom
    
    def get_visible_chunks(self) -> Tuple[int, int]:
        """Get the range of chunks that are currently visible."""
        left, _, right, _ = self.get_viewport_bounds()
        
        chunk_width = 40
        start_chunk = left // chunk_width
        end_chunk = (right - 1) // chunk_width + 1
        
        return start_chunk, end_chunk
