"""
Universal tile-to-entity conversion system for map generation.

Converts special tile types generated during map creation into proper game entities.
This allows templates to use tile-based generation while still creating interactive entities.
"""

from typing import Dict, Callable, Optional, List
from components.core import Position, Renderable, Blocking, Visible, Door
from game.glyph_config import GlyphConfig
from game.dungeon_level import DungeonLevel


class TileEntityConverter:
    """Converts special tile types to entities after map generation."""
    
    def __init__(self, world, glyph_config: GlyphConfig = None):
        self.world = world
        self.glyph_config = glyph_config or GlyphConfig()
        
        # Mapping of tile types to entity creation functions
        self.conversion_map: Dict[str, Callable] = {
            'door_closed': self._create_door_entity,
            'door_open': self._create_door_entity,
        }
    
    def convert_level_tiles(self, level: DungeonLevel) -> None:
        """Convert all special tiles in a level to entities."""
        tiles_to_convert = []
        
        # Scan the level for tiles that need conversion
        for y in range(level.height):
            for x in range(level.width):
                tile = level.get_tile(x, y)
                if tile and tile.tile_type in self.conversion_map:
                    tiles_to_convert.append((x, y, tile.tile_type))
        
        # Create all entities first (without modifying tiles)
        created_entities = []
        for x, y, tile_type in tiles_to_convert:
            entity_id = self.conversion_map[tile_type](x, y, tile_type, level)
            if entity_id:
                created_entities.append((entity_id, x, y, tile_type))
        
        # Now atomically add all entities and update tiles
        for entity_id, x, y, original_tile_type in created_entities:
            level.add_entity(entity_id)
            
            # Set the underlying tile back to floor after entity creation
            # Get a fresh reference to the tile to ensure we're updating the right object
            tile = level.get_tile(x, y)
            if tile:
                # Double-check that this tile still needs conversion
                if tile.tile_type == original_tile_type:
                    tile.is_wall = False
                    tile.tile_type = 'floor'
                    # Clear any special properties that might interfere
                    if 'door' in tile.properties:
                        del tile.properties['door']
                else:
                    # Log if we find a tile that was already converted
                    print(f"Warning: Tile at ({x}, {y}) was already converted from {original_tile_type} to {tile.tile_type}")
    
    def _create_door_entity(self, x: int, y: int, tile_type: str, level: DungeonLevel) -> Optional[int]:
        """Create a door entity from a door tile."""
        # Determine if door is open or closed
        is_open = (tile_type == 'door_open')
        
        # Create the entity
        entity_id = self.world.create_entity()
        
        # Add components
        self.world.add_component(entity_id, Position(x, y))
        
        # Set appearance based on door state
        door_char = '-' if is_open else '+'
        door_color = 'brown'
        self.world.add_component(entity_id, Renderable(door_char, door_color))
        
        # Add door component
        self.world.add_component(entity_id, Door(is_open))
        
        # Add visibility
        self.world.add_component(entity_id, Visible())
        
        # Closed doors block movement and vision
        if not is_open:
            self.world.add_component(entity_id, Blocking())
        
        return entity_id
    
    def register_tile_conversion(self, tile_type: str, conversion_func: Callable) -> None:
        """Register a new tile type for conversion."""
        self.conversion_map[tile_type] = conversion_func
    
    def get_convertible_tile_types(self) -> List[str]:
        """Get a list of all tile types that can be converted to entities."""
        return list(self.conversion_map.keys())
