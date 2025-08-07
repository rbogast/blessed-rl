"""
Core game components.
"""

from ecs.component import Component


class Position(Component):
    """Entity position in the world using global coordinates."""
    
    def __init__(self, x: int, y: int):
        self.x = x  # X coordinate
        self.y = y  # Y coordinate


class Renderable(Component):
    """Visual representation of an entity."""
    
    def __init__(self, char: str, color: str = 'white'):
        self.char = char
        self.color = color


class Player(Component):
    """Marker component for the player entity."""
    pass


class Blocking(Component):
    """Entities with this component block movement."""
    pass


class Visible(Component):
    """Tracks visibility state for FOV system."""
    
    def __init__(self):
        self.visible = False      # Currently visible to player
        self.explored = False     # Has been seen before


class Door(Component):
    """Door that can be opened/closed, affecting movement and vision."""
    
    def __init__(self, is_open: bool = False):
        self.is_open = is_open


class Prefab(Component):
    """Marker component for entities created from prefabs."""
    
    def __init__(self, prefab_id: str):
        self.prefab_id = prefab_id
