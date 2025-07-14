"""
Compatibility layer for the new modular world generation system.

This module maintains the existing API while using the new biome/scheduler system underneath.
"""

import random
from typing import Dict, Any
from .worldgen.core import WorldGenerator as NewWorldGenerator, WorldConfig, Tile, Chunk
from .worldgen.scheduler import WorldScheduler


class WorldGenerator:
    """Compatibility wrapper for the new world generation system."""
    
    def __init__(self, world, seed: int = None):
        self.world = world
        self._seed = seed or random.randint(0, 1000000)
        
        # Create new system with updated chunk size (40x23)
        self.config = WorldConfig(
            chunk_width=40,
            chunk_height=23,
            halo_size=5,  # Smaller halo for legacy compatibility
            seed=self._seed
        )
        
        # Create scheduler with schedule file
        self.scheduler = WorldScheduler('data/schedule.yaml')
        
        # Create new generator
        self._generator = NewWorldGenerator(world, self.config, self.scheduler)
        
        # Legacy properties for compatibility
        self.chunks: Dict[int, Chunk] = self._generator.chunks
    
    def generate_chunk(self, chunk_id: int) -> Chunk:
        """Generate a new chunk using the new system."""
        return self._generator.generate_chunk(chunk_id)
    
    def get_chunk(self, chunk_id: int) -> Chunk:
        """Get a chunk, generating it if necessary."""
        return self._generator.get_chunk(chunk_id)
    
    def is_wall_at(self, global_x: int, global_y: int) -> bool:
        """Check if there's a wall at global coordinates."""
        return self._generator.is_wall_at(global_x, global_y)
    
    def get_tile_at(self, global_x: int, global_y: int) -> Tile:
        """Get tile at global coordinates."""
        return self._generator.get_tile_at(global_x, global_y)
    
    @property
    def seed(self) -> int:
        """Get the world seed."""
        return self._generator.seed


# Re-export classes for compatibility
__all__ = ['WorldGenerator', 'Tile', 'Chunk']
