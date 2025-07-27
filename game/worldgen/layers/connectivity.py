"""
Connectivity layer for ensuring east-west traversal.
"""

import random
from typing import List
from ..core import GenLayer, GenContext, Tile


class ConnectivityLayer(GenLayer):
    """Ensures east-west connectivity."""
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Create a path from west to east edge."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        halo_size = ctx.config.halo_size
        
        # Work within the core area (excluding halo)
        core_width = width - 2 * halo_size
        core_height = height - 2 * halo_size
        
        if core_width <= 0 or core_height <= 0:
            return
        
        # Find or create entrance on west edge
        west_x = halo_size
        west_y = self._find_or_create_entrance(tiles, west_x, halo_size, core_height, ctx.rng)
        
        # Find or create exit on east edge
        east_x = halo_size + core_width - 1
        east_y = self._find_or_create_entrance(tiles, east_x, halo_size, core_height, ctx.rng)
        
        # Create path between them
        self._create_path(tiles, (west_x, west_y), (east_x, east_y), ctx.rng)
    
    def _find_or_create_entrance(self, tiles: List[List[Tile]], x: int, y_start: int, height: int, rng: random.Random) -> int:
        """Find or create an entrance at the specified x coordinate."""
        # Look for existing opening
        for offset in range(height):
            y = y_start + offset
            if not tiles[y][x].is_wall:
                return y
        
        # Create opening in random position (avoid very edges)
        y = y_start + rng.randint(2, height - 3)
        tiles[y][x].is_wall = False
        tiles[y][x].tile_type = 'floor'
        return y
    
    def _create_path(self, tiles: List[List[Tile]], start: tuple, end: tuple, rng: random.Random) -> None:
        """Create a winding path between two points."""
        x1, y1 = start
        x2, y2 = end
        current_x, current_y = x1, y1
        
        while current_x != x2 or current_y != y2:
            # Clear current position
            tiles[current_y][current_x].is_wall = False
            tiles[current_y][current_x].tile_type = 'floor'
            
            # Choose direction with bias toward target
            if current_x < x2 and rng.random() < 0.7:
                current_x += 1
            elif current_x > x2 and rng.random() < 0.7:
                current_x -= 1
            elif current_y < y2 and rng.random() < 0.5:
                current_y += 1
            elif current_y > y2 and rng.random() < 0.5:
                current_y -= 1
            else:
                # Random movement
                direction = rng.choice(['north', 'south', 'east', 'west'])
                if direction == 'north' and current_y > 0:
                    current_y -= 1
                elif direction == 'south' and current_y < len(tiles) - 1:
                    current_y += 1
                elif direction == 'east' and current_x < len(tiles[0]) - 1:
                    current_x += 1
                elif direction == 'west' and current_x > 0:
                    current_x -= 1
