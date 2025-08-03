"""
Maze template using Recursive Backtracking algorithm.
"""

from typing import Dict
from .base import MapTemplate, ParameterDef
from ..maze_generator import MazeRoomLayer, RecursiveBacktrackingLayer, MazeInterconnectionLayer, MazeBorderLayer


class MazeTemplate(MapTemplate):
    """
    Maze template using Recursive Backtracking algorithm.
    
    Creates a perfect maze where:
    - Even coordinates are walls
    - Odd coordinates are corridors
    - Full border of walls
    - Exactly one path between any two points
    - Stairs are placed at dead ends for optimal gameplay
    """
    
    name = "maze"
    
    def __init__(self):
        super().__init__()
    
    def get_parameters(self) -> Dict[str, ParameterDef]:
        """Return the parameters this template exposes for editing."""
        return {
            'maze_openings': ParameterDef(int, 0, 20, 5),
            'num_rooms': ParameterDef(int, 0, 10, 0),
            'min_room_size': ParameterDef(int, 3, 15, 5),  # Must be odd
            'max_room_size': ParameterDef(int, 3, 15, 9),  # Must be odd, now allows 3x3 rooms
        }
    
    def _setup_layers(self) -> None:
        """Set up the generation layers for maze generation."""
        self.layers = [
            MazeRoomLayer(),  # Generate rooms first
            RecursiveBacktrackingLayer(),
            MazeInterconnectionLayer(),  # Add interconnections for tactical options
            MazeBorderLayer(),  # Ensure border integrity
        ]
    
    def generate_with_stairs(self, tiles, ctx, start_position=None):
        """Generate maze with stair-aware placement. Returns suggested downstairs position."""
        # Get the recursive backtracking layer
        maze_layer = self.layers[1]  # RecursiveBacktrackingLayer
        
        # Generate rooms first
        room_layer = self.layers[0]  # MazeRoomLayer
        room_layer.generate(tiles, ctx)
        
        # Get room information for smart stair placement
        rooms = ctx.parameters.get('maze_rooms', [])
        
        # Determine smart stair positions based on rooms
        smart_start, suggested_downstairs = self._determine_stair_positions(tiles, ctx, start_position, rooms)
        
        # Generate base maze starting from smart upstairs position
        actual_downstairs = maze_layer.generate_with_stairs(tiles, ctx, smart_start)
        
        # Apply interconnection layer (before final stair placement)
        interconnection_layer = self.layers[2]  # MazeInterconnectionLayer
        interconnection_layer.generate(tiles, ctx)
        
        # Apply border layer
        border_layer = self.layers[3]  # MazeBorderLayer
        border_layer.generate(tiles, ctx)
        
        # Return the actual downstairs position from maze generation
        return actual_downstairs if actual_downstairs else suggested_downstairs
    
    def _determine_stair_positions(self, tiles, ctx, start_position, rooms):
        """Determine optimal stair positions based on room availability."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        if not rooms:
            # No rooms - use original logic
            return start_position, None
        
        # Find room centers for potential stair placement
        room_centers = []
        for room in rooms:
            center_x = room.x + room.width // 2
            center_y = room.y + room.height // 2
            room_centers.append((center_x, center_y, room))
        
        if len(rooms) == 1:
            # Only one room - place one stair in room, one in corridor
            room_center = room_centers[0]
            if start_position:
                # Upstairs position is specified - check if it's in the room
                up_x, up_y = start_position
                room = room_center[2]
                if (room.x <= up_x < room.x + room.width and 
                    room.y <= up_y < room.y + room.height):
                    # Upstairs is in room - place downstairs in corridor
                    return start_position, self._find_corridor_position(tiles, rooms, ctx.rng)
                else:
                    # Upstairs is in corridor - place downstairs in room
                    return start_position, room_center[:2]
            else:
                # No upstairs specified - place upstairs in room center
                return room_center[:2], self._find_corridor_position(tiles, rooms, ctx.rng)
        
        elif len(rooms) >= 2:
            # Multiple rooms - place stairs in different rooms
            if start_position:
                # Find which room the upstairs is in (if any)
                up_x, up_y = start_position
                upstairs_room = None
                for room in rooms:
                    if (room.x <= up_x < room.x + room.width and 
                        room.y <= up_y < room.y + room.height):
                        upstairs_room = room
                        break
                
                if upstairs_room:
                    # Upstairs is in a room - find a different room for downstairs
                    other_rooms = [r for r in rooms if r != upstairs_room]
                    if other_rooms:
                        down_room = ctx.rng.choice(other_rooms)
                        down_center_x = down_room.x + down_room.width // 2
                        down_center_y = down_room.y + down_room.height // 2
                        return start_position, (down_center_x, down_center_y)
                    else:
                        # Fallback to corridor
                        return start_position, self._find_corridor_position(tiles, rooms, ctx.rng)
                else:
                    # Upstairs is in corridor - place downstairs in any room
                    down_room = ctx.rng.choice(rooms)
                    down_center_x = down_room.x + down_room.width // 2
                    down_center_y = down_room.y + down_room.height // 2
                    return start_position, (down_center_x, down_center_y)
            else:
                # No upstairs specified - place both in different rooms
                selected_rooms = ctx.rng.sample(rooms, min(2, len(rooms)))
                up_room = selected_rooms[0]
                down_room = selected_rooms[1] if len(selected_rooms) > 1 else selected_rooms[0]
                
                up_center_x = up_room.x + up_room.width // 2
                up_center_y = up_room.y + up_room.height // 2
                down_center_x = down_room.x + down_room.width // 2
                down_center_y = down_room.y + down_room.height // 2
                
                return (up_center_x, up_center_y), (down_center_x, down_center_y)
        
        # Fallback to original logic
        return start_position, None
    
    def _find_corridor_position(self, tiles, rooms, rng):
        """Find a valid position in a corridor (not in any room)."""
        height = len(tiles)
        width = len(tiles[0]) if height > 0 else 0
        
        # Create set of room positions
        room_positions = set()
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    room_positions.add((x, y))
        
        # Find corridor positions (odd coordinates, not walls, not in rooms)
        corridor_positions = []
        for y in range(1, height - 1, 2):  # Odd coordinates only
            for x in range(1, width - 1, 2):
                if ((x, y) not in room_positions and 
                    0 <= y < height and 0 <= x < width and
                    not tiles[y][x].is_wall):
                    corridor_positions.append((x, y))
        
        if corridor_positions:
            return rng.choice(corridor_positions)
        
        # Fallback - any non-room floor position
        for y in range(height):
            for x in range(width):
                if ((x, y) not in room_positions and 
                    not tiles[y][x].is_wall):
                    corridor_positions.append((x, y))
        
        if corridor_positions:
            return rng.choice(corridor_positions)
        
        return None
