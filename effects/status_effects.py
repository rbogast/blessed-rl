"""
Status effects system for handling bleeding, poison, etc.
"""

import random
from typing import TYPE_CHECKING
from .core import Effect
from components.core import Position
from components.effects import StatusEffect
from components.combat import Health

if TYPE_CHECKING:
    from ecs.world import World


class StatusEffectsSystem:
    """Handles processing of status effects each turn."""
    
    def __init__(self, world: 'World', effects_manager, message_log, game_state=None, world_generator=None):
        self.world = world
        self.effects_manager = effects_manager
        self.message_log = message_log
        self.game_state = game_state
        self.world_generator = world_generator
    
    def update(self) -> None:
        """Process all status effects for all entities."""
        entities_with_status = self.world.get_entities_with_components(StatusEffect)
        
        for entity_id in entities_with_status:
            self._process_entity_status_effects(entity_id)
    
    def _process_entity_status_effects(self, entity_id: int) -> None:
        """Process status effects for a single entity."""
        status_effect = self.world.get_component(entity_id, StatusEffect)
        if not status_effect:
            return
        
        # Process each active effect
        for effect_name, effect_data in list(status_effect.effects.items()):
            if effect_name == "bleeding":
                self._process_bleeding(entity_id, effect_data)
        
        # Tick down effect durations and remove expired effects
        expired_effects = status_effect.tick_effects()
        for effect_name in expired_effects:
            self._handle_effect_expiration(entity_id, effect_name)
    
    def _process_bleeding(self, entity_id: int, effect_data: dict) -> None:
        """Process bleeding effect for an entity."""
        intensity = effect_data.get('intensity', 1)
        
        # Apply bleeding damage
        health = self.world.get_component(entity_id, Health)
        if health:
            bleeding_damage = max(1, intensity)
            health.take_damage(bleeding_damage)
            
            entity_name = self._get_entity_name(entity_id)
            self.message_log.add_combat(f"The {entity_name} bleeds for {bleeding_damage} damage!")
        
        # Chance to create blood splatter based on intensity
        position = self.world.get_component(entity_id, Position)
        if position and self.game_state and self.world_generator:
            # Higher intensity = more frequent blood splatter
            splatter_chance = min(0.8, intensity * 0.2)  # 20% per intensity level, max 80%
            
            if random.random() < splatter_chance:
                # Trigger blood splatter effect directly
                from .implementations.blood_splatter import BloodSplatterEffect
                blood_effect = BloodSplatterEffect(level=intensity)
                blood_effect.trigger(position.x, position.y, self.game_state, self.world_generator)
    
    def _handle_effect_expiration(self, entity_id: int, effect_name: str) -> None:
        """Handle when a status effect expires."""
        entity_name = self._get_entity_name(entity_id)
        
        if effect_name == "bleeding":
            self.message_log.add_info(f"The {entity_name} stops bleeding.")
    
    def _get_entity_name(self, entity_id: int) -> str:
        """Get display name for an entity."""
        from components.core import Player
        from components.ai import AI
        
        if self.world.has_component(entity_id, Player):
            return "player"
        
        ai = self.world.get_component(entity_id, AI)
        if ai:
            return ai.ai_type.value
        
        return "entity"
    
    def apply_bleeding(self, entity_id: int, intensity: int, duration: int) -> None:
        """Apply bleeding status effect to an entity."""
        status_effect = self.world.get_component(entity_id, StatusEffect)
        if not status_effect:
            status_effect = StatusEffect()
            self.world.add_component(entity_id, status_effect)
        
        # If already bleeding, increase intensity and reset duration
        if status_effect.has_effect("bleeding"):
            existing = status_effect.get_effect("bleeding")
            new_intensity = min(5, existing['intensity'] + intensity)  # Max intensity of 5
            new_duration = max(existing['duration'], duration)  # Use longer duration
            status_effect.add_effect("bleeding", new_duration, new_intensity)
        else:
            status_effect.add_effect("bleeding", duration, intensity)
        
        entity_name = self._get_entity_name(entity_id)
        self.message_log.add_combat(f"The {entity_name} starts bleeding!")


class BleedingEffect(Effect):
    """Effect that applies bleeding status to an entity."""
    
    def __init__(self, status_effects_system: StatusEffectsSystem):
        super().__init__("apply_bleeding")
        self.status_effects_system = status_effects_system
    
    def apply(self, world: 'World', **context) -> None:
        """Apply bleeding effect to target."""
        target_id = context.get('target_id')
        intensity = context.get('intensity', 1)
        duration = context.get('duration', 5)
        
        if target_id is None:
            return
        
        self.status_effects_system.apply_bleeding(target_id, intensity, duration)
