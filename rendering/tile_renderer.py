"""Tile rendering system for terrain and world tiles."""

from typing import Tuple
from game.config import GameConfig


class TileRenderer:
    """Handles rendering of terrain tiles and world elements."""
    
    def __init__(self, world_generator, glyph_config, entity_renderer, game_state=None, throwing_system=None):
        self.world_generator = world_generator
        self.glyph_config = glyph_config
        self.entity_renderer = entity_renderer
        self.game_state = game_state
        self.throwing_system = throwing_system
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
        
        # Check for throwing cursor and line first (highest priority)
        if self.throwing_system and self.game_state:
            player_entity = self.game_state.get_player_entity()
            if player_entity and self.throwing_system.is_throwing_active(player_entity):
                # Check if this position is the cursor
                cursor_pos = self.throwing_system.get_cursor_position(player_entity)
                if cursor_pos and cursor_pos == (world_x, world_y):
                    # Get the original glyph that would be displayed at this position
                    original_char, original_color = self._get_original_tile_glyph(world_x, world_y, tile)
                    
                    # Check if cursor is blocked by walls
                    throwing_line = self.throwing_system.get_throwing_line(player_entity)
                    is_blocked = self._is_throwing_line_blocked(throwing_line, world_x, world_y)
                    
                    if is_blocked:
                        # Red text on tile's background color for blocked cursor
                        return original_char, 'red'
                    else:
                        # Black text on magenta background for normal cursor
                        # We'll need to use a special color code for this
                        return original_char, 'black_on_magenta'
                
                # Check if this position is on the throwing line
                throwing_line = self.throwing_system.get_throwing_line(player_entity)
                if (world_x, world_y) in throwing_line:
                    # Check if this part of the line is blocked
                    is_blocked = self._is_throwing_line_blocked(throwing_line, world_x, world_y)
                    
                    if is_blocked:
                        return '*', 'red'  # Red line segment
                    else:
                        return '*', 'white'  # White line segment
        
        # Find the topmost renderable entity at this position
        entity_char, entity_color = self.entity_renderer.get_entity_at_position(world_x, world_y)
        
        if entity_char:
            # Show entity with appropriate color based on visibility
            if tile.visible:
                return entity_char, entity_color
            else:
                # Entity is out of FOV - show same character in explored color
                return entity_char, GameConfig.EXPLORED_TILE_COLOR
        else:
            # No entity - render terrain
            # Get the terrain glyph based on tile type
            terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(tile.tile_type, tile.visible)
            
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
    
    def _get_original_tile_glyph(self, world_x: int, world_y: int, tile) -> Tuple[str, str]:
        """Get the original glyph and color that would be displayed at this position."""
        # Check for entities first
        entity_char, entity_color = self.entity_renderer.get_entity_at_position(world_x, world_y)
        
        if entity_char:
            # Show entity with appropriate color based on visibility
            if tile.visible:
                return entity_char, entity_color
            else:
                # Entity is out of FOV - show same character in explored color
                return entity_char, GameConfig.EXPLORED_TILE_COLOR
        else:
            # No entity - render terrain
            # Get the terrain glyph based on tile type
            terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(tile.tile_type, tile.visible)
            
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
    
    def _is_throwing_line_blocked(self, throwing_line: list, target_x: int, target_y: int) -> bool:
        """Check if the throwing line is blocked by walls up to the target position."""
        if not throwing_line:
            return False
        
        # Find the target position in the line
        target_index = -1
        for i, (x, y) in enumerate(throwing_line):
            if x == target_x and y == target_y:
                target_index = i
                break
        
        if target_index == -1:
            return False
        
        # Check if any position before the target (including target) hits a wall
        for i in range(target_index + 1):
            x, y = throwing_line[i]
            if self.world_generator.is_wall_at(x, y):
                return True
        
        return False
