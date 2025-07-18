"""
AI system for controlling NPC behavior.
"""

from ecs.system import System
from components.core import Position, Player, Visible
from components.combat import Health
from components.ai import AI, AIType
from systems.movement import MovementSystem
from systems.combat import CombatSystem
import random


class AISystem(System):
    """Handles AI behavior for NPCs."""
    
    def __init__(self, world, movement_system: MovementSystem, combat_system: CombatSystem, message_log):
        super().__init__(world)
        self.movement_system = movement_system
        self.combat_system = combat_system
        self.message_log = message_log
    
    def update(self, dt: float = 0.0) -> None:
        """Update all AI entities."""
        ai_entities = self.world.get_entities_with_components(AI, Position, Health)
        
        for entity_id in ai_entities:
            self._update_ai_entity(entity_id)
    
    def _update_ai_entity(self, entity_id: int) -> None:
        """Update a single AI entity."""
        ai = self.world.get_component(entity_id, AI)
        position = self.world.get_component(entity_id, Position)
        health = self.world.get_component(entity_id, Health)
        visible = self.world.get_component(entity_id, Visible)
        
        if not ai or not position or not health or not health.is_alive():
            return
        
        # Only act if the entity is visible to the player (or if player is dead, always act)
        player_entity = self._find_player_any_state()
        player_alive = False
        if player_entity:
            player_health = self.world.get_component(player_entity, Health)
            player_alive = player_health and player_health.is_alive()
        
        if not player_alive:
            # Player is dead, AI should continue acting (wandering around)
            pass
        elif not visible or not visible.visible:
            # Player is alive but this entity isn't visible, don't act
            return
        
        # Check if current target is still alive
        if ai.target_entity:
            target_health = self.world.get_component(ai.target_entity, Health)
            if not target_health or not target_health.is_alive():
                ai.target_entity = None
                ai.last_known_position = None
        
        # Find the player (alive or dead)
        player_pos = None
        if player_entity:
            player_pos = self.world.get_component(player_entity, Position)
        
        # If player is alive, update targeting
        if player_alive and player_pos:
            # Calculate distance to player
            distance = self.movement_system.calculate_distance(
                position.x, position.y, player_pos.x, player_pos.y
            )
            
            # Update AI state
            if distance <= ai.detection_range:
                ai.target_entity = player_entity
                ai.last_known_position = (player_pos.x, player_pos.y)
        elif not player_alive:
            # Player is dead, clear target and wander
            ai.target_entity = None
            ai.last_known_position = None
        
        # Execute AI behavior
        if ai.ai_type == AIType.AGGRESSIVE:
            self._aggressive_behavior(entity_id, ai, position)
        elif ai.ai_type == AIType.PATROL:
            self._patrol_behavior(entity_id, ai, position)
        elif ai.ai_type == AIType.GUARD:
            self._guard_behavior(entity_id, ai, position)
    
    def _aggressive_behavior(self, entity_id: int, ai: AI, position: Position) -> None:
        """Aggressive AI: moves toward and attacks the player, or wanders if no target."""
        if not ai.target_entity:
            # No target, wander around
            self._random_movement(entity_id)
            return
        
        target_pos = self.world.get_component(ai.target_entity, Position)
        if not target_pos:
            # Target position not found, wander around
            self._random_movement(entity_id)
            return
        
        # Check if we can attack
        if self.combat_system.can_attack(entity_id, target_pos.x, target_pos.y):
            self.combat_system.attack(entity_id, ai.target_entity)
            return
        
        # Move toward the target
        dx, dy = self.movement_system.get_direction_to(
            position.x, position.y, target_pos.x, target_pos.y
        )
        
        # Try to move toward target
        if dx != 0 or dy != 0:
            success = self.movement_system.try_move_entity(entity_id, dx, dy)
            
            # If direct path is blocked, try alternative moves
            if not success:
                self._try_alternative_moves(entity_id, dx, dy)
    
    def _patrol_behavior(self, entity_id: int, ai: AI, position: Position) -> None:
        """Patrol AI: moves in patterns, attacks when player is close."""
        # If we have a target and they're close, act aggressively
        if ai.target_entity:
            target_pos = self.world.get_component(ai.target_entity, Position)
            if target_pos:
                distance = self.movement_system.calculate_distance(
                    position.x, position.y, target_pos.x, target_pos.y
                )
                
                if distance <= 3:  # Close enough to attack
                    self._aggressive_behavior(entity_id, ai, position)
                    return
        
        # Otherwise, patrol randomly
        self._random_movement(entity_id)
    
    def _guard_behavior(self, entity_id: int, ai: AI, position: Position) -> None:
        """Guard AI: stays in area, attacks when approached."""
        # Set home position if not set
        if ai.home_position is None:
            ai.home_position = (position.x, position.y)
        
        # If we have a target and they're close, attack
        if ai.target_entity:
            target_pos = self.world.get_component(ai.target_entity, Position)
            if target_pos:
                distance = self.movement_system.calculate_distance(
                    position.x, position.y, target_pos.x, target_pos.y
                )
                
                if distance <= 2:  # Very close - attack
                    if self.combat_system.can_attack(entity_id, target_pos.x, target_pos.y):
                        self.combat_system.attack(entity_id, ai.target_entity)
                        return
                    else:
                        # Move toward target if not adjacent
                        dx, dy = self.movement_system.get_direction_to(
                            position.x, position.y, target_pos.x, target_pos.y
                        )
                        self.movement_system.try_move_entity(entity_id, dx, dy)
                        return
        
        # Return to home position if too far away
        home_distance = self.movement_system.calculate_distance(
            position.x, position.y, ai.home_position[0], ai.home_position[1]
        )
        
        if home_distance > 3:
            dx, dy = self.movement_system.get_direction_to(
                position.x, position.y, ai.home_position[0], ai.home_position[1]
            )
            self.movement_system.try_move_entity(entity_id, dx, dy)
    
    def _try_alternative_moves(self, entity_id: int, preferred_dx: int, preferred_dy: int) -> None:
        """Try alternative movement directions when preferred path is blocked."""
        # List of alternative directions, prioritizing those close to the preferred direction
        alternatives = []
        
        # Add perpendicular directions
        if preferred_dx != 0:
            alternatives.extend([(preferred_dx, 0), (0, preferred_dy), (0, -preferred_dy)])
        if preferred_dy != 0:
            alternatives.extend([(preferred_dy, 0), (0, preferred_dy), (-preferred_dx, 0)])
        
        # Try each alternative
        for dx, dy in alternatives:
            if self.movement_system.try_move_entity(entity_id, dx, dy):
                break
    
    def _random_movement(self, entity_id: int) -> None:
        """Move randomly."""
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        # 70% chance to move, 30% chance to stay still
        if random.random() < 0.7:
            dx, dy = random.choice(directions)
            self.movement_system.try_move_entity(entity_id, dx, dy)
    
    def _find_player(self) -> int:
        """Find the player entity (alive only)."""
        player_entities = self.world.get_entities_with_components(Player, Position, Health)
        for player_id in player_entities:
            player_health = self.world.get_component(player_id, Health)
            if player_health and player_health.is_alive():
                return player_id
        return None
    
    def _find_player_any_state(self) -> int:
        """Find the player entity (alive or dead)."""
        player_entities = self.world.get_entities_with_components(Player, Position)
        for player_id in player_entities:
            return player_id
        return None
