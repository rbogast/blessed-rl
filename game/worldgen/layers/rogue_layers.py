"""
Rogue-style generation layers implementing the classic room-and-corridor algorithm.
"""

import random
from typing import List, Set, Tuple, Dict, Any, Optional
from ..core import GenLayer, GenContext, Tile
from dataclasses import dataclass


@dataclass
class Room:
    """Represents a room in the dungeon."""
    x: int          # Left edge
    y: int          # Top edge  
    width: int      # Room width
    height: int     # Room height
    grid_x: int     # Grid cell X (0-2)
    grid_y: int     # Grid cell Y (0-2)
    
    @property
    def center_x(self) -> int:
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        return self.y + self.height // 2
    
    @property
    def right(self) -> int:
        return self.x + self.width - 1
    
    @property
    def bottom(self) -> int:
        return self.y + self.height - 1


@dataclass
class Corridor:
    """Represents a corridor connection between two rooms."""
    room1: Room
    room2: Room
    path: List[Tuple[int, int]]  # List of (x, y) coordinates forming the corridor


class RogueRoomLayer(GenLayer):
    """
    Generates rooms using the classic Rogue algorithm.
    
    Divides the 23x45 map into a 3x3 grid and places rooms randomly.
    Grid layout for 23x45:
    - Each cell is approximately 15x7-8 tiles
    - Rooms are placed randomly within their assigned cells
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate rooms in a 3x3 grid layout."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if width != 45 or height != 23:
            # Fallback for different dimensions - scale the grid
            self._generate_scaled(tiles, ctx, width, height)
            return
        
        # Initialize entire map as walls
        for y in range(height):
            for x in range(width):
                tiles[y][x].is_wall = True
                tiles[y][x].tile_type = 'wall'
        
        # Define 3x3 grid cells for 23x45 map
        grid_cells = self._define_grid_cells(width, height)
        
        # Get parameters
        min_rooms = ctx.get_param('min_rooms', 5)
        max_rooms = ctx.get_param('max_rooms', 7)
        min_room_size = ctx.get_param('min_room_size', 4)
        max_room_size = ctx.get_param('max_room_size', 8)
        
        # Randomly select which cells will have rooms
        num_rooms = ctx.rng.randint(min_rooms, max_rooms)
        selected_cells = ctx.rng.sample(list(range(9)), num_rooms)
        
        # Generate rooms
        rooms = []
        for cell_idx in selected_cells:
            grid_x = cell_idx % 3
            grid_y = cell_idx // 3
            cell = grid_cells[grid_y][grid_x]
            
            room = self._create_room_in_cell(cell, grid_x, grid_y, min_room_size, max_room_size, ctx.rng)
            if room:
                rooms.append(room)
                self._carve_room(tiles, room)
        
        # Store rooms in context for other layers
        ctx.parameters['rogue_rooms'] = rooms
    
    def _generate_scaled(self, tiles: List[List[Tile]], ctx: GenContext, width: int, height: int) -> None:
        """Generate rooms for non-standard dimensions by scaling the algorithm."""
        # Initialize as walls
        for y in range(height):
            for x in range(width):
                tiles[y][x].is_wall = True
                tiles[y][x].tile_type = 'wall'
        
        # Scale grid cells based on actual dimensions
        cell_width = width // 3
        cell_height = height // 3
        
        grid_cells = []
        for gy in range(3):
            row = []
            for gx in range(3):
                x_start = gx * cell_width
                y_start = gy * cell_height
                # Handle remainder for last cells
                x_end = (gx + 1) * cell_width if gx < 2 else width
                y_end = (gy + 1) * cell_height if gy < 2 else height
                row.append((x_start, y_start, x_end - x_start, y_end - y_start))
            grid_cells.append(row)
        
        # Generate rooms with scaled parameters
        min_rooms = ctx.get_param('min_rooms', 5)
        max_rooms = ctx.get_param('max_rooms', 7)
        min_room_size = max(3, min(ctx.get_param('min_room_size', 4), cell_width // 3))
        max_room_size = max(min_room_size, min(ctx.get_param('max_room_size', 8), cell_width - 2))
        
        num_rooms = ctx.rng.randint(min_rooms, max_rooms)
        selected_cells = ctx.rng.sample(list(range(9)), num_rooms)
        
        rooms = []
        for cell_idx in selected_cells:
            grid_x = cell_idx % 3
            grid_y = cell_idx // 3
            cell = grid_cells[grid_y][grid_x]
            
            room = self._create_room_in_cell(cell, grid_x, grid_y, min_room_size, max_room_size, ctx.rng)
            if room:
                rooms.append(room)
                self._carve_room(tiles, room)
        
        ctx.parameters['rogue_rooms'] = rooms
    
    def _define_grid_cells(self, width: int, height: int) -> List[List[Tuple[int, int, int, int]]]:
        """Define the 3x3 grid cells for room placement."""
        # For 23x45, create cells of size ~15x7-8
        grid_cells = []
        
        # Calculate cell dimensions
        cell_width = width // 3  # 15
        cell_height = height // 3  # 7 or 8
        
        for gy in range(3):
            row = []
            for gx in range(3):
                x_start = gx * cell_width
                y_start = gy * cell_height
                
                # Handle remainder for rightmost and bottom cells
                if gx == 2:  # Last column
                    cell_w = width - x_start
                else:
                    cell_w = cell_width
                
                if gy == 2:  # Last row
                    cell_h = height - y_start
                else:
                    cell_h = cell_height
                
                row.append((x_start, y_start, cell_w, cell_h))
            grid_cells.append(row)
        
        return grid_cells
    
    def _create_room_in_cell(self, cell: Tuple[int, int, int, int], grid_x: int, grid_y: int,
                           min_size: int, max_size: int, rng: random.Random) -> Optional[Room]:
        """Create a room within the given grid cell."""
        cell_x, cell_y, cell_width, cell_height = cell
        
        # Ensure minimum cell size
        if cell_width < min_size + 2 or cell_height < min_size + 2:
            return None
        
        # Calculate room dimensions
        max_room_width = min(max_size, cell_width - 2)
        max_room_height = min(max_size, cell_height - 2)
        
        room_width = rng.randint(min_size, max_room_width)
        room_height = rng.randint(min_size, max_room_height)
        
        # Calculate room position within cell (leave at least 1 tile border)
        max_x_offset = cell_width - room_width - 1
        max_y_offset = cell_height - room_height - 1
        
        x_offset = rng.randint(1, max(1, max_x_offset))
        y_offset = rng.randint(1, max(1, max_y_offset))
        
        room_x = cell_x + x_offset
        room_y = cell_y + y_offset
        
        return Room(room_x, room_y, room_width, room_height, grid_x, grid_y)
    
    def _carve_room(self, tiles: List[List[Tile]], room: Room) -> None:
        """Carve out a room in the tile grid."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
                    tiles[y][x].is_wall = False
                    tiles[y][x].tile_type = 'floor'


