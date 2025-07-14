"""
Entity management for the ECS system.
"""

from typing import Set, Iterator


class EntityManager:
    """Manages entity creation, destruction, and ID allocation."""
    
    def __init__(self):
        self._next_id = 0
        self._alive_entities: Set[int] = set()
        self._dead_entities: Set[int] = set()
    
    def create_entity(self) -> int:
        """Create a new entity and return its ID."""
        if self._dead_entities:
            # Reuse a dead entity ID
            entity_id = self._dead_entities.pop()
        else:
            # Create a new ID
            entity_id = self._next_id
            self._next_id += 1
        
        self._alive_entities.add(entity_id)
        return entity_id
    
    def destroy_entity(self, entity_id: int) -> None:
        """Mark an entity as destroyed."""
        if entity_id in self._alive_entities:
            self._alive_entities.remove(entity_id)
            self._dead_entities.add(entity_id)
    
    def is_alive(self, entity_id: int) -> bool:
        """Check if an entity is alive."""
        return entity_id in self._alive_entities
    
    def get_alive_entities(self) -> Iterator[int]:
        """Get all alive entity IDs."""
        return iter(self._alive_entities)
    
    def get_entity_count(self) -> int:
        """Get the number of alive entities."""
        return len(self._alive_entities)
