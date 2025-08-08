"""
Simplified tile renderer that uses clean data from SimpleLightingSystem.

This renderer is much simpler than LayeredTileRenderer because it receives
clean, consistent data from the simple lighting system. No more emergency fallbacks
or complex state checking - just render what we're told.
"""

from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from game.config import GameConfig


@dataclass
class CompositeLayer:
    """Represents the final composite of all layers for a tile."""
    char: str
    color: str


class UnifiedTileRenderer:
    """
    Simplified tile renderer that uses clean data from SimpleLightingSystem.
    
    This renderer trusts the data it receives and doesn't need to make decisions
    about visibility or lighting - that's all handled by the simple lighting system.
    """
    
    def __init__(self, world, world_generator, glyph_config, game_state=None, 
                 throwing_system=None, examine_system=None, unified_fov_lighting=None):
        self.world = world
        self.world_generator = world_generator
        self.glyph_config = glyph_config
        self.game_state = game_state
        self.throwing_system = throwing_system
        self.examine_system = examine_system
        self.unified_fov_lighting = unified_fov_lighting
        
        # Simple tile cache for FOV tiles only
        self.tile_cache: Dict[Tuple[int, int], CompositeLayer] = {}
        
        # Spatial entity indexing for performance
        self.entity_spatial_index: Dict[Tuple[int, int], list] = {}
        self.visible_entities_index: Dict[Tuple[int, int], Optional[CompositeLayer]] = {}
        self.spatial_index_dirty = True
    
    def set_unified_fov_lighting(self, unified_fov_lighting) -> None:
        """Set the unified FOV lighting system reference."""
        self.unified_fov_lighting = unified_fov_lighting
    
    def get_tile_display(self, world_x: int, world_y: int) -> Tuple[str, str]:
        """Get the character and color to display for a tile."""
        # Check if position is in bounds
        if world_y < 0 or world_y >= GameConfig.MAP_HEIGHT:
            return ' ', 'black'
        
        # Get tile info
        tile = self.world_generator.get_tile_at(world_x, world_y)
        if not tile:
            return ' ', 'black'
        
        # Never explored tiles are always black
        if not tile.explored:
            return ' ', 'black'
        
        # Get clean render data from unified system
        if not self.unified_fov_lighting:
            # Fallback to explored color if no unified system
            return self._get_explored_tile_display(world_x, world_y, tile)
        
        render_data = self.unified_fov_lighting.get_render_data()
        pos = (world_x, world_y)
        
        # Check if we need to recalculate this tile
        if pos in render_data:
            # Tile is in current FOV - render with full detail
            render_info = render_data[pos]
            composite = self._render_tile_layers(world_x, world_y, tile, render_info)
            self.tile_cache[pos] = composite
            return composite.char, composite.color
        else:
            # Tile is not in FOV - always render as explored (don't use cache for explored tiles)
            return self._get_explored_tile_display(world_x, world_y, tile)
    
    def _get_explored_tile_display(self, world_x: int, world_y: int, tile) -> Tuple[str, str]:
        """Get the display for an explored but not visible tile (simple, no caching)."""
        # Get explored terrain glyph (not visible, so use explored variant)
        terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(
            tile.tile_type, visible=False, lit=False, penumbra=False
        )
        terrain_layer = CompositeLayer(terrain_char, terrain_color)
        
        effects_layer = self._render_effects_layer(world_x, world_y, tile)
        item_layer = self._render_item_layer(world_x, world_y, tile)
        character_layer = self._render_last_seen_character_layer(world_x, world_y, tile)
        
        # Composite layers
        final_char = terrain_layer.char
        final_color = terrain_layer.color
        
        # Apply effects layer if present
        if effects_layer:
            final_color = effects_layer.color
        
        # Apply item layer if present
        if item_layer:
            final_char = item_layer.char
            final_color = item_layer.color
        
        # Apply last seen character layer if present
        if character_layer:
            final_char = character_layer.char
            final_color = character_layer.color
        
        # Always use explored color for out-of-FOV tiles
        return final_char, GameConfig.EXPLORED_TILE_COLOR
    
    def _render_tile_layers(self, world_x: int, world_y: int, tile, render_info) -> CompositeLayer:
        """Render all layers for a tile using clean render data."""
        # Layer 1: Base terrain - use explored glyph if not lit/penumbra
        terrain_layer = self._render_terrain_layer(world_x, world_y, tile, render_info)
        
        # Layer 2: Blood/effects
        effects_layer = self._render_effects_layer(world_x, world_y, tile, render_info)
        
        # Layer 3: Non-character entities (items, etc.)
        item_layer = self._render_item_layer(world_x, world_y, tile)
        
        # Layer 4: Character entities (player, NPCs)
        character_layer = self._render_character_layer(world_x, world_y, tile)
        
        # Layer 5: Special overlays (examine cursor, throwing cursor)
        overlay_layer = self._render_overlay_layer(world_x, world_y, tile)
        
        # Composite all layers together
        return self._composite_layers(
            terrain_layer, effects_layer, item_layer, 
            character_layer, overlay_layer, render_info
        )
    
    def _render_terrain_layer(self, world_x: int, world_y: int, tile, render_info=None) -> CompositeLayer:
        """Render the base terrain layer."""
        # Determine if we should use explored glyph based on lighting
        if render_info and (render_info.lit or render_info.penumbra):
            # Use normal glyph for lit/penumbra tiles
            terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(
                tile.tile_type, visible=True, lit=True, penumbra=False
            )
        else:
            # Use explored glyph for tiles outside lit/penumbra areas
            terrain_char, terrain_color = self.glyph_config.get_terrain_glyph(
                tile.tile_type, visible=False, lit=False, penumbra=False
            )
        return CompositeLayer(terrain_char, terrain_color)
    
    def _render_effects_layer(self, world_x: int, world_y: int, tile, render_info=None) -> Optional[CompositeLayer]:
        """Render blood and other tile effects."""
        # Check for blood
        blood_tiles = set()
        if hasattr(self.world_generator, 'get_blood_tiles'):
            blood_tiles = self.world_generator.get_blood_tiles()
        
        if (world_x, world_y) in blood_tiles:
            # Blood effect - use appropriate terrain char based on lighting
            if render_info and (render_info.lit or render_info.penumbra):
                # Use normal glyph for lit/penumbra tiles
                terrain_char, _ = self.glyph_config.get_terrain_glyph(
                    tile.tile_type, visible=True, lit=True, penumbra=False
                )
            else:
                # Use explored glyph for tiles outside lit/penumbra areas
                terrain_char, _ = self.glyph_config.get_terrain_glyph(
                    tile.tile_type, visible=False, lit=False, penumbra=False
                )
            return CompositeLayer(terrain_char, 'red')
        
        return None
    
    def _render_item_layer(self, world_x: int, world_y: int, tile) -> Optional[CompositeLayer]:
        """Render non-character entities (items, corpses, etc.)."""
        from components.corpse import Corpse
        from components.items import Pickupable
        
        # Rebuild spatial index if dirty
        if self.spatial_index_dirty:
            self._rebuild_spatial_index()
        
        # Get entities at this position from spatial index
        pos = (world_x, world_y)
        entities_at_pos = self.entity_spatial_index.get(pos, [])
        
        if not entities_at_pos:
            return None
        
        # Prioritize corpses over items
        corpse_entities = []
        item_entities = []
        other_entities = []
        
        for entity_id, char, color in entities_at_pos:
            if self.world.has_component(entity_id, Corpse):
                corpse_entities.append((entity_id, char, color))
            elif self.world.has_component(entity_id, Pickupable):
                item_entities.append((entity_id, char, color))
            else:
                other_entities.append((entity_id, char, color))
        
        # Determine what to show
        total_pickupable = len(corpse_entities) + len(item_entities)
        has_corpses = len(corpse_entities) > 0
        
        if total_pickupable > 1:
            # Multiple items - show stack indicator
            stack_color = 'red' if has_corpses else 'white'
            return CompositeLayer('%', stack_color)
        elif corpse_entities:
            # Single corpse
            return CompositeLayer(corpse_entities[0][1], corpse_entities[0][2])
        elif item_entities:
            # Single item
            return CompositeLayer(item_entities[0][1], item_entities[0][2])
        elif other_entities:
            # Other entities
            return CompositeLayer(other_entities[0][1], other_entities[0][2])
        
        return None
    
    def _render_character_layer(self, world_x: int, world_y: int, tile) -> Optional[CompositeLayer]:
        """Render character entities (player, NPCs) that are currently visible."""
        from components.core import Player, Visible
        from components.ai import AI
        
        # Rebuild spatial index if dirty
        if self.spatial_index_dirty:
            self._rebuild_spatial_index()
        
        # Check for player first (most common case)
        player_entity = self.game_state.get_player_entity() if self.game_state else None
        if player_entity:
            from components.core import Position, Renderable
            position = self.world.get_component(player_entity, Position)
            if position and position.x == world_x and position.y == world_y:
                renderable = self.world.get_component(player_entity, Renderable)
                if renderable:
                    return CompositeLayer(renderable.char, renderable.color)
        
        # Check for visible AI entities at this position
        pos = (world_x, world_y)
        entities_at_pos = self.entity_spatial_index.get(pos, [])
        
        for entity_id, char, color in entities_at_pos:
            if self.world.has_component(entity_id, AI):
                visible = self.world.get_component(entity_id, Visible)
                if visible and visible.visible:
                    return CompositeLayer(char, color)
        
        return None
    
    def _render_last_seen_character_layer(self, world_x: int, world_y: int, tile) -> Optional[CompositeLayer]:
        """Render last seen character entities for explored but not visible tiles."""
        # Rebuild spatial index if dirty
        if self.spatial_index_dirty:
            self._rebuild_spatial_index()
        
        # Use spatial index for fast lookup
        pos = (world_x, world_y)
        return self.visible_entities_index.get(pos)
    
    def _render_overlay_layer(self, world_x: int, world_y: int, tile) -> Optional[CompositeLayer]:
        """Render special overlays like examine cursor and throwing cursor."""
        # Check for examine cursor first (highest priority)
        if self.examine_system and self.game_state:
            player_entity = self.game_state.get_player_entity()
            if player_entity and self.examine_system.is_examine_active(player_entity):
                cursor_pos = self.examine_system.get_cursor_position(player_entity)
                if cursor_pos and cursor_pos == (world_x, world_y):
                    # Return special overlay that will be handled in compositing
                    return CompositeLayer('', 'examine_cursor')
        
        # Check for throwing cursor
        if self.throwing_system and self.game_state:
            player_entity = self.game_state.get_player_entity()
            if player_entity and self.throwing_system.is_throwing_active(player_entity):
                cursor_pos = self.throwing_system.get_cursor_position(player_entity)
                if cursor_pos and cursor_pos == (world_x, world_y):
                    # Check if cursor is blocked
                    throwing_line = self.throwing_system.get_throwing_line(player_entity)
                    is_blocked = self._is_throwing_line_blocked(throwing_line, world_x, world_y)
                    
                    if is_blocked:
                        return CompositeLayer('', 'throwing_cursor_blocked')
                    else:
                        return CompositeLayer('', 'throwing_cursor')
                
                # Check for throwing line
                throwing_line = self.throwing_system.get_throwing_line(player_entity)
                if (world_x, world_y) in throwing_line:
                    is_blocked = self._is_throwing_line_blocked(throwing_line, world_x, world_y)
                    
                    if is_blocked:
                        return CompositeLayer('*', 'red')
                    else:
                        return CompositeLayer('*', 'white')
        
        return None
    
    def _composite_layers(self, terrain_layer: CompositeLayer, effects_layer: Optional[CompositeLayer],
                         item_layer: Optional[CompositeLayer], character_layer: Optional[CompositeLayer],
                         overlay_layer: Optional[CompositeLayer], render_info) -> CompositeLayer:
        """Composite all layers together with clean lighting from render_info."""
        
        # Start with the topmost visible layer
        final_char = terrain_layer.char
        final_color = terrain_layer.color
        
        # Apply effects layer if present
        if effects_layer:
            final_color = effects_layer.color  # Effects modify color, not char
        
        # Apply item layer if present
        if item_layer:
            final_char = item_layer.char
            final_color = item_layer.color
        
        # Apply character layer if present (highest priority for entities)
        if character_layer:
            final_char = character_layer.char
            final_color = character_layer.color
        
        # Apply overlay layer if present (special cursors)
        if overlay_layer:
            if overlay_layer.char:  # Throwing line has its own char
                final_char = overlay_layer.char
                final_color = overlay_layer.color
            else:  # Cursor overlays modify the background
                if overlay_layer.color == 'examine_cursor':
                    final_color = 'black_on_white'
                elif overlay_layer.color == 'throwing_cursor':
                    final_color = 'black_on_magenta'
                elif overlay_layer.color == 'throwing_cursor_blocked':
                    final_color = 'red'
        
        # Apply lighting using clean render_info data
        final_color = self._apply_clean_lighting(final_color, render_info)
        
        return CompositeLayer(final_char, final_color)
    
    def _apply_clean_lighting(self, color: str, render_info) -> str:
        """Apply lighting using clean data from render_info - no fallbacks needed."""
        # This is much simpler than the old system because we trust the render_info
        
        if render_info.lit:
            # Fully lit - use natural color
            return color
        elif render_info.penumbra:
            # In penumbra - use centralized penumbra color
            return GameConfig.PENUMBRA_COLOR
        else:
            # Outside light range but visible - use centralized unlit color
            return GameConfig.UNLIT_COLOR
    
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
    
    def _rebuild_spatial_index(self) -> None:
        """Rebuild the spatial entity index for fast position-based lookups."""
        from components.core import Position, Renderable, Player
        from components.ai import AI
        
        self.entity_spatial_index.clear()
        self.visible_entities_index.clear()
        
        # Index all entities with position and renderable components
        entities = self.world.get_entities_with_components(Position, Renderable)
        for entity_id in entities:
            position = self.world.get_component(entity_id, Position)
            renderable = self.world.get_component(entity_id, Renderable)
            
            if position and renderable:
                pos = (position.x, position.y)
                
                # Skip player and AI entities for item layer (they go in character layer)
                if not (self.world.has_component(entity_id, Player) or 
                       self.world.has_component(entity_id, AI)):
                    if pos not in self.entity_spatial_index:
                        self.entity_spatial_index[pos] = []
                    self.entity_spatial_index[pos].append((entity_id, renderable.char, renderable.color))
                else:
                    # Include AI entities in spatial index for character layer optimization
                    if self.world.has_component(entity_id, AI):
                        if pos not in self.entity_spatial_index:
                            self.entity_spatial_index[pos] = []
                        self.entity_spatial_index[pos].append((entity_id, renderable.char, renderable.color))
        
        # Index last seen character positions
        from components.core import Visible
        visible_entities = self.world.get_entities_with_components(Visible)
        for entity_id in visible_entities:
            visible = self.world.get_component(entity_id, Visible)
            if (visible and visible.explored and 
                visible.last_seen_x is not None and visible.last_seen_y is not None and
                visible.last_seen_char and visible.last_seen_color):
                pos = (visible.last_seen_x, visible.last_seen_y)
                self.visible_entities_index[pos] = CompositeLayer(visible.last_seen_char, visible.last_seen_color)
        
        self.spatial_index_dirty = False
    
    def invalidate_cache(self) -> None:
        """Invalidate the entire tile cache (for major changes)."""
        self.tile_cache.clear()
        self.spatial_index_dirty = True
    
    def invalidate_position(self, world_x: int, world_y: int) -> None:
        """Invalidate cache for a specific position."""
        pos = (world_x, world_y)
        if pos in self.tile_cache:
            del self.tile_cache[pos]
        # Mark spatial index as dirty when entities move
        self.spatial_index_dirty = True
    
    def update_fov(self, fov_positions: set) -> None:
        """Update the set of positions currently in FOV (for compatibility)."""
        # This is handled by the unified system now, but keep for compatibility
        pass
