"""
Unified FOV and Lighting system that eliminates race conditions and phantom lighting.

This system replaces both SimpleFOVSystem and LightingSystem with a single,
atomic calculation that produces clean render data and world lighting data.

Key principles:
1. Single source of truth - one system calculates both FOV and lighting
2. Dual output - world lighting (for game logic) and render data (for display)
3. No tile state mutation - never touches tile objects directly
4. Clean data flow - this system -> renderer -> display
"""

from ecs.system import System
from components.core import Position, Player, Visible, Door
from components.corpse import Corpse
from components.items import LightEmitter, EquipmentSlots
from typing import TYPE_CHECKING, Set, Tuple, Dict, NamedTuple
from dataclasses import dataclass

if TYPE_CHECKING:
    from game.level_world_gen import LevelWorldGenerator
from game.config import GameConfig


@dataclass
class LightInfo:
    """Information about lighting at a position for game logic."""
    brightness: int
    source_positions: Set[Tuple[int, int]]


@dataclass
class RenderInfo:
    """Clean render information for a position."""
    visible: bool
    lit: bool
    penumbra: bool
    explored: bool


class UnifiedFOVLightingSystem(System):
    """
    Unified system that calculates both FOV and lighting atomically.
    
    Produces two outputs:
    1. World lighting data - for NPCs and game logic
    2. Render data - for the renderer (intersection of FOV + lighting)
    """
    
    def __init__(self, world, world_generator: "LevelWorldGenerator", sight_radius: int = None, 
                 message_log=None):
        super().__init__(world)
        self.world_generator = world_generator
        self.sight_radius = sight_radius if sight_radius is not None else GameConfig.PLAYER_SIGHT_RADIUS
        self.message_log = message_log
        
        # World lighting data (for game logic - full map)
        self.world_lighting: Dict[Tuple[int, int], LightInfo] = {}
        
        # Render data (for display - FOV intersection with lighting)
        self.render_data: Dict[Tuple[int, int], RenderInfo] = {}
        
        # Current player FOV (for quick lookups)
        self.player_fov: Set[Tuple[int, int]] = set()
        
        # Shadowcasting cache for performance
        self.light_cache: Dict[Tuple[int, int, int, int], Set[Tuple[int, int]]] = {}
        self.map_version = 0  # Increment when walls/doors change
        self.max_cache_size = 100  # Prevent memory bloat
        
        # Track static vs mobile light sources
        self.static_light_sources: Set[Tuple[int, int, int]] = set()  # (x, y, radius)
        
        # Octant multipliers for shadowcasting
        self.octant_multipliers = [
            [1,  0,  0, -1, -1,  0,  0,  1],
            [0,  1, -1,  0,  0, -1,  1,  0],
            [0,  1,  1,  0,  0, -1, -1,  0],
            [1,  0,  0,  1, -1,  0,  0, -1]
        ]
    
    def update(self, dt: float = 0.0) -> None:
        """Update both world lighting and render data atomically."""
        player_entities = self.world.get_entities_with_components(Player, Position)
        
        for player_entity in player_entities:
            self._calculate_unified_data(player_entity)
    
    def get_render_data(self) -> Dict[Tuple[int, int], RenderInfo]:
        """Get clean render data for the renderer."""
        return self.render_data.copy()
    
    def get_world_lighting(self) -> Dict[Tuple[int, int], LightInfo]:
        """Get world lighting data for game logic."""
        return self.world_lighting.copy()
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is currently visible to the player."""
        return (x, y) in self.player_fov
    
    def is_lit(self, x: int, y: int) -> bool:
        """Check if a position is currently lit (in world lighting)."""
        return (x, y) in self.world_lighting
    
    def get_visible_positions(self) -> Set[Tuple[int, int]]:
        """Get all currently visible positions (for compatibility)."""
        return self.player_fov.copy()
    
    def _calculate_unified_data(self, player_entity: int) -> None:
        """Calculate both world lighting and render data atomically."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Step 1: Calculate world lighting (full map) for game logic
        self._calculate_world_lighting(player_entity)
        
        # Step 2: Calculate player FOV
        self._calculate_player_fov(player_entity)
        
        # Step 3: Create render data (intersection of world lighting + player FOV)
        self._create_render_data()
        
        # Step 4: Apply visibility to entities and handle exploration
        self._apply_entity_visibility()
        self._handle_exploration()
    
    def _calculate_world_lighting(self, player_entity: int) -> None:
        """Calculate lighting for the entire world (for game logic)."""
        self.world_lighting.clear()
        
        # Get all light sources in the world
        light_sources = self._get_all_light_sources(player_entity)
        
        # Calculate lighting from each source
        for light_source in light_sources:
            self._add_world_light_source(
                light_source['x'], 
                light_source['y'], 
                light_source['brightness']
            )
    
    def _calculate_player_fov(self, player_entity: int) -> None:
        """Calculate field of view for the player using shadowcasting."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Clear previous FOV
        self.player_fov.clear()
        self.player_fov.add((player_pos.x, player_pos.y))
        
        # Cast shadows in all 8 octants
        for octant in range(8):
            self._cast_light(player_pos.x, player_pos.y, 1, 1.0, 0.0, 
                           self.octant_multipliers[0][octant],
                           self.octant_multipliers[1][octant],
                           self.octant_multipliers[2][octant],
                           self.octant_multipliers[3][octant])
    
    def _create_render_data(self) -> None:
        """Create render data as intersection of world lighting and player FOV."""
        self.render_data.clear()
        
        # Get current level for exploration data
        current_level = self.world_generator.get_current_level()
        if not current_level:
            return
        
        # For each position in player FOV, determine render state
        for x, y in self.player_fov:
            # Get tile for exploration status
            tile = self.world_generator.get_tile_at(x, y)
            explored = tile.explored if tile else False
            
            # Check lighting state
            light_info = self.world_lighting.get((x, y))
            if light_info:
                # Position is lit
                lit = True
                penumbra = False
            else:
                # Check if in penumbra (2x radius of any light source)
                penumbra = self._is_in_penumbra(x, y)
                lit = False
            
            # Create render info
            self.render_data[(x, y)] = RenderInfo(
                visible=True,  # Everything in FOV is visible
                lit=lit,
                penumbra=penumbra,
                explored=explored
            )
    
    def _get_all_light_sources(self, player_entity: int) -> list:
        """Get all active light sources in the world."""
        light_sources = []
        
        # Get player's equipped light
        player_pos = self.world.get_component(player_entity, Position)
        if player_pos:
            player_light_radius = self._get_player_equipped_light_radius(player_entity)
            if player_light_radius > 0:
                light_sources.append({
                    'entity_id': player_entity,
                    'x': player_pos.x,
                    'y': player_pos.y,
                    'brightness': player_light_radius
                })
        
        # Get world light sources (items with Position + LightEmitter)
        light_entities = self.world.get_entities_with_components(LightEmitter, Position)
        for entity_id in light_entities:
            light = self.world.get_component(entity_id, LightEmitter)
            position = self.world.get_component(entity_id, Position)
            
            if light and position and light.active:
                light_sources.append({
                    'entity_id': entity_id,
                    'x': position.x,
                    'y': position.y,
                    'brightness': light.brightness
                })
        
        # Get equipped lights on NPCs/entities
        entities_with_equipment = self.world.get_entities_with_components(EquipmentSlots, Position)
        for entity_id in entities_with_equipment:
            # Skip player (already handled above)
            if entity_id == player_entity:
                continue
                
            equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
            position = self.world.get_component(entity_id, Position)
            
            if equipment_slots and position and equipment_slots.accessory:
                light = self.world.get_component(equipment_slots.accessory, LightEmitter)
                if light and light.active:
                    light_sources.append({
                        'entity_id': equipment_slots.accessory,
                        'x': position.x,
                        'y': position.y,
                        'brightness': light.brightness
                    })
        
        return light_sources
    
    def _get_player_equipped_light_radius(self, player_entity_id: int) -> int:
        """Get the light radius for a player based only on equipped light sources."""
        equipment_slots = self.world.get_component(player_entity_id, EquipmentSlots)
        if not equipment_slots:
            return 0
        
        total_brightness = 0
        
        # Check accessory slot for light sources
        if equipment_slots.accessory:
            light = self.world.get_component(equipment_slots.accessory, LightEmitter)
            if light and light.active:
                total_brightness += light.brightness
        
        return total_brightness
    
    def _add_world_light_source(self, cx: int, cy: int, radius: int) -> None:
        """Add lighting from a single light source with proper shadow casting."""
        # Calculate which positions this light can actually illuminate using shadowcasting
        lit_positions = self._calculate_light_shadowcasting(cx, cy, radius)
        
        # Add lit positions to world lighting
        for x, y in lit_positions:
            pos = (x, y)
            if pos not in self.world_lighting:
                self.world_lighting[pos] = LightInfo(
                    brightness=radius,
                    source_positions={(cx, cy)}
                )
            else:
                # Combine with existing light
                existing = self.world_lighting[pos]
                existing.brightness = max(existing.brightness, radius)
                existing.source_positions.add((cx, cy))
    
    def _is_in_penumbra(self, x: int, y: int) -> bool:
        """Check if a position is in penumbra (2x radius of any light source with shadowcasting)."""
        # Get all light sources from the player entity (we need this to get the original sources)
        player_entities = self.world.get_entities_with_components(Player, Position)
        if not player_entities:
            return False
        
        player_entity = list(player_entities)[0]
        light_sources = self._get_all_light_sources(player_entity)
        
        for light_source in light_sources:
            # Calculate penumbra using shadowcasting with 2x radius
            penumbra_radius = light_source['brightness'] * 2
            penumbra_positions = self._calculate_light_shadowcasting(
                light_source['x'], 
                light_source['y'], 
                penumbra_radius
            )
            
            # Check if this position is in penumbra (within 2x radius but not in main light)
            if (x, y) in penumbra_positions:
                # Make sure it's not already lit (penumbra is only for areas outside main light)
                light_positions = self._calculate_light_shadowcasting(
                    light_source['x'], 
                    light_source['y'], 
                    light_source['brightness']
                )
                if (x, y) not in light_positions:
                    return True
        
        return False
    
    def _calculate_light_shadowcasting(self, cx: int, cy: int, radius: int) -> Set[Tuple[int, int]]:
        """Calculate which positions a light source can illuminate using shadowcasting with caching."""
        # Check cache first
        cache_key = (cx, cy, radius, self.map_version)
        if cache_key in self.light_cache:
            return self.light_cache[cache_key].copy()  # Cache hit!
        
        # Cache miss - calculate shadowcasting
        lit_positions = set()
        lit_positions.add((cx, cy))  # Light source position is always lit
        
        # Cast shadows in all 8 octants
        for octant in range(8):
            self._cast_light_for_source(cx, cy, 1, 1.0, 0.0, radius, lit_positions,
                                      self.octant_multipliers[0][octant],
                                      self.octant_multipliers[1][octant],
                                      self.octant_multipliers[2][octant],
                                      self.octant_multipliers[3][octant])
        
        # Store in cache (with size limit)
        if len(self.light_cache) >= self.max_cache_size:
            # Remove oldest entries (simple FIFO for now)
            oldest_key = next(iter(self.light_cache))
            del self.light_cache[oldest_key]
        
        self.light_cache[cache_key] = lit_positions.copy()
        return lit_positions
    
    def _cast_light_for_source(self, cx: int, cy: int, row: int, start: float, end: float,
                              radius: int, lit_positions: Set[Tuple[int, int]],
                              xx: int, xy: int, yx: int, yy: int) -> None:
        """Recursive shadowcasting algorithm for individual light sources."""
        if start < end:
            return
        
        radius_squared = radius * radius
        new_start = 0.0
        
        for j in range(row, radius + 1):
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
                
                # Check if within light radius
                if dx * dx + dy * dy <= radius_squared:
                    lit_positions.add((mx, my))
                
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
                    if self._is_wall(mx, my) and j < radius:
                        # Hit a wall, cast shadow
                        blocked = True
                        self._cast_light_for_source(cx, cy, j + 1, start, l_slope, radius, lit_positions,
                                                  xx, xy, yx, yy)
                        new_start = r_slope
            
            # If we ended the row blocked, we're done
            if blocked:
                break
    
    def _cast_light(self, cx: int, cy: int, row: int, start: float, end: float,
                   xx: int, xy: int, yx: int, yy: int) -> None:
        """Recursive shadowcasting algorithm for player FOV."""
        if start < end:
            return
        
        radius_squared = self.sight_radius * self.sight_radius
        new_start = 0.0
        
        for j in range(row, self.sight_radius + 1):
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
                    self.player_fov.add((mx, my))
                
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
                    if self._is_wall(mx, my) and j < self.sight_radius:
                        # Hit a wall, cast shadow
                        blocked = True
                        self._cast_light(cx, cy, j + 1, start, l_slope,
                                       xx, xy, yx, yy)
                        new_start = r_slope
            
            # If we ended the row blocked, we're done
            if blocked:
                break
    
    def _is_wall(self, x: int, y: int) -> bool:
        """Check if a position blocks line of sight (reused from SimpleFOVSystem)."""
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
    
    def _apply_entity_visibility(self) -> None:
        """Apply visibility to entities based on FOV."""
        # Clear all entity visibility first
        visible_entities = self.world.get_entities_with_components(Visible)
        for entity_id in visible_entities:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.visible = False
        
        # Build entity position cache for fast lookup
        entity_position_cache = {}
        entities = self.world.get_entities_with_components(Position)
        for entity_id in entities:
            position = self.world.get_component(entity_id, Position)
            if position:
                entity_position_cache[(position.x, position.y)] = entity_id
        
        # Apply visibility to entities in FOV
        for x, y in self.player_fov:
            entity_id = entity_position_cache.get((x, y))
            if entity_id:
                visible = self.world.get_component(entity_id, Visible)
                if visible:
                    visible.visible = True
                    # Update last seen information
                    from components.core import Renderable
                    renderable = self.world.get_component(entity_id, Renderable)
                    if renderable:
                        visible.last_seen_x = x
                        visible.last_seen_y = y
                        visible.last_seen_char = renderable.char
                        visible.last_seen_color = renderable.color
    
    def _handle_exploration(self) -> None:
        """Handle tile exploration and interesting discoveries."""
        for x, y in self.player_fov:
            tile = self.world_generator.get_tile_at(x, y)
            if tile and not tile.explored:
                # Only mark as explored if the tile has some level of lighting
                light_info = self.world_lighting.get((x, y))
                is_lit = light_info is not None
                is_penumbra = self._is_in_penumbra(x, y) if not is_lit else False
                
                # Mark as explored only if lit or in penumbra
                if is_lit or is_penumbra:
                    tile.explored = True
                    self._check_and_mark_tile_interesting(x, y, tile)
    
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
    
    def force_recalculation(self) -> None:
        """Force a recalculation of FOV and lighting on the next update."""
        # For the unified system, we just trigger an immediate update
        player_entities = self.world.get_entities_with_components(Player, Position)
        for player_entity in player_entities:
            self._calculate_unified_data(player_entity)
    
    def invalidate_light_cache(self) -> None:
        """Invalidate the light cache when the map changes (doors, walls, etc.)."""
        self.map_version += 1
        # Optionally clear the cache entirely for immediate effect
        # self.light_cache.clear()
    
    def clear_light_cache(self) -> None:
        """Clear the entire light cache (for debugging or major map changes)."""
        self.light_cache.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for debugging/monitoring."""
        return {
            'cache_size': len(self.light_cache),
            'max_cache_size': self.max_cache_size,
            'map_version': self.map_version
        }
