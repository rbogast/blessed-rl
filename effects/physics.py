"""
Physics system for knockback and collision effects.
"""

import math
import random
from typing import Set, Tuple, Optional, TYPE_CHECKING
from .core import Effect
from components.core import Position
from components.effects import Physics
from components.combat import Health

if TYPE_CHECKING:
    from ecs.world import World


class PhysicsSystem:
    """Handles physics calculations and entity movement from forces."""
    
    def __init__(self, world: 'World', movement_system, message_log, render_system=None, camera=None):
        self.world = world
        self.movement_system = movement_system
        self.message_log = message_log
        self.render_system = render_system
        self.camera = camera
    
    def update(self, dt: float = 0.0) -> None:
        """Update physics system - currently no per-turn processing needed."""
        # Physics effects are applied immediately when triggered
        # No ongoing physics simulation needed for turn-based game
        pass
    
    def apply_knockback(self, entity_id: int, force: float, direction_x: int, direction_y: int, source_x: int, source_y: int) -> None:
        """Apply knockback force to an entity."""
        physics = self.world.get_component(entity_id, Physics)
        position = self.world.get_component(entity_id, Position)
        
        if not physics or not position:
            return
        
        # Calculate knockback distance based on force and mass
        # Further reduced knockback for more balanced gameplay
        # Troll (300lbs) should move 1-2 tiles, Skeleton (80lbs) should move ~6 tiles
        mass_factor = physics.mass / 50.0  # Normalize mass around 150lbs = 3.0
        knockback_distance = max(1, int(force / (mass_factor * 4.0)))
        
        # Normalize direction
        if direction_x == 0 and direction_y == 0:
            # Calculate direction from source to target
            direction_x = position.x - source_x
            direction_y = position.y - source_y
            
            # Normalize
            if direction_x == 0 and direction_y == 0:
                direction_x = random.choice([-1, 0, 1])
                direction_y = random.choice([-1, 0, 1])
        
        # Ensure we have some direction
        if direction_x == 0 and direction_y == 0:
            direction_x = 1
        
        # Calculate step direction (normalize to -1, 0, or 1)
        step_x = 0 if direction_x == 0 else (1 if direction_x > 0 else -1)
        step_y = 0 if direction_y == 0 else (1 if direction_y > 0 else -1)
        
        # Apply knockback movement step by step using movement system for validation
        damage_taken = 0
        tiles_moved = 0
        from components.core import Player
        is_player = self.world.has_component(entity_id, Player)
        
        for step in range(knockback_distance):
            # Try to move one step in the knockback direction
            if self.movement_system.try_move_entity(entity_id, step_x, step_y):
                tiles_moved += 1
                
                # Invalidate render cache since entity moved
                if self.render_system:
                    self.render_system.invalidate_cache()
                
                # Update camera if player was knocked back
                if is_player and self.camera:
                    new_position = self.world.get_component(entity_id, Position)
                    if new_position:
                        self.camera.follow_entity(new_position.x, new_position.y)
            else:
                # Movement was blocked - take collision damage
                collision_damage = max(2, int(force / 2))  # Increased collision damage based on force
                damage_taken += collision_damage
                
                # Check what we hit
                target_x = position.x + step_x
                target_y = position.y + step_y
                blocking_entity = self.movement_system.get_blocking_entity_at(target_x, target_y)
                
                if blocking_entity:
                    # Hit another entity - both take damage
                    self._apply_collision_damage(entity_id, blocking_entity, collision_damage)
                else:
                    # Hit a wall
                    self._apply_wall_collision_damage(entity_id, collision_damage)
                
                break
        
        # Apply minor knockback damage (separate from collision damage)
        if tiles_moved > 0:
            knockback_damage = max(1, int(force / 10))  # Small damage from being knocked back
            health = self.world.get_component(entity_id, Health)
            if health:
                health.take_damage(knockback_damage)
        
        # Generate message
        entity_name = self._get_entity_name(entity_id)
        if tiles_moved > 0:
            self.message_log.add_combat(f"The {entity_name} is knocked back {tiles_moved} tiles!")
        if damage_taken > 0:
            self.message_log.add_combat(f"The {entity_name} takes {damage_taken} collision damage!")
    
    def _is_position_blocked(self, x: int, y: int, moving_entity: int) -> bool:
        """Check if a position is blocked for movement."""
        return self.movement_system._is_position_blocked(x, y, moving_entity)
    
    def _apply_collision_damage(self, entity1_id: int, entity2_id: int, base_damage: int) -> None:
        """Apply damage when two entities collide."""
        health1 = self.world.get_component(entity1_id, Health)
        health2 = self.world.get_component(entity2_id, Health)
        
        if health1:
            health1.take_damage(base_damage)
        
        if health2:
            # Entity being hit takes less damage
            health2.take_damage(max(1, base_damage // 2))
        
        name1 = self._get_entity_name(entity1_id)
        name2 = self._get_entity_name(entity2_id)
        self.message_log.add_combat(f"The {name1} slams into the {name2}!")
    
    def _apply_wall_collision_damage(self, entity_id: int, damage: int) -> None:
        """Apply damage when entity hits a wall."""
        health = self.world.get_component(entity_id, Health)
        if health:
            health.take_damage(damage)
        
        entity_name = self._get_entity_name(entity_id)
        self.message_log.add_combat(f"The {entity_name} slams into a wall!")
    
    def _get_entity_name(self, entity_id: int) -> str:
        """Get display name for an entity."""
        from utils.entity_naming import get_entity_name
        return get_entity_name(self.world, entity_id)


class KnockbackEffect(Effect):
    """Effect that applies knockback to entities in a radius."""
    
    def __init__(self, physics_system: PhysicsSystem):
        super().__init__("knockback")
        self.physics_system = physics_system
    
    def apply(self, world: 'World', **context) -> None:
        """Apply knockback effect."""
        target_id = context.get('target_id')
        force = context.get('force', 20.0)
        source_x = context.get('source_x', 0)
        source_y = context.get('source_y', 0)
        direction_x = context.get('direction_x', 0)
        direction_y = context.get('direction_y', 0)
        
        if target_id is None:
            return
        
        # Ensure target has physics component
        if not world.has_component(target_id, Physics):
            world.add_component(target_id, Physics())
        
        self.physics_system.apply_knockback(
            target_id, force, direction_x, direction_y, source_x, source_y
        )


class ShockwaveEffect(Effect):
    """Effect that applies knockback to all entities in a radius."""
    
    def __init__(self, physics_system: PhysicsSystem, movement_system):
        super().__init__("shockwave")
        self.physics_system = physics_system
        self.movement_system = movement_system
    
    def apply(self, world: 'World', **context) -> None:
        """Apply shockwave effect to all entities in radius."""
        center_x = context.get('center_x', 0)
        center_y = context.get('center_y', 0)
        radius = context.get('radius', 3)
        force = context.get('force', 30.0)
        damage = context.get('damage', 5)
        
        # Get all entities in radius
        affected_entities = self.movement_system.get_entities_in_radius(
            center_x, center_y, radius
        )
        
        for entity_id in affected_entities:
            # Skip if entity is at the center (usually the caster)
            position = world.get_component(entity_id, Position)
            if position and position.x == center_x and position.y == center_y:
                continue
            
            # Ensure entity has physics component
            if not world.has_component(entity_id, Physics):
                world.add_component(entity_id, Physics())
            
            # Apply shockwave damage
            health = world.get_component(entity_id, Health)
            if health:
                health.take_damage(damage)
            
            # Apply knockback
            self.physics_system.apply_knockback(
                entity_id, force, 0, 0, center_x, center_y
            )
