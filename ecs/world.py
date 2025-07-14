"""
ECS World - coordinates entities, components, and systems.
"""

from typing import Type, Optional, Set, TypeVar
from .entity import EntityManager
from .component import ComponentManager, Component
from .system import SystemManager

T = TypeVar('T', bound=Component)


class World:
    """The main ECS world that coordinates all managers."""
    
    def __init__(self):
        self.entities = EntityManager()
        self.components = ComponentManager()
        self.systems = SystemManager()
    
    def create_entity(self) -> int:
        """Create a new entity."""
        return self.entities.create_entity()
    
    def destroy_entity(self, entity_id: int) -> None:
        """Destroy an entity and all its components."""
        self.components.remove_all_components(entity_id)
        self.entities.destroy_entity(entity_id)
    
    def add_component(self, entity_id: int, component: Component) -> None:
        """Add a component to an entity."""
        if not self.entities.is_alive(entity_id):
            raise ValueError(f"Entity {entity_id} is not alive")
        self.components.add_component(entity_id, component)
    
    def remove_component(self, entity_id: int, component_type: Type[Component]) -> None:
        """Remove a component from an entity."""
        self.components.remove_component(entity_id, component_type)
    
    def get_component(self, entity_id: int, component_type: Type[T]) -> Optional[T]:
        """Get a component from an entity."""
        return self.components.get_component(entity_id, component_type)
    
    def has_component(self, entity_id: int, component_type: Type[Component]) -> bool:
        """Check if an entity has a component."""
        return self.components.has_component(entity_id, component_type)
    
    def has_components(self, entity_id: int, *component_types: Type[Component]) -> bool:
        """Check if an entity has all specified components."""
        return self.components.has_components(entity_id, *component_types)
    
    def get_entities_with_components(self, *component_types: Type[Component]) -> Set[int]:
        """Get all entities that have all specified components."""
        return self.components.get_entities_with_components(*component_types)
    
    def update(self, dt: float = 0.0) -> None:
        """Update all systems."""
        self.systems.update_all(dt)
    
    def get_entity_count(self) -> int:
        """Get the number of alive entities."""
        return self.entities.get_entity_count()
