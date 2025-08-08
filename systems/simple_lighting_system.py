"""
Optimized lighting and FOV system with caching for performance.

This system provides clean data to the renderer while maintaining high performance:
1. Light sources illuminate tiles (using cached shadowcasting)
2. Player has FOV (using shadowcasting or dark vision)
3. Renderer gets simple boolean flags: visible, lit, penumbra, explored
4. Aggressive caching to avoid redundant calculations

Performance optimizations:
- Shadowcasting result caching
- Early exit when nothing changed
- Distance culling for line-of-sight checks
- Incremental entity visibility updates
"""

from ecs.system import System
from components.core import Position, Player, Visible, Door
from components.items import LightEmitter, EquipmentSlots
from components.character import DarkVision
from typing import TYPE_CHECKING, Set, Tuple, Dict, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from game.level_world_gen import LevelWorldGenerator
from game.config import GameConfig


@dataclass
class RenderInfo:
    """Clean render information for a position."""
    visible: bool
    lit: bool
    penumbra: bool
    explored: bool


class SimpleLightingSystem(System):
    """
    Optimized lighting and FOV system that provides clean data to the renderer.
    
    Core principle: Keep it simple and predictable, but cache aggressively.
    """
    
    def __init__(self, world, world_generator: "LevelWorldGenerator", message_log=None):
        super().__init__(world)
        self.world_generator = world_generator
        self.message_log = message_log
        
        # Current state
        self.player_fov: Set[Tuple[int, int]] = set()
        self.lit_tiles: Set[Tuple[int, int]] = set()
        self.penumbra_tiles: Set[Tuple[int, int]] = set()
        
        # Performance optimization: caching
        self.shadowcast_cache: Dict[Tuple[int, int, int], Set[Tuple[int, int]]] = {}
        self.last_player_pos: Optional[Tuple[int, int]] = None
        self.last_light_sources: Optional[list] = None
        self.last_player_sight_radius: Optional[int] = None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Cache management
        self.max_cache_size = 1000  # Prevent memory leaks during long sessions
        self.cache_cleanup_counter = 0
        
        # Octant multipliers for shadowcasting
        self.octant_multipliers = [
            [1,  0,  0, -1, -1,  0,  0,  1],
            [0,  1, -1,  0,  0, -1,  1,  0],
            [0,  1,  1,  0,  0, -1, -1,  0],
            [1,  0,  0,  1, -1,  0,  0, -1]
        ]
    
    def update(self, dt: float = 0.0) -> None:
        """Update lighting and FOV."""
        player_entities = self.world.get_entities_with_components(Player, Position)
        
        for player_entity in player_entities:
            self._update_for_player(player_entity)
    
    def get_render_data(self) -> Dict[Tuple[int, int], RenderInfo]:
        """Get clean render data for the renderer."""
        render_data = {}
        
        # Get current level for exploration data
        current_level = self.world_generator.get_current_level()
        if not current_level:
            return render_data
        
        # Create render info for all tiles in player FOV
        for x, y in self.player_fov:
            tile = self.world_generator.get_tile_at(x, y)
            explored = tile.explored if tile else False
            
            render_data[(x, y)] = RenderInfo(
                visible=True,
                lit=(x, y) in self.lit_tiles,
                penumbra=(x, y) in self.penumbra_tiles,
                explored=explored
            )
        
        return render_data
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is currently visible to the player."""
        return (x, y) in self.player_fov
    
    def get_visible_positions(self) -> Set[Tuple[int, int]]:
        """Get all currently visible positions."""
        return self.player_fov.copy()
    
    def _update_for_player(self, player_entity: int) -> None:
        """Update lighting and FOV for a player."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        current_pos = (player_pos.x, player_pos.y)
        current_sight_radius = self._get_player_sight_radius(player_entity)
        current_light_sources = self._get_all_light_sources()
        
        # Performance optimization: Early exit if nothing changed
        if (self.last_player_pos == current_pos and 
            self.last_player_sight_radius == current_sight_radius and
            self.last_light_sources == current_light_sources):
            return
        
        # Update cache tracking
        self.last_player_pos = current_pos
        self.last_player_sight_radius = current_sight_radius
        self.last_light_sources = current_light_sources.copy()
        
        # Step 1: Calculate what tiles are lit by light sources
        self._calculate_lighting_cached()
        
        # Step 2: Calculate player FOV
        self._calculate_player_fov_cached(player_entity)
        
        # Step 3: Apply visibility to entities and handle exploration
        self._apply_entity_visibility()
        self._handle_exploration(player_entity)
    
    def _calculate_lighting(self) -> None:
        """Calculate which tiles are lit and which are in penumbra."""
        self.lit_tiles.clear()
        self.penumbra_tiles.clear()
        
        # Get all light sources
        light_sources = self._get_all_light_sources()
        
        # For each light source, calculate what it illuminates
        for light_source in light_sources:
            x, y, radius = light_source
            
            # Calculate lit tiles (normal radius)
            lit_positions = self._shadowcast_from_point(x, y, radius)
            self.lit_tiles.update(lit_positions)
            
            # Calculate penumbra tiles (2x radius, but exclude lit tiles)
            penumbra_positions = self._shadowcast_from_point(x, y, radius * 2)
            for pos in penumbra_positions:
                if pos not in self.lit_tiles:
                    self.penumbra_tiles.add(pos)
    
    def _calculate_player_fov(self, player_entity: int) -> None:
        """Calculate what the player can see."""
        self.player_fov.clear()
        
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Always see current tile
        self.player_fov.add((player_pos.x, player_pos.y))
        
        # Get effective sight radius
        sight_radius = self._get_player_sight_radius(player_entity)
        
        if sight_radius == 0:
            # No vision beyond current tile, but still check for visible lit tiles
            pass
        elif sight_radius == 1:
            # Dark vision level 1 - see adjacent tiles
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    x, y = player_pos.x + dx, player_pos.y + dy
                    if GameConfig.is_valid_position(x, y):
                        self.player_fov.add((x, y))
        else:
            # Normal shadowcasting
            fov_positions = self._shadowcast_from_point(player_pos.x, player_pos.y, sight_radius)
            self.player_fov.update(fov_positions)
        
        # IMPORTANT: Always add any lit or penumbra tiles that player has line of sight to
        # This allows seeing distant light sources even when player has no light
        self._add_visible_lit_tiles(player_pos.x, player_pos.y)
    
    def _add_visible_lit_tiles(self, player_x: int, player_y: int) -> None:
        """Add lit/penumbra tiles that the player has line of sight to."""
        # Check all lit and penumbra tiles
        all_lit_tiles = self.lit_tiles | self.penumbra_tiles
        
        for x, y in all_lit_tiles:
            if self._has_line_of_sight(player_x, player_y, x, y):
                self.player_fov.add((x, y))
    
    def _get_all_light_sources(self) -> list:
        """Get all light sources as (x, y, radius) tuples."""
        light_sources = []
        
        # Get player's equipped light
        player_entities = self.world.get_entities_with_components(Player, Position)
        for player_entity in player_entities:
            player_pos = self.world.get_component(player_entity, Position)
            if player_pos:
                radius = self._get_player_equipped_light_radius(player_entity)
                if radius > 0:
                    light_sources.append((player_pos.x, player_pos.y, radius))
        
        # Get world light sources (items on ground)
        light_entities = self.world.get_entities_with_components(LightEmitter, Position)
        for entity_id in light_entities:
            light = self.world.get_component(entity_id, LightEmitter)
            position = self.world.get_component(entity_id, Position)
            
            if light and position and light.active:
                light_sources.append((position.x, position.y, light.brightness))
        
        # Get equipped lights on NPCs
        entities_with_equipment = self.world.get_entities_with_components(EquipmentSlots, Position)
        for entity_id in entities_with_equipment:
            # Skip players (already handled)
            if self.world.has_component(entity_id, Player):
                continue
                
            equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
            position = self.world.get_component(entity_id, Position)
            
            if equipment_slots and position and equipment_slots.accessory:
                light = self.world.get_component(equipment_slots.accessory, LightEmitter)
                if light and light.active:
                    light_sources.append((position.x, position.y, light.brightness))
        
        return light_sources
    
    def _get_player_sight_radius(self, player_entity: int) -> int:
        """Get player's effective sight radius (light or dark vision)."""
        # Check for equipped light first
        light_radius = self._get_player_equipped_light_radius(player_entity)
        if light_radius > 0:
            return light_radius
        
        # No light - check dark vision
        dark_vision = self.world.get_component(player_entity, DarkVision)
        if dark_vision:
            return dark_vision.radius
        
        # No light, no dark vision
        return 0
    
    def _get_player_equipped_light_radius(self, player_entity: int) -> int:
        """Get radius from player's equipped light sources."""
        equipment_slots = self.world.get_component(player_entity, EquipmentSlots)
        if not equipment_slots:
            return 0
        
        total_brightness = 0
        
        # Check accessory slot
        if equipment_slots.accessory:
            light = self.world.get_component(equipment_slots.accessory, LightEmitter)
            if light and light.active:
                total_brightness += light.brightness
        
        return total_brightness
    
    def _shadowcast_from_point(self, cx: int, cy: int, radius: int) -> Set[Tuple[int, int]]:
        """Calculate visible positions from a point using shadowcasting."""
        visible = set()
        visible.add((cx, cy))  # Source position is always visible
        
        # Cast shadows in all 8 octants
        for octant in range(8):
            self._cast_shadow(cx, cy, 1, 1.0, 0.0, radius, visible,
                            self.octant_multipliers[0][octant],
                            self.octant_multipliers[1][octant],
                            self.octant_multipliers[2][octant],
                            self.octant_multipliers[3][octant])
        
        return visible
    
    def _cast_shadow(self, cx: int, cy: int, row: int, start: float, end: float,
                    radius: int, visible: Set[Tuple[int, int]],
                    xx: int, xy: int, yx: int, yy: int) -> None:
        """Recursive shadowcasting algorithm."""
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
                
                # Transform coordinates
                mx = cx + dx * xx + dy * xy
                my = cy + dx * yx + dy * yy
                
                # Calculate slopes
                l_slope = (dx - 0.5) / (dy + 0.5)
                r_slope = (dx + 0.5) / (dy - 0.5)
                
                # Skip if outside cone
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                
                # Check if within radius
                if dx * dx + dy * dy <= radius_squared:
                    visible.add((mx, my))
                
                if blocked:
                    # In shadow
                    if self._is_wall(mx, my):
                        new_start = r_slope
                        continue
                    else:
                        blocked = False
                        start = new_start
                else:
                    # In light
                    if self._is_wall(mx, my) and j < radius:
                        blocked = True
                        self._cast_shadow(cx, cy, j + 1, start, l_slope, radius, visible,
                                        xx, xy, yx, yy)
                        new_start = r_slope
            
            if blocked:
                break
    
    def _has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check line of sight using Bresenham's algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        x, y = x1, y1
        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1
        error = dx - dy
        
        while True:
            # Check for walls (skip start and end points)
            if (x, y) != (x1, y1) and (x, y) != (x2, y2):
                if self._is_wall(x, y):
                    return False
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc
        
        return True
    
    def _is_wall(self, x: int, y: int) -> bool:
        """Check if position blocks line of sight."""
        # Terrain walls
        if self.world_generator.is_wall_at(x, y):
            return True
        
        # Closed doors
        door_entities = self.world.get_entities_with_components(Position, Door)
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            door = self.world.get_component(entity_id, Door)
            
            if position and door and position.x == x and position.y == y:
                return not door.is_open
        
        return False
    
    def _apply_entity_visibility(self) -> None:
        """Apply visibility to entities based on FOV (optimized)."""
        # Performance optimization: Only update entities that have changed visibility
        
        # Get all entities with position and visibility
        entities_with_visibility = self.world.get_entities_with_components(Position, Visible)
        
        for entity_id in entities_with_visibility:
            position = self.world.get_component(entity_id, Position)
            visible = self.world.get_component(entity_id, Visible)
            
            if not position or not visible:
                continue
            
            # Check if entity should be visible
            should_be_visible = (position.x, position.y) in self.player_fov
            
            # Only update if visibility changed
            if visible.visible != should_be_visible:
                visible.visible = should_be_visible
                
                # Update last seen info if now visible
                if should_be_visible:
                    from components.core import Renderable
                    renderable = self.world.get_component(entity_id, Renderable)
                    if renderable:
                        visible.last_seen_x = position.x
                        visible.last_seen_y = position.y
                        visible.last_seen_char = renderable.char
                        visible.last_seen_color = renderable.color
    
    def _handle_exploration(self, player_entity: int) -> None:
        """Handle tile exploration."""
        for x, y in self.player_fov:
            tile = self.world_generator.get_tile_at(x, y)
            if tile and not tile.explored:
                # Check if tile should be explored
                should_explore = self._should_explore_tile(x, y, player_entity)
                
                if should_explore:
                    tile.explored = True
                    self._check_for_interesting_discoveries(x, y, tile)
    
    def _should_explore_tile(self, x: int, y: int, player_entity: int) -> bool:
        """Check if tile should be explored."""
        # If lit or in penumbra, always explore
        if (x, y) in self.lit_tiles or (x, y) in self.penumbra_tiles:
            return True
        
        # Not lit - check if using dark vision
        light_radius = self._get_player_equipped_light_radius(player_entity)
        if light_radius > 0:
            # Has light source, so not dark vision
            return False
        
        # No light source - using dark vision, so explore
        return True
    
    def _check_for_interesting_discoveries(self, x: int, y: int, tile) -> None:
        """Check for interesting discoveries and interrupt auto-explore."""
        from components.items import Item, Pickupable
        from components.auto_explore import AutoExplore
        
        # Check for interesting things
        has_stairs = self.world_generator.is_stairs_at(x, y) is not None
        
        has_items = False
        item_entities = self.world.get_entities_with_components(Position, Item, Pickupable)
        for entity_id in item_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                has_items = True
                break
        
        has_door = False
        door_entities = self.world.get_entities_with_components(Position, Door)
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            door = self.world.get_component(entity_id, Door)
            if position and door and position.x == x and position.y == y and not door.is_open:
                has_door = True
                break
        
        if has_stairs or has_items or has_door:
            tile.interesting = True
            
            # Interrupt auto-explore
            player_entities = self.world.get_entities_with_components(Player, Position, AutoExplore)
            for player_entity in player_entities:
                auto_explore = self.world.get_component(player_entity, AutoExplore)
                if auto_explore and auto_explore.is_active():
                    discovery_type = "stairs" if has_stairs else ("item" if has_items else "door")
                    auto_explore.interrupt(f"Discovered {discovery_type}")
                    
                    if self.message_log:
                        self.message_log.add_warning(f"Auto-explore interrupted - discovered {discovery_type}!")
    
    def _calculate_lighting_cached(self) -> None:
        """Calculate which tiles are lit and which are in penumbra (with caching)."""
        self.lit_tiles.clear()
        self.penumbra_tiles.clear()
        
        # Get all light sources
        light_sources = self._get_all_light_sources()
        
        # For each light source, calculate what it illuminates
        for light_source in light_sources:
            x, y, radius = light_source
            
            # Calculate lit tiles (normal radius) - use cache
            cache_key = (x, y, radius)
            if cache_key in self.shadowcast_cache:
                lit_positions = self.shadowcast_cache[cache_key]
                self.cache_hits += 1
            else:
                lit_positions = self._shadowcast_from_point(x, y, radius)
                self._add_to_cache(cache_key, lit_positions)
                self.cache_misses += 1
            
            self.lit_tiles.update(lit_positions)
            
            # Calculate penumbra tiles (2x radius) - use cache
            penumbra_cache_key = (x, y, radius * 2)
            if penumbra_cache_key in self.shadowcast_cache:
                penumbra_positions = self.shadowcast_cache[penumbra_cache_key]
                self.cache_hits += 1
            else:
                penumbra_positions = self._shadowcast_from_point(x, y, radius * 2)
                self._add_to_cache(penumbra_cache_key, penumbra_positions)
                self.cache_misses += 1
            
            for pos in penumbra_positions:
                if pos not in self.lit_tiles:
                    self.penumbra_tiles.add(pos)
    
    def _calculate_player_fov_cached(self, player_entity: int) -> None:
        """Calculate what the player can see (with caching)."""
        self.player_fov.clear()
        
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return
        
        # Always see current tile
        self.player_fov.add((player_pos.x, player_pos.y))
        
        # Get effective sight radius
        sight_radius = self._get_player_sight_radius(player_entity)
        
        if sight_radius == 0:
            # No vision beyond current tile, but still check for visible lit tiles
            pass
        elif sight_radius == 1:
            # Dark vision level 1 - see adjacent tiles
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    x, y = player_pos.x + dx, player_pos.y + dy
                    if GameConfig.is_valid_position(x, y):
                        self.player_fov.add((x, y))
        else:
            # Normal shadowcasting - use cache
            cache_key = (player_pos.x, player_pos.y, sight_radius)
            if cache_key in self.shadowcast_cache:
                fov_positions = self.shadowcast_cache[cache_key]
                self.cache_hits += 1
            else:
                fov_positions = self._shadowcast_from_point(player_pos.x, player_pos.y, sight_radius)
                self.shadowcast_cache[cache_key] = fov_positions
                self.cache_misses += 1
            
            self.player_fov.update(fov_positions)
        
        # IMPORTANT: Always add any lit or penumbra tiles that player has line of sight to
        # This allows seeing distant light sources even when player has no light
        self._add_visible_lit_tiles_optimized(player_pos.x, player_pos.y)
    
    def _add_visible_lit_tiles_optimized(self, player_x: int, player_y: int) -> None:
        """Add lit/penumbra tiles that the player has line of sight to (optimized)."""
        # Check all lit and penumbra tiles with distance culling
        all_lit_tiles = self.lit_tiles | self.penumbra_tiles
        
        # Performance optimization: Only check tiles within reasonable distance
        MAX_SIGHT_DISTANCE = 20  # Reasonable maximum for line-of-sight checks
        
        for x, y in all_lit_tiles:
            # Distance culling - skip very distant tiles
            distance_squared = (x - player_x) ** 2 + (y - player_y) ** 2
            if distance_squared > MAX_SIGHT_DISTANCE ** 2:
                continue
            
            if self._has_line_of_sight(player_x, player_y, x, y):
                self.player_fov.add((x, y))
    
    def force_recalculation(self) -> None:
        """Force recalculation on next update."""
        # Clear cache to force recalculation
        self.shadowcast_cache.clear()
        self.last_player_pos = None
        self.last_light_sources = None
        self.last_player_sight_radius = None
        
        player_entities = self.world.get_entities_with_components(Player, Position)
        for player_entity in player_entities:
            self._update_for_player(player_entity)
    
    def _add_to_cache(self, cache_key: Tuple[int, int, int], positions: Set[Tuple[int, int]]) -> None:
        """Add shadowcasting result to cache with size management."""
        # Check if cache is getting too large
        if len(self.shadowcast_cache) >= self.max_cache_size:
            # Remove oldest 25% of cache entries
            keys_to_remove = list(self.shadowcast_cache.keys())[:self.max_cache_size // 4]
            for key in keys_to_remove:
                del self.shadowcast_cache[key]
        
        self.shadowcast_cache[cache_key] = positions
    
    def get_cache_stats(self) -> Tuple[int, int]:
        """Get cache performance statistics (hits, misses)."""
        return self.cache_hits, self.cache_misses
