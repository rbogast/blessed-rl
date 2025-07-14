"""
Effects system for the ECS roguelike.

This module provides a comprehensive effects system including:
- Physics-based knockback and shockwave effects
- Status effects like bleeding
- Tile modifications like blood splatter
"""

from .core import EffectsManager, Effect
from .physics import PhysicsSystem, KnockbackEffect
from .status_effects import StatusEffectsSystem, BleedingEffect
from .tile_effects import TileEffectsSystem, BloodSplatterEffect

__all__ = [
    'EffectsManager',
    'Effect',
    'PhysicsSystem',
    'KnockbackEffect', 
    'StatusEffectsSystem',
    'BleedingEffect',
    'TileEffectsSystem',
    'BloodSplatterEffect'
]