class RogueCorridorLayer(GenLayer):
    """
    Connects rooms with corridors using the Rogue algorithm.
    
    Creates straight horizontal/vertical corridors and L-shaped turns.
    Ensures all rooms are connected and optionally adds extra connections.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate corridors connecting all rooms."""
        rooms = ctx.parameters.get('rogue_rooms', [])
        if len(rooms) < 2:
            return  # Need at least 2 rooms to connect
        
        # Generate minimum spanning tree for basic connectivity
        corridors = self._generate_minimum_spanning_tree(rooms, ctx.rng)
        
        # Add extra connections for loops and tactical options
        extra_connections = ctx.get_param('extra_connections', 1)
        if extra_connections > 0:
            additional_corridors = self._add_extra_connections(rooms, corridors, extra_connections, ctx.rng)
            corridors.extend(additional_corridors)
        
        # Carve all corridors
        for corridor in corridors:
            self._carve_corridor(tiles, corridor)
        
        # Store corridors for door placement
        ctx.parameters['rogue_corridors'] = corridors
    
    def _generate_minimum_spanning_tree(self, rooms: List[Room], rng: random.Random) -> List[Corridor]:
        """Generate a minimum spanning tree to connect all rooms."""
        if len(rooms) < 2:
            return []
        
        corridors = []
        connected = {0}  # Start with first room
        unconnected = set(range(1, len(rooms)))
        
        while unconnected:
            # Find closest unconnected room to any connected room
            min_distance = float('inf')
            best_connection = None
            
            for connected_idx in connected:
                for unconnected_idx in unconnected:
                    distance = self._room_distance(rooms[connected_idx], rooms[unconnected_idx])
                    if distance < min_distance:
                        min_distance = distance
                        best_connection = (connected_idx, unconnected_idx)
            
            if best_connection:
                room1_idx, room2_idx = best_connection
                corridor = self._create_corridor(rooms[room1_idx], rooms[room2_idx], rng)
                corridors.append(corridor)
                
                connected.add(room2_idx)
                unconnected.remove(room2_idx)
        
        return corridors
    
    def _add_extra_connections(self, rooms: List[Room], existing_corridors: List[Corridor],
                             num_extra: int, rng: random.Random) -> List[Corridor]:
        """Add extra connections between rooms for loops and tactical options."""
        extra_corridors = []
        
        # Get all existing connections
        existing_connections = set()
        for corridor in existing_corridors:
            room1_idx = rooms.index(corridor.room1)
            room2_idx = rooms.index(corridor.room2)
            existing_connections.add((min(room1_idx, room2_idx), max(room1_idx, room2_idx)))
        
        # Find potential new connections
        potential_connections = []
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                if (i, j) not in existing_connections:
                    potential_connections.append((i, j))
        
        # Randomly select extra connections
        num_to_add = min(int(num_extra), len(potential_connections))
        if num_to_add > 0:
            selected_connections = rng.sample(potential_connections, num_to_add)
        else:
            selected_connections = []
        
        for room1_idx, room2_idx in selected_connections:
            corridor = self._create_corridor(rooms[room1_idx], rooms[room2_idx], rng)
            extra_corridors.append(corridor)
        
        return extra_corridors
    
    def _room_distance(self, room1: Room, room2: Room) -> float:
        """Calculate Manhattan distance between room centers."""
        return abs(room1.center_x - room2.center_x) + abs(room1.center_y - room2.center_y)
    
    def _create_corridor(self, room1: Room, room2: Room, rng: random.Random) -> Corridor:
        """Create a corridor between two rooms using straight lines or L-shapes."""
        # Choose connection points on room edges
        start_x, start_y = self._get_connection_point(room1, room2, rng)
        end_x, end_y = self._get_connection_point(room2, room1, rng)
        
        # Create path (straight or L-shaped)
        path = self._create_path(start_x, start_y, end_x, end_y, rng)
        
        return Corridor(room1, room2, path)
    
    def _get_connection_point(self, from_room: Room, to_room: Room, rng: random.Random) -> Tuple[int, int]:
        """Get a connection point on the edge of from_room closest to to_room."""
        # Determine which edge of from_room is closest to to_room
        if to_room.center_x < from_room.x:
            # Connect from left edge
            x = from_room.x - 1
            y = rng.randint(from_room.y, from_room.bottom)
        elif to_room.center_x > from_room.right:
            # Connect from right edge
            x = from_room.right + 1
            y = rng.randint(from_room.y, from_room.bottom)
        elif to_room.center_y < from_room.y:
            # Connect from top edge
            x = rng.randint(from_room.x, from_room.right)
            y = from_room.y - 1
        else:
            # Connect from bottom edge
            x = rng.randint(from_room.x, from_room.right)
            y = from_room.bottom + 1
        
        return x, y
    
    def _create_path(self, start_x: int, start_y: int, end_x: int, end_y: int,
                    rng: random.Random) -> List[Tuple[int, int]]:
        """Create a path from start to end using straight lines or L-shapes."""
        path = []
        
        # Randomly choose L-shape direction (horizontal first or vertical first)
        if rng.choice([True, False]):
            # Horizontal first, then vertical
            # Move horizontally
            current_x, current_y = start_x, start_y
            while current_x != end_x:
                path.append((current_x, current_y))
                current_x += 1 if end_x > current_x else -1
            
            # Move vertically
            while current_y != end_y:
                path.append((current_x, current_y))
                current_y += 1 if end_y > current_y else -1
            
            path.append((end_x, end_y))
        else:
            # Vertical first, then horizontal
            # Move vertically
            current_x, current_y = start_x, start_y
            while current_y != end_y:
                path.append((current_x, current_y))
                current_y += 1 if end_y > current_y else -1
            
            # Move horizontally
            while current_x != end_x:
                path.append((current_x, current_y))
                current_x += 1 if end_x > current_x else -1
            
            path.append((end_x, end_y))
        
        return path
    
    def _carve_corridor(self, tiles: List[List[Tile]], corridor: Corridor) -> None:
        """Carve a corridor in the tile grid, preserving room walls except for door positions."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        for x, y in corridor.path:
            if 0 <= x < width and 0 <= y < height:
                # Only carve if this tile is not part of a room's wall perimeter
                # or if it's a designated door position
                if not self._is_room_wall_perimeter(x, y, corridor.room1, corridor.room2):
                    tiles[y][x].is_wall = False
                    tiles[y][x].tile_type = 'floor'
    
    def _is_room_wall_perimeter(self, x: int, y: int, room1: Room, room2: Room) -> bool:
        """Check if a position is part of a room's wall perimeter that should be preserved."""
        # Check if this position is on the perimeter of either room
        for room in [room1, room2]:
            if self._is_on_room_perimeter(x, y, room):
                # This is on a room perimeter - only allow carving if it's a valid door position
                if self._is_valid_door_position(x, y, room):
                    return False  # Allow carving for door positions
                else:
                    return True   # Preserve wall
        return False  # Not on any room perimeter, safe to carve
    
    def _is_on_room_perimeter(self, x: int, y: int, room: Room) -> bool:
        """Check if a position is on the perimeter (wall) of a room."""
        # Check if position is exactly on the room boundary
        on_left_wall = (x == room.x - 1 and room.y <= y <= room.bottom)
        on_right_wall = (x == room.right + 1 and room.y <= y <= room.bottom)
        on_top_wall = (y == room.y - 1 and room.x <= x <= room.right)
        on_bottom_wall = (y == room.bottom + 1 and room.x <= x <= room.right)
        
        return on_left_wall or on_right_wall or on_top_wall or on_bottom_wall
    
    def _is_valid_door_position(self, x: int, y: int, room: Room) -> bool:
        """Check if a position is a valid door position for a room."""
        # A valid door position should be:
        # 1. On the room perimeter (already checked by caller)
        # 2. Not at the corners of the room (leave corner walls intact)
        
        # Check if it's a corner position
        corner_positions = [
            (room.x - 1, room.y - 1),      # Top-left corner
            (room.right + 1, room.y - 1),  # Top-right corner
            (room.x - 1, room.bottom + 1), # Bottom-left corner
            (room.right + 1, room.bottom + 1) # Bottom-right corner
        ]
        
        if (x, y) in corner_positions:
            return False  # Don't allow doors at corners
        
        # Check if it's at the very edge of walls (preserve structural integrity)
        on_left_wall = (x == room.x - 1 and room.y <= y <= room.bottom)
        on_right_wall = (x == room.right + 1 and room.y <= y <= room.bottom)
        on_top_wall = (y == room.y - 1 and room.x <= x <= room.right)
        on_bottom_wall = (y == room.bottom + 1 and room.x <= x <= room.right)
        
        # For walls, don't allow doors at the very ends (preserve corner integrity)
        if on_left_wall or on_right_wall:
            return y != room.y and y != room.bottom  # Not at top or bottom edge
        if on_top_wall or on_bottom_wall:
            return x != room.x and x != room.right   # Not at left or right edge
        
        return True


