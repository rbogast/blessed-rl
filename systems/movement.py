"""
Movement system for handling entity movement and collision detection.
"""

from ecs.system import System
from components.core import Position, Blocking, Door, Renderable
from components.combat import Health
from game.level_world_gen import LevelWorldGenerator
from game.config import GameConfig
from typing import Set


class MovementSystem(System):
    """Handles movement and collision detection."""
    
    def __init__(self, world, world_generator: LevelWorldGenerator, message_log):
        super().__init__(world)
        self.world_generator = world_generator
        self.message_log = message_log
    
    def update(self, dt: float = 0.0) -> None:
        """Movement system doesn't auto-update - it responds to action requests."""
        pass
    
    def try_move_entity(self, entity_id: int, dx: int, dy: int) -> bool:
        """Attempt to move an entity by the given offset."""
        position = self.world.get_component(entity_id, Position)
        if not position:
            return False
        
        new_x = position.x + dx
        new_y = position.y + dy
        
        # Check bounds using centralized config
        if not GameConfig.is_valid_y(new_y):
            return False
        
        # Check for doors first - they can be opened
        door_entity = self._get_door_at_position(new_x, new_y)
        if door_entity is not None:
            door = self.world.get_component(door_entity, Door)
            if door and not door.is_open:
                # Open the door and move to its position
                self._open_door(door_entity)
                position.x = new_x
                position.y = new_y
                return True
        
        # Check for collision
        if self._is_position_blocked(new_x, new_y, entity_id):
            return False
        
        # Move the entity
        position.x = new_x
        position.y = new_y
        
        return True
    
    def try_move_to(self, entity_id: int, target_x: int, target_y: int) -> bool:
        """Attempt to move an entity to a specific position."""
        position = self.world.get_component(entity_id, Position)
        if not position:
            return False
        
        # Check bounds using centralized config
        if not GameConfig.is_valid_y(target_y):
            return False
        
        # Check for collision
        if self._is_position_blocked(target_x, target_y, entity_id):
            return False
        
        # Move the entity
        position.x = target_x
        position.y = target_y
        
        return True
    
    def _is_position_blocked(self, x: int, y: int, moving_entity: int = None) -> bool:
        """Check if a position is blocked by walls or other entities."""
        # Check for walls
        if self.world_generator.is_wall_at(x, y):
            return True
        
        # Check for blocking entities
        blocking_entities = self.world.get_entities_with_components(Position, Blocking)
        
        for entity_id in blocking_entities:
            if entity_id == moving_entity:
                continue  # Don't check collision with self
            
            entity_pos = self.world.get_component(entity_id, Position)
            if entity_pos and entity_pos.x == x and entity_pos.y == y:
                return True
        
        return False
    
    def get_entity_at_position(self, x: int, y: int) -> int:
        """Get the first entity at the given position, or None."""
        entities_with_position = self.world.get_entities_with_components(Position)
        
        for entity_id in entities_with_position:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                return entity_id
        
        return None
    
    def get_blocking_entity_at(self, x: int, y: int) -> int:
        """Get the blocking entity at the given position, or None."""
        blocking_entities = self.world.get_entities_with_components(Position, Blocking)
        
        for entity_id in blocking_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                return entity_id
        
        return None
    
    def get_entities_in_radius(self, center_x: int, center_y: int, radius: int) -> Set[int]:
        """Get all entities within a given radius of a position."""
        entities = set()
        entities_with_position = self.world.get_entities_with_components(Position)
        
        for entity_id in entities_with_position:
            position = self.world.get_component(entity_id, Position)
            if position:
                dx = abs(position.x - center_x)
                dy = abs(position.y - center_y)
                distance = max(dx, dy)  # Chebyshev distance (8-directional)
                
                if distance <= radius:
                    entities.add(entity_id)
        
        return entities
    
    def calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Chebyshev distance between two points."""
        return max(abs(x2 - x1), abs(y2 - y1))
    
    def get_direction_to(self, from_x: int, from_y: int, to_x: int, to_y: int) -> tuple:
        """Get the direction (dx, dy) to move from one point toward another."""
        dx = 0
        dy = 0
        
        if to_x > from_x:
            dx = 1
        elif to_x < from_x:
            dx = -1
        
        if to_y > from_y:
            dy = 1
        elif to_y < from_y:
            dy = -1
        
        return dx, dy
    
    def _get_door_at_position(self, x: int, y: int) -> int:
        """Get the door entity at the given position, or None."""
        door_entities = self.world.get_entities_with_components(Position, Door)
        
        for entity_id in door_entities:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                return entity_id
        
        return None
    
    def _open_door(self, door_entity: int) -> None:
        """Open a door entity."""
        door = self.world.get_component(door_entity, Door)
        renderable = self.world.get_component(door_entity, Renderable)
        
        if door and not door.is_open:
            # Open the door
            door.is_open = True
            
            # Update visual representation
            if renderable:
                renderable.char = '-'  # Open door character
            
            # Remove blocking component so entities can pass through
            if self.world.has_component(door_entity, Blocking):
                self.world.remove_component(door_entity, Blocking)
            
            # Log the action
            if self.message_log:
                self.message_log.add_info("You open the door.")
