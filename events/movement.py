"""
Movement-related events.
"""

from .core import Event
from typing import Tuple


class EntityMovedEvent(Event):
    """Event emitted when an entity moves from one position to another."""
    
    def __init__(self, entity_id: int, old_pos: Tuple[int, int], new_pos: Tuple[int, int]):
        self.entity_id = entity_id
        self.old_pos = old_pos  # (x, y) tuple
        self.new_pos = new_pos  # (x, y) tuple
    
    def __repr__(self):
        return f"EntityMovedEvent(entity_id={self.entity_id}, old_pos={self.old_pos}, new_pos={self.new_pos})"


class EntityTeleportedEvent(Event):
    """Event emitted when an entity teleports (for special movement like stairs)."""
    
    def __init__(self, entity_id: int, old_pos: Tuple[int, int], new_pos: Tuple[int, int], teleport_type: str = "unknown"):
        self.entity_id = entity_id
        self.old_pos = old_pos
        self.new_pos = new_pos
        self.teleport_type = teleport_type  # "stairs", "magic", etc.
    
    def __repr__(self):
        return f"EntityTeleportedEvent(entity_id={self.entity_id}, old_pos={self.old_pos}, new_pos={self.new_pos}, type={self.teleport_type})"
