"""
Maze generation layers using Recursive Backtracking algorithm.
"""

import random
from typing import List, Set, Tuple, Optional
from ..core import GenLayer, GenContext, Tile


class RecursiveBacktrackingLayer(GenLayer):
    """
    Generates a maze using the Recursive Backtracking algorithm (randomized depth-first search).
    
    Grid system:
    - Even coordinates (0, 2, 4, ...) are walls
    - Odd coordinates (1, 3, 5, ...) are potential corridors
    - Full border of walls around the map
    - Ensures corners and intersections only occur on odd coordinates
    """
    
    def __init__(self):
        self.last_visited_cell = None
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate maze using recursive backtracking on odd coordinates only."""
        self.generate_with_stairs(tiles, ctx)
    
    def generate_with_stairs(self, tiles: List[List[Tile]], ctx: GenContext, 
                           start_position: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int]]:
        """Generate maze and return the last visited cell (ideal for downstairs placement)."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if width < 3 or height < 3:
            return None  # Too small for maze generation
        
        # Step 1: Initialize entire map as walls
        for y in range(height):
            for x in range(width):
                tiles[y][x].is_wall = True
                tiles[y][x].tile_type = 'wall'
        
        # Step 2: Find all valid maze cells (odd coordinates, not on border)
        maze_cells = []
        for y in range(1, height - 1, 2):  # Odd y coordinates, skip borders
            for x in range(1, width - 1, 2):  # Odd x coordinates, skip borders
                maze_cells.append((x, y))
        
        if not maze_cells:
            return None  # No valid maze cells
        
        # Step 3: Determine starting cell
        if start_position:
            # Ensure start position is on odd coordinates
            start_x, start_y = start_position
            # Convert to nearest odd coordinates if needed
            start_x = start_x if start_x % 2 == 1 else start_x + 1
            start_y = start_y if start_y % 2 == 1 else start_y + 1
            
            # Ensure it's within bounds and valid
            if (1 <= start_x < width - 1 and 1 <= start_y < height - 1 and 
                (start_x, start_y) in maze_cells):
                start_cell = (start_x, start_y)
            else:
                # Fallback to closest valid cell
                start_cell = min(maze_cells, key=lambda cell: 
                    abs(cell[0] - start_x) + abs(cell[1] - start_y))
        else:
            # Start from a random odd coordinate
            start_cell = ctx.rng.choice(maze_cells)
        
        # Step 4: Run recursive backtracking algorithm
        visited: Set[Tuple[int, int]] = set()
        self.last_visited_cell = None
        
        self._recursive_backtrack(tiles, start_cell, visited, ctx.rng, width, height)
        
        return self.last_visited_cell
    
    def _recursive_backtrack(self, tiles: List[List[Tile]], current: Tuple[int, int], 
                           visited: Set[Tuple[int, int]], rng: random.Random, 
                           width: int, height: int) -> None:
        """
        Recursive backtracking maze generation.
        
        Args:
            tiles: The tile grid to modify
            current: Current cell coordinates (must be odd)
            visited: Set of visited cells
            rng: Random number generator
            width: Grid width
            height: Grid height
        """
        x, y = current
        
        # Mark current cell as visited and carve it out
        visited.add(current)
        tiles[y][x].is_wall = False
        tiles[y][x].tile_type = 'floor'
        
        # Track this as the last visited cell (potential downstairs location)
        self.last_visited_cell = current
        
        # Get all unvisited neighbors (2 steps away on odd coordinates)
        neighbors = self._get_unvisited_neighbors(current, visited, width, height)
        
        # Randomize neighbor order for random maze generation
        rng.shuffle(neighbors)
        
        # Visit each unvisited neighbor
        for neighbor in neighbors:
            if neighbor not in visited:
                # Carve passage between current cell and neighbor
                self._carve_passage(tiles, current, neighbor)
                
                # Recursively visit the neighbor
                self._recursive_backtrack(tiles, neighbor, visited, rng, width, height)
    
    def _get_unvisited_neighbors(self, cell: Tuple[int, int], visited: Set[Tuple[int, int]], 
                               width: int, height: int) -> List[Tuple[int, int]]:
        """
        Get all unvisited neighboring cells that are 2 steps away on odd coordinates.
        
        Args:
            cell: Current cell coordinates
            visited: Set of visited cells
            width: Grid width
            height: Grid height
            
        Returns:
            List of unvisited neighbor coordinates
        """
        x, y = cell
        neighbors = []
        
        # Check all four directions (2 steps away to maintain odd coordinates)
        directions = [
            (0, -2),  # North
            (2, 0),   # East
            (0, 2),   # South
            (-2, 0),  # West
        ]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check bounds (must be odd coordinates and not on border)
            if (1 <= nx < width - 1 and 1 <= ny < height - 1 and 
                nx % 2 == 1 and ny % 2 == 1 and (nx, ny) not in visited):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def _carve_passage(self, tiles: List[List[Tile]], cell1: Tuple[int, int], 
                      cell2: Tuple[int, int]) -> None:
        """
        Carve a passage between two cells by removing the wall between them.
        Ensures only odd coordinates become corridors.
        
        Args:
            tiles: The tile grid to modify
            cell1: First cell coordinates (odd, odd)
            cell2: Second cell coordinates (odd, odd)
        """
        x1, y1 = cell1
        x2, y2 = cell2
        
        # The wall between the cells is at the midpoint
        wall_x = (x1 + x2) // 2
        wall_y = (y1 + y2) // 2
        
        # Since both cells are on odd coordinates and 2 apart,
        # the wall between them will be on even coordinates
        # We need to carve this wall to connect the cells
        tiles[wall_y][wall_x].is_wall = False
        tiles[wall_y][wall_x].tile_type = 'floor'


