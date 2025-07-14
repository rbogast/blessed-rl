"""
Helper classes for the combat system to improve modularity and maintainability.
"""

from typing import Tuple, Optional, TYPE_CHECKING
from components.core import Position
from components.combat import Health
from components.character import CharacterAttributes, Experience
from components.effects import WeaponEffects, Physics
from components.ai import AI
from game.character_stats import (
    calculate_attack_power, calculate_evasion, calculate_damage_reduction,
    calculate_hit_chance, calculate_critical_chance,
    get_total_equipment_bonuses, get_effective_attributes
)
import random

if TYPE_CHECKING:
    from ecs.world import World


class CombatStats:
    """Container for an entity's combat statistics."""
    
    def __init__(self, attack_power: int, evasion: int, damage_reduction: int, agility: int):
        self.attack_power = attack_power
        self.evasion = evasion
        self.damage_reduction = damage_reduction
        self.agility = agility


class CombatStatsResolver:
    """Handles resolving combat stats from entity components."""
    
    def __init__(self, world: 'World'):
        self.world = world
    
    def get_combat_stats(self, entity_id: int) -> CombatStats:
        """Get combat stats for an entity, handling both new and old attribute systems."""
        attrs = self.world.get_component(entity_id, CharacterAttributes)
        exp = self.world.get_component(entity_id, Experience)
        
        if attrs:
            # New attribute system
            level = exp.level if exp else 1
            equipment = get_total_equipment_bonuses(self.world, entity_id)
            effective_attrs = get_effective_attributes(attrs, equipment)
            
            attack_power = calculate_attack_power(effective_attrs, level) + equipment['attack']
            evasion = calculate_evasion(effective_attrs, level)
            damage_reduction = calculate_damage_reduction(effective_attrs, equipment['defense'])
            agility = effective_attrs.agility
        else:
            # Fallback to old system
            from components.combat import Stats
            stats = self.world.get_component(entity_id, Stats)
            attack_power = stats.get_damage() if stats else 5
            evasion = 5
            damage_reduction = stats.get_defense() if stats else 0
            agility = 10
        
        return CombatStats(attack_power, evasion, damage_reduction, agility)


class CombatCalculator:
    """Handles combat calculations like hit chance, damage, and critical hits."""
    
    @staticmethod
    def calculate_hit_result(attacker_stats: CombatStats, target_stats: CombatStats) -> Tuple[bool, bool]:
        """Calculate if an attack hits and if it's a critical hit."""
        hit_chance = calculate_hit_chance(attacker_stats.attack_power, target_stats.evasion)
        hit_roll = random.randint(1, 100)
        is_hit = hit_roll <= hit_chance
        
        if not is_hit:
            return False, False
        
        crit_chance = calculate_critical_chance(attacker_stats.agility, target_stats.agility)
        crit_roll = random.randint(1, 100)
        is_critical = crit_roll <= crit_chance
        
        return True, is_critical
    
    @staticmethod
    def calculate_damage(attacker_stats: CombatStats, target_stats: CombatStats, is_critical: bool) -> int:
        """Calculate final damage after all modifiers."""
        base_damage = attacker_stats.attack_power
        
        # Add randomness (±20%)
        damage_variance = int(base_damage * 0.2)
        damage = base_damage + random.randint(-damage_variance, damage_variance)
        
        # Apply critical hit multiplier
        if is_critical:
            damage = int(damage * 1.5)
        
        # Apply damage reduction
        final_damage = max(1, damage - target_stats.damage_reduction)
        
        return final_damage


class WeaponEffectsHandler:
    """Handles weapon effects like knockback and bleeding."""
    
    def __init__(self, world: 'World', effects_manager, message_log):
        self.world = world
        self.effects_manager = effects_manager
        self.message_log = message_log
    
    def apply_weapon_effects(self, attacker_id: int, target_id: int, damage: int) -> None:
        """Apply all weapon effects from the attacker's weapon to the target."""
        if not self.effects_manager:
            return
        
        weapon_entity = self._get_equipped_weapon(attacker_id)
        if not weapon_entity:
            return
        
        weapon_effects = self.world.get_component(weapon_entity, WeaponEffects)
        if not weapon_effects:
            return
        
        attacker_pos = self.world.get_component(attacker_id, Position)
        target_pos = self.world.get_component(target_id, Position)
        
        if not attacker_pos or not target_pos:
            return
        
        # Apply knockback effects
        self._apply_knockback_effect(attacker_id, target_id, weapon_effects, attacker_pos)
        
        # Apply slashing effects
        self._apply_slashing_effect(target_id, damage, weapon_effects, target_pos)
    
    def _apply_knockback_effect(self, attacker_id: int, target_id: int, weapon_effects: WeaponEffects, attacker_pos: Position) -> None:
        """Apply knockback effect if weapon has it."""
        if not weapon_effects.has_knockback():
            return
        
        if random.random() >= weapon_effects.knockback_chance:
            return
        
        # Ensure target has physics component
        if not self.world.has_component(target_id, Physics):
            self.world.add_component(target_id, Physics())
        
        # Calculate knockback force based on attacker's strength
        calculated_force = self._calculate_knockback_force(attacker_id, weapon_effects)
        
        self.effects_manager.trigger_effect("knockback",
            target_id=target_id,
            force=calculated_force,
            source_x=attacker_pos.x,
            source_y=attacker_pos.y
        )
    
    def _apply_slashing_effect(self, target_id: int, damage: int, weapon_effects: WeaponEffects, target_pos: Position) -> None:
        """Apply slashing effects (bleeding and blood splatter)."""
        if not weapon_effects.has_slashing():
            return
        
        if random.random() >= weapon_effects.slashing_chance:
            return
        
        # Apply bleeding status effect
        self.effects_manager.trigger_effect("apply_bleeding",
            target_id=target_id,
            intensity=max(1, weapon_effects.slashing_damage // 2),
            duration=5 + (damage // 5)  # Duration based on damage dealt
        )
        
        # Trigger blood splatter effect
        splatter_intensity = max(1, damage // 10)  # More damage = more blood
        self.effects_manager.trigger_effect("blood_splatter",
            center_x=target_pos.x,
            center_y=target_pos.y,
            intensity=splatter_intensity,
            radius=1
        )
    
    def _calculate_knockback_force(self, attacker_id: int, weapon_effects: WeaponEffects) -> float:
        """Calculate knockback force based on weapon and attacker strength."""
        attacker_attrs = self.world.get_component(attacker_id, CharacterAttributes)
        if attacker_attrs:
            # Use attacker's strength to determine knockback force
            strength_multiplier = attacker_attrs.strength / 10.0  # Normalize around 10
            return weapon_effects.knockback_force * strength_multiplier
        else:
            # Fallback to weapon's base force if no attributes
            return weapon_effects.knockback_force
    
    def _get_equipped_weapon(self, entity_id: int) -> Optional[int]:
        """Get the equipped weapon entity for an entity."""
        from components.items import EquipmentSlots
        
        equipment_slots = self.world.get_component(entity_id, EquipmentSlots)
        if not equipment_slots:
            return None
        
        return equipment_slots.weapon
