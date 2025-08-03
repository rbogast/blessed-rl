"""
Maze generation using Recursive Backtracking algorithm.
"""

import random
from typing import List, Set, Tuple, Optional
from .core import GenLayer, GenContext, Tile
from dataclasses import dataclass


@dataclass
class MazeRoom:
    """Represents a room in the maze."""
    x: int      # Must be odd
    y: int      # Must be odd  
    width: int  # Must be odd
    height: int # Must be odd
    
    @property
    def right(self) -> int:
        return self.x + self.width - 1
    
    @property
    def bottom(self) -> int:
        return self.y + self.height - 1


class MazeRoomLayer:
    """
    Generates rooms in the maze before maze generation.
    
    Rooms follow maze grid rules:
    - Room dimensions must be odd numbers
    - Room positions must start on odd coordinates
    - Rooms are carved as floor areas before maze generation
    - Maze generation will naturally connect to room edges
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate rooms before maze generation."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Get room parameters
        num_rooms = ctx.get_param('num_rooms', 0)
        min_room_size = ctx.get_param('min_room_size', 5)
        max_room_size = ctx.get_param('max_room_size', 9)
        
        if num_rooms <= 0:
            return  # No rooms requested
        
        if width < 7 or height < 7:
            return  # Too small for rooms
        
        # Validate and adjust room size parameters to be odd
        min_room_size = self._ensure_odd(max(3, min_room_size))
        max_room_size = self._ensure_odd(min(max_room_size, min(width // 3, height // 3)))
        
        if min_room_size > max_room_size:
            max_room_size = min_room_size
        
        # Generate rooms
        rooms = []
        max_attempts = num_rooms * 10  # Prevent infinite loops
        attempts = 0
        
        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            room = self._try_create_room(width, height, min_room_size, max_room_size, rooms, ctx.rng)
            if room:
                rooms.append(room)
                self._carve_room(tiles, room)
        
        # Store rooms in context for potential use by other layers
        ctx.parameters['maze_rooms'] = rooms
    
    def _ensure_odd(self, value: int) -> int:
        """Ensure a value is odd."""
        return value if value % 2 == 1 else value + 1
    
    def _try_create_room(self, width: int, height: int, min_size: int, max_size: int, 
                        existing_rooms: List[MazeRoom], rng: random.Random) -> Optional[MazeRoom]:
        """Try to create a room that doesn't collide with existing rooms."""
        # Generate random odd dimensions (square rooms only)
        room_size = self._ensure_odd(rng.randint(min_size, max_size))
        room_width = room_size
        room_height = room_size
        
        # Find valid odd positions (respecting borders and spacing)
        min_x = 1  # Start at odd coordinate, respect border
        max_x = width - room_width - 1  # Ensure room fits with border
        min_y = 1  # Start at odd coordinate, respect border  
        max_y = height - room_height - 1  # Ensure room fits with border
        
        # Ensure we have valid bounds
        if min_x >= max_x or min_y >= max_y:
            return None
        
        # Try multiple random positions
        for _ in range(20):  # Limit attempts per room
            # Generate random odd coordinates
            room_x = self._ensure_odd(rng.randint(min_x, max_x))
            room_y = self._ensure_odd(rng.randint(min_y, max_y))
            
            # Ensure the room fits within bounds
            if room_x + room_width >= width - 1 or room_y + room_height >= height - 1:
                continue
            
            # Create candidate room
            candidate_room = MazeRoom(room_x, room_y, room_width, room_height)
            
            # Check for collisions with existing rooms
            if not self._room_collides(candidate_room, existing_rooms):
                return candidate_room
        
        return None  # Failed to place room
    
    def _room_collides(self, new_room: MazeRoom, existing_rooms: List[MazeRoom]) -> bool:
        """Check if a new room collides with existing rooms (including spacing)."""
        for existing_room in existing_rooms:
            # Check for overlap or insufficient spacing
            # Require at least 2 tiles spacing between rooms for maze corridors
            spacing = 2
            
            if (new_room.x - spacing <= existing_room.right and 
                new_room.right + spacing >= existing_room.x and
                new_room.y - spacing <= existing_room.bottom and 
                new_room.bottom + spacing >= existing_room.y):
                return True  # Collision or insufficient spacing
        
        return False
    
    def _carve_room(self, tiles: List[List[Tile]], room: MazeRoom) -> None:
        """Carve out a room area as floor tiles and add one door."""
        # Carve the room interior
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
                    tiles[y][x].is_wall = False
                    tiles[y][x].tile_type = 'floor'
        
        # Add one door to the room
        self._add_door_to_room(tiles, room)
    
    def _add_door_to_room(self, tiles: List[List[Tile]], room: MazeRoom) -> None:
        """Add exactly one door to a room by creating an opening in the wall."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Find all possible door positions (walls adjacent to room perimeter)
        door_candidates = []
        
        # Check all four sides of the room
        # Top side
        for x in range(room.x, room.x + room.width):
            door_y = room.y - 1
            if door_y > 0 and door_y < height - 1:  # Not on map border
                door_candidates.append((x, door_y, 'north'))
        
        # Bottom side  
        for x in range(room.x, room.x + room.width):
            door_y = room.y + room.height
            if door_y > 0 and door_y < height - 1:  # Not on map border
                door_candidates.append((x, door_y, 'south'))
        
        # Left side
        for y in range(room.y, room.y + room.height):
            door_x = room.x - 1
            if door_x > 0 and door_x < width - 1:  # Not on map border
                door_candidates.append((door_x, y, 'west'))
        
        # Right side
        for y in range(room.y, room.y + room.height):
            door_x = room.x + room.width
            if door_x > 0 and door_x < width - 1:  # Not on map border
                door_candidates.append((door_x, y, 'east'))
        
        # Filter to only valid door positions (must be walls currently)
        # Note: Room perimeters are on even coordinates, which is fine for doors
        # as they connect rooms (odd coordinate areas) to corridors (odd coordinate paths)
        valid_doors = []
        for x, y, direction in door_candidates:
            if (0 <= x < width and 0 <= y < height and 
                tiles[y][x].is_wall):
                valid_doors.append((x, y, direction))
        
        # Place one door randomly if we have valid positions
        if valid_doors:
            import random
            door_x, door_y, direction = random.choice(valid_doors)
            tiles[door_y][door_x].is_wall = False
            tiles[door_y][door_x].tile_type = 'door_closed'  # This will be converted to a door entity
            # Store door properties for the tile converter
            tiles[door_y][door_x].properties = {'direction': direction}


class RecursiveBacktrackingLayer:
    """
    Generates a maze using the Recursive Backtracking algorithm (randomized depth-first search).
    
    Grid system:
    - Even coordinates (0, 2, 4, ...) are walls
    - Odd coordinates (1, 3, 5, ...) are potential corridors
    - Full border of walls around the map
    - Ensures corners and intersections only occur on odd coordinates
    - COMPLETELY PRESERVES room areas without modification
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
        
        # Find all room areas (floor tiles) to preserve completely
        room_areas = set()
        for y in range(height):
            for x in range(width):
                if not tiles[y][x].is_wall:
                    room_areas.add((x, y))
        
        # Find all valid maze cells (odd coordinates, not rooms, not borders)
        maze_cells = []
        for y in range(1, height - 1, 2):  # Odd y coordinates
            for x in range(1, width - 1, 2):  # Odd x coordinates
                if (x, y) not in room_areas:  # Not a room area
                    maze_cells.append((x, y))
        
        if not maze_cells:
            return None  # No valid maze cells
        
        # Determine starting cell
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
            # Start from a random maze cell
            start_cell = ctx.rng.choice(maze_cells)
        
        # Mark room areas as "visited" to avoid them completely
        visited = room_areas.copy()
        self.last_visited_cell = None
        
        self._recursive_backtrack(tiles, start_cell, visited, ctx.rng, width, height, room_areas)
        
        return self.last_visited_cell
    
    def _recursive_backtrack(self, tiles: List[List[Tile]], current: Tuple[int, int], 
                           visited: Set[Tuple[int, int]], rng: random.Random, 
                           width: int, height: int, room_areas: Set[Tuple[int, int]]) -> None:
        """
        Recursive backtracking maze generation that never touches room areas.
        
        Args:
            tiles: The tile grid to modify
            current: Current cell coordinates (must be odd)
            visited: Set of visited cells
            rng: Random number generator
            width: Grid width
            height: Grid height
            room_areas: Set of room coordinates to avoid
        """
        x, y = current
        
        # Skip if this is a room area
        if (x, y) in room_areas:
            return
        
        # Mark as visited and carve
        visited.add(current)
        tiles[y][x].is_wall = False
        tiles[y][x].tile_type = 'floor'
        
        # Track this as the last visited cell (potential downstairs location)
        self.last_visited_cell = current
        
        # Get neighbors
        neighbors = self._get_unvisited_neighbors(current, visited, width, height, room_areas)
        rng.shuffle(neighbors)
        
        # Visit each unvisited neighbor
        for neighbor in neighbors:
            if neighbor not in visited:
                # Carve passage
                self._carve_passage(tiles, current, neighbor, room_areas)
                self._recursive_backtrack(tiles, neighbor, visited, rng, width, height, room_areas)
    
    def _get_unvisited_neighbors(self, cell: Tuple[int, int], visited: Set[Tuple[int, int]], 
                               width: int, height: int, room_areas: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Get all unvisited neighboring cells that are 2 steps away on odd coordinates.
        EXCLUDES room areas completely.
        
        Args:
            cell: Current cell coordinates
            visited: Set of visited cells
            width: Grid width
            height: Grid height
            room_areas: Set of room coordinates to avoid
            
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
            
            # Check bounds and validity
            if (1 <= nx < width - 1 and 1 <= ny < height - 1 and 
                nx % 2 == 1 and ny % 2 == 1 and 
                (nx, ny) not in visited and (nx, ny) not in room_areas):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def _carve_passage(self, tiles: List[List[Tile]], cell1: Tuple[int, int], 
                      cell2: Tuple[int, int], room_areas: Set[Tuple[int, int]]) -> None:
        """
        Carve a passage between two cells by removing the wall between them.
        NEVER overwrites room areas.
        
        Args:
            tiles: The tile grid to modify
            cell1: First cell coordinates (odd, odd)
            cell2: Second cell coordinates (odd, odd)
            room_areas: Set of room coordinates to avoid
        """
        x1, y1 = cell1
        x2, y2 = cell2
        
        # The wall between the cells is at the midpoint
        wall_x = (x1 + x2) // 2
        wall_y = (y1 + y2) // 2
        
        # Only carve if not a room area
        if (wall_x, wall_y) not in room_areas and tiles[wall_y][wall_x].is_wall:
            tiles[wall_y][wall_x].is_wall = False
            tiles[wall_y][wall_x].tile_type = 'floor'


class MazeInterconnectionLayer:
    """
    Creates additional openings in the maze to increase interconnectivity.
    This layer runs after maze generation to add tactical options.
    Strictly follows maze grid rules and preserves stair dead-ends.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Create additional openings in the maze based on parameters."""
        # Get the number of openings to create from parameters
        maze_openings = ctx.parameters.get('maze_openings', 0)
        
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
        4. Adjacent to a room area
        
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
                
                # Rule 4: Not adjacent to a room area
                if self._is_adjacent_to_room(x, y, tiles, width, height):
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
    
    def _is_adjacent_to_room(self, x: int, y: int, tiles: List[List[Tile]], 
                           width: int, height: int) -> bool:
        """
        Check if a position is adjacent to any room area (floor tile).
        
        Args:
            x, y: Position to check
            tiles: The tile grid
            width: Grid width
            height: Grid height
            
        Returns:
            True if adjacent to a room area, False otherwise
        """
        # For now, disable interconnections entirely when rooms are present
        # This ensures room integrity is preserved
        return True  # Always return True to disable all interconnections when rooms exist
        
        # Original logic (commented out for now):
        # # Check all 4 adjacent positions (not diagonals for rooms)
        # for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        #     nx, ny = x + dx, y + dy
        #     
        #     # Check bounds and if it's a floor tile
        #     if (0 <= nx < width and 0 <= ny < height and 
        #         not tiles[ny][nx].is_wall):
        #         return True
        # 
        # return False


class MazeBorderLayer:
    """
    Ensures a full border of walls around the maze.
    This layer runs after maze generation to guarantee border integrity.
    Respects existing room areas and only enforces borders where needed.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Force walls on border tiles, but respect existing room areas."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if width == 0 or height == 0:
            return
        
        # Get room information to avoid overwriting room areas
        rooms = ctx.parameters.get('maze_rooms', [])
        room_areas = set()
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    room_areas.add((x, y))
        
        # Force walls on border positions, but respect room areas
        for y in range(height):
            for x in range(width):
                # Check if on border
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    # Only force wall if not part of a room
                    if (x, y) not in room_areas:
                        tiles[y][x].is_wall = True
                        tiles[y][x].tile_type = 'wall'
