"""
Noise generation layer for creating random terrain.
"""

from typing import List
from ..core import GenLayer, GenContext, Tile


class NoiseLayer(GenLayer):
    """Basic noise generation layer."""
    
    def __init__(self, wall_probability: float = 0.45):
        self.wall_probability = wall_probability
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Fill with random noise."""
        wall_prob = ctx.get_param('wall_probability', self.wall_probability)
        
        for row in tiles:
            for tile in row:
                tile.is_wall = ctx.rng.random() < wall_prob
                tile.tile_type = 'wall' if tile.is_wall else 'floor'
