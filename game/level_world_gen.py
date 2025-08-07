"""
Level-based world generator for dungeon diving.
"""

import random
from typing import Dict, Any, Optional, Tuple
from game.level_generator import LevelGenerator
from game.dungeon_level import DungeonLevel
from game.worldgen.scheduler import WorldScheduler
from game.worldgen.core import Tile
from game.config import GameConfig


class LevelWorldGenerator:
    """Level-based world generator for dungeon diving."""
    
    def __init__(self, world, seed: int = None):
        self.world = world
        self._seed = seed or random.randint(0, 1000000)
        
        # Create scheduler for level-based generation
        self.scheduler = WorldScheduler('data/schedule.yaml')
        
        # Create level generator
        self.level_generator = LevelGenerator(world, self.scheduler, self._seed)
        
        # Current level cache
        self._current_level: Optional[DungeonLevel] = None
        self._current_level_id: int = 0
    
    def set_current_level(self, level: DungeonLevel) -> None:
        """Set the current active level."""
        self._current_level = level
        self._current_level_id = level.level_id
    
    def get_current_level(self) -> Optional[DungeonLevel]:
        """Get the current active level."""
        return self._current_level
    
    def generate_level(self, level_id: int, stairs_up_pos: Optional[Tuple[int, int]] = None, turn_count: int = 0) -> DungeonLevel:
        """Generate a new level."""
        return self.level_generator.generate_level(level_id, stairs_up_pos, turn_count)
    
    def is_wall_at(self, x: int, y: int) -> bool:
        """Check if there's a wall at the given coordinates on the current level."""
        if not self._current_level:
            return True  # No level loaded - treat as wall
        
        return self._current_level.is_wall(x, y)
    
    def get_tile_at(self, x: int, y: int) -> Optional[Tile]:
        """Get tile at the given coordinates on the current level."""
        if not self._current_level:
            return None  # No level loaded
        
        return self._current_level.get_tile(x, y)
    
    def is_stairs_at(self, x: int, y: int) -> Optional[str]:
        """Check if there are stairs at the given position. Returns 'up', 'down', or None."""
        if not self._current_level:
            return None
        
        return self._current_level.is_stairs_at(x, y)
    
    def get_stairs_down_pos(self) -> Optional[Tuple[int, int]]:
        """Get the position of downward stairs on the current level."""
        if not self._current_level:
            return None
        
        return self._current_level.get_stairs_down_pos()
    
    def get_stairs_up_pos(self) -> Optional[Tuple[int, int]]:
        """Get the position of upward stairs on the current level."""
        if not self._current_level:
            return None
        
        return self._current_level.get_stairs_up_pos()
    
    def get_level_entities(self) -> list:
        """Get all entities on the current level."""
        if not self._current_level:
            return []
        
        return self._current_level.entities.copy()
    
    def add_entity_to_level(self, entity_id: int) -> None:
        """Add an entity to the current level."""
        if self._current_level:
            self._current_level.add_entity(entity_id)
    
    def remove_entity_from_level(self, entity_id: int) -> None:
        """Remove an entity from the current level."""
        if self._current_level:
            self._current_level.remove_entity(entity_id)
    
    def get_blood_tiles(self) -> set:
        """Get blood tiles for the current level."""
        if not self._current_level:
            return set()
        
        return self._current_level.blood_tiles.copy()
    
    def add_blood_tile(self, x: int, y: int) -> None:
        """Add a blood tile to the current level."""
        if self._current_level:
            self._current_level.blood_tiles.add((x, y))
    
    def get_biome_for_current_level(self) -> str:
        """Get the biome name for the current level."""
        return self.level_generator.get_biome_for_level(self._current_level_id)
    
    @property
    def seed(self) -> int:
        """Get the world seed."""
        return self._seed
