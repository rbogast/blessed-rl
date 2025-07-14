"""
System management for the ECS system.
"""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .world import World


class System(ABC):
    """Base class for all systems."""
    
    def __init__(self, world: 'World'):
        self.world = world
    
    @abstractmethod
    def update(self, dt: float = 0.0) -> None:
        """Update the system. dt is delta time (unused in turn-based game)."""
        pass


class SystemManager:
    """Manages system registration and execution order."""
    
    def __init__(self):
        self._systems: List[System] = []
    
    def add_system(self, system: System) -> None:
        """Add a system to the manager."""
        self._systems.append(system)
    
    def remove_system(self, system: System) -> None:
        """Remove a system from the manager."""
        if system in self._systems:
            self._systems.remove(system)
    
    def update_all(self, dt: float = 0.0) -> None:
        """Update all systems in order."""
        for system in self._systems:
            system.update(dt)
    
    def get_system(self, system_type: type) -> System:
        """Get a system by type."""
        for system in self._systems:
            if isinstance(system, system_type):
                return system
        raise ValueError(f"System of type {system_type} not found")
    
    def clear(self) -> None:
        """Remove all systems."""
        self._systems.clear()
