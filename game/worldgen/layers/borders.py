"""
Border layers for creating boundaries and walls.
"""

from typing import List
from ..core import GenLayer, GenContext, Tile


class BorderWallLayer(GenLayer):
    """Forces walls on specified rows to create canyon-like boundaries."""
    
    def __init__(self, border_rows: List[int] = None):
        self.border_rows = border_rows or [0, 22]  # Default to top and bottom
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Force walls on specified rows."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        halo_size = ctx.config.halo_size
        
        # Get border rows from parameters or use defaults
        border_rows = ctx.get_param('border_rows', self.border_rows)
        
        # Apply to the full tile area (including halo for seamless borders)
        for y in range(height):
            # Convert from halo coordinates to core coordinates for checking
            core_y = y - halo_size
            
            if core_y in border_rows:
                for x in range(width):
                    tiles[y][x].is_wall = True
                    tiles[y][x].tile_type = 'wall'
