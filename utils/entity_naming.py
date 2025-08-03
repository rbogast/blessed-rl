"""
Utility functions for getting entity names consistently across systems.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs.world import World


def get_entity_name(world: 'World', entity_id: int) -> str:
    """Get a display name for an entity with proper fallback hierarchy."""
    from components.core import Player
    from components.corpse import Species
    from components.ai import AI
    
    if world.has_component(entity_id, Player):
        return "player"
    
    # First priority: Species component (new system)
    species = world.get_component(entity_id, Species)
    if species:
        return species.species_name
    
    # Second priority: AI type (fallback for compatibility)
    ai = world.get_component(entity_id, AI)
    if ai:
        return ai.ai_type.value
    
    # Last resort
    return "entity"
