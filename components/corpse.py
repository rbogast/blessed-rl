"""
Corpse-related components.
"""

from ecs.component import Component


class Corpse(Component):
    """Marker component indicating this entity is a corpse."""
    
    def __init__(self, original_entity_type: str):
        self.original_entity_type = original_entity_type  # "orc", "goblin", etc.


class Race(Component):
    """Race information for entities."""
    
    def __init__(self, race_name: str):
        self.race_name = race_name  # "orc", "goblin", "skeleton", etc.
