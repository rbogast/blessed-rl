"""
Camera system for viewport management.
"""

from typing import Tuple
from game.config import GameConfig


class Camera:
    """Manages the viewport for level-based dungeon exploration."""
    
    def __init__(self, viewport_width: int = 55, viewport_height: int = 23):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.x = 0  # Camera's X position
        self.y = 0  # Camera's Y position
        
        # Level bounds for camera constraint
        self.level_width = GameConfig.LEVEL_WIDTH
        self.level_height = GameConfig.LEVEL_HEIGHT
    
    def follow_entity(self, entity_x: int, entity_y: int) -> None:
        """Update camera to follow an entity (usually the player)."""
        # Center the camera on the entity
        target_x = entity_x - self.viewport_width // 2
        target_y = entity_y - self.viewport_height // 2
        
        # Constrain camera to level bounds
        self.x = max(0, min(target_x, self.level_width - self.viewport_width))
        self.y = max(0, min(target_y, self.level_height - self.viewport_height))
        
        # If the level is smaller than or equal to viewport, center it
        if self.level_width <= self.viewport_width:
            self.x = 0
        if self.level_height <= self.viewport_height:
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
    
    def set_level_bounds(self, width: int, height: int) -> None:
        """Update the camera's level bounds for a new level."""
        self.level_width = width
        self.level_height = height
        
        # Recalculate camera position to ensure it's within new bounds
        self.x = max(0, min(self.x, self.level_width - self.viewport_width))
        self.y = max(0, min(self.y, self.level_height - self.viewport_height))
        
        # If the level is smaller than or equal to viewport, center it
        if self.level_width <= self.viewport_width:
            self.x = 0
        if self.level_height <= self.viewport_height:
            self.y = 0
