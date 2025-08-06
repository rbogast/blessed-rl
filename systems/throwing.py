"""
Throwing system for handling item throwing mechanics.
"""

from ecs.system import System
from components.core import Position, Player
from components.throwing import ThrowingCursor, ThrownObject
from components.items import Inventory, Item, Throwable
from components.effects import Physics
from components.character import CharacterAttributes
from components.skills import Skills
from components.ai import AI
from utils.line_drawing import draw_line, calculate_distance
import random
from typing import Optional, Tuple, List


class ThrowingSystem(System):
    """Handles throwing mechanics and cursor management."""
    
    def __init__(self, world, movement_system, fov_system, physics_system, 
                 skills_system, message_log):
        super().__init__(world)
        self.movement_system = movement_system
        self.fov_system = fov_system
        self.physics_system = physics_system
        self.skills_system = skills_system
        self.message_log = message_log
    
    def update(self, dt: float = 0.0) -> None:
        """Update throwing system - process thrown objects."""
        # Process any thrown objects that need to land
        thrown_entities = self.world.get_entities_with_components(ThrownObject, Position)
        for entity_id in thrown_entities:
            self._process_thrown_object(entity_id)
    
    def start_throwing(self, player_entity: int, selected_item: int) -> bool:
        """Start the throwing process with cursor targeting."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return False
        
        # Find initial cursor position
        cursor_x, cursor_y = self._find_initial_cursor_position(player_entity)
        
        # Create throwing cursor component
        cursor = ThrowingCursor(cursor_x, cursor_y, selected_item)
        self.world.add_component(player_entity, cursor)
        
        self.message_log.add_info("Select target with arrow keys, Enter to throw, Escape to cancel.")
        return True
    
    def move_cursor(self, player_entity: int, dx: int, dy: int) -> bool:
        """Move the throwing cursor."""
        cursor = self.world.get_component(player_entity, ThrowingCursor)
        player_pos = self.world.get_component(player_entity, Position)
        
        if not cursor or not player_pos:
            return False
        
        new_x = cursor.cursor_x + dx
        new_y = cursor.cursor_y + dy
        
        # Check if new position is within FOV
        if not self.fov_system.is_visible(new_x, new_y):
            return False
        
        # Check if within reasonable range (5 tiles as specified)
        distance = calculate_distance(player_pos.x, player_pos.y, new_x, new_y)
        if distance > 5:
            return False
        
        cursor.move_cursor(new_x, new_y)
        return True
    
    def execute_throw(self, player_entity: int) -> bool:
        """Execute the throw action."""
        cursor = self.world.get_component(player_entity, ThrowingCursor)
        player_pos = self.world.get_component(player_entity, Position)
        inventory = self.world.get_component(player_entity, Inventory)
        
        if not cursor or not player_pos or not inventory:
            return False
        
        # Get the item being thrown
        item_entity = cursor.selected_item
        if item_entity not in inventory.items:
            self.message_log.add_warning("Item no longer in inventory!")
            return False
        
        # Remove item from inventory
        inventory.remove_item(item_entity)
        
        # Get player stats
        attributes = self.world.get_component(player_entity, CharacterAttributes)
        skills = self.world.get_component(player_entity, Skills)
        
        strength = attributes.strength if attributes else 10
        agility = attributes.agility if attributes else 10
        throwing_skill = skills.get_skill('throwing') if skills else 1
        
        # Get item weight
        item_weight = self._get_item_weight(item_entity)
        
        # Calculate maximum throwing distance
        max_distance = self.skills_system.calculate_throwing_distance(strength, item_weight)
        
        # Calculate actual throw
        target_distance = calculate_distance(player_pos.x, player_pos.y, cursor.cursor_x, cursor.cursor_y)
        accuracy = self.skills_system.calculate_throwing_accuracy(throwing_skill, target_distance, agility)
        
        # Determine actual landing position
        actual_x, actual_y = self._calculate_landing_position(
            player_pos.x, player_pos.y, cursor.cursor_x, cursor.cursor_y,
            max_distance, accuracy
        )
        
        # Check if this is an active light source before moving
        from components.items import LightEmitter
        light = self.world.get_component(item_entity, LightEmitter)
        is_active_light = light and light.active
        
        # Move item to landing position
        item_pos = self.world.get_component(item_entity, Position)
        if not item_pos:
            item_pos = Position(actual_x, actual_y)
            self.world.add_component(item_entity, item_pos)
        else:
            item_pos.x = actual_x
            item_pos.y = actual_y
        
        # Force FOV recalculation if throwing an active light source
        if is_active_light and self.fov_system:
            self.fov_system.force_recalculation()
        
        # Add thrown object component for processing
        thrown_obj = ThrownObject(cursor.cursor_x, cursor.cursor_y, player_entity, 
                                throwing_skill, strength)
        self.world.add_component(item_entity, thrown_obj)
        
        # Try to gain throwing skill
        difficulty = min(90, target_distance * 10 + 20)  # Higher difficulty for longer throws
        self.skills_system.try_skill_gain(player_entity, 'throwing', difficulty)
        
        # Clean up cursor
        self.world.remove_component(player_entity, ThrowingCursor)
        
        # Log the throw
        item = self.world.get_component(item_entity, Item)
        item_name = item.name if item else "item"
        if actual_x == cursor.cursor_x and actual_y == cursor.cursor_y:
            self.message_log.add_combat(f"You throw the {item_name} accurately!")
        else:
            self.message_log.add_combat(f"You throw the {item_name}, but it goes off target.")
        
        return True
    
    def cancel_throwing(self, player_entity: int) -> bool:
        """Cancel the throwing action."""
        cursor = self.world.get_component(player_entity, ThrowingCursor)
        if cursor:
            self.world.remove_component(player_entity, ThrowingCursor)
            self.message_log.add_info("Throwing cancelled.")
            return True
        return False
    
    def is_throwing_active(self, player_entity: int) -> bool:
        """Check if player is currently in throwing mode."""
        return self.world.has_component(player_entity, ThrowingCursor)
    
    def get_cursor_position(self, player_entity: int) -> Optional[Tuple[int, int]]:
        """Get current cursor position."""
        cursor = self.world.get_component(player_entity, ThrowingCursor)
        if cursor:
            return (cursor.cursor_x, cursor.cursor_y)
        return None
    
    def get_throwing_line(self, player_entity: int) -> List[Tuple[int, int]]:
        """Get the line from player to cursor for rendering."""
        cursor = self.world.get_component(player_entity, ThrowingCursor)
        player_pos = self.world.get_component(player_entity, Position)
        
        if not cursor or not player_pos:
            return []
        
        return draw_line(player_pos.x, player_pos.y, cursor.cursor_x, cursor.cursor_y)
    
    def _find_initial_cursor_position(self, player_entity: int) -> Tuple[int, int]:
        """Find initial cursor position - nearest enemy or random visible tile."""
        player_pos = self.world.get_component(player_entity, Position)
        if not player_pos:
            return (0, 0)
        
        # Look for nearest enemy within 5 tiles
        nearest_enemy = None
        nearest_distance = float('inf')
        
        ai_entities = self.world.get_entities_with_components(AI, Position)
        for entity_id in ai_entities:
            entity_pos = self.world.get_component(entity_id, Position)
            if entity_pos:
                distance = calculate_distance(player_pos.x, player_pos.y, entity_pos.x, entity_pos.y)
                if distance <= 5 and self.fov_system.is_visible(entity_pos.x, entity_pos.y):
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_enemy = entity_pos
        
        if nearest_enemy:
            return (nearest_enemy.x, nearest_enemy.y)
        
        # No enemy found, pick a random visible tile within 5 tiles
        for attempt in range(20):  # Try 20 random positions
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            test_x = player_pos.x + dx
            test_y = player_pos.y + dy
            
            if (calculate_distance(player_pos.x, player_pos.y, test_x, test_y) <= 5 and
                self.fov_system.is_visible(test_x, test_y)):
                return (test_x, test_y)
        
        # Fallback to adjacent tile
        return (player_pos.x + 1, player_pos.y)
    
    def _get_item_weight(self, item_entity: int) -> float:
        """Get the weight of an item."""
        throwable = self.world.get_component(item_entity, Throwable)
        if throwable:
            return throwable.weight
        
        physics = self.world.get_component(item_entity, Physics)
        if physics:
            return physics.mass
        
        return 1.0  # Default weight
    
    def _calculate_landing_position(self, start_x: int, start_y: int, target_x: int, target_y: int,
                                  max_distance: int, accuracy: float) -> Tuple[int, int]:
        """Calculate where the item actually lands based on accuracy and distance."""
        target_distance = calculate_distance(start_x, start_y, target_x, target_y)
        
        # If throw is beyond max distance, reduce the distance
        if target_distance > max_distance:
            # Calculate direction and limit distance
            dx = target_x - start_x
            dy = target_y - start_y
            
            # Normalize and scale to max distance
            if dx != 0 or dy != 0:
                factor = max_distance / target_distance
                dx = int(dx * factor)
                dy = int(dy * factor)
            
            target_x = start_x + dx
            target_y = start_y + dy
            target_distance = max_distance
        
        # Apply accuracy deviation
        if accuracy < 1.0:
            max_deviation = int((1.0 - accuracy) * target_distance + 1)
            deviation_x = random.randint(-max_deviation, max_deviation)
            deviation_y = random.randint(-max_deviation, max_deviation)
            
            target_x += deviation_x
            target_y += deviation_y
        
        return (target_x, target_y)
    
    def _process_thrown_object(self, item_entity: int) -> None:
        """Process a thrown object for collision and damage."""
        thrown_obj = self.world.get_component(item_entity, ThrownObject)
        item_pos = self.world.get_component(item_entity, Position)
        
        if not thrown_obj or not item_pos or thrown_obj.has_landed:
            return
        
        # Mark as landed
        thrown_obj.has_landed = True
        
        # Check for collision with entities at landing position
        target_entity = self.movement_system.get_blocking_entity_at(item_pos.x, item_pos.y)
        
        if target_entity:
            # Calculate damage
            item_weight = self._get_item_weight(item_entity)
            distance_thrown = calculate_distance(
                self.world.get_component(thrown_obj.thrower_id, Position).x,
                self.world.get_component(thrown_obj.thrower_id, Position).y,
                item_pos.x, item_pos.y
            )
            
            throwable = self.world.get_component(item_entity, Throwable)
            damage_modifier = throwable.damage_modifier if throwable else 1.0
            
            damage = self.skills_system.calculate_throwing_damage(
                item_weight, distance_thrown, thrown_obj.strength, damage_modifier
            )
            
            # Apply damage and knockback
            from components.combat import Health
            health = self.world.get_component(target_entity, Health)
            if health:
                health.take_damage(damage)
                
                # Get target name for message
                target_name = self._get_entity_name(target_entity)
                item = self.world.get_component(item_entity, Item)
                item_name = item.name if item else "object"
                
                self.message_log.add_combat(f"The {item_name} hits the {target_name} for {damage} damage!")
            
            # Apply knockback
            if self.physics_system:
                knockback_force = item_weight * 5  # 5 force per pound
                self.physics_system.apply_knockback(
                    target_entity, knockback_force, 0, 0, 
                    item_pos.x - 1, item_pos.y  # Approximate source position
                )
        
        # Remove thrown object component
        self.world.remove_component(item_entity, ThrownObject)
    
    def _get_entity_name(self, entity_id: int) -> str:
        """Get display name for an entity."""
        if self.world.has_component(entity_id, Player):
            return "player"
        
        ai = self.world.get_component(entity_id, AI)
        if ai:
            return ai.ai_type.value
        
        return "entity"
