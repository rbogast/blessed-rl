"""
Field of View system using recursive shadowcasting.
"""

from ecs.system import System
from components.core import Position, Player, Visible, Door
from components.corpse import Corpse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.level_world_gen import LevelWorldGenerator
from game.config import GameConfig
import math


class FOVSystem(System):
    """Implements recursive shadowcasting for field of view calculation."""
    
    def __init__(self, world, world_generator: "LevelWorldGenerator", sight_radius: int = None, message_log=None, lighting_system=None):
        super().__init__(world)
        self.world_generator = world_generator
        self.sight_radius = sight_radius if sight_radius is not None else GameConfig.PLAYER_SIGHT_RADIUS
        self.last_player_pos = None  # Cache last position to avoid unnecessary recalculation
        self.previously_visible_tiles = set()  # Track previously visible tiles
        self.preview_mode = False  # Flag for map preview mode
        self.message_log = message_log  # For discovery messages
        self.lighting_system = lighting_system  # Reference to lighting system
        self.previously_lit_tiles = set()  # Track previously lit tiles
        self.previously_penumbra_tiles = set()  # Track previously penumbra tiles
        
        # Octant multipliers for the 8 directions
        self.octant_multipliers = [
            [1,  0,  0, -1, -1,  0,  0,  1],
            [0,  1, -1,  0,  0, -1,  1,  0],
            [0,  1,  1,  0,  0, -1, -1,  0],
            [1,  0,  0,  1, -1,  0,  0, -1]
        ]
    
    def set_preview_mode(self, enabled: bool) -> None:
        """Enable or disable preview mode."""
        self.preview_mode = enabled
        # Force recalculation when mode changes
        self.last_player_pos = None
    
    def force_recalculation(self) -> None:
        """Force FOV recalculation on next update."""
        self.last_player_pos = None
    
    def update(self, dt: float = 0.0) -> None:
        """Update FOV for all player entities only if they moved."""
        player_entities = self.world.get_entities_with_components(Player, Position)
        
        for player_entity in player_entities:
            player_pos = self.world.get_component(player_entity, Position)
            if not player_pos:
                continue
                
            # Only recalculate if player moved or preview mode changed
            current_pos = (player_pos.x, player_pos.y)
            if self.last_player_pos != current_pos:
                if self.preview_mode:
                    self._calculate_preview_fov(player_entity)
                else:
                    self._calculate_fov(player_entity)
                self.last_player_pos = current_pos
    
    def _calculate_preview_fov(self, player_entity: int) -> None:
        """Calculate preview FOV - show almost all tiles except those completely surrounded by walls."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Clear tile visibility in world generator
        self._clear_tile_visibility(player_pos.x, player_pos.y)
        
        # Clear entity visibility and build position cache
        self.entity_position_cache = {}
        visible_entities = self.world.get_entities_with_components(Visible)
        for entity_id in visible_entities:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.visible = False
            
            # Cache entity positions for fast lookup
            position = self.world.get_component(entity_id, Position)
            if position:
                self.entity_position_cache[(position.x, position.y)] = entity_id
        
        # Player position is always visible
        player_visible = self.world.get_component(player_entity, Visible)
        if player_visible:
            player_visible.visible = True
            player_visible.explored = True
        
        # Get current level to determine bounds
        current_level = self.world_generator.get_current_level()
        if not current_level:
            return
        
        # Make almost all tiles visible except those completely surrounded by walls
        for y in range(current_level.height):
            for x in range(current_level.width):
                # Check if this tile is completely surrounded by walls on all 8 directions
                if self._is_completely_surrounded_by_walls(x, y):
                    # Don't make this tile visible
                    continue
                else:
                    # Make this tile visible
                    self._set_visible(x, y)
    
    def _is_completely_surrounded_by_walls(self, x: int, y: int) -> bool:
        """Check if a position is completely surrounded by walls on all 8 directions."""
        # Check all 8 adjacent positions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip the center position
                
                adj_x = x + dx
                adj_y = y + dy
                
                # If any adjacent position is not a wall, this tile is not completely surrounded
                if not self.world_generator.is_wall_at(adj_x, adj_y):
                    return False
        
        # All 8 adjacent positions are walls
        return True
    
    def _calculate_fov(self, player_entity: int) -> None:
        """Calculate field of view for a player entity."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Use fixed large sight radius for line of sight (independent of light sources)
        self.current_sight_radius = self.sight_radius
        
        # Clear tile visibility and lighting in world generator
        self._clear_tile_visibility(player_pos.x, player_pos.y)
        self._clear_tile_lighting(player_pos.x, player_pos.y)
        self._clear_tile_penumbra(player_pos.x, player_pos.y)
        
        # Clear entity visibility and build position cache
        self.entity_position_cache = {}
        visible_entities = self.world.get_entities_with_components(Visible)
        for entity_id in visible_entities:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.visible = False
            
            # Cache entity positions for fast lookup
            position = self.world.get_component(entity_id, Position)
            if position:
                self.entity_position_cache[(position.x, position.y)] = entity_id
        
        # Player position is always visible
        player_visible = self.world.get_component(player_entity, Visible)
        if player_visible:
            player_visible.visible = True
            # Only mark as explored if within light radius
            if self.lighting_system:
                light_radius = self.lighting_system.get_player_light_radius(player_entity)
                if light_radius > 0:
                    player_visible.explored = True
        
        # Mark player tile as visible (use _set_visible to track it)
        self._set_visible(player_pos.x, player_pos.y)
        
        # Cast shadows in all 8 octants for sight
        for octant in range(8):
            self._cast_light(player_pos.x, player_pos.y, 1, 1.0, 0.0, 
                           self.octant_multipliers[0][octant],
                           self.octant_multipliers[1][octant],
                           self.octant_multipliers[2][octant],
                           self.octant_multipliers[3][octant])
        
        # Calculate lighting and penumbra separately if lighting system is available
        if self.lighting_system:
            # Calculate lighting from player's equipped light sources
            player_light_radius = self.lighting_system.get_player_equipped_light_radius(player_entity)
            if player_light_radius > 0:
                # Calculate lit tiles (inner radius)
                self._calculate_lighting(player_pos.x, player_pos.y, player_light_radius)
                # Calculate penumbra tiles (outer radius = 2x light radius)
                penumbra_radius = player_light_radius * 2
                self._calculate_penumbra(player_pos.x, player_pos.y, player_light_radius, penumbra_radius)
            
            # Calculate lighting from all world light sources
            self._calculate_world_lighting()
    
    def _cast_light(self, cx: int, cy: int, row: int, start: float, end: float,
                   xx: int, xy: int, yx: int, yy: int) -> None:
        """Recursive shadowcasting algorithm."""
        if start < end:
            return
        
        radius_squared = self.current_sight_radius * self.current_sight_radius
        new_start = 0.0
        
        for j in range(row, self.current_sight_radius + 1):
            dx = -j - 1
            dy = -j
            blocked = False
            
            while dx <= 0:
                dx += 1
                
                # Translate the dx, dy coordinates into map coordinates
                mx = cx + dx * xx + dy * xy
                my = cy + dx * yx + dy * yy
                
                # Calculate slopes for this cell
                l_slope = (dx - 0.5) / (dy + 0.5)
                r_slope = (dx + 0.5) / (dy - 0.5)
                
                # Skip if outside our light cone
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                
                # Check if within sight radius
                if dx * dx + dy * dy <= radius_squared:
                    self._set_visible(mx, my)
                
                if blocked:
                    # We're in a shadow
                    if self._is_wall(mx, my):
                        new_start = r_slope
                        continue
                    else:
                        # Found light again
                        blocked = False
                        start = new_start
                else:
                    # We're in light
                    if self._is_wall(mx, my) and j < self.current_sight_radius:
                        # Hit a wall, cast shadow
                        blocked = True
                        self._cast_light(cx, cy, j + 1, start, l_slope,
                                       xx, xy, yx, yy)
                        new_start = r_slope
            
            # If we ended the row blocked, we're done
            if blocked:
                break
    
    def _clear_tile_visibility(self, player_x: int, player_y: int) -> None:
        """Clear tile visibility for previously visible tiles."""
        # Clear all previously visible tiles
        for x, y in self.previously_visible_tiles:
            tile = self.world_generator.get_tile_at(x, y)
            if tile:
                tile.visible = False
        
        # Reset the set for this FOV calculation
        self.previously_visible_tiles.clear()
    
    def _is_wall(self, x: int, y: int) -> bool:
        """Check if a position blocks line of sight."""
        # Check for terrain walls
        if self.world_generator.is_wall_at(x, y):
            return True
        
        # Check for closed doors
        door_entities = self.world.get_entities_with_components(Position, Door)
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            door = self.world.get_component(entity_id, Door)
            
            if position and door and position.x == x and position.y == y:
                # Closed doors block vision, open doors don't
                return not door.is_open
        
        # Check for large corpse piles (8+ corpses block vision)
        corpse_count = 0
        corpse_entities = self.world.get_entities_with_components(Position, Corpse)
        for entity_id in corpse_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                corpse_count += 1
                if corpse_count >= 8:
                    return True
        
        return False
    
    def _set_visible(self, x: int, y: int) -> None:
        """Mark a position as visible (but not necessarily explored)."""
        # Track this tile as visible for next clearing
        self.previously_visible_tiles.add((x, y))
        
        # Mark the tile as visible in the world generator
        tile = self.world_generator.get_tile_at(x, y)
        if tile:
            was_explored = tile.explored
            tile.visible = True
            # Don't automatically mark as explored - that happens only with lighting
            
            # Check if this tile should become interesting (first time seeing stairs/items)
            # Only if it was already explored (so we don't interrupt for things we can't reach)
            if was_explored and not tile.interesting:
                self._check_and_mark_tile_interesting(x, y, tile)
        
        # Mark any entities at this position as visible using cache
        entity_id = self.entity_position_cache.get((x, y))
        if entity_id:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.visible = True
                # Don't automatically mark entities as explored either
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is currently visible."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and tile.visible
    
    def is_explored(self, x: int, y: int) -> bool:
        """Check if a position has been explored."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and tile.explored
    
    def _check_and_mark_tile_interesting(self, x: int, y: int, tile) -> None:
        """Check if a tile should be marked as interesting and interrupt auto-explore if needed."""
        from components.items import Item, Pickupable
        
        # Check for stairs
        stairs_type = self.world_generator.is_stairs_at(x, y)
        has_stairs = stairs_type is not None
        
        # Check for items
        has_items = False
        item_entities = self.world.get_entities_with_components(Position, Item, Pickupable)
        for entity_id in item_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                has_items = True
                break
        
        # Check for closed doors
        has_door = False
        door_entities = self.world.get_entities_with_components(Position, Door)
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            door = self.world.get_component(entity_id, Door)
            if position and door and position.x == x and position.y == y and not door.is_open:
                has_door = True
                break
        
        # Mark tile as interesting if it contains interesting things
        if has_stairs or has_items or has_door:
            tile.interesting = True
            
            # Interrupt auto-explore for any player entities
            self._interrupt_auto_explore_for_discovery(x, y, has_stairs, has_items, has_door)
    
    def _interrupt_auto_explore_for_discovery(self, x: int, y: int, has_stairs: bool, has_items: bool, has_door: bool) -> None:
        """Interrupt auto-explore when new interesting things are discovered."""
        from components.auto_explore import AutoExplore
        
        # Find all player entities with auto-explore
        player_entities = self.world.get_entities_with_components(Player, Position, AutoExplore)
        
        for player_entity in player_entities:
            auto_explore = self.world.get_component(player_entity, AutoExplore)
            if auto_explore and auto_explore.is_active():
                # Determine what was discovered
                discovery_type = ""
                if has_stairs:
                    discovery_type = "stairs"
                elif has_items:
                    discovery_type = "item"
                elif has_door:
                    discovery_type = "door"
                
                # Interrupt auto-explore
                auto_explore.interrupt(f"Discovered {discovery_type}")
                
                # Add message to log if available
                if self.message_log:
                    self.message_log.add_warning(f"Auto-explore interrupted - discovered {discovery_type}!")
    
    def _clear_tile_lighting(self, player_x: int, player_y: int) -> None:
        """Clear tile lighting for previously lit tiles."""
        # Clear all previously lit tiles
        for x, y in self.previously_lit_tiles:
            tile = self.world_generator.get_tile_at(x, y)
            if tile:
                tile.lit = False
        
        # Reset the set for this lighting calculation
        self.previously_lit_tiles.clear()
    
    def _calculate_lighting(self, cx: int, cy: int, light_radius: int) -> None:
        """Calculate lighting using simple circular radius."""
        # Mark player position as lit
        self._set_lit(cx, cy)
        
        # Simple circular lighting - check all positions within radius
        for dx in range(-light_radius, light_radius + 1):
            for dy in range(-light_radius, light_radius + 1):
                # Check if within circular radius
                distance_squared = dx * dx + dy * dy
                if distance_squared <= light_radius * light_radius:
                    light_x = cx + dx
                    light_y = cy + dy
                    
                    # Only light tiles that are visible (within FOV)
                    if self.is_visible(light_x, light_y):
                        self._set_lit(light_x, light_y)
    
    def _set_lit(self, x: int, y: int) -> None:
        """Mark a position as lit and explored."""
        # Track this tile as lit for next clearing
        self.previously_lit_tiles.add((x, y))
        
        # Mark the tile as lit and explored in the world generator
        tile = self.world_generator.get_tile_at(x, y)
        if tile:
            was_explored = tile.explored
            tile.lit = True
            tile.explored = True
            
            # Check if this tile should become interesting (first time exploring)
            if not was_explored:
                self._check_and_mark_tile_interesting(x, y, tile)
        
        # Mark any entities at this position as explored using cache
        entity_id = self.entity_position_cache.get((x, y))
        if entity_id:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.explored = True
    
    def is_lit(self, x: int, y: int) -> bool:
        """Check if a position is currently lit."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and getattr(tile, 'lit', False)
    
    def _clear_tile_penumbra(self, player_x: int, player_y: int) -> None:
        """Clear tile penumbra for previously penumbra tiles."""
        # Clear all previously penumbra tiles
        for x, y in self.previously_penumbra_tiles:
            tile = self.world_generator.get_tile_at(x, y)
            if tile:
                tile.penumbra = False
        
        # Reset the set for this penumbra calculation
        self.previously_penumbra_tiles.clear()
    
    def _calculate_penumbra(self, cx: int, cy: int, light_radius: int, penumbra_radius: int) -> None:
        """Calculate penumbra using circular radius (outer ring around lit area)."""
        # Calculate penumbra - check all positions within penumbra radius but outside light radius
        for dx in range(-penumbra_radius, penumbra_radius + 1):
            for dy in range(-penumbra_radius, penumbra_radius + 1):
                # Check if within penumbra radius
                distance_squared = dx * dx + dy * dy
                if distance_squared <= penumbra_radius * penumbra_radius:
                    # But not within light radius (those are already lit)
                    if distance_squared > light_radius * light_radius:
                        penumbra_x = cx + dx
                        penumbra_y = cy + dy
                        
                        # Only mark penumbra for tiles that are visible (within FOV)
                        if self.is_visible(penumbra_x, penumbra_y):
                            self._set_penumbra(penumbra_x, penumbra_y)
    
    def _set_penumbra(self, x: int, y: int) -> None:
        """Mark a position as penumbra and explored."""
        # Track this tile as penumbra for next clearing
        self.previously_penumbra_tiles.add((x, y))
        
        # Mark the tile as penumbra and explored in the world generator
        tile = self.world_generator.get_tile_at(x, y)
        if tile:
            was_explored = tile.explored
            tile.penumbra = True
            tile.explored = True
            
            # Check if this tile should become interesting (first time exploring)
            if not was_explored:
                self._check_and_mark_tile_interesting(x, y, tile)
        
        # Mark any entities at this position as explored using cache
        entity_id = self.entity_position_cache.get((x, y))
        if entity_id:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.explored = True
    
    def is_penumbra(self, x: int, y: int) -> bool:
        """Check if a position is currently in penumbra."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and getattr(tile, 'penumbra', False)
    
    def _calculate_world_lighting(self) -> None:
        """Calculate lighting from all active light sources in the world."""
        if not self.lighting_system:
            return
        
        # Get all world light sources
        world_lights = self.lighting_system.get_all_world_light_sources()
        
        for light_source in world_lights:
            cx = light_source['x']
            cy = light_source['y']
            brightness = light_source['brightness']
            
            # Calculate lighting for this light source
            self._calculate_lighting(cx, cy, brightness)
            
            # Calculate penumbra for this light source
            penumbra_radius = brightness * 2
            self._calculate_penumbra(cx, cy, brightness, penumbra_radius)
