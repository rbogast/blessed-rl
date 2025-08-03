"""
Tree placement layers for forest environments.
"""

import random
from typing import List
from ..core import GenLayer, GenContext, Tile


class TreeScatterLayer(GenLayer):
    """Scatters trees on floor tiles using cellular automata for natural clustering."""
    
    def __init__(self, tree_type: str = 'pine_tree', density: float = 0.3, cluster_iterations: int = 1):
        self.tree_type = tree_type
        self.density = density
        self.cluster_iterations = cluster_iterations
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Place trees on floor tiles with natural clustering."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Get parameters from context
        tree_density = ctx.get_param('tree_density', self.density)
        tree_type = ctx.get_param('tree_type', self.tree_type)
        cluster_iterations = ctx.get_param('tree_cluster_iterations', self.cluster_iterations)
        
        # First pass: randomly place tree seeds on floor tiles
        tree_map = [[False for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                tile = tiles[y][x]
                # Only place trees on floor tiles
                if not tile.is_wall and ctx.rng.random() < tree_density:
                    tree_map[y][x] = True
        
        # Apply clustering iterations using cellular automata
        for _ in range(int(cluster_iterations)):
            new_tree_map = [[False for _ in range(width)] for _ in range(height)]
            
            for y in range(height):
                for x in range(width):
                    tile = tiles[y][x]
                    # Only consider floor tiles
                    if tile.is_wall:
                        continue
                    
                    tree_neighbors = self._count_tree_neighbors(tree_map, x, y, width, height)
                    
                    if tree_map[y][x]:
                        # Tree survives if it has at least 1 tree neighbor
                        new_tree_map[y][x] = tree_neighbors >= 1
                    else:
                        # Floor becomes tree if it has 3+ tree neighbors (creates small clusters)
                        new_tree_map[y][x] = tree_neighbors >= 3
            
            tree_map = new_tree_map
        
        # Apply trees to tiles
        for y in range(height):
            for x in range(width):
                if tree_map[y][x]:
                    tiles[y][x].tile_type = tree_type
                    # Trees block movement and vision like walls
                    tiles[y][x].is_wall = True
    
    def _count_tree_neighbors(self, tree_map: List[List[bool]], x: int, y: int, width: int, height: int) -> int:
        """Count trees in 3x3 neighborhood."""
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Don't count self
                
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    if tree_map[ny][nx]:
                        count += 1
        
        return count


class SparseTreeLayer(GenLayer):
    """Scatters a fixed number of trees randomly across the chunk."""
    
    def __init__(self, tree_type: str = 'oak_tree', count: int = 10):
        self.tree_type = tree_type
        self.count = count
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Place a fixed number of trees randomly on floor tiles."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Get parameters from context
        tree_count = int(ctx.get_param('tree_count', self.count))
        tree_type = ctx.get_param('sparse_tree_type', self.tree_type)
        
        # Find all available floor positions
        floor_positions = []
        for y in range(height):
            for x in range(width):
                tile = tiles[y][x]
                if not tile.is_wall:
                    floor_positions.append((x, y))
        
        # If we don't have enough floor tiles, place as many as we can
        actual_count = min(tree_count, len(floor_positions))
        
        # Randomly select positions for trees
        if floor_positions:
            selected_positions = ctx.rng.sample(floor_positions, actual_count)
            
            for x, y in selected_positions:
                tiles[y][x].tile_type = tree_type
                tiles[y][x].is_wall = True
