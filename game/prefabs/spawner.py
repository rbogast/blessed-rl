"""
Prefab spawner for placing prefab structures in the world.
"""

import random
from typing import List, Optional, Tuple, Set
from components.core import Position, Renderable, Blocking, Visible, Door, Prefab
from game.glyph_config import GlyphConfig
from .loader import PrefabDefinition


class PrefabSpawner:
    """Handles spawning prefab structures in chunks."""
    
    def __init__(self, world, world_generator, glyph_config: GlyphConfig = None):
        self.world = world
        self.world_generator = world_generator
        self.glyph_config = glyph_config or GlyphConfig()
    
    def try_spawn_prefab(self, prefab: PrefabDefinition, chunk_id: int, rng: random.Random) -> bool:
        """Attempt to spawn a prefab in the given chunk."""
        chunk = self.world_generator.get_chunk(chunk_id)
        if not chunk:
            return False
        
        # Find a valid spawn position
        spawn_pos = self._find_spawn_position(prefab, chunk, rng)
        if not spawn_pos:
            return False
        
        local_x, local_y = spawn_pos
        
        # Check if the area is clear
        if not self._is_area_clear(prefab, chunk, local_x, local_y):
            return False
        
        # Spawn the prefab
        self._place_prefab(prefab, chunk, local_x, local_y)
        return True
    
    def _find_spawn_position(self, prefab: PrefabDefinition, chunk, rng: random.Random) -> Optional[Tuple[int, int]]:
        """Find a valid position to spawn the prefab within the chunk."""
        # Calculate valid spawn area considering edge distance
        min_x = prefab.min_distance_from_edge
        min_y = prefab.min_distance_from_edge
        max_x = chunk.width - prefab.width - prefab.min_distance_from_edge
        max_y = chunk.height - prefab.height - prefab.min_distance_from_edge
        
        if max_x < min_x or max_y < min_y:
            return None  # Prefab too large for chunk
        
        # Try multiple random positions
        attempts = 20
        for _ in range(attempts):
            local_x = rng.randint(min_x, max_x)
            local_y = rng.randint(min_y, max_y)
            
            # Check if this position works
            if self._is_position_valid(prefab, chunk, local_x, local_y):
                return local_x, local_y
        
        return None
    
    def _is_position_valid(self, prefab: PrefabDefinition, chunk, local_x: int, local_y: int) -> bool:
        """Check if a position is valid for spawning the prefab."""
        # Check if the area has enough open space
        open_tiles = 0
        total_tiles = prefab.width * prefab.height
        
        for py in range(prefab.height):
            for px in range(prefab.width):
                tile_x = local_x + px
                tile_y = local_y + py
                
                if not chunk.is_wall(tile_x, tile_y):
                    open_tiles += 1
        
        # Require at least 60% open space for placement
        return (open_tiles / total_tiles) >= 0.6
    
    def _is_area_clear(self, prefab: PrefabDefinition, chunk, local_x: int, local_y: int) -> bool:
        """Check if the area is clear of entities (except walls that will be replaced)."""
        for py in range(prefab.height):
            for px in range(prefab.width):
                global_x = chunk.chunk_id * chunk.width + local_x + px
                global_y = local_y + py
                
                # Check for existing entities at this position
                entities_at_pos = self._get_entities_at_position(global_x, global_y)
                
                # Allow wall entities to be replaced, but not other entities
                for entity_id in entities_at_pos:
                    if not self._is_wall_entity(entity_id):
                        return False
        
        return True
    
    def _get_entities_at_position(self, global_x: int, global_y: int) -> List[int]:
        """Get all entities at a specific global position."""
        entities = []
        entities_with_position = self.world.get_entities_with_components(Position)
        
        for entity_id in entities_with_position:
            pos = self.world.get_component(entity_id, Position)
            if pos and pos.x == global_x and pos.y == global_y:
                entities.append(entity_id)
        
        return entities
    
    def _is_wall_entity(self, entity_id: int) -> bool:
        """Check if an entity is a wall entity (can be replaced)."""
        # Wall entities have Blocking and Renderable but no other special components
        has_blocking = self.world.has_component(entity_id, Blocking)
        has_renderable = self.world.has_component(entity_id, Renderable)
        has_door = self.world.has_component(entity_id, Door)
        has_prefab = self.world.has_component(entity_id, Prefab)
        
        # It's a wall if it has blocking and renderable, but no door or prefab components
        return has_blocking and has_renderable and not has_door and not has_prefab
    
    def _place_prefab(self, prefab: PrefabDefinition, chunk, local_x: int, local_y: int) -> None:
        """Place the prefab at the specified position."""
        # Remove existing wall entities in the area
        self._clear_area(prefab, chunk, local_x, local_y)
        
        # Place prefab tiles and entities
        for py, row in enumerate(prefab.layout):
            for px, char in enumerate(row):
                if char == ' ':  # Ignore character - don't modify terrain
                    continue
                
                global_x = chunk.chunk_id * chunk.width + local_x + px
                global_y = local_y + py
                
                # Get tile type from legend
                tile_type = prefab.legend.get(char, 'floor')
                
                # Update the tile in the chunk
                tile = chunk.get_tile(local_x + px, local_y + py)
                if tile:
                    if tile_type == 'wall':
                        tile.is_wall = True
                        tile.tile_type = 'wall'
                    else:
                        tile.is_wall = False
                        tile.tile_type = 'floor'
                
                # Create entity based on tile type
                self._create_prefab_entity(tile_type, global_x, global_y, prefab.id, chunk)
    
    def _clear_area(self, prefab: PrefabDefinition, chunk, local_x: int, local_y: int) -> None:
        """Clear existing wall entities in the prefab area."""
        entities_to_remove = []
        
        for py in range(prefab.height):
            for px in range(prefab.width):
                global_x = chunk.chunk_id * chunk.width + local_x + px
                global_y = local_y + py
                
                entities_at_pos = self._get_entities_at_position(global_x, global_y)
                for entity_id in entities_at_pos:
                    if self._is_wall_entity(entity_id):
                        entities_to_remove.append(entity_id)
        
        # Remove the entities
        for entity_id in entities_to_remove:
            # Remove from chunk's entity list
            if entity_id in chunk.entities:
                chunk.entities.remove(entity_id)
            # Destroy the entity
            self.world.destroy_entity(entity_id)
    
    def _create_prefab_entity(self, tile_type: str, global_x: int, global_y: int, prefab_id: str, chunk) -> None:
        """Create an entity for a prefab tile."""
        if tile_type == 'wall':
            # Create stone wall entity (for prefab buildings)
            wall_char, wall_color = self.glyph_config.get_entity_glyph('stone_wall')
            entity_id = self.world.create_entity()
            
            self.world.add_component(entity_id, Position(global_x, global_y))
            self.world.add_component(entity_id, Renderable(wall_char, wall_color))
            self.world.add_component(entity_id, Blocking())
            self.world.add_component(entity_id, Visible())
            self.world.add_component(entity_id, Prefab(prefab_id))
            
            chunk.entities.append(entity_id)
        
        elif tile_type in ['door_closed', 'door_open']:
            # Create door entity
            is_open = (tile_type == 'door_open')
            door_char = '-' if is_open else '+'
            door_color = 'brown'
            
            entity_id = self.world.create_entity()
            
            self.world.add_component(entity_id, Position(global_x, global_y))
            self.world.add_component(entity_id, Renderable(door_char, door_color))
            self.world.add_component(entity_id, Door(is_open))
            self.world.add_component(entity_id, Visible())
            self.world.add_component(entity_id, Prefab(prefab_id))
            
            # Closed doors block movement and vision
            if not is_open:
                self.world.add_component(entity_id, Blocking())
            
            chunk.entities.append(entity_id)
        
        # Floor tiles don't need entities (just the tile data is enough)
