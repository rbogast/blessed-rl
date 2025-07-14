"""
Core effects system components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from ecs.system import System

if TYPE_CHECKING:
    from ecs.world import World


class Effect(ABC):
    """Base class for all effects."""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.parameters = kwargs
    
    @abstractmethod
    def apply(self, world: 'World', **context) -> None:
        """Apply the effect to the world."""
        pass


class EffectsManager(System):
    """Central manager for all effects in the game."""
    
    def __init__(self, world: 'World'):
        super().__init__(world)
        self.registered_effects: Dict[str, Effect] = {}
        self.pending_effects: List[tuple] = []  # (effect_name, context)
    
    def register_effect(self, effect: Effect) -> None:
        """Register an effect with the manager."""
        self.registered_effects[effect.name] = effect
    
    def trigger_effect(self, effect_name: str, **context) -> None:
        """Queue an effect to be applied on the next update."""
        self.pending_effects.append((effect_name, context))
    
    def update(self, dt: float = 0.0) -> None:
        """Process all pending effects."""
        for effect_name, context in self.pending_effects:
            if effect_name in self.registered_effects:
                effect = self.registered_effects[effect_name]
                effect.apply(self.world, **context)
        
        self.pending_effects.clear()
    
    def get_effect(self, effect_name: str) -> Optional[Effect]:
        """Get a registered effect by name."""
        return self.registered_effects.get(effect_name)
