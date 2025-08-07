"""Tile rendering system for terrain and world tiles."""

from typing import Tuple
from game.config import GameConfig


class TileRenderer:
    """Handles rendering of terrain tiles and world elements."""
    
    def __init__(self, world_generator, glyph_config, entity_renderer, game_state=None, throwing_system=None, examine_system=None):
        self.world_generator = world_generator
        self.glyph_config = glyph_config
        self.entity_renderer = entity_renderer
        self.game_state = game_state
        self.throwing_system = throwing_system
        self.examine_system = examine_system
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
        
        # Check for examine cursor first (highest priority)
        if self.examine_system and self.game_state:
            player_entity = self.game_state.get_player_entity()
            if player_entity and self.examine_system.is_examine_active(player_entity):
                # Check if this position is the examine cursor
                cursor_pos = self.examine_system.get_cursor_position(player_entity)
                if cursor_pos and cursor_pos == (world_x, world_y):
                    # Get the original glyph that would be displayed at this position
                    original_char, original_color = self._get_original_tile_glyph(world_x, world_y, tile)
                    # Black text on white background for examine cursor
                    return original_char, 'black_on_white'
        
        # Check for throwing cursor and line (second priority)
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
            # Check if the entity is actually visible (has Visible component and is marked as visible)
            entity_visible = self._is_entity_visible_at_position(world_x, world_y)
            
            if entity_visible:
                # Show entity with appropriate color based on visibility and lighting
                if tile.visible:
                    # Check if tile is lit or in penumbra
                    is_lit = getattr(tile, 'lit', False)
                    is_penumbra = getattr(tile, 'penumbra', False)
                    if is_lit:
                        return entity_char, entity_color
                    elif is_penumbra:
                        # Visible and in penumbra - show in blue
                        return entity_char, 'blue'
                    else:
                        # Visible but outside penumbra - show in explored color (gray)
                        return entity_char, GameConfig.EXPLORED_TILE_COLOR
                else:
                    # Entity is out of FOV - show same character in explored color
                    return entity_char, GameConfig.EXPLORED_TILE_COLOR
            # If entity is not visible, fall through to check for last seen entities
        
        # No currently visible entity, check for last seen entities at this position
        last_seen_char, last_seen_color = self._get_last_seen_entity_at_position(world_x, world_y)
        if last_seen_char:
            # Show last seen entity in explored color
            return last_seen_char, GameConfig.EXPLORED_TILE_COLOR
        
        # No visible entity - render terrain
        # Get the terrain glyph based on tile type and lighting
        is_lit = getattr(tile, 'lit', False)  # Check if tile has lit attribute
        is_penumbra = getattr(tile, 'penumbra', False)  # Check if tile has penumbra attribute
        terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(tile.tile_type, tile.visible, is_lit, is_penumbra)
        
        # Check if this tile is bloody (level-based blood overlay system)
        blood_tiles = set()
        if hasattr(self.world_generator, 'get_blood_tiles'):
            blood_tiles = self.world_generator.get_blood_tiles()
        
        if (world_x, world_y) in blood_tiles:
            # Render the terrain glyph with blood color based on visibility and lighting
            if tile.visible:
                # Check if tile is lit
                if is_lit:
                    return terrain_char, 'red'  # Lit blood is red
                elif is_penumbra:
                    return terrain_char, 'blue'  # Penumbra blood is blue
                else:
                    return terrain_char, GameConfig.EXPLORED_TILE_COLOR  # Outside penumbra blood is gray
            else:
                # Out of FOV - show blood in same color as other explored tiles
                return terrain_char, GameConfig.EXPLORED_TILE_COLOR
        else:
            # No blood - show normal terrain
            return terrain_char, terrain_color
    
    def _get_original_tile_glyph(self, world_x: int, world_y: int, tile) -> Tuple[str, str]:
        """Get the original glyph and color that would be displayed at this position."""
        # Check for entities first
        entity_char, entity_color = self.entity_renderer.get_entity_at_position(world_x, world_y)
        
        if entity_char:
            # Show entity with appropriate color based on visibility and lighting
            if tile.visible:
                # Check if tile is lit or in penumbra
                is_lit = getattr(tile, 'lit', False)
                is_penumbra = getattr(tile, 'penumbra', False)
                if is_lit:
                    return entity_char, entity_color
                elif is_penumbra:
                    # Visible and in penumbra - show in blue
                    return entity_char, 'blue'
                else:
                    # Visible but outside penumbra - show in explored color (gray)
                    return entity_char, GameConfig.EXPLORED_TILE_COLOR
            else:
                # Entity is out of FOV - show same character in explored color
                return entity_char, GameConfig.EXPLORED_TILE_COLOR
        else:
            # No entity - render terrain
            # Get the terrain glyph based on tile type and lighting
            is_lit = getattr(tile, 'lit', False)  # Check if tile has lit attribute
            is_penumbra = getattr(tile, 'penumbra', False)  # Check if tile has penumbra attribute
            terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(tile.tile_type, tile.visible, is_lit, is_penumbra)
            
            # Check if this tile is bloody (level-based blood overlay system)
            blood_tiles = set()
            if hasattr(self.world_generator, 'get_blood_tiles'):
                blood_tiles = self.world_generator.get_blood_tiles()
            
            if (world_x, world_y) in blood_tiles:
                # Render the terrain glyph with blood color based on visibility and lighting
                if tile.visible:
                    # Check if tile is lit
                    if is_lit:
                        return terrain_char, 'red'  # Lit blood is red
                    elif is_penumbra:
                        return terrain_char, 'blue'  # Penumbra blood is blue
                    else:
                        return terrain_char, GameConfig.EXPLORED_TILE_COLOR  # Outside penumbra blood is gray
                else:
                    # Out of FOV - show blood in same color as other explored tiles
                    return terrain_char, GameConfig.EXPLORED_TILE_COLOR
            else:
                # No blood - show normal terrain
                return terrain_char, terrain_color
    
    def _get_entity_at_position(self, world_x: int, world_y: int) -> tuple:
        """Get entity info at position, including last seen entities. Returns (char, color, is_current)."""
        if not hasattr(self.entity_renderer, 'world'):
            return None, None, False
        
        from components.core import Position, Visible, Player
        from components.items import Item, Pickupable
        from components.ai import AI
        
        # First, check if there's a current entity at this position using the entity renderer
        entity_char, entity_color = self.entity_renderer.get_entity_at_position(world_x, world_y)
        
        if entity_char:
            # There's an entity here - check if it should be visible
            tile = self.world_generator.get_tile_at(world_x, world_y)
            
            # The entity renderer already handles priority and returns the top entity
            # We just need to check if any entity at this position should be visible
            entities = self.entity_renderer.world.get_entities_with_components(Position)
            for entity_id in entities:
                position = self.entity_renderer.world.get_component(entity_id, Position)
                if position and position.x == world_x and position.y == world_y:
                    # Check visibility based on entity type
                    visible_component = self.entity_renderer.world.get_component(entity_id, Visible)
                    
                    # Player is always visible if tile is visible
                    if self.entity_renderer.world.has_component(entity_id, Player):
                        if tile and tile.visible:
                            return entity_char, entity_color, True
                        continue
                    
                    # NPCs/AI entities need to be marked as visible in their Visible component
                    if self.entity_renderer.world.has_component(entity_id, AI):
                        if visible_component and visible_component.visible:
                            return entity_char, entity_color, True
                        continue
                    
                    # Items are visible if the tile is visible
                    if (self.entity_renderer.world.has_component(entity_id, Item) or 
                        self.entity_renderer.world.has_component(entity_id, Pickupable)):
                        if tile and tile.visible:
                            return entity_char, entity_color, True
                        continue
                    
                    # Other entities without Visible component are visible if tile is visible
                    if not visible_component:
                        if tile and tile.visible:
                            return entity_char, entity_color, True
                        continue
                    
                    # Entities with Visible component need to be marked as visible
                    if visible_component and visible_component.visible:
                        return entity_char, entity_color, True
        
        # No currently visible entity, check for last seen entities at this position
        tile = self.world_generator.get_tile_at(world_x, world_y)
        if not tile or not tile.explored:
            return None, None, False
        
        # Look for entities that were last seen at this position
        all_entities = self.entity_renderer.world.get_entities_with_components(Visible)
        for entity_id in all_entities:
            visible = self.entity_renderer.world.get_component(entity_id, Visible)
            if (visible and visible.explored and 
                visible.last_seen_x == world_x and visible.last_seen_y == world_y and
                visible.last_seen_char and visible.last_seen_color):
                # Return last seen entity info
                return visible.last_seen_char, visible.last_seen_color, False
        
        return None, None, False
    
    def _is_entity_visible_at_position(self, world_x: int, world_y: int) -> bool:
        """Check if any entity at the given position should be visible."""
        if not hasattr(self.entity_renderer, 'world'):
            return False
        
        from components.core import Position, Visible, Player
        from components.items import Item, Pickupable
        from components.ai import AI
        
        # Get all entities at this position with Position component
        entities = self.entity_renderer.world.get_entities_with_components(Position)
        
        for entity_id in entities:
            position = self.entity_renderer.world.get_component(entity_id, Position)
            
            if position and position.x == world_x and position.y == world_y:
                # Player is always visible if they have a Visible component
                if self.entity_renderer.world.has_component(entity_id, Player):
                    visible = self.entity_renderer.world.get_component(entity_id, Visible)
                    return visible and visible.visible
                
                # NPCs/AI entities need to be marked as visible
                elif self.entity_renderer.world.has_component(entity_id, AI):
                    visible = self.entity_renderer.world.get_component(entity_id, Visible)
                    return visible and visible.visible
                
                # Items are visible if the tile is visible (they don't have their own visibility state)
                elif (self.entity_renderer.world.has_component(entity_id, Item) or 
                      self.entity_renderer.world.has_component(entity_id, Pickupable)):
                    # Items are visible if the tile they're on is visible
                    tile = self.world_generator.get_tile_at(world_x, world_y)
                    return tile and tile.visible
                
                # Other entities with Visible component
                elif self.entity_renderer.world.has_component(entity_id, Visible):
                    visible = self.entity_renderer.world.get_component(entity_id, Visible)
                    return visible and visible.visible
                
                # Entities without Visible component are visible if tile is visible
                else:
                    tile = self.world_generator.get_tile_at(world_x, world_y)
                    return tile and tile.visible
        
        return False
    
    def _get_last_seen_entity_at_position(self, world_x: int, world_y: int) -> tuple:
        """Get last seen entity at position. Returns (char, color)."""
        if not hasattr(self.entity_renderer, 'world'):
            return None, None
        
        from components.core import Visible
        
        # Check if this tile has been explored
        tile = self.world_generator.get_tile_at(world_x, world_y)
        if not tile or not tile.explored:
            return None, None
        
        # Look for entities that were last seen at this position
        all_entities = self.entity_renderer.world.get_entities_with_components(Visible)
        for entity_id in all_entities:
            visible = self.entity_renderer.world.get_component(entity_id, Visible)
            if (visible and visible.explored and 
                visible.last_seen_x == world_x and visible.last_seen_y == world_y and
                visible.last_seen_char and visible.last_seen_color):
                # Return last seen entity info
                return visible.last_seen_char, visible.last_seen_color
        
        return None, None
    
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
