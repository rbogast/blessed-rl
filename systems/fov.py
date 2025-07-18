"""
Field of View system using recursive shadowcasting.
"""

from ecs.system import System
from components.core import Position, Player, Visible, Door
from components.corpse import Corpse
from game.worldgen.core import WorldGenerator
from game.config import GameConfig
import math


class FOVSystem(System):
    """Implements recursive shadowcasting for field of view calculation."""
    
    def __init__(self, world, world_generator: WorldGenerator, sight_radius: int = None):
        super().__init__(world)
        self.world_generator = world_generator
        self.sight_radius = sight_radius if sight_radius is not None else GameConfig.PLAYER_SIGHT_RADIUS
        self.last_player_pos = None  # Cache last position to avoid unnecessary recalculation
        
        # Octant multipliers for the 8 directions
        self.octant_multipliers = [
            [1,  0,  0, -1, -1,  0,  0,  1],
            [0,  1, -1,  0,  0, -1,  1,  0],
            [0,  1,  1,  0,  0, -1, -1,  0],
            [1,  0,  0,  1, -1,  0,  0, -1]
        ]
    
    def update(self, dt: float = 0.0) -> None:
        """Update FOV for all player entities only if they moved."""
        player_entities = self.world.get_entities_with_components(Player, Position)
        
        for player_entity in player_entities:
            player_pos = self.world.get_component(player_entity, Position)
            if not player_pos:
                continue
                
            # Only recalculate if player moved
            current_pos = (player_pos.x, player_pos.y)
            if self.last_player_pos != current_pos:
                self._calculate_fov(player_entity)
                self.last_player_pos = current_pos
    
    def _calculate_fov(self, player_entity: int) -> None:
        """Calculate field of view for a player entity."""
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
        
        # Mark player tile as visible
        player_tile = self.world_generator.get_tile_at(player_pos.x, player_pos.y)
        if player_tile:
            player_tile.visible = True
            player_tile.explored = True
        
        # Cast shadows in all 8 octants
        for octant in range(8):
            self._cast_light(player_pos.x, player_pos.y, 1, 1.0, 0.0, 
                           self.octant_multipliers[0][octant],
                           self.octant_multipliers[1][octant],
                           self.octant_multipliers[2][octant],
                           self.octant_multipliers[3][octant])
    
    def _cast_light(self, cx: int, cy: int, row: int, start: float, end: float,
                   xx: int, xy: int, yx: int, yy: int) -> None:
        """Recursive shadowcasting algorithm."""
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
                    if self._is_wall(mx, my) and j < self.sight_radius:
                        # Hit a wall, cast shadow
                        blocked = True
                        self._cast_light(cx, cy, j + 1, start, l_slope,
                                       xx, xy, yx, yy)
                        new_start = r_slope
            
            # If we ended the row blocked, we're done
            if blocked:
                break
    
    def _clear_tile_visibility(self, player_x: int, player_y: int) -> None:
        """Clear tile visibility in a radius around the player."""
        for x in range(player_x - self.sight_radius, player_x + self.sight_radius + 1):
            for y in range(player_y - self.sight_radius, player_y + self.sight_radius + 1):
                tile = self.world_generator.get_tile_at(x, y)
                if tile:
                    tile.visible = False
    
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
        """Mark a position as visible and explored."""
        # Mark the tile as explored in the world generator
        tile = self.world_generator.get_tile_at(x, y)
        if tile:
            tile.visible = True
            tile.explored = True
        
        # Mark any entities at this position as visible using cache
        entity_id = self.entity_position_cache.get((x, y))
        if entity_id:
            visible = self.world.get_component(entity_id, Visible)
            if visible:
                visible.visible = True
                visible.explored = True
    
    def is_visible(self, x: int, y: int) -> bool:
        """Check if a position is currently visible."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and tile.visible
    
    def is_explored(self, x: int, y: int) -> bool:
        """Check if a position has been explored."""
        tile = self.world_generator.get_tile_at(x, y)
        return tile and tile.explored
