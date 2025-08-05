"""
Combat system for handling battles between entities.
"""

from ecs.system import System
from components.core import Position, Player, Renderable
from components.combat import Health
from components.character import CharacterAttributes, Experience, XPValue
from components.ai import AI
from components.corpse import Corpse, Species, Disposition, DispositionType
from components.effects import Physics
from components.items import Pickupable
from game.game_state import GameStateManager
from game.character_stats import update_health_from_attributes
from .combat_helpers import CombatStatsResolver, CombatCalculator, WeaponEffectsHandler
import random
import json


class CombatSystem(System):
    """Handles combat resolution between entities."""
    
    def __init__(self, world, game_state: GameStateManager, message_log, effects_manager=None, world_generator=None):
        super().__init__(world)
        self.game_state = game_state
        self.message_log = message_log
        self.effects_manager = effects_manager
        self.world_generator = world_generator
        
        # Initialize helper classes
        self.stats_resolver = CombatStatsResolver(world)
        self.weapon_effects_handler = WeaponEffectsHandler(world, effects_manager, message_log)
        
        # Load corpse configuration
        self.corpse_config = self._load_corpse_config()
    
    def _load_corpse_config(self) -> dict:
        """Load corpse configuration from JSON file."""
        try:
            with open('data/corpses.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration if file not found
            return {
                "default": {
                    "char": "inherit",
                    "color": "red"
                }
            }
    
    def update(self, dt: float = 0.0) -> None:
        """Combat system doesn't auto-update - it responds to attack requests."""
        pass
    
    def attack(self, attacker_id: int, target_id: int) -> bool:
        """Perform an attack from attacker to target."""
        target_health = self.world.get_component(target_id, Health)
        if not target_health:
            return False
        
        # Get combat stats for both entities
        attacker_stats = self.stats_resolver.get_combat_stats(attacker_id)
        target_stats = self.stats_resolver.get_combat_stats(target_id)
        
        # Calculate hit result
        is_hit, is_critical = CombatCalculator.calculate_hit_result(attacker_stats, target_stats)
        
        if not is_hit:
            self._generate_miss_message(attacker_id, target_id)
            return True
        
        # Calculate damage
        final_damage = CombatCalculator.calculate_damage(attacker_stats, target_stats, is_critical)
        
        # Deal damage
        actual_damage = target_health.take_damage(final_damage)
        
        # Generate combat message
        self._generate_combat_message(attacker_id, target_id, actual_damage, is_critical)
        
        # Calculate weapon effects before checking if target dies
        # This allows us to apply physics to corpses if the target dies
        weapon_effects_data = self.weapon_effects_handler.calculate_weapon_effects(attacker_id, target_id, actual_damage)
        
        # Trigger blood splatter for high damage (regardless of weapon effects)
        self._handle_blood_splatter(target_id, actual_damage)
        
        # Check if target died
        if not target_health.is_alive():
            # Target died - create corpse and apply effects to it
            corpse_id = self._handle_death(attacker_id, target_id)
            if corpse_id and weapon_effects_data:
                self.weapon_effects_handler.apply_calculated_effects(corpse_id, weapon_effects_data)
        else:
            # Target survived - apply effects normally
            if weapon_effects_data:
                self.weapon_effects_handler.apply_calculated_effects(target_id, weapon_effects_data)
        
        return True
    
    
    def _handle_blood_splatter(self, target_id: int, damage: int) -> None:
        """Handle blood splatter based on damage dealt."""
        if not self.game_state or not self.world_generator:
            return
        
        target_pos = self.world.get_component(target_id, Position)
        if not target_pos:
            return
        
        # Trigger blood splatter for high damage (10+ damage)
        if damage >= 10:
            from effects.implementations.blood_splatter import BloodSplatterEffect
            splatter_level = min(5, damage // 5)  # 1-5 tiles based on damage
            blood_effect = BloodSplatterEffect(level=splatter_level)
            blood_effect.trigger(target_pos.x, target_pos.y, self.game_state, self.world_generator)
            
    
    
    def _generate_combat_message(self, attacker_id: int, target_id: int, damage: int, is_critical: bool = False) -> None:
        """Generate a combat message for the message log."""
        attacker_name = self._get_entity_name(attacker_id)
        target_name = self._get_entity_name(target_id)
        
        crit_text = " critically" if is_critical else ""
        
        if self.world.has_component(attacker_id, Player):
            message = f"You{crit_text} hit the {target_name} for {damage} damage!"
        elif self.world.has_component(target_id, Player):
            message = f"The {attacker_name}{crit_text} hits you for {damage} damage!"
        else:
            message = f"The {attacker_name}{crit_text} hits the {target_name} for {damage} damage!"
        
        self.message_log.add_combat(message)
    
    def _generate_miss_message(self, attacker_id: int, target_id: int) -> None:
        """Generate a miss message for the message log."""
        attacker_name = self._get_entity_name(attacker_id)
        target_name = self._get_entity_name(target_id)
        
        if self.world.has_component(attacker_id, Player):
            message = f"You miss the {target_name}."
        elif self.world.has_component(target_id, Player):
            message = f"The {attacker_name} misses you."
        else:
            message = f"The {attacker_name} misses the {target_name}."
        
        self.message_log.add_combat(message)
    
    def _get_entity_name(self, entity_id: int) -> str:
        """Get a display name for an entity."""
        from utils.entity_naming import get_entity_name
        return get_entity_name(self.world, entity_id)
    
    def _handle_death(self, attacker_id: int, target_id: int) -> int:
        """Handle entity death and XP gain. Returns corpse entity ID if created."""
        target_name = self._get_entity_name(target_id)
        
        if self.world.has_component(target_id, Player):
            # Player died - handle permadeath
            species = self.world.get_component(target_id, Species)
            if not species:
                # Add default human species if missing
                self.world.add_component(target_id, Species('human'))
            
            # Add corpse component to mark as dead
            self.world.add_component(target_id, Corpse('human'))
            
            # Change player appearance to red
            renderable = self.world.get_component(target_id, Renderable)
            if renderable:
                renderable.color = 'red'
            
            # Set game over state
            position = self.world.get_component(target_id, Position)
            final_x = position.x if position else 0
            self.game_state.game_over("You died!", final_x)
            
            self.message_log.add_combat("You have died! Game Over.")
            self.message_log.add_combat("Your save file has been deleted (permadeath).")
            self.message_log.add_combat("Press any key to return to the launcher.")
            
            # Delete save file for permadeath (will be called by main game loop)
            # We don't call it directly here to avoid import cycles
            return None
        else:
            # Enemy died
            self.message_log.add_combat(f"The {target_name} dies!")
            
            # Handle XP gain if player killed the enemy
            if self.world.has_component(attacker_id, Player):
                self._award_xp(attacker_id, target_id)
            
            # Create corpse before destroying the entity
            corpse_id = self._create_corpse(target_id)
            
            # Add corpse to current level if we have a world generator
            if corpse_id and self.world_generator:
                current_level = self.world_generator.get_current_level()
                if current_level:
                    current_level.add_entity(corpse_id)
            
            # Remove the entity from the world
            self.world.destroy_entity(target_id)
            
            return corpse_id
    
    def _create_corpse(self, entity_id: int) -> int:
        """Create a corpse entity from a dead entity. Returns corpse entity ID."""
        # Get components from the original entity
        position = self.world.get_component(entity_id, Position)
        renderable = self.world.get_component(entity_id, Renderable)
        species = self.world.get_component(entity_id, Species)
        physics = self.world.get_component(entity_id, Physics)
        
        if not position or not species:
            return None  # Can't create corpse without position and species
        
        # Get corpse configuration
        species_name = species.species_name
        corpse_config = self.corpse_config.get(species_name, self.corpse_config.get('default', {}))
        
        # Determine corpse appearance
        if corpse_config.get('char') == 'inherit' and renderable:
            corpse_char = renderable.char
        else:
            corpse_char = corpse_config.get('char', '%')
        
        corpse_color = corpse_config.get('color', 'red')
        
        # Create corpse entity
        corpse_entity = self.world.create_entity()
        
        # Add corpse components
        self.world.add_component(corpse_entity, Position(position.x, position.y))
        self.world.add_component(corpse_entity, Renderable(corpse_char, corpse_color))
        self.world.add_component(corpse_entity, Corpse(species_name))
        self.world.add_component(corpse_entity, Species(species_name))
        self.world.add_component(corpse_entity, Pickupable())  # Corpses can be picked up
        
        # Preserve physics (weight) if available
        if physics:
            self.world.add_component(corpse_entity, Physics(mass=physics.mass))
        else:
            # Default weight for corpses
            self.world.add_component(corpse_entity, Physics(mass=150.0))
        
        return corpse_entity
    
    def _award_xp(self, player_id: int, enemy_id: int) -> None:
        """Award XP to the player for killing an enemy."""
        player_exp = self.world.get_component(player_id, Experience)
        enemy_xp_value = self.world.get_component(enemy_id, XPValue)
        
        if not player_exp or not enemy_xp_value:
            return
        
        # Award XP
        xp_gained = enemy_xp_value.xp_value
        leveled_up = player_exp.add_xp(xp_gained)
        
        self.message_log.add_info(f"You gain {xp_gained} XP!")
        
        if leveled_up:
            self.message_log.add_info(f"Level up! You are now level {player_exp.level}!")
            
            # Update player's health based on new level
            player_health = self.world.get_component(player_id, Health)
            player_attrs = self.world.get_component(player_id, CharacterAttributes)
            
            if player_health and player_attrs:
                update_health_from_attributes(player_health, player_attrs, player_exp.level)
                self.message_log.add_info(f"Your max HP is now {player_health.max_health}!")
    
    def can_attack(self, attacker_id: int, target_x: int, target_y: int) -> bool:
        """Check if an attacker can attack a target at the given position."""
        attacker_pos = self.world.get_component(attacker_id, Position)
        if not attacker_pos:
            return False
        
        # Check if target is adjacent (including diagonals)
        dx = abs(attacker_pos.x - target_x)
        dy = abs(attacker_pos.y - target_y)
        
        return dx <= 1 and dy <= 1 and (dx > 0 or dy > 0)  # Adjacent but not same position
    
    def get_attackable_entity_at(self, x: int, y: int) -> int:
        """Get an entity that can be attacked at the given position."""
        entities_at_pos = self.world.get_entities_with_components(Position, Health)
        
        for entity_id in entities_at_pos:
            position = self.world.get_component(entity_id, Position)
            if position and position.x == x and position.y == y:
                return entity_id
        
        return None
