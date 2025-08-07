"""
Event system for the ECS roguelike game.
"""

from .core import EventManager, Event
from .movement import EntityMovedEvent

__all__ = ['EventManager', 'Event', 'EntityMovedEvent']
