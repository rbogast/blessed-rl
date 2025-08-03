"""
Corpse-related components and character species/disposition.
"""

from ecs.component import Component
from enum import Enum


class Corpse(Component):
    """Marker component indicating this entity is a corpse."""
    
    def __init__(self, original_entity_type: str):
        self.original_entity_type = original_entity_type  # "goliath", "cultist", etc.


class Species(Component):
    """Species information for entities."""
    
    def __init__(self, species_name: str):
        self.species_name = species_name  # "goliath", "cultist", "skeleton", etc.


class DispositionType(Enum):
    """Types of disposition a character can have."""
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"


class Disposition(Component):
    """Disposition component indicating how a character behaves toward others."""
    
    def __init__(self, disposition: DispositionType = DispositionType.NEUTRAL):
        self.disposition = disposition
    
    def is_hostile(self) -> bool:
        """Check if this character is hostile."""
        return self.disposition == DispositionType.HOSTILE
    
    def is_friendly(self) -> bool:
        """Check if this character is friendly."""
        return self.disposition == DispositionType.FRIENDLY
    
    def is_neutral(self) -> bool:
        """Check if this character is neutral."""
        return self.disposition == DispositionType.NEUTRAL


# Backward compatibility alias - will be removed after refactoring
Race = Species
