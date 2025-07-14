"""
Combat-related components.
"""

from ecs.component import Component


class Health(Component):
    """Health component for entities that can take damage."""
    
    def __init__(self, max_health: int):
        self.max_health = max_health
        self.current_health = max_health
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage dealt."""
        actual_damage = min(damage, self.current_health)
        self.current_health -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal and return actual amount healed."""
        actual_heal = min(amount, self.max_health - self.current_health)
        self.current_health += actual_heal
        return actual_heal
    
    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.current_health > 0
    
    def is_full_health(self) -> bool:
        """Check if entity is at full health."""
        return self.current_health == self.max_health


class Stats(Component):
    """Combat statistics for entities."""
    
    def __init__(self, strength: int, defense: int, speed: int = 100):
        self.strength = strength
        self.defense = defense
        self.speed = speed  # Initiative/turn order (higher = faster)
    
    def get_damage(self) -> int:
        """Calculate damage output."""
        return self.strength
    
    def get_defense(self) -> int:
        """Calculate damage reduction."""
        return self.defense