class MazeInterconnectionLayer(GenLayer):
    """
    Creates additional openings in the maze to increase interconnectivity.
    This layer runs after maze generation to add tactical options.
    Strictly follows maze grid rules and preserves stair dead-ends.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Create additional openings in the maze based on parameters."""
        # Get the number of openings to create from parameters
        maze_openings = ctx.get_param('maze_openings', 0)
        
        if maze_openings <= 0:
            return  # No openings requested
        
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if width < 7 or height < 7:
            return  # Too small for meaningful interconnections
        
        # Find stair positions to avoid them
        stair_positions = self._find_stair_positions(tiles, width, height)
        
        # Find valid walls that can be converted to openings
        valid_walls = self._find_valid_interconnection_walls(tiles, width, height, stair_positions)
        
        if not valid_walls:
            return  # No valid walls found
        
        # Randomly select walls to convert, up to the requested amount
        num_openings = min(int(maze_openings), len(valid_walls))
        selected_walls = ctx.rng.sample(valid_walls, num_openings)
        
        # Convert selected walls to floor tiles
        for x, y in selected_walls:
            tiles[y][x].is_wall = False
            tiles[y][x].tile_type = 'floor'
    
    def _find_stair_positions(self, tiles: List[List[Tile]], width: int, height: int) -> Set[Tuple[int, int]]:
        """Find all stair positions to avoid creating openings around them."""
        stair_positions = set()
        
        for y in range(height):
            for x in range(width):
                if hasattr(tiles[y][x], 'has_stairs') and tiles[y][x].has_stairs:
                    stair_positions.add((x, y))
                # Also check for stair tile types if they exist
                elif hasattr(tiles[y][x], 'tile_type') and tiles[y][x].tile_type in ['stairs_up', 'stairs_down']:
                    stair_positions.add((x, y))
        
        return stair_positions
    
    def _find_valid_interconnection_walls(self, tiles: List[List[Tile]], 
                                        width: int, height: int,
                                        stair_positions: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Find walls that can be converted to create interconnections.
        Uses simple rule: any tile that is NOT:
        1. A border tile
        2. Adjacent to a stair tile  
        3. Both x and y are even numbers
        
        Args:
            tiles: The tile grid
            width: Grid width
            height: Grid height
            stair_positions: Set of stair coordinates to avoid
            
        Returns:
            List of (x, y) coordinates of valid walls for interconnection
        """
        valid_walls = []
        
        # Check all tiles except borders
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                # Must be a wall to be a candidate
                if not tiles[y][x].is_wall:
                    continue
                
                # Rule 1: Not a border tile (already handled by range)
                # Rule 2: Not adjacent to a stair tile
                if self._is_adjacent_to_stair(x, y, stair_positions):
                    continue
                
                # Rule 3: Not both x and y even numbers
                if x % 2 == 0 and y % 2 == 0:
                    continue
                
                # This wall passes all rules - it's valid for interconnection
                valid_walls.append((x, y))
        
        return valid_walls
    
    def _is_adjacent_to_stair(self, x: int, y: int, stair_positions: Set[Tuple[int, int]]) -> bool:
        """
        Check if a position is adjacent to any stair.
        
        Args:
            x, y: Position to check
            stair_positions: Set of stair coordinates
            
        Returns:
            True if adjacent to a stair, False otherwise
        """
        # Check all 8 adjacent positions (including diagonals for safety)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip the center position
                
                check_pos = (x + dx, y + dy)
                if check_pos in stair_positions:
                    return True
        
        return False


class MazeBorderLayer(GenLayer):
    """
    Ensures a full border of walls around the maze.
    This layer runs after maze generation to guarantee border integrity.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Force walls on all border tiles."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if width == 0 or height == 0:
            return
        
        # Force walls on all border positions
        for y in range(height):
            for x in range(width):
                # Check if on border
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    tiles[y][x].is_wall = True
                    tiles[y][x].tile_type = 'wall'
