"""
Utility functions for calculating derived stats from character attributes.
"""

from components.character import CharacterAttributes, Experience
from components.combat import Health


def calculate_max_hp(attributes: CharacterAttributes, level: int = 1, base_hp: int = 30) -> int:
    """Calculate maximum HP from attributes and level."""
    return base_hp + (attributes.constitution * 2) + (attributes.strength * 1) + (level * 2)


def calculate_attack_power(attributes: CharacterAttributes, level: int = 1, base_attack: int = 5) -> int:
    """Calculate attack power from attributes and level."""
    return base_attack + attributes.strength + (level // 2)


def calculate_evasion(attributes: CharacterAttributes, level: int = 1, base_evasion: int = 5) -> int:
    """Calculate evasion from attributes and level."""
    return base_evasion + attributes.agility + (level // 3)


def calculate_damage_reduction(attributes: CharacterAttributes, equipment_bonus: int = 0) -> int:
    """Calculate damage reduction from constitution and equipment."""
    return (attributes.constitution // 3) + equipment_bonus


def get_total_equipment_bonuses(world, entity_id: int) -> dict:
    """Get total equipment bonuses for an entity."""
    from components.items import EquipmentSlots, Equipment
    
    equipment_slots = world.get_component(entity_id, EquipmentSlots)
    if not equipment_slots:
        return {'attack': 0, 'defense': 0, 'attributes': {}}
    
    total_attack = 0
    total_defense = 0
    total_attributes = {}
    
    for slot, item_entity_id in equipment_slots.get_equipped_items().items():
        if item_entity_id:
            equipment = world.get_component(item_entity_id, Equipment)
            if equipment:
                total_attack += equipment.attack_bonus
                total_defense += equipment.defense_bonus
                
                # Add attribute bonuses
                for attr, bonus in equipment.attribute_bonuses.items():
                    total_attributes[attr] = total_attributes.get(attr, 0) + bonus
    
    return {
        'attack': total_attack,
        'defense': total_defense,
        'attributes': total_attributes
    }


def get_effective_attributes(attributes: CharacterAttributes, equipment_bonuses: dict) -> CharacterAttributes:
    """Get effective attributes including equipment bonuses."""
    attr_bonuses = equipment_bonuses.get('attributes', {})
    
    # Create a copy with bonuses applied
    effective_attrs = CharacterAttributes(
        strength=attributes.strength + attr_bonuses.get('strength', 0),
        agility=attributes.agility + attr_bonuses.get('agility', 0),
        constitution=attributes.constitution + attr_bonuses.get('constitution', 0),
        intelligence=attributes.intelligence + attr_bonuses.get('intelligence', 0),
        willpower=attributes.willpower + attr_bonuses.get('willpower', 0),
        aura=attributes.aura + attr_bonuses.get('aura', 0)
    )
    
    return effective_attrs


def calculate_speed(attributes: CharacterAttributes, base_speed: int = 100) -> int:
    """Calculate speed/initiative from agility."""
    return base_speed + (attributes.agility * 2)


def calculate_hit_chance(attacker_ap: int, target_ev: int, base_chance: int = 70) -> int:
    """Calculate hit chance percentage based on attack power vs evasion."""
    # Base 70% hit chance, modified by AP vs EV difference
    ap_advantage = attacker_ap - target_ev
    hit_chance = base_chance + (ap_advantage * 3)  # 3% per point difference
    
    # Clamp between 5% and 95%
    return max(5, min(95, hit_chance))


def calculate_critical_chance(attacker_agility: int, target_agility: int, base_crit: int = 5) -> int:
    """Calculate critical hit chance based on agility difference."""
    agility_advantage = attacker_agility - target_agility
    crit_chance = base_crit + max(0, agility_advantage)  # Only positive advantage helps
    
    # Clamp between 0% and 25%
    return max(0, min(25, crit_chance))


def update_health_from_attributes(health: Health, attributes: CharacterAttributes, level: int = 1) -> None:
    """Update a Health component's max HP based on current attributes and level."""
    old_max = health.max_health
    new_max = calculate_max_hp(attributes, level)
    
    # Maintain the same percentage of health if possible
    if old_max > 0:
        health_percentage = health.current_health / old_max
        health.current_health = int(new_max * health_percentage)
    else:
        health.current_health = new_max
    
    health.max_health = new_max


def get_resistance_bonus(attributes: CharacterAttributes, resistance_type: str) -> int:
    """Get resistance bonus for different types of effects."""
    if resistance_type == 'physical':
        return attributes.constitution // 4
    elif resistance_type == 'mental':
        return attributes.willpower // 3
    elif resistance_type == 'fear':
        return attributes.aura // 4 + attributes.willpower // 4
    else:
        return 0