class RogueDoorLayer(GenLayer):
    """
    Places doors where corridors connect to rooms.
    
    Places a single door at the entry point where each corridor connects to each room,
    following the original Rogue algorithm behavior.
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Place doors at room entrances."""
        rooms = ctx.parameters.get('rogue_rooms', [])
        corridors = ctx.parameters.get('rogue_corridors', [])
        
        if not rooms or not corridors:
            return
        
        # Find all door positions - one per room per corridor
        door_positions = self._find_door_positions(rooms, corridors)
        
        # Place doors and carve through walls at door positions
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        for x, y in door_positions:
            if 0 <= x < width and 0 <= y < height:
                # Carve through the wall to create the door opening
                tiles[y][x].is_wall = False
                tiles[y][x].tile_type = 'door_closed'
    
    def _find_door_positions(self, rooms: List[Room], corridors: List[Corridor]) -> Set[Tuple[int, int]]:
        """Find all positions where doors should be placed - one per room per corridor."""
        door_positions = set()
        
        for corridor in corridors:
            # Find the single entry point for each room
            room1_door = self._find_room_entry_point(corridor.room1, corridor.path)
            room2_door = self._find_room_entry_point(corridor.room2, corridor.path)
            
            if room1_door:
                door_positions.add(room1_door)
            if room2_door:
                door_positions.add(room2_door)
        
        return door_positions
    
    def _find_room_entry_point(self, room: Room, corridor_path: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find the single entry point where a corridor connects to a room."""
        # Look for the first point in the corridor path that is adjacent to the room
        for i, (x, y) in enumerate(corridor_path):
            if self._is_room_entry_point(x, y, room):
                return (x, y)
        
        return None
    
    def _is_room_entry_point(self, x: int, y: int, room: Room) -> bool:
        """Check if a position is a valid entry point to a room."""
        # Entry point should be exactly one tile away from the room boundary
        # and should be perpendicular to the room wall
        
        # Check if adjacent to room (within 1 tile)
        if not (room.x - 1 <= x <= room.right + 1 and room.y - 1 <= y <= room.bottom + 1):
            return False
        
        # Check if it's exactly on the room's perimeter (not inside the room)
        inside_room = (room.x <= x <= room.right and room.y <= y <= room.bottom)
        if inside_room:
            return False
        
        # Check if it's adjacent to a room wall (exactly 1 tile away)
        adjacent_to_left = (x == room.x - 1 and room.y <= y <= room.bottom)
        adjacent_to_right = (x == room.right + 1 and room.y <= y <= room.bottom)
        adjacent_to_top = (y == room.y - 1 and room.x <= x <= room.right)
        adjacent_to_bottom = (y == room.bottom + 1 and room.x <= x <= room.right)
        
        return adjacent_to_left or adjacent_to_right or adjacent_to_top or adjacent_to_bottom


class RoomsLayer(GenLayer):
    """
    Generates connected rooms starting from a downstairs location.
    
    Creates rooms by:
    - Starting at downstairs location from previous floor (if available) or random location
    - Generating rooms of random sizes within specified bounds
    - Each new room is placed adjacent to an existing room
    - Doors connect adjacent rooms
    - Respects 1-tile border around the entire map
    """
    
    def generate(self, tiles: List[List[Tile]], ctx: GenContext) -> None:
        """Generate connected rooms."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Initialize entire map as walls
        for y in range(height):
            for x in range(width):
                tiles[y][x].is_wall = True
                tiles[y][x].tile_type = 'wall'
        
        # Get parameters
        num_rooms = int(ctx.get_param('num_rooms', 6))
        min_room_size = int(ctx.get_param('min_room_size', 4))
        max_room_size = int(ctx.get_param('max_room_size', 8))
        
        # Find starting position (downstairs from previous floor or random)
        start_x, start_y = self._find_start_position(ctx, width, height)
        
        # Generate first room at starting position
        rooms = []
        doors = []
        
        first_room = self._create_room_at_position(start_x, start_y, min_room_size, max_room_size, 
                                                  width, height, [], ctx.rng)
        if first_room:
            rooms.append(first_room)
            self._carve_room(tiles, first_room)
        
        # Generate additional rooms
        for i in range(1, num_rooms):
            new_room, door_pos = self._create_adjacent_room(rooms, min_room_size, max_room_size,
                                                           width, height, ctx.rng)
            if new_room and door_pos:
                rooms.append(new_room)
                doors.append(door_pos)
                self._carve_room(tiles, new_room)
                self._place_door(tiles, door_pos)
        
        # Store rooms and doors in context for potential use by other layers
        ctx.parameters['rooms_rooms'] = rooms
        ctx.parameters['rooms_doors'] = doors
    
    def _find_start_position(self, ctx: GenContext, width: int, height: int) -> Tuple[int, int]:
        """Find starting position for first room."""
        # Check if there's a downstairs position from previous floor
        downstairs_pos = ctx.get_param('downstairs_position', None)
        
        if downstairs_pos and isinstance(downstairs_pos, (tuple, list)) and len(downstairs_pos) == 2:
            x, y = downstairs_pos
            # Ensure position is within valid bounds (respecting 1-tile border)
            if 1 <= x < width - 1 and 1 <= y < height - 1:
                return x, y
        
        # Generate random position within 1-tile border
        x = ctx.rng.randint(1, width - 2)
        y = ctx.rng.randint(1, height - 2)
        return x, y
    
    def _create_room_at_position(self, center_x: int, center_y: int, min_size: int, max_size: int,
                                width: int, height: int, existing_rooms: List[Room], 
                                rng: random.Random) -> Optional[Room]:
        """Create a room centered around the given position."""
        # Generate random room size
        room_width = rng.randint(min_size, max_size)
        room_height = rng.randint(min_size, max_size)
        
        # Calculate room position (try to center around given position)
        # Ensure there's enough space around the room for future adjacent rooms
        min_x = max(1, min_size + 2)  # Leave space for adjacent rooms
        max_x = min(width - room_width - min_size - 3, width - room_width - 1)
        min_y = max(1, min_size + 2)  # Leave space for adjacent rooms  
        max_y = min(height - room_height - min_size - 3, height - room_height - 1)
        
        # Clamp the centered position to valid bounds
        room_x = max(min_x, min(center_x - room_width // 2, max_x))
        room_y = max(min_y, min(center_y - room_height // 2, max_y))
        
        # Final bounds check
        if (room_x < 1 or room_y < 1 or 
            room_x + room_width >= width - 1 or room_y + room_height >= height - 1):
            return None
        
        # Check for collisions with existing rooms
        new_room = Room(room_x, room_y, room_width, room_height, 0, 0)
        if self._room_collides(new_room, existing_rooms):
            return None
        
        return new_room
    
    def _create_adjacent_room(self, existing_rooms: List[Room], min_size: int, max_size: int,
                             width: int, height: int, rng: random.Random) -> Tuple[Optional[Room], Optional[Tuple[int, int]]]:
        """Create a new room adjacent to an existing room."""
        # Try each existing room as a potential anchor
        anchor_rooms = existing_rooms.copy()
        rng.shuffle(anchor_rooms)
        
        for anchor_room in anchor_rooms:
            # Try each side of the anchor room
            sides = ['north', 'south', 'east', 'west']
            rng.shuffle(sides)
            
            for side in sides:
                new_room, door_pos = self._try_place_room_on_side(anchor_room, side, min_size, max_size,
                                                                 width, height, existing_rooms, rng)
                if new_room and door_pos:
                    return new_room, door_pos
        
        return None, None
    
    def _try_place_room_on_side(self, anchor_room: Room, side: str, min_size: int, max_size: int,
                               width: int, height: int, existing_rooms: List[Room], 
                               rng: random.Random) -> Tuple[Optional[Room], Optional[Tuple[int, int]]]:
        """Try to place a room on the specified side of the anchor room."""
        # Generate random room size
        room_width = rng.randint(min_size, max_size)
        room_height = rng.randint(min_size, max_size)
        
        # Calculate room position based on side
        if side == 'north':
            # Place room above anchor room
            room_y = anchor_room.y - room_height - 1
            # Check if room fits vertically
            if room_y < 1:
                return None, None
            
            # Calculate horizontal position with some overlap potential
            min_x = max(1, anchor_room.x - room_width + 2)  # Allow some overlap
            max_x = min(anchor_room.right - 1, width - room_width - 1)
            if min_x > max_x:
                return None, None
            room_x = rng.randint(min_x, max_x)
            
            # Door position - in the wall between rooms
            door_y = anchor_room.y - 1
            door_x = rng.randint(max(anchor_room.x, room_x), min(anchor_room.right, room_x + room_width - 1))
            
        elif side == 'south':
            # Place room below anchor room
            room_y = anchor_room.bottom + 2
            # Check if room fits vertically
            if room_y + room_height >= height - 1:
                return None, None
            
            # Calculate horizontal position with some overlap potential
            min_x = max(1, anchor_room.x - room_width + 2)  # Allow some overlap
            max_x = min(anchor_room.right - 1, width - room_width - 1)
            if min_x > max_x:
                return None, None
            room_x = rng.randint(min_x, max_x)
            
            # Door position - in the wall between rooms
            door_y = anchor_room.bottom + 1
            door_x = rng.randint(max(anchor_room.x, room_x), min(anchor_room.right, room_x + room_width - 1))
            
        elif side == 'west':
            # Place room to the left of anchor room
            room_x = anchor_room.x - room_width - 1
            # Check if room fits horizontally
            if room_x < 1:
                return None, None
            
            # Calculate vertical position with some overlap potential
            min_y = max(1, anchor_room.y - room_height + 2)  # Allow some overlap
            max_y = min(anchor_room.bottom - 1, height - room_height - 1)
            if min_y > max_y:
                return None, None
            room_y = rng.randint(min_y, max_y)
            
            # Door position - in the wall between rooms
            door_x = anchor_room.x - 1
            door_y = rng.randint(max(anchor_room.y, room_y), min(anchor_room.bottom, room_y + room_height - 1))
            
        else:  # east
            # Place room to the right of anchor room
            room_x = anchor_room.right + 2
            # Check if room fits horizontally
            if room_x + room_width >= width - 1:
                return None, None
            
            # Calculate vertical position with some overlap potential
            min_y = max(1, anchor_room.y - room_height + 2)  # Allow some overlap
            max_y = min(anchor_room.bottom - 1, height - room_height - 1)
            if min_y > max_y:
                return None, None
            room_y = rng.randint(min_y, max_y)
            
            # Door position - in the wall between rooms
            door_x = anchor_room.right + 1
            door_y = rng.randint(max(anchor_room.y, room_y), min(anchor_room.bottom, room_y + room_height - 1))
        
        # Final bounds check
        if (room_x < 1 or room_y < 1 or 
            room_x + room_width >= width - 1 or room_y + room_height >= height - 1):
            return None, None
        
        # Check door position bounds
        if door_x < 1 or door_y < 1 or door_x >= width - 1 or door_y >= height - 1:
            return None, None
        
        # Create room and check for collisions
        new_room = Room(room_x, room_y, room_width, room_height, 0, 0)
        if self._room_collides(new_room, existing_rooms):
            return None, None
        
        return new_room, (door_x, door_y)
    
    def _room_collides(self, new_room: Room, existing_rooms: List[Room]) -> bool:
        """Check if a new room collides with any existing rooms or touches at corners."""
        for existing_room in existing_rooms:
            # Check if rooms overlap (not allowing any overlap)
            if (new_room.x <= existing_room.right and 
                new_room.right >= existing_room.x and
                new_room.y <= existing_room.bottom and 
                new_room.bottom >= existing_room.y):
                return True
            
            # Check for corner touching (diagonal adjacency) - prevent this
            # Check all four corners of the new room against all four corners of existing room
            new_corners = [
                (new_room.x, new_room.y),                    # top-left
                (new_room.right, new_room.y),                # top-right
                (new_room.x, new_room.bottom),               # bottom-left
                (new_room.right, new_room.bottom)            # bottom-right
            ]
            
            existing_corners = [
                (existing_room.x, existing_room.y),          # top-left
                (existing_room.right, existing_room.y),      # top-right
                (existing_room.x, existing_room.bottom),     # bottom-left
                (existing_room.right, existing_room.bottom)  # bottom-right
            ]
            
            # Check if any corner of new room touches any corner of existing room
            for new_corner in new_corners:
                for existing_corner in existing_corners:
                    if new_corner == existing_corner:
                        return True  # Corner touching detected
            
            # Also check if corners are diagonally adjacent (1 tile away diagonally)
            for new_x, new_y in new_corners:
                for existing_x, existing_y in existing_corners:
                    dx = abs(new_x - existing_x)
                    dy = abs(new_y - existing_y)
                    if dx == 1 and dy == 1:  # Diagonally adjacent
                        return True
        
        return False
    
    def _carve_room(self, tiles: List[List[Tile]], room: Room) -> None:
        """Carve out a room in the tile grid."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
                    tiles[y][x].is_wall = False
                    tiles[y][x].tile_type = 'floor'
    
    def _place_door(self, tiles: List[List[Tile]], door_pos: Tuple[int, int]) -> None:
        """Place a door at the specified position."""
        x, y = door_pos
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            tiles[y][x].is_wall = False
            tiles[y][x].tile_type = 'door_closed'
