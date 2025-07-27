"""
Cellular automata layer for smoothing terrain.
"""

from typing import List
from ..core import GenLayer, GenContext, Tile


class CellularAutomataLayer(GenLayer):
    """Cellular automata smoothing layer."""
    
    def __init__(self, iterations: int = 5, birth_limit: int = 4, death_limit: int = 3):
        self.iterations = iterations
        self.birth_limit = birth_limit
        self.death_limit = death_limit
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Apply cellular automata smoothing."""
        iterations = ctx.get_param('ca_iterations', self.iterations)
        
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        for _ in range(int(iterations)):
            new_tiles = [[None for _ in range(width)] for _ in range(height)]
            
            for y in range(height):
                for x in range(width):
                    wall_count = self._count_walls(tiles, x, y, width, height)
                    
                    if tiles[y][x].is_wall:
                        new_tiles[y][x] = wall_count >= self.death_limit
                    else:
                        new_tiles[y][x] = wall_count > self.birth_limit
            
            # Apply changes
            for y in range(height):
                for x in range(width):
                    tiles[y][x].is_wall = new_tiles[y][x]
                    tiles[y][x].tile_type = 'wall' if new_tiles[y][x] else 'floor'
    
    def _count_walls(self, tiles: List[List[Tile]], x: int, y: int, width: int, height: int) -> int:
        """Count walls in 3x3 neighborhood."""
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    count += 1  # Treat out-of-bounds as walls
                elif tiles[ny][nx].is_wall:
                    count += 1
        
        return count
