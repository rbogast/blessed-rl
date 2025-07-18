"""
Dead component for marking entities as dead but still in the simulation.
"""

from ecs.component import Component


class Dead(Component):
    """Marker component indicating this entity is dead but still present in the simulation."""
    
    def __init__(self):
        pass
