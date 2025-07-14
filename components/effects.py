"""
Components for the effects system.
"""

from ecs.component import Component
from typing import Dict, List, Any
import time


class Physics(Component):
    """Physics properties for entities that can be affected by knockback."""
    
    def __init__(self, mass: float = 10.0):
        self.mass = mass  # Mass affects how far entity is knocked back
        self.velocity_x = 0.0  # Current velocity in X direction
        self.velocity_y = 0.0  # Current velocity in Y direction


class StatusEffect(Component):
    """Container for status effects affecting an entity."""
    
    def __init__(self):
        self.effects: Dict[str, Dict[str, Any]] = {}  # effect_name -> effect_data
    
    def add_effect(self, effect_name: str, duration: int, intensity: int = 1, **kwargs) -> None:
        """Add a status effect."""
        self.effects[effect_name] = {
            'duration': duration,
            'intensity': intensity,
            'start_time': time.time(),
            **kwargs
        }
    
    def remove_effect(self, effect_name: str) -> None:
        """Remove a status effect."""
        if effect_name in self.effects:
            del self.effects[effect_name]
    
    def has_effect(self, effect_name: str) -> bool:
        """Check if entity has a specific effect."""
        return effect_name in self.effects
    
    def get_effect(self, effect_name: str) -> Dict[str, Any]:
        """Get effect data."""
        return self.effects.get(effect_name, {})
    
    def tick_effects(self) -> List[str]:
        """Reduce duration of all effects and return list of expired effects."""
        expired = []
        for effect_name, data in list(self.effects.items()):
            data['duration'] -= 1
            if data['duration'] <= 0:
                expired.append(effect_name)
                del self.effects[effect_name]
        return expired


class TileModification(Component):
    """Tracks modifications to world tiles (like blood splatter)."""
    
    def __init__(self):
        self.bloody_tiles: Dict[tuple, int] = {}  # (x, y) -> intensity
    
    def add_blood_tile(self, x: int, y: int, intensity: int = 1) -> None:
        """Add or increase blood intensity at a tile."""
        current = self.bloody_tiles.get((x, y), 0)
        self.bloody_tiles[(x, y)] = min(current + intensity, 5)  # Max intensity of 5
    
    def get_blood_intensity(self, x: int, y: int) -> int:
        """Get blood intensity at a tile."""
        return self.bloody_tiles.get((x, y), 0)
    
    def is_bloody(self, x: int, y: int) -> bool:
        """Check if a tile is bloody."""
        return (x, y) in self.bloody_tiles
    
    def get_all_bloody_tiles(self) -> Dict[tuple, int]:
        """Get all bloody tiles."""
        return self.bloody_tiles.copy()


class WeaponEffects(Component):
    """Special effects that weapons can trigger."""
    
    def __init__(self):
        self.knockback_chance = 0.0  # Chance to cause knockback (0.0 to 1.0)
        self.knockback_force = 0.0   # Force of knockback
        self.slashing_chance = 0.0   # Chance to cause bleeding (0.0 to 1.0)
        self.slashing_damage = 0     # Base damage for slashing effects
    
    def set_knockback(self, chance: float, force: float) -> None:
        """Set knockback properties."""
        self.knockback_chance = max(0.0, min(1.0, chance))
        self.knockback_force = max(0.0, force)
    
    def set_slashing(self, chance: float, damage: int) -> None:
        """Set slashing properties."""
        self.slashing_chance = max(0.0, min(1.0, chance))
        self.slashing_damage = max(0, damage)
    
    def has_knockback(self) -> bool:
        """Check if weapon has knockback effect."""
        return self.knockback_chance > 0.0
    
    def has_slashing(self) -> bool:
        """Check if weapon has slashing effect."""
        return self.slashing_chance > 0.0
