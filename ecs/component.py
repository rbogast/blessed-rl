"""
Component management for the ECS system.
"""

from typing import Dict, Type, Any, Set, Optional, TypeVar, Generic
from collections import defaultdict

T = TypeVar('T')


class Component:
    """Base class for all components."""
    pass


class ComponentManager:
    """Manages component storage and retrieval."""
    
    def __init__(self):
        # component_type -> entity_id -> component_instance
        self._components: Dict[Type[Component], Dict[int, Component]] = defaultdict(dict)
        # entity_id -> set of component types
        self._entity_components: Dict[int, Set[Type[Component]]] = defaultdict(set)
    
    def add_component(self, entity_id: int, component: Component) -> None:
        """Add a component to an entity."""
        component_type = type(component)
        self._components[component_type][entity_id] = component
        self._entity_components[entity_id].add(component_type)
    
    def remove_component(self, entity_id: int, component_type: Type[Component]) -> None:
        """Remove a component from an entity."""
        if component_type in self._components:
            self._components[component_type].pop(entity_id, None)
        self._entity_components[entity_id].discard(component_type)
    
    def get_component(self, entity_id: int, component_type: Type[T]) -> Optional[T]:
        """Get a component from an entity."""
        return self._components[component_type].get(entity_id)
    
    def has_component(self, entity_id: int, component_type: Type[Component]) -> bool:
        """Check if an entity has a component."""
        return component_type in self._entity_components[entity_id]
    
    def has_components(self, entity_id: int, *component_types: Type[Component]) -> bool:
        """Check if an entity has all specified components."""
        entity_components = self._entity_components[entity_id]
        return all(comp_type in entity_components for comp_type in component_types)
    
    def get_entities_with_components(self, *component_types: Type[Component]) -> Set[int]:
        """Get all entities that have all specified components."""
        if not component_types:
            return set()
        
        # Start with entities that have the first component type
        entities = set(self._components[component_types[0]].keys())
        
        # Intersect with entities that have each additional component type
        for component_type in component_types[1:]:
            entities &= set(self._components[component_type].keys())
        
        return entities
    
    def remove_all_components(self, entity_id: int) -> None:
        """Remove all components from an entity."""
        component_types = list(self._entity_components[entity_id])
        for component_type in component_types:
            self.remove_component(entity_id, component_type)
    
    def get_component_count(self, component_type: Type[Component]) -> int:
        """Get the number of entities with a specific component type."""
        return len(self._components[component_type])
