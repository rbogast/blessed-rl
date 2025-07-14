"""Tile rendering system for terrain and world tiles."""

from typing import Tuple
from game.config import GameConfig


class TileRenderer:
    """Handles rendering of terrain tiles and world elements."""
    
    def __init__(self, world_generator, glyph_config, entity_renderer, game_state=None):
        self.world_generator = world_generator
        self.glyph_config = glyph_config
        self.entity_renderer = entity_renderer
        self.game_state = game_state
        self.WORLD_HEIGHT = GameConfig.MAP_HEIGHT
    
    def get_tile_display(self, world_x: int, world_y: int) -> Tuple[str, str]:
        """Get the character and color to display for a tile."""
        # Check if position is in bounds
        if world_y < 0 or world_y >= self.WORLD_HEIGHT:
            return ' ', 'black'
        
        # Get tile info
        tile = self.world_generator.get_tile_at(world_x, world_y)
        if not tile:
            return ' ', 'black'
        
        # Check visibility - only show tiles that have been explored
        if not tile.explored:
            return ' ', 'black'  # Never explored - show nothing
        
        # Find the topmost renderable entity at this position
        entity_char, entity_color = self.entity_renderer.get_entity_at_position(world_x, world_y)
        
        if entity_char:
            # Show entity with appropriate color based on visibility
            if tile.visible:
                return entity_char, entity_color
            else:
                # Entity is out of FOV - show same character but in gray
                return entity_char, 'bright_black'
        else:
            # No entity - render terrain
            # Get the normal terrain glyph and color
            if tile.is_wall:
                terrain_char, terrain_color = self.glyph_config.get_terrain_glyph('wall', tile.visible)
            else:
                terrain_char, terrain_color = self.glyph_config.get_terrain_glyph('floor', tile.visible)
            
            # Check if this tile is bloody (simple blood overlay system)
            if self.game_state and (world_x, world_y) in self.game_state.blood_tiles:
                # Render the terrain glyph in red instead of normal color
                if tile.visible:
                    return terrain_char, 'red'
                else:
                    # Out of FOV - show darker blood
                    return terrain_char, 'dark_red'
            else:
                # No blood - show normal terrain
                return terrain_char, terrain_color
